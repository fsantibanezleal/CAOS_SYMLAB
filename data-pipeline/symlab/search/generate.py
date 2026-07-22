"""Building random expressions, optionally constrained by units.

Two generators live here and they are not variations of one idea.

`grow` and `full` are the classical Koza initialisation methods, combined by `ramped_half_and_half`
into a population with a spread of shapes and depths. This is the baseline every later rung of the
ladder has to beat by a measured margin, so it is implemented as published rather than improved.

`grow_typed` is the unit-constrained generator. It never builds a node whose units cannot work, so
the search never spends an evaluation on `sin(length)` or on adding a mass to a time. That is a
different thing from checking an expression afterwards and discarding it: filtering wastes the
evaluation, constraining never makes it. The physics-aware literature is consistent that this is
where the gain comes from, and it is why the unit-typed grammar is a distinct rung rather than a
flag on the others.

Reference transcribed from the persisted research: Koza, J. R. (1992). Genetic Programming: On the
Programming of Computers by Means of Natural Selection. MIT Press, chapter 6 (ramped half-and-half).
"""
from __future__ import annotations

import numpy as np

from ..model.expr import OPERATORS, Node
from ..model.units import DIMENSIONLESS, Dims, add, halves, scale, sub


def _terminal(rng: np.random.Generator, n_vars: int, const_range: tuple[float, float],
              const_probability: float) -> Node:
    if rng.random() < const_probability:
        low, high = const_range
        return Node.const(float(rng.uniform(low, high)))
    return Node.var(int(rng.integers(0, n_vars)))


def grow(
    rng: np.random.Generator,
    *,
    primitives: tuple[str, ...],
    n_vars: int,
    max_depth: int,
    const_range: tuple[float, float] = (-5.0, 5.0),
    const_probability: float = 0.3,
) -> Node:
    """Koza's `grow`: a node may become a terminal at any depth, producing irregular shapes."""
    if max_depth <= 1:
        return _terminal(rng, n_vars, const_range, const_probability)
    # The chance of stopping early is what gives `grow` its variety of shapes.
    if rng.random() < 0.3:
        return _terminal(rng, n_vars, const_range, const_probability)
    op = primitives[int(rng.integers(0, len(primitives)))]
    arity = OPERATORS[op].arity
    children = [
        grow(rng, primitives=primitives, n_vars=n_vars, max_depth=max_depth - 1,
             const_range=const_range, const_probability=const_probability)
        for _ in range(arity)
    ]
    return Node.call(op, *children)


def full(
    rng: np.random.Generator,
    *,
    primitives: tuple[str, ...],
    n_vars: int,
    max_depth: int,
    const_range: tuple[float, float] = (-5.0, 5.0),
    const_probability: float = 0.3,
) -> Node:
    """Koza's `full`: every branch runs to `max_depth`, producing dense, uniform trees."""
    if max_depth <= 1:
        return _terminal(rng, n_vars, const_range, const_probability)
    op = primitives[int(rng.integers(0, len(primitives)))]
    arity = OPERATORS[op].arity
    children = [
        full(rng, primitives=primitives, n_vars=n_vars, max_depth=max_depth - 1,
             const_range=const_range, const_probability=const_probability)
        for _ in range(arity)
    ]
    return Node.call(op, *children)


def ramped_half_and_half(
    rng: np.random.Generator,
    *,
    size: int,
    primitives: tuple[str, ...],
    n_vars: int,
    min_depth: int = 2,
    max_depth: int = 6,
    const_range: tuple[float, float] = (-5.0, 5.0),
    const_probability: float = 0.3,
) -> list[Node]:
    """Koza's ramped half-and-half: half `grow`, half `full`, ramped across the depth range.

    The point is shape diversity in the initial population. A population built by one method at one
    depth starts the search from a much narrower basin, and the difference shows up in the final
    Pareto front rather than only in the first few generations.
    """
    out: list[Node] = []
    depths = list(range(min_depth, max_depth + 1))
    for i in range(size):
        depth = depths[i % len(depths)]
        builder = full if (i // len(depths)) % 2 == 0 else grow
        out.append(builder(rng, primitives=primitives, n_vars=n_vars, max_depth=depth,
                           const_range=const_range, const_probability=const_probability))
    return out


# --------------------------------------------------------------------------------------------
# Unit-constrained generation
# --------------------------------------------------------------------------------------------


def _candidate_ops_for(target: Dims, primitives: tuple[str, ...]) -> list[str]:
    """Which operators could possibly produce `target`, before looking at the children."""
    out: list[str] = []
    for op in primitives:
        rule = OPERATORS[op].unit_rule
        if rule in ("same", "add", "sub"):
            out.append(op)
        elif rule == "double":
            if all(x % 2 == 0 for x in target):
                out.append(op)
        elif rule == "half":
            out.append(op)  # target*2 is always representable
        elif rule == "dimensionless":
            if all(x == 0 for x in target):
                out.append(op)
    return out


def grow_typed(
    rng: np.random.Generator,
    *,
    primitives: tuple[str, ...],
    input_dims: list[Dims],
    target: Dims,
    max_depth: int,
    const_range: tuple[float, float] = (-5.0, 5.0),
    const_probability: float = 0.3,
    attempts: int = 24,
) -> Node | None:
    """Grow an expression that is dimensionally correct BY CONSTRUCTION.

    Returns `None` when no admissible tree could be built within `attempts`, which happens when the
    declared inputs genuinely cannot reach the target dimension. That is a real answer about the
    problem, not a failure of the generator, and the caller reports it rather than falling back to
    unconstrained search.
    """
    matching = [i for i, d in enumerate(input_dims) if d == target]

    def build(target_dims: Dims, depth: int) -> Node | None:
        # A terminal is available when an input carries exactly this dimension, or when the target is
        # dimensionless, in which case a bare constant is legitimate.
        candidates = [i for i, d in enumerate(input_dims) if d == target_dims]
        dimensionless_target = all(x == 0 for x in target_dims)

        if depth <= 1 or rng.random() < 0.3:
            if dimensionless_target and (not candidates or rng.random() < const_probability):
                low, high = const_range
                return Node.const(float(rng.uniform(low, high)))
            if candidates:
                return Node.var(int(rng.choice(candidates)))
            if not dimensionless_target:
                return None

        options = _candidate_ops_for(target_dims, primitives)
        rng.shuffle(options)
        for op in options:
            spec = OPERATORS[op]
            rule = spec.unit_rule
            if rule == "same":
                kids = [build(target_dims, depth - 1) for _ in range(spec.arity)]
            elif rule == "add":
                # A product: split the target exponents between the two children. Giving one child a
                # dimensionless role is the split that always exists, so it anchors the recursion.
                left_dims = target_dims if rng.random() < 0.5 else DIMENSIONLESS
                right_dims = sub(target_dims, left_dims)
                kids = [build(left_dims, depth - 1), build(right_dims, depth - 1)]
            elif rule == "sub":
                if spec.arity == 2:
                    left_dims = target_dims
                    right_dims = DIMENSIONLESS
                    kids = [build(left_dims, depth - 1), build(right_dims, depth - 1)]
                else:
                    kids = [build(scale(target_dims, -1), depth - 1)]
            elif rule == "double":
                h = halves(target_dims)
                kids = [build(h, depth - 1)] if h is not None else [None]
            elif rule == "half":
                kids = [build(scale(target_dims, 2), depth - 1)]
            elif rule == "dimensionless":
                kids = [build(DIMENSIONLESS, depth - 1)]
            else:
                kids = [None]

            if all(k is not None for k in kids):
                return Node.call(op, *kids)  # type: ignore[arg-type]
        # Last resort at this level: a matching input, if one exists.
        if candidates:
            return Node.var(int(rng.choice(candidates)))
        return None

    for _ in range(attempts):
        tree = build(target, max_depth)
        if tree is not None:
            return tree
    if matching:
        return Node.var(int(rng.choice(matching)))
    return None


def typed_population(
    rng: np.random.Generator,
    *,
    size: int,
    primitives: tuple[str, ...],
    input_dims: list[Dims],
    target: Dims,
    min_depth: int = 2,
    max_depth: int = 6,
) -> list[Node]:
    """A unit-correct initial population. Short by construction if the target is hard to reach."""
    out: list[Node] = []
    depths = list(range(min_depth, max_depth + 1))
    for i in range(size * 3):
        if len(out) >= size:
            break
        tree = grow_typed(
            rng, primitives=primitives, input_dims=input_dims, target=target,
            max_depth=depths[i % len(depths)],
        )
        if tree is not None:
            out.append(tree)
    return out
