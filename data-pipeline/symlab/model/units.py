"""Dimensional analysis as a hard constraint on the search space.

Every quantity carries a 7-vector of exponents over the SI base dimensions, in the fixed order

    [length, mass, time, electric current, temperature, amount, luminous intensity]
    [  m   ,  kg ,  s  ,        A        ,      K     ,  mol  ,        cd        ]

which is the order the exported contract uses for its `dims` fields. A dimensionless quantity is the
zero vector.

Two things use this module, and they are different in kind:

1. **Checking**: given a finished expression, is it dimensionally consistent? This is a post-hoc
   filter and it is the weaker use.
2. **Constraining generation**: refusing to build a node whose units cannot work, so the search
   never spends evaluations on `sin(length)` or on adding a mass to a time. This is the strong use
   and it is why the unit-typed grammar is a distinct rung of the ladder rather than a flag on the
   others. The physics-aware literature is consistent that constraining generation, rather than
   filtering afterwards, is where the gain comes from.

The relevant caveat, stated because the lab is not allowed to overclaim: unit consistency is a
necessary condition for a physical law, never a sufficient one. A dimensionally perfect expression
can still be the wrong law, and this lab's own evaluation protocol exists precisely because a
plausible-looking fit is not a discovery.

Reference transcribed from the persisted research: Buckingham, E. (1914). On physically similar
systems; illustrations of the use of dimensional equations. Physical Review 4(4):345-376,
doi:10.1103/PhysRev.4.345.
"""
from __future__ import annotations

from dataclasses import dataclass

from .expr import KIND_CONST, KIND_VAR, OPERATORS, Node

#: Number of SI base dimensions tracked.
N_DIMS = 7

#: Human-readable symbols, in the fixed contract order.
DIM_SYMBOLS = ("m", "kg", "s", "A", "K", "mol", "cd")

Dims = tuple[int, ...]

DIMENSIONLESS: Dims = (0,) * N_DIMS


def dims(**kwargs: int) -> Dims:
    """Build a dimension vector by name, for example `dims(m=1, s=-2)` for an acceleration."""
    index = {s: i for i, s in enumerate(DIM_SYMBOLS)}
    out = [0] * N_DIMS
    for key, value in kwargs.items():
        if key not in index:
            raise KeyError(f"unknown base dimension {key!r}; known: {DIM_SYMBOLS}")
        out[index[key]] = int(value)
    return tuple(out)


#: A few named dimensions the case definitions reuse.
COMMON: dict[str, Dims] = {
    "dimensionless": DIMENSIONLESS,
    "length": dims(m=1),
    "mass": dims(kg=1),
    "time": dims(s=1),
    "temperature": dims(K=1),
    "velocity": dims(m=1, s=-1),
    "acceleration": dims(m=1, s=-2),
    "force": dims(kg=1, m=1, s=-2),
    "energy": dims(kg=1, m=2, s=-2),
    "power": dims(kg=1, m=2, s=-3),
    "pressure": dims(kg=1, m=-1, s=-2),
    "density": dims(kg=1, m=-3),
    "frequency": dims(s=-1),
    "volume_flow": dims(m=3, s=-1),
    "mass_flow": dims(kg=1, s=-1),
}


def add(a: Dims, b: Dims) -> Dims:
    return tuple(x + y for x, y in zip(a, b))


def sub(a: Dims, b: Dims) -> Dims:
    return tuple(x - y for x, y in zip(a, b))


def scale(a: Dims, k: int) -> Dims:
    return tuple(x * k for x in a)


def is_dimensionless(a: Dims) -> bool:
    return all(x == 0 for x in a)


def halves(a: Dims) -> Dims | None:
    """Halve the exponents, or return None when the result would not be integral.

    A square root of a quantity whose exponents are odd has no representation in this integer
    exponent lattice, so the generator must refuse to build it rather than round.
    """
    if any(x % 2 for x in a):
        return None
    return tuple(x // 2 for x in a)


def format_dims(a: Dims) -> str:
    """Render as a readable unit string, for example `kg.m.s^-2`. Empty means dimensionless."""
    parts = []
    for symbol, exponent in zip(DIM_SYMBOLS, a):
        if exponent == 0:
            continue
        parts.append(symbol if exponent == 1 else f"{symbol}^{exponent}")
    return ".".join(parts) if parts else "1"


@dataclass(frozen=True)
class UnitCheck:
    """The outcome of checking one expression."""

    ok: bool
    dims: Dims | None
    reason: str = ""


def infer_dims(node: Node, input_dims: list[Dims], *, const_dims: Dims | None = None) -> UnitCheck:
    """Infer the dimensions of an expression, or explain why it is inconsistent.

    `const_dims` controls how numeric leaves are treated. `None`, the default, is the permissive
    reading used when checking an expression produced by a unit-blind engine: a constant adopts
    whatever dimension its context needs, which is how a fitted coefficient behaves in practice. The
    strict reading, used by the unit-typed generator, passes `DIMENSIONLESS` so that a bare number
    can never silently repair a dimensional mismatch.
    """
    flexible = const_dims is None

    def visit(n: Node) -> UnitCheck:
        if n.kind == KIND_CONST:
            return UnitCheck(True, None if flexible else const_dims)
        if n.kind == KIND_VAR:
            idx = int(n.var_index)  # type: ignore[arg-type]
            if idx >= len(input_dims):
                return UnitCheck(False, None, f"no declared dimension for input x{idx}")
            return UnitCheck(True, input_dims[idx])

        spec = OPERATORS[n.op]  # type: ignore[index]
        children = [visit(c) for c in n.children]
        for c in children:
            if not c.ok:
                return c
        rule = spec.unit_rule
        values = [c.dims for c in children]

        if rule == "same":
            known = [v for v in values if v is not None]
            if not known:
                return UnitCheck(True, None)
            first = known[0]
            for other in known[1:]:
                if other != first:
                    return UnitCheck(
                        False, None,
                        f"{spec.name} needs matching dimensions, got "
                        f"{format_dims(first)} and {format_dims(other)}",
                    )
            return UnitCheck(True, first)

        if rule in ("add", "sub"):
            left = values[0] if values[0] is not None else DIMENSIONLESS
            right = values[1] if values[1] is not None else DIMENSIONLESS
            return UnitCheck(True, add(left, right) if rule == "add" else sub(left, right))

        if rule == "double":
            v = values[0]
            return UnitCheck(True, None if v is None else scale(v, 2))

        if rule == "half":
            v = values[0]
            if v is None:
                return UnitCheck(True, None)
            h = halves(v)
            if h is None:
                return UnitCheck(False, None, f"sqrt of {format_dims(v)} is not representable in integer exponents")
            return UnitCheck(True, h)

        if rule == "dimensionless":
            v = values[0]
            if v is not None and not is_dimensionless(v):
                return UnitCheck(False, None, f"{spec.name} requires a dimensionless argument, got {format_dims(v)}")
            return UnitCheck(True, DIMENSIONLESS)

        return UnitCheck(False, None, f"unknown unit rule {rule!r}")

    return visit(node)


def check(node: Node, input_dims: list[Dims], target: Dims, *, strict: bool = False) -> UnitCheck:
    """Check an expression end to end against the declared target dimension."""
    result = infer_dims(node, input_dims, const_dims=DIMENSIONLESS if strict else None)
    if not result.ok:
        return result
    if result.dims is None:
        # A pure-constant expression adopts the target under the permissive reading.
        return UnitCheck(True, target)
    if result.dims != target:
        return UnitCheck(
            False, result.dims,
            f"expression has dimensions {format_dims(result.dims)}, target is {format_dims(target)}",
        )
    return UnitCheck(True, target)
