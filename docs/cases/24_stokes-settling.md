# 24. Stokes terminal settling velocity

| | |
|---|---|
| Case id | `stokes-settling` |
| Category | S, synthetic generators |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, a `truth_node` is defined |
| Recovery regime | **structure+constants** |
| Generator | `stokes-settling` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

The steady velocity at which a small sphere falls through a viscous fluid, once drag has grown to
balance its submerged weight.

Why anyone wants a closed form: settling velocity is the design variable of every thickener,
clarifier, classifier and hydrocyclone in a mineral processing or water treatment plant, and it is
the quantity that decides how long a tailings pond takes to clear. It is also the basis of particle
size analysis by sedimentation. The expression is short enough to carry around and it makes the
dependencies explicit: quadruple the particle radius and the settling velocity goes up sixteenfold,
which is why fine grinding creates a dewatering problem.

## The published law

Drag on a sphere in creeping flow is $F_d = 6\pi\mu R v$. Setting it equal to the submerged weight
gives

$$v = \frac{2}{9}\,\frac{\rho_p - \rho_f}{\mu}\,g\,R^{2}$$

with $g = 9.80665$ m/s^2, the standard gravity used throughout this repo.

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate:

    mul( mul(2/9*g, div(sub(rho_p, rho_f), mu)), square(R) )

with the leading numeric constant folded to $\tfrac{2}{9}g$.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `R` | $R$ | particle radius | m | log-uniform, 1e-6 to 1e-3 (one micron to one millimetre) |
| `rho_p` | $\rho_p$ | particle density | kg/m^3 | uniform, 1,500 to 8,000 |
| `rho_f` | $\rho_f$ | fluid density | kg/m^3 | uniform, 900 to 1,300 |
| `mu` | $\mu$ | dynamic viscosity | Pa s | log-uniform, 1e-4 to 1e-1 |
| `v` | $v$ | terminal velocity (target) | m/s | follows from the law |

Radius spans three decades logarithmically, which is the range from a clay particle to a fine sand.
Particle density spans a light mineral to a heavy sulphide or a metal. Fluid density spans water to a
dense brine or a light slurry. Viscosity spans three decades from water to a viscous oil.

Dimensions are declared on every input, including the compound dimension of viscosity built as
$\mathrm{m}^{-1}\mathrm{kg}\,\mathrm{s}^{-1}$, so the unit-typed rung has real work to do here.

## Recovery regime: structure+constants

Gravity and the factor $2/9$ are baked in and are not input columns, so the numeric constant has to
be recovered along with the form. The four physical quantities do arrive as columns.

## Why the density DIFFERENCE is the whole case

The recorded caveat states it plainly and it is the sharpest small lesson in the set.

The target depends on $\rho_p - \rho_f$. Fluid density varies over a range of about 400 kg/m^3 in this
sample while particle density varies over about 6,500, so **a fit that latches onto $\rho_p$ alone
looks excellent** on almost any sample where the fluid is water-like. It will have a high coefficient
of determination, a low residual and a compact form, and it will be the WRONG LAW.

It fails the moment somebody applies it to a dense medium separation, where the fluid density is
deliberately raised to float part of the feed. There, $\rho_p - \rho_f$ can approach zero or change
sign, and the expression that ignores the difference predicts brisk settling for a particle that in
reality floats.

This is the clearest small example in the set of a correct-looking fit that is the wrong law, and it
is the reason the lab evaluates on a held-out extrapolation region rather than only on a random test
split: only leaving the sampled box exposes it.

## Validity, and the variant that leaves it

Stokes' law holds for particle Reynolds number below 1, which gives about 10 percent error at the
boundary. That limit is stated explicitly on the verified source.

The recorded caveat describes the deliberate variant: sample BEYOND $\mathrm{Re} = 1$ using an
empirical drag law, so the lab can show a law BREAKING DOWN outside its validity range. That is
described on the generator as the single most useful honest lesson available here, and it is the same
argument the friction-factor case makes about the laminar branch: knowing where a law stops is part
of knowing the law.

## Provenance

| | |
|---|---|
| Source | Stokes law, verified reference transcription, research dossier 7.2.10 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |
| Real-data twin | NONE, and stated as such |

The third recorded caveat is a negative result carried honestly: no open tabulated sphere-drag
experimental dataset was found during the research phase, so this case stays synthetic rather than
claiming a real twin it does not have.

**UNVERIFIED:** no DOI for Stokes' 1851 paper was resolved during the research phase, and none is
stated here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Stokes, G. G. (1851). On the effect of the internal friction of fluids on the motion of pendulums.
  Transactions of the Cambridge Philosophical Society 9, page 8. UNVERIFIED: no DOI resolved during
  the research phase.
