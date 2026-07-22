# 21. Heat exchanger effectiveness, counter-current NTU

| | |
|---|---|
| Case id | `heat-exchanger-ntu` |
| Category | S, synthetic generators |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure+constants` |
| Generator | `heat-exchanger-ntu` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

Effectiveness: the heat a heat exchanger actually transfers, divided by the most it could possibly
transfer with infinite area. It is a number between 0 and 1, and it is the standard way to
characterise an exchanger without knowing the outlet temperatures in advance.

Why anyone wants a closed form: the alternative is the log-mean temperature difference method, which
requires the outlet temperatures you are usually trying to compute, so it needs iteration. The
effectiveness-NTU formulation gives the answer directly from two dimensionless groups, which is why
it is the method used for RATING an existing exchanger and for every exchanger inside a process
simulation.

## The two groups

$$\mathrm{NTU} = \frac{UA}{C_{min}}, \qquad C_r = \frac{C_{min}}{C_{max}}, \qquad C = \dot{m}c_p$$

NTU is the exchanger's size measured in thermal units rather than square metres: how much heat
transfer capability it has relative to the stream that limits it. $C_r$ is how well matched the two
streams are.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `NTU` | NTU | number of transfer units, $UA/C_{min}$ | 1 | log-uniform, 0.1 to 8 |
| `Cr` | $C_r$ | heat capacity rate ratio | 1 | uniform, 0 to 0.95 |
| `eps` | $\varepsilon$ | effectiveness (target) | 1 | 0 to 1 |

NTU is sampled logarithmically from a badly undersized exchanger to a generously oversized one; above
about NTU 5 effectiveness is so close to its ceiling that additional area buys almost nothing, which
is visible in the sampled range.

$C_r$ stops at 0.95 on purpose, which is the subject of the next section.

Both inputs are dimensionless by construction, so the unit-typed rung has nothing to constrain and
this case is one of those where a units-aware search has no advantage available to it. That contrast,
against case [23](23_pump-affinity-power.md) where it has every advantage, is worth having in the set.

## The published law

$$\varepsilon = \frac{1 - e^{-\mathrm{NTU}(1 - C_r)}}{1 - C_r e^{-\mathrm{NTU}(1 - C_r)}}$$

for the counter-current arrangement. The parallel-flow arrangement is a different and simpler
expression, $\varepsilon = (1 - e^{-\mathrm{NTU}(1+C_r)})/(1 + C_r)$, and is not the shipped truth.

`ground_truth_known` is true and a `truth_node` is defined, so this case contributes to the exact
recovery rate:

    div( sub(1, exp(neg(mul(NTU, sub(1, Cr))))),
         sub(1, mul(Cr, exp(neg(mul(NTU, sub(1, Cr)))))) )

Note that the same subexpression appears in the numerator and the denominator. That is what makes
this case a good exercise for the deduplication rung: a search that re-evaluates the shared exponential
independently is doing twice the necessary work, and the count avoided is reported as a measurement
about the search rather than hidden as an implementation detail.

## Recovery regime: structure+constants

The only numeric literal in the expression is 1, appearing four times: twice as the leading term of a
difference and twice inside $1 - C_r$. None of them is an input column, so a candidate has to produce
the form with those literals in the right places. Recorded as `structure+constants` on the generator;
the numeric burden here is much lighter than on cases such as [20](20_friction-factor.md), which
bakes in four unrelated constants, and the label is carried as declared rather than softened.

## The removable singularity, which is the point of the case

At $C_r = 1$ both numerator and denominator go to zero and the expression is indeterminate. The limit
exists and is finite:

$$\varepsilon = \frac{\mathrm{NTU}}{1 + \mathrm{NTU}} \qquad (C_r = 1)$$

This is the physically important case, because $C_r = 1$ is BALANCED counter-current flow, the
arrangement a well-designed exchanger is usually built for.

The generator keeps $C_r$ below 0.95 so the sampled data contain no NaNs. A comment in the generator
calls the singularity "the subject of a dedicated variant"; **no such variant exists**. The nine
chips on this case are the eight ladder rungs plus the sparse-regression arm, all of them SEARCH
configurations over the same $C_r \le 0.95$ sample, so the $C_r = 1$ limit is reachable only through
the extrapolation view and never as a sampled case. The recorded caveat states why it matters:

> a fitted result that blows up at $C_r = 1$ is wrong in a way a plain error metric hides completely,
> and the extrapolation view is what exposes it

A candidate that fits the sampled region well and diverges just outside it scores excellently on test
error and is unusable. That failure is invisible in any aggregate metric computed on the sample, and
visible immediately in an extrapolation plot. It is the clearest argument in the set for why the
lab holds out an extrapolation region rather than only a random test split.

## Validity

Steady state, constant properties, no phase change, no losses to the surroundings. A condenser or an
evaporator violates the phase-change assumption, and for those $C_r = 0$ is the applicable limit,
which the sampled range does include.

## Provenance

| | |
|---|---|
| Source | Effectiveness-NTU method, counter-current arrangement, verified reference transcription, research dossier 7.2.7 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |

**UNVERIFIED:** the effectiveness-NTU relations were verified from a reference transcription rather
than a primary paper. No DOI is attached and none is invented here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard. The
only sampling intervention is the $C_r \le 0.95$ bound described above, which is part of the
generator's definition.

## References

- No primary reference with a resolvable DOI was recorded for the effectiveness-NTU method during the
  research phase. Treat the citation as UNVERIFIED rather than assuming a textbook DOI.
