# 19. Wind turbine power curve with the Betz cubic and a rated plateau

| | |
|---|---|
| Case id | `wind-power-curve` |
| Category | E, environment and energy |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | NO, no truth node; see the generator for the recorded reason |
| Recovery regime | `structure+constants` |
| Generator | `wind-power-curve` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

Electrical power delivered by a wind turbine, in watts, as a function of the wind speed reaching it
and the state of the air it is moving through. The power curve is the single most important
characteristic of a turbine: energy yield assessments, warranty tests, curtailment accounting and
underperformance detection are all comparisons against it.

Why anyone wants a closed form: the curve is normally shipped as a lookup table, which cannot be
corrected for air density, cannot be differentiated, and cannot be transferred to a machine of a
different size. An explicit expression carrying the density term and the geometry can be, which is
what makes cross-site transfer testable.

## The physics, and where it stops

The kinetic energy flux through the rotor disc gives

$$P = \tfrac{1}{2}\rho S v^3 C_p$$

with $S$ the swept area and $C_p$ the power coefficient. Air density comes from the ideal gas law,

$$\rho = \frac{p}{R_d T}, \qquad R_d = 287.058\ \mathrm{J\,kg^{-1}K^{-1}}$$

so the cubic in wind speed carries a pressure-over-temperature correction, which is exactly the
structure the search has to assemble from two separate inputs.

The Betz limit caps $C_p$ at $16/27 = 0.593$; real machines peak between 0.45 and 0.50. The generator
uses $C_p = 0.47$, which is inside that band, so a discovered coefficient above the Betz limit is
detectably unphysical rather than merely inaccurate. That is what the category E label means in
practice: physical bounds a discovered form can visibly violate.

**The curve is PIECEWISE by construction.** Below cut-in the machine does not turn and power is zero.
Between cut-in and rated wind the cubic applies. Above rated wind the blades pitch to hold the
generator at its rating and power is flat. Above cut-out the machine shuts down for its own
protection and power returns to zero.

$$P = \begin{cases}
0 & v < v_{in} \\
\min\!\left(\tfrac{1}{2}\rho S v^3 C_p,\ P_{rated}\right) & v_{in} \le v \le v_{out} \\
0 & v > v_{out}
\end{cases}$$

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `v` | $v$ | upstream wind speed | m/s | uniform, 0 to 28 |
| `T` | $T$ | air temperature | K | uniform, 263 to 313 (about -10 to 40 degC) |
| `p` | $p$ | air pressure | Pa | uniform, 95,000 to 104,000 |
| `P` | $P$ | electrical power output (target) | W | 0 to 2,050,000 |

Wind speed is sampled from zero to beyond cut-out, so all four branches are populated including both
zero regions. That is the point: a sample restricted to the cubic region would make the case a plain
power law.

Fixed inside the generator, taken from the verified Kelmarsh geometry so the synthetic and real cases
are directly comparable: swept area 6,647.6 m^2 (a Senvion MM92, 92 m rotor), rated power 2,050 kW,
$C_p = 0.47$, cut-in 3 m/s, cut-out 25 m/s.

Dimensions ARE declared on all three inputs (velocity, temperature, pressure) and on the target
(power), which makes this one of the cases where the unit-typed rung has real work to do.

## The published law

Yes, the piecewise form above, from the Betz analysis plus the ideal gas law plus the machine's own
rating. `ground_truth_known` is true and `truth_latex` renders it.

**No machine-comparable truth is shipped.** No `truth_node` is defined, because the truth contains a
`min` and two hard gates, and an equivalence test over a piecewise definition is a different object
from the structural comparison the scorer performs. The case contributes to the error metrics and the
structural-distance statistics; the exact-recovery scorer reports "not checkable" rather than zero,
and reporting zero would be false.

## Recovery regime: structure+constants

Swept area, $C_p$, the rated power and both cut speeds are baked in, not input columns. The numbers
have to come out as well as the form.

## What the case actually tests

The recorded caveat states it: no single smooth expression represents this curve, so the case tests
whether the search reports an HONEST PARTIAL FIT or an overconfident smooth one.

A smooth expression fitted across all four branches will round the knee at rated wind, will predict
nonzero power below cut-in, and will predict large power above cut-out where the real machine
produces none. Each of those errors is small in aggregate, because the branches are short relative to
the whole range, and each of them is operationally serious. That is the specific failure a plain
error metric hides and the reason this case sits in the set.

## Provenance

| | |
|---|---|
| Source | Betz law and the verified Kelmarsh turbine geometry, research dossier 7.2.13 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |
| Real-data twin | Kelmarsh wind farm, Zenodo record 5841834, CC BY 4.0, identified but NOT shipped as a case |

The Kelmarsh geometry was verified during the research phase from `Kelmarsh_WT_static.csv`: Senvion
MM92, rated 2,050 kW, rotor diameter 92 m, hub height 78.5 m or 68.5 m, released by Cubico
Sustainable Investments under CC BY 4.0. Signal units were verified from
`Kelmarsh_WT_dataSignalMapping.csv`. Penmanshiel (Senvion MM82, 82 m rotor, same rating, same schema)
is the natural cross-site transfer test: does an expression learned at one rotor diameter hold at
another.

**UNVERIFIED:** no DOI for Betz's 1920 publication was resolved during the research phase, and none is
stated here.

The research phase also recorded a trap in this area, kept out of the set: the popular Kaggle wind
turbine SCADA file returns `"licenses": "Unknown"` from the Kaggle API, publishes no rotor geometry
so no physical constant is identifiable, and ships a `Theoretical_Power_Curve` column that leaks the
target outright.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Kelmarsh wind farm data. Zenodo record 5841834, CC BY 4.0, Cubico Sustainable Investments.
- Betz, A. (1920). Das Maximum der theoretisch moglichen Ausnutzung des Windes durch Windmotoren.
  Zeitschrift fur das gesamte Turbinenwesen 26, pages 307 to 309. UNVERIFIED: no DOI resolved during
  the research phase.
