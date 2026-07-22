# Framework card, TPSR (transformer plus Monte Carlo tree search decoding)

**Status in this repo: SURVEYED, NOT USED.** It is carded because its result changes what a small lab
should build, not because this build uses it.

## What it is, and the one thing it does better

TPSR replaces beam search with Monte Carlo tree search over the decoding tree of a pretrained
symbolic-regression transformer. The transformer's token probabilities become the MCTS prior, and the
reward combines fitting accuracy with an explicit complexity penalty controlled by a `lambda`.

The one thing it does better than the alternatives is that it decouples what the model knows from
what you want. A pretrained model gives `p(next token | prefix, data)`, and beam search decodes it
toward high likelihood. Likelihood is not the objective anyone actually has: the real objective is
fit **and** parsimony, and both are non-differentiable. TPSR makes the pretrained model a proposal
distribution and chooses the optimisation target at inference time.

The verified numbers, from Table 1 of the paper, R2 > 0.99 accuracy and expression complexity:

| Dataset | E2E + beam | E2E + sampling | TPSR (lambda = 0.1) |
|---|---|---|---|
| SRBench Feynman | 0.815 acc / 54.19 cplx | 0.848 acc / 50.73 cplx | **0.949 acc / 57.22 cplx** |
| SRBench Strogatz | 0.357 acc / 53.21 cplx | 0.357 acc / 50.14 cplx | **0.785 acc / 56.14 cplx** |
| SRBench black-box | 0.847 R2 / 83.61 cplx | 0.864 R2 / 82.78 cplx | **0.945 R2 / 95.71 cplx** |

And on a different backbone, Table 3, the 52 Feynman equations with `D <= 3`:

| Backbone | R2 > 0.99 | Complexity |
|---|---|---|
| NeSymReS | 0.635 | 9.98 |
| NeSymReS + TPSR (lambda = 0.1) | **0.808** | **9.98** |

On Strogatz, MCTS decoding more than doubles the accuracy of the same frozen model. On NeSymReS it
lifts accuracy from 0.635 to 0.808 at identical complexity. The weights did not change; only the
decoding did.

## Licence, and whether this MIT repo may use it

MIT (`deep-symbolic-mathematics/TPSR`, verified). Compatible with this repo. It depends on the E2E
and NeSymReS checkpoints, which are Apache 2.0 and MIT respectively, so the whole stack is
permissively licensed.

## Install reality

Source checkout plus both backbone checkpoints (the NeSymReS one via a Google Drive link in the
README). Reported experiments ran on four Quadro RTX 8000 GPUs with 48 GB. Runtime peaks at roughly
10^3 seconds (about 30 minutes) for `d = 9` and stays relatively flat in dimension, unlike genetic
programming. `UNVERIFIED`: inference-time numbers beyond that peak.

## Usage

No snippet. No calling convention was transcribed from a primary source.

## Applying it here

Not used. This build has no transformer, no checkpoint and no MCTS rung.

The transferable claim is recorded because it is the research's first conclusion for a lab of this
size: **a search layer over a public checkpoint is worth more than any model a small lab could
pretrain.** NeSymReS weights are MIT and on Hugging Face, E2E weights are Apache 2.0, and the
measured gains above come entirely from the decoding strategy.

The principle already appears here in a much smaller form, and the parallel should be read as a
parallel and not as an implementation: the objective is imposed at selection time rather than baked
into the generator. Multi-objective survival on (loss, complexity) is
`nsga2_survival` in [`search/select.py`](../../data-pipeline/symlab/search/select.py), the Pareto
front is built from the run archive in
[`search/engine.py`](../../data-pipeline/symlab/search/engine.py), and the front is reduced to one
answer by description length rather than by best accuracy
([`model/complexity.py`](../../data-pipeline/symlab/model/complexity.py), and `description_length`
in `sreval`). Choosing the most accurate member of a front is the field's routine way of inflating a
result, because the most accurate member is usually the most over-parameterised one.

If this lab ever adds a neural rung, TPSR is the shape it should take: a search layer, not a
pretraining run.

## Caveats

- MCTS decoding costs inference time. The gains above are bought with a tree search per problem, not
  with a faster forward pass.
- The reward's `lambda` sets the accuracy-complexity tradeoff, so a TPSR number is only comparable
  against another TPSR number at the same `lambda`.
- Everything inherited from the backbone is still true: the out-of-distribution degradation verified
  for pretrained SR transformers (arXiv:2509.19849) is not fixed by better decoding.
- The E2E backbone's repository is archived read-only ([11_e2e-transformer.md](11_e2e-transformer.md)).

## Citations

- Shojaee, P., Meidani, K., Barati Farimani, A. and Reddy, C. K. (2023). Transformer-based Planning
  for Symbolic Regression. NeurIPS 2023, arXiv:2303.06833.
- Kamienny, P.-A., d'Ascoli, S., Lample, G. and Charton, F. (2022). End-to-end symbolic regression
  with transformers. NeurIPS 2022, arXiv:2204.10532. The backbone in Table 1.
- Biggio, L., Bendinelli, T., Neitz, A., Lucchi, A. and Parascandolo, G. (2021). Neural Symbolic
  Regression that Scales. ICML 2021, arXiv:2106.06427. The backbone in Table 3.
