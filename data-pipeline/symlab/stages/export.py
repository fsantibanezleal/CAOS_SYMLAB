"""Stage 6: emit the committed artifact and the case manifest.

This is the boundary between the pipeline and the web app, and it is the only place either side is
allowed to learn about the other. Everything downstream is a pure function of what this stage writes,
which is why the schema is frozen at 1.0.0 before any user interface existed.

Two files per case:

- `data/derived/<case>/run.json`, the payload the app renders. Every float already rounded, every
  colour index already assigned, every downsample already disclosed with its original count.
- `manifests/<case>.json`, the audit record: which sources, which licences, which contract warnings,
  which lane, which measured costs, which defects were applied to the data on the way in.

Keeping them separate matters. The manifest is what a reviewer reads to decide whether to believe the
run; the payload is what the browser reads to draw it. Merging them would put provenance behind a
render path and make it easy to ship a number whose origin nobody can reconstruct.
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path

import numpy as np

from .. import __version__
from ..cases.registry import Case
from ..cases import physics_truths
from ..model import latex as tex
from ..core.contract import (
    SCHEMA_VERSION,
    dataset_descriptor,
    history_payload,
    pareto_member_payload,
    run_payload,
    validation_payload,
)
from ..model.expr import Node
from .evaluate import VariantScore, summarise
from .feature_extraction import Features
from .infer import VariantInference
from .preprocess import PreparedCase
from .train import TrainedVariant

MANIFEST_SCHEMA = "symlab.manifest/v1"
INDEX_SCHEMA = "symlab.index/v1"

#: Pareto members exported in full per variant. A front can grow long, and every member carries a
#: tree plus validation arrays. The cap is disclosed in the payload rather than applied silently.
MAX_EXPORTED_MEMBERS = 12


def _plain(value):
    """Make a dataclass tree JSON-serialisable without losing the non-finite markers."""
    if is_dataclass(value):
        return {k: _plain(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    # BOOLEANS FIRST. `bool` is a subclass of `int` in Python, and `np.bool_` answers to the numpy
    # integer check, so the integer branch below used to swallow every boolean in the artifact and
    # write it as 0 or 1. The web contract declares these fields `boolean | null`, so the payload
    # was quietly violating its own schema everywhere: `symbolic`, `numerical`, `agreed`,
    # `accuracy_solution`, `on_front`, `units_ok`, `complete`, `accepted`.
    #
    # It survived because almost every consumer tested truthiness, where 1 and true behave alike.
    # It broke the moment one of them compared identity: `member.units_ok === false` is false when
    # the value is 0, so the dimensional-consistency warning could never render.
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        if not np.isfinite(v):
            return None
        # SIGNIFICANT digits, not decimal places. `round(v, 8)` collapses everything below 5e-9 to
        # exactly 0.0, so a mean squared error of 6.1e-12 published as "0.0" and an R-squared of
        # 0.999999998 published as "1.0". Those are claims of an EXACT fit, and this lab's whole
        # argument turns on the difference between a very good fit and the right answer. A method
        # that reports zero error while reporting that it did not recover the law reads as a
        # contradiction rather than as the finding it actually is.
        #
        # Ten significant digits keeps the payload compact and keeps small magnitudes intact.
        return float(f"{v:.10g}")
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    return value


def build_run(
    case: Case,
    prepared: PreparedCase,
    features: Features,
    trained: list[TrainedVariant],
    inferred: list[VariantInference],
    scores: list[VariantScore],
    *,
    seed: int,
    truth: Node | None = None,
    certificate: dict | None = None,
) -> dict:
    """Assemble the schema 1.0.0 payload for one case."""
    dataset = prepared.dataset
    descriptor = dataset_descriptor(
        prepared.X_train, prepared.y_train,
        name=dataset.name,
        input_keys=dataset.input_keys,
        input_display=dataset.input_display,
        input_units=dataset.input_units,
        input_dims=dataset.input_dims,
        target_key=dataset.target_key,
        target_display=dataset.target_display,
        target_unit=dataset.target_unit,
        target_dims=dataset.target_dims,
        real_or_synthetic=dataset.real_or_synthetic,
        source=dataset.citation,
        license_note=dataset.licence,
    )
    # `n_rows` above is the TRAINING row count, because the descriptor is built from X_train. On its
    # own it contradicts the case description, which quotes the size of the published dataset. So the
    # whole accounting ships and the app can state every number it shows.
    descriptor["rows"] = {
        "source": dataset.n_rows_source,
        "used": int(prepared.X_train.shape[0] + prepared.X_test.shape[0]
                    + (0 if prepared.X_extrap is None else prepared.X_extrap.shape[0])),
        "train": int(prepared.X_train.shape[0]),
        "test": int(prepared.X_test.shape[0]),
        "extrapolation": 0 if prepared.X_extrap is None else int(prepared.X_extrap.shape[0]),
    }

    variants_payload = []
    for entry, inference, score in zip(trained, inferred, scores):
        members = entry.result.pareto[:MAX_EXPORTED_MEMBERS]
        pareto = [
            pareto_member_payload(
                individual.expression,
                prepared.X_train, prepared.y_train,
                index=index,
                X_test=prepared.X_test, y_test=prepared.y_test,
                display_names=dataset.input_display,
                input_dims=dataset.input_dims if features.units_declared else None,
                target_dims=dataset.target_dims if features.units_declared else None,
                n_primitives=len(entry.result.config.primitive_set),
                on_front=True,
                score=entry.result.pareto_scores[index] if index < len(entry.result.pareto_scores) else 0.0,
            )
            for index, individual in enumerate(members)
        ]
        selected = min(score.selected_index, len(pareto) - 1) if pareto else 0
        best_expression = (
            entry.result.pareto[selected].expression if entry.result.pareto else None
        )
        # A non-GP arm has no population and no generations. Exporting the ladder's numbers for it
        # would put figures in the audit record that describe a search it never ran.
        gp = entry.variant.method == "gp"
        variants_payload.append({
            "id": entry.variant.id,
            "method": entry.variant.method,
            "label_en": entry.variant.label_en,
            "label_es": entry.variant.label_es,
            "note_en": entry.variant.note_en,
            "note_es": entry.variant.note_es,
            "config": {
                "population": entry.result.config.population if gp else None,
                "generations": entry.result.config.generations if gp else None,
                "primitive_set": entry.result.config.primitive_set,
                "linear_scaling": entry.result.config.linear_scaling,
                "interval_guard": entry.result.config.interval_guard,
                "constant_tuning": entry.result.config.constant_tuning,
                "multi_objective": entry.result.config.multi_objective,
                "epsilon_lexicase": entry.result.config.epsilon_lexicase,
                "age_fitness": entry.result.config.age_fitness,
                "n_islands": entry.result.config.n_islands,
                "dedup": entry.result.config.dedup_structural or entry.result.config.dedup_semantic,
                "unit_typed": entry.result.config.unit_typed,
                "parsimony_coefficient": entry.result.config.parsimony_coefficient,
            },
            "pareto": pareto,
            "pareto_exported": len(pareto),
            "pareto_total": len(entry.result.pareto),
            "selected_index": selected,
            "history": history_payload(
                generation=entry.result.history["generation"],
                best_loss=entry.result.history["best_loss"],
                mean_loss=entry.result.history["mean_loss"],
                worst_loss=entry.result.history["worst_loss"],
                evaluations=entry.result.history["evals"],
                diversity_structural=entry.result.history["diversity"]["structural"],
                diversity_semantic=entry.result.history["diversity"]["semantic"],
                operator_entropy=entry.result.history["diversity"]["operator_entropy"],
                operator_names=entry.result.history["operator_freq"]["ops"],
                operator_matrix=entry.result.history["operator_freq"]["matrix"],
                islands=entry.result.history["islands"],
                migrations=entry.result.history["migrations"],
            ),
            "validation": (
                validation_payload(
                    best_expression, prepared.X_train, prepared.y_train,
                    X_test=prepared.X_test, y_test=prepared.y_test,
                    input_keys=dataset.input_keys,
                )
                if best_expression is not None else {}
            ),
            "score": _plain(score),
            "seconds": entry.seconds,
        })

    return run_payload(
        run_id=f"{case.id}-seed{seed}",
        dataset=descriptor,
        engine={
            "name": "symlab",
            "version": __version__,
            "seed": seed,
            "primitive_set": case.primitive_set,
            "deterministic": True,
        },
        pareto=[],   # the front lives per variant; a case has no single front
        selected_index=0,
        history={},
        validation={},
        notes={
            "case_id": case.id,
            "category": case.category,
            "category_name": case.category_name,
            "category_name_es": case.category_name_es,
            "name_en": case.name_en,
            "name_es": case.name_es,
            "summary_en": case.summary_en,
            "summary_es": case.summary_es,
            "ground_truth_known": case.ground_truth_known,
            "ground_truth_latex": (
                tex.to_latex(truth, display_names=dataset.input_display)
                if truth is not None else case.ground_truth_latex
            ),
            "ground_truth_available": truth is not None,
            # WHY it is not checkable, not merely THAT it is not. "nobody wrote the truth down",
            # "the law is outside the search space" and "the published formula does not describe
            # this data" mean entirely different things about the result on screen.
            "not_checkable_reason": (
                "" if truth is not None else physics_truths.not_checkable_reason(
                    case.loader,
                    is_generator=case.is_generator,
                    generator_id=case.loader.split(":", 1)[1] if case.is_generator else "",
                )
            ),
            "regime": prepared.regime,
            "real_or_synthetic": case.real_or_synthetic,
            "caveats": list(case.caveats),
            # The ingestion contract's own warnings, carried into the WEB payload rather than only
            # into the audit manifest. The pipeline detects, for instance, that the flotation target
            # takes 719 distinct values across 4097 rows and warns that fitting at that resolution
            # may leak it. That warning lived in manifests/<case>.json, which the app never reads,
            # so the reader most in need of it was the only one who could not see it.
            "contract_warnings": list(prepared.contract_report.get("warnings", [])),
            "defects_applied": list(prepared.contract_report.get("defects_applied", [])),
            "split_note": prepared.split_note,
            "features_note": features.note,
            "sampling": features.sampling,
            "variants": variants_payload,
            "summary": summarise(scores),
            "certificate": certificate,
            "max_exported_members": MAX_EXPORTED_MEMBERS,
        },
    )


def build_manifest(
    case: Case,
    prepared: PreparedCase,
    features: Features,
    scores: list[VariantScore],
    *,
    seed: int,
    artifact_relative: str,
    artifact_bytes: int,
) -> dict:
    """The audit record. Deterministic: no wall-clock timestamps that would dirty git on a re-run."""
    return {
        "schema": MANIFEST_SCHEMA,
        "case_id": case.id,
        "category": case.category,
        "engine": {"package": "symlab", "version": __version__},
        "seed": seed,
        "artifact": {
            "path": artifact_relative,
            "format": "json",
            "schema_version": SCHEMA_VERSION,
            "bytes": artifact_bytes,
        },
        "lane": "precompute",
        "data": {
            "source_id": prepared.dataset.source_id,
            "citation": prepared.dataset.citation,
            "licence": prepared.dataset.licence,
            "redistribution": prepared.dataset.redistribution,
            "real_or_synthetic": prepared.dataset.real_or_synthetic,
            "defects_applied": list(prepared.dataset.defects_applied),
        },
        "contract": prepared.contract_report,
        "units_declared": features.units_declared,
        "split_note": prepared.split_note,
        "variants": [
            {
                "id": s.variant_id,
                "seconds": s.seconds,
                "evaluations": s.evaluations,
                "front_size": s.front_size,
                "selected_complexity": s.selected_complexity,
                "test_r2": s.best_test_r2,
                "accuracy_solution": s.accuracy_solution,
                "exact_recovery": s.equivalence.recovered if s.equivalence else None,
                "symbolic_test_decided": (s.equivalence.symbolic is not None) if s.equivalence else None,
                "irrelevant_features": s.n_irrelevant_features,
            }
            for s in scores
        ],
        "summary": summarise(scores),
    }


def write(
    case: Case,
    run: dict,
    manifest_stub: dict,
    *,
    derived_dir: Path,
    manifests_dir: Path,
) -> tuple[Path, Path, int]:
    """Write the artifact and the manifest, returning their paths and the artifact size."""
    case_dir = derived_dir / case.id
    case_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = case_dir / "run.json"
    payload = json.dumps(_plain(run), separators=(",", ":"), allow_nan=False)
    artifact_path.write_text(payload, encoding="utf-8")

    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / f"{case.id}.json"
    manifest_stub["artifact"]["bytes"] = len(payload.encode("utf-8"))
    manifest_path.write_text(json.dumps(_plain(manifest_stub), indent=2), encoding="utf-8")
    return artifact_path, manifest_path, len(payload.encode("utf-8"))


def build_index(entries: list[dict], coverage: dict) -> dict:
    """The flat inventory the app loads first."""
    return {
        "schema": INDEX_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "engine_version": __version__,
        "generated_on": date.today().isoformat(),
        "n_cases": len(entries),
        "coverage": coverage,
        "cases": sorted(entries, key=lambda e: (e["category"], e["case_id"])),
    }
