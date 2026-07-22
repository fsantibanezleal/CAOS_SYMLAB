"""Complexity measures, and the model-selection rule that uses them.

The Pareto front of this lab is (loss, complexity), so "complexity" is not a cosmetic label; it is
one of the two axes every result is reported on, and a different choice of measure changes which
expression sits at the elbow. Three measures are implemented, and the exported payload carries all
three so a reader can see that the ranking is not an artefact of one of them.

1. **Node count.** The field default, and what the main benchmark suite uses. Its known weakness,
   stated by that suite's own authors, is that it ignores nested nonlinearity: `sin(sin(sin(x)))` and
   `x + y + z` both score 4 or so, while only one of them is hard to reason about.
2. **Weighted node count.** Each operator carries a cost reflecting how much harder it makes the
   expression to read and to trust. This is the measure the lab uses for its own Pareto elbow.
3. **Description length.** An information-theoretic count in nats, combining the cost of writing the
   structure down with the cost of the residuals. This is the measure that actually selects a single
   model, because it is the only one of the three that trades accuracy against complexity on a
   common scale instead of leaving the trade to the reader's eye.

The selection rule matters more than it looks. The benchmark literature's strongest negative result
for this lab is a transformer scoring 26.7 percent of problems at R-squared above 0.999 while
recovering the correct structure 0.00 percent of the time. Selecting the front point by best
accuracy reproduces exactly that failure. Selecting by description length is the incumbent
alternative and is what this lab uses by default.

References transcribed from the persisted research:
- Rissanen, J. (1978). Modeling by shortest data description. Automatica 14(5):465-471,
  doi:10.1016/0005-1098(78)90005-5.
- Schwarz, G. (1978). Estimating the dimension of a model. Annals of Statistics 6(2):461-464,
  doi:10.1214/aos/1176344136.
- Grunwald, P. (2007). The Minimum Description Length Principle. MIT Press.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .expr import KIND_CONST, KIND_VAR, Node, n_constants, size, walk

#: Per-operator readability cost for the weighted measure. Arithmetic is cheap, transcendental
#: functions are not, and composition of transcendental functions is what makes an expression
#: unreadable. These weights are a stated convention of this build, not a published standard, and
#: the docs say so; the unweighted count ships alongside precisely so the choice is auditable.
OPERATOR_COST: dict[str, float] = {
    "add": 1.0,
    "sub": 1.0,
    "neg": 1.0,
    "mul": 1.0,
    "div": 2.0,
    "inv": 2.0,
    "abs": 2.0,
    "square": 2.0,
    "sqrt": 3.0,
    "exp": 4.0,
    "log": 4.0,
    "sin": 4.0,
    "cos": 4.0,
    "tanh": 4.0,
}

LEAF_VAR_COST = 1.0
LEAF_CONST_COST = 1.0

#: Extra multiplier applied to a transcendental function nested inside another transcendental
#: function, which is the case the plain node count is blind to.
NESTING_PENALTY = 1.5

TRANSCENDENTAL = {"exp", "log", "sin", "cos", "tanh"}


def node_count(node: Node) -> int:
    """The field-default complexity: every node counts one."""
    return size(node)


def weighted_complexity(node: Node) -> float:
    """Readability-weighted complexity, with a penalty for nested transcendental functions."""

    def visit(n: Node, inside_transcendental: bool) -> float:
        if n.kind == KIND_VAR:
            return LEAF_VAR_COST
        if n.kind == KIND_CONST:
            return LEAF_CONST_COST
        op = str(n.op)
        cost = OPERATOR_COST.get(op, 2.0)
        if inside_transcendental and op in TRANSCENDENTAL:
            cost *= NESTING_PENALTY
        deeper = inside_transcendental or op in TRANSCENDENTAL
        return cost + sum(visit(c, deeper) for c in n.children)

    return round(visit(node, False), 4)


def structure_bits(node: Node, *, n_primitives: int, n_variables: int) -> float:
    """Nats needed to write the structure down, ignoring the constant values.

    Each node is one symbol drawn from an alphabet of (primitives + variables + "a constant"), so
    the structural cost is `n_nodes * ln(alphabet_size)`. This is the standard coding argument and it
    is deliberately crude: a sharper prior over expression shapes would be better, and the docs say
    so rather than implying this is the last word.
    """
    alphabet = max(2, n_primitives + n_variables + 1)
    return size(node) * math.log(alphabet)


def constant_bits(node: Node, *, precision_nats: float = math.log(2.0) * 16.0) -> float:
    """Nats needed to write the fitted constants down, at a stated precision.

    Charging a fixed cost per constant is what stops the search from buying accuracy with an endless
    supply of free parameters. The default of 16 bits per constant is a convention of this build and
    is recorded in the manifest so a reader can recompute the ranking under a different choice.
    """
    return n_constants(node) * precision_nats


def residual_bits(y: np.ndarray, y_pred: np.ndarray, *, sigma_floor: float = 1e-12) -> float:
    """Nats needed to code the residuals under a Gaussian model with the fitted variance.

    This is the negative log-likelihood at the maximum-likelihood variance, which reduces to
    `n/2 * (ln(2*pi*sigma^2) + 1)`.
    """
    n = int(y.shape[0])
    if n == 0:
        return 0.0
    residual = y - y_pred
    sigma_squared = max(float(np.mean(residual * residual)), sigma_floor)
    return 0.5 * n * (math.log(2.0 * math.pi * sigma_squared) + 1.0)


@dataclass(frozen=True)
class DescriptionLength:
    """The description-length decomposition, reported in full so the trade-off is visible."""

    total: float
    structure: float
    constants: float
    residuals: float


def description_length(
    node: Node,
    y: np.ndarray,
    y_pred: np.ndarray,
    *,
    n_primitives: int,
    n_variables: int,
    precision_nats: float = math.log(2.0) * 16.0,
) -> DescriptionLength:
    """Total description length in nats: the cost of the model plus the cost of the data given it."""
    structure = structure_bits(node, n_primitives=n_primitives, n_variables=n_variables)
    constants = constant_bits(node, precision_nats=precision_nats)
    residuals = residual_bits(y, y_pred)
    return DescriptionLength(
        total=round(structure + constants + residuals, 6),
        structure=round(structure, 6),
        constants=round(constants, 6),
        residuals=round(residuals, 6),
    )


def bic(node: Node, y: np.ndarray, y_pred: np.ndarray) -> float:
    """Bayesian information criterion, with the fitted constants as the free parameters.

    Reported next to the description length because the two disagree in an informative way: BIC
    charges only for the constants, description length also charges for the structure, so BIC is
    systematically kinder to a large expression with few numeric leaves.
    """
    n = int(y.shape[0])
    if n == 0:
        return float("nan")
    k = n_constants(node)
    residual = y - y_pred
    sigma_squared = max(float(np.mean(residual * residual)), 1e-12)
    log_likelihood = -0.5 * n * (math.log(2.0 * math.pi * sigma_squared) + 1.0)
    return round(-2.0 * log_likelihood + k * math.log(n), 6)


def pareto_front(points: list[tuple[float, float]]) -> list[int]:
    """Indices of the non-dominated points of a (loss, complexity) set, both minimised.

    Ties are resolved so that only one point survives at a given complexity: the best loss. Without
    that, the front fills with structurally different expressions of identical size and the front
    stops being readable.
    """
    order = sorted(range(len(points)), key=lambda i: (points[i][1], points[i][0]))
    front: list[int] = []
    best_loss = float("inf")
    for i in order:
        loss, _complexity = points[i]
        if loss < best_loss:
            front.append(i)
            best_loss = loss
    return front


def pareto_score(front_points: list[tuple[float, float]]) -> list[float]:
    """Per-point score: the drop in log loss per unit of added complexity, relative to the previous
    front member.

    This is the quantity that makes an "elbow" identifiable rather than eyeballed. The first member
    has no predecessor and scores zero by definition.
    """
    scores: list[float] = []
    previous_loss: float | None = None
    previous_complexity: float | None = None
    for loss, complexity in front_points:
        if previous_loss is None or previous_complexity is None:
            scores.append(0.0)
        else:
            delta_complexity = complexity - previous_complexity
            if delta_complexity <= 0:
                scores.append(0.0)
            else:
                safe_previous = max(previous_loss, 1e-300)
                safe_current = max(loss, 1e-300)
                scores.append(round((math.log(safe_previous) - math.log(safe_current)) / delta_complexity, 6))
        previous_loss, previous_complexity = loss, complexity
    return scores


def count_primitives_used(node: Node) -> int:
    return len({n.op for n in walk(node) if not n.is_leaf})
