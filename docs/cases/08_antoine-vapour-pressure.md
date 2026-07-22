# 08. Antoine vapour pressure (water, lower window)

| | |
|---|---|
| Case id | `antoine-vapour-pressure` |
| Category | I, industrial process |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure+constants` |
| Generator | `antoine-vapour-pressure` in [`cases/generators.py`](../../data-pipeline/symlab/cases/generators.py) |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

Saturation vapour pressure: the pressure at which a pure liquid and its own vapour sit in
equilibrium at a given temperature. It is the quantity that decides whether a stream boils, and it is
the input every distillation, evaporation and flash calculation starts from. Column temperature
profiles, relief-valve sizing and solvent-recovery designs all reduce to repeated evaluations of
this function.

Why anyone wants a closed form rather than a table: the calculation is inside an inner loop. A
distillation simulation evaluates vapour pressure for every component on every tray at every
iteration, so a three-parameter expression is not a convenience, it is what makes the simulation
tractable.

## Inputs

One input, which makes this the smallest case in the set and a useful floor for the search.

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `T` | $T$ | temperature | degC | uniform on -20 to 100 |
| `p` | $p$ | saturation vapour pressure (target) | mmHg | follows from the law |

Non-SI units on both axes are deliberate: the verified constants below are published for degrees
Celsius and millimetres of mercury, and converting them would mean transcribing a different constant
set than the one that was checked.

Because the input is a temperature in Celsius on a dimensionless declaration, this case carries no
usable dimension vector and the unit-typed rung has nothing to constrain.

## The published law

$$\log_{10} p = A - \frac{B}{C + T}, \qquad A = 8.07131,\ B = 1730.63,\ C = 233.426$$

equivalently $p = 10^{\,A - B/(C+T)}$, which is the form the generator evaluates.

The constants above are the verified water constants for the window -20 to 100 degC. A DIFFERENT
verified set, $A = 8.14019$, $B = 1810.94$, $C = 244.485$, covers 99 to 374 degC. Both were checked
during the research phase against the same reference; this case ships the lower window and says so in
its name.

The structure to recover is the RECIPROCAL-SHIFTED temperature form $B/(C + T)$. It is not a plain
reciprocal and not a plain linear term: the shift $C$ moves the pole away from absolute zero and is
what lets three constants cover a hundred-degree span.

**No machine-comparable truth is shipped.** The generator carries `truth_latex` and `truth_infix` but
no `truth_node`, so the equivalence test has no expression tree to compare a candidate against. This
case contributes to the error metrics and to the structural-distance statistics; the exact-recovery
scorer reports "not checkable" rather than zero. Reporting zero would be false, because the search
was never scored against a comparable object.

## Recovery regime: structure+constants

Material, and stated rather than glossed. $A$, $B$ and $C$ are NOT input columns. They are baked into
the generator, so a candidate expression has to produce the right FORM and the right three NUMBERS.
That is a harder task than the structure-only cases, where the parameters arrive as columns and only
the assembly is unknown, and the two are never averaged into one recovery rate.

The practical consequence is that this case exercises the constant-tuning rung (`r3`, Levenberg-
Marquardt fitting of every numeric leaf written back into the tree) much harder than a structure-only
case does. A run where `r1` and `r2` fail and `r3` succeeds is the expected shape here.

## Validity, and the variant that leaves it

The constants are valid from -20 to 100 degC. Outside that window they are simply wrong, not
approximately right, because a fitted Antoine set is an interpolation over the range it was regressed
on.

The recorded caveat states the interesting variant: a single constant set cannot cover the whole
liquid range of water, so a two-window variant asks the search to DETECT that, which is a change-point
question dressed as a fitting question. An engine that reports one smooth expression with a good
aggregate error across both windows has answered the wrong question.

## Provenance

| | |
|---|---|
| Source | Antoine equation, verified reference transcription, research dossier section 7.2.11 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; the generator is deterministic in `(generator.id, n_rows, seed, noise)` and regenerates byte for byte |

The dossier's verification for this generator was a reference transcription rather than a primary
paper. **UNVERIFIED:** no DOI for Antoine's 1888 original was resolved during the research phase, and
none is stated here.

## Defects applied

None. This is a generator: there are no rows to drop, no folds to ignore, no aggregation and no LFS
pointer to guard against. The manifest for a generator case carries an empty `defects_applied` list,
and that emptiness is itself informative when read next to the real cases.

The recorded caveat about a real-data twin is honest about its status: the batch distillation dataset
names its three chemical systems, so the true Antoine constants of every component are independently
obtainable rather than assumed. That twin is identified but is not shipped as a case.

## References

- Antoine, C. (1888). Tensions des vapeurs: nouvelle relation entre les tensions et les temperatures.
  Comptes Rendus des Seances de l'Academie des Sciences 107, pages 681 to 684, 778 to 780, 836 to
  837. UNVERIFIED: no DOI resolved during the research phase.
