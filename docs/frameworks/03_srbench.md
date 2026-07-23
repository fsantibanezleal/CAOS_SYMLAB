# Framework card, SRBench

**Status in this repo: PROTOCOL REFERENCE. The code is NOT used and must not be vendored.** Its
licence is GPL-3.0 and this repo is MIT.

## What it is, and the one thing it does better

SRBench is the containerised benchmarking harness for symbolic regression: a fixed problem set, a
fixed experimental protocol, and a scoring pipeline, published so that methods can be compared
without each author choosing their own conditions.

The one thing it does better than the alternatives is that it decides symbolic recovery in published,
readable code rather than in prose. The exact rule can be read, criticised and reimplemented, which is
what makes cross-paper numbers mean anything at all.

## Licence, and whether this MIT repo may use it

GPL-3.0 (`github.com/cavalab/srbench`, verified through the GitHub licence API). This repo may
reproduce its protocol and cite its numbers. It may **not** copy its code into an MIT-licensed
package. The research recorded the instruction plainly: reimplement the equivalence logic from the
specification rather than vendoring `symbolic_utils.py`. That reimplementation is
[`sreval`](01_sreval.md).

A name trap worth recording: `pypi.org/project/srbench` is an unrelated "self-rewarding benchmark"
package (0.1.0, 2026-03-28). Installing it will not give you this harness, which exists only at
`github.com/cavalab/srbench`.

## Install reality

Source checkout plus a conda environment. No wheel, no `pip install`. Full replication is a server
job rather than a workstation one: 252 problems by 14 methods by 10 seeds is thousands of CPU hours,
and the published run allocated 9 hours wall clock and 16 GB per job on the ground-truth track and 48
hours on the black-box track.

## Usage

The parts worth lifting are the protocol constants, all read from the repository source:

- Split: `train_test_split(X, y, train_size=0.75, test_size=0.25, random_state=seed)`.
- Scaling: `StandardScaler` on X and on y, y scaled with the training scaler only.
- Target noise, relative rather than absolute:
  `y_train += Normal(0, target_noise * sqrt(mean(y_train_scaled^2)))`, swept over
  `target_noise in {0, 0.001, 0.01, 0.1}`.
- Fit time limit: 3600 s, raised to 36 000 s above 1000 training rows, enforced with `SIGALRM` plus a
  600 s grace period.
- Seeds: a fixed list of 100 integers in `experiment/seeds.py`, with 10 trials used.
- Equivalence, from `assess_symbolic_model.py` and `symbolic_utils.py`: round floats
  (`|a| < 1e-4` to integer 0, otherwise 3 decimals), `simplify(model_sym, ratio=1)`, run the check
  only when `r2_test > 0.5`, then compute `symbolic_error_is_zero`, `symbolic_error_is_constant` and
  `symbolic_fraction_is_constant`, with `symbolic_solution = any of the three`.
- Accuracy: `accuracy_solution = (r2_test > 0.999)`.
- Complexity: `len(list(sympy.preorder_traversal(expr)))`, an unweighted node count.

Two consequences follow directly from that code and are stated in this repo's documentation because
they change what a published number means: a model off by an additive or multiplicative constant is
scored as a **symbolic solution**, and a model whose simplification times out or throws is scored as
a **failure** rather than as unknown.

## Applying it here

Not applied as code, and not run. This repo has not executed SRBench, does not ship its datasets and
does not report an SRBench rank. What it takes from SRBench is the protocol and the honesty
constraints:

- The accuracy threshold `R2 > 0.999` appears as `ACCURACY_R2_THRESHOLD` in
  [`stages/evaluate.py`](../../data-pipeline/symlab/stages/evaluate.py).
- The rule that accuracy and recovery are never merged is the argument of the whole product
  ([docs/README.md](../README.md)), and it exists because SRBench's two tracks measure different
  things and are topped by different methods.
- The equivalence protocol is reimplemented in `sreval` from the specification above, with the
  addition SRBench does not make: the symbolic test's own failure rate is reported.

## What its results say, and why they are quoted here rather than beaten

Three verified findings from the SRBench line shape this lab's claims more than any algorithm does:

- **SRBench++** evaluated twelve modern SR algorithms and states there is no dominant method, because
  performance varies significantly by task type. The synthetic track ranked QLattice, PySR and uDSR
  first to third; the real-world COVID-19 track ranked uDSR first at 5.75.
- **Feature selection: none of the algorithms retrieved the correct expression with complete absence
  of irrelevant features.** Not one, in the whole field.
- **Extrapolation was "particularly challenging, with most models showing subpar accuracy."** Noise
  sensitivity is the one axis where the field has genuinely delivered.

## Caveats

- Composition: 252 problems, being 122 black-box plus 130 ground-truth. PMLB carries 119 `feynman_*`
  and 14 `strogatz_*` regression datasets, which is 133, so three are excluded. `UNVERIFIED`: which
  three. The datasets page states 130 without listing the exclusions.
- Half of the black-box problems were variants of the Friedman synthetic families, which biases the
  aggregate. SRBench 2.0 caps any single family at 25% of the selected datasets.
- The v1 budget was defined in evaluations, which is not comparable across a transformer, a mutation
  search and a C++ GP loop. SRBench 2.0's own call for action is to move to wall clock and to report
  energy.
- Solution rate is binary: an equation wrong by one term scores the same as one that is wholly wrong.
- The 2022 competition reports 11 distinct submissions in the paper while the competition web page
  states 13 entrants with 9 advancing. Both numbers are recorded; the paper is the primary source.
- `UNVERIFIED`: whether a competition edition ran at GECCO 2023 with published results. A
  `Competition2023` branch exists whose README is a verbatim copy of the 2022 guidelines, and no
  results paper was located.
- `UNVERIFIED`: the full contents of SRBench++ beyond title and author list. The citation itself is
  verified; the DOI resolves to IEEE Xplore, which was not fetched.

## Citations

- La Cava, W., Orzechowski, P., Burlacu, B., de França, F. O., Virgolin, M., Jin, Y., Kommenda, M. and
  Moore, J. H. (2021). Contemporary Symbolic Regression Methods and their Relative Performance.
  NeurIPS 2021 Datasets and Benchmarks, arXiv:2107.14351.
- de França, F. O. et al. (2023). Interpretable Symbolic Regression for Data Science: Analysis of the
  2022 Competition. arXiv:2304.01117.
- de França, F. O., Virgolin, M., Kommenda, M. et al. (2024). SRBench++: Principled Benchmarking of
  Symbolic Regression With Domain-Expert Interpretation. IEEE Transactions on Evolutionary
  Computation, doi:10.1109/TEVC.2024.3423681.
- Imai Aldeia, G. S. et al. (2025). Call for Action: Towards the Next Generation of Symbolic
  Regression Benchmark. GECCO 2025 SR workshop, arXiv:2505.03977, doi:10.1145/3712255.3734309.
