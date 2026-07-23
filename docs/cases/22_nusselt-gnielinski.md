# 22. Convective heat transfer: Gnielinski, the misspecification case

| | |
|---|---|
| Case id | `nusselt-gnielinski` |
| Category | S, synthetic generators |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure+constants` |
| Generator | `nusselt-gnielinski` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

The Nusselt number: convective heat transfer at a surface, divided by what pure conduction through
the same fluid layer would deliver. It is the dimensionless answer to "how much better is moving
fluid than still fluid", and it is what converts a flow condition into a heat transfer coefficient.

Why anyone wants a closed form: every heat exchanger, every reactor jacket, every cooling channel is
sized from a Nusselt correlation. The correlation is where the empirical knowledge of the field is
stored, and it is precisely the kind of compact dimensionless relation symbolic regression is
supposed to be good at producing.

## Why this case exists, which is not to be solved

**This case is designed to be UNRECOVERABLE by the obvious hypothesis.**

The obvious hypothesis is a power law in the two dimensionless groups. It has excellent pedigree:
Dittus-Boelter,

$$\mathrm{Nu}_D = 0.023\,\mathrm{Re}_D^{4/5}\,\mathrm{Pr}^{0.4}$$

is exactly that, valid for $0.6 \le \mathrm{Pr} \le 160$, $\mathrm{Re}_D$ above about 10,000 and
length-to-diameter above about 10. It ships in this repo as a separate generator,
`nusselt-dittus-boelter`, which is NOT registered as a case; it exists so the power-law hypothesis has
a concrete referent.

Gnielinski's correlation covers a wider range and is NOT a pure power law. Data generated from it
cannot be fitted by one at low Reynolds number, because of the $(\mathrm{Re} - 1000)$ offset that
drives the Nusselt number towards zero as Reynolds approaches 1,000 while a power law drives it
towards a finite value.

So a search will report a good power-law fit here. Aggregate error will look acceptable, because the
sampled range is logarithmic and most of the rows sit where the two families agree.
**Reporting that fit and stopping is exactly the failure this lab exists to demonstrate.**

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `Re` | $\mathrm{Re}_D$ | Reynolds number | 1 | log-uniform, 3,000 to 5e6 |
| `Pr` | Pr | Prandtl number | 1 | log-uniform, 0.5 to 200 |
| `Nu` | $\mathrm{Nu}_D$ | Nusselt number (target) | 1 | follows from the law |

The Reynolds range starts at 3,000, which is the lower bound of the correlation's validity and also
the region where the misspecification bites hardest. Sampling from 10,000 instead would have hidden
the whole effect and turned this into a slightly awkward power-law case.

The Prandtl range spans gases (around 0.7) through water (around 7) to viscous oils (into the
hundreds). The correlation claims validity to Pr 2000; the generator samples to 200, so the sampled
window is a tenth of the claimed one at the top end and the case says nothing about the decade above
it.

Both inputs are dimensionless, so the unit-typed rung has nothing to constrain.

## The published law

$$\mathrm{Nu}_D = \frac{(f/8)(\mathrm{Re}_D - 1000)\mathrm{Pr}}{1 + 12.7\sqrt{f/8}\left(\mathrm{Pr}^{2/3} - 1\right)}, \qquad f = \left(0.79\ln\mathrm{Re}_D - 1.64\right)^{-2}$$

valid for $0.5 \le \mathrm{Pr} \le 2000$ and $3000 \le \mathrm{Re}_D \le 5\times10^{6}$.

Note the nesting: a friction factor defined by a logarithm raised to a negative power, which then
appears in the numerator, under a square root in the denominator, alongside a two-thirds power of
Prandtl. Six constants and four distinct nonlinearities.

`ground_truth_known` is true, and a `truth_node` IS defined, so the equivalence test runs and this
case contributes to the exact recovery rate. The intermediate quantity $f$ is built once as a
subtree and substituted into both the numerator and the denominator:

    f8 = div( inv(square(sub(mul(0.79, log(Re)), 1.64))), 8 )
    Nu = div( mul(mul(f8, sub(Re, 1000)), Pr),
              add(1, mul(mul(12.7, sqrt(f8)), sub(exp((2/3)*log(Pr)), 1))) )

so the composition through $f$ is represented, as a shared subtree rather than as a named
intermediate. $\mathrm{Pr}^{2/3}$ goes through the same `_pow_const` rewrite used elsewhere in the
module, exact because Prandtl is sampled strictly positive.

Being scoreable does not make this a case anybody should expect to recover. The case does not measure
whether a search can recover Gnielinski. It measures whether the reporting is honest when it cannot,
and a recovery flag of false here is the expected result rather than a finding about the engine.

## Recovery regime: structure+constants

Seven baked-in constants (0.79, 1.64, the exponent -2, the divisor 8, the offset 1000, 12.7 and the
2/3 power) and none of them arrive as columns.

## How to read a run on this case

The useful output is not a recovery flag. It is the pair of diagnostics:

- the residual pattern against Reynolds number, which should show the fit degrading systematically as
  Reynolds falls towards 3,000 rather than scattering randomly;
- the extrapolation error, which should be much worse than the interpolation error if the recovered
  form is the wrong family.

A method that reports a high coefficient of determination and no caveat has failed this case while
appearing to pass it.

## Provenance

| | |
|---|---|
| Source | Gnielinski correlation, verified reference transcription, research dossier 7.2.8 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |

The research phase found no open tabulated Nusselt-number experimental dataset, which is why this is a
generator rather than a measured case.

**UNVERIFIED, and recorded in the dossier's own unverified list:** the Dittus and Boelter 1930
publication (University of California Publications in Engineering 2, pages 443 to 461) did not resolve
in Crossref; the query returned HTTP 429 and was not retried. A commonly cited 1985 reprint in
International Communications in Heat and Mass Transfer exists and was NOT verified. No DOI for the
Gnielinski 1976 paper was resolved either. Neither identifier is invented here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Gnielinski, V. (1976). New equations for heat and mass transfer in turbulent pipe and channel flow.
  International Chemical Engineering 16(2), pages 359 to 368. UNVERIFIED: no DOI resolved during the
  research phase.
- Dittus, F. W. and Boelter, L. M. K. (1930). Heat transfer in automobile radiators of the tubular
  type. University of California Publications in Engineering 2, pages 443 to 461. UNVERIFIED: the
  Crossref query returned HTTP 429 and was not retried.
