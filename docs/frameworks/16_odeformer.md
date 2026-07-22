# Framework card, ODEFormer

**Status in this repo: SURVEYED, NOT USED.** There is no dynamics track here. It is carded for its
benchmark and for one measured result that every SR lab should quote.

## What it is, and the one thing it does better

ODEFormer is the first transformer that infers a **multidimensional ODE system in symbolic form from
a single observed solution trajectory**. It is the transformer answer to SINDy.

Architecture, verified: encoder-decoder transformer with 4 encoder layers, 16 decoder layers, 16
attention heads, embedding dimension 512, 86M parameters, the same shape as E2E. Floating-point
values are tokenized as three tokens (sign, mantissa, exponent), and an embedding layer compresses
the trajectory back to its original length before encoding.

Training data, verified: synthetic random ODE systems with dimension sampled from [1, 6], up to 5
binary and 3 unary operators per component, integrated over [1, 10] with 50 to 200 points per
trajectory.

The one thing it does better than the alternatives is noisy, subsampled dynamics. On clean Strogatz
data it is top, occasionally matched by PySR. Under **5% noise and 50% subsampling** it substantially
outperforms all eight baselines tested, which include ProGED, SINDy variants and the genetic
programming methods AFP, FE-AFP, EHC and EPLEX. Inference is on the order of seconds against minutes,
and the complexity of the produced equations stays low and stable even at high noise.

## Licence, and whether this MIT repo may use it

MIT (`github.com/sdascoli/odeformer`, verified). Compatible with this repo. A pretrained model is
loaded in the demo notebook; `UNVERIFIED`: its size.

## Install reality

`pip install odeformer`, plus PyTorch and a checkpoint download. Inference on one GPU is adequate at
86M parameters and is reported in the order of seconds. `UNVERIFIED`: the total training dataset
size, training hardware and training duration, none of which the paper states.

## Usage

No snippet. No calling convention was transcribed from a primary source.

## Applying it here

Not used. This build has no time axis in any case, no derivative estimation and no ODE contract, so
there is nothing for it to infer.

Two things from the paper are recorded here because they would shape a dynamics track if one is ever
added:

**ODEBench is the benchmark to adopt.** Counted directly from `odeformer/odebench/strogatz_extended.json`:
63 systems, being 23 one-dimensional, 28 two-dimensional, 10 three-dimensional and 2 four-dimensional,
of which 4 are chaotic. That is a substantially better dynamics benchmark than the 14-dataset,
two-state ODE-Strogatz set that SRBench uses, and it is MIT-licensed and machine-readable.

**The generalization result is the one to quote.** On the generalization metric, does the discovered
ODE reproduce trajectories from *new initial conditions* rather than only the one it was fitted to,
accuracy drops by roughly half compared with the reconstruction metric, **for every method tested,
ODEFormer included**. It merely remains the best relatively. A lab that reports only reconstruction
accuracy is misleading its users, and the research names a systematic cross-family study of that gap
as a pure evaluation contribution with high credibility and low risk.

The algebraic analogue of that trap is already handled here: this lab distinguishes interpolation
from extrapolation and reports the accuracy solution rate separately from the recovery rate
([docs/README.md](../README.md)).

## Caveats

- The generalization drop above is the headline caveat and it belongs to the whole field, not to this
  model.
- `UNVERIFIED`: whether ODEFormer was published at ICLR 2024. The neural-methods research pass
  records ICLR 2024; the benchmarks pass explicitly marks the venue unverified, having confirmed only
  the arXiv listing. Both are recorded; do not state the venue as fact without closing it.
- Everything true of pretrained SR transformers is true here: out-of-distribution degradation
  (arXiv:2509.19849), and ONNX or browser export status `UNVERIFIED` with no documented path.

## Citations

- d'Ascoli, S., Becker, S., Mathis, A., Schwaller, P. and Kilbertus, N. (2024). ODEFormer: Symbolic
  regression of dynamical systems with transformers. arXiv:2310.05573.
- La Cava, W., Danai, K. and Spector, L. Inference of compact nonlinear dynamic models by epigenetic
  local search. Engineering Applications of Artificial Intelligence,
  doi:10.1016/j.engappai.2016.07.004. The ODE-Strogatz set ODEBench extends.
