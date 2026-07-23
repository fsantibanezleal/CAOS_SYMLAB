# 13. Flotation kinetics: first-order recovery

| | |
|---|---|
| Case id | `flotation-kinetics` |
| Category | M, mining and metallurgy |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure` |
| Generator | `flotation-kinetics` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

Cumulative recovery in a batch flotation test: the fraction of the valuable mineral that has reported
to the concentrate after a given flotation time. A batch test is the standard laboratory experiment
of mineral processing, a small cell run with the froth scraped into separate pans at fixed
intervals, and the recovery-versus-time curve it produces is what a circuit design is built on.

Why anyone wants a closed form: the rate constant and the ultimate recovery extracted from that curve
are the two numbers that size a flotation bank. How many cells in series, at what residence time, to
reach a target recovery is a direct calculation from the kinetic model. Fitting a curve gives a
number; recovering the FORM tells you whether the ore behaves as one floatable population or several,
which changes the circuit rather than just its size.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `t` | $t$ | flotation time | minutes | drawn from the standard batch grid: 0.5, 1, 2, 4, 8, 16 |
| `Rinf` | $R_\infty$ | ultimate recovery | 1 | uniform, 0.60 to 0.98 |
| `KB` | $K_B$ | average flotation rate constant | 1/min | uniform, 0.05 to 2.0 |
| `R` | $R$ | cumulative recovery fraction (target) | 1 | 0 to $R_\infty$ |

Time is DISCRETE by design: the six sampling intervals are the ones a real batch test uses, so the
design of experiments is the one a metallurgist would actually run rather than a dense uniform sweep.
That matters for the search: with only six distinct time values, an expression can fit the sampled
points while behaving badly between them, and the extrapolation split is what exposes it.

The rate constant range spans a factor of forty, from a slow-floating fine to a fast-floating
liberated particle. The ultimate recovery is bounded below 1 because no ore floats completely; some
fraction is locked in the gangue and will never report regardless of time.

## The published law

$$R(t) = R_\infty\left(1 - e^{-K_B t}\right)$$

This is the classical first-order batch model, and it is the one case in the generator set with a
PRIMARY, open-access, DOI-bearing source rather than a reference transcription:

> Bu, X., Xie, G., Peng, Y., Ge, L. and Ni, C. (2017). Kinetics of flotation: order of process, rate
> constant distribution and ultimate recovery. Physicochemical Problems of Mineral Processing 53(1),
> pages 342 to 365, doi:10.5277/ppmp170128, equation (8).

Verified during the research phase by extracting the open-access PDF, which is why the source string
on the generator names the equation number.

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate:

    mul( Rinf, sub(1, exp(neg(mul(KB, t)))) )

## Recovery regime: structure

$R_\infty$ and $K_B$ arrive as INPUT COLUMNS. Only the form is unknown: the search has to assemble an
exponential saturation from a product and a difference. It does not have to recover the numbers.
Stated explicitly because the distinction changes what the recovery rate means, and this case is not
comparable with the structure-plus-constants cases such as [17](17_lotka-volterra-rhs.md) or
[24](24_stokes-settling.md).

## The interesting question is not the fit

The recorded caveat names the Kelsall TWO-COMPONENT model,

$$R = R_\infty\left(1 - \phi e^{-k_f t} - (1 - \phi) e^{-k_s t}\right)$$

which splits a fast-floating and a slow-floating fraction. The cited paper is a survey of flotation
kinetic orders and rate-constant distributions, so the rectangular (Klimpel) and Gamma variants
belong to the same literature; UNVERIFIED here, since only equation (8) was extracted from the PDF
during the research phase and the generator's caveat names Kelsall alone.

**Neither the Kelsall form nor any other alternative model is shipped as a variant.** The nine chips
on this case are the eight ladder rungs plus the sparse-regression arm, all of them SEARCH
configurations over the same single-component data.

Whether the data justify ONE rate constant or TWO is a genuine accuracy-versus-complexity Pareto
decision on a real industrial problem, and it is the reason this case matters more than its fit
quality suggests. A two-component model will always fit at least as well; the question the Pareto
front answers is whether the improvement is worth the two extra parameters. That is the same question
metallurgists argue about in front of real batch data.

## Validity

Classical first-order batch flotation, assuming a SINGLE floatability component. Real ores are
mixtures of liberation classes with different rate constants, which is exactly what the Kelsall
variant exists to represent, so the shipped truth is a deliberate simplification and is labelled as
one.

## Provenance

| | |
|---|---|
| Source | Bu, Xie, Peng, Ge and Ni (2017), doi:10.5277/ppmp170128, equation (8), verified by extracting the open-access PDF |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |
| Real-data twin | case [10](10_flotation-silica.md), the plant soft sensor |

The research phase found NO open flotation kinetics dataset (recovery against time) anywhere. That
absence is what makes this a generator rather than a measured case, and it is recorded as a finding
rather than as a gap in the search.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Bu, X., Xie, G., Peng, Y., Ge, L. and Ni, C. (2017). Kinetics of flotation: order of process, rate
  constant distribution and ultimate recovery. Physicochemical Problems of Mineral Processing 53(1),
  pages 342 to 365, doi:10.5277/ppmp170128.
