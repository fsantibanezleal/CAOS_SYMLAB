"""Every generator truth must reproduce its own generator, and every absence must have a reason.

The truth is the yardstick the recovery rate is measured against. A wrong one does not fail loudly:
it publishes a confident "structure not recovered" against a method that recovered the law
perfectly. So each expression is evaluated over the generator's own sampled rows and required to
agree to 1e-9 relative.

The second test is the one that closes the hole this file was written for. Six generators carried no
truth at all, so their cases reported recovery as "not checkable" while the case summaries claimed a
known ground truth. Nothing failed, because an absent truth and an unscoreable case look identical
from the outside. Now an absent truth must be justified in the source, and the justification has to
be long enough to be an actual reason rather than a flag.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from symlab.cases import generators as generators_module
from symlab.cases.generators import GENERATORS, make_dataset
from symlab.model.expr import evaluate

ROWS = 3000
TOLERANCE = 1e-9

WITH_TRUTH = sorted(k for k, g in GENERATORS.items() if g.truth_node is not None)
WITHOUT_TRUTH = sorted(k for k, g in GENERATORS.items() if g.truth_node is None)


@pytest.mark.parametrize("key", WITH_TRUTH)
def test_truth_reproduces_its_generator(key: str) -> None:
    generator = GENERATORS[key]
    X, y = make_dataset(generator, n_rows=ROWS, seed=0, noise=0.0)

    predicted = evaluate(generator.truth_node(), X)
    assert np.all(np.isfinite(predicted)), f"{key}: truth produced non-finite values"

    relative = np.abs(predicted - y) / np.maximum(np.abs(y), 1e-12)
    worst = float(np.max(relative))
    assert worst < TOLERANCE, (
        f"{key}: truth disagrees with its own generator, max relative error {worst:.3e}. "
        "A wrong truth reports a false 'not recovered' against a method that succeeded."
    )


@pytest.mark.parametrize("key", WITHOUT_TRUTH)
def test_a_missing_truth_carries_a_written_reason(key: str) -> None:
    """An unscoreable case must say WHY, in the source, next to the generator.

    Without this, "we did not write the truth" is indistinguishable from "the law cannot be
    written", and only one of those is a statement about the method.
    """
    source = inspect.getsource(generators_module)
    marker = f'id="{key}",'
    start = source.index(marker)
    block = source[start : start + 2500]
    assert "NO truth node" in block, (
        f"{key} has no truth and no recorded reason. Either write the truth or write why it "
        "cannot be written."
    )
    reason_start = block.index("NO truth node")
    reason = block[reason_start : reason_start + 600]
    assert len(reason.split()) > 25, f"{key}: the reason must be an explanation, not a label"


def test_regime_is_declared_wherever_a_truth_exists() -> None:
    """A recovery claim without its regime is two different claims wearing one word.

    "structure" means the physical parameters were input columns so only the form was unknown;
    "structure+constants" means the numbers had to be found too, which is materially harder.
    """
    undeclared = [
        key
        for key in WITH_TRUTH
        if GENERATORS[key].regime not in {"structure", "structure+constants"}
    ]
    assert not undeclared, f"these carry a truth but no meaningful regime: {undeclared}"


def test_coverage_is_stated_rather_than_assumed() -> None:
    """A canary on the counts, so a silently dropped truth is visible in the diff."""
    assert len(WITH_TRUTH) == 17, (
        f"expected 17 generators with a verified truth, found {len(WITH_TRUTH)}: {WITH_TRUTH}"
    )
    assert WITHOUT_TRUTH == ["wind-power-curve"], (
        f"the only generator without a truth should be the piecewise wind curve, found "
        f"{WITHOUT_TRUTH}"
    )
