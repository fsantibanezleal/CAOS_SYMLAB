"""A NON-evolutionary search: sparse regression over a fixed nonlinear basis.

Every rung of the ladder up to this point is genetic programming with one more mechanism bolted on.
That makes the ladder an excellent ablation of GP and a poor survey of symbolic regression, because
the strongest practical alternative to evolving expressions is not to evolve anything: build a
library of candidate terms once, then select a sparse subset of them by least squares.

This is the family behind FFX (McConaghy 2011) and, in the dynamical-systems setting, SINDy (Brunton
et al. 2016). Both are surveyed in `docs/frameworks/`, neither is vendored here, and the reason is
the same reason the GP engine is hand-written: the live lane runs the same modules in the browser
through Pyodide, so anything that cannot be expressed in numpy cannot ship. This can.

What it buys, stated as what a reader can check rather than as a claim:

- **It is deterministic.** No seed, no population, no variance between runs. Where it recovers a
  law it recovers it every time, and where it fails it fails identically, which makes it a much
  harder baseline to dismiss than a lucky evolutionary run.
- **It produces a Pareto front by construction.** One model per sparsity level, so the
  accuracy-versus-complexity trade-off is swept rather than searched for.
- **Its failure mode is interesting.** It can only ever return a linear combination of the library
  terms, so a law that is not in that span is unreachable no matter how much budget it is given.
  A GP search fails at such a law slowly and ambiguously; this fails immediately and legibly.

The honest limit, and it is a real one: the library is fixed before the data is seen. Nested
structure (an exponential of a ratio, a saturation inside a product) is not in the span unless
somebody put it there. That is precisely the gap genetic programming exists to close, and reporting
both families on the same cases is how a reader sees the size of it.

Method: sequentially thresholded least squares (STLSQ). Fit the full library by least squares, drop
every coefficient below a threshold, refit on what survives, repeat until the support stops
changing. Sweeping the threshold sweeps the front.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
import numpy as np

from ..model.complexity import node_count
from ..model.expr import Node, evaluate
from ..model import scaling as scaling_mod
from .engine import Individual, SearchConfig, SearchResult

#: Thresholds swept to produce the front. Logarithmic, because coefficient magnitudes in a fitted
#: library span orders of magnitude and a linear sweep spends most of its steps in one regime.
#: Thresholds are applied to coefficients on SCALE-NORMALISED columns, so they read as "how much
#: does this term contribute relative to the others" rather than as raw magnitudes. The sweep is
#: relative to the target scale, which is what makes one set of numbers work across cases whose
#: targets differ by many orders of magnitude.
THRESHOLD_FRACTIONS: tuple[float, ...] = (
    1e-6, 1e-5, 1e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 2e-1, 4e-1, 7e-1,
)

#: Maximum STLSQ refit iterations. The support is monotonically shrinking, so this terminates well
#: before the bound in every practical case; the bound exists so a pathological input cannot spin.
MAX_REFITS = 12


@dataclass(frozen=True)
class BasisTerm:
    """One column of the library.

    The column is computed by evaluating the EXPRESSION, not by a parallel numpy lambda. The first
    version carried both, and they disagreed: the lambda clipped `exp` to avoid overflow and took
    `log` of an absolute value, while the expression did neither. So the fit was performed against
    one function and the model reported against a different one, and the reported R2 came out as
    minus infinity on any case that touched an exponential. A method whose published expression is
    not the thing it fitted is exactly the failure this product exists to refuse, so there is one
    definition and the column is derived from it.
    """

    name: str
    node: Node
    complexity: int


def _usable_columns(terms: list[BasisTerm], X: np.ndarray) -> tuple[list[BasisTerm], np.ndarray]:
    """Evaluate every candidate term and keep only those that are finite everywhere.

    Dropping a term is honest; zero-filling it is not. A column that is non-finite on some rows and
    zero-filled still enters the fit, gets a coefficient, and ships inside the published expression
    where it will produce that same non-finite value for any reader who evaluates it.
    """
    kept: list[BasisTerm] = []
    columns: list[np.ndarray] = []
    for term in terms:
        try:
            values = np.asarray(evaluate(term.node, X), dtype=float)
        except Exception:  # noqa: BLE001 - an unusable term is data, not an error
            continue
        if values.shape != (X.shape[0],) or not np.all(np.isfinite(values)):
            continue
        kept.append(term)
        columns.append(values)
    if not columns:
        return [], np.zeros((X.shape[0], 0))
    return kept, np.column_stack(columns)


def build_library(X: np.ndarray, *, degree: int = 2) -> list[BasisTerm]:
    """The candidate terms, in a fixed order that does not depend on the data.

    Deliberately modest: identity, square, reciprocal, square root, logarithm and exponential of
    each input, plus pairwise products. A larger library is not obviously better, because every
    extra column is another chance for the least-squares fit to explain noise, and the sparsity
    sweep then has to work harder to throw it away again.
    """
    n_features = X.shape[1]
    terms: list[BasisTerm] = [BasisTerm("1", Node.const(1.0), 1)]

    for j in range(n_features):
        variable = Node.var(j)
        terms.extend([
            BasisTerm(f"x{j}", variable, 1),
            BasisTerm(f"x{j}^2", Node.call("square", variable), 2),
            BasisTerm(f"1/x{j}", Node.call("inv", variable), 2),
            BasisTerm(f"sqrt(x{j})", Node.call("sqrt", variable), 2),
            BasisTerm(f"log(x{j})", Node.call("log", variable), 2),
            BasisTerm(f"exp(x{j})", Node.call("exp", variable), 2),
        ])

    if degree >= 2:
        for a in range(n_features):
            for b in range(a + 1, n_features):
                terms.append(BasisTerm(
                    f"x{a}*x{b}",
                    Node.call("mul", Node.var(a), Node.var(b)),
                    3,
                ))
    return terms


def _column_scales(library: np.ndarray) -> np.ndarray:
    """The scale of each library column, used to make coefficients comparable.

    Without this the method does not work at all, and it fails silently rather than loudly. The
    library mixes `x`, `x^2`, `log x` and `exp x`, whose columns can differ by twenty orders of
    magnitude; the least-squares solution then puts coefficients of 1e-25 on the enormous columns
    and 1e+3 on the small ones. A single threshold applied to THOSE numbers is meaningless, and the
    first version of this file duly deleted every coefficient at every threshold and returned the
    mean of y for every case.

    Thresholding is a statement about how much a term CONTRIBUTES, so the coefficients have to be
    expressed in units where that comparison holds. Scaling each column to unit norm does that, and
    the coefficients are scaled back before the expression is built, so what ships is a fit to the
    original data rather than to a normalised copy of it.
    """
    # Max absolute value rather than root-mean-square. An `exp` column on a wide input range holds
    # finite values near 1e300, and squaring those overflows to infinity, which would make the
    # scale itself non-finite and put the column back into the fit unnormalised. The maximum needs
    # no intermediate larger than the value it is measuring.
    scales = np.max(np.abs(library), axis=0)
    # A column that is all zeros carries no signal, and a non-finite scale cannot normalise
    # anything. Leaving the scale at 1 keeps the column in the fit at its own magnitude, where the
    # threshold sweep will discard it.
    scales[~np.isfinite(scales)] = 1.0
    scales[scales < 1e-12] = 1.0
    return scales


def _stlsq(library: np.ndarray, y: np.ndarray, threshold: float, scales: np.ndarray) -> np.ndarray:
    """Sequentially thresholded least squares, on scale-normalised columns.

    Returns coefficients in the ORIGINAL column units, so the caller can build an expression
    against the real data without knowing normalisation happened.
    """
    normalised = library / scales
    coefficients, *_ = np.linalg.lstsq(normalised, y, rcond=None)
    support = np.ones(library.shape[1], dtype=bool)

    for _ in range(MAX_REFITS):
        small = np.abs(coefficients) < threshold
        new_support = support & ~small
        if not new_support.any():
            return np.zeros(library.shape[1])
        if np.array_equal(new_support, support):
            break
        support = new_support
        coefficients = np.zeros(library.shape[1])
        fitted, *_ = np.linalg.lstsq(normalised[:, support], y, rcond=None)
        coefficients[support] = fitted

    return coefficients / scales


def _to_expression(terms: list[BasisTerm], coefficients: np.ndarray) -> Node | None:
    """Assemble the selected terms into one expression, or None when nothing survived."""
    parts: list[Node] = []
    for term, coefficient in zip(terms, coefficients):
        if coefficient == 0.0:
            continue
        base = term.node
        parts.append(
            base if term.name == "1" and coefficient == 1.0
            else Node.call("mul", Node.const(float(coefficient)), base)
            if term.name != "1"
            else Node.const(float(coefficient))
        )
    if not parts:
        return None
    expression = parts[0]
    for part in parts[1:]:
        expression = Node.call("add", expression, part)
    return expression


class SparseRegressionSearch:
    """The same interface the GP engine presents, so the pipeline treats it as one more variant."""

    def __init__(self, config: SearchConfig) -> None:
        self.config = config

    @staticmethod
    def _mean_member(y: np.ndarray, operator: str) -> Individual:
        """The mean of y: the only model available when no term is usable.

        Returned rather than raised, because "this library cannot express anything about this
        data" is a finding about the method and belongs in the front where a reader can see it.
        """
        return Individual(
            expression=Node.const(float(np.mean(y))),
            loss=float(np.mean((y - np.mean(y)) ** 2)),
            complexity=int(node_count(Node.const(float(np.mean(y))))),
            operator=operator,
        )

    def _empty(self, y: np.ndarray, seed: int, started: float, *, reason: str) -> SearchResult:
        member = self._mean_member(y, f"stlsq({reason})")
        return SearchResult(
            config=self.config, seed=seed, pareto=[member], pareto_scores=[0.0], best=member,
            history={
                "generation": [0], "evals": [0],
                "best_loss": [member.loss], "mean_loss": [member.loss], "worst_loss": [member.loss],
                "diversity": {"structural": [1.0], "semantic": [1.0], "operator_entropy": [0.0]},
                "operator_freq": {"ops": ["stlsq"], "matrix": [[1.0]]},
                "islands": [], "migrations": [],
            },
            counters={"library_terms": 0, "thresholds": 0},
            duplicates_avoided=0, invalid_rejected=0,
            wall_seconds=round(time.perf_counter() - started, 3),
        )

    def run(self, X: np.ndarray, y: np.ndarray, *, seed: int = 0) -> SearchResult:
        started = time.perf_counter()
        terms, library = _usable_columns(build_library(X), X)
        if not terms:
            return self._empty(y, seed, started, reason="no library term is finite on this data")
        scales = _column_scales(library)

        members: list[Individual] = []
        seen_supports: set[tuple[int, ...]] = set()
        invalid = 0

        # Thresholds scale with the target, so a case whose y is in megawatts and one whose y is a
        # fraction sweep the same relative range rather than the same absolute one.
        target_scale = float(np.sqrt(np.mean(y ** 2))) or 1.0
        for fraction in THRESHOLD_FRACTIONS:
            threshold = fraction * target_scale
            coefficients = _stlsq(library, y, threshold, scales)
            support = tuple(int(i) for i in np.flatnonzero(coefficients))
            if not support or support in seen_supports:
                continue
            seen_supports.add(support)

            expression = _to_expression(terms, coefficients)
            if expression is None:
                invalid += 1
                continue

            # The loss is measured on the EXPRESSION, not on the matrix product that produced the
            # coefficients. The two agree to about 1e-6, because a tree evaluation and a matrix
            # product sum in different orders, and the number that ships has to be the one a reader
            # reproduces by evaluating the published formula.
            predicted = np.asarray(evaluate(expression, X), dtype=float)
            if not np.all(np.isfinite(predicted)):
                invalid += 1
                continue
            loss = float(np.mean((y - predicted) ** 2))
            if not np.isfinite(loss):
                invalid += 1
                continue

            members.append(Individual(
                expression=expression,
                loss=loss,
                # node_count of the PUBLISHED expression, for the same reason the loss two
                # comments up is measured on it. This used to be a hand-rolled tally,
                # `sum(term complexities) + len(support)`, which disagreed with the node count the
                # exporter writes into the front by one on 25 of the 39 committed artifacts. The
                # front then plotted a member at one complexity while the score beside it reported
                # another, and the two arms' fronts were not on the same axis at all.
                complexity=int(node_count(expression)),
                scaling=scaling_mod.IDENTITY,
                operator=f"stlsq(threshold={threshold:g})",
            ))

        if not members:
            # Nothing survived at any threshold. That is a result about the library, not a crash:
            # the target is not in the span of these terms at any sparsity.
            members = [self._mean_member(y, "stlsq(empty support)")]

        members.sort(key=lambda m: (m.complexity, m.loss))
        # Keep only the members that are not dominated: strictly better loss than everything simpler.
        front: list[Individual] = []
        best_loss = float("inf")
        for member in members:
            if member.loss < best_loss:
                front.append(member)
                best_loss = member.loss

        best = min(front, key=lambda m: m.loss)
        elapsed = time.perf_counter() - started

        return SearchResult(
            config=self.config,
            seed=seed,
            pareto=front,
            pareto_scores=[0.0] * len(front),
            best=best,
            history={
                "generation": list(range(len(front))),
                "evals": [len(THRESHOLD_FRACTIONS)] * len(front),
                "best_loss": [m.loss for m in front],
                "mean_loss": [m.loss for m in front],
                "worst_loss": [m.loss for m in front],
                "diversity": {
                    "structural": [1.0] * len(front),
                    "semantic": [1.0] * len(front),
                    "operator_entropy": [0.0] * len(front),
                },
                "operator_freq": {"ops": ["stlsq"], "matrix": [[1.0]] * len(front)},
                "islands": [],
                "migrations": [],
            },
            counters={"library_terms": len(terms), "thresholds": len(THRESHOLD_FRACTIONS)},
            duplicates_avoided=max(0, len(THRESHOLD_FRACTIONS) - len(seen_supports)),
            invalid_rejected=invalid,
            wall_seconds=round(elapsed, 3),
        )
