# Framework card, pykan (Kolmogorov-Arnold Networks)

**Status in this repo: SURVEYED, NOT USED.** It is carded because the KAN-to-formula pipeline is
widely presented as solved and the primary sources say it is not.

## What it is, and the one thing it does better

A Kolmogorov-Arnold Network puts **learnable univariate activation functions on the edges** and plain
summation at the nodes, inverting the multilayer perceptron's arrangement of fixed activations at
nodes and learnable weights on edges. Each edge function is a B-spline plus a residual basis:

    phi(x) = w_b * silu(x) + w_s * sum_i c_i B_i(x)

where `B_i` are B-spline basis functions on a grid and `c_i` are learnable. MultKAN (KAN 2.0) adds
multiplication nodes, which matters because pure summation nodes make products expensive to
represent.

The symbolic pitch is that each `phi` is a single-variable function you can look at. The symbolic
workflow fits each learned edge function against a library of candidate primitives with affine pre-
and post-transforms,

    phi(x)  approx  c * f(a*x + b) + d

selecting the best-fitting candidate and composing the network into a closed form through sympy.
KAN 2.0 adds a Kanpiler (compiles symbolic formulas into KANs, the inverse direction), a tree
converter, and claimed discovery of conserved quantities, Lagrangians, symmetries and constitutive
laws.

The one thing it does better than the alternatives is that it produces a **decomposition into
univariate functions** as a byproduct of fitting. That is a genuinely useful structural prior for
symbolic regression, and it is the same factor-the-problem idea as AI Feynman's separability tests
and as symbolic distillation of a graph neural network.

## Licence, and whether this MIT repo may use it

MIT (verified in the raw `LICENSE`, copyright Ziming Liu 2024). Compatible with this repo.

## Install reality

`pip install pykan`. Latest release v0.2.8 dated 2024-11-14. Requires Python >= 3.9.7 and PyTorch
2.2.2. CPU or GPU. For a package under this much research attention, the release cadence stalling in
November 2024 is a maintenance signal worth noting.

The extracted formula is trivially runnable in a browser; the KAN itself is not a good browser
target, and the splines export awkwardly.

## Usage

`UNVERIFIED` at the API level. The repository README confirms the existence of "the symbolic branch"
and advises calling `model.speed()` before training if you are not using it, because **symbolic
computations are not parallelized**. The specific function names `auto_symbolic` and
`symbolic_formula` are widely referenced in the community but were not confirmed from a primary
source, so no snippet is written here.

## Applying it here

Not used. There is no PyTorch dependency in any requirements file in this repo, no neural component
in [`data-pipeline/symlab/`](../../data-pipeline/symlab/), and no place a spline network would fit
into the pipeline's stages.

What is carried forward is the criticism, because it is the part a public lab is obliged to state.
Four verified points:

1. **The symbolic advantage comes from the B-splines, not from the KAN structure.** A controlled
   comparison with equalized parameter counts and FLOPs found that KAN excels at symbolic formula
   representation but that the advantage mainly stems from the B-spline activation, and that
   integrating B-splines into MLPs improves MLP performance significantly. Across machine learning,
   computer vision, NLP and audio, MLP generally outperformed KAN. KAN's forgetting in continual
   learning was also **more severe** than MLP's, contradicting the original paper's claim.
2. **Cost.** Roughly 2x the wall time of same-size MLPs because splines are computed recursively,
   worse for PDE solving, and the symbolic branch is explicitly not parallelized. The interpretable
   mode is the slow mode.
3. **Stability.** Reported instability at large depths and large grid sizes, with training
   compromised around grid size 20, and reduced effectiveness on noisy functions.
4. **The symbolification step is the weak link.** The standard KAN-to-symbol approach fits operators
   **in isolation**: each edge function is symbolised greedily against its own local spline, with no
   regard for how the substitution error propagates through the composition. The published fix,
   Greedy in-context Symbolic Regression, chooses each edge replacement by **end-to-end loss
   improvement** rather than local fit quality and reports up to a 99.8% reduction in median OFAT
   test MSE.

The lab's position, stated so it is not mistaken for dismissal: KAN gives a useful structural
decomposition, the symbolification step is not free, a naive automatic symbolic call can destroy a
model that fit fine, and KAN-to-formula should not be presented as a solved pipeline.

## Caveats

- `UNVERIFIED`: the exact pykan API names for the symbolic branch.
- `UNVERIFIED`: contents beyond title, identifier, authors and date for the 2026 KAN-symbolic papers
  the research listed, specifically SINDy-KANs (arXiv:2603.18548), Symbolic-KAN (arXiv:2603.23854),
  Deep-Koopman-KANDy (arXiv:2605.06000) and constrained KANs for integro-differential equations
  (arXiv:2607.11110). Symbolic-KAN is the one to watch: it claims to embed discrete symbolic
  structure directly in the trainable network, giving closed forms without post-hoc symbolic fitting,
  which would remove the weak link above.

## Citations

- Liu, Z., Wang, Y., Vaidya, S., Ruehle, F., Halverson, J., Soljačić, M., Hou, T. Y. and Tegmark, M.
  (2025). KAN: Kolmogorov-Arnold Networks. ICLR 2025, arXiv:2404.19756.
- Liu, Z., Ma, P., Wang, Y., Matusik, W. and Tegmark, M. (2024). KAN 2.0: Kolmogorov-Arnold Networks
  Meet Science. arXiv:2408.10205.
- Yu, R., Yu, W. and Wang, X. (2024). KAN or MLP: A Fairer Comparison. arXiv:2407.16674.
- Sovrano, F., Losavio, S., Vilone, G. and Langheinrich, M. (2026). arXiv:2603.15250. Greedy
  in-context Symbolic Regression and Gated Matching Pursuit for KAN symbolification.
