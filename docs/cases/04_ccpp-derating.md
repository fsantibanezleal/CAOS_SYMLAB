# 04. Combined cycle power plant: ambient derating

| | |
|---|---|
| Case id | `ccpp-derating` |
| Category | I, industrial process |
| Data | REAL, 9,568 hourly records from an operating plant |
| Ground truth known | NO |
| Machine-comparable truth | no |
| Recovery regime | `unknown` |
| Loader | `ccpp-derating`, `load_ccpp` |

## What the quantity is

Net hourly electrical energy output of a combined cycle power plant, in megawatts, as a function of
the ambient conditions the plant is breathing. A combined cycle plant is a gas turbine whose exhaust
heat raises steam for a second, steam turbine; the two respond to the environment through different
mechanisms, and the dataset's own readme states that split explicitly.

Why anyone wants a closed form: the ambient derating curve is what a plant is dispatched and
contractually guaranteed against. On a hot afternoon the same machine produces materially less power
than on a cold morning, and the difference is money. A compact expression in four measured variables
is directly usable for dispatch planning, for performance-guarantee testing and for degradation
monitoring, which a black-box regressor is not.

The physical mechanism is mass flow. A gas turbine is a volumetric machine: it swallows a roughly
fixed volume of air per second, so the MASS it swallows, and therefore the power it makes, scales
with air density,

$$\rho = \frac{p}{R_d T}, \qquad R_d = 287.058\ \mathrm{J\,kg^{-1}K^{-1}}$$

which makes a term in ambient pressure over ambient temperature physically motivated. Neither the
ratio nor the density is an input column; a search has to assemble it from two separate inputs.

## Inputs

Verified ranges from the research phase against the extracted archive.

| Column | Symbol | Meaning | Unit | Range |
|---|---|---|---|---|
| `AT` | $T_{amb}$ | ambient temperature | degC | 1.81 to 37.11 |
| `V` | $V_{exh}$ | exhaust vacuum | cm Hg | 25.36 to 81.56 |
| `AP` | $p_{amb}$ | ambient pressure | mbar | 992.89 to 1033.30 |
| `RH` | RH | relative humidity | % | 25.56 to 100.16 |
| `PE` | $P_e$ | net hourly electrical energy output (target) | MW | 420.26 to 495.76 |

Sampling: hourly averages over six years, 2006 to 2011, with the plant at FULL LOAD only. That last
condition matters. The dataset contains no part-load operation, so any expression fitted here is an
expression about a fully loaded machine and says nothing about turndown.

The exhaust vacuum acts mainly on the steam turbine (condenser back-pressure), while temperature,
pressure and humidity act mainly on the gas turbine. Two mechanisms, one target.

## Is there a published law

**No.** There is no equation that generates these records, and the registry sets
`ground_truth_known` to false accordingly. What exists is a physical ANCHOR: the density term above,
so a form containing $a + b\,p_{amb}/T_{amb}$ is motivated, and the dominant behaviour is known to be
close to linear in ambient temperature and in exhaust vacuum, with the interesting structure in the
temperature-humidity interaction.

That anchor is a hypothesis to be tested against a discovered expression, not a truth to score
against. This case therefore contributes to the error metrics, to the complexity front and to the
extrapolation diagnostics only. It contributes to NO recovery rate, and reporting a zero recovery
rate for it would be false: the search cannot fail to recover something nobody has written down.

## Recovery regime

Not applicable, recorded as `unknown`.

## Provenance

| | |
|---|---|
| Source | UCI Machine Learning Repository, dataset 294, `combined+cycle+power+plant.zip`, about 3.67 MB |
| Licence | CC BY 4.0, quoted verbatim from the landing page during research |
| Redistribution | `mirror` |
| Citation | Tufekci, P. and Kaya, H. Combined Cycle Power Plant. UCI Machine Learning Repository, doi:10.24432/C5002N |
| Verified on | 2026-07-21 |

The associated paper is Tufekci, P. (2014), Prediction of full load electrical power output of a base
load operated combined cycle power plant using machine learning methods, International Journal of
Electrical Power and Energy Systems 60, pages 126 to 140, doi:10.1016/j.ijepes.2014.02.027.

## What the loader actually does

`load_ccpp` opens the zip, finds the first `.xlsx` member, and reads the FIRST SHEET only.

**The recorded defect, carried verbatim:** the archive ships five shuffled folds of the SAME 9,568
records, in different orders, for 5x2 cross-validation; the workbook name `Folds5x2_pp` says so.
Concatenating them would duplicate every row five times and destroy any held-out split, because a row
in the training fold would reappear in the test fold under a different index. Only the first sheet is
read.

A second defect is applied above the loader, by the preprocessor: deterministic subsampling to 4,000
rows with seed 0, to keep the search budget on the structure rather than on redundant rows. Both
lines appear in `manifests/ccpp-derating.json` under `contract.defects_applied`, and the manifest
also records the source row count so the app can state "4,000 of 9,568 used" rather than printing one
number that contradicts the case description.

The loader declares units on the inputs (degC, cmHg, mbar, %) but declares every dimension vector as
dimensionless, so `units_declared` is 0 in the manifest and this case runs the `UNITLESS_LADDER`: the
unit-typed rung is omitted rather than shown as a chip that does nothing.

## What the manifest measures

The ingestion contract for this case records, among other fields: rows kept, input keys, target key,
the count of DISTINCT target values and the repeat ratio (a leakage tripwire, low here), the
train/test/extrapolation split sizes, and the split note naming which input the extrapolation hold-out
was taken along. Those are the numbers to read; the specific values live in the manifest rather than
in this page because a re-bake changes them and a hand-copied number goes stale silently.

## References

- Tufekci, P. (2014). Prediction of full load electrical power output of a base load operated
  combined cycle power plant using machine learning methods. International Journal of Electrical
  Power and Energy Systems 60, pages 126 to 140, doi:10.1016/j.ijepes.2014.02.027.
- Tufekci, P. and Kaya, H. Combined Cycle Power Plant. UCI Machine Learning Repository,
  doi:10.24432/C5002N.
