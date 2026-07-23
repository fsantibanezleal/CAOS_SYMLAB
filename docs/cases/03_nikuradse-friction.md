# 03. Nikuradse rough-pipe friction: 362 measured points

| | |
|---|---|
| Case id | `nikuradse-friction` |
| Category | P, physics ground truth |
| Data | REAL, 1933 laboratory measurements |
| Ground truth known | NO |
| Machine-comparable truth | NO, loaded from a file; no in-repo expression to compare against |
| Recovery regime | `unknown` |
| Loader | `nikuradse-friction`, via `load_nikuradse` over the PMLB carrier |
| Rows | 362, the full measured set, no subsampling |

## What the quantity is

The Darcy friction factor $\lambda$ of flow through a pipe whose inner wall has been artificially
roughened with sand grains of a controlled size. It is the dimensionless coefficient that converts a
velocity head into a pressure loss per unit length,

$$\Delta p = \lambda \frac{L}{D} \frac{\rho v^2}{2}$$

so it is the single number that decides pump sizing for every pipeline ever built. An error in
$\lambda$ propagates directly into installed pump power, and therefore into capital cost and into
lifetime energy consumption.

Nikuradse's 1933 experiments are the measurements the whole subject rests on: six relative roughness
ratios, Reynolds numbers spanning more than two decades, taken by hand.

## Inputs

The PMLB carrier ships the two features and the target under the column names below.

| Column | Symbol | Meaning | Unit | Range in the file |
|---|---|---|---|---|
| `r_k` | $r/k$ | relative roughness, pipe radius over grain size | dimensionless | six discrete values: 507, 252, 126, 60, 30.6, 15 |
| `log_Re` | $\log_{10}\mathrm{Re}$ | base-10 logarithm of the Reynolds number | dimensionless | Reynolds numbers from 4.27e3 to 1.02e6 |
| target | $\lambda$ | Darcy friction factor | dimensionless | measured |

Point counts per roughness ratio, first recorded during the research phase from the Princeton
spreadsheet `NikRough_f_vs_Re.xls` and re-counted on 2026-07-22 directly from the PMLB file in the
vault, which is the copy this case actually loads: 48, 38, 71, 73, 62 and 70 points for `r_k` equal
to 507, 252, 126, 60, 30.6 and 15 respectively, summing to 362. The two counts agree exactly. The
`log_Re` column runs from 3.63 to 6.008, which is the Reynolds range quoted above.

Note that the second input arrives ALREADY logarithmic. The search is therefore not being asked to
discover that a logarithm belongs in the law; it is handed one.

## Is there a published law

**No closed form reproduces these points**, and that is the reason the case is here rather than in the
synthetic set. The registry records the ground truth as
`\text{no closed form; Colebrook is implicit and incomplete here}` and sets `ground_truth_known` to
false.

What does exist is a family of branch expressions, each valid over part of the domain and none valid
over all of it. All were verified during the research phase:

$$\lambda = \frac{64}{\mathrm{Re}} \quad \text{(laminar, exact)}$$

$$\lambda = 0.316\,\mathrm{Re}^{-1/4} \quad \text{(Blasius, } 4\times10^3 < \mathrm{Re} < 10^5\text{)}$$

$$\frac{1}{\sqrt{\lambda}} = 2.0\log_{10}\!\left(\mathrm{Re}\sqrt{\lambda}\right) - 0.8 \quad \text{(Prandtl, smooth turbulent)}$$

$$\frac{1}{\sqrt{\lambda}} = 2.0\log_{10}(r/k) + 1.74 \quad \text{(von Karman, fully rough)}$$

$$\frac{1}{\sqrt{\lambda}} = -2.0\log_{10}\!\left(\frac{k}{3.7 D} + \frac{2.51}{\mathrm{Re}\sqrt{\lambda}}\right) \quad \text{(Colebrook-White, implicit)}$$

Colebrook is the correlation engineering practice still uses, and it is implicit: it has to be solved
iteratively for $\lambda$, or replaced by an explicit approximation such as Swamee-Jain, which is
exactly what case [20](20_friction-factor.md) generates.

**The transitional-roughness hump in these measurements is genuinely NOT reproduced by Colebrook.**
Between the smooth-wall and fully-rough asymptotes the data dip and recover in a way the interpolating
formula smooths over. So this is not a solved exercise dressed as a case: the accepted answer is
visibly incomplete over part of the domain, and a discovered expression has something real to add.

Because no truth is declared, this case contributes to the error metrics and to the extrapolation
diagnostics ONLY. It contributes to no recovery rate, and reporting a zero recovery rate for it would
be false.

## Recovery regime

Not applicable. There is no parameterisation anybody handed the search, so the field is `unknown` and
the structure-versus-structure-plus-constants distinction does not arise.

## Provenance

| | |
|---|---|
| Source | PMLB `nikuradse_1` (two features), fetched through the LFS media route |
| Licence | MIT (EpistasisLab/pmlb) |
| Redistribution | `mirror` |
| Citation | Romano, J. D. et al. arXiv:2012.00058, carrying the 1933 Nikuradse measurements |
| Verified on | 2026-07-21 for the source entry, 2026-07-22 for the media route |

**The originally cited host returns HTTP 404.** The Princeton Gas Dynamics Lab page named by the
research dossier is dead; it is the SECOND dead canonical URL found in this field, after the AI
Feynman landing page. PMLB carries the same 362 points under MIT, which is strictly better than the
original: the original stated no licence at all and could therefore only ever have been link-only,
while the PMLB copy can be mirrored with attribution.

PMLB also ships `nikuradse_2`, a one-feature variant. The registered source entry exists; the case
uses `nikuradse_1`.

## What the loader actually does

`load_nikuradse` calls `load_pmlb("nikuradse_1")` and then relabels: it renames the dataset id and
name, sets the input displays to $r/k$ and $\log_{10}\mathrm{Re}$, sets the target display to
$\lambda$, and replaces the generic PMLB note with the provenance paragraph above. No rows are
dropped, no columns are excluded, no aggregation is applied. The LFS pointer guard described in case
[01](01_feynman-suite.md) applies.

Recorded in `manifests/nikuradse-friction.json`: 362 rows kept, 2 inputs, 186 distinct target values
across those 362 rows, a repeat ratio of 1.946, an empty `defects_applied` list, and a split of 231
train, 77 test, 54 extrapolation. All of those were reproduced from the vault file on 2026-07-22.
The manifest's split note names `r_k` as the pivot, so the extrapolation hold-out is the 27 lowest
and 27 highest rows of the roughness ratio, which means the held-out region is two whole roughness
ratios rather than a slice of each. The repeat ratio is a property of the digitised measurements
rather than a defect the loader introduced, and it is reported rather than corrected.

## Its twin

This case is the real half of the strongest pairing in the set. Case
[20](20_friction-factor.md) generates the explicit Swamee-Jain turbulent correlation with the answer
known exactly; this case carries the measurements where the accepted answer is visibly incomplete.
Calibrate the engine there, then bring it here. A method that recovers Swamee-Jain to the digit and
then produces something worse than Colebrook on these 362 points has told you something specific
about itself.

## References

- Colebrook, C. F. (1939). Turbulent flow in pipes, with particular reference to the transition
  region between the smooth and rough pipe laws. Journal of the Institution of Civil Engineers 11,
  pages 133 to 156, doi:10.1680/ijoti.1939.13150. The correspondence volume is
  doi:10.1680/ijoti.1939.14509.
- Romano, J. D. et al. (2021). PMLB v1.0. arXiv:2012.00058.
- Nikuradse, J. (1933). Stromungsgesetze in rauhen Rohren. VDI-Forschungsheft 361. UNVERIFIED: no DOI
  for the 1933 publication was resolved during the research phase. Pre-1950 engineering literature is
  inconsistently indexed, and this repo does not fabricate an identifier to fill the gap.
