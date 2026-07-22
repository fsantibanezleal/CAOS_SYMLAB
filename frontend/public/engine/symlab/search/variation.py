"""Variation operators: how one expression becomes another.

The classical set (subtree crossover, subtree mutation, point mutation, hoist mutation) is
implemented as published, because it is the control condition. Hoist mutation earns its place for a
reason worth stating: it is the only operator here that reliably makes an expression SMALLER, and
without it a population under a pure accuracy objective grows without bound. That growth is bloat,
and it is the oldest known pathology of tree genetic programming.

Every operator respects a depth cap and returns the parent unchanged rather than raising when it
cannot act. Silent no-ops are acceptable here and are counted by the engine, because an operator
that fails half the time on a constrained problem is information about the problem.

References transcribed from the persisted research:
- Koza, J. R. (1992). Genetic Programming. MIT Press. Subtree crossover and mutation.
- Poli, R., Langdon, W. B. and McPhee, N. F. (2008). A Field Guide to Genetic Programming.
  The operator set and the bloat discussion.
"""
from __future__ import annotations

import numpy as np

from ..model.expr import OPERATORS, Node, depth, size, walk
from .generate import grow


def _nodes_with_ids(root: Node) -> list[tuple[int, Node]]:
    return list(enumerate(walk(root)))


def _replace_at(root: Node, target_id: int, replacement: Node) -> Node:
    """Rebuild the tree with the subtree at the given pre-order id replaced."""
    counter = 0

    def rebuild(node: Node) -> Node:
        nonlocal counter
        my_id = counter
        counter += 1
        if my_id == target_id:
            counter += size(node) - 1
            return replacement
        if node.is_leaf:
            return node
        return Node(kind=node.kind, op=node.op, children=tuple(rebuild(c) for c in node.children))

    return rebuild(root)


def _subtree_at(root: Node, target_id: int) -> Node:
    for node_id, node in _nodes_with_ids(root):
        if node_id == target_id:
            return node
    return root


def _pick_node(rng: np.random.Generator, root: Node, *, internal_bias: float = 0.9) -> int:
    """Pick a crossover or mutation point, biased towards internal nodes.

    Koza's 90/10 convention. Without the bias, most crossovers swap single leaves and the search
    barely moves, because a random tree is mostly leaves.
    """
    nodes = _nodes_with_ids(root)
    internal = [i for i, n in nodes if not n.is_leaf]
    leaves = [i for i, n in nodes if n.is_leaf]
    if internal and rng.random() < internal_bias:
        return int(rng.choice(internal))
    if leaves:
        return int(rng.choice(leaves))
    return 0


def subtree_crossover(
    rng: np.random.Generator, a: Node, b: Node, *, max_depth: int = 12
) -> Node:
    """Swap a random subtree of `a` for a random subtree of `b`.

    Returns `a` unchanged if the result would breach the depth cap, which is the standard way of
    keeping crossover from producing runaway trees.
    """
    point_a = _pick_node(rng, a)
    point_b = _pick_node(rng, b)
    donor = _subtree_at(b, point_b)
    child = _replace_at(a, point_a, donor)
    return child if depth(child) <= max_depth else a


def subtree_mutation(
    rng: np.random.Generator,
    root: Node,
    *,
    primitives: tuple[str, ...],
    n_vars: int,
    max_depth: int = 12,
    subtree_depth: int = 3,
    const_range: tuple[float, float] = (-5.0, 5.0),
) -> Node:
    """Replace a random subtree with a freshly grown one. The main source of new material."""
    point = _pick_node(rng, root)
    fresh = grow(rng, primitives=primitives, n_vars=n_vars, max_depth=subtree_depth,
                 const_range=const_range)
    child = _replace_at(root, point, fresh)
    return child if depth(child) <= max_depth else root


def point_mutation(
    rng: np.random.Generator,
    root: Node,
    *,
    primitives: tuple[str, ...],
    n_vars: int,
    rate: float = 0.1,
    const_jitter: float = 0.1,
) -> Node:
    """Perturb nodes in place, keeping the shape: swap an operator for one of equal arity, a
    variable for another variable, and jitter a constant multiplicatively.

    This is the local operator. Crossover and subtree mutation move far; point mutation refines, and
    a search with only the far-moving operators wanders.
    """
    def rebuild(node: Node) -> Node:
        if rng.random() < rate:
            if node.kind == "const":
                factor = 1.0 + float(rng.normal(0.0, const_jitter))
                return Node.const(float(node.value) * factor)  # type: ignore[arg-type]
            if node.kind == "var" and n_vars > 1:
                return Node.var(int(rng.integers(0, n_vars)))
            if not node.is_leaf:
                arity = OPERATORS[str(node.op)].arity
                same_arity = [o for o in primitives if OPERATORS[o].arity == arity and o != node.op]
                if same_arity:
                    new_op = str(rng.choice(same_arity))
                    return Node.call(new_op, *[rebuild(c) for c in node.children])
        if node.is_leaf:
            return node
        return Node(kind=node.kind, op=node.op, children=tuple(rebuild(c) for c in node.children))

    return rebuild(root)


def hoist_mutation(rng: np.random.Generator, root: Node) -> Node:
    """Replace the whole tree by one of its own subtrees.

    The only operator here that reliably shrinks an expression. Under a pure accuracy objective a
    population grows without bound, and this is the classical counter-pressure. The lab also carries
    a multi-objective survival rung, which attacks the same problem from the other side; running
    both and measuring which does more is one of the ablations the Experiments page reports.
    """
    nodes = _nodes_with_ids(root)
    internal = [i for i, n in nodes if not n.is_leaf and i != 0]
    if not internal:
        return root
    return _subtree_at(root, int(rng.choice(internal)))


def vary(
    rng: np.random.Generator,
    a: Node,
    b: Node,
    *,
    primitives: tuple[str, ...],
    n_vars: int,
    p_crossover: float = 0.6,
    p_subtree: float = 0.2,
    p_point: float = 0.15,
    p_hoist: float = 0.05,
    max_depth: int = 12,
) -> tuple[Node, str]:
    """Apply one operator, chosen by the configured probabilities.

    Returns the child and the operator name, because the engine records which operator produced each
    individual. That record is what makes the expression genealogy view possible, and it is also how
    an operator that never contributes to a surviving lineage becomes visible instead of just costing
    evaluations quietly.
    """
    roll = rng.random()
    if roll < p_crossover:
        return subtree_crossover(rng, a, b, max_depth=max_depth), "crossover"
    roll -= p_crossover
    if roll < p_subtree:
        return subtree_mutation(rng, a, primitives=primitives, n_vars=n_vars, max_depth=max_depth), "subtree"
    roll -= p_subtree
    if roll < p_point:
        return point_mutation(rng, a, primitives=primitives, n_vars=n_vars), "point"
    roll -= p_point
    if roll < p_hoist:
        return hoist_mutation(rng, a), "hoist"
    return a, "reproduction"
