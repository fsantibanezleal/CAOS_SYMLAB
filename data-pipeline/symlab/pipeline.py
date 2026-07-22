"""The offline pipeline orchestrator and its command line.

    python -m symlab.pipeline                     # every case
    python -m symlab.pipeline ccpp-derating       # one case
    python -m symlab.pipeline --list              # what exists
    python -m symlab.pipeline --quick             # a reduced budget, for a smoke run

A run is a pure function of `(case, config, seed, data)`. Nothing here reads the clock into an
artifact, so regenerating a case produces byte-identical output and a re-bake never dirties git
without a real change behind it.

The suite cases (the published-physics collections) expand into one sub-case per problem, because a
case in the app is one dataset with one workbench. Presenting eighteen different physical laws as a
single case would make every number on that workbench an average over incomparable things.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

from .cases.registry import Case, coverage_summary, list_cases
from .core.contract import SCHEMA_VERSION
from .io.sources import FEYNMAN_SELECTION, STROGATZ_SELECTION
from .stages import evaluate as evaluate_stage
from .stages import export as export_stage
from .stages import feature_extraction as features_stage
from .stages import infer as infer_stage
from .stages import preprocess as preprocess_stage
from .stages import train as train_stage

REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED = REPO_ROOT / "data" / "derived"
MANIFESTS = REPO_ROOT / "manifests"

STAGES = ("preprocess", "feature_extraction", "train", "infer", "evaluate", "export")


def expand_suites(cases: list[Case]) -> list[Case]:
    """Turn a suite case into one case per underlying problem."""
    out: list[Case] = []
    for case in cases:
        if case.loader == "pmlb:feynman":
            for dataset in FEYNMAN_SELECTION:
                short = dataset.replace("feynman_", "").lower()
                out.append(replace(
                    case, id=f"feynman-{short}", loader=f"pmlb-dataset:{dataset}",
                    name_en=f"Feynman {short.replace('_', '.').upper()}",
                    name_es=f"Feynman {short.replace('_', '.').upper()}",
                ))
        elif case.loader == "pmlb:strogatz":
            for dataset in STROGATZ_SELECTION:
                short = dataset.replace("strogatz_", "").lower()
                out.append(replace(
                    case, id=f"strogatz-{short}", loader=f"pmlb-dataset:{dataset}",
                    name_en=f"Strogatz {short}", name_es=f"Strogatz {short}",
                ))
        else:
            out.append(case)
    return out


def _quick(case: Case) -> Case:
    """A reduced budget for a smoke run. Never used for published numbers."""
    variants = tuple(
        replace(v, config=replace(v.config, population=60, generations=8))
        for v in case.variants[:3]
    )
    return replace(case, variants=variants)


def run_case(case: Case, *, seed: int = 0, noise: float = 0.0, quick: bool = False) -> dict:
    """Run every stage for one case and write its artifact and manifest."""
    if quick:
        case = _quick(case)

    prepared = preprocess_stage.run(case, noise=noise, seed=seed, max_rows=600 if quick else 4000)
    features = features_stage.run(prepared)
    trained = train_stage.run(prepared, features, case, seed=seed)
    inferred = infer_stage.run(prepared, trained)
    scores = evaluate_stage.run(prepared, trained, inferred, truth=None, seed=seed)

    certificate = None
    if not quick and prepared.n_inputs <= 3:
        # The completeness certificate is only affordable, and only meaningful, on a small input
        # space. Where it does not run, the app says so rather than showing an empty panel.
        exhaustive = train_stage.run_certificate(prepared, max_nodes=6)
        best = exhaustive.expressions[exhaustive.best_index]
        from .model.expr import to_infix

        certificate = {
            "statement": exhaustive.certificate.statement,
            "caveats": list(exhaustive.certificate.caveats),
            "complete": exhaustive.certificate.complete,
            "n_enumerated": exhaustive.certificate.n_enumerated,
            "n_admissible": exhaustive.certificate.n_admissible,
            "max_nodes": exhaustive.certificate.max_nodes,
            "best_infix": to_infix(best, prepared.dataset.input_keys),
            "best_mse": round(float(exhaustive.losses[exhaustive.best_index]), 10),
        }

    run = export_stage.build_run(case, prepared, features, trained, inferred, scores,
                                 seed=seed, truth=None, certificate=certificate)
    manifest = export_stage.build_manifest(case, prepared, features, scores, seed=seed,
                                           artifact_relative=f"{case.id}/run.json",
                                           artifact_bytes=0)
    _artifact, _manifest, size = export_stage.write(
        case, run, manifest, derived_dir=DERIVED, manifests_dir=MANIFESTS
    )
    return {
        "case_id": case.id,
        "category": case.category,
        "manifest_path": f"manifests/{case.id}.json",
        "artifact_path": f"{case.id}/run.json",
        "bytes": size,
        "n_variants": len(trained),
        "summary": evaluate_stage.summarise(scores),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="symlab.pipeline")
    parser.add_argument("case", nargs="?", default="all")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--quick", action="store_true",
                        help="reduced budget; never for published numbers")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--expand", action="store_true",
                        help="expand the physics suites into one case per problem")
    args = parser.parse_args()

    cases = expand_suites(list_cases()) if args.expand else list_cases()

    if args.list:
        print(f"{len(cases)} cases, contract schema {SCHEMA_VERSION}")
        for case in cases:
            print(f"  {case.category}  {case.id:30s} {len(case.variants)} variants  {case.name_en[:52]}")
        print(json.dumps(coverage_summary(), indent=2))
        return 0

    if args.case != "all":
        cases = [c for c in cases if c.id == args.case]
        if not cases:
            print(f"unknown case: {args.case}")
            return 1

    entries: list[dict] = []
    failures: list[tuple[str, str]] = []
    started = time.perf_counter()
    for case in cases:
        case_started = time.perf_counter()
        try:
            entry = run_case(case, seed=args.seed, noise=args.noise, quick=args.quick)
            entries.append(entry)
            elapsed = time.perf_counter() - case_started
            rate = entry["summary"].get("accuracy_solution_rate")
            print(f"  {case.id:30s} {entry['n_variants']:2d} var {entry['bytes']/1024:8.1f} KB "
                  f"{elapsed:7.1f}s  acc-rate {rate}")
        except Exception as error:  # noqa: BLE001 - one failing case must not abort the bake
            failures.append((case.id, f"{type(error).__name__}: {error}"))
            print(f"  {case.id:30s} FAILED  {type(error).__name__}: {str(error)[:70]}")

    if entries:
        index = export_stage.build_index(entries, coverage_summary())
        MANIFESTS.mkdir(parents=True, exist_ok=True)
        (MANIFESTS / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
        total_kb = sum(e["bytes"] for e in entries) / 1024
        print(f"\n  index -> manifests/index.json  ({len(entries)} cases, {total_kb:.0f} KB total)")

    print(f"  total {time.perf_counter() - started:.1f}s")
    if failures:
        print(f"\n  {len(failures)} FAILED:")
        for case_id, message in failures:
            print(f"    {case_id}: {message}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
