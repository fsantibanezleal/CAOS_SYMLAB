# 02. Strogatz systems: two-state ODE right-hand sides

| | |
|---|---|
| Case id | `strogatz-dynamics` |
| Category | P, physics ground truth |
| Data | synthetic (analytic right-hand sides evaluated along trajectories) |
| Ground truth known | yes |
| Machine-comparable truth | no |
| Recovery regime | `unknown` (loaded from a file, not from an in-repo generator) |
| Loader | `pmlb:strogatz`, a SUITE expanded by the pipeline into one case per right-hand side |

## What the quantity is

The target is a time DERIVATIVE. For a two-state system $\dot{x} = f(x, y)$, $\dot{y} = g(x, y)$,
each of $f$ and $g$ ships as its own dataset, so seven classical systems produce fourteen problems.
The inputs are the two state variables; the target is the rate of change of one of them.

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

The right-hand side of each is in the PMLB metadata. One verified example from the research phase,
quoted as fetched: `x' = 10*(y - (1)/(3)*(x**3-x))`.

The Lotka-Volterra and predator-prey pairs overlap in subject with case
[17](17_lotka-volterra-rhs.md), which is the useful kind of overlap: there the parameters are baked
into an in-repo generator and the truth is machine-comparable, here they are not, so the two cases
disagree about what can be scored and the disagreement is visible.

## Inputs, units and ranges

Two state variables per problem, 400 rows each. The states are abstract populations, angles,
velocities or concentrations depending on the system, and the collection carries no unit metadata
that this loader reads. `load_pmlb` labels every column with the dimensionless unit `1`, so this case
runs the `UNITLESS_LADDER` and the unit-typed rung is omitted rather than shown as an inert chip.

Row counts are small enough that the deterministic 4,000-row subsample never triggers: 400 rows are
kept in full.

## The published law

Yes, fourteen of them, one per dataset, recorded in the source metadata.

**Not machine-comparable in this pipeline**, for the same reason as case 01: `preprocess.run` only
constructs a `truth_node` for cases backed by an in-repo generator, so a PMLB-backed case gets
`truth = None`. This case contributes to the error metrics and the structural-distance statistics;
the exact-recovery scorer reports "not checkable" rather than zero, because zero would read as
fourteen failed recoveries when the scorer was never given a comparable object.

## Recovery regime

Recorded as `unknown`. The parameters of each system are baked into the published right-hand side and
are not input columns, so in the taxonomy's terms this is closer to `structure+constants` than to
`structure`; the field is left `unknown` because the pipeline sets it only from a generator's own
declaration and will not infer it. That distinction is material and is the reason the field exists at
all: averaging a structure-only recovery rate with a structure-and-constants one produces a number
that describes neither.

## Provenance

| | |
|---|---|
| Source | PMLB, `EpistasisLab/pmlb`, `strogatz_*` datasets |
| Licence | MIT |
| Redistribution | `mirror` |
| Citation | Romano, J. D. et al. arXiv:2012.00058 |
| Verified on | 2026-07-21 |

The upstream repository these problems come from, `lacava/ode-strogatz`, is GPL-3.0. The PMLB
redistribution is MIT, so this repo takes the PMLB copy. That is a licence decision, not a
convenience: vendoring the GPL copy would bind this repository's terms.

## What the loader actually does

`load_pmlb` reads the gzip, header line first, last column as target. The LFS pointer guard described
in case [01](01_feynman-suite.md) applies identically: the `raw.githubusercontent` route returns a
132-byte pointer with HTTP 200, so the media route is used and `scripts/fetch_data.py` fails loudly on
the pointer signature.

No defects beyond that are applied to these files. Nothing is dropped, nothing is aggregated, no
column is excluded.

## What this case is for

Two things the static cases cannot show.

- **Whether a method degrades when the design is a trajectory rather than a box.** The extrapolation
  split holds out the lowest and highest rows of the widest-spanning input, so the held-out region
  lies outside the support the search ever saw. On a trajectory that hold-out is severe.
- **Whether recovering an invariant is the same task as recovering a derivative.** It is not, and
  case 17 ships the conserved-quantity formulation as its own variant so the two can be compared on
  the same system.

## References

- Schmidt, M. and Lipson, H. (2009). Distilling free-form natural laws from experimental data.
  Science 324(5923), pages 81 to 85, doi:10.1126/science.1165893.
- La Cava, W. et al. (2021). Contemporary symbolic regression methods and their relative performance.
  NeurIPS 2021 Datasets and Benchmarks Track. arXiv:2107.14351. The 130 ground-truth problems of
  SRBench are the 119 Feynman plus these 14 Strogatz datasets.
- Romano, J. D. et al. (2021). PMLB v1.0. arXiv:2012.00058.
