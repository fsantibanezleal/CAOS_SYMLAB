# 18. ASM1 aerobic heterotrophic growth: a product of saturations

| | |
|---|---|
| Case id | `asm1-aerobic-growth` |
| Category | E, environment and energy |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, a `truth_node` is defined |
| Recovery regime | **structure+constants** |
| Generator | `asm1-aerobic-growth` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

The aerobic growth rate of heterotrophic bacteria in an activated sludge reactor, in grams of
chemical oxygen demand produced per cubic metre per day. It is the first process of the IWA Activated
Sludge Model No. 1, the model that describes how a municipal wastewater plant actually removes
organic pollution: bacteria consume dissolved organic substrate, using dissolved oxygen as the
electron acceptor, and turn it into more bacteria.

Why anyone wants a closed form: this rate is what sets the aeration demand, and aeration is typically
the largest electricity consumer in a wastewater plant. It also sets the sludge age, and therefore
the reactor volume. Every activated sludge design and every aeration control strategy is built on
this expression.

## The structure that makes this case worth having

The rate is a PRODUCT of two Monod switching functions and a biomass concentration:

$$\rho_1 = \mu_H \frac{S_S}{K_S + S_S}\cdot\frac{S_O}{K_{OH} + S_O}\cdot X_{B,H}$$

Each factor is a switch: growth is limited by whichever of substrate and oxygen is scarce, and the
product goes to zero if either does. That is the physically correct behaviour and it is why the model
multiplies rather than adds.

**A product of saturations has no additive decomposition.** A search that assembles sums of terms,
which is what a linear-in-features approach and many practical genetic-programming setups effectively
do, cannot represent this target no matter how many terms it uses. This is the case that separates
engines doing a real multiplicative search from those that only assemble sums, and the separation is
structural rather than a matter of budget.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `Ss` | $S_S$ | readily biodegradable substrate | g COD/m^3 | log-uniform, 0.1 to 200 |
| `So` | $S_O$ | dissolved oxygen | g O2/m^3 | log-uniform, 0.01 to 8 |
| `Xbh` | $X_{B,H}$ | heterotrophic biomass | g COD/m^3 | uniform, 500 to 4,000 |
| `rate` | $\rho_1$ | aerobic growth rate (target) | g COD/(m^3 d) | follows from the law |

Both concentrations are sampled LOG-uniformly, spanning from far below the half-saturation constant
to far above it, so each switching function is exercised across its full range. Dissolved oxygen from
0.01 to 8 g/m^3 covers anoxia through saturation with air, which is the range a real aeration
controller moves through.

Biomass is sampled linearly over the range of a real activated sludge reactor, roughly 0.5 to 4 grams
of COD per litre.

Fixed inside the generator, not sampled: $\mu_H = 4.0$ per day, $K_S = 10$ g COD/m^3 and
$K_{OH} = 0.2$ g O2/m^3.

## The published law

The expression above, with the constants above, giving

$$\rho_1 = 4.0\,\frac{S_S}{10 + S_S}\cdot\frac{S_O}{0.2 + S_O}\cdot X_{B,H}$$

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate:

    mul( mul(4.0, div(Ss, add(10.0, Ss))), mul( div(So, add(0.2, So)), Xbh ) )

## Recovery regime: structure+constants

The three kinetic parameters are BAKED IN, not input columns, so the numbers 4.0, 10 and 0.2 have to
be recovered along with the form. Material and stated: this case is not comparable with the
structure-only cases, and their recovery rates are never averaged.

The two half-saturation constants differ by a factor of fifty, so a constant-tuning stage has to get
a value near 0.2 right in the same expression as one near 10.

## Provenance

| | |
|---|---|
| Source | IWA ASM1 kinetic rate expressions, from the published BSM1 specification, research dossier 7.2.15 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |

The provenance question here is unusually clean and worth stating in full, because the recorded
caveat turns on it.

**The BSM1 model is PUBLISHED but its reference implementation is NOT.** The IWA technical report
gives the complete ASM1 stoichiometric matrix and the kinetic rate expressions, and the influent file
layout is documented verbatim as `t Si Ss Xi Xs Xbh Xba Xp So Sno Snh Snd Xnd Salk Q`. The MATLAB and
Simulink code is not published: the page states the files are available on request. No licence is
stated anywhere on that page, so the influent files are not a shipped artifact under any terms.

The conclusion recorded in the research phase, and applied here: treat BSM1 as a GENERATOR
SPECIFICATION rather than as a dataset. This lab implements and owns its own simulator rather than
claiming compatibility with one it cannot inspect. That is why the generator's caveat says so
explicitly rather than implying an association that does not exist.

**UNVERIFIED:** the BSM1 and BSM2 licence terms. No licence text was found anywhere on the IWA page.
This blocks any redistribution of their files; it does not block reimplementation from the published
specification, which is what this case does.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## Its relative in the set

Case [06](06_wwtp-removal-identity.md) is real data from an operating urban wastewater plant, where
the recoverable target is an accounting identity rather than a kinetic law. The two together cover the
same plant from opposite ends: the mechanism nobody measures directly, and the performance number
everybody reports.

## References

- Henze, M., Grady, C. P. L., Gujer, W., Marais, G. v. R. and Matsuo, T. (1987). Activated Sludge
  Model No. 1. IAWPRC Scientific and Technical Report No. 1. UNVERIFIED: no DOI resolved during the
  research phase.
- IWA Benchmark Simulation Model No. 1 (BSM1) general description technical report, IWA Task Group on
  Benchmarking of Control Strategies. UNVERIFIED licence; specification used, files not redistributed.
