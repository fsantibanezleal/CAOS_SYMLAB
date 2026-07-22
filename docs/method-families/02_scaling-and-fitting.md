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
2. **A degenerate candidate is reported, not scored as a fit.** When `var(f)` is zero the candidate is
   constant and carries no information. That is reported explicitly, because a constant model scoring
   well means the target has no signal the primitives can reach.

## Nonlinear constant fitting

All remaining numeric leaves are fitted jointly by Levenberg-Marquardt and written back into the
tree, so the improvement is inherited rather than rediscovered each generation. The Jacobian is
computed by forward differences with a step scaled to each parameter's magnitude, because the
operator table is open: an analytic Jacobian would have to supply a derivative for every primitive a
case might add.

### Identifiability is checked, not assumed

When two constants are redundant, for example the `a` and `b` in `a * (b * x)`, infinitely many pairs
give the same output, the Jacobian is rank-deficient, and the fitted values carry no information.
That is detected by a singular-value decomposition and REPORTED as parameters not identifiable,
rather than returning arbitrary values that look like measurements.

## Measured effect

On 383 hourly rows of real flotation-plant data:

| Configuration | Test R2 |
|---|---|
| Koza baseline | -23.37 |
| plus linear scaling and interval guards | 0.947 |
| plus constant tuning | 0.947 |

The baseline is worse than predicting the mean. Linear scaling alone accounts for the entire gain on
this case, and constant tuning adds nothing further, which is itself worth reporting: a mechanism
that does not help on a given case should be visible as such rather than absorbed into a bundle.

## Reference

Kommenda, M., Burlacu, B., Kronberger, G. and Affenzeller, M. (2020). Parameter identification for
symbolic regression using nonlinear least squares. Genetic Programming and Evolvable Machines 21,
pages 471 to 501, doi:10.1007/s10710-019-09371-3.
