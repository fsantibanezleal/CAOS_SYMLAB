# Framework card, ESR (Exhaustive Symbolic Regression)

**Status in this repo: SURVEYED, NOT USED, and the same rung is implemented independently.** This is
the one card where this build ships its own version of the method rather than only its principle.

## What it is, and the one thing it does better

ESR enumerates. Four stages:

1. **Enumerate every tree** of complexity up to `k` over a chosen operator basis. Complexity is node
   count, so the enumeration is finite and complete at each level.
2. **Deduplicate by symbolic equivalence**, so that `x*x`, `x^2` and `(x*x)*1` collapse to one
   representative. This is the step that makes exhaustive search tractable at all.
3. **Fit parameters** by maximum likelihood for each surviving structure.
4. **Rank by minimum description length**, trading goodness of fit against the codelength of the
   function, its parameters and its residuals.

The one thing it does better than every other method in this card set is that it can prove a
negative. It is the only approach that returns a completeness certificate: nothing simpler over this
basis fits better. Every other engine returns the best expression it *found*.

Its headline application is cosmological and is the right kind of result to reproduce: applied to
cosmic chronometer and supernova data, it found roughly 40 functions fitting better than the Friedmann
equation. That is a statement about model selection, not about cosmology, and it is exactly the sort
of adversarial finding a lab should be willing to publish.

## Licence, and whether this MIT repo may use it

MIT, but declared rather than shipped, and the difference matters for a repo that has to be able to
point at a file. Read on 2026-07-22: `github.com/DeaglanBartlett/ESR` carries NO `LICENSE` file in
its root, GitHub's licence endpoint returns none for it, and the only declaration is in `setup.py`,
which sets `license='MIT licence'` and the classifier `'License :: MIT License'`. Nothing here is
copied into this repo, so nothing turns on it today; if any ESR code were ever vendored, that file
would have to exist first. The earlier reading of this card, "MIT, copyright 2022 Deaglan J.
Bartlett", asserted a copyright line that no licence file carries.

## Install reality

`git clone` then `pip install -e ESR`. There is no PyPI package. Documentation at esr.readthedocs.io.
Repository last pushed 2026-07-16, 35 stars.

The real install cost is data, not code: the precomputed function sets are published as multi-GB
Zenodo artifacts (doi:10.5281/zenodo.7339113). That is why full-scale ESR cannot run in a browser,
though a truncated basis at low complexity absolutely can.

## Usage

No snippet. The research verified the algorithm, the licence and the artifact distribution, not the
package's calling convention.

## Applying it here

**The rung is implemented here, from the paper's method, not from its code.**
[`data-pipeline/symlab/search/exhaustive.py`](../../data-pipeline/symlab/search/exhaustive.py)
enumerates by node count, building each size from smaller ones, with structural deduplication through
`canonical_key` so commutative rearrangements are enumerated once, an interval-arithmetic
admissibility filter, Levenberg-Marquardt fitting of a single constant placeholder leaf, and a
description-length ranking. The deep page is
[method-families/06_exhaustive.md](../method-families/06_exhaustive.md).

Measured in this build: 573 expressions enumerated over four operators up to 5 nodes, 546 admissible
after the interval guard, recovering `x0 * x1` exactly at zero mean squared error, with the
certificate complete. Reproduced on 2026-07-22 at the conditions that make the count meaningful:
the `arithmetic` primitive set, two input variables plus the constant placeholder, `max_nodes = 5`,
guard margin 0.25.

Three differences from ESR that must not be blurred:

1. **The codelength is not ESR's.** The exact minimum-description-length formula of Bartlett et al. is
   marked `UNVERIFIED` in the research (it was not transcribed from the PDF), so it is deliberately
   not reproduced. This build uses the description length defined in
   [`model/complexity.py`](../../data-pipeline/symlab/model/complexity.py) and says so wherever it
   reports a number. A number ranked by this codelength is not comparable with a number ranked by
   ESR's.
2. **The scale is not ESR's.** No precomputed Zenodo function sets are shipped or downloaded. The
   enumeration here runs live at low complexity over a small basis, which is what makes it a browser
   demonstration rather than a cosmology tool.
3. **The certificate is bounded and says so.** If the enumeration hits its cap, it is marked INVALID
   explicitly. A truncated enumeration proves nothing and must never be presented as if it did.

## Caveats

- Combinatorial explosion. The regime is small operator bases, complexity up to roughly 10 nodes, and
  one or two input variables.
- Constants are fitted after enumeration, so only expression **structures** are exhaustively covered.
  Enumerating constant values is not possible, and pretending otherwise would make the certificate
  false.
- `UNVERIFIED`: the exact MDL codelength formula in Bartlett et al. Read it from the PDF before any
  claim of comparability with published ESR results.

## Citations

- Bartlett, D. J., Desmond, H. and Ferreira, P. G. (2023). Exhaustive Symbolic Regression. IEEE
  Transactions on Evolutionary Computation 28(4):950-964, doi:10.1109/TEVC.2023.3280250,
  arXiv:2211.11461. Precomputed function sets: doi:10.5281/zenodo.7339113.
- Kronberger, G. et al. (2020). Symbolic Regression by Exhaustive Search: Reducing the Search Space
  Using Syntactical Constraints and Efficient Semantic Structure Deduplication.
  doi:10.1007/978-3-030-39958-0_5. The same deduplication idea, arrived at independently.
- Desmond, H. (2025). (Exhaustive) Symbolic Regression and model selection by minimum description
  length. arXiv:2507.13033. The argument for measuring accuracy and complexity in the same units,
  bits, rather than trading them off with an arbitrary heuristic.
- Worm, T. and Chiu, K. (2013). Prioritized grammar enumeration: symbolic regression by dynamic
  programming. GECCO 2013 (Best Paper), doi:10.1145/2463372.2463486. The deterministic-enumeration
  ancestor, whose ideas (memoisation on a canonical form, a Pareto priority queue, abstract
  parameters fitted after the structural search) are absorbed into this rung and into deduplication.
  Its implementation, `verdverm/pypge`, is Docker-only and dormant.
