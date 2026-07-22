# 14. Two-product mass balance: metal recovery

| | |
|---|---|
| Case id | `two-product-recovery` |
| Category | M, mining and metallurgy |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure` |
| Generator | `two-product-recovery` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

Metallurgical recovery: the percentage of the metal contained in the plant feed that ends up in the
concentrate. It is the number every concentrator reports daily and the number a mine plan is
evaluated against, because a percentage point of recovery on a large operation is worth more than
most capital projects.

Why anyone wants a closed form: because the mass flows are not measured. A concentrator weighs its
feed, but weighing a slurry concentrate stream continuously and accurately is impractical, so the
split is inferred from ASSAYS alone. Three assays, one on each of feed, concentrate and tailings, are
enough to close the balance, and the expression that closes it is the two-product formula.

## The derivation

Mass balance on the total solids, $F = C + T$, and on the contained metal, $Ff = Cc + Tt$, where $f$,
$c$ and $t$ are the assays. Eliminating the unmeasured masses gives the mass split

$$\frac{F}{C} = \frac{c - t}{f - t}$$

and the metal recovery follows as

$$X_R = 100\,\frac{c}{f}\cdot\frac{f - t}{c - t}$$

with weight recovery $X_W = 100(f-t)/(c-t)$ and metal lost $X_L = 100 - X_R$ available from the same
three numbers.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `f` | $f$ | feed assay | mass % | uniform, 0.3 to 3.0 (a copper feed grade) |
| `c` | $c$ | concentrate assay | mass % | $f$ times an upgrade ratio uniform on 10 to 40 |
| `t` | $t$ | tailings assay | mass % | uniform, 0.02 to 0.3, then clipped to at most $0.9f$ |
| `R` | $X_R$ | metal recovery (target) | % | follows from the law |

The ranges are a real porphyry copper operation: a feed of a few tenths of a percent copper, a
concentrate an order of magnitude or two richer, and a tailing carrying the loss.

Two sampling constraints are physical rather than cosmetic. The concentrate assay is generated as the
feed times an upgrade ratio, so $c > f$ always; and the tailings assay is clipped to at most
$0.9f$, so $t < f$ always. Without them the generator would emit rows where the concentrate is
poorer than the feed or the tailing richer than it, which cannot happen in a working circuit and
would leave the search fitting an impossible region.

## The published law

$$X_R = 100\,\frac{c}{f}\cdot\frac{f - t}{c - t}$$

It is an accounting IDENTITY, exact by construction, not an empirical correlation.
`ground_truth_known` is true and a `truth_node` is defined:

    mul( mul(100, div(c, f)), div( sub(f, t), sub(c, t) ) )

so this case contributes to the exact recovery rate.

## Recovery regime: structure

All three assays are input columns. The only constant is the factor 100 that converts a fraction to a
percentage. What is unknown is the FORM, and the form is the difficulty.

## Why it is a hard exact-recovery test on purpose

The recorded caveat says it plainly: the answer is a RATIO OF DIFFERENCES, which most search spaces
reach only with a competent simplification stage. A candidate that has assembled the right subtrees
in the wrong arrangement scores badly on error and is structurally close to correct, and without
simplification the search has no way to notice that it is one rewrite away.

So a failure here is informative about the ENGINE rather than about the data. That is the opposite of
what a real-data case tells you, and it is why a synthetic identity belongs in the set: it isolates a
property of the search from every property of the measurement.

## Provenance

| | |
|---|---|
| Source | Two-product formula, froth flotation metallurgical accounting, verified reference transcription, research dossier 7.2.6 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |

**UNVERIFIED:** the dossier verified this from a reference transcription rather than a primary paper,
and no DOI attaches to a mass-balance identity of this age. None is invented here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard. The
two physical clips described above are part of the generator's definition.

## Its relative in the set

Case [06](06_wwtp-removal-identity.md) is the same idea on REAL data: an exact identity defined
between columns of the same file, recoverable to the digit, on measurements with real noise and real
missingness. Running the two together separates "can the engine find an identity" from "can it find
an identity through sensor noise".

## References

- No primary reference with a resolvable DOI was recorded for the two-product formula during the
  research phase. It is standard metallurgical accounting, transcribed from a verified reference;
  treat the citation as UNVERIFIED rather than assuming one.
