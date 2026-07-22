# Cases

The case taxonomy and the coverage matrix. A case is one dataset plus the set of search
configurations run against it.

## Categories

| Code | Category | What it is for |
|---|---|---|
| P | Physics ground truth | The law is published, so recovery is verifiable to the digit |
| I | Industrial process | Real plant and equipment data, real noise |
| M | Mining and metallurgy | The domain the research found to be the field's clearest gap |
| B | Biology and ecology | Published models with fitted parameters to compare against |
| E | Environment and energy | Physical bounds a discovered form can visibly violate |
| S | Synthetic generators | First-principles, exactly scoreable, four with a real twin |

The single-letter code is an internal key. It never reaches the screen; the human name does.

## Two rules the registry enforces

1. **A case declares whether its ground truth is KNOWN.** Only cases with a known truth contribute to
   a recovery rate. Mixing the two would let the lab quote a recovery percentage that silently
   includes problems where recovery cannot be checked.
2. **A case declares its honest variant count.** Where a case genuinely admits no meaningful
   parametric family, it ships one deeply documented variant and says so, rather than being padded
   with fabricated regimes to hit a number.

## Documented traps carried, not hidden

Three datasets in this set have a defect that would silently corrupt a result, and each is carried
verbatim into the manifest rather than quietly fixed:

- **The flotation set broadcasts its target.** Concentrate assays are HOURLY laboratory measurements
  repeated across 20-second rows, about 13.5 times each. The loader aggregates to the hourly grid and
  offers no row-level access at all, so the leak is structurally unavailable rather than merely
  discouraged. It also excludes both concentrate assays from the inputs: predicting silica from iron
  is reading the answer off the other half of the same laboratory measurement.
- **A wastewater landing page understates its missing values.** It states there are none; the file
  contains 591. Rows carrying them are dropped, not imputed, because imputing into an exact identity
  would manufacture the relationship the case exists to recover.
- **An astronomy archive derives one of its columns from the law under test**, which makes a naive run
  circular. That case was excluded entirely rather than shipped with a caveat.

## The calibration twins

Four synthetic generators have a real-data twin in the case list. That is the strongest arrangement
available: calibrate the engine where the answer is known, then take it where it is not.

| Generator | Real twin |
|---|---|
| pipe friction factor | Nikuradse, 362 measured points, where the transitional hump is genuinely not reproduced by the accepted correlation |
| flotation kinetics | the plant soft-sensor case |
| comminution energy | the geometallurgy comminution table |
| Monod saturation | the penicillin fermentation case |

## Contamination, declared

The published physics set has been public since 2019 and is inside the pretraining corpus of every
large language model, and arguably inside the synthetic distributions of every pretrained symbolic
regression transformer. Any pretrained method evaluated on it carries that warning in its results.
