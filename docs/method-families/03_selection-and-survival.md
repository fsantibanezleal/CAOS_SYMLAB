# 4, 5 and 6. Selection and survival

Which individuals reproduce is the decision that most shapes what a search finds. The four mechanisms
here are genuinely different theories of that, not tunings of one.

## Tournament, the baseline

Best of `k` sampled with replacement, judged on aggregate error. Its known weakness is that aggregate
error hides WHICH cases an individual solves: two candidates with the same mean can be good at
disjoint parts of the problem, and tournament cannot tell them apart.

## Epsilon-lexicase

Judges one training case at a time, in random order, keeping only individuals within epsilon of the
best on that case, until one survives. Specialists therefore survive where aggregate error would
discard them. Epsilon is set automatically from the median absolute deviation of that case's errors,
taken over the individuals still in the pool rather than over the whole population:

    epsilon_j = median_i | e_ij - median_k e_kj |

That automatic epsilon is what makes lexicase work on continuous targets at all. When the case list
runs out with more than one individual still in the pool, the winner is drawn uniformly from what
survives.

**Its cost is real and is published.** At population 100 over 10 generations on 120 rows it takes the
run from 0.30 s to 6.73 s, roughly 22 times. A selection method that buys quality at that price has
to be compared at equal BUDGET rather than at equal generation count. That measurement does not
record its case or its primitive set, so it is a direction rather than a reproducible number; see
[method-families.md](../method-families.md) for a re-measurement at the same budget.

Down-sampling evaluates on a random subset of cases per selection event, which is the standard way to
make it affordable. It changes the selection pressure, and here it is fixed at
`lexicase_down_sample = 64` cases per event. It is NOT among the configuration fields written into
the artifact, so a reader cannot recover it from a run: the exported config carries the switches and
the budget, not the down-sample size or the tuning schedule.

## NSGA-II survival

Complexity stops being a penalty term and becomes a second objective. Survival is by non-domination
rank with crowding distance breaking ties, and boundary points receive infinite distance so the
extremes of the front are never lost. Without that a front collapses towards its middle over
generations.

The output stops being a model and becomes a FRONT. This is the rung that changes what the whole
product reports.

The textbook presentation of the sort is a nested double loop, and a direct transcription dominates
the wall clock, so the domination relation is computed as a single vectorised matrix instead. The
result is identical; only the constant factor changes. Measured while auditing this page, at
population 400 over 20 generations on 120 rows: 0.88 s with multi-objective survival off, 1.36 s
with it on and the vectorised sort, 161 s with the same run and a textbook nested loop substituted
for it, and the two sorts return the same fronts on random objective matrices. The docstring of
`fast_non_dominated_sort` records a different pair from an earlier measurement (39 s against 1.3 s)
whose case is not recorded, so treat the ratio rather than the seconds as the finding.

## Age-fitness Pareto survival

Age becomes an objective, so a young individual only has to beat older ones on error rather than the
whole population, and a fresh lineage gets a window in which to become competitive. Survival is then
Pareto non-domination on (error, age), and it costs one extra objective.

Two deviations from the published method, stated because the page would otherwise describe Schmidt
and Lipson's algorithm rather than this one. In the paper, age is the number of generations since an
individual's OLDEST ancestor entered the population, inherited as `1 + max(parent ages)`, and one
brand-new random individual of age 0 is injected every generation. Here a child's age is
`1 + min(parent ages)`, which tracks its youngest ancestor rather than its oldest, and no random
individual is injected: the only age-0 material is the initial population. The consequence is that
this rung protects the youngest LINEAGE rather than continuously refreshing the population, so it is
a weaker guard against premature convergence than the paper's version.

Combined with islands and periodic migration it is the recipe behind Eureqa, the Schmidt and Lipson
engine (see [frameworks/21_feyn-qlattice.md](../frameworks/21_feyn-qlattice.md)), and it remains
cheap. `UNVERIFIED`: whether Eureqa itself used islands with migration. The dossier records AFP plus
an island model with migration as "the Eureqa recipe" without a primary source for the island half.

## References

- La Cava, W., Spector, L. and Danai, K. (2016). Epsilon-lexicase selection for regression.
  GECCO 2016, doi:10.1145/2908812.2908898.
- Deb, K., Pratap, A., Agarwal, S. and Meyarivan, T. (2002). A fast and elitist multiobjective
  genetic algorithm: NSGA-II. IEEE Transactions on Evolutionary Computation 6(2), pages 182 to 197,
  doi:10.1109/4235.996017.
- Schmidt, M. and Lipson, H. (2011). Age-fitness Pareto optimization. In Genetic Programming Theory
  and Practice VIII, doi:10.1007/978-1-4419-7747-2_8.
