# 11. Ore mineralogy: the measured line against the stoichiometric one

| | |
|---|---|
| Case id | `ore-mineralogy-closure` |
| Category | M, mining and metallurgy |
| Data | REAL, the same operating concentrator as case [10](10_flotation-silica.md) |
| Ground truth known | YES, a stoichiometric reference line |
| Machine-comparable truth | no |
| Recovery regime | `unknown` |
| Loader | `ore-mineralogy-closure`, `load_flotation_mineralogy` |
| Inputs | ONE |

## What the quantity is

Iron grade of the plant feed, in mass percent, as a function of the silica grade of the same feed.
Both are routine assays on the material entering the concentrator.

Why anyone wants a closed form: because in this case one already EXISTS, derived rather than fitted,
and comparing it against the measured relationship says something about the ore that neither number
says alone.

If the ore were only hematite and quartz, every unit of rock would be one or the other, and
stoichiometry fixes the line exactly. Hematite is $\mathrm{Fe_2O_3}$: with atomic masses 55.845 for
iron and 15.999 for oxygen, hematite is 69.94 percent iron by mass. So a rock that is a fraction $x$
quartz ($\mathrm{SiO_2}$) and $1-x$ hematite carries $\%\mathrm{SiO_2} = 100x$ and
$\%\mathrm{Fe} = 69.94(1-x)$, and eliminating $x$ gives a straight line with intercept 69.94 and
slope $-0.6994$.

$$\%\mathrm{Fe} = 69.94 - 0.699\,\%\mathrm{SiO_2}$$

**The measured line differs, and the size of that difference is a statement about the other minerals
present.** Goethite, magnetite, clays and carbonates all carry iron or silica in different ratios, so
a plant line that sits below the two-mineral line is telling you the gangue is not pure quartz. That
is a geological inference obtained from process assays, which is the reason a metallurgist cares.

## Inputs

| Column | Symbol | Meaning | Unit | Note |
|---|---|---|---|---|
| `%_Silica_Feed` | $\%\mathrm{SiO_2}$ feed | silica grade of the plant feed | % | the single input |
| `%_Iron_Feed` | $\%\mathrm{Fe}$ feed | iron grade of the plant feed (target) | % | promoted from an input of case 10 to the target here |

One input and one target is the whole design. There is nowhere for a search to hide: any expression
it produces is a curve in one variable, and it either sits on the stoichiometric line or it does not.

Physical range: both are mass percentages, so both are bounded to 0 to 100, and the plant operates in
a narrow band of that range because the mine blends to a target feed grade.

## The published law

Yes, as a DERIVED reference rather than as a fitted empirical result:

$$\%\mathrm{Fe} = 69.94 - 0.699\,\%\mathrm{SiO_2} \quad \text{(two-mineral stoichiometry)}$$

`ground_truth_known` is true. The registry also carries the measured comparison, recorded verbatim as
a caveat from a measurement made on the raw file during this build:

> the plant line is Fe = 67.08 - 0.736 Si with correlation -0.9718, against the stoichiometric
> 69.94 - 0.699

The research phase independently measured, on its own parse of the same file,
`Fe = 67.11 - 0.738*Si` with `corr = -0.9720`. The two measurements were made by different code on
different parses and agree to about three parts in a thousand on the intercept and to the third
decimal on the correlation. Both are stated rather than one being quietly dropped, because the small
disagreement is itself the honest picture of what a re-parse costs.

**The lab reports BOTH lines and does not choose one.** The stoichiometric line is what the mineralogy
would give if the assumption held; the plant line is what the ore actually does. Presenting the
measured fit as though it were the physics, or the physics as though it described the plant, would
each be a specific falsehood.

**Not machine-comparable.** No `truth_node` is constructed, because this case is loaded from a file
rather than from an in-repo generator, so the exact-recovery test does not run and the app says "not
checkable" rather than reporting zero.

## Recovery regime

Recorded as `unknown`. The reference line has two constants and nobody handed them to the search as
columns, so in substance a recovery here would be structure-plus-constants; the field stays `unknown`
because the pipeline sets it only from a generator's declaration.

## Provenance

Identical to case [10](10_flotation-silica.md), because it is the same file.

| | |
|---|---|
| Source | OpenML dataset 43311 |
| Licence | CC0 1.0 Public Domain |
| Redistribution | `mirror` |
| Verified on | 2026-07-21, URL corrected 2026-07-22 |

## What the loader actually does

`load_flotation_mineralogy` calls `load_flotation(target="silica")` and then re-projects the result:
it takes the silica feed column as the sole input and the iron feed column as the target, and it
carries the base loader's `defects_applied` list forward unchanged.

That inheritance matters. Every defect listed on case 10 applies here in full:

1. the content guard on the attribute schema, because the recorded source id once served an unrelated
   dataset with HTTP 200;
2. hourly aggregation before any fitting, with row-level access withheld;
3. explicit comma-decimal parsing, with the malformed-row count written into the defect string (0 in
   the baked manifest);
4. exclusion of both concentrate assay columns, which here removes nothing since neither is used;
5. deterministic subsampling to 4,000 rows with seed 0, added by the preprocessor.

The ingestion contract raises its leakage warning on this case too, and more loudly than on case 10:
the target takes only a few hundred distinct values across the 4,000 rows, a repeat ratio above 14.
The cause is that feed assays are reported to one decimal over a narrow operating band, so the same
value recurs constantly. The warning stays. A tripwire that only fires when the cause is unknown is
not a tripwire.

## Why one input is enough

The case is deliberately the smallest search in the set. A method that cannot fit a straight line in
one variable has a defect. What the case actually measures is whether the reported result is honest
about WHICH line it found: an engine that reports the plant fit and calls it the mineralogy has
produced a correct number attached to a false claim, which is the failure mode this whole lab is
built to make visible.

## References

- Quality Prediction in a Mining Process. OpenML dataset 43311, CC0 1.0 Public Domain.
- The stoichiometric iron content of hematite, 69.94 percent by mass, follows from the standard atomic
  masses of iron and oxygen. It is a calculation, not a citation.
