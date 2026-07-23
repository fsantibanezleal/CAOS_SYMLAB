# The two data contracts

A product is only real if data flows through two **enforced** contracts. Both are CI-checked.

## CONTRACT 1, ingestion (`raw to pipeline`), the *bring-your-own-data* gate
`data-pipeline/symlab/stages/preprocess.py :: _contract_check`. It runs on every dataset before any search
sees it, and it separates FATAL problems from WARNINGS rather than treating every complaint the same way.

Fatal, and the dataset is refused with a `ValueError` naming every reason at once:

- fewer than 20 rows, which is too few for a train/test split
- any non-finite value in the inputs or in the target
- a target with zero variance, because there is nothing to model

Warned, recorded, and carried into both the manifest and the web payload, but not fatal:

- a constant input column, which cannot contribute and inflates any count of irrelevant features
- a target taking so few distinct values relative to its row count (more than 3 repeats each) that fitting at
  that resolution may leak it. This is the broadcast trap the flotation dataset carries; on the committed
  `flotation-silica` artifact the check reports 709 distinct values across 4000 rows.

The report also carries the row and input counts, the input keys, the target key, the distinct-target count and
repeat ratio, the licence, the redistribution verdict and the citation. Recorded defects travel with the
dataset (rows dropped, folds ignored, aggregation applied, deterministic subsampling, Git LFS pointers
rejected) and are published in the artifact rather than tidied away. Full table:
[`data/README.md`](../../data/README.md).

Note that a file named `data-pipeline/symlab/io/contract.py` used to sit beside this one and was NOT this
contract: it declared an SIR parameter table with a reject/clip/flag row policy and nothing imported it. It has
been deleted, so the enforcement described above is the only one in the tree as well as the only one that runs.

## CONTRACT 2, artifact (`pipeline to web`)
`data-pipeline/symlab/core/contract.py` declares the payload (frozen at `SCHEMA_VERSION = "1.0.0"`) and
`stages/export.py` writes it. Two files per case:

- `data/derived/<case>/run.json`, the document the app renders: the dataset descriptor with full row
  accounting, every variant with its config, Pareto members, history, validation arrays and score, the truth it
  was scored against, the contract warnings, the defects applied and the certificate where one was computed.
- `manifests/<case>.json` (`symlab.manifest/v1`), the audit record: case id, category, engine package and
  version, seed, the artifact path/format/schema/byte size, the source's citation, licence, redistribution
  verdict and defects, the full CONTRACT 1 report, the split note, and per-variant seconds, evaluations, front
  size, selected complexity, test R2, accuracy verdict, recovery verdict and irrelevant-feature count.

`manifests/index.json` (`symlab.index/v1`) inventories every baked case with the coverage summary. Both trees
are copied into `frontend/public/data/` by `copy-data.mjs`.

The manifest's `lane` is the literal `"precompute"` on every case and no manifest carries a `gate` field; see
[the gate](03_the-gate.md) for why. Wall-clock timestamps are deliberately absent from the manifest itself, so
a re-bake does not dirty git through the audit record; the measured per-variant `seconds` are recorded because
what a rung costs is part of its evaluation.

**Enforcement:** `frontend/src/lib/contract.types.ts` mirrors this schema and a drift fails `tsc --noEmit`, so
the build stops rather than a panel going blank at runtime; `assertSchemaSupported` refuses a payload whose
major version does not match. `scripts/check_artifacts.py` (run in CI and by `scripts/smoke.{sh,ps1}`) verifies
that every indexed case has a manifest and an artifact, that the artifact is non-empty and its byte size
matches the manifest, and that the index COVERS the derived tree in both directions, so a truncated index
cannot read as full coverage. It also compares `manifest.lane` against `manifest.gate.lane`, which passes
vacuously today because no manifest has a `gate` key. The web loads **only** these artifacts; it never
recomputes, except the optional live lane, which computes its own data in the browser and reports separately.

## Why this matters
Without Contract 1 the app can't be applied to new data (it's a demo). Without Contract 2 the web can silently
drift from what the pipeline produced. The contracts are the seam that makes the product a tool, not a
slideshow.
