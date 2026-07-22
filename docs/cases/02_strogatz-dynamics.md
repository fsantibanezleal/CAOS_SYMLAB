# 02. Strogatz systems: two-state ODE right-hand sides

| | |
|---|---|
| Case id | `strogatz-dynamics` |
| Category | P, physics ground truth |
| Data | synthetic (analytic right-hand sides evaluated along trajectories) |
| Ground truth known | yes |
| Machine-comparable truth | NO, loaded from a file; no in-repo expression to compare against |
| Recovery regime | `unknown` |
| Loader | `pmlb:strogatz`, a SUITE expanded by the pipeline into one case per right-hand side |

## What the quantity is

The quantity the COLLECTION carries is a time DERIVATIVE. For a two-state system
$\dot{x} = f(x, y)$, $\dot{y} = g(x, y)$, each of $f$ and $g$ ships as its own PMLB dataset, so
seven classical systems produce fourteen problems. In the file, the two state variables are the
columns `x` and `y` and the derivative is the column named `target`.

> **The quantity this LAB fits is not that derivative.** In every `strogatz_*` file the target column
> is FIRST, not last: the header is `target`, `x`, `y`. `load_pmlb` takes the last column as the
> target "by PMLB convention", so this case is loaded with `y` as the target and `[target, x]` as the
> inputs. Verified two ways on 2026-07-22. First, against the published right-hand side recorded in
> the research dossier for `strogatz_bacres1`, `x' = 20 - x - (x*y)/(1 + 0.5*x**2)`: the `target`
> column reproduces it to 4.9e-14 while the `y` column misses it by 55.2 in absolute terms. Second,
> against the baked artifacts: all seven `data/derived/strogatz-*/run.json` present carry
> `dataset.target.key = "y"`. Everything below that describes recovering a derivative describes the
> collection, NOT what the shipped pipeline currently scores. This is a loader defect, recorded here
> because the page must not claim a task the code is not performing.

Why anyone wants a closed form: a fitted derivative field IS the model of the system. Once you have
$f$ and $g$ symbolically you can find fixed points, linearise around them, classify their stability
and predict bifurcations, none of which a numerical surrogate gives you. This is the task Schmidt and
Lipson framed as distilling natural laws from motion data.

Recovering a derivative from a trajectory is a genuinely different task from fitting a static
function, and it is where a method that looks strong on static problems often stops working: the
sampled states are not independent draws from a box, they lie on a trajectory, so whole regions of
state space carry no data at all.

## The fourteen problems

Seven two-state systems, two right-hand sides each. Names verified from PMLB during the research
phase; each ships 400 rows and 2 features.

| Pair | System |
|---|---|
| `strogatz_bacres1`, `strogatz_bacres2` | bacterial respiration |
| `strogatz_barmag1`, `strogatz_barmag2` | coupled bar magnets |
| `strogatz_glider1`, `strogatz_glider2` | glider flight dynamics |
| `strogatz_lv1`, `strogatz_lv2` | Lotka-Volterra competition |
| `strogatz_predprey1`, `strogatz_predprey2` | predator-prey |
| `strogatz_shearflow1`, `strogatz_shearflow2` | shear flow |
| `strogatz_vdp1`, `strogatz_vdp2` | Van der Pol oscillator |

The right-hand side of each is in the PMLB metadata. Two examples verified during the research phase
and quoted as fetched: `x' = 10*(y - (1)/(3)*(x**3-x))` for the Van der Pol pair, and
`x' = 20 - x - (x*y)/(1 + 0.5*x**2)` for `strogatz_bacres1`. The second was re-checked numerically
against the `target` column of the vault copy on 2026-07-22 and agrees to 4.9e-14.

The Lotka-Volterra and predator-prey pairs overlap in subject with case
[17](17_lotka-volterra-rhs.md), which is the useful kind of overlap: there the parameters are baked
into an in-repo generator and the truth is machine-comparable, here they are not, so the two cases
disagree about what can be scored and the disagreement is visible.

The pair labels above are the PMLB dataset names. `strogatz_lv1` and `strogatz_lv2` are the two
right-hand sides of one Lotka-Volterra system; the separate `strogatz_predprey1` and
`strogatz_predprey2` pair is a different system in the same collection.

## Inputs, units and ranges

Two state variables per problem, 400 rows each. The states are abstract populations, angles,
velocities or concentrations depending on the system, and the collection carries no unit metadata
that this loader reads. `load_pmlb` labels every column with the dimensionless unit `1`, so this case
runs the `UNITLESS_LADDER` and the unit-typed rung is omitted rather than shown as an inert chip.

Row counts are small enough that the deterministic 4,000-row subsample never triggers: 400 rows are
kept in full.

## The published law

Yes, fourteen of them, one per dataset, recorded in the source metadata.

**Not machine-comparable in this pipeline**, but NOT for the reason case 01 once gave. The
`pmlb-dataset:` branch of `preprocess.run` does resolve a truth for a PMLB-backed case; it calls
`physics_truths.truth_for`, whose `FEYNMAN_TRUTHS` table has an entry for seventeen Feynman problems
and none for any `strogatz_*` dataset. So `truth_for` returns `None` here and the recorded reason,
which the artifact carries in `not_checkable_reason`, is the third branch of
`physics_truths.not_checkable_reason`: this problem has a published law, but no machine-comparable
expression is wired for it in this lab, so recovery is not scored. That is a gap here rather than a
finding. Wiring the fourteen right-hand sides is work not done, and it is a prerequisite that the
target-column defect above be fixed first, since a truth bound to the published derivative cannot
score a run that is fitting `y`.

This case contributes to the error metrics and the structural-distance statistics; the exact-recovery
scorer reports "not checkable" rather than zero, because zero would read as fourteen failed
recoveries when the scorer was never given a comparable object.

## Recovery regime

Recorded as `unknown`, and the seven baked artifacts carry that value. The parameters of each system
are baked into the published right-hand side and are not input columns, so in the taxonomy's terms a
scored version of this case would be `structure+constants` rather than `structure`. The field stays
`unknown` because `preprocess.run` sets a regime only where it resolves a truth, and it resolves
none here. That distinction is material and is the reason the field exists at all: averaging a
structure-only recovery rate with a structure-and-constants one produces a number that describes
neither.

## Provenance

| | |
|---|---|
| Source | PMLB, `EpistasisLab/pmlb`, `strogatz_*` datasets |
| Licence | MIT |
| Redistribution | `mirror` |
| Citation | Romano, J. D. et al. arXiv:2012.00058 |
| Verified on | 2026-07-21 |

The upstream repository these problems come from is `lacava/ode-strogatz`, published with
La Cava, Danai and Spector, Engineering Applications of Artificial Intelligence,
doi:10.1016/j.engappai.2016.07.004. **UNVERIFIED: the licence of that upstream repository.** The
research dossier's GitHub-API licence sweep covers `cavalab/srbench` (GPL-3.0),
`EpistasisLab/pmlb` (MIT) and five others, and does not include `lacava/ode-strogatz`; an earlier
version of this page asserted GPL-3.0 for it, which appears to have been carried over from SRBench
and is not supported by anything in the dossier. What IS verified is that this repo takes the PMLB
copy, which is MIT, so no upstream term binds this repository either way.

## What the loader actually does

`load_pmlb` reads the gzip, header line first, last column as target. The LFS pointer guard described
in case [01](01_feynman-suite.md) applies identically: the `raw.githubusercontent` route returns a
132-byte pointer with HTTP 200, so the media route is used and `scripts/fetch_data.py` fails loudly on
the pointer signature.

**The last-column rule is wrong for this collection**, as recorded at the top of this page: the
`strogatz_*` files put `target` first, so the loader binds `y` as the target and the published
derivative as an input. The Feynman files do put `target` last, which is why the same loader is
correct there and silently wrong here. Nothing in the pipeline detects the difference, because
neither file carries a machine-readable statement of which column is the target.

No defects beyond that are applied to these files. Nothing is dropped, nothing is aggregated, no
column is excluded. The 400 rows of each file are used in full: they are below the 4,000-row
subsample cap, and the seven baked manifests record 255 train, 85 test and 60 extrapolation rows.

## What this case is for

Two things the static cases cannot show.

- **Whether a method degrades when the design is a trajectory rather than a box.** The extrapolation
  split holds out the lowest and highest rows of the widest-spanning input, so the held-out region
  lies outside the support the search ever saw. On a trajectory that hold-out is severe.
- **Whether recovering an invariant is the same task as recovering a derivative.** It is not. Case
  17 names the conserved-quantity formulation in its caveat, but no such variant is shipped: every
  chip on every case in this registry is a SEARCH configuration, and the nine on this case are the
  seven ladder rungs available without declared units, the parsimony arm and the sparse-regression
  arm. The comparison is recorded as work not done.

## References

- Schmidt, M. and Lipson, H. (2009). Distilling free-form natural laws from experimental data.
  Science 324(5923), pages 81 to 85, doi:10.1126/science.1165893.
- La Cava, W. et al. (2021). Contemporary symbolic regression methods and their relative performance.
  NeurIPS 2021 Datasets and Benchmarks Track. arXiv:2107.14351. SRBench's ground-truth track reports
  130 problems drawn from the Feynman and ODE-Strogatz collections. PMLB today carries 119
  `feynman_*` and 14 `strogatz_*`, which sum to 133, so the two counts do not reconcile.
  UNVERIFIED: which subset of the 119 SRBench used. The discrepancy is stated rather than resolved
  by adjusting one of the numbers.
- La Cava, W., Danai, K. and Spector, L. (2016). Inference of compact nonlinear dynamic models by
  epigenetic local search. Engineering Applications of Artificial Intelligence,
  doi:10.1016/j.engappai.2016.07.004. The publication behind the ODE-Strogatz collection.
- Romano, J. D. et al. (2021). PMLB v1.0. arXiv:2012.00058.
