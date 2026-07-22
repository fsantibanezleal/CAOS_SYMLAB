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
discard them. Epsilon is set automatically from the median absolute deviation of that case's errors:

    epsilon_j = median_i | e_ij - median_k e_kj |

That automatic epsilon is what makes lexicase work on continuous targets at all.

**Its cost is real and is published.** At population 100 over 10 generations on 120 rows it takes the
run from 0.30 s to 6.73 s, roughly 22 times. A selection method that buys quality at that price has
to be compared at equal BUDGET rather than at equal generation count.

Down-sampling evaluates on a random subset of cases per selection event, which is the standard way to
make it affordable. It changes the selection pressure, so it is recorded in the manifest rather than
treated as a free speedup.

## NSGA-II survival

Complexity stops being a penalty term and becomes a second objective. Survival is by non-domination
rank with crowding distance breaking ties, and boundary points receive infinite distance so the
extremes of the front are never lost. Without that a front collapses towards its middle over
generations.

The output stops being a model and becomes a FRONT. This is the rung that changes what the whole
product reports.

The textbook presentation of the sort is a nested double loop. A direct transcription dominated the
wall clock here, 39.2 s against 0.8 s for the same budget without multi-objective survival, so it is
computed as a single vectorised domination matrix instead. The result is identical; only the constant
factor changes.

## Age-fitness Pareto survival

Age becomes an objective, where age is how many generations an individual's oldest ancestor has
survived. A young individual only has to beat older ones on error, so fresh material is not
immediately outcompeted by an entrenched lineage. That is the mechanism that stops premature
convergence, and it costs one extra objective.

Combined with islands and periodic migration it is the recipe the best-known commercial engine of the
previous generation used, and it remains cheap and competitive.

## References

- La Cava, W., Spector, L. and Danai, K. (2016). Epsilon-lexicase selection for regression.
  GECCO 2016, doi:10.1145/2908812.2908898.
- Deb, K., Pratap, A., Agarwal, S. and Meyarivan, T. (2002). A fast and elitist multiobjective
  genetic algorithm: NSGA-II. IEEE Transactions on Evolutionary Computation 6(2), pages 182 to 197,
  doi:10.1109/4235.996017.
- Schmidt, M. and Lipson, H. (2011). Age-fitness Pareto optimization. In Genetic Programming Theory
  and Practice VIII, doi:10.1007/978-1-4419-7747-2_8.
