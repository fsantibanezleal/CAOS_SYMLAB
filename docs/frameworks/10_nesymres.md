# Framework card, NeSymReS (Neural Symbolic Regression that Scales)

**Status in this repo: SURVEYED, NOT USED.** No pretrained model is downloaded, shipped or executed
anywhere in this build.

## What it is, and the one thing it does better

NeSymReS moves the combinatorial search offline. A transformer is pretrained on a very large corpus
of synthetically generated (function, sampled points) pairs, so that at inference time one forward
pass plus a decode produces a candidate expression in seconds.

Architecture, verified from the paper rendering:

| Part | Detail |
|---|---|
| Encoder | Set Transformer, 5 Induced Set Attention Blocks, hidden 512, 8 heads, 50 inducing points, latent dimension 10, 11M parameters |
| Decoder | Standard transformer, 5 layers, hidden 512, 8 heads, embedding 32, vocabulary 32 tokens, 15M parameters |
| Total | 26M parameters, operating on IEEE-754 half-precision bit representations of the numeric inputs |

A set-based encoder is the right choice because the input is an unordered set of (x, y) points. The
decoder emits a **skeleton**, the expression with placeholder constants, and the constants are then
fit by BFGS on the actual data.

The one thing it does better than the alternatives is inference cost at usable accuracy: on
AI-Feynman it is more than **three orders of magnitude faster** than genetic programming while
reaching equivalent maximum accuracy. It is also the first SR method whose accuracy **improves with
pretraining set size**, where the baselines show no such scaling.

The price of that is verified and worth quoting whenever the speed is: about 225M distinct equations
seen over 1.5M training steps at batch size 150, from a pre-compiled library of 10M unique skeletons,
trained on a single GeForce RTX 2080 for **333 days**.

## Licence, and whether this MIT repo may use it

MIT (`SymposiumOrganization/NeuralSymbolicRegressionThatScales`, verified on the repository page).
Compatible with this repo. The pretrained checkpoints are hosted on Hugging Face at
`huggingface.co/TommasoBendinelli/NeuralSymbolicRegressionThatScales`, in two variants trained on 10M
and 100M datasets. `UNVERIFIED`: the file sizes of those checkpoints.

This is the most accessible pretrained SR checkpoint in the field, and the licence is not the reason
it is unused here.

## Install reality

Source checkout plus PyTorch, plus a checkpoint download. Inference fits comfortably on a single GPU
because the model is 26M parameters; the pretraining figure above is what it cost to make, not what
it costs to run.

Browser and ONNX status: `UNVERIFIED`, and deliberately so. No primary source documents an ONNX
export path for NeSymReS or for any other transformer in this family. The encoder and decoder forward
passes are plausibly exportable; the beam search and the BFGS constant refit sit outside the graph.
Every claim of that kind is an engineering hypothesis the lab would have to test, not a documented
fact.

## Usage

No snippet. The research transcribed architecture and training facts from the paper, not the
repository's calling convention, and a fabricated API call would be worse than an omission.

## Applying it here

Not used. There is no PyTorch dependency in any requirements file
([`requirements.txt`](../../requirements.txt) is numpy only,
[`requirements-precompute.txt`](../../requirements-precompute.txt) adds two spreadsheet readers,
`sreval[symbolic]` and sympy), no checkpoint in `models/`, whose only file is a four-term linear
least-squares surrogate, and no inference stage that would load one.

The reasons are scope rather than merit. This lab's argument is about the classical spine and about
the measurement of recovery, and a pretrained transformer is a different product: it needs a weights
distribution story, a version pin on a checkpoint hosted by a third party, and an out-of-distribution
warning on every result. Adopting one would be a decision to make deliberately, not a dependency to
add quietly.

If it were adopted, the research's recorded conclusion is that the search layer is worth more than
the model: see [12_tpsr.md](12_tpsr.md), where MCTS decoding lifts a frozen NeSymReS from 0.635 to
0.808 accuracy at identical complexity.

## Caveats

- Small input dimensionality. The model was designed around few variables, and TPSR's comparison
  evaluates NeSymReS only on the 52 Feynman equations with `D <= 3`.
- Skeleton-then-BFGS means a correct structure with a poor constant fit is scored as a failure.
- It inherits its prior from the synthetic generator. If a real function is unlike the generator's
  distribution, the model has never seen anything like it. The adversarial paper on this family
  (arXiv:2509.19849) verifies that transformer SR models perform well in distribution and
  **consistently degrade out of distribution**, and calls that gap a critical barrier for
  practitioners. Any product built on one must surface it.

## Citations

- Biggio, L., Bendinelli, T., Neitz, A., Lucchi, A. and Parascandolo, G. (2021). Neural Symbolic
  Regression that Scales. ICML 2021, PMLR v139, arXiv:2106.06427.
- Valipour, M., You, B., Panju, M. and Ghodsi, A. (2021). SymbolicGPT: A Generative Transformer Model
  for Symbolic Regression. arXiv:2106.14131. The first "SR as language modelling" paper, superseded
  technically, included as history.
- Voigt, K., Kahlmeyer, P., Lawonn, K., Habeck, M. and Giesen, J. (2025). Analyzing Generalization in
  Pre-Trained Symbolic Regression. arXiv:2509.19849.
