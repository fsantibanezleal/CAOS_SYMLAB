# Framework card, EvoGP

**Status in this repo: SURVEYED, NOT USED.** It is the only verified GPU-native tree-GP engine, and
it is GPL-3.0. This card exists so the GPU question has a documented answer.

## What it is, and the one thing it does better

EvoGP is a tensorized tree genetic-programming engine with CUDA kernels, parallelising at the level
of the **population** rather than of a single evaluation. It was accepted at IEEE Transactions on
Evolutionary Computation.

The one thing it does better than the alternatives is raw throughput: it reports peak throughput
above 10^11 GP operations per second and speedups up to 304x over prior GPU tree-GP implementations,
with its README stating 100x over existing tree-GP implementations generally.

## Licence, and whether this MIT repo may use it

**No, not as a linked dependency.** GPL-3.0. Linking it into a non-GPL product is not permitted, so
an MIT lab cannot ship it. It could be run separately to produce comparison numbers, in the same way
SRBench can, but it cannot become part of the engine.

## Install reality

`pip install git+https://github.com/EMI-Group/evogp.git --no-build-isolation`. Requires the CUDA
toolkit (or ROCm) and a C++ compiler; Visual C++ Build Tools are documented for Windows. 296 stars.
An NVIDIA GPU is not optional here, it is the point.

## Usage

No snippet. The research verified the packaging, the licence and the reported throughput, not the
API.

## Applying it here

Not used. More usefully, this card records the **GPU position statement** the research asked the lab
to make explicitly, because it is easy to imply otherwise:

Classical genetic-programming symbolic regression is a CPU-bound, branchy, irregular workload. The
NVIDIA GPU in the workstation is not the bottleneck-solver for it. Neither PySR nor Operon has a GPU
search path (`UNVERIFIED` for the PySR 2.0 alpha line), and their published performance comes from
SIMD, cache-friendly encodings and thread-level parallelism on the CPU. EvoGP is the verified
exception, and claiming GPU acceleration for a tree-GP lab without it would be false.

This build's own position is consistent and is stated in
[guides/03_gpu-lane.md](../guides/03_gpu-lane.md): SymLab has no GPU step. The search is a population
of small expression trees evaluated against at most a few thousand rows, which is memory-bandwidth
bound on arrays far too small to repay a device transfer, and the measured cost that matters here is
selection rather than evaluation throughput. The published cost table in
[method-families.md](../method-families.md) supports that: epsilon-lexicase costs 22 times the
baseline wall clock, and it is a selection method, not an evaluation kernel.

[`requirements-gpu.txt`](../../requirements-gpu.txt) exists and is deliberately empty of pins: its
whole content is the reason there is no GPU lane, and the instruction to pin here and reclassify the
case in the live/precompute gate if a future rung ever reaches for a differentiable component. An
earlier version of this card said the file did not exist and argued that its absence was the honest
form. The file was added, this paragraph was not updated with it, and the contradiction stood until
this audit.

## Caveats

- GPL-3.0 forbids linking into a non-GPL product. The speedup is real and unavailable to this repo.
- The reported multipliers are vendor claims from the paper and README. The research transcribed no
  independent runtime table, and no benchmark here reproduces them.
- Population-level tensorization changes the algorithm's shape: it favours large populations of
  bounded-depth trees, which is not the regime every rung of this ladder runs in.

## Citations

- Wu, Z., Wang, L., Sun, K., Li, Z. and Cheng, R. (2025). Enabling Population-Level Parallelism in
  Tree-Based Genetic Programming for GPU Acceleration. arXiv:2501.17168, accepted at IEEE
  Transactions on Evolutionary Computation. This is the EvoGP paper; the framework name is the
  repository's, not the paper title's. The abstract is the source of both figures quoted above:
  peak throughput exceeding 10^11 GP operations per second, and a speedup of up to 304 times over
  existing GPU-based tree-GP implementations (and 18 times over CPU libraries).
- Burlacu, B., Kronberger, G. and Kommenda, M. (2020). Operon C++. GECCO 2020 Companion,
  doi:10.1145/3377929.3398099. The CPU counterfactual: SIMD and parallel execution policies rather
  than a device.
