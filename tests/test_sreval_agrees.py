"""The published scorer and the browser-lane fallback must produce identical numbers.

`sreval` was extracted as its own MIT package because telling "the method failed" apart from "the
scorer failed" is a general problem, not one specific to this lab. For a while the package was
imported at the top of `stages/evaluate.py`, pinned in `requirements-precompute.txt`, and documented
as "used here", while nothing in the module ever referenced it. The dependency was decoration.

It is called now, with the local implementation kept as the fallback for Pyodide, which never
installs it. That arrangement is only honest if the two agree: a browser run and an offline run
would otherwise report different structural distances for the same pair of expressions, and the app
tells the reader they are the same engine.

These tests skip when sreval is absent, because the browser lane is a supported configuration.
"""

from __future__ import annotations

import numpy as np
import pytest

from symlab.cases.generators import GENERATORS
from symlab.model.expr import Node
from symlab.stages.evaluate import HAS_SREVAL, _canonical_labels, structural_distance

pytestmark = pytest.mark.skipif(not HAS_SREVAL, reason="sreval is not installed in this lane")

TRUTHS = {key: g.truth_node() for key, g in GENERATORS.items() if g.truth_node is not None}
KEYS = sorted(TRUTHS)


def _sreval_distance(a: Node, b: Node) -> float:
    from sreval.equivalence import structural_distance as published

    return round(min(1.0, float(published(_canonical_labels(a), _canonical_labels(b)).distance)), 6)


@pytest.mark.parametrize("key", KEYS)
def test_a_truth_has_zero_distance_from_itself(key: str) -> None:
    assert structural_distance(TRUTHS[key], TRUTHS[key]) == 0.0


@pytest.mark.parametrize("pair", list(zip(KEYS, KEYS[1:])), ids=lambda p: f"{p[0]}|{p[1]}")
def test_local_and_published_agree_on_real_truths(pair: tuple[str, str]) -> None:
    a, b = TRUTHS[pair[0]], TRUTHS[pair[1]]
    assert structural_distance(a, b) == pytest.approx(_sreval_distance(a, b), abs=1e-9)


def test_they_agree_on_the_shapes_that_matter() -> None:
    """The cases where a distance metric usually goes wrong."""
    x, y = Node.var(0), Node.var(1)
    cases = {
        # Constants are collapsed, so numeric drift is not scored as a structural difference.
        "constant drift only": (
            Node.call("mul", Node.const(2.0), x),
            Node.call("mul", Node.const(9.9), x),
        ),
        "swapped variables": (Node.call("mul", x, y), Node.call("mul", y, x)),
        "leaf against deep": (x, Node.call("exp", Node.call("log", Node.call("sqrt", x)))),
        "both bare constants": (Node.const(1.0), Node.const(2.0)),
    }
    for label, (a, b) in cases.items():
        assert structural_distance(a, b) == pytest.approx(_sreval_distance(a, b), abs=1e-9), label


def test_constant_drift_alone_is_not_a_structural_difference() -> None:
    """The property the collapsing exists for, asserted rather than assumed.

    Recovering the right FORM with a different constant is a different result from recovering the
    wrong form, and a distance that conflated them would make the recovery rate meaningless.
    """
    x = Node.var(0)
    same_shape = structural_distance(
        Node.call("mul", Node.const(2.0), x), Node.call("mul", Node.const(1e6), x)
    )
    assert same_shape == 0.0


def test_the_distance_is_bounded_and_symmetric() -> None:
    rng = np.random.default_rng(0)
    for _ in range(20):
        a, b = (TRUTHS[KEYS[int(rng.integers(len(KEYS)))]] for _ in range(2))
        forward, backward = structural_distance(a, b), structural_distance(b, a)
        assert 0.0 <= forward <= 1.0
        assert forward == pytest.approx(backward, abs=1e-9)
