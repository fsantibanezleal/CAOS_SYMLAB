# Framework card, AI Feynman

**Status in this repo: SURVEYED, NOT USED.** It is Linux or macOS only and needs a Fortran compiler,
which rules it out on the workstation this lab is built on.

## What it is, and the one thing it does better

AI Feynman is a recursive divide-and-conquer algorithm that uses physics structure instead of brute
search. Its components, in the order it applies them:

- **Dimensional analysis**: use the units of the variables to reduce the problem to dimensionless
  groups, cutting the number of free variables before any search happens.
- **Polynomial fit**: try low-degree polynomials directly.
- **Brute-force search**: enumerate short expressions over a primitive set, feasible only because the
  previous steps shrank the problem.
- **Symmetry tests**: check numerically whether `f(x, y)` depends only on `x + y`, `x - y`, `x * y`
  or `x / y`; if so, substitute one new variable and recurse.
- **Separability tests**: check whether `f(x, y) = g(x) h(y)` or `g(x) + h(y)`; if so, solve the two
  lower-dimensional subproblems independently and recurse.

A neural network is fitted to the data purely as a **smooth interpolator**, so that the symmetry and
separability tests can be evaluated anywhere, including at points not in the dataset.

The one thing it does better than the alternatives is decomposition. It does not search harder, it
makes the problem smaller, and on textbook physics that is decisive: it discovered all 100 equations
from the Feynman Lectures, improving the previous state of the art from 71 to 100, and improved a
harder test set from 15% to 90%.

**AI Feynman 2.0** adds four things: Pareto-optimal output with complexity measured in **bits of
description length**; generalised symmetry discovery, where arbitrary modularity in the formula's
computational graph is read from the gradient and Hessian properties of a fitted neural surrogate
rather than from a fixed catalogue of symmetries; normalising flows, extending the method to
probability distributions known only through samples; and statistical hypothesis testing to
accelerate robust brute-force search. It is reported as typically orders of magnitude more robust to
noise and bad data than the previous state of the art.

## Licence, and whether this MIT repo may use it

MIT (`github.com/SJ001/AI-Feynman`, verified on the repository page). Compatible with this repo. The
blocker is the platform, not the licence.

## Install reality

**Linux or macOS only** (verified). It requires compiling Fortran through `compile.sh`, plus PyTorch.
96 commits, lightly maintained. Runtime is long: the brute-force stage is time-budgeted by the user
and the neural stage runs 500 to 4000 epochs.

On a Windows workstation that means WSL2 or Docker. Combined with the maintenance level, that is the
reason this is a survey entry.

## Usage

No snippet. The research transcribed the algorithm and the results, not the repository's calling
convention.

## Applying it here

Not used, and not reimplemented. There is no neural surrogate in this build, so the symmetry and
separability tests, which depend on being able to evaluate the fitted function at arbitrary points,
have nothing to run against.

Two of its ideas are present in a different form, and the differences matter:

- **Dimensional analysis.** AI Feynman uses units to *reduce* the problem to dimensionless groups
  before searching. This build uses units to *constrain generation*, so the generator never builds
  the sine of a length ([`model/units.py`](../../data-pipeline/symlab/model/units.py),
  `typed_population` in [`search/generate.py`](../../data-pipeline/symlab/search/generate.py), and
  [method-families/05_units.md](../method-families/05_units.md)). That is PhySO's framing rather than
  AI Feynman's, and the two are not interchangeable.
- **Complexity in bits.** AI Feynman 2.0 selects on description length, and so does this build
  (`description_length` in [`model/complexity.py`](../../data-pipeline/symlab/model/complexity.py)).
  The codelength here is this build's own definition and is stated as such wherever a number is
  reported; it is not AI Feynman's, and it is not the Exhaustive Symbolic Regression one, which is
  marked `UNVERIFIED` in the research and deliberately not reproduced (see
  [18_esr.md](18_esr.md)).

## Caveats

- The method's leverage comes from assumptions that hold in textbook physics (low noise, exact
  functional forms, meaningful units) and largely do not hold on real measured data.
- Solving 100 of 100 Feynman equations is also what created the benchmark-saturation problem the
  field now has: a suite that a 2020 method solves completely cannot rank 2026 methods.
- The canonical Feynman database URL is dead. `space.mit.edu/home/tegmark/aifeynman.html` returns
  HTTP 404 as of 2026-07-22, and every PMLB Feynman dataset still cites it as its source. Take the
  equations from PMLB or SRSD ([04_pmlb.md](04_pmlb.md)).
- `UNVERIFIED`: Science Advances article details beyond "Science Advances 6:eaay2631, 2020-04-15" as
  reported in the arXiv journal-reference field. science.org returned HTTP 403 to the research
  session.

## Citations

- Udrescu, S.-M. and Tegmark, M. (2020). AI Feynman: a physics-inspired method for symbolic
  regression. Science Advances 6, eaay2631, doi:10.1126/sciadv.aay2631, arXiv:1905.11481.
- Udrescu, S.-M., Tan, A., Feng, J., Neto, O., Wu, T. and Tegmark, M. (2020). AI Feynman 2.0:
  Pareto-optimal symbolic regression exploiting graph modularity. NeurIPS 2020, arXiv:2006.10782.
