# 15. Michaelis-Menten and Monod saturation

| | |
|---|---|
| Case id | `monod-saturation` |
| Category | B, biology and ecology |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure` |
| Generator | `monod-saturation` |
| Rows per run | 400, noise levels 0, 0.01, 0.05, 0.1 |

## What the quantity is

A saturating reaction rate. In enzyme kinetics it is the velocity at which an enzyme converts
substrate, rising linearly when substrate is scarce and flattening onto a ceiling when every active
site is occupied. In fermentation it is the specific growth rate of a microbial culture as a function
of the limiting nutrient. The algebra is identical, which is why one generator serves both tracks and
why this case is the bridge between the biology and industrial parts of the set.

Why anyone wants a closed form: the two parameters of that form are the quantities biochemistry
actually reports. $V_{max}$ is the catalytic capacity of the enzyme population and $K_m$ is the
substrate concentration at half that capacity, which is the standard measure of affinity. A
bioreactor is designed, and an inhibitor is characterised, by comparing these numbers between
conditions. A fitted curve without the form gives neither.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `a` | $a$ | substrate concentration | mol/m^3 | $K_m$ times a log-uniform factor on 0.03 to 30 |
| `Vmax` | $V_{max}$ | limiting rate | 1/s | uniform, 0.1 to 100 |
| `Km` | $K_m$ | substrate concentration at half $V_{max}$ | mol/m^3 | log-uniform, 0.01 to 10 |
| `v` | $v$ | reaction rate (target) | 1/s | follows from the law |

**The substrate sampling is the design decision that makes this case work.** Substrate is drawn
log-uniformly across three decades AROUND $K_m$ rather than uniformly over a fixed interval, so both
the linear regime and the saturating plateau are populated. Sampling uniformly would put almost every
row on the plateau, where the law is nearly constant and nothing can be identified: the data would
look clean, the fit would look excellent, and $K_m$ would be unrecoverable.

For the seed-0 bake recorded in `data/derived/monod-saturation/run.json`, the realised training
ranges were substrate about 0.005 to 15.5, $V_{max}$ about 0.73 to 99.9 and $K_m$ about 0.010 to 9.6.
Those are properties of that bake and will move with a re-run; the ranges in the table above are the
generator's declaration and will not.

Dimension vectors are declared dimensionless on all three inputs, so `units_declared` is 0 and this
case runs the `UNITLESS_LADDER` with the unit-typed rung omitted rather than shown as an inert chip.

## The published law

$$v = \frac{V_{max}\,a}{K_m + a}$$

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate:

    div( mul(Vmax, a), add(Km, a) )

## Recovery regime: structure

$V_{max}$ and $K_m$ arrive as INPUT COLUMNS, so the numbers are given and only the FORM is unknown:
one product over one sum, with the substrate appearing in both. That is the convention the published
physics benchmarks use, and it is materially easier than the structure-plus-constants cases in this
set. The distinction is stated because a recovery rate that mixes the two describes neither.

## Validity

The steady-state (Briggs-Haldane) approximation, with enzyme concentration far below substrate
concentration. Outside that regime the quasi-steady-state assumption fails and the observed velocity
is not this function of the instantaneous substrate.

## The linearisation, shipped as a worked example of a mistake

The recorded caveat names it: a Lineweaver-Burk transformation,

$$\frac{1}{v} = \frac{K_m}{V_{max}}\cdot\frac{1}{a} + \frac{1}{V_{max}}$$

fits this law EXACTLY and turns the estimation into a straight line, which is why it was standard
practice for decades. It also distorts the error structure: taking reciprocals inflates the weight of
the lowest-velocity, noisiest measurements and compresses everything else, so the fitted parameters
are biased even though the algebra is exact. The lab ships that as a worked example of a
transformation that helps a human read a plot and hurts the fit underneath it.

## Provenance

| | |
|---|---|
| Source | Michaelis-Menten kinetics, verified reference transcription, research dossier 7.2.1 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |
| Real-data twin | the penicillin fermentation case, identified but NOT shipped as a case |

**UNVERIFIED:** no DOI for the 1913 Michaelis and Menten paper or for Monod's 1949 growth paper was
resolved during the research phase, and none is stated here. The research phase also looked for a
standalone symbolic-regression rediscovery paper for this law and did not find one: the rediscovery
is demonstrated as one of three test systems inside the implicit-SINDy work (Mangan, Brunton, Proctor
and Kutz, arXiv:1605.08368), which is recorded as the closest available reference rather than as the
paper that does not exist.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Mangan, N. M., Brunton, S. L., Proctor, J. L. and Kutz, J. N. (2016). Inferring biological networks
  by sparse identification of nonlinear dynamics. arXiv:1605.08368. Recovers rational rate laws
  including Michaelis-Menten from simulated time series.
- The R `datasets` package ships `Puromycin`, 23 rows, whose own documentation states the ground truth
  as `rate ~ Vm * conc / (K + conc)`. It is the canonical small real Michaelis-Menten table and is
  recorded in the research dossier as a unit-test-tier candidate, not shipped as a case here.
