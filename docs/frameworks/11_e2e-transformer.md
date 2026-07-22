# Framework card, E2E (end-to-end symbolic regression with transformers)

**Status in this repo: SURVEYED, NOT USED.** Its repository has been archived read-only since
2023-10-31, which is the largest supply-chain risk in the transformer SR family.

## What it is, and the one thing it does better

E2E is the pretrained transformer that stopped emitting skeletons. Where NeSymReS predicts an
expression with placeholder constants and fits them afterwards by BFGS, E2E **predicts the constants
too, in the same sequence**. Numbers are tokenized as three tokens (sign, mantissa, exponent), so a
float is representable in the vocabulary. A BFGS refinement still runs, but it starts from the
model's own predicted constants rather than from random.

Architecture, verified from the paper rendering: an asymmetric sequence-to-sequence transformer with
4 encoder layers, 16 decoder layers, 16 attention heads, embedding dimension 512, 86M parameters
total. An embedder compresses each input point into a single embedding, which is how it avoids the
quadratic attention cost over hundreds of points.

Training, verified: random expression trees with up to 10 input dimensions, up to 5 binary and 5
unary operators, 100 to 200 input points per function sampled from multimodal distributions, roughly
150M examples over about 50 epochs on 32 GPUs of 32 GB, at about half an hour per epoch.

The one thing it does better than the alternatives is its position on the accuracy-complexity plane.
On SRBench Feynman it ranked fourth in accuracy but produced formulas of **lower complexity than the
top competitors**, at inference several orders of magnitude faster than genetic-programming
baselines. The Pareto position, not the raw accuracy rank, is the selling point.

## Licence, and whether this MIT repo may use it

Apache 2.0 (`github.com/facebookresearch/symbolicregression`, verified on the repository page).
Permissive and compatible with an MIT product. Pretrained weights are published at
`https://dl.fbaipublicfiles.com/symbolicregression/model1.pt`, verified as the exact file the SNIP
and TPSR READMEs instruct downloading. `UNVERIFIED`: its size.

## Install reality

Source checkout of an archived repository, plus a weight download. The repository pins an old stack
(PyTorch tested at 1.3, and a forked `sympytorch` from a personal GitHub account). Any lab depending
on E2E must vendor the code and modernise it.

That matters more than it would for an isolated project, because E2E is the backbone under TPSR,
under SNIP, and under several 2025-2026 papers. A single archived repository sits under a large part
of the pretrained SR literature.

## Usage

No snippet. The research transcribed architecture, training and results from the paper; the calling
convention was not read, and a fabricated one would be worse than an omission.

## Applying it here

Not used. Same position as [NeSymReS](10_nesymres.md): no PyTorch dependency, no checkpoint, no
inference stage. The archived-repository risk is an additional reason not to take the dependency
casually, but it is not the deciding one; the deciding one is that this lab's scope is the classical
spine and the measurement of recovery.

The idea worth carrying forward without the model is the tokenisation decision: predicting constants
inside the sequence removes an entire failure mode (a correct structure scored as a failure because
its constants were fitted badly). The equivalent in this build is that constants are fitted, not
searched, in closed form where possible
([`model/scaling.py`](../../data-pipeline/symlab/model/scaling.py)) and by Levenberg-Marquardt
otherwise ([`search/tune.py`](../../data-pipeline/symlab/search/tune.py)), so the search is never
asked to discover a number it can solve for.

## Caveats

- The repository is archived read-only since 2023-10-31 (verified). No fixes, no dependency updates.
- The out-of-distribution degradation verified for this family (arXiv:2509.19849) applies here.
- `UNVERIFIED`: ONNX exportability and browser runnability, as for every model in this family. The
  numeric tokenizer and the BFGS refinement sit outside any exported graph.
- Related work developed concurrently with the same central insight: SymFormer (arXiv:2205.15764)
  emits symbols and their constants simultaneously on the stated argument that separately optimised
  constants yield suboptimal results. `UNVERIFIED`: SymFormer's repository URL and licence.

## Citations

- Kamienny, P.-A., d'Ascoli, S., Lample, G. and Charton, F. (2022). End-to-end symbolic regression
  with transformers. NeurIPS 2022, arXiv:2204.10532.
- Vastl, M., Kulhánek, J., Kubalík, J., Derner, E. and Babuška, R. (2022). SymFormer: End-to-end
  symbolic regression using transformer-based architecture. arXiv:2205.15764.
- Meidani, K., Shojaee, P., Reddy, C. K. and Barati Farimani, A. (2024). SNIP: Bridging Mathematical
  Symbolic and Numeric Realms with Unified Pre-training. ICLR 2024 Spotlight, arXiv:2310.02227. Uses
  the E2E decoder weights; its contrastive symbolic-numeric latent space is the most direct bridge to
  gradient-free search over expression space.
