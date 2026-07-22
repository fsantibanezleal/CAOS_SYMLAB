"""Linear scaling: the cheapest large win in classical symbolic regression.

Given a candidate expression `f`, the search does not have to find the right multiplicative and
additive constants by evolution. For a squared-error objective they have a closed form:

    a = cov(y, f) / var(f)          slope
    b = mean(y) - a * mean(f)       intercept

and the scaled candidate `a * f + b` is optimal in `a` and `b` by construction. The effect is that
the search is freed to look for the SHAPE of the relationship, which is the part evolution is
actually good at, instead of burning generations tuning two numbers it could have solved exactly.

Keijzer's result is that this substantially improves both the speed and the final quality of tree
genetic programming, and the dossier's judgement is that it remains the single largest quality gain
per line of code in the classical spine.

Two honesty points this module records rather than hides:

1. Scaling changes what "the discovered expression" means. The lab reports the SCALED expression,
   with `a` and `b` folded in as explicit constants, because reporting an unscaled skeleton and
   quietly scoring it scaled would inflate every number.
2. When `var(f)` is zero the candidate is constant and carries no information; slope is undefined.
   That case is reported, not silently replaced by a fitted mean, because a constant model scoring
   well means the target has no signal the primitives can reach.

Reference transcribed from the persisted research: Keijzer, M. (2003). Improving symbolic regression
with interval arithmetic and linear scaling. EuroGP 2003, doi:10.1007/3-540-36599-0_7.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .expr import Node


@dataclass(frozen=True)
class Scaling:
    """The closed-form optimal affine correction for one candidate."""

    slope: float
    intercept: float
    degenerate: bool = False

    def apply(self, values: np.ndarray) -> np.ndarray:
        return self.slope * values + self.intercept


IDENTITY = Scaling(1.0, 0.0)


def fit(y: np.ndarray, f: np.ndarray, *, var_floor: float = 1e-12) -> Scaling:
    """Closed-form least-squares slope and intercept of `y` on `f`.

    A degenerate candidate (near-zero variance) is reported with slope 0 and the mean of `y` as the
    intercept, and `degenerate=True` so the caller can score it as the trivial constant model it is
    rather than as a discovery.
    """
    f_mean = float(np.mean(f))
    y_mean = float(np.mean(y))
    f_centered = f - f_mean
    denominator = float(np.dot(f_centered, f_centered))
    if denominator <= var_floor:
        return Scaling(0.0, y_mean, degenerate=True)
    slope = float(np.dot(f_centered, y - y_mean)) / denominator
    return Scaling(slope, y_mean - slope * f_mean)


def fold_into_expression(node: Node, scaling: Scaling, *, tol: float = 1e-12) -> Node:
    """Rewrite `f` as `a*f + b` so the exported expression is the one that was actually scored.

    Terms that are exactly neutral are omitted, so an unscaled candidate is not decorated with
    `1.0 *` and `+ 0.0`, which would inflate its complexity for no reason.
    """
    out = node
    if abs(scaling.slope - 1.0) > tol:
        out = Node.call("mul", Node.const(scaling.slope), out)
    if abs(scaling.intercept) > tol:
        out = Node.call("add", out, Node.const(scaling.intercept))
    return out
