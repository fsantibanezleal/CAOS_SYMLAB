# 25. Arrhenius temperature dependence

| | |
|---|---|
| Case id | `arrhenius-rate` |
| Category | S, synthetic generators |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure` |
| Generator | `arrhenius-rate` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

The rate constant of a chemical reaction as a function of absolute temperature. It is the single most
consequential temperature dependence in chemistry and materials engineering: reaction rates,
diffusion coefficients, creep rates, corrosion rates and semiconductor leakage currents all follow it.

Why anyone wants a closed form: the activation energy in the exponent is a physically meaningful
number that identifies the rate-limiting step. Two processes with the same rate at one temperature
and different activation energies diverge by orders of magnitude at another, so extrapolating a rate
to a temperature you did not measure requires the FORM, not an interpolation. Accelerated life
testing exists entirely because of this expression.

## The published law

$$k = A\,e^{-E_a/(RT)}$$

with $R = 8.314462618$ J/(mol K), the CODATA value used throughout this repo. The linearised form,
$\ln k = \ln A - (E_a/R)(1/T)$, is what an Arrhenius plot draws.

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate:

    mul( A, exp(neg(div(Ea, mul(8.314462618, T)))) )

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `T` | $T$ | absolute temperature | K | uniform, 280 to 420 |
| `Ea` | $E_a$ | activation energy | J/mol | uniform, 20,000 to 200,000 |
| `A` | $A$ | pre-exponential factor | 1/s | log-uniform, 1e4 to 1e14 |
| `k` | $k$ | rate constant (target) | 1/s | follows from the law |

Temperature spans roughly 7 to 147 degrees Celsius, the practical range of liquid-phase chemistry.
Activation energy spans 20 to 200 kJ/mol, from a diffusion-limited process to a strongly bond-breaking
one. The pre-exponential factor spans TEN DECADES and is sampled logarithmically, because it is a
collision-frequency term whose magnitude varies enormously between reaction types.

The consequence of those ranges is that the target itself spans an extreme dynamic range. That is a
real property of the physics and it makes the choice of noise model matter: multiplicative log-normal
noise is the right model for a rate, where the error scales with the value, and the additive
proportional-to-RMS model that the benchmark literature uses would drown every slow reaction in the
noise attached to a fast one.

`add_noise` implements both and the module says they are not interchangeable. **The offline runs use
the additive one.** `make_dataset` takes `multiplicative_noise` as a keyword defaulting to false and
`run_case` never passes it, so every baked artifact on this case at a nonzero noise level carries
additive noise proportional to the root-mean-square of a target that spans ten decades. Selecting
the multiplicative path for the rate-like generators is work not done, and the mismatch matters most
precisely here.

Temperature carries a declared temperature dimension and the pre-exponential factor a frequency
dimension; the activation energy is declared dimensionless, because a per-mole quantity has no
representation in the seven-vector of SI base dimensions this repo uses. That is a limitation of the
dimension system rather than of the physics and is recorded here rather than glossed.

## Recovery regime: structure

$E_a$ and $A$ arrive as INPUT COLUMNS, so only the form is unknown. The gas constant is the one
number in the expression and it is a fixed physical constant rather than a fitted parameter.

## Why this is a DIAGNOSTIC case, not a difficulty case

The recorded caveat is unusually direct and worth quoting in substance: this generator does not test
how good a search is, it tests whether the PRIMITIVE SET can express the answer at all.

The structure to recover is $\exp(-c/T)$: a division INSIDE an exponent. An engine whose operator set
has no path from a variable, through a reciprocal or a division, into the argument of an exponential
CANNOT produce this expression. No budget, no selection mechanism and no constant tuner will fix
that, because the target is not in the reachable space.

**Reporting that as a search failure would be a category error.** It is a representation failure, and
the two require different responses: one calls for a bigger budget or a better selection mechanism,
the other calls for a different operator set. Conflating them produces a benchmark number that
measures the wrong thing.

That is why this case is worth running FIRST, before the two real cases that need the same structure:

- [07 gas turbine NOx](07_gasturbine-nox.md), where thermal NOx formation is exponential in the
  inverse of flame temperature and a discovered expression containing $\exp(-a/\mathrm{TIT})$ is in
  the physically correct family;
- [09 CSTR conversion](09_cstr-conversion.md), where the same Arrhenius structure is nested inside a
  saturation.

If this case cannot be recovered, a poor result on either of those says nothing about the data.

## Validity

Empirically excellent over moderate temperature ranges, and NOT a derivation from first principles.
Transition state theory gives a related expression with an additional temperature prefactor, and over
a wide enough range the difference is measurable. The generator implements the classical form and the
limitation is stated on it.

## Provenance

| | |
|---|---|
| Source | Arrhenius equation, verified reference transcription, research dossier 7.2.2 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |

**UNVERIFIED:** no DOI for Arrhenius' 1889 publication was resolved during the research phase, and
none is stated here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- No primary reference with a resolvable DOI was recorded for the Arrhenius equation during the
  research phase. Treat the citation as UNVERIFIED rather than assuming one.
