"""Selection and survival: four mechanisms that answer the same question differently.

Which individuals get to reproduce is the decision that most shapes what a genetic-programming
search finds, and the four implemented here are genuinely different theories of that, not tunings
of one:

1. **Tournament** picks the best of a random handful, judged on aggregate error. It is the baseline.
   Its known weakness is that aggregate error hides which CASES an individual solves: two candidates
   with the same mean error can be good at disjoint parts of the problem, and tournament cannot tell.

2. **Epsilon-lexicase** judges on one training case at a time, in random order, keeping only those
   within epsilon of the best on that case, until one survives. It therefore preserves specialists
   that aggregate error would discard. Epsilon is set automatically from the median absolute
   deviation of the errors on that case, which is what makes it work on continuous targets at all.
   The lab cites its critical reflection alongside the original, because the honest position is that
   lexicase is a strong default and not a solved question.

3. **NSGA-II survival** stops treating complexity as a penalty term and makes it a second objective.
   The output stops being a model and becomes a front. This is the rung that changes what the whole
   product reports.

4. **Age-fitness Pareto survival** adds AGE as an objective, where age is how many generations an
   individual's oldest ancestor has survived. A young individual only has to beat older ones on
   error to survive, so the search keeps a supply of fresh material and stops converging prematurely
   onto one lineage. This is the Eureqa recipe, and it is cheap.

References transcribed from the persisted research:
- La Cava, W., Spector, L. and Danai, K. (2016). Epsilon-lexicase selection for regression.
  GECCO 2016, doi:10.1145/2908812.2908898.
- Deb, K., Pratap, A., Agarwal, S. and Meyarivan, T. (2002). A fast and elitist multiobjective
  genetic algorithm: NSGA-II. IEEE TEC 6(2):182-197, doi:10.1109/4235.996017.
- Schmidt, M. and Lipson, H. (2011). Age-fitness Pareto optimization. In Genetic Programming Theory
  and Practice VIII, doi:10.1007/978-1-4419-7747-2_8.
"""
from __future__ import annotations

import numpy as np


def tournament(rng: np.random.Generator, losses: np.ndarray, *, k: int = 5) -> int:
    """Best of `k` sampled with replacement. The baseline every other rung must beat."""
    n = len(losses)
    picks = rng.integers(0, n, size=min(k, n))
    return int(picks[int(np.argmin(losses[picks]))])


def epsilon_lexicase(
    rng: np.random.Generator,
    errors: np.ndarray,
    *,
    down_sample: int | None = None,
) -> int:
    """Epsilon-lexicase selection.

    `errors` has shape (n_individuals, n_cases) and holds the absolute error of each individual on
    each training case. Cases are shuffled and applied one at a time; after each, only individuals
    within `epsilon` of the best remaining are kept, where epsilon is the median absolute deviation
    of that case's errors across the surviving pool. The first case that reduces the pool to one
    decides the winner.

    `down_sample` evaluates on a random subset of cases per selection event, which is the standard
    way to make lexicase affordable on large training sets. It changes the selection pressure, so it
    is recorded in the manifest rather than treated as a free speedup.
    """
    n_individuals, n_cases = errors.shape
    case_order = rng.permutation(n_cases)
    if down_sample is not None and down_sample < n_cases:
        case_order = case_order[:down_sample]

    pool = np.arange(n_individuals)
    for case in case_order:
        if len(pool) <= 1:
            break
        column = errors[pool, case]
        best = float(np.min(column))
        # Automatic epsilon: the median absolute deviation from the median, per La Cava et al.
        median = float(np.median(column))
        mad = float(np.median(np.abs(column - median)))
        pool = pool[column <= best + mad]
    if len(pool) == 0:
        return int(rng.integers(0, n_individuals))
    return int(pool[int(rng.integers(0, len(pool)))])


def fast_non_dominated_sort(objectives: np.ndarray) -> list[list[int]]:
    """Sort into non-domination fronts. `objectives` is (n, m), all minimised.

    Returns a list of fronts, each a list of indices. Front 0 is the Pareto-optimal set.

    The domination relation is computed as a single vectorised (n, n) boolean matrix rather than a
    double Python loop. The textbook presentation of NSGA-II uses the nested loop, and a direct
    transcription of it dominated the wall-clock of a search run here (measured: 39 s against 1.3 s
    for the same budget without multi-objective survival, on a population of 400 over 20
    generations). The result is identical; only the constant factor changes.
    """
    n = objectives.shape[0]
    if n == 0:
        return []
    # a[i, j] is True when i is no worse than j on every objective.
    no_worse = np.all(objectives[:, None, :] <= objectives[None, :, :], axis=2)
    strictly_better = np.any(objectives[:, None, :] < objectives[None, :, :], axis=2)
    dominates = no_worse & strictly_better
    np.fill_diagonal(dominates, False)

    domination_count = dominates.sum(axis=0)
    fronts: list[list[int]] = []
    remaining = np.ones(n, dtype=bool)
    counts = domination_count.copy()

    while remaining.any():
        current = np.flatnonzero(remaining & (counts == 0))
        if current.size == 0:
            # Defensive: a cycle cannot occur under a valid domination relation, but a degenerate
            # objective matrix (all-equal rows with non-finite entries) could stall the loop.
            fronts.append(sorted(np.flatnonzero(remaining).tolist()))
            break
        fronts.append(current.tolist())
        remaining[current] = False
        counts = counts - dominates[current, :].sum(axis=0)
    return fronts


def _dominates(a: np.ndarray, b: np.ndarray) -> bool:
    """`a` dominates `b` when it is no worse on every objective and strictly better on one."""
    return bool(np.all(a <= b) and np.any(a < b))


def crowding_distance(objectives: np.ndarray, front: list[int]) -> np.ndarray:
    """NSGA-II crowding distance for one front.

    Boundary points get infinite distance so the extremes of the front are never lost, which is what
    keeps a Pareto front from collapsing towards its middle over generations.
    """
    length = len(front)
    distance = np.zeros(length)
    if length <= 2:
        return np.full(length, np.inf)
    for m in range(objectives.shape[1]):
        values = objectives[front, m]
        order = np.argsort(values)
        distance[order[0]] = np.inf
        distance[order[-1]] = np.inf
        spread = float(values[order[-1]] - values[order[0]])
        if spread <= 0:
            continue
        for i in range(1, length - 1):
            distance[order[i]] += float(values[order[i + 1]] - values[order[i - 1]]) / spread
    return distance


def nsga2_survival(objectives: np.ndarray, n_survivors: int) -> list[int]:
    """Elitist survival by non-domination rank, breaking ties by crowding distance."""
    fronts = fast_non_dominated_sort(objectives)
    survivors: list[int] = []
    for front in fronts:
        if len(survivors) + len(front) <= n_survivors:
            survivors.extend(front)
            continue
        distances = crowding_distance(objectives, front)
        order = np.argsort(-distances)
        remaining = n_survivors - len(survivors)
        survivors.extend([front[i] for i in order[:remaining]])
        break
    return survivors


def age_fitness_survival(
    losses: np.ndarray, ages: np.ndarray, n_survivors: int
) -> list[int]:
    """Age-fitness Pareto survival: minimise (loss, age) jointly.

    A young individual survives by beating older ones on error alone, so newly injected material is
    not immediately outcompeted by an entrenched lineage. That is the mechanism that keeps the search
    from converging prematurely, and it costs one extra objective.
    """
    objectives = np.column_stack([losses, ages.astype(float)])
    return nsga2_survival(objectives, n_survivors)
