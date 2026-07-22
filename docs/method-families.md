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
switch defaulting OFF. The `LADDER` dictionary in
[`search/engine.py`](../data-pipeline/symlab/search/engine.py) then turns those switches on in
order, which is what makes the Experiments page an ablation rather than an assertion.

Three steps of that chain move more than one switch, and reading the table as "one mechanism per
step" everywhere would misattribute their differences:

| Step | What changes |
|---|---|
| r1 to r2 | `linear_scaling` AND `interval_guard` together, with `interval_margin=0.25`. Keijzer's contribution is both, and this build does not separate them. |
| r5 to r6 | `age_fitness` and `n_islands=4` on, and `multi_objective` OFF. Three switches move, and one of them moves backwards. |
| r6 to r7 | both deduplication switches on, and `multi_objective` back on. |

Every other step (r3 constant tuning, r4 multi-objective survival, r5 epsilon-lexicase, r8 unit
typing) adds exactly one switch. `parsimony-arm` is not a rung at all: it is r3 plus
`parsimony_coefficient=0.001`, the single-objective comparison against r4.

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

What the table does NOT record is which case it was measured on, or which primitive set, so the
seconds above cannot be reproduced from this page alone. Re-running the same four configurations at
the same budget on 120 synthetic rows over three inputs reproduces the ordering and the
order-of-magnitude gap, not the absolute values: 0.19 s baseline, 1.43 s adding epsilon-lexicase,
0.38 s adding deduplication, 7.61 s adding both. The direction of the finding survives
re-measurement; the exact multipliers are a property of the case and are stated here as such.

An earlier version of this table blamed deduplication for the whole slowdown of the combined rung.
Isolating the switches showed that attribution was wrong. The corrected numbers are above, and the
episode is recorded because a wrong attribution in a comment is as misleading as a wrong number in a
result.

## Measured quality, on real data

From the committed artifact for the ore-mineralogy case
([`data/derived/ore-mineralogy-closure/run.json`](../data/derived/ore-mineralogy-closure/run.json),
2550 rows of real flotation-plant data, CC0, run at population 200 over 20 generations, seed 0):

| Rung | Test R2 | Selected model |
|---|---|---|
| Koza baseline | 0.908 | 8 nodes, the square of a constant minus a reciprocal logarithm |
| plus linear scaling | 0.968 | 17 nodes |
| plus constant tuning | 0.961 | 22 nodes |
| plus Pareto survival | 0.959 | 6 nodes, `-9.838 ln(SiO2) + 81.69` |

The rung that changes the ANSWER here is multi-objective survival, and it does so by giving up
0.009 of test R2 for a model a third of the size that reads as a law. Selecting on accuracy alone
would have kept the 17-node expression and reported a better number.

On a recoverable synthetic law, multi-objective survival recovers `2.5*(x1*x0) + 0.3` exactly at
7 nodes, where the baseline does not recover it at all. Reproduced while auditing this page: the
`r4-multi-objective` configuration at its ladder budget, on 200 rows of `2.5*x0*x1 + 0.3`, seed 0,
returns that expression at mean squared error 1.1e-30, and `r1-koza-baseline` on the same data
returns a 16-node expression at 1.1e-03 with no exact member anywhere on its front.
