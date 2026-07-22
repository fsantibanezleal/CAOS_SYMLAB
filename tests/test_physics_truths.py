"""Every published physical law must reproduce its own dataset before it is allowed to score.

A wrong truth does not fail loudly. It produces a confident "structure not recovered" against a
method that recovered the law perfectly, and the artifact then publishes that verdict as a
measurement. So each expression is evaluated over real rows of its own dataset and required to
agree to 1e-9 relative, which is the same bar the generator truths are held to.

These tests skip rather than fail when a dataset has not been fetched, because the raw data is
deliberately out of git (ADR-0055). They do NOT skip when the file is present and the law
disagrees: that is the failure this file exists to catch.
"""

from __future__ import annotations

import gzip

import numpy as np
import pytest

from symlab.cases.physics_truths import (
    FEYNMAN_TRUTHS,
    IDEALISED_NOT_RECOVERABLE,
    INEXPRESSIBLE,
    MEASURED_TRUTHS,
    measured_truth_for,
    truth_for,
)
from symlab.io.sources import FEYNMAN_SELECTION, SOURCES
from symlab.model.expr import evaluate

MAX_ROWS = 3000
TOLERANCE = 1e-9


def _load(dataset: str) -> tuple[list[str], np.ndarray, np.ndarray]:
    source = SOURCES[f"pmlb-{dataset}"]
    if not source.path.exists():
        pytest.skip(f"{dataset} not fetched; raw data is out of git by ADR-0055")
    with gzip.open(source.path, "rt", encoding="utf-8") as handle:
        header = handle.readline().strip().split("\t")
        rows = np.loadtxt(handle, delimiter="\t", max_rows=MAX_ROWS)
    return header[:-1], rows[:, :-1], rows[:, -1]


@pytest.mark.parametrize("dataset", sorted(FEYNMAN_TRUTHS))
def test_truth_reproduces_its_dataset(dataset: str) -> None:
    keys, X, y = _load(dataset)
    node = truth_for(dataset, keys)
    assert node is not None, f"{dataset} has a builder but truth_for returned None"

    predicted = evaluate(node, X)
    assert np.all(np.isfinite(predicted)), f"{dataset} truth produced non-finite values"

    relative = np.abs(predicted - y) / np.maximum(np.abs(y), 1e-12)
    worst = float(np.max(relative))
    assert worst < TOLERANCE, (
        f"{dataset} truth disagrees with its own dataset: max relative error {worst:.3e}. "
        "A wrong truth reports a false 'not recovered' against a method that succeeded."
    )


@pytest.mark.parametrize("dataset", sorted(INEXPRESSIBLE))
def test_inexpressible_laws_get_no_truth_and_a_reason(dataset: str) -> None:
    """A law outside the operator set must yield no truth, with the reason published.

    Approximating it would let the app show a recovery verdict that describes the primitive set
    rather than the method.
    """
    assert dataset not in FEYNMAN_TRUTHS
    assert truth_for(dataset, ["theta2", "n"]) is None
    assert len(INEXPRESSIBLE[dataset]) > 40, "the reason must be stated, not merely flagged"


def test_every_selected_dataset_is_accounted_for() -> None:
    """No dataset may be silently absent from both tables.

    Without this, adding a problem to the selection would quietly produce a case whose recovery is
    unscoreable for no recorded reason, which is exactly the state this module was written to end.
    """
    unaccounted = [
        dataset
        for dataset in FEYNMAN_SELECTION
        if dataset not in FEYNMAN_TRUTHS and dataset not in INEXPRESSIBLE
    ]
    assert not unaccounted, (
        f"these datasets have neither a truth nor a recorded reason: {unaccounted}"
    )


def test_truth_binds_by_column_name_not_position() -> None:
    """A reordered source must rebind correctly, or refuse, never bind to the wrong symbol."""
    forward = truth_for("feynman_I_12_1", ["mu", "Nn"])
    reversed_ = truth_for("feynman_I_12_1", ["Nn", "mu"])
    assert forward is not None and reversed_ is not None

    X = np.array([[2.0, 5.0]])
    # mu=2, Nn=5 gives 10 either way ONLY if each expression read its own column order.
    assert float(evaluate(forward, X)[0]) == pytest.approx(10.0)
    assert float(evaluate(reversed_, X)[0]) == pytest.approx(10.0)

    # A column set that does not carry the expected names must refuse rather than guess.
    assert truth_for("feynman_I_12_1", ["a", "b"]) is None


# ---------------------------------------------------------------------------- measured identities


@pytest.mark.parametrize("loader", sorted(MEASURED_TRUTHS))
def test_measured_identity_holds_on_the_real_rows(loader: str) -> None:
    """An exact identity claimed over MEASURED data must actually hold over that data.

    The tolerance is per case and describes the RECORDING, not the law: published percentages are
    given to a fixed number of decimals, so a definition that is exact in principle shows a small
    residual in the file. The reason has to be written down, so "the identity is approximate" can
    never be confused with "we widened the tolerance until it passed".
    """
    from symlab.io.loaders import LOADERS

    builder, tolerance, reason = MEASURED_TRUTHS[loader]
    assert len(reason.split()) > 20, f"{loader}: the tolerance needs a written justification"

    dataset = LOADERS[loader]()
    node = measured_truth_for(loader, list(dataset.input_keys))
    assert node is not None

    predicted = evaluate(node, dataset.X)
    relative = np.abs(predicted - dataset.y) / np.maximum(np.abs(dataset.y), 1e-12)
    worst = float(np.max(relative))
    assert worst <= tolerance, (
        f"{loader}: identity misses its own data by {worst:.3e}, above the stated {tolerance:.1e}"
    )


@pytest.mark.parametrize("loader", sorted(IDEALISED_NOT_RECOVERABLE))
def test_an_idealised_reference_is_never_scored_as_a_truth(loader: str) -> None:
    """A published line the data does not follow must not become a recovery target.

    Scoring against it reports "not recovered" for expressions that describe the material BETTER
    than the reference does, which inverts the meaning of the measurement.
    """
    assert loader not in MEASURED_TRUTHS
    assert measured_truth_for(loader, ["anything"]) is None
    assert len(IDEALISED_NOT_RECOVERABLE[loader].split()) > 25
