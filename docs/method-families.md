# Method families

Every rung of the ladder, with the mathematics this build uses and the exact constants it applies.
A page that describes the literature instead of the build is a reading list, and a reader cannot
check a number with it.

| Page | Rung | What it adds |
|---|---|---|
| [01 representation](method-families/01_representation.md) | 1 | The expression tree, and why there are no protected operators |
| [02 scaling and fitting](method-families/02_scaling-and-fitting.md) | 2, 3 | Closed-form linear scaling, then Levenberg-Marquardt on the numeric leaves |
| [03 selection and survival](method-families/03_selection-and-survival.md) | 4, 5, 6 | Pareto survival, epsilon-lexicase, age-fitness with islands |
| [04 deduplication](method-families/04_deduplication.md) | 7 | Structural and semantic hashing, and its measured cost |
| [05 units as a constraint](method-families/05_units.md) | 8 | Dimensional analysis constraining GENERATION |
| [06 exhaustive search](method-families/06_exhaustive.md) | 12 | The only rung that can prove a negative |
| [07 sparse regression](method-families/07_sparse-regression.md) | arm | The non-evolutionary family: a fixed library, a sparsity sweep, no search at all |

Pages 01 to 06 describe mechanisms inside one genetic-programming search. Page 07 does not: it is a
different family, run as its own arm on every case, and it is here because a ladder made only of GP
rungs is an excellent ablation of GP and a poor survey of symbolic regression.

## The ladder as configurations

`SearchConfig()` with no arguments is a faithful Koza-1992 baseline: every later mechanism is a
switch defaulting OFF. The `LADDER` dictionary adds exactly ONE mechanism per step, which is what
makes the Experiments page an ablation rather than an assertion.

## Measured cost, published

Cost is part of a rung's evaluation, not bookkeeping. Measured at population 100 over 10 generations
on 120 rows, seed 7:

| Configuration | Wall clock |
|---|---|
| baseline | 0.30 s |
| plus epsilon-lexicase | 6.73 s |
| plus deduplication | 0.75 s |
| plus both | 13.43 s |

Epsilon-lexicase dominates by an order of magnitude over deduplication. A selection method that buys
quality at 22 times the wall clock has to be compared at equal BUDGET, not at equal generation count,
and budget unfairness is a problem the benchmark literature acknowledges in itself.

An earlier version of this table blamed deduplication for the whole slowdown of the combined rung.
Isolating the switches showed that attribution was wrong. The corrected numbers are above, and the
episode is recorded because a wrong attribution in a comment is as misleading as a wrong number in a
result.

## Measured quality, on real data

On 383 hourly rows from a real flotation plant (ore mineralogy, CC0):

| Rung | Test R2 | Outcome |
|---|---|---|
| Koza baseline | -23.37 | worse than predicting the mean |
| plus linear scaling | 0.947 | recovered `-9.806 ln(SiO2) + 81.63` |
| plus constant tuning | 0.947 | no further gain on this case |

On a recoverable synthetic law, multi-objective survival recovers `2.5*(x1*x0) + 0.3` exactly at
7 nodes, where the baseline does not recover it at all.
