# Determinism + the artifact

**A run is a pure function of `(case, config, seed, data)`.** Always thread an explicit
`numpy.random.Generator` built from the declared seed, never a global or implicit RNG, and never the builtin
`hash()`: string hashing is randomised per process, so a `hash()`-seeded generator drew different data from the
same declared seed and made the deduplication rung's measured effect a property of interpreter startup. Both
call sites in `stages/preprocess.py` construct `np.random.default_rng(seed)` directly. (`core/rng.py ::
make_rng` offers the same factory but is left over from the archetype template and is called by nothing here.)

Same inputs reproduce every scientific number exactly, asserted in `tests/test_rebake_reproduces_results.py`
and, across process boundaries, in `tests/test_cross_process_determinism.py`. The latter also parses every
module and fails on any call to the builtin `hash()`, so the defect cannot be reintroduced. The measured wall
clock IS recorded, on every variant, and does vary between runs, deliberately, because what a rung costs is
part of its evaluation: a re-bake shows a timing diff and never a result diff. `test_rebake_reproduces_results`
pins both halves of that, requiring the two documents to agree once `seconds`, `wall_seconds`, `total_seconds`
and `generated_on` are stripped, and separately requiring `seconds` to still be there. This is what makes the
committed artifact a trustworthy source-of-truth the SPA merely animates (ADR-0052 / ADR-0054).

**The artifact** is `data/derived/<case>/run.json`, assembled by `core/contract.py :: run_payload` and written
by `stages/export.py`. It is the compact replay document, not the raw solver state: floats are serialised to
ten significant digits (not to a fixed number of decimals, which would publish a mean squared error of 6.1e-12
as `0.0`), non-finite values become `null` rather than crashing the encoder, and each variant exports at most
`MAX_EXPORTED_MEMBERS = 12` Pareto members with the true front size alongside, so the cap is disclosed rather
than applied silently. Its shape is mirrored by `frontend/src/lib/contract.types.ts` (CONTRACT 2), frozen at
`schema_version 1.0.0`.

`core/trace.py` (schema `example.trace/v1`, `build_trace()`, `MAX_POINTS`) is not part of this: it decimates an
SIR trajectory and is template residue that nothing imports. It is named here only because an earlier version
of this page described it as the product's artifact.
