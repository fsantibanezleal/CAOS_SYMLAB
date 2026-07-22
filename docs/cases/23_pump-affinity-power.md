# 23. Pump affinity law: shaft power ratio

| | |
|---|---|
| Case id | `pump-affinity-power` |
| Category | S, synthetic generators |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure` |
| Generator | `pump-affinity-power` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |
| Inputs | SIX, the widest in the generator set |

## What the quantity is

The ratio of shaft power absorbed by a centrifugal pump or fan at one operating point to the power it
absorbs at another, when the two points differ in shaft speed, impeller diameter or fluid density.

Why anyone wants a closed form: this is the calculation behind variable-speed drives. Slowing a pump
from full speed cuts flow proportionally, cuts head as the square and cuts POWER AS THE CUBE, which
is why throttling a valve is a bad way to control flow and why variable-frequency drives pay for
themselves. Sizing a motor for a trimmed impeller, or predicting the duty of the same pump on a denser
slurry, is the same calculation.

## The published law

$$\frac{W_1}{W_2} = \frac{\rho_1}{\rho_2}\left(\frac{n_1}{n_2}\right)^{3}\left(\frac{D_1}{D_2}\right)^{5}$$

There are three affinity relations in the family and they differ only in their exponent pair:

| Quantity | Exponents on $(n_1/n_2, D_1/D_2)$ |
|---|---|
| volumetric flow | $(1, 3)$ |
| head or pressure rise | $(2, 2)$ |
| shaft power | $(3, 5)$ |

so the recovery target here is the INTEGER EXPONENT TRIPLE, and getting 3 and 5 in the right places
distinguishes the power law from its two siblings.

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate. The tree builds the fifth power as `square(square(x)) * x` and the cube as
`x * square(x)`, which is worth knowing when reading a structural distance: an engine that finds the
same function with a different factorisation of the exponents is close, not wrong.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `n1` | $n_1$ | shaft speed, point 1 | rpm | uniform, 600 to 3,600 |
| `n2` | $n_2$ | shaft speed, point 2 | rpm | uniform, 600 to 3,600 |
| `D1` | $D_1$ | impeller diameter, point 1 | m | uniform, 0.1 to 1.0 |
| `D2` | $D_2$ | impeller diameter, point 2 | m | uniform, 0.1 to 1.0 |
| `rho1` | $\rho_1$ | density, point 1 | kg/m^3 | uniform, 800 to 1,400 |
| `rho2` | $\rho_2$ | density, point 2 | kg/m^3 | uniform, 800 to 1,400 |
| `Wratio` | $W_1/W_2$ | shaft power ratio (target) | 1 | follows from the law |

The speed range runs from the synchronous speed of a two-pole motor at 60 Hz (3,600 rpm) down to
that of a ten-pole motor at 50 Hz (600 rpm). The diameter range covers a
small process pump to a large one. The density range runs from a hydrocarbon to a moderately dense
slurry.

Every input is sampled independently, so both operating points roam freely and the ratios span a wide
range in both directions. Six inputs is the widest search space among the generators, and the target
depends on all six.

**Dimensions ARE declared**: frequency on the two speeds, length on the two diameters, density on the
two densities, dimensionless on the target. The manifest records `units_declared` as 1, and this case
runs the FULL ladder including the unit-typed rung.

## Recovery regime: structure

All six physical quantities arrive as INPUT COLUMNS. There are no baked-in constants at all: the
expression is a pure product of powers of ratios of the given inputs. Only the FORM is unknown, which
makes this the cleanest structure-only case in the set and the fairest place to compare search
mechanisms without a constant-fitting stage confounding the result.

## Why this is the argument for unit-typed generation

The recorded caveat states it: this is the cleanest DIMENSIONAL-ANALYSIS case in the set, and the
natural place to demonstrate rung 8.

The target is dimensionless. Each of the three factors must therefore be dimensionless on its own,
and each is a ratio of two quantities with identical dimensions, so any exponent leaves it
dimensionless. Dimensional analysis alone does not fix the exponents 3 and 5; what it does do,
decisively, is forbid the vast majority of the expressions a blind search would otherwise construct:
anything adding a speed to a diameter, anything taking a logarithm of a density, anything mixing the
two operating points in a dimensionally inconsistent way.

Running the same case with rung 8 on and off, at the same budget, is the whole argument for
constraining GENERATION rather than filtering finished expressions. Filtering spends the evaluation
and then discards it; constraining never spends it.

**This case also found a real defect in the unit system.** The `sub` unit rule is shared by the binary
quotient and the UNARY reciprocal. The first implementation indexed the second child unconditionally
and raised an IndexError on `inv`, which surfaced here because reciprocals are exactly what these
ratios call for. A reciprocal negates the exponent vector. Fixed, with regression tests for the
reciprocal rule and for the reciprocal of a frequency being a time; the incident is recorded in
[`docs/method-families/05_units.md`](../method-families/05_units.md).

## Validity

The affinity relations assume CONSTANT EFFICIENCY between the two operating points. That is a good
approximation for a modest speed change and a poor one for a large impeller trim or a large speed
turndown, where the pump moves to a different part of its efficiency map. Nothing in the generated
data shows that breakdown, because the generator implements the idealised relation; the limitation is
recorded rather than demonstrated.

## Provenance

| | |
|---|---|
| Source | Affinity laws for centrifugal pumps and fans, verified reference transcription, research dossier 7.2.12 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |

**UNVERIFIED:** the affinity laws were verified from a reference transcription rather than a primary
paper, and no DOI attaches to them. None is invented here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Buckingham, E. (1914). On physically similar systems; illustrations of the use of dimensional
  equations. Physical Review 4(4), pages 345 to 376, doi:10.1103/PhysRev.4.345. The theorem behind
  the affinity relations, and behind rung 8.
- Tenachi, W., Ibata, R. and Diakogiannis, F. I. (2023). Deep symbolic regression for physics guided
  by units constraints. The Astrophysical Journal 959(2), 99, doi:10.3847/1538-4357/ad014c.
