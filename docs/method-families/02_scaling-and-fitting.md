# 2 and 3. Scaling and constant fitting

A tree search spends a surprising share of its budget nudging numeric leaves towards values a local
optimiser reaches in a handful of iterations. Two mechanisms address that, and they are
complementary rather than alternatives.

## Linear scaling, in closed form

For a squared-error objective the optimal slope and intercept have a closed form, so they need not be
searched at all:

    a = cov(y, f) / var(f)
    b = mean(y) - a * mean(f)

The scaled candidate `a*f + b` is optimal in `a` and `b` by construction. The search is freed to look
for the SHAPE of the relationship, which is the part evolution is actually good at.

Two honesty points this build records rather than hides:

1. **Scaling changes what "the discovered expression" means.** The expression reported is the SCALED
   one, with `a` and `b` folded in as explicit constants. Reporting an unscaled skeleton and scoring
   it scaled would inflate every number.
2. **A degenerate candidate is not scored as a fit.** When the centred sum of squares of `f` falls
   below `var_floor = 1e-12` the candidate is constant and carries no information. `fit` returns
   slope 0, the mean of `y` as the intercept, and `degenerate=True`, so the candidate is scored as
   the trivial constant model it is: its loss comes out as the variance of `y`. The flag is asserted
   by the test suite and is not carried into the exported artifact, so a reader sees the degenerate
   candidate as a constant model rather than as a labelled one.

## Nonlinear constant fitting

The remaining numeric leaves are fitted jointly by Levenberg-Marquardt and written back into the
tree, so the improvement is inherited rather than rediscovered each generation. The Jacobian is
computed by forward differences, with the step for parameter `j` set to `1e-6 * max(1, |theta_j|)`
so it stays meaningful across the range of values constants actually take. It is a finite-difference
Jacobian rather than an analytic one because the operator table is open: an analytic Jacobian would
have to supply a derivative for every primitive a case might add.

"Jointly" is bounded on three sides, and the bounds are the reason this is a rung with a measurable
cost rather than a free improvement. The engine tunes only the best `tuning_top_k = 30` candidates,
only on generations divisible by `tuning_every = 5`, for at most `tuning_iterations = 15` LM
iterations, and `tune_population` skips any expression carrying more than `max_constants = 12`
numeric leaves.

### Identifiability is checked, not assumed

When two constants are redundant, for example the `a` and `b` in `a * (b * x)`, infinitely many pairs
give the same output, the Jacobian is rank-deficient, and the fitted values carry no information.
That is detected by a singular-value decomposition on the first iteration, and `levenberg_marquardt`
returns `identifiable=False` with a note naming the rank and the parameter count, rather than
returning arbitrary values that look like measurements.

Where that verdict stops is worth stating, because the check is only useful if a reader can see it:
`tune_population`, the only caller the engine uses, returns the tuned expressions and a count of how
many improved, and discards the identifiability field. Nothing downstream of it carries the verdict,
so it does not reach the artifact or the app today.

## Measured effect

From the committed artifact for the ore-mineralogy case
([`data/derived/ore-mineralogy-closure/run.json`](../../data/derived/ore-mineralogy-closure/run.json)),
2550 rows of real flotation-plant data at population 200 over 20 generations, seed 0:

| Configuration | Test R2 | Selected complexity |
|---|---|---|
| Koza baseline | 0.908 | 8 |
| plus linear scaling and interval guards | 0.968 | 17 |
| plus constant tuning | 0.961 | 22 |

Linear scaling accounts for the accuracy gain on this case. Constant tuning does not add to it here,
and it costs complexity, which is itself worth reporting: a mechanism that does not help on a given
case should be visible as such rather than absorbed into a bundle. What tuning does change on this
case is the extrapolation error, which falls from 754 to 7.1 mean squared error on the held-out
outer rows: the rung earns its place outside the training box rather than inside it.

## Reference

Kommenda, M., Burlacu, B., Kronberger, G. and Affenzeller, M. (2020). Parameter identification for
symbolic regression using nonlinear least squares. Genetic Programming and Evolvable Machines 21,
pages 471 to 501, doi:10.1007/s10710-019-09371-3.
