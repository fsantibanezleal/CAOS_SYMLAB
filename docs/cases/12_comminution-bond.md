# 12. Comminution energy: Bond, with Kick and Rittinger as rival hypotheses

| | |
|---|---|
| Case id | `comminution-bond` |
| Category | M, mining and metallurgy |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure` |
| Generator | `comminution-bond`, with `comminution-kick` shipped as the rival |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

Specific comminution energy: the electrical energy, in kilowatt-hours per tonne, needed to reduce
ore from a feed size to a product size in a crushing and grinding circuit.

Why anyone wants a closed form: comminution is the largest single electricity consumer in mining, and
the grinding circuit usually sets the throughput of the whole concentrator. Sizing a mill, choosing a
grind target, or deciding whether a harder ore blend can be pushed through the existing plant all come
down to evaluating this relationship. The Bond work index that appears in it is the standard
grindability number the industry trades ore hardness in.

The research phase found no published symbolic-regression work on the Bond work index at all, and no
open Bond work index database in existence. Repeated searching returned only journal articles. That
absence is why the law is shipped here as a generator with a real-data companion rather than as a
case over measurements.

## The rival hypotheses

The three classical comminution laws are the same differential statement with a different exponent:

$$\frac{dE}{dx} = -\frac{C}{x^{n}}$$

with $n = 1$ giving Kick, $n = 1.5$ giving Bond and $n = 2$ giving Rittinger. Integrating gives the
three published forms.

**Bond** (the shipped truth):

$$E = 10\,W_i\left(\frac{1}{\sqrt{P_{80}}} - \frac{1}{\sqrt{F_{80}}}\right)$$

**Kick** (shipped as a separate generator so the selection question has a real alternative):

$$E = C\,\ln\!\left(\frac{F_{80}}{P_{80}}\right)$$

**Rittinger**, $E = C\,(1/P_{80} - 1/F_{80})$, is described in the research dossier and is not shipped
as a scored generator today.

Shipping competing ground truths turns this into a model SELECTION question rather than a fitting
question: which exponent do the data support, not how small can the residual be. That reframing is
the case.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `F80` | $F_{80}$ | 80 percent passing size of the feed | micrometres | log-uniform, 1,000 to 20,000 |
| `P80` | $P_{80}$ | 80 percent passing size of the product | micrometres | log-uniform, 45 to 500, then clipped |
| `Wi` | $W_i$ | Bond work index | kWh/t | uniform, 5 to 25 (soft to very hard ore) |
| `E` | $E$ | specific comminution energy (target) | kWh/t | follows from the law |

Both size ranges are the practical ones: a feed of one to twenty millimetres into a ball mill, a
product between 45 and 500 micrometres, which spans a fine regrind to a coarse rougher feed.

**A physical constraint is enforced during sampling.** $P_{80}$ is clipped to at most $0.9\,F_{80}$,
because a comminution stage cannot produce a product coarser than its feed. Without the clip the
generator would emit rows with negative energy, and a search would then be fitting a physically
impossible region.

Dimensions are declared on the two sizes (length), which is why this case can run the full ladder
including the unit-typed rung. The manifest records `units_declared` as 1.

## Recovery regime: structure

The work index arrives as an INPUT COLUMN. So does each size. Nothing has to be recovered numerically
except the leading factor 10, which is part of the definition of the Bond index rather than a fitted
parameter; the FORM is what is unknown. This is the convention the published physics benchmarks use,
and it is a materially easier task than the structure-plus-constants cases, which is why the two are
never averaged into a single recovery rate.

What the search actually has to assemble is the difference of two inverse square roots. That is not a
polynomial and not a simple ratio, and reaching it requires a `sqrt` and an `inv` in the primitive set.

## The machine-comparable truth

A `truth_node` is defined, so the equivalence test runs and this case contributes to the exact
recovery rate:

    mul( mul(10, Wi), sub( inv(sqrt(P80)), inv(sqrt(F80)) ) )

The Kick generator carries its own truth node, `mul(C, log(div(F80, P80)))`, so a candidate can be
tested for equivalence against either hypothesis rather than only against the one that generated the
rows.

## Validity and what is deliberately not shipped

Bond's relation is EMPIRICAL, calibrated by the standard Bond ball mill work index test. It is not a
derivation from fracture mechanics, and the exponent 1.5 has no first-principles justification; it is
the value that fit the plant data of the time.

**The Morrell size-specific-energy refinement is deliberately NOT shipped as a scored target.** It is
a known extension, but the research phase could not verify its exact coefficient form, and the repo's
standing rule is that an unverified formula is not a scored generator. That is recorded on the
generator as a caveat rather than left as an absence somebody might mistake for an oversight.

## Provenance

| | |
|---|---|
| Source | Bond comminution law, verified reference transcription, research dossier 7.2.4 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Real-data twin | the GeoMet comminution table, 78 rows by 28 columns with $F_{80}$ and $P_{80}$, Zenodo record 7051975, CC BY 4.0, redistribution `derived`; declared on the generator as `geomet-bond`, not shipped as a case |

**UNVERIFIED:** no DOI for Bond's original publications was resolved during the research phase. The
law was transcribed from a verified reference; no identifier is invented here.

The GeoMet twin is registered as a source but is NOT yet shipped as a case. The blocker is recorded:
the companion paper has to be read to pin the semantics of the `th1`, `th2`, `th3`, `M`, `A`, `fr` and
`xr` columns before the comminution case can be scored. GeoMet is the only permissively licensed
geometallurgy data the research found, released by Vale S.A. and IMPA, and its redistribution verdict
is `derived`: only derived metrics and artifacts may be published, never the table.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard. The
only sampling intervention is the physical $P_{80} < F_{80}$ clip described above, which is part of
the generator's definition rather than a correction to a defective source.

## References

- Bond, F. C. (1952). The third theory of comminution. Transactions AIME 193, pages 484 to 494.
  UNVERIFIED: no DOI resolved during the research phase.
- GeoMet: a geometallurgical dataset. Zenodo record 7051975, CC BY 4.0, Vale S.A. and IMPA.
