# Framework card, PySINDy

**Status in this repo: SURVEYED, NOT USED.** It solves a different problem class: this build has no
dynamics track and no derivative-estimation stage.

## What it is, and the one thing it does better

SINDy (sparse identification of nonlinear dynamics) fixes the search space and solves for
coefficients. Given state snapshots `X` in R^(m x n) and time derivatives `Xdot`, build a library of
candidate functions evaluated on the data,

    Theta(X) = [ 1 | X | X^P2 | X^P3 | ... | sin(X) | cos(X) | ... ]   in R^(m x p)

and solve `Xdot = Theta(X) Xi` for a **sparse** coefficient matrix `Xi`. Each column of `Xi` is the
right-hand side of one state equation. The whole method rests on the assumption that the dynamics are
sparse in the chosen dictionary.

PySINDy is the mature implementation of that family. Verified exported optimizers:
`STLSQ`, `SR3`, `ConstrainedSR3`, `StableLinearSR3`, `TrappingSR3`, `SSR`, `FROLS`, `SINDyPI`,
`MIOSR`, `SBR`, `EnsembleOptimizer`, `WrappedOptimizer`, `EvidenceGreedy`, `BaseOptimizer`. Verified
exported feature libraries: `PolynomialLibrary`, `FourierLibrary`, `CustomLibrary`, `IdentityLibrary`,
`PDELibrary`, `WeakPDELibrary`, `SINDyPILibrary`, `ConcatLibrary`, `TensoredLibrary`,
`GeneralizedLibrary`, `ParameterizedLibrary`.

The one thing it does better than the alternatives is **uncertainty on the discovered structure**.
Tree symbolic regression has essentially none in production tools: you get one expression, or a
Pareto front, with no probability attached to the structure. PySINDy gives two mature routes:

- `EnsembleOptimizer` bootstraps rows (bragging) or dictionary columns (library bagging) and returns
  an inclusion probability per term, `p_j = (models where xi_j != 0) / (number of models)`, with no
  MCMC.
- `SBR` runs sparse Bayesian regression through numpyro and jax, giving a **posterior inclusion
  probability** per dictionary term, which is precisely the quantity a scientist means by "is this
  term real".

Two robustness results worth carrying:

- **Weak-form SINDy** removes numerical differentiation entirely by multiplying the equation by a
  compactly supported test function and integrating by parts, so no pointwise derivative of the data
  ever appears. Its authors state it improves on standard SINDy by orders of magnitude. Numerical
  differentiation, not the regression, is the dominant error source, so this is the single highest
  value trick in the family.
- **Ensemble-SINDy** with library bagging recovers PDE models from data with more than twice as much
  noise as previously possible.

## Licence, and whether this MIT repo may use it

MIT (read from the repository `LICENSE` on 2026-07-22; copyright M. Quade 2019 for the
sparsereg-derived portions, B. de Silva and K. Champion 2019 for the rest, over the standard MIT
text). Compatible with this repo. One wrinkle worth recording because it looks alarming and is not:
GitHub's licence endpoint reports `NOASSERTION` for this repository, because the split-copyright
header stops its detector matching the template. The PyPI metadata and the file itself both say MIT.
Two optional paths carry their own terms: `MIOSR` needs Gurobi (commercial, free academic licence),
and the `sbr` extra pulls numpyro and jax.

## Install reality

`pip install pysindy`. Release v2.1.0 dated 2026-01-08. Its published metadata declares
`requires-python >= 3.10`, `numpy >= 2.0` and `scikit-learn >= 1.1` with three excluded point
releases (1.5.0, 1.6.0, 1.7.1), plus `derivative >= 0.6.2` and scipy. An earlier version of this
card said Python >= 3.11; the wheel says 3.10. CPU. Extras: `cvxpy` for some SR3 variants,
`gurobipy` for MIOSR, `numpyro` and `jax` for SBR.

## Usage

No calling-convention snippet. What the research verified is the class inventory above and the
mathematics; the fitting API was not transcribed, and the JOSS papers plus the documentation site are
the source for it.

## Applying it here

Not used, and the reason is that it answers a different question.

| | SINDy family | This build |
|---|---|---|
| Search space | fixed, finite dictionary of `p` terms; the unknown is a coefficient vector | open space of expression trees over an operator set |
| Optimisation | linear in the parameters; convex under an L1 relaxation, exactly solvable with MIOSR | non-convex, discrete, combinatorial |
| Expressive limit | cannot discover a term absent from the dictionary; `sin(exp(x))` needs an explicit column | composes to arbitrary depth |
| Native output | a differential equation with coefficients | an algebraic expression |
| Uncertainty | mature | immature, here and everywhere else |

This lab's cases are algebraic (`y = f(x)`) and carry no time axis, so there is nothing for a dynamics
identifier to identify: `Xdot` does not exist. The registry is in
[`data-pipeline/symlab/cases/registry.py`](../../data-pipeline/symlab/cases/registry.py) and the
taxonomy in [docs/cases.md](../cases.md).

The two are best read as points on a prior-strength axis rather than as rivals. SINDy imposes a very
strong structural prior and buys robustness and speed; tree search imposes a very weak one and buys
expressiveness at the price of search cost and seed variance. This build sits at the weak-prior end,
and its rungs 2, 3 and 8 (linear scaling, closed-form constant fitting, unit typing) are all attempts
to add back some of what the strong prior gives for free.

The research named uncertainty quantification, composed with active learning, as the second highest
leverage direction available to a small lab, and named PySINDy's `EnsembleOptimizer` and `SBR` as the
existing MIT-licensed components to build it from. Nothing of that kind exists in this build today,
and it is recorded here as an absence rather than a plan.

## Caveats

- Dictionary misspecification is the failure mode, and it is silent: the method returns the best
  sparse combination of terms you supplied, whether or not the true term is among them.
- Severe collinearity as the library grows.
- `UNVERIFIED`: which paper `EvidenceGreedy` implements. It does not appear in older literature
  summaries and its provenance should be read from the source.
- `UNVERIFIED`: primary citations for `SSR` (commonly attributed to Boninsegna, Nueske and Clementi,
  J. Chem. Phys. 2018), for `FROLS` (commonly attributed to Billings and coworkers in the NARMAX
  literature), and for implicit SINDy (commonly attributed to Mangan, Brunton, Proctor and Kutz,
  2016). None was confirmed against a primary source.
- `UNVERIFIED`: SR3's journal of record; only the arXiv identifier is confirmed.

## Citations

- Brunton, S. L., Proctor, J. L. and Kutz, J. N. (2016). Discovering governing equations from data by
  sparse identification of nonlinear dynamical systems. PNAS 113(15):3932-3937,
  doi:10.1073/pnas.1517384113, arXiv:1509.03580.
- de Silva, B. M., Champion, K., Quade, M., Loiseau, J.-C., Kutz, J. N. and Brunton, S. L. (2020).
  PySINDy: A Python package for the sparse identification of nonlinear dynamical systems from data.
  Journal of Open Source Software 5(49):2104, doi:10.21105/joss.02104.
- Kaptanoglu, A. A. et al. (2022). PySINDy: A comprehensive Python package for robust sparse system
  identification. JOSS 7(69):3994, doi:10.21105/joss.03994.
- Messenger, D. A. and Bortz, D. M. (2021). Weak SINDy: Galerkin-based data-driven model selection.
  arXiv:2005.04339, doi:10.1137/20M1343166. PDE version: arXiv:2007.02848.
- Fasel, U., Kutz, J. N., Brunton, B. W. and Brunton, S. L. (2022). Ensemble-SINDy. Proceedings of
  the Royal Society A 478(2260):20210904, doi:10.1098/rspa.2021.0904, arXiv:2111.10992.
- Hirsh, S. M., Barajas-Solano, D. A. and Kutz, J. N. (2022). Sparsifying priors for Bayesian
  uncertainty quantification in model discovery. Royal Society Open Science 9(2):211823,
  doi:10.1098/rsos.211823, arXiv:2107.02107.
- Bertsimas, D. and Gurnee, W. (2022). Learning sparse nonlinear dynamics via mixed-integer
  optimization. arXiv:2206.00176.
- Kaheman, K., Kutz, J. N. and Brunton, S. L. (2020). SINDy-PI. Proceedings of the Royal Society A
  476(2242):20200279, doi:10.1098/rspa.2020.0279.
- Rudy, S. H., Brunton, S. L., Proctor, J. L. and Kutz, J. N. (2017). Data-driven discovery of
  partial differential equations. Science Advances 3:e1602614. Code at `github.com/snagcliffs/PDE-FIND`;
  `UNVERIFIED` licence.
