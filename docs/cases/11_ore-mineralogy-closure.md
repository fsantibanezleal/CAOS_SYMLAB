# 11. Ore mineralogy: the measured line against the stoichiometric one

| | |
|---|---|
| Case id | `ore-mineralogy-closure` |
| Category | M, mining and metallurgy |
| Data | REAL, the same operating concentrator as case [10](10_flotation-silica.md) |
| Ground truth known | YES, a stoichiometric reference line |
| Machine-comparable truth | NO, %Fe = 69.94 - 0.699 %SiO2 assumes the ore is hematite and quartz only. Measured rows deviate by 6.5 percent at the median and 11.8 percent at worst, so the line is a reference to compare against and not a law to recover. An expression that fits the ore better than this line is a better description of the ore, and scoring it as a failed recovery would invert that. |
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

The research phase independently measured `Fe = 67.11 - 0.738*Si` with `corr = -0.9720`. The registry
caveat was reproduced exactly on 2026-07-22 from the loader output: intercept 67.083, slope -0.7363,
correlation -0.9718.

The two measurements are not two parses of the same rows. The research figure is an ordinary least
squares fit at ROW level over the raw 20-second records; the registry figure is the same fit on the
HOURLY aggregate this case actually ships, which is what the loader returns. They agree to about
four parts in ten thousand on the intercept, three parts in a thousand on the slope and to the third
decimal on the correlation. Both are stated rather than one being quietly dropped, and the reason
they differ at all is the aggregation, not parser noise.

**The lab reports BOTH lines and does not choose one.** The stoichiometric line is what the mineralogy
would give if the assumption held; the plant line is what the ore actually does. Presenting the
measured fit as though it were the physics, or the physics as though it described the plant, would
each be a specific falsehood.

**Not machine-comparable, and the reason is a DECISION rather than a gap.** This is the one case in
the registry listed in `IDEALISED_NOT_RECOVERABLE` in
[`physics_truths.py`](../../data-pipeline/symlab/cases/physics_truths.py), which is a table of
measured datasets whose published formula is an idealisation the data does not follow. The recorded
reason is carried into the artifact's `not_checkable_reason` verbatim:

> %Fe = 69.94 - 0.699 %SiO2 assumes the ore is hematite and quartz only. Measured rows deviate by
> 6.5 percent at the median and 11.8 percent at worst, so the line is a reference to compare against
> and not a law to recover. An expression that fits the ore better than this line is a better
> description of the ore, and scoring it as a failed recovery would invert that.

Those two deviation figures were re-measured against the loader output on 2026-07-22: 6.49 percent
at the median and 11.75 percent at worst. Note that this is NOT the generic "loaded from a file"
reason. The pipeline's measured-truth branch does construct exact identities for measured cases, as
case [06](06_wwtp-removal-identity.md) shows; this case is deliberately excluded from that table
because scoring against the stoichiometric line would report "not recovered" for expressions that
describe the ore better than the reference does.

## Recovery regime

Recorded as `unknown`. The reference line has two constants and nobody handed them to the search as
columns, so in substance a recovery here would be structure-plus-constants. The field stays
`unknown` because `preprocess.run` sets a regime only where it resolves a truth, and this case is
deliberately given none.

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
`manifests/ore-mineralogy-closure.json` records 278 distinct target values across the 4,000 kept
rows, a repeat ratio of 14.388, against 5.642 on case 10.
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
