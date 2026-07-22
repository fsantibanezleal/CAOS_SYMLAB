# 01. Feynman equations: published physical laws

| | |
|---|---|
| Case id | `feynman-suite` |
| Category | P, physics ground truth |
| Data | synthetic (noise-free analytic evaluation on uniformly sampled inputs) |
| Ground truth known | yes |
| Machine-comparable truth | no |
| Recovery regime | `unknown` (loaded from a file, not from an in-repo generator) |
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
| `feynman_III_15_14` | $m = \dfrac{h}{(2\pi)^2 E_n d^2}$ | 3 |
| `feynman_III_17_37` | $f = \beta (1 + \alpha\cos\theta)$ | 3 |

`feynman_I_12_1`, a plain product of two variables, is deliberately in the list as the FLOOR: an
engine that cannot recover it has a defect, not a difficulty.

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

**It is not machine-comparable in this pipeline.** `preprocess.run` builds a `truth_node`, the
expression tree the equivalence test scores against, only for cases whose loader is an in-repo
generator. A PMLB-backed case gets `truth = None` and `regime = "unknown"`. So this case contributes
to the error metrics and to the structural-distance statistics, and the exact-recovery scorer reports
"not checkable" rather than zero. Reporting zero here would be false: it would read as eighteen
failed recoveries when in fact the scorer was never handed a comparable object.

## Recovery regime

Recorded as `unknown`. The physical parameters ARE input columns in this collection, which is the
convention the published physics benchmarks use, so in the sense of the taxonomy this is a
structure-only task; the field is left `unknown` because the pipeline only sets it from a generator's
declaration and will not infer it.

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
  about its structure, and they would spend the whole search budget on redundancy. The manifests
  baked so far (`manifests/feynman-i_6_2a.json`, `manifests/feynman-i_12_1.json`) carry that line
  verbatim.

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
