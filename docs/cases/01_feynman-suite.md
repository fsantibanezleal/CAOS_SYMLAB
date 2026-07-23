# 01. Feynman equations: published physical laws

| | |
|---|---|
| Case id | `feynman-suite` |
| Category | P, physics ground truth |
| Data | synthetic (noise-free analytic evaluation on uniformly sampled inputs) |
| Ground truth known | yes |
| Machine-comparable truth | YES, 17 of 18 expanded problems carry a verified law; 1 cannot be written in this operator set |
| Recovery regime | `structure` |
| Loader | `pmlb:feynman`, a SUITE expanded by the pipeline into one case per equation |

## What the quantity is

There is no single quantity. This case is eighteen separate physical laws drawn from the Feynman
Lectures collection, each shipped as its own dataset with its own target: a force, a potential, an
energy density, an angular momentum, a shear modulus. What they have in common is that each one is a
CLOSED FORM somebody published, and the formula is recorded in machine-readable metadata alongside
the rows.

That is why the case exists. On a real dataset nobody knows the true law, so a result can only be
scored on error, and an error metric cannot distinguish a correct rediscovery from a flexible
surrogate that happens to interpolate well. Here the answer is written down, so the lab can report a
SOLUTION RATE, which is a categorically stronger claim than a coefficient of determination. The
field's most damaging benchmark finding, a method scoring above 0.999 while recovering the correct
structure zero percent of the time, is only measurable because sets like this one exist.

## The eighteen selected problems

The selection spans arities from one to several inputs, so the case covers trivially linear laws and
genuinely multi-variable ones rather than being padded with near-duplicates of the same shape. The
list lives in `FEYNMAN_SELECTION` in [`io/sources.py`](../../data-pipeline/symlab/io/sources.py); the
formulas below are transcribed from the comments carried on that tuple, which were taken from the
PMLB `metadata.yaml` of each dataset.

| PMLB dataset | Law | Inputs |
|---|---|---|
| `feynman_I_6_2a` | $f = \dfrac{e^{-\theta^2/2}}{\sqrt{2\pi}}$ | 1 |
| `feynman_I_12_1` | $F = \mu N_n$ | 2 |
| `feynman_I_12_5` | $F = q_2 E_f$ | 2 |
| `feynman_I_14_3` | $U = m g z$ | 3 |
| `feynman_I_25_13` | $V = q / C$ | 2 |
| `feynman_I_26_2` | $\theta_1 = \arcsin(n \sin\theta_2)$ | 2 |
| `feynman_I_29_4` | $k = \omega / c$ | 2 |
| `feynman_I_34_27` | $E = \dfrac{h}{2\pi}\,\omega$ | 2 |
| `feynman_I_39_1` | $E = \tfrac{3}{2} p_r V$ | 2 |
| `feynman_I_43_31` | $D = \mu_{mob} k_b T$ | 3 |
| `feynman_II_3_24` | $h = \dfrac{P_{wr}}{4\pi r^2}$ | 2 |
| `feynman_II_8_31` | $E = \dfrac{E_f^2 \epsilon}{2}$ | 2 |
| `feynman_II_10_9` | $E_f = \dfrac{\sigma_{den}}{\epsilon (1 + \chi)}$ | 3 |
| `feynman_II_27_18` | $E = \epsilon E_f^2$ | 2 |
| `feynman_II_38_14` | $G = \dfrac{Y}{2(1 + \sigma)}$ | 2 |
| `feynman_III_12_43` | $L = \dfrac{n h}{2\pi}$ | 2 |
| `feynman_III_15_14` | $m = \dfrac{h^2}{8\pi^2 E_n d^2}$ | 3 |
| `feynman_III_17_37` | $f = \beta (1 + \alpha\cos\theta)$ | 3 |

`feynman_I_12_1`, a plain product of two variables, is deliberately in the list as the FLOOR: an
engine that cannot recover it has a defect, not a difficulty.

Two of these forms are worth reading against the code rather than against the comment they came
from. The `FEYNMAN_SELECTION` comment in `io/sources.py` writes III.15.14 as
`m = h/(2*pi)**2/(E_n*d**2)`; the expression actually scored, in
[`physics_truths.py`](../../data-pipeline/symlab/cases/physics_truths.py), is
$h^2/(8\pi^2 E_n d^2)$, and the table above states the scored form. That constant was solved from the
data rather than guessed: `y * E_n * d^2 / h^2` is 0.0126651 with no spread across 3,000 rows, and
$1/(8\pi^2)$ is 0.01266515. `tests/test_physics_truths.py` evaluates every expression in that module
over real rows of its own dataset and requires agreement to 1e-9 relative; the suite passes on the
vault copy (29 tests, run 2026-07-22).

## Inputs, units and ranges

Every dataset ships its own input columns with SI units recorded in the PMLB metadata. The pipeline
does NOT read those units: `load_pmlb` assigns every column the dimensionless unit `1`, because the
metadata parser is not wired into the loader. The consequence is stated rather than hidden: this case
runs the `UNITLESS_LADDER`, so the unit-typed rung is omitted from its variant list entirely rather
than shown as a chip that silently does nothing. Making the rung meaningful here requires parsing the
18 `metadata.yaml` files, which is recorded as work not done.

Sampling ranges are uniform rather than physically realistic. That is a known property of the
collection and the specific defect the SRSD companion set was built to correct; it means a recovered
constant is being recovered from a region no experiment would ever visit.

## The published law

Yes, one per problem, listed above, and machine-readable in the source metadata.

**Seventeen of the eighteen are machine-comparable.** `preprocess.run` has a branch for loaders of
the form `pmlb-dataset:<name>`: it calls `physics_truths.truth_for`, which builds the published law
as an expression tree bound by column NAME rather than by position, so a change in the source column
order cannot rebind a variable to the wrong symbol. Every one of those trees is verified against
real rows of its own dataset before it is allowed to score.

The exception is `feynman_I_26_2`, Snell's law in the form $\theta_1 = \arcsin(n\sin\theta_2)$. The
operator set has no inverse-sine primitive, so the recorded reason, carried in `INEXPRESSIBLE` and
surfaced in the artifact's `not_checkable_reason`, is that the target lies outside the space the
search can reach. Recovery for that one problem is reported as not checkable rather than as zero,
because a zero would describe the primitive set rather than the method.

The baked artifacts agree: `data/derived/feynman-i_26_2/run.json` carries
`ground_truth_available: false` and `regime: "unknown"`, while the other seventeen carry
`ground_truth_available: true` and `regime: "structure"`.

## Recovery regime

Recorded as `structure` on the seventeen scored problems. The physical parameters ARE input columns
in this collection, which is the convention the published physics benchmarks use, so only the FORM
is unknown and the numbers are handed over. The suite row in
[`docs/cases.md`](../cases.md) reports the same value, and a recovery rate over this case is never
averaged with a `structure+constants` case.

## Provenance

| | |
|---|---|
| Source | PMLB (Penn Machine Learning Benchmarks), `EpistasisLab/pmlb`, one `.tsv.gz` per dataset |
| Licence | MIT |
| Redistribution | `mirror`, a compact sample may be committed with attribution |
| Citation | Romano, J. D. et al. PMLB v1.0: an open-source dataset collection for benchmarking machine learning methods. arXiv:2012.00058 |
| Verified on | 2026-07-21 |

The ORIGINAL canonical host for this collection, `space.mit.edu/home/tegmark/aifeynman.html`, returns
HTTP 404, verified twice including a curl with a browser user agent. It nevertheless remains the
cited source inside PMLB's own metadata. Nothing in this repo may point at it.

Counted during the research phase from `pmlb/all_summary_stats.tsv`: 450 datasets today, of which 119
are named `feynman_*` and 14 `strogatz_*`, against 417 reported in the PMLB paper. A lab that
hard-codes a count from a paper is describing a collection that no longer exists.

## What the loader actually does

`load_pmlb` in [`io/loaders.py`](../../data-pipeline/symlab/io/loaders.py) opens the gzip, takes the
first line as the header, and treats the LAST column as the target by PMLB convention. It attaches
the source citation, licence and redistribution verdict to the returned dataset so nothing downstream
has to re-derive where a number came from.

Two things happen above the loader:

- **The LFS pointer guard.** PMLB stores its dataset files in Git LFS. The ordinary
  `raw.githubusercontent` URL returns a 132-byte pointer file, and it returns it with HTTP 200, so a
  fetcher that checks only the status code writes garbage and reports success. The source registry
  uses the `media.githubusercontent.com/media/...` route, verified 2026-07-22 to give real gzip, and
  `scripts/fetch_data.py` detects the pointer signature and fails loudly so this cannot regress.
- **Deterministic subsampling.** Each source dataset ships exactly 100,000 rows. `preprocess.run`
  subsamples to 4,000 with seed 0 and records the fact as a defect on the manifest, with the stated
  reason: the source is a smooth low-dimensional law, the extra rows carry no additional information
  about its structure, and they would spend the whole search budget on redundancy. All eighteen
  manifests carry that line verbatim as their only entry under `contract.defects_applied`, and all
  eighteen record the same split, 2,550 train, 850 test and 600 extrapolation rows.

The suite is expanded by `expand_suites` in `pipeline.py` into one case per equation, with ids of the
form `feynman-i_6_2a`. Asking the preprocessor to load `pmlb:feynman` as a single dataset raises
rather than silently concatenating eighteen unrelated tables.

## Caveats carried on the case

Both are recorded in the registry and printed with any number derived from this case.

1. This set has been public since 2019 and is inside the pretraining corpus of every large language
   model, and arguably inside the synthetic distributions of every pretrained symbolic-regression
   transformer. Contamination is a live risk for any pretrained method evaluated here.
2. Sampling ranges are uniform rather than physically realistic, which is exactly what the SRSD
   companion set exists to correct.

## References

- Udrescu, S.-M. and Tegmark, M. (2020). AI Feynman: a physics-inspired method for symbolic
  regression. Science Advances 6(16), eaay2631, doi:10.1126/sciadv.aay2631.
- Romano, J. D. et al. (2021). PMLB v1.0: an open-source dataset collection for benchmarking machine
  learning methods. arXiv:2012.00058.
- La Cava, W. et al. (2021). Contemporary symbolic regression methods and their relative performance.
  NeurIPS 2021 Datasets and Benchmarks Track. arXiv:2107.14351.
