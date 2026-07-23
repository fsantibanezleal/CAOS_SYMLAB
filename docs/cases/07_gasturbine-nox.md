# 07. Gas turbine NOx: thermal formation from combustion conditions

| | |
|---|---|
| Case id | `gasturbine-nox` |
| Category | I, industrial process |
| Data | REAL, 36,733 hourly records over five years |
| Ground truth known | NO |
| Machine-comparable truth | NO, loaded from a file; no in-repo expression to compare against |
| Recovery regime | `unknown` |
| Loader | `gasturbine-nox`, `load_gas_turbine` |

## What the quantity is

Nitrogen oxide concentration in the exhaust of an operating gas turbine, in milligrams per normal
cubic metre. NOx is a regulated pollutant: it drives ground-level ozone and acid deposition, and a
turbine's operating licence carries a hard concentration limit.

Why anyone wants a closed form: emissions compliance is managed by trading load against combustion
temperature in real time, and an explicit expression in the measured process variables is a
predictive emissions monitoring system, the accepted alternative to a physical continuous analyser.
Regulators accept models, and a model they can read is easier to accept than one they cannot.

The physics is the Zeldovich thermal mechanism: at flame temperature, atmospheric nitrogen is
oxidised at a rate governed by an Arrhenius factor,

$$\text{formation rate} \propto \exp\!\left(-\frac{E_a}{R\,T_{flame}}\right)$$

so NOx is EXPONENTIAL IN THE INVERSE of flame temperature. Turbine inlet temperature is the available
proxy for flame temperature, and a discovered expression containing $\exp(-a/\mathrm{TIT})$, or an
equivalently steep monotone in TIT, is in the physically correct family.

That structural demand is the reason this case is here. It requires a DIVISION INSIDE AN EXPONENT. A
primitive set without that path simply cannot express the answer, and the failure will look like a
search failure while being a representation failure. Case [25](25_arrhenius-rate.md) is the clean
synthetic diagnostic for exactly that question, and running it first tells you whether a poor result
here is about the data or about the operator set.

## Inputs

Nine process variables. Ranges re-measured from the loader output over all 36,733 rows on
2026-07-22; three cells of this table were wrong before that check and are corrected here.

| Column | Meaning | Unit | Range |
|---|---|---|---|
| `AT` | ambient temperature | degC | -6.2348 to 37.103 |
| `AP` | ambient pressure | mbar | 985.85 to 1036.60 |
| `AH` | ambient humidity | % | 24.085 to 100.20 |
| `AFDP` | air filter differential pressure | mbar | 2.0874 to 7.6106 |
| `GTEP` | gas turbine exhaust pressure | mbar | 17.698 to 40.716 |
| `TIT` | turbine inlet temperature | degC | 1000.80 to 1100.90 |
| `TAT` | turbine after temperature | degC | 511.04 to 550.61 |
| `TEY` | turbine energy yield | MWh | 100.02 to 179.50 |
| `CDP` | compressor discharge pressure | mbar | 9.8518 to 15.159 |
| `NOX` | nitrogen oxides (target) | mg/m^3 | 25.905 to 119.91 |

The turbine inlet temperature range is worth reading twice: 100.1 degrees across the whole five-year
record, which on the absolute scale is 1,273.95 K to 1,374.05 K. The exponential argument therefore
varies over a narrow window, and a search can approximate the exponential with a steep polynomial
inside that window and extrapolate catastrophically outside it. The extrapolation split is what
exposes that.

## Is there a published law

**No.** No equation generates these records; `ground_truth_known` is false. What exists is the
Zeldovich FAMILY described above, which is a hypothesis about the shape of the answer, not a target
to score against.

This case therefore contributes to the error metrics, the complexity front and the extrapolation
diagnostics. It contributes to no recovery rate, and reporting a zero recovery rate would be false.

The dataset also carries a carbon monoxide column, and the research phase identified the pair as the
best available "two competing mechanisms, one dataset" case: NOx is thermal-NOx dominated and rises
with temperature, CO is combustion-completeness dominated and rises at LOW load. A single expression
that fits both is wrong. This case ships the NOx half.

## Recovery regime

Not applicable, recorded as `unknown`.

## Provenance

| | |
|---|---|
| Source | UCI Machine Learning Repository, dataset 551, `gas+turbine+co+and+nox+emission+data+set.zip`, about 1 MB |
| Licence | CC BY 4.0 |
| Redistribution | `mirror` |
| Citation | Kaya, H., Tufekci, P. and Uzun, E. Gas Turbine CO and NOx Emission Data Set. UCI Machine Learning Repository, doi:10.24432/C5WC95. 36,733 hourly records, 2011 to 2015 |
| Verified on | 2026-07-21 |

## What the loader actually does

`load_gas_turbine` iterates the `.csv` members of the archive in sorted order, one per year, takes
the header from the first, and vertically stacks the years into a single matrix. Sorting the member
names is what makes the concatenation deterministic across platforms.

**The recorded defect, carried verbatim:**

> Carbon monoxide excluded from the inputs: it is a co-measured emission rather than a driver, and
> including it lets a search explain one pollutant with another.

That exclusion is a modelling decision with a reason, and the reason is that CO and NOx are both
outputs of the same combustion state. An expression predicting NOx from CO would fit well and would
be useless: it would tell an operator to change one pollutant in order to change another, with no
lever in between. The physics lever is temperature, and it stays in the inputs.

A second defect is applied by the preprocessor: deterministic subsampling to 4,000 rows with seed 0,
recorded on the manifest with the source row count alongside, so the app can state how many of the
available rows were used. Both lines appear in `manifests/gasturbine-nox.json`.

Units are declared as `1` on every input, so `units_declared` is 0 and this case runs the
`UNITLESS_LADDER` with the unit-typed rung omitted. The physical units of these columns ARE known and
are listed in the table above; wiring them into the loader's dimension vectors would make rung 8
meaningful on a real industrial case, and it is recorded as work not done.

## References

- Kaya, H., Tufekci, P. and Uzun, E. Gas Turbine CO and NOx Emission Data Set. UCI Machine Learning
  Repository, doi:10.24432/C5WC95.
- Zeldovich, Y. B. (1946). The oxidation of nitrogen in combustion and explosions. Acta
  Physicochimica URSS 21, pages 577 to 628. UNVERIFIED: no DOI was resolved for this reference during
  the research phase, and none is fabricated here.
