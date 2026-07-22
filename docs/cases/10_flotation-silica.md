# 10. Froth flotation: silica in the concentrate, a soft sensor with a laboratory delay

| | |
|---|---|
| Case id | `flotation-silica` |
| Category | M, mining and metallurgy |
| Data | REAL, an operating iron concentrator |
| Ground truth known | NO |
| Machine-comparable truth | no |
| Recovery regime | `unknown` |
| Loader | `flotation-silica`, `load_flotation(target="silica")` |
| Registry row count | 4,097 on the hourly grid |

## What the quantity is

Silica grade of the flotation concentrate, in mass percent. In reverse cationic flotation of iron
ore, the silica is what floats: an amine collector renders quartz hydrophobic, air is sparged into
the column, and the quartz leaves in the froth while the iron reports to the underflow product. The
silica remaining in that product is the penalty element, and it is what the concentrate is priced
against, because every point of silica has to be fluxed and slagged off later in the steel plant.

Why anyone wants a closed form: **the measurement arrives an hour late.** The silica grade is a
laboratory assay taken once per hour, while the process variables that drive it are measured every
twenty seconds. An operator adjusting amine dosage or column level today is flying on an assay from
an hour ago. An expression that predicts the assay from the process readings is a SOFT SENSOR, and a
readable expression is preferable to a black box because operators have to be willing to act on it.

## Inputs

Twenty-one process variables, all real plant instrumentation.

| Group | Columns |
|---|---|
| Feed assays | `%_Iron_Feed`, `%_Silica_Feed` |
| Reagents | `Starch_Flow` (depressant), `Amina_Flow` (amine collector) |
| Pulp condition | `Ore_Pulp_Flow`, `Ore_Pulp_pH`, `Ore_Pulp_Density` |
| Column air | `Flotation_Column_01_Air_Flow` through `_07_Air_Flow` |
| Column level | `Flotation_Column_01_Level` through `_07_Level` |
| Target | `%_Silica_Concentrate`, mass percent |

pH matters because amine adsorption on quartz is pH-dependent; starch depresses the iron minerals so
they do not float with the silica; air flow and froth level set the residence time and the drainage
of entrained particles.

**Units are UNVERIFIED against the source.** The ARFF file carries no unit metadata, which the
research phase recorded explicitly. The loader therefore labels every input with the dimensionless
unit `1` and only the target carries a `%`. Flows and levels have real physical units in the plant;
this repo does not invent them. Consequently `units_declared` is 0 in the manifest and this case runs
the `UNITLESS_LADDER`, with the unit-typed rung omitted rather than shown as an inert chip.

## Is there a published law

**No.** Flotation of a real ore in a real circuit is not described by a closed form in these
variables. `ground_truth_known` is false.

The case therefore contributes to the error metrics, to the accuracy-versus-complexity front and to
the extrapolation diagnostics. It contributes to NO recovery rate, and reporting a zero recovery rate
for it would be false.

Its calibration twin is case [13](13_flotation-kinetics.md), where first-order batch kinetics IS
written down and can be scored exactly. The pairing is the point: fit the engine where the answer is
known, then bring it here where it is not.

## Recovery regime

Not applicable, recorded as `unknown`.

## Provenance

| | |
|---|---|
| Source | OpenML dataset 43311, `Quality-Prediction-in-a-Mining-Process.arff`, about 185 MB |
| Licence | CC0 1.0 Public Domain, read from the OpenML API `licence` field |
| Redistribution | `mirror` |
| Citation | Quality Prediction in a Mining Process, OpenML dataset 43311, CC0 Public Domain. Real froth flotation plant, 20-second process readings with hourly laboratory assays |
| Verified on | 2026-07-21, URL corrected 2026-07-22 |

The data originate as a Kaggle upload (Eduardo Magalhaes, 2017). The Kaggle page is a JavaScript
application that returned no extractable text on repeated fetches, so the Kaggle-side licence is
UNVERIFIED and the download needs an account. The OpenML mirror solves both problems: the licence
field is machine-readable and the download is anonymous.

This is the most important mining dataset in the set, and the research phase found the area to be the
thinnest in the entire dossier. Direct Zenodo queries for froth flotation, hydrocyclone, ball mill
grinding and mineral processing datasets returned no usable process data. Open mineral-processing
plant data essentially does not exist outside this source and GeoMet.

## The defects the loader actually applies

Four, and they are the reason this case is worth having.

**1. The recorded source URL was WRONG.** The research dossier gave OpenML file id 22102255, which
serves a completely different dataset (Counter-Strike round snapshots, 97 attributes, about 50 MB)
with HTTP 200 and a plausible size. The correct id for dataset 43311 is 22102136, resolved through
the OpenML API. A fetcher that trusts the status code cannot catch this. `load_flotation` therefore
carries a CONTENT GUARD: it asserts that the attribute set contains `%_Iron_Feed`, `%_Silica_Feed`,
`%_Silica_Concentrate`, `Amina_Flow` and `Ore_Pulp_pH`, and raises with an instruction to re-fetch if
any is missing. It also raises if zero data rows parsed.

**2. The target is BROADCAST, and the loader refuses row-level access.** The concentrate assays are
hourly laboratory measurements repeated verbatim across every 20-second process row, about 13.5
repeats per distinct value, over roughly 4,000 distinct hourly timestamps. Fitting at row level leaks
the target 13.5 times over: the same assay appears in both the training and the test split. The
loader groups rows by the timestamp string truncated to the hour, averages the process variables
within each hour, and returns only the aggregated table. Row-level access is not offered at all, so
the leak is structurally unavailable rather than merely discouraged.

**3. The decimal separator is a comma INSIDE quoted fields.** A naive split on commas corrupts every
number and produces wrong results rather than an error. The loader parses field by field honouring
the quotes, then replaces the comma with a point. It counts malformed rows and writes the count into
the defect string; the baked manifest records 0 malformed rows skipped.

**4. Both concentrate assays are excluded from the inputs.** Predicting silica from iron in the same
concentrate is reading the answer off the other half of the same laboratory measurement, not soft
sensing. Every column whose name contains `Concentrate` is dropped from the input set.

A fifth line is added by the preprocessor: deterministic subsampling to 4,000 rows with seed 0.

## The warning the contract raises anyway

Even after hourly aggregation, the ingestion contract reports that the target takes fewer distinct
values than there are rows, with a repeat ratio above 5, and raises the leakage warning:

> if those repeats come from a coarser measurement grid, fitting at this resolution leaks the target

That warning is correct and is left in place. The residual repeats come from the laboratory rounding
its assay to one decimal, not from the broadcast the aggregation removed. Suppressing the warning
because the cause is understood would remove a tripwire that works.

## References

- Quality Prediction in a Mining Process. OpenML dataset 43311, CC0 1.0 Public Domain.
- Measured during the research phase on the parsed file, and quoted here as a measurement rather than
  a published value: 699,816 of 737,453 raw rows parse cleanly, and `corr(Fe_feed, Si_feed)` is
  -0.9720. That correlation is the subject of case [11](11_ore-mineralogy-closure.md).
