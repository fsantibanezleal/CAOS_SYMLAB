# 20. Pipe friction factor: the Swamee-Jain explicit form

| | |
|---|---|
| Case id | `friction-factor` |
| Category | S, synthetic generators |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | NO, no `truth_node` is defined |
| Recovery regime | **structure+constants** |
| Generator | `friction-factor` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

The Darcy friction factor of turbulent flow in a pipe: the dimensionless coefficient that converts a
velocity head into a pressure loss per unit length. See case [03](03_nikuradse-friction.md) for the
physical framing; this page is the synthetic half of that pair.

Why anyone wants a closed form specifically here: the accepted correlation, Colebrook-White, is
IMPLICIT. It has the friction factor on both sides and must be solved iteratively for every
evaluation, which is unacceptable inside a network solver that evaluates it thousands of times per
iteration. Swamee and Jain published an explicit approximation to it, and explicit approximations to
Colebrook are a small literature in their own right. So this is a case where the object symbolic
regression produces, a compact explicit expression approximating something harder to evaluate, is
exactly the object the engineering literature has been producing by hand for fifty years.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `Re` | Re | Reynolds number | 1 | log-uniform, 5,000 to 1e8 |
| `relrough` | $\epsilon/D$ | relative roughness | 1 | log-uniform, 1e-6 to 5e-2 |
| `f` | $f$ | Darcy friction factor (target) | 1 | follows from the law |

Both inputs span many decades and both are sampled logarithmically, because the physics is
logarithmic: the correlation contains a base-10 logarithm and its behaviour is organised by orders of
magnitude, not by linear intervals.

The ranges are exactly the stated validity window of the correlation, no wider. Sampling outside it
would generate rows the source formula does not claim to describe.

Both inputs are dimensionless, so the unit-typed rung has nothing to constrain here; the manifest
records `units_declared` as 0.

## The published law

$$f = \frac{0.25}{\left[\log_{10}\!\left(\dfrac{\epsilon/D}{3.7} + \dfrac{5.74}{\mathrm{Re}^{0.9}}\right)\right]^{2}}$$

valid for $5000 \le \mathrm{Re} \le 10^{8}$ and $10^{-6} \le \epsilon/D \le 0.05$.

`ground_truth_known` is true.

**No machine-comparable truth is shipped.** No `truth_node` is defined for this generator, so the
equivalence test has no expression tree to score against. The case contributes to the error metrics
and the structural-distance statistics; the exact-recovery scorer reports "not checkable" rather than
zero, and reporting zero would be false.

## Recovery regime: structure+constants

The four numbers 0.25, 3.7, 5.74 and 0.9 are baked into the generator and are not input columns. A
candidate has to recover both the nested logarithmic form and those constants, which puts this among
the harder cases in the set: the constants sit inside a logarithm inside a square, so their influence
on the residual is indirect and a gradient-based tuner has a poorly conditioned problem.

## The laminar branch, deliberately excluded

The recorded caveat is a statement about what the case does NOT ask.

$$f = \frac{64}{\mathrm{Re}} \quad \text{(laminar, exact, Hagen-Poiseuille)}$$

is exact and belongs to a different flow regime. **No single expression covers both branches**, so a
case that sampled across the laminar-turbulent transition would be asking for something that does not
exist, and any engine would be scored against an impossible target. The generator samples the
turbulent branch only, and says so.

That is a general point this lab keeps making concretely: a case that cannot be solved should be
identified as such before it is run, not discovered afterwards from a poor score.

## The real-data twin, which is the strongest in the set

Case [03](03_nikuradse-friction.md) carries the 362 measured points from Nikuradse's 1933 rough-pipe
experiments. The arrangement is the one the whole lab is built around:

- HERE the answer is known exactly, so an engine can be calibrated and its recovery verified;
- THERE the accepted correlation is visibly incomplete, because the transitional-roughness hump in
  the measurements is genuinely not reproduced by Colebrook.

A method that recovers Swamee-Jain to the digit and then produces something worse than Colebrook on
the 362 points has told you something specific about itself that neither case alone would have shown.

## Provenance

| | |
|---|---|
| Source | Swamee-Jain explicit approximation to Colebrook-White, verified reference transcription, research dossier 7.2.9 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |
| Real-data twin | case [03](03_nikuradse-friction.md), PMLB `nikuradse_1`, MIT |

**UNVERIFIED:** no DOI for the Swamee and Jain 1976 paper was resolved during the research phase, and
none is stated here. The Colebrook 1939 paper that it approximates DID resolve and is cited below.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Colebrook, C. F. (1939). Turbulent flow in pipes, with particular reference to the transition
  region between the smooth and rough pipe laws. Journal of the Institution of Civil Engineers 11,
  pages 133 to 156, doi:10.1680/ijoti.1939.13150. The implicit correlation this case approximates.
- Swamee, P. K. and Jain, A. K. (1976). Explicit equations for pipe-flow problems. Journal of the
  Hydraulics Division, ASCE 102(5), pages 657 to 664. UNVERIFIED: no DOI resolved during the research
  phase.
