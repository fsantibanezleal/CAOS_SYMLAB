"""Interval arithmetic guards: reject an invalid expression BEFORE evaluating it.

The classical genetic-programming workaround for division by zero and for the logarithm of a
negative number is a "protected" operator that returns some arbitrary value in the bad case. Keijzer
showed why that is the wrong trade: protection makes every candidate evaluable, so the search never
learns to avoid the singularity, and the resulting expression is only meaningful on the sample it
was fitted to. The moment you extrapolate, the protection is gone and the model diverges.

The alternative implemented here propagates the interval of each input through the expression. If
the interval reaching a division contains zero, or the interval reaching a logarithm or a square
root extends below zero, the candidate is rejected outright and never enters the population. No
evaluation is wasted on it and no unsound expression can survive to the Pareto front.

This is the second rung of the lab's ladder, and the dossier's judgement was that it produces the
largest quality gain per line of code in the whole classical spine, while being almost absent from
tutorial implementations.

Reference transcribed from the persisted research: Keijzer, M. (2003). Improving symbolic regression
with interval arithmetic and linear scaling. EuroGP 2003, Lecture Notes in Computer Science 2610,
pages 70-82, doi:10.1007/3-540-36599-0_7.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .expr import KIND_CONST, KIND_VAR, Node

INF = float("inf")


@dataclass(frozen=True)
class Interval:
    """A closed interval. An empty or non-finite interval marks the candidate as rejected."""

    lo: float
    hi: float

    @property
    def valid(self) -> bool:
        return not (math.isnan(self.lo) or math.isnan(self.hi)) and self.lo <= self.hi

    @property
    def contains_zero(self) -> bool:
        return self.lo <= 0.0 <= self.hi

    @property
    def is_negative_anywhere(self) -> bool:
        return self.lo < 0.0

    def __repr__(self) -> str:  # pragma: no cover, debugging aid
        return f"[{self.lo:.4g}, {self.hi:.4g}]"


INVALID = Interval(float("nan"), float("nan"))


def _bounds(*values: float) -> Interval:
    finite = [v for v in values if not math.isnan(v)]
    if not finite:
        return INVALID
    return Interval(min(finite), max(finite))


def from_data(X: np.ndarray, *, margin: float = 0.0) -> list[Interval]:
    """Per-column intervals from the training rows.

    `margin` widens each interval by a fraction of its width. Widening is what turns the guard from
    "safe on the training sample" into "safe on the neighbourhood we intend to extrapolate into",
    and the extrapolation track of this lab depends on it.
    """
    out: list[Interval] = []
    for j in range(X.shape[1]):
        col = X[:, j]
        lo = float(np.min(col))
        hi = float(np.max(col))
        if margin:
            width = hi - lo
            lo -= margin * width
            hi += margin * width
        out.append(Interval(lo, hi))
    return out


def propagate(node: Node, inputs: list[Interval]) -> Interval:
    """Propagate intervals through the expression. An invalid result means: reject this candidate."""
    if node.kind == KIND_CONST:
        v = float(node.value)  # type: ignore[arg-type]
        return Interval(v, v)
    if node.kind == KIND_VAR:
        idx = int(node.var_index)  # type: ignore[arg-type]
        if idx >= len(inputs):
            return INVALID
        return inputs[idx]

    kids = [propagate(c, inputs) for c in node.children]
    for k in kids:
        if not k.valid:
            return INVALID
    op = node.op

    if op == "add":
        a, b = kids
        return Interval(a.lo + b.lo, a.hi + b.hi)
    if op == "sub":
        a, b = kids
        return Interval(a.lo - b.hi, a.hi - b.lo)
    if op == "mul":
        a, b = kids
        return _bounds(a.lo * b.lo, a.lo * b.hi, a.hi * b.lo, a.hi * b.hi)
    if op == "div":
        a, b = kids
        if b.contains_zero:
            return INVALID  # the whole point: no protected division
        return _bounds(a.lo / b.lo, a.lo / b.hi, a.hi / b.lo, a.hi / b.hi)
    if op == "inv":
        (a,) = kids
        if a.contains_zero:
            return INVALID
        return _bounds(1.0 / a.lo, 1.0 / a.hi)
    if op == "neg":
        (a,) = kids
        return Interval(-a.hi, -a.lo)
    if op == "abs":
        (a,) = kids
        if a.contains_zero:
            return Interval(0.0, max(abs(a.lo), abs(a.hi)))
        return _bounds(abs(a.lo), abs(a.hi))
    if op == "square":
        (a,) = kids
        if a.contains_zero:
            return Interval(0.0, max(a.lo * a.lo, a.hi * a.hi))
        return _bounds(a.lo * a.lo, a.hi * a.hi)
    if op == "sqrt":
        (a,) = kids
        if a.is_negative_anywhere:
            return INVALID
        return Interval(math.sqrt(a.lo), math.sqrt(a.hi))
    if op == "log":
        (a,) = kids
        if a.lo <= 0.0:
            return INVALID
        return Interval(math.log(a.lo), math.log(a.hi))
    if op == "exp":
        (a,) = kids
        if a.hi > 700.0:  # float64 overflows above roughly exp(709)
            return INVALID
        return Interval(math.exp(a.lo), math.exp(a.hi))
    if op in ("sin", "cos"):
        (a,) = kids
        # Exact only when the interval is narrower than a period; otherwise the safe bound is [-1, 1],
        # which is correct and is all the guard needs.
        if a.hi - a.lo >= 2.0 * math.pi:
            return Interval(-1.0, 1.0)
        fn = math.sin if op == "sin" else math.cos
        samples = [fn(a.lo), fn(a.hi)]
        # include any extremum falling inside the interval
        k0 = math.floor(a.lo / (math.pi / 2.0))
        k1 = math.ceil(a.hi / (math.pi / 2.0))
        for k in range(int(k0), int(k1) + 1):
            x = k * math.pi / 2.0
            if a.lo <= x <= a.hi:
                samples.append(fn(x))
        return _bounds(*samples)
    if op == "tanh":
        (a,) = kids
        return Interval(math.tanh(a.lo), math.tanh(a.hi))

    return INVALID


def admissible(node: Node, inputs: list[Interval], *, max_abs: float = 1e12) -> bool:
    """True when the expression is defined and bounded across the whole input box.

    `max_abs` rejects expressions that are technically defined but numerically useless, which keeps
    the population free of candidates whose loss is finite only by luck of the sample.
    """
    result = propagate(node, inputs)
    if not result.valid:
        return False
    if not (math.isfinite(result.lo) and math.isfinite(result.hi)):
        return False
    return max(abs(result.lo), abs(result.hi)) <= max_abs
