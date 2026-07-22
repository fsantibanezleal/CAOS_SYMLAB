# 16. Theta-logistic population growth

| | |
|---|---|
| Case id | `theta-logistic-growth` |
| Category | B, biology and ecology |
| Data | synthetic, first-principles generator |
| Ground truth known | YES |
| Machine-comparable truth | YES, verified against its own generator to 1e-9 relative |
| Recovery regime | `structure` |
| Generator | `theta-logistic-growth` |
| Rows per run | 400, noise levels 0, 0.01, 0.1 |

## What the quantity is

The instantaneous growth rate of a population, in individuals per year, as a function of how large
the population already is. Growth is positive and near-exponential when the population is small
relative to the resources available, slows as crowding sets in, and reaches zero at the carrying
capacity.

Why anyone wants a closed form: the SHAPE of the slow-down is the whole argument in population
ecology. The plain logistic assumes density dependence kicks in linearly, which puts maximum
sustainable yield at exactly half the carrying capacity. The theta-logistic generalises that with a
shape exponent, and the exponent decides whether a population is resilient at low density or collapses
there. Harvest quotas, extinction-risk assessments and reintroduction plans all turn on it.

## Inputs

| Key | Symbol | Meaning | Unit | Sampled range |
|---|---|---|---|---|
| `N` | $N$ | population size | 1 | $K$ times a uniform factor on 0.01 to 1.5 |
| `r` | $r$ | intrinsic growth rate | 1/a | uniform, 0.1 to 3.0 per year |
| `K` | $K$ | carrying capacity | 1 | log-uniform, 10 to 100,000 |
| `theta` | $\theta$ | density-dependence shape | 1 | uniform, 0.3 to 3.0 |
| `dNdt` | $dN/dt$ | growth rate (target) | 1/a | follows from the law |

Population is sampled relative to the carrying capacity, from one percent of it to half again above
it. The rows above $K$ matter: they carry NEGATIVE growth, the regime where a population overshoots
and declines, and a search that only ever saw the increasing branch has not seen the law.

Carrying capacity spans four decades log-uniformly, which is the range separating an insect
population from a large mammal one.

## The published law

$$\frac{dN}{dt} = r N\left(1 - \left(\frac{N}{K}\right)^{\theta}\right)$$

At $\theta = 1$ this collapses to the plain logistic $rN(1 - N/K)$, so recovering $\theta$ near 1 is
itself an answer: it says the data do not support the generalisation.

`ground_truth_known` is true.

**No machine-comparable truth is shipped.** This generator carries `truth_latex` and `truth_infix`
but no `truth_node`, so the equivalence test has no expression tree to compare against. The reason is
the variable exponent: $(N/K)^{\theta}$ raises one input to the power of another, which the repo's
node vocabulary does not express as a fixed structural pattern the way `square` or `sqrt` do. The
case therefore contributes to the error metrics and the structural-distance statistics, and the
exact-recovery scorer reports "not checkable" rather than zero. Reporting zero would be false: the
search was never given a comparable object to be scored against.

## Recovery regime: structure

$r$, $K$ and $\theta$ all arrive as INPUT COLUMNS. Only the form is unknown. Stated because a
recovery rate over this case and a structure-plus-constants case would describe neither.

## The real-data twin, and why it is unusually strong

The recorded caveat states it: the Global Population Dynamics Database ships 5,156 population series
WITH PUBLISHED FITTED PARAMETERS. Its `main.csv` carries `SiblyFittedTheta`,
`SiblyCarryingCapacity` and `SiblyReturnRate` columns.

That is a rare arrangement. On almost every real case a recovered expression can only be compared
against a residual; here a recovered EXPONENT can be compared against an exponent somebody else
published for the same series, which is a much stronger check. Two independent estimates of the same
physical quantity disagreeing is informative in a way a large residual is not.

The GPDD twin is identified and licensed (CC BY 4.0, verified from the EML `intellectualRights`,
DOI 10.5063/F1BZ63Z8, 179,859 records) but is NOT shipped as a case in the current registry. That is
recorded here as pending rather than described as done.

## Provenance

| | |
|---|---|
| Source | Theta-logistic model, verified against GPDD provenance, research dossier 7.2.14 |
| Licence | MIT, generator authored in this repository |
| Redistribution | `mirror` |
| Raw data | none; deterministic in `(generator.id, n_rows, seed, noise)` |
| Real-data twin | GPDD via KNB, DOI 10.5063/F1BZ63Z8, CC BY 4.0, not yet a case |

**UNVERIFIED:** no DOI for the primary theta-logistic publication was resolved during the research
phase. The form was verified against the GPDD documentation and the published fitted-parameter
columns; no identifier is invented here.

## Defects applied

None. Generator case: no rows dropped, no folds ignored, no aggregation, no LFS pointer guard.

## References

- Global Population Dynamics Database, mirrored at KNB, doi:10.5063/F1BZ63Z8, CC BY 4.0. 179,859
  records across 5,156 series, with published theta fits in `main.csv`.
