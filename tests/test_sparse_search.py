"""The non-evolutionary arm: what it must guarantee, and the two ways it silently failed.

Both failures produced a running, green, plausible-looking search that was wrong, and neither raised
anything. They are pinned here because each is easy to reintroduce.

1. **Unnormalised thresholding.** The library mixes `x`, `x^2`, `log x` and `exp x`, whose columns
   differ by many orders of magnitude, so the least-squares coefficients came out around 1e-25 on
   the large columns. Every threshold in the sweep then deleted everything, and the method returned
   the mean of y for every case with a straight face.
2. **A column that was not its own expression.** The library column was computed by a numpy lambda
   that clipped `exp` and took `log` of an absolute value, while the published expression did
   neither. The fit was performed against one function and reported as another, and R2 measured on
   the returned expression came out at minus infinity.

The second is the one that matters beyond this file: a method whose published expression is not the
thing it fitted is the exact failure this whole product exists to refuse.
"""

from __future__ import annotations

import numpy as np
import pytest

from symlab.cases.generators import GENERATORS, make_dataset
from symlab.model.expr import evaluate
from symlab.search.engine import SearchConfig
from symlab.search.sparse import (
    THRESHOLD_FRACTIONS,
    SparseRegressionSearch,
    build_library,
)


def _r2(y: np.ndarray, predicted: np.ndarray) -> float:
    return float(1.0 - np.sum((y - predicted) ** 2) / np.sum((y - np.mean(y)) ** 2))


@pytest.mark.parametrize("key", sorted(GENERATORS))
def test_the_returned_expression_is_the_model_that_was_fitted(key: str) -> None:
    """Evaluating the published expression must reproduce the loss the search reported.

    This is the guarantee that broke when the library column and the expression diverged. Without
    it, every downstream number, the Pareto front, the parity plot, the recovery verdict, describes
    a function nobody can reconstruct.
    """
    X, y = make_dataset(GENERATORS[key], n_rows=300, seed=0, noise=0.0)
    result = SparseRegressionSearch(SearchConfig()).run(X, y, seed=0)

    for member in result.pareto:
        predicted = evaluate(member.expression, X)
        assert np.all(np.isfinite(predicted)), (
            f"{key}: a front member evaluates to non-finite values, so the published expression "
            "cannot be the one that was fitted"
        )
        reported = member.loss
        actual = float(np.mean((y - predicted) ** 2))
        assert actual == pytest.approx(reported, rel=1e-6, abs=1e-12), (
            f"{key}: reported loss {reported:.6g} but the expression gives {actual:.6g}"
        )


@pytest.mark.parametrize("key", sorted(GENERATORS))
def test_it_is_deterministic(key: str) -> None:
    """No seed, no population, no run-to-run variance. That is the point of this arm."""
    X, y = make_dataset(GENERATORS[key], n_rows=300, seed=0, noise=0.0)
    first = SparseRegressionSearch(SearchConfig()).run(X, y, seed=0)
    second = SparseRegressionSearch(SearchConfig()).run(X, y, seed=999)

    assert [m.complexity for m in first.pareto] == [m.complexity for m in second.pareto]
    assert [m.loss for m in first.pareto] == [m.loss for m in second.pareto]


def test_the_front_is_actually_a_front() -> None:
    """Members must improve strictly in loss as complexity rises, or it is a list, not a front."""
    X, y = make_dataset(GENERATORS["heat-exchanger-ntu"], n_rows=300, seed=0, noise=0.0)
    front = SparseRegressionSearch(SearchConfig()).run(X, y, seed=0).pareto

    complexities = [m.complexity for m in front]
    losses = [m.loss for m in front]
    assert complexities == sorted(complexities)
    assert all(later < earlier for earlier, later in zip(losses, losses[1:]))


def test_a_polynomial_law_is_recovered_essentially_exactly() -> None:
    """The Lotka-Volterra right-hand side IS in the span of the library, so it must be found.

    A method that cannot find the law that is definitionally inside its own search space is broken,
    and this is the check that would have caught the unnormalised-threshold failure immediately.
    """
    X, y = make_dataset(GENERATORS["lotka-volterra-rhs"], n_rows=300, seed=0, noise=0.0)
    result = SparseRegressionSearch(SearchConfig()).run(X, y, seed=0)
    predicted = evaluate(result.best.expression, X)
    assert _r2(y, predicted) > 0.999999


def test_thresholds_are_relative_to_the_target_scale() -> None:
    """The same sweep must work on a target in megawatts and on a target that is a fraction.

    An absolute threshold sweep works on whichever case it was tuned against and quietly returns
    the mean everywhere else.
    """
    X, y = make_dataset(GENERATORS["lotka-volterra-rhs"], n_rows=300, seed=0, noise=0.0)
    small = SparseRegressionSearch(SearchConfig()).run(X, y * 1e-9, seed=0)
    large = SparseRegressionSearch(SearchConfig()).run(X, y * 1e9, seed=0)

    assert _r2(y * 1e-9, evaluate(small.best.expression, X)) > 0.999
    assert _r2(y * 1e9, evaluate(large.best.expression, X)) > 0.999


def test_every_library_term_is_finite_or_dropped() -> None:
    """A term that cannot be evaluated is removed, never zero-filled.

    Zero-filling keeps an unusable column in the fit, gives it a coefficient, and ships it inside
    the published expression, where it produces that same non-finite value for any reader.
    """
    X = np.array([[0.0, 1.0], [-1.0, 2.0], [1e-300, 3.0]])
    terms = build_library(X)
    assert len(terms) > 0

    from symlab.search.sparse import _usable_columns

    kept, library = _usable_columns(terms, X)
    assert library.shape[0] == X.shape[0]
    assert library.shape[1] == len(kept)
    assert np.all(np.isfinite(library))


def test_the_sweep_is_ordered_and_non_trivial() -> None:
    assert list(THRESHOLD_FRACTIONS) == sorted(THRESHOLD_FRACTIONS)
    assert len(THRESHOLD_FRACTIONS) >= 5
    assert THRESHOLD_FRACTIONS[0] > 0
