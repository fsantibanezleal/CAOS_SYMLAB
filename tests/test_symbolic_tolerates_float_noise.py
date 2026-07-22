"""The symbolic test must not call one unit in the last place a different law.

It did. `symbolic_equivalence` simplified `candidate - truth` and tested `== 0`, which with floating
coefficients is bit-exact. The sparse arm returned `1 * (mu * Nn)` on `feynman-i_12_1`, the law, with
a least-squares coefficient 2.2e-16 away from 1. The numerical test agreed with the truth to a
maximum relative error of 7.6e-16, and the artifact published "structure NOT recovered" beside a
printed expression identical to the truth, on the product's headline measurement.

The counterpart risk is forgiving too much: a tolerance loose enough to accept a coefficient a search
got genuinely wrong would manufacture recoveries. So both directions are pinned here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from symlab.model.expr import Node  # noqa: E402
from symlab.stages.evaluate import symbolic_equivalence  # noqa: E402

VARIABLES = ["a", "b"]
TRUTH = Node.call("mul", Node.var(0), Node.var(1))


def _scaled(coefficient: float) -> Node:
    return Node.call("mul", Node.const(coefficient), TRUTH)


@pytest.mark.parametrize(
    "coefficient",
    [1.0, 1.0 + 2.220446049250313e-16, 1.0 - 2.220446049250313e-16, 1.0 + 1e-13],
    ids=["exact", "plus-one-ulp", "minus-one-ulp", "1e-13"],
)
def test_float_noise_is_still_the_same_law(coefficient: float):
    verdict, error = symbolic_equivalence(_scaled(coefficient), TRUTH, VARIABLES)
    assert verdict is True, (
        f"a coefficient {coefficient - 1:.1e} away from 1 was called a different structure "
        f"(error: {error!r}). That is floating-point noise, not a finding about the method."
    )


@pytest.mark.parametrize(
    "coefficient",
    [1.0 + 1e-9, 1.01, 0.99, 2.0],
    ids=["1e-9", "plus-1pc", "minus-1pc", "double"],
)
def test_a_real_difference_is_still_rejected(coefficient: float):
    """The tolerance must not manufacture recoveries. 1e-9 is far outside float noise."""
    verdict, _ = symbolic_equivalence(_scaled(coefficient), TRUTH, VARIABLES)
    assert verdict is False, (
        f"a coefficient {coefficient - 1:.1e} away from 1 was accepted as the same law. The "
        "rounding is there to ignore last-bit noise, not to widen what counts as recovery."
    )


def test_a_different_structure_is_rejected():
    """The obvious case, asserted so the rounding cannot ever swallow it."""
    verdict, _ = symbolic_equivalence(Node.call("add", Node.var(0), Node.var(1)), TRUTH, VARIABLES)
    assert verdict is False, "a sum was accepted as equivalent to a product"


def test_the_rounding_is_documented_where_it_is_set():
    """The constant carries the measurement that forced it, so it cannot be tuned casually."""
    from symlab.stages import evaluate

    assert evaluate.SYMBOLIC_COEFFICIENT_DIGITS >= 10, (
        "fewer than 10 significant digits starts forgiving differences a search could mean"
    )
