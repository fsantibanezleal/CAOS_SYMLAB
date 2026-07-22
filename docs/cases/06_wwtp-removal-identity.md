# 06. Wastewater treatment: an exact identity hiding in real data

| | |
|---|---|
| Case id | `wwtp-removal-identity` |
| Category | I, industrial process |
| Data | REAL, daily records from an urban wastewater plant |
| Ground truth known | YES, exact by the definition of the column |
| Machine-comparable truth | NO, loaded from a file; no in-repo expression to compare against |
| Recovery regime | `unknown` |
| Loader | `wwtp-removal-identity`, `load_water_treatment` |
| Rows | 380 retained of 527 shipped |

## What the quantity is

Global biological oxygen demand removal, the percentage of the incoming organic load that the plant
destroyed before discharging. BOD is the oxygen a microbial population consumes while metabolising
the organic matter in a water sample, so it is the standard proxy for how much treatable pollution
the water carries; the removal figure is the plant's headline performance number and is what a
discharge permit is written against.

Why this case exists is not that anybody needs a closed form for it. Everybody already has one. The
removal column in this file is DEFINED as

$$\mathrm{RD} = 100\,\frac{\mathrm{BOD}_{in} - \mathrm{BOD}_{out}}{\mathrm{BOD}_{in}}$$

computed from two other columns in the same file. A search handed only the inlet and outlet
concentrations should recover that expression exactly, on real daily plant data with real sensor
noise and real missingness.

**A method that cannot recover an exact identity present in its own inputs will not recover a
physical law from noisy data.** That makes this the cheapest honest sanity check in the whole set,
and the first case to run when an engine change is suspected of having broken something.

## Inputs

| Column | Symbol | Meaning | Unit as declared | Range |
|---|---|---|---|---|
| `DBO-E` | $\mathrm{BOD}_{in}$ | biological oxygen demand at plant entry | mg/L | real plant variation, with storm-day outliers |
| `DBO-S` | $\mathrm{BOD}_{out}$ | biological oxygen demand at plant outlet | mg/L | real plant variation |
| `RD-DBO-G` | $\mathrm{RD}_{\mathrm{BOD}}$ | global BOD removal (target) | % | 0 to 100 by construction |

The Spanish column abbreviations are the source's own: DBO is biological oxygen demand, DQO chemical
oxygen demand, SS suspended solids, SSV volatile suspended solids, SED sediments, COND conductivity.
The suffixes are positional: `-E` entry, `-P` primary settler, `-D` secondary settler input, `-S`
output, `-G` global, and `RD-` marks a removal column.

**The unit is inferred, not stated.** The research phase verified from `water-treatment.names` that
the source gives NO units for any column. The loader labels the two BOD columns mg/L because that is
the universal unit for the quantity; treat the label as UNVERIFIED against the source. It does not
affect the identity, which is scale-invariant in the numerator and denominator.

The full file has 38 attributes across the entry, primary settler, secondary settler, output and
performance blocks. This case uses three of them and ignores the rest, deliberately: handing the
search the other eight removal columns would let it recover the identity from a sibling rather than
from the concentrations.

## The published law

Yes, and it is exact:

$$\mathrm{RD} = 100\,\frac{\mathrm{BOD}_{in} - \mathrm{BOD}_{out}}{\mathrm{BOD}_{in}}$$

It is not a law of nature; it is the definition of the column, which is exactly what makes it
verifiable to the digit. `ground_truth_known` is true.

**It is not machine-comparable in this pipeline.** `preprocess.run` constructs a `truth_node` only
for cases backed by an in-repo generator, so this case reaches the scorer with `truth = None`. The
identity is rendered for a reader and can be checked by eye against the discovered expression, and it
contributes to the error metrics, but the automatic exact-recovery test does not run on it and the
app says "not checkable" rather than reporting zero. Wiring a hand-written truth node for the two
real cases that have an exact truth (this one and case [11](11_ore-mineralogy-closure.md)) is
recorded as work not done.

## Recovery regime

Recorded as `unknown`. In substance this is a structure-only task with one constant, the factor 100,
that has to come out right; the field stays `unknown` because the pipeline sets it only from a
generator's declaration.

## Provenance

| | |
|---|---|
| Source | UCI Machine Learning Repository, dataset 106, `water+treatment+plant.zip`, about 38.5 kB |
| Licence | CC BY 4.0 |
| Redistribution | `mirror` |
| Citation | Water Treatment Plant. UCI Machine Learning Repository, doi:10.24432/C5854H. 527 days |
| Verified on | 2026-07-21 |

## What the loader actually does

`load_water_treatment` reads the `.data` member from the zip, splits on commas, discards the first
field (a date label), and applies the fixed 38-column attribute order from the documentation, because
the file has no header row.

**The recorded defect, carried verbatim and counted at load time:**

> The UCI landing page states there are no missing values. The shipped file contains 591 occurrences
> of `?`. Rows containing any are DROPPED, not imputed: imputing into an exact identity would
> manufacture the relationship this case exists to recover.

The research phase confirmed both halves independently: the landing page says "Has Missing Values:
No", while the shipped `water-treatment.names` says "There are some missing values, all are unknown
information", and a direct count of the `?` sentinel gives 591 cells.

The count of retained rows is computed at load time and written into the defect string, so the
manifest records the real number rather than a number copied from a page. In
`manifests/wwtp-removal-identity.json` the baked value is 380 of 527 rows retained, with 243 train,
81 test and 56 extrapolation rows. Dropping 147 of 527 rows is a 28 percent loss, which is a large
correction to apply silently, and it is not applied silently.

The reason for dropping rather than imputing is worth stating plainly. Any imputation of a missing
inlet or outlet concentration would have to come from a model, and the most natural model available
is the identity itself; the case would then be scoring an engine's ability to rediscover a
relationship the pipeline had just written into the data.

Note also the repeat structure the manifest records: the target takes far fewer distinct values than
there are rows, because the source rounds the removal percentages. That is a property of the file,
recorded as a contract statistic, not a defect the loader introduced.

## References

- Water Treatment Plant. UCI Machine Learning Repository, doi:10.24432/C5854H.
