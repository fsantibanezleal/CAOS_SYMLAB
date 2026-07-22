# Determinism + the trace

**A run is a pure function of `(params, seed)`.** Use `core/rng.py :: make_rng(seed)`, never a global/implicit
RNG. Same inputs reproduce every scientific number exactly, asserted in
`tests/test_rebake_reproduces_results.py` and, across process boundaries, in
`tests/test_cross_process_determinism.py`. The measured wall clock IS recorded and does vary
between runs, deliberately, because what a rung costs is part of its evaluation: a re-bake shows a
timing diff and never a result diff. This is what makes the
committed artifact a trustworthy source-of-truth the SPA merely animates (ADR-0052 / ADR-0054).

**The trace** (`core/trace.py`, schema `example.trace/v1`) is the compact, decimated replay artifact, not the raw
solver state. `build_trace()` down-samples long trajectories to `MAX_POINTS` so the committed JSON stays small.
For a heavy product the offline run also emits the full raw output (kept local/LFS, git-ignored); only the compact
trace is committed and shipped. Its shape is mirrored by `frontend/src/lib/contract.types.ts` (CONTRACT 2).
