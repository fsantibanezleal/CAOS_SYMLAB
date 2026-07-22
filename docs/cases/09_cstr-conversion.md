# 09. Non-isothermal CSTR conversion

| | |
|---|---|
| Case id | `cstr-conversion` |
| Category | I, industrial process |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure+constants` |
| Generator | `cstr-conversion` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

Fractional conversion in a continuous stirred-tank reactor: the fraction of the reactant fed to the
vessel that has been consumed by the time the stream leaves it. A CSTR is the workhorse continuous
reactor of the chemical industry, an agitated vessel with a feed in and a product out, assumed
perfectly mixed so that the contents are everywhere at the outlet composition.

Why anyone wants a closed form: conversion is the variable a reactor is designed and controlled
around. It sets the vessel volume for a required production rate, it sets the recycle load on the
separation train downstream, and it responds to temperature far more sharply than intuition suggests.
An explicit expression in residence time and temperature is directly usable for sizing and for
control design.

## The derivation the generator implements

Steady-state mass balance on the reactant, with residence time $\tau = V/Q$ and first-order kinetics
$r_A = k C_A$, gives $C_A = C_{A0}/(1 + k\tau)$, so conversion is

$$X = \frac{k\tau}{1 + k\tau}$$

The product $k\tau$ is the Damkohler number: the ratio of the reaction rate to the flow rate, the
dimensionless group that says whether the vessel is kinetics-limited or residence-limited. Conversion
SATURATES in it, approaching 1 from below and never reaching it.

The second structure is inside $k$. The rate constant is Arrhenius in temperature, so the full target
is

$$X = \frac{\tau A e^{-E_a/(RT)}}{1 + \tau A e^{-E_a/(RT)}}$$

Two nested structures the search has to find TOGETHER: a saturation in a product, and an exponential
of a reciprocal inside that product. Either alone is a solved case elsewhere in this set; the
composition is what makes this one hard.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `tau` | $\tau$ | residence time, $V/Q$ | s | log-uniform on 0.1 to 100 |
| `T` | $T$ | reactor temperature | K | uniform on 300 to 420 |
| `X` | $X$ | fractional conversion (target) | 1 | 0 to 1 by construction |

Residence time is sampled LOG-uniformly across three decades, because the interesting behaviour is
the crossover between the kinetics-limited and conversion-limited regimes and a linear sample would
put almost every row on one side of it.

Fixed inside the generator, not sampled: $E_a = 60{,}000$ J/mol, $A = 10^7$ s^-1, and the gas
constant $R = 8.314462618$ J/(mol K), the CODATA value used throughout this repo.

The recorded caveat explains the choice: the activation energy and pre-exponential factor are FIXED
rather than sampled, so the target is a function of two inputs. Sampling them too would make the
problem trivially separable and remove the point of the case.

## The published law

Yes, the expression above, standard reactor engineering. `ground_truth_known` is true and
`truth_latex` renders the full nested form.

**No machine-comparable truth is shipped.** No `truth_node` is defined for this generator, so the
equivalence test has no tree to compare against. The case contributes to the error metrics and to the
structural-distance statistics; the exact-recovery scorer reports "not checkable" rather than zero,
and reporting zero would be false.

The reason a truth node is hard to write here is itself informative: the correct expression contains a
constant in an exponent (60000) and a constant multiplying an exponential ($10^7$) whose recovered
values will be correlated, so an equivalence test would need a numerical tolerance policy rather than
a structural comparison. That is recorded rather than papered over.

## Recovery regime: structure+constants

The two Arrhenius parameters are baked into the generator and are not input columns, so the numbers
have to be recovered as well as the form. That is the harder half of the taxonomy and it is stated
here rather than left implicit, because a recovery rate quoted across this case and a structure-only
case would describe neither.

## Validity

Steady state, perfect mixing, first-order irreversible kinetics, constant density. Each of those is a
real restriction: a real vessel has mixing time constants, most industrial reactions are not
first-order, and liquid-phase density changes with conversion for many systems.

## Provenance

| | |
|---|---|
| Source | Continuous stirred-tank reactor, first-order kinetics, verified reference transcription, research dossier 7.2.3 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |

**UNVERIFIED:** the dossier's verification was a reference transcription rather than a primary paper;
no DOI is attached to this derivation and none is invented here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## Its relatives in the set

- [25 Arrhenius](25_arrhenius-rate.md) isolates the exponential-of-a-reciprocal half as a pure
  diagnostic of the primitive set. Run it first: if it fails, the failure here is a representation
  failure, not a search failure.
- [15 Monod](15_monod-saturation.md) isolates the saturating-hyperbola half, in its
  $z/(\text{const}+z)$ form.
- [07 gas turbine NOx](07_gasturbine-nox.md) is the real-data case that needs the same
  division-inside-an-exponent path, on measurements where no truth exists.

## References

- No primary reference with a resolvable DOI was recorded for this derivation during the research
  phase. It is standard reactor engineering, transcribed from a verified reference; treat the
  citation as UNVERIFIED rather than assuming a textbook DOI.
