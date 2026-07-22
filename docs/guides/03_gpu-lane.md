# Guide, the GPU lane (optional)

Only for products whose offline engine/sweep/training genuinely needs CUDA (large DEM, big Monte-Carlo, heavy
model training). Never required for the live/replay path.

1. Pin the CUDA build in `requirements-gpu.txt` (e.g. `cupy-cuda12x`, `torch==…+cu12x`, `numba`, `taichi`).
2. On a CUDA box: `.venv/bin/python -m pip install -r requirements-gpu.txt`.
3. Document the engine as a card in `docs/frameworks/`.

The committed artifacts are produced offline regardless of lane, so a GPU-only product still deploys as a
static replay (the browser never needs the GPU).

**SymLab has no GPU step.** The search is a population of small expression trees evaluated against at most
4000 rows, which is memory-bandwidth bound on arrays far too small to repay a device transfer. The costs that
actually dominate are not arithmetic throughput: measured across the committed manifests, with each case's
Koza baseline as 1, epsilon-lexicase selection costs a median of about 24 times the baseline wall clock and the
deduplication rung about 122 times, while linear scaling, constant tuning and multi-objective survival all stay
under 1.5. Neither selection nor deduplication bookkeeping is work a GPU accelerates. `requirements-gpu.txt` is a commented placeholder for
that reason rather than by omission, and it says so in the file.

If a future rung reaches for a differentiable or neural component (a transformer prior over expressions, for
instance), pin it there and revisit the [live/precompute gate](../architecture/03_the-gate.md), which today
states its criteria without being called.
