# Framework card, FFX (Fast Function Extraction)

**Status in this repo: SURVEYED, NOT USED, and it is LICENCE BLOCKED as a dependency.** The
algorithm is publishable and reimplementable; the package is not shippable inside an MIT product.

## What it is, and the one thing it does better

FFX is deterministic symbolic regression in three stages, with no search at all:

1. **Enumerate a massive basis set.** Univariate bases `x_j^e` for exponents from a small set such as
   {-1, -0.5, 0.5, 1}, optionally wrapped in a nonlinear operator (`abs`, `log`, ...), then bivariate
   bases formed as products of pairs of univariate bases. This yields thousands of candidate basis
   functions with no stochastic component.
2. **Pathwise regularized learning.** Fit an elastic net over the full basis along a regularisation
   path, minimising

       (1 / 2n) || y - B w ||_2^2  +  lambda ( alpha ||w||_1 + (1 - alpha) ||w||_2^2 / 2 )

   for a decreasing sequence of `lambda`. The L1 term drives most coefficients to exactly zero, so
   each `lambda` yields a model with a different number of active bases, and the whole path costs
   about one least-squares fit thanks to coordinate descent with warm starts.
3. **Non-dominated filter** on (test error, number of bases), returning a Pareto front of models.

The one thing it does better than the alternatives is determinism at scale. Its own PyPI description
states the operating regime plainly: runtime of 5 to 60 seconds with 1000+ input variables. Every
stochastic engine in this card set has seed variance to report; FFX has none, and it handles wide
data that a tree search cannot.

## Licence, and whether this MIT repo may use it

**No.** PyPI metadata for `ffx` 2.1.0 states an "FFX Software Licence Agreement" restricted to usage
that does not involve commercial gain, with a patent-pending note. That is not an OSI open-source
licence, and it is incompatible with shipping inside an MIT-licensed public product.

`UNVERIFIED`: the actual contents of the `LICENSE` file in the repository. The PyPI metadata is the
source of the restriction above, and the file itself must be read directly before any use. If the
non-commercial restriction holds, the options are to reimplement the algorithm or to drop it.

The algorithm itself is published and reimplementable, and the research estimated a clean
reimplementation at about 200 lines: enumerate the bases, run scikit-learn's `ElasticNet` path,
Pareto-filter. That is the recommended route, and it carries no licence encumbrance because the
method is in the literature, not in the package.

## Install reality

`pip install ffx` installs version 2.1.0 (released 2025-06-28), pure Python over numpy, pandas,
scikit-learn and click. Technically trivial, legally not. Do not add it to a requirements file in
this repo.

## Usage

Not reproduced. Publishing a usage snippet for a package this repo has decided it may not depend on
would be an invitation to install it.

## Applying it here

Not used and, as of this writing, **not reimplemented either**. This is an absence in the ladder and
it is recorded as one rather than glossed over.

The ladder in [`search/engine.py`](../../data-pipeline/symlab/search/engine.py) is stochastic from
rung 1 to rung 8. The only deterministic rung this build has is bounded exhaustive search
([18_esr.md](18_esr.md), [`search/exhaustive.py`](../../data-pipeline/symlab/search/exhaustive.py)),
which is deterministic and complete but restricted to small bases and low complexity. A reimplemented
FFX would fill a different gap: deterministic, sub-minute, and comfortable with wide data, which is
the exact contrast case to everything else here. It would also be a natural browser rung, since the
basis enumeration and an elastic-net path are both cheap.

If it is added, two things must be true of it: it must be written from the published method rather
than from the package, and the docs must say that a linear combination of predefined basis shapes is
interpretable in the sparse sense and not in the "this is a law" sense.

## Caveats

- The model is always a linear combination of predefined basis shapes, so it cannot discover nesting
  and cannot discover a genuinely novel functional form.
- It produces models with many terms.
- Elite Bases Regression (arXiv:1704.07313) positions itself against FFX in the same regime, using a
  parse-matrix encoding and correlation-based elite basis selection. `UNVERIFIED`: any maintained
  reference implementation, its language and its licence. Its greedy correlation criterion also
  ignores interaction, so a basis that is individually uncorrelated with the target but essential
  jointly will never be selected.

## Citations

- McConaghy, T. (2011). FFX: Fast, Scalable, Deterministic Symbolic Regression Technology. In Genetic
  Programming Theory and Practice IX, Springer, doi:10.1007/978-1-4614-1770-5_13.
- Kronberger, G. et al. (2022). Symbolic Regression with Fast Function Extraction and Nonlinear Least
  Squares Optimization. arXiv:2209.09675. Adds nonlinear least-squares constant fitting on top of the
  FFX bases.
- Chen, C., Luo, C. and Jiang, Z. (2017). Elite Bases Regression: A Real-time Algorithm for Symbolic
  Regression. ICNC-FSKD 2017, arXiv:1704.07313.
- Zou, H. and Hastie, T. (2005). Regularization and variable selection via the elastic net. Journal of
  the Royal Statistical Society B 67(2):301-320, doi:10.1111/j.1467-9868.2005.00503.x. The estimator
  in stage 2.
