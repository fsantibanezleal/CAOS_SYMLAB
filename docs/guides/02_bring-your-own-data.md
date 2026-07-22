# Guide, bring your own data

The product is **applicable to NEW data**, not just the baked cases, that is what makes it a tool. The door is
**CONTRACT 1**, enforced in `data-pipeline/symlab/stages/preprocess.py :: _contract_check`. (The file named
`symlab/io/contract.py` is template residue describing an SIR parameter table; nothing imports it.)

1. Put your data in the documented standard format (see [`data/README.md`](../../data/README.md)): one numeric
   column per input, one target column, and a unit per column where you know it. Raw files stay out of git; the
   download vault lives outside the repository (`io/sources.py :: VAULT`).
2. Register it as a case in `data-pipeline/symlab/cases/registry.py` and give it a loader in
   `data-pipeline/symlab/io/loaders.py`, then run `scripts/precompute.{sh,ps1}`. CONTRACT 1 validates the
   dataset before any search runs and **refuses** it, with every reason named at once, when:
   - it has fewer than 20 rows, too few for a train/test split
   - any input or target value is non-finite
   - the target has zero variance, so there is nothing to model

   It **warns and records**, rather than refusing, when an input column is constant, or when the target takes
   so few distinct values relative to its row count (more than 3 repeats each) that fitting at that resolution
   may leak it. Those warnings travel into both the manifest and the web payload, so the reader who most needs
   them can see them. Anything the loader had to do to make the data usable (rows dropped, folds ignored,
   aggregation applied, deterministic subsampling) is recorded as a defect and published in the artifact, not
   tidied away.
3. Declare units where you have them. With units declared, the unit-typed rung constrains GENERATION rather
   than merely checking the result, which is a materially different thing: it removes dimensionally impossible
   candidates from the search space instead of rejecting them after they were built.
4. If a published closed form exists for your quantity, wire it as a machine-comparable expression so recovery
   becomes scoreable, and state the regime. A synthetic case does it through the generator's `truth_node` in
   `cases/generators.py`; a measured dataset does it through `MEASURED_TRUTHS` in `cases/physics_truths.py`,
   keyed by loader and bound to input columns by NAME so a change in source column order cannot rebind it.
   Without one the case still runs and still reports error metrics; its recovery is reported as not checkable
   rather than as zero, with the reason recorded.
5. The pipeline produces a compact artifact and manifest you can replay in the SPA exactly like the built-in
   cases. The Live tab will not run your dataset: it regenerates data in the browser from a registered
   generator, so it applies to synthetic cases only.

If your data legitimately doesn't fit, extend CONTRACT 1 (and its tests) **deliberately**, never loosen it just
to make bad data pass.
