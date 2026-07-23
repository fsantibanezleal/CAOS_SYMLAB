# 05. Concrete compressive strength: the Abrams law

| | |
|---|---|
| Case id | `concrete-abrams` |
| Category | I, industrial process |
| Data | REAL, 1,030 laboratory-tested mixes |
| Ground truth known | NO |
| Machine-comparable truth | NO, loaded from a file; no in-repo expression to compare against |
| Recovery regime | `unknown` |
| Loader | `concrete-abrams`, `load_concrete` |

## What the quantity is

Compressive strength of a hardened concrete cylinder, in megapascals, given the proportions of the
mix it was cast from and the age at which it was crushed. Compressive strength is the design variable
of every concrete structure: it sets the section a column needs, and it is the number a batch plant
is paid against.

Why anyone wants a closed form: mix design is an optimisation under a strength constraint, and the
constraint has to be evaluated thousands of times over candidate mixes. More importantly, the
century-old empirical answer is a compact expression, so a discovered expression can be compared
against it directly rather than only against a residual.

## Inputs

Eight columns, seven of them mass per unit volume of mixture and one an age.

| Key | Symbol | Meaning | Unit |
|---|---|---|---|
| `cement` | $c$ | cement content | kg/m^3 |
| `slag` | $s$ | blast furnace slag | kg/m^3 |
| `fly_ash` | $f$ | fly ash | kg/m^3 |
| `water` | $w$ | water | kg/m^3 |
| `superplasticizer` | $sp$ | superplasticiser | kg/m^3 |
| `coarse_aggregate` | $g_{coarse}$ | coarse aggregate | kg/m^3 |
| `fine_aggregate` | $g_{fine}$ | fine aggregate | kg/m^3 |
| `age` | $t_{age}$ | age at test | days |
| `strength` | $f_c$ | compressive strength (target) | MPa |

The physical ranges are the ranges of practical concrete: ordinary structural mixes, supplementary
cementitious replacement of part of the cement by slag and fly ash, and ages spanning early strength
to long-term maturity. No missing values; these are real laboratory compression tests.

## Is there a published law

Yes, as a NAMED EMPIRICAL LAW, and no, as a generator of these rows. The registry sets
`ground_truth_known` to false and carries the law as a reference expression rather than as a scored
target.

Abrams' law states that strength depends on the water-to-cement RATIO,

$$f_c \approx \frac{A}{B^{w/c}}$$

with $A$ and $B$ material constants, combined with a logarithmic maturity term in age. The registry's
`ground_truth_latex` states only that there is a $\ln(t)$ maturity term. One common way to write it
is

$$f_c(t) \approx f_{c,28}\,\frac{\ln t}{\ln 28}$$

**UNVERIFIED:** no primary source for that particular normalisation was resolved during the research
phase. What is verified is the presence of a logarithm of age, not this exact expression.

**Neither the ratio nor the logarithm is an input column.** The search is handed water and cement as
separate masses and age as a plain number of days; to reach the published form it has to CONSTRUCT
$w/c$ and it has to construct $\ln t$. That is what makes this one of the best real cases in the set:
the inputs are raw quantities and the correct answer is a ratio the model must build itself.

What it is not is an exact truth. Real concrete strength depends on aggregate grading, curing
conditions, admixture chemistry and the pozzolanic reaction of the slag and fly ash, none of which
Abrams describes. So this case contributes to the error metrics and to a qualitative structural
check, does the discovered expression contain a $w/c$ ratio and a logarithm of age, and it
contributes to no recovery rate. Reporting it as zero recovery would be false.

## Recovery regime

Not applicable, recorded as `unknown`.

## Provenance

| | |
|---|---|
| Source | UCI Machine Learning Repository, dataset 165, `concrete+compressive+strength.zip`, about 34 kB |
| Licence | CC BY 4.0 |
| Redistribution | `mirror` |
| Citation | Yeh, I.-C. Concrete Compressive Strength. UCI Machine Learning Repository, doi:10.24432/C5PK67 |
| Verified on | 2026-07-21 |

## What the loader actually does

`load_concrete` opens the zip, takes the first `.xls` or `.xlsx` member, and dispatches to the
matching reader (`openpyxl` for xlsx, `xlrd` for the legacy format). All columns but the last are
inputs; the last is the target.

**The recorded defect:** the workbook column names carry their units inside the label, in the style of
a spreadsheet caption. They are replaced by the short machine keys listed above and the units are
recorded separately on the dataset, so a discovered expression renders as mathematics rather than as
a spreadsheet heading. That line is carried into `manifests/concrete-abrams.json` under
`contract.defects_applied`.

No rows are dropped and no subsampling applies: 1,030 rows is below the 4,000-row cap, so the whole
set is used. The manifest records the distinct-target count and repeat ratio; a modest repeat count
is expected here because several mixes were cast in replicate.

Units are declared as strings but the dimension vectors are all dimensionless, so `units_declared` is
0 and this case runs the `UNITLESS_LADDER`. Making the unit-typed rung meaningful here would require
declaring mass-per-volume dimensions on seven inputs and a time on the eighth, which is possible and
is recorded as work not done.

## A note on the target the registry carries

Both the registry and the loader set a `ground_truth_latex` for this case, and the two strings differ
in whitespace only. An earlier version of this page reported the loader's string as shipping mangled
control bytes (`pprox`, `rac`, `ext`, from backslashes eaten by a non-raw Python string). That defect
has been fixed: the literal in `load_concrete` is a raw string today and renders correctly, and
`tests/test_no_control_characters.py` guards the class of bug. The note is kept because the failure
is worth remembering, not because it is still present.

## References

- Yeh, I.-C. Concrete Compressive Strength. UCI Machine Learning Repository, doi:10.24432/C5PK67.
- Yeh, I.-C. (1998). Modeling of strength of high-performance concrete using artificial neural
  networks. Cement and Concrete Research 28(12), pages 1797 to 1808. UNVERIFIED: this reference is
  the commonly cited origin of the dataset, but no DOI was resolved for it during the research phase,
  so none is stated here.
- Abrams, D. A. (1918). Design of concrete mixtures. Structural Materials Research Laboratory,
  Lewis Institute, Bulletin 1. UNVERIFIED: no DOI resolved during the research phase.
