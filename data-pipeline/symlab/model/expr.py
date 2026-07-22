"""The expression core: the representation every lane of this lab shares.

This module is deliberately dependency-light (numpy only) so the SAME code runs in the offline
pipeline, in the browser under Pyodide, and inside the dormant API. It is the only code allowed to
be shared across lanes, per the product archetype.

An expression is an immutable tree of `Node`. Nodes carry no identity of their own; identity is
assigned by a pre-order walk (`assign_ids`) so that the integer id space is IDENTICAL in the LaTeX
`\\htmlData{nid=N}` annotations, the flat tree node list shipped to the web, and the per-term
`node_id` references. That single shared id space is a contract requirement, not a convenience: the
web app highlights a subterm by id and expects the tree, the equation and the stacked area chart to
agree.

Design notes that are load-bearing rather than stylistic:

- **Protected operators are NOT used.** The classical genetic-programming habit of defining
  protected division (returning 1.0 on a zero denominator) silently changes the function being
  searched and produces expressions that are wrong outside the sample. Instead, evaluation is
  allowed to produce non-finite values and the caller rejects the candidate, and the interval guard
  in `intervals.py` rejects it BEFORE it is ever evaluated. Keijzer's argument, and the reason it is
  the second rung of this lab's ladder.
- **Evaluation is vectorised over rows.** `evaluate` takes an (n_rows, n_vars) array and returns
  (n_rows,), because the search evaluates millions of candidates and a per-row Python loop would
  dominate the runtime.
- **Constants are leaves with a value**, not symbols. Constant optimisation rewrites those leaves in
  place through `set_constants`, which is what makes Lamarckian write-back cheap.

References transcribed from the persisted research dossiers:
- Koza, J. R. (1992). Genetic Programming. MIT Press. The tree representation itself.
- Keijzer, M. (2003). Improving symbolic regression with interval arithmetic and linear scaling.
  EuroGP 2003, doi:10.1007/3-540-36599-0_7. Why protected operators are a mistake.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Callable, Iterator, Sequence

import numpy as np

# --------------------------------------------------------------------------------------------
# Operator table
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Operator:
    """One primitive, with everything the whole lab needs to know about it in one place.

    `latex` is a format string over the children's rendered LaTeX. `commutative` drives the
    canonical ordering used by structural hashing, so that `a + b` and `b + a` hash identically.
    """

    name: str
    arity: int
    fn: Callable[..., np.ndarray]
    latex: str
    infix: str | None = None
    commutative: bool = False
    # Unit rule, see units.py. One of: "same" (all children share the target dims), "add" (product),
    # "sub" (quotient), "dimensionless" (children must be dimensionless, result dimensionless),
    # "half" (square root halves the exponents), "double" (square doubles them).
    unit_rule: str = "same"


def _safe_div(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # No protection: a zero denominator yields inf or nan and the candidate is rejected upstream.
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.divide(a, b)


def _safe_log(a: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(a)


def _safe_sqrt(a: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return np.sqrt(a)


def _safe_exp(a: np.ndarray) -> np.ndarray:
    with np.errstate(over="ignore"):
        return np.exp(a)


OPERATORS: dict[str, Operator] = {
    op.name: op
    for op in (
        Operator("add", 2, np.add, "{0} + {1}", "+", commutative=True, unit_rule="same"),
        Operator("sub", 2, np.subtract, "{0} - {1}", "-", unit_rule="same"),
        Operator("mul", 2, np.multiply, "{0} \\cdot {1}", "*", commutative=True, unit_rule="add"),
        Operator("div", 2, _safe_div, "\\frac{{{0}}}{{{1}}}", "/", unit_rule="sub"),
        Operator("neg", 1, np.negative, "-{0}", unit_rule="same"),
        Operator("square", 1, np.square, "{0}^{{2}}", unit_rule="double"),
        Operator("sqrt", 1, _safe_sqrt, "\\sqrt{{{0}}}", unit_rule="half"),
        Operator("exp", 1, _safe_exp, "e^{{{0}}}", unit_rule="dimensionless"),
        Operator("log", 1, _safe_log, "\\ln{{\\left({0}\\right)}}", unit_rule="dimensionless"),
        Operator("sin", 1, np.sin, "\\sin{{\\left({0}\\right)}}", unit_rule="dimensionless"),
        Operator("cos", 1, np.cos, "\\cos{{\\left({0}\\right)}}", unit_rule="dimensionless"),
        Operator("tanh", 1, np.tanh, "\\tanh{{\\left({0}\\right)}}", unit_rule="dimensionless"),
        Operator("inv", 1, lambda a: _safe_div(np.ones_like(a), a), "\\frac{{1}}{{{0}}}", unit_rule="sub"),
        Operator("abs", 1, np.abs, "\\left|{0}\\right|", unit_rule="same"),
    )
}

#: Operator sets used by the case definitions. Named so a manifest can record exactly which
#: primitives a run was allowed to use, which is part of the honest-comparison protocol: two engines
#: given different primitive sets were not solving the same problem.
PRIMITIVE_SETS: dict[str, tuple[str, ...]] = {
    "arithmetic": ("add", "sub", "mul", "div"),
    "koza": ("add", "sub", "mul", "div", "sin", "cos", "exp", "log"),
    "physics": ("add", "sub", "mul", "div", "square", "sqrt", "exp", "log", "sin", "cos", "inv"),
    "rational": ("add", "sub", "mul", "div", "square", "inv"),
    "full": tuple(OPERATORS),
}


# --------------------------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------------------------

KIND_OP_BINARY = "op_binary"
KIND_OP_UNARY = "op_unary"
KIND_VAR = "var"
KIND_CONST = "const"


@dataclass(frozen=True)
class Node:
    """One node of an expression tree.

    Exactly one of `op`, `var_index`, `value` is meaningful, selected by `kind`:
    an operator node carries `op` and `children`, a variable leaf carries `var_index`, and a
    constant leaf carries `value`.
    """

    kind: str
    op: str | None = None
    var_index: int | None = None
    value: float | None = None
    children: tuple["Node", ...] = ()

    # -- constructors ------------------------------------------------------------------------

    @staticmethod
    def var(index: int) -> "Node":
        return Node(kind=KIND_VAR, var_index=index)

    @staticmethod
    def const(value: float) -> "Node":
        return Node(kind=KIND_CONST, value=float(value))

    @staticmethod
    def call(op: str, *children: "Node") -> "Node":
        spec = OPERATORS[op]
        if len(children) != spec.arity:
            raise ValueError(f"operator {op!r} takes {spec.arity} children, got {len(children)}")
        kind = KIND_OP_BINARY if spec.arity == 2 else KIND_OP_UNARY
        return Node(kind=kind, op=op, children=tuple(children))

    # -- predicates --------------------------------------------------------------------------

    @property
    def is_leaf(self) -> bool:
        return self.kind in (KIND_VAR, KIND_CONST)

    @property
    def arity(self) -> int:
        return 0 if self.is_leaf else OPERATORS[self.op].arity  # type: ignore[index]


def walk(node: Node) -> Iterator[Node]:
    """Pre-order traversal. The id space in every exported payload follows this order."""
    yield node
    for child in node.children:
        yield from walk(child)


def size(node: Node) -> int:
    """Node count, the field's default complexity measure."""
    return 1 + sum(size(c) for c in node.children)


def depth(node: Node) -> int:
    return 1 + max((depth(c) for c in node.children), default=0)


def assign_ids(root: Node) -> dict[int, Node]:
    """Map the shared integer id space to nodes, by pre-order position.

    Returned as `{id: node}`. Callers that need the reverse direction should build it from this,
    keyed by `id()` of the node object, because `Node` is a value type and equal subtrees compare
    equal.
    """
    return {i: n for i, n in enumerate(walk(root))}


def parent_map(root: Node) -> dict[int, int | None]:
    """`{node_id: parent_id}` over the same pre-order id space, for the flat exported node list."""
    out: dict[int, int | None] = {}
    counter = 0

    def visit(node: Node, parent: int | None) -> None:
        nonlocal counter
        my_id = counter
        counter += 1
        out[my_id] = parent
        for child in node.children:
            visit(child, my_id)

    visit(root, None)
    return out


# --------------------------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------------------------


def evaluate(node: Node, X: np.ndarray) -> np.ndarray:
    """Evaluate over `X` of shape (n_rows, n_vars); returns shape (n_rows,).

    Non-finite results are returned as-is. Callers decide what to do with them; the search treats a
    candidate producing any non-finite value on the training rows as invalid. That is deliberate:
    silently repairing it would change the function being searched.
    """
    if node.kind == KIND_CONST:
        return np.full(X.shape[0], float(node.value), dtype=np.float64)
    if node.kind == KIND_VAR:
        return X[:, node.var_index].astype(np.float64, copy=False)
    spec = OPERATORS[node.op]  # type: ignore[index]
    args = [evaluate(c, X) for c in node.children]
    return spec.fn(*args)


def is_valid(values: np.ndarray) -> bool:
    """A candidate is usable only if every predicted value is finite."""
    return bool(np.all(np.isfinite(values)))


# --------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------


def constants(node: Node) -> list[float]:
    """Every constant leaf value, in pre-order. The parameter vector for constant optimisation."""
    return [n.value for n in walk(node) if n.kind == KIND_CONST]  # type: ignore[misc]


def set_constants(node: Node, values: Sequence[float]) -> Node:
    """Rebuild the tree with constant leaves replaced, in pre-order. Lamarckian write-back."""
    it = iter(values)

    def rebuild(n: Node) -> Node:
        if n.kind == KIND_CONST:
            return replace(n, value=float(next(it)))
        if n.is_leaf:
            return n
        return replace(n, children=tuple(rebuild(c) for c in n.children))

    out = rebuild(node)
    return out


def n_constants(node: Node) -> int:
    return sum(1 for n in walk(node) if n.kind == KIND_CONST)


def variables_used(node: Node) -> set[int]:
    """Which input columns the expression actually reads.

    This is what makes the feature-selection finding measurable: the benchmark literature reports
    that no method recovers an expression free of irrelevant features, and a lab that wants to say
    so has to be able to count them.
    """
    return {n.var_index for n in walk(node) if n.kind == KIND_VAR}  # type: ignore[misc]


# --------------------------------------------------------------------------------------------
# Canonical form and structural hashing
# --------------------------------------------------------------------------------------------


def canonical_key(node: Node, *, const_digits: int = 6) -> str:
    """A structural key that is invariant to the argument order of commutative operators.

    Used to deduplicate the search population. Semantic duplicates (different structure, identical
    output) are caught separately by hashing the evaluated vector; this catches the syntactic ones
    cheaply, before any evaluation happens.
    """
    if node.kind == KIND_CONST:
        return f"c({round(float(node.value), const_digits)})"
    if node.kind == KIND_VAR:
        return f"v{node.var_index}"
    spec = OPERATORS[node.op]  # type: ignore[index]
    keys = [canonical_key(c, const_digits=const_digits) for c in node.children]
    if spec.commutative:
        keys.sort()
    return f"{node.op}({','.join(keys)})"


def semantic_key(values: np.ndarray, *, digits: int = 8) -> str:
    """Hash of the evaluated output vector, for semantic deduplication.

    Non-finite candidates all collapse to one key so they are discarded together.
    """
    if not is_valid(values):
        return "invalid"
    rounded = np.round(values, digits)
    return str(hash(rounded.tobytes()))


# --------------------------------------------------------------------------------------------
# Readable text form
# --------------------------------------------------------------------------------------------


def to_infix(node: Node, var_names: Sequence[str] | None = None, *, digits: int = 6) -> str:
    """Plain infix text, the `raw_string` field of the exported contract."""
    if node.kind == KIND_CONST:
        v = float(node.value)  # type: ignore[arg-type]
        return repr(round(v, digits)) if not float(v).is_integer() else str(int(v))
    if node.kind == KIND_VAR:
        idx = int(node.var_index)  # type: ignore[arg-type]
        return var_names[idx] if var_names and idx < len(var_names) else f"x{idx}"
    spec = OPERATORS[node.op]  # type: ignore[index]
    parts = [to_infix(c, var_names, digits=digits) for c in node.children]
    if spec.infix and spec.arity == 2:
        return f"({parts[0]} {spec.infix} {parts[1]})"
    return f"{node.op}({', '.join(parts)})"


def top_level_terms(node: Node) -> list[Node]:
    """Split an expression into its top-level additive terms.

    `a + b - c` yields `[a, b, neg(c)]`. The exported contract orders these by their contribution to
    the output, colours them, and drives the per-term highlight in both the equation and the tree
    from that single ordering.
    """
    if node.kind == KIND_OP_BINARY and node.op == "add":
        return top_level_terms(node.children[0]) + top_level_terms(node.children[1])
    if node.kind == KIND_OP_BINARY and node.op == "sub":
        left = top_level_terms(node.children[0])
        right = [Node.call("neg", t) for t in top_level_terms(node.children[1])]
        return left + right
    return [node]


def count_operators(node: Node) -> dict[str, int]:
    """Operator histogram, for the building-block frequency view."""
    out: dict[str, int] = {}
    for n in walk(node):
        if not n.is_leaf:
            out[n.op] = out.get(n.op, 0) + 1  # type: ignore[index]
    return out


def is_finite_number(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))
