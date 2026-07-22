"""Stage 1: load a case, apply the ingestion contract, and split it.

The split is where a symbolic-regression lab either earns its numbers or quietly inflates them, so
it is done here, once, and recorded in the manifest rather than left to each downstream stage.

Three splits, not two:

- **train**, what the search sees.
- **test**, held out inside the same input region. This answers "does it generalise to unseen rows".
- **extrapolation**, held out OUTSIDE the training support. This answers a different and much harder
  question: "does the discovered form remain sensible where no data constrained it". The benchmark
  literature is explicit that extrapolation is where every method degrades, and it is under-served by
  the standard suites, which is exactly why this lab makes it a first-class split rather than an
  afterthought.

The extrapolation split is built by holding out the rows in the tails of the input with the widest
range, so the training region is genuinely an interior box. Where a case is too small for that to
leave a usable training set, the split is skipped and the manifest says so, rather than being faked.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..cases.generators import GENERATORS, make_dataset
from ..cases.registry import Case
from ..io.loaders import LOADERS, LoadedDataset, load_pmlb

#: Fraction of rows held out for the interior test split.
TEST_FRACTION = 0.25

#: Fraction of rows held out, from the tails, for the extrapolation split.
EXTRAPOLATION_FRACTION = 0.15

#: Below this many rows the extrapolation split is skipped rather than faked.
MIN_ROWS_FOR_EXTRAPOLATION = 120


@dataclass
class PreparedCase:
    """A case after loading, contract checks and splitting."""

    case_id: str
    dataset: LoadedDataset
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    X_extrap: np.ndarray | None
    y_extrap: np.ndarray | None
    split_note: str
    contract_report: dict = field(default_factory=dict)
    noise: float = 0.0

    @property
    def n_inputs(self) -> int:
        return int(self.X_train.shape[1])


def _contract_check(dataset: LoadedDataset) -> dict:
    """The ingestion contract: what must hold before a dataset is allowed into the pipeline.

    Violations are REPORTED, and the fatal ones raise. A dataset that silently passes a contract it
    does not satisfy is worse than no contract, because every number downstream then carries an
    assumption nobody stated.
    """
    problems: list[str] = []
    warnings: list[str] = []

    if dataset.X.shape[0] < 20:
        problems.append(f"only {dataset.X.shape[0]} rows; too few for a train/test split")
    if not np.all(np.isfinite(dataset.X)):
        problems.append(f"{int(np.sum(~np.isfinite(dataset.X)))} non-finite values in the inputs")
    if not np.all(np.isfinite(dataset.y)):
        problems.append(f"{int(np.sum(~np.isfinite(dataset.y)))} non-finite values in the target")
    if float(np.var(dataset.y)) <= 0:
        problems.append("the target has zero variance; there is nothing to model")

    constant_inputs = [
        dataset.input_keys[j]
        for j in range(dataset.X.shape[1])
        if float(np.var(dataset.X[:, j])) <= 0
    ]
    if constant_inputs:
        warnings.append(
            f"constant input column(s) {constant_inputs}: they cannot contribute and will inflate "
            "any count of irrelevant features carried into the result"
        )

    # A duplicated target value repeated across many rows is the signature of the broadcast trap the
    # flotation dataset carries. Detecting it generically means the next dataset with the same defect
    # is caught before it produces a leaked number.
    unique_targets = len(np.unique(np.round(dataset.y, 10)))
    repeat_ratio = dataset.y.shape[0] / max(1, unique_targets)
    if repeat_ratio > 3.0:
        warnings.append(
            f"the target takes only {unique_targets} distinct values across {dataset.y.shape[0]} rows "
            f"({repeat_ratio:.1f} repeats each). If those repeats come from a coarser measurement grid, "
            "fitting at this resolution leaks the target."
        )

    if problems:
        raise ValueError(f"{dataset.id}: ingestion contract failed: " + "; ".join(problems))

    return {
        "n_rows": int(dataset.X.shape[0]),
        "n_inputs": int(dataset.X.shape[1]),
        "input_keys": list(dataset.input_keys),
        "target_key": dataset.target_key,
        "distinct_target_values": int(unique_targets),
        "target_repeat_ratio": round(float(repeat_ratio), 3),
        "constant_inputs": constant_inputs,
        "warnings": warnings,
        "defects_applied": list(dataset.defects_applied),
        "licence": dataset.licence,
        "redistribution": dataset.redistribution,
        "citation": dataset.citation,
    }


def load_case_dataset(case: Case, *, noise: float = 0.0, seed: int = 0,
                      max_rows: int | None = 4000) -> LoadedDataset:
    """Resolve a case to a dataset, whatever kind of source it names.

    `max_rows` subsamples deterministically. Several sources ship 100,000 rows, and evaluating a
    population of candidates against all of them, every generation, spends the entire budget on rows
    that carry no additional information about a smooth low-dimensional law. The subsample size is
    recorded, so the choice is visible rather than hidden.
    """
    if case.is_generator:
        generator = GENERATORS[case.loader.split(":", 1)[1]]
        X, y = make_dataset(generator, n_rows=case.n_rows or 400, seed=seed, noise=noise)
        return LoadedDataset(
            id=case.id, name=generator.name, X=X, y=y,
            input_keys=generator.input_keys,
            input_display=[i.display for i in generator.inputs],
            input_units=[i.unit for i in generator.inputs],
            input_dims=generator.input_dims,
            target_key=generator.target.key,
            target_display=generator.target.display,
            target_unit=generator.target.unit,
            target_dims=generator.target.dims,
            source_id=generator.id,
            citation=generator.source,
            licence="MIT (generator authored in this repository)",
            redistribution="mirror",
            real_or_synthetic="synthetic",
            ground_truth_latex=generator.truth_latex,
            notes=generator.recovery_target,
        )

    if case.loader.startswith("pmlb-dataset:"):
        dataset = load_pmlb(case.loader.split(":", 1)[1])
        if max_rows is not None and dataset.X.shape[0] > max_rows:
            rng = np.random.default_rng(seed)
            keep = np.sort(rng.choice(dataset.X.shape[0], size=max_rows, replace=False))
            dataset.X, dataset.y = dataset.X[keep], dataset.y[keep]
            dataset.defects_applied = dataset.defects_applied + [
                f"Deterministically subsampled to {max_rows} of {dataset.X.shape[0]} rows (seed "
                f"{seed}). The source ships 100,000 rows of a smooth low-dimensional law; the extra "
                "rows carry no additional information about its structure and would spend the whole "
                "search budget on redundancy."
            ]
        return dataset

    if case.loader.startswith("pmlb:"):
        raise ValueError(
            f"{case.id}: this case is a SUITE over many problems and is expanded by the pipeline "
            "with --expand, not loaded as one dataset."
        )

    dataset = LOADERS[case.loader]()
    if max_rows is not None and dataset.X.shape[0] > max_rows:
        rng = np.random.default_rng(seed)
        keep = np.sort(rng.choice(dataset.X.shape[0], size=max_rows, replace=False))
        dataset.X = dataset.X[keep]
        dataset.y = dataset.y[keep]
        dataset.defects_applied = dataset.defects_applied + [
            f"Deterministically subsampled to {max_rows} of the available rows (seed {seed}) to keep "
            "the search budget on the structure rather than on redundant rows."
        ]
    return dataset


def run(case: Case, *, noise: float = 0.0, seed: int = 0,
        max_rows: int | None = 4000) -> PreparedCase:
    """Load, contract-check and split one case."""
    dataset = load_case_dataset(case, noise=noise, seed=seed, max_rows=max_rows)
    report = _contract_check(dataset)

    rng = np.random.default_rng(seed + 17)
    n = dataset.X.shape[0]

    extrap_index: np.ndarray | None = None
    split_note = "train/test only; too few rows for a meaningful extrapolation split"

    if n >= MIN_ROWS_FOR_EXTRAPOLATION:
        # Hold out the tails of the widest-ranging input, so training sees an interior box and the
        # extrapolation split is genuinely outside the support rather than merely unseen.
        spans = dataset.X.max(axis=0) - dataset.X.min(axis=0)
        pivot = int(np.argmax(spans))
        order = np.argsort(dataset.X[:, pivot])
        tail = max(1, int(EXTRAPOLATION_FRACTION * n / 2))
        extrap_index = np.concatenate([order[:tail], order[-tail:]])
        split_note = (
            f"extrapolation split holds out the lowest and highest {tail} rows of "
            f"'{dataset.input_keys[pivot]}', so the training region is an interior box and the "
            "extrapolation rows lie outside the support the search ever saw"
        )

    interior = np.setdiff1d(np.arange(n), extrap_index if extrap_index is not None else np.array([], dtype=int))
    shuffled = rng.permutation(interior)
    n_test = max(1, int(TEST_FRACTION * len(shuffled)))
    test_index = shuffled[:n_test]
    train_index = shuffled[n_test:]

    return PreparedCase(
        case_id=case.id,
        dataset=dataset,
        X_train=dataset.X[train_index], y_train=dataset.y[train_index],
        X_test=dataset.X[test_index], y_test=dataset.y[test_index],
        X_extrap=dataset.X[extrap_index] if extrap_index is not None else None,
        y_extrap=dataset.y[extrap_index] if extrap_index is not None else None,
        split_note=split_note,
        contract_report=report | {
            "n_train": int(len(train_index)),
            "n_test": int(len(test_index)),
            "n_extrapolation": int(len(extrap_index)) if extrap_index is not None else 0,
        },
        noise=noise,
    )
