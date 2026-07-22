# 17. Lotka-Volterra: the prey right-hand side

| | |
|---|---|
| Case id | `lotka-volterra-rhs` |
| Category | B, biology and ecology |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure+constants` |
| Generator | `lotka-volterra-rhs` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

The rate of change of a prey population, in individuals per year, given the current abundance of prey
and of the predator eating them. It is one half of the oldest coupled model in ecology: prey breed in
proportion to their own number and are removed in proportion to the ENCOUNTER RATE between the two
species, which is proportional to the product of the abundances.

Why anyone wants a closed form: the bilinear interaction term is the modelling claim. It asserts that
predation scales with the product of the two populations, which is the mass-action assumption
borrowed from chemical kinetics. Alternatives exist (Holling type II saturating responses,
ratio-dependent responses) and they predict qualitatively different outcomes for the same data, so
recovering WHICH functional response the data support is a real question, not a fitting exercise.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `H` | $H$ | prey abundance | 1 | uniform, 5 to 90 |
| `L` | $L$ | predator abundance | 1 | uniform, 5 to 60 |
| `dHdt` | $dH/dt$ | prey growth rate (target) | 1/a | follows from the law |

The abundance ranges are the scale of the lynx-hare pelt record, thousands of animals, and the
parameters are chosen to reproduce roughly its ten-year cycle.

Sampling is over a BOX in the two abundances rather than along a trajectory. That is a deliberate
simplification and it makes this case easier than case [02](02_strogatz-dynamics.md), where the
states lie on an orbit and whole regions of the plane carry no data. Both are shipped so the contrast
is visible.

## The published law

$$\frac{dH}{dt} = \alpha H - \beta H L, \qquad \alpha = 0.55,\ \beta = 0.028$$

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate:

    sub( mul(0.55, H), mul(0.028, mul(H, L)) )

The full system carries a second equation, $dL/dt = -\gamma L + \delta H L$, whose parameters are
deliberately NOT used by this generator: only the prey right-hand side is generated here, so only
$\alpha$ and $\beta$ appear. That is recorded in the generator's own comment rather than left for a
reader to infer from the code.

## Recovery regime: structure+constants

The two parameters are BAKED IN, not input columns. A candidate has to recover both the form and the
numbers 0.55 and 0.028. That makes this materially harder than the structure-only biology cases
[15](15_monod-saturation.md) and [16](16_theta-logistic-growth.md), and the three are never averaged
into a single recovery rate.

The two constants also differ by a factor of about twenty in magnitude, so a search that fits them
jointly has to get a small coefficient right in the presence of a large one; a constant-tuning stage
that rescales poorly will find the linear term and miss the interaction.

## The harder formulation, shipped as its own variant

The recorded caveat names it. The system has a CONSERVED QUANTITY:

$$V = \delta H - \gamma \ln H + \beta L - \alpha \ln L$$

which is constant along every orbit. Recovering an invariant is not the same task as recovering a
derivative: the target is not measured at all, it is the thing that does not change, so the search is
looking for a function of the states whose value is the same on every row rather than one that
predicts a column. That is the formulation Schmidt and Lipson used to recover Hamiltonians and
Lagrangians from motion-tracking data, and it is harder.

It ships as its own variant so that recovering the derivative and recovering the invariant can be
compared on the same system, which is the only way to say by how much the second is harder.

## Provenance

| | |
|---|---|
| Source | Lotka-Volterra predator-prey model, lynx-hare parameterisation, research dossier 7.2.14 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |
| Real-data twin | the lynx-hare series, 21 points, 1900 to 1920, identified but NOT shipped as a case |

**UNVERIFIED:** no DOI for Lotka's 1925 or Volterra's 1926 primary publications was resolved during
the research phase, and none is stated here.

The lynx-hare twin is 21 rows. That is small enough to be honest about: it can show whether a
recovered form survives contact with a real series, and it cannot support any claim about noise
robustness.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Schmidt, M. and Lipson, H. (2009). Distilling free-form natural laws from experimental data.
  Science 324(5923), pages 81 to 85, doi:10.1126/science.1165893. The invariant-recovery formulation.
- Chen, Y., Angulo, M. T. and Liu, Y.-Y. (2019). Revealing complex ecological dynamics via symbolic
  regression. BioEssays 41(12), e1900069, doi:10.1002/bies.201900069. Recovers Lotka-Volterra,
  Holling type II, DeAngelis-Beddington and Crowley-Martin functional responses when the search is
  seeded with a dictionary of ecological forms.
