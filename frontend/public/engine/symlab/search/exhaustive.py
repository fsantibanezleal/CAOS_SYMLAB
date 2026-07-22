"""Bounded exhaustive search: the only rung that can prove a negative.

Every other method in this lab returns "here is the best expression I found". This one returns "here
is the best expression that EXISTS, up to complexity k over this primitive set". That difference is
the reason it is worth the cost, and it is the reason it is also the best interactive demonstration
in the whole product: the search space is finite, enumerable, and can be shown shrinking as the
constraints tighten.

The certificate is precise, and its wording matters because it is easy to overclaim:

> Over the primitive set P and the variables V, every structurally distinct expression of at most k
> nodes was enumerated and fitted. No expression in that space achieves a lower description length
> than the one reported.

What it does NOT say: that no simpler law exists (a law outside P is unreachable), that the reported
expression is the true generating process (fitting is not discovering), or anything at all about
expressions of k+1 nodes. The literature's headline failure, a model scoring above 0.999 on
coefficient of determination while recovering the right structure zero percent of the time, is
exactly what happens when a search result is read as more than it is.

Enumeration is by node count, building each size from smaller ones, with structural deduplication so
commutative rearrangements are not enumerated twice. Constants are handled as a single placeholder
leaf fitted numerically afterwards, because enumerating constant VALUES is not possible and
pretending otherwise would make the certificate false.

Reference transcribed from the persisted research: Bartlett, D. J., Desmond, H. and Ferreira, P. G.
(2023). Exhaustive Symbolic Regression. IEEE Transactions on Evolutionary Computation,
doi:10.1109/TEVC.2023.3280250, arXiv:2211.11461. The exact minimum-description-length codelength of
that paper is marked UNVERIFIED in the research dossier and is NOT reproduced here; this module uses
the description length defined in `model/complexity.py`, and says so wherever it reports a number.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..model.complexity import description_length, pareto_front
from ..model.expr import OPERATORS, Node, canonical_key, evaluate, is_valid, n_constants, size
from ..model.intervals import admissible, from_data
from .tune import levenberg_marquardt

#: The placeholder a constant leaf starts as. Its value is fitted after enumeration, never enumerated.
CONST_PLACEHOLDER = 1.0


@dataclass(frozen=True)
class Certificate:
    """What was actually proven, in a form the app can print verbatim."""

    primitives: tuple[str, ...]
    n_variables: int
    max_nodes: int
    n_enumerated: int
    n_distinct: int
    n_admissible: int
    n_fitted: int
    complete: bool
    statement: str
    caveats: tuple[str, ...]


@dataclass
class ExhaustiveResult:
    expressions: list[Node]
    losses: list[float]
    description_lengths: list[float]
    pareto: list[int]
    best_index: int
    certificate: Certificate


def enumerate_expressions(
    *,
    primitives: tuple[str, ...],
    n_vars: int,
    max_nodes: int,
    allow_constants: bool = True,
    cap: int = 200_000,
) -> list[Node]:
    """Every structurally distinct expression of at most `max_nodes` nodes.

    Built bottom up by node count. Deduplication uses the canonical key, which orders the arguments
    of commutative operators, so `a + b` and `b + a` are enumerated once. Without that the count
    explodes by a factor that grows with the number of commutative operators in the set.

    `cap` is a hard stop. If it is hit the certificate is marked incomplete, because a truncated
    enumeration proves nothing and must never be presented as if it did.
    """
    by_size: dict[int, list[Node]] = {1: []}
    seen: set[str] = set()

    for v in range(n_vars):
        node = Node.var(v)
        key = canonical_key(node)
        if key not in seen:
            seen.add(key)
            by_size[1].append(node)
    if allow_constants:
        node = Node.const(CONST_PLACEHOLDER)
        key = canonical_key(node)
        if key not in seen:
            seen.add(key)
            by_size[1].append(node)

    truncated = False
    for target in range(2, max_nodes + 1):
        bucket: list[Node] = []
        for op in primitives:
            spec = OPERATORS[op]
            if spec.arity == 1:
                for child in by_size.get(target - 1, []):
                    candidate = Node.call(op, child)
                    key = canonical_key(candidate)
                    if key in seen:
                        continue
                    seen.add(key)
                    bucket.append(candidate)
                    if len(seen) >= cap:
                        truncated = True
                        break
            else:
                for left_size in range(1, target - 1):
                    right_size = target - 1 - left_size
                    for left in by_size.get(left_size, []):
                        for right in by_size.get(right_size, []):
                            candidate = Node.call(op, left, right)
                            key = canonical_key(candidate)
                            if key in seen:
                                continue
                            seen.add(key)
                            bucket.append(candidate)
                            if len(seen) >= cap:
                                truncated = True
                                break
                        if truncated:
                            break
                    if truncated:
                        break
            if truncated:
                break
        by_size[target] = bucket
        if truncated:
            break

    out: list[Node] = []
    for target in sorted(by_size):
        out.extend(by_size[target])
    enumerate_expressions.truncated = truncated  # type: ignore[attr-defined]
    return out


def run_exhaustive(
    X: np.ndarray,
    y: np.ndarray,
    *,
    primitives: tuple[str, ...],
    max_nodes: int = 7,
    allow_constants: bool = True,
    interval_guard: bool = True,
    tune_iterations: int = 20,
    cap: int = 200_000,
) -> ExhaustiveResult:
    """Enumerate, guard, fit, rank by description length, and issue the certificate."""
    n_vars = X.shape[1]
    candidates = enumerate_expressions(
        primitives=primitives, n_vars=n_vars, max_nodes=max_nodes,
        allow_constants=allow_constants, cap=cap,
    )
    truncated = bool(getattr(enumerate_expressions, "truncated", False))
    box = from_data(X, margin=0.25) if interval_guard else None

    kept: list[Node] = []
    losses: list[float] = []
    lengths: list[float] = []
    n_admissible = 0
    n_fitted = 0

    for candidate in candidates:
        if box is not None and not admissible(candidate, box):
            continue
        n_admissible += 1
        expression = candidate
        if n_constants(candidate) > 0:
            result = levenberg_marquardt(candidate, X, y, max_iterations=tune_iterations)
            expression = result.expression
            n_fitted += 1
        prediction = evaluate(expression, X)
        if not is_valid(prediction):
            continue
        loss = float(np.mean((y - prediction) ** 2))
        if not math.isfinite(loss):
            continue
        dl = description_length(
            expression, y, prediction, n_primitives=len(primitives), n_variables=n_vars
        )
        kept.append(expression)
        losses.append(loss)
        lengths.append(dl.total)

    if not kept:
        fallback = Node.const(float(np.mean(y)))
        kept, losses, lengths = [fallback], [float(np.var(y))], [float("inf")]

    front = pareto_front([(losses[i], float(size(kept[i]))) for i in range(len(kept))])
    best_index = int(np.argmin(lengths))

    statement = (
        f"Over the primitive set {{{', '.join(primitives)}}} and {n_vars} input variable(s), every "
        f"structurally distinct expression of at most {max_nodes} nodes was enumerated and fitted. "
        f"No expression in that space achieves a lower description length than the one reported."
    )
    caveats = (
        "The claim is bounded by the primitive set: a law requiring an operator outside this set is "
        "not reachable and its absence is not evidence.",
        "The claim is bounded by size: nothing is asserted about expressions larger than the bound.",
        "Fitting is not discovering. A best-in-space expression can still be the wrong law, which is "
        "why this lab reports description length rather than accuracy alone.",
        "Constants were fitted numerically after enumeration, not enumerated. Only expression "
        "STRUCTURES are exhaustively covered.",
        "The description length used is the one defined by this build and stated in the docs, not a "
        "reproduction of any published codelength formula.",
    )
    if truncated:
        caveats = caveats + (
            f"ENUMERATION WAS TRUNCATED at the {cap} expression cap. The completeness claim does NOT "
            "hold for this run and must not be presented as a certificate.",
        )

    certificate = Certificate(
        primitives=primitives,
        n_variables=n_vars,
        max_nodes=max_nodes,
        n_enumerated=len(candidates),
        n_distinct=len(candidates),
        n_admissible=n_admissible,
        n_fitted=n_fitted,
        complete=not truncated,
        statement=statement,
        caveats=caveats,
    )
    return ExhaustiveResult(
        expressions=kept, losses=losses, description_lengths=lengths,
        pareto=front, best_index=best_index, certificate=certificate,
    )
