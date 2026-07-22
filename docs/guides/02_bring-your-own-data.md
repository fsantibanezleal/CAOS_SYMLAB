# Guide, bring your own data

The product is **applicable to NEW data**, not just the baked cases, that is what makes it a tool. The door is
**CONTRACT 1** (`data-pipeline/symlab/io/contract.py`).

1. Put your data in the documented standard format (see [`data/README.md`](../../data/README.md)): one numeric
   column per input, one target column, and a unit per column where you know it. Drop the file under `data/raw/`
   (git-ignored).
2. Register it as a case in `data-pipeline/symlab/cases/registry.py` and give it a loader in
   `data-pipeline/symlab/io/loaders.py`, then run `scripts/precompute.{sh,ps1}`. CONTRACT 1 validates the
   dataset before any search runs and **refuses** it with a reason rather than coercing it:
   - non-finite values in inputs or target
   - a constant input column, which cannot carry information and would waste the whole budget
   - a target taking so few distinct values relative to its row count that fitting at that resolution leaks it
   Anything the loader had to do to make the data usable (rows dropped, folds ignored, aggregation applied) is
   recorded as a defect and published in the artifact, not tidied away.
3. Declare units where you have them. With units declared, the unit-typed rung constrains GENERATION rather than
   merely checking the result, which is a materially different thing: it removes dimensionally impossible
   candidates from the search space instead of rejecting them after they were built.
4. If a published closed form exists for your quantity, attach it as a `truth_node` so recovery becomes
   scoreable, and state the regime. Without one the case still runs and still reports error metrics; its
   recovery is reported as not checkable rather than as zero.
5. The pipeline produces a compact artifact and manifest you can replay in the SPA exactly like the built-in
   cases, and the live lane runs the same engine on it in the browser at a reduced budget.

If your data legitimately doesn't fit, extend CONTRACT 1 (and its tests) **deliberately**, never loosen it just
to make bad data pass.
