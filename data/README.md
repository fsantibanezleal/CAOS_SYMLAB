# data/

## Layout

| Path | What | Git |
|---|---|---|
| `raw/` | source files as downloaded, some hundreds of megabytes | **git-ignored**, staged by `scripts/fetch_data.py` into a vault outside the repository |
| `examples/` | one tiny dataset in the standard format, which passes CONTRACT 1 | committed |
| `derived/<case>/run.json` | the artifact the web replays, one per case | committed |
| `demo/`, `samples/`, `artifacts/` | empty scaffolds, kept for the layout the archetype defines | committed (`.gitkeep` only) |

The per-case manifests are NOT under `data/`. They are in `manifests/` at the repository root, next
to the pipeline that writes them, with the flat inventory in `manifests/index.json`.

## CONTRACT 1, ingestion, the bring-your-own-data gate

Enforced in `data-pipeline/symlab/stages/preprocess.py :: _contract_check`, and it runs on every
dataset before any search does. There is no separate contract module: an earlier `io/contract.py`
declared a different contract, was imported by nothing, and has been deleted.

The standard format is a table of numbers: **one numeric column per input, one numeric target
column**, with a unit per column wherever you know it. Units are declared in the case registry rather
than in the file, because a header cannot carry a dimension vector.

**Refused outright**, with every reason named at once rather than the first one hit:

| Condition | Why |
|---|---|
| fewer than 20 rows | too few for a train/test split |
| any non-finite value in an input | a search cannot evaluate against it |
| any non-finite value in the target | the same, and it silently poisons every error metric |
| zero variance in the target | there is nothing to model |

**Warned and recorded**, rather than refused, because each can be legitimate and the reader has to
be told either way:

| Condition | Why it matters |
|---|---|
| a constant input column | it cannot contribute, and it inflates any count of irrelevant features carried into the result |
| the target takes few distinct values relative to its row count (more than 3 repeats each) | the signature of a coarser measurement grid broadcast across finer rows, which leaks the target. The flotation dataset carries exactly this defect, and the check is written generically so the next dataset with it is caught before it produces a leaked number |

Those warnings travel into the manifest AND into the web payload, so the reader who most needs them
can see them next to the number they qualify.

Anything a loader had to do to make a dataset usable (rows dropped, folds ignored, aggregation
applied, deterministic subsampling) is recorded as a defect and published in the artifact rather than
tidied away.

`examples/monod.csv` is a dataset in this format: 40 rows of the Monod saturation law,
`mu = mu_max * S / (Ks + S)` at `mu_max = 0.62` per hour and `Ks = 12.5` mg/L. It is deterministic,
so it is stable under regeneration, and it passes CONTRACT 1.

## CONTRACT 2, artifact, pipeline to web

Each case writes `derived/<case>/run.json`, frozen at `schema_version 1.0.0` in
`data-pipeline/symlab/core/contract.py` and mirrored in `frontend/src/lib/contract.types.ts`, so
drift between producer and consumer fails the build rather than blanking a panel at runtime. The
audit record is `manifests/<case>.json`, schema `symlab.manifest/v1`, carrying the sources, the
licences, the contract warnings, the lane verdict from the gate, the measured costs and the defects
applied on the way in. The inventory is `manifests/index.json`, schema `symlab.index/v1`.

The web loads ONLY these committed artifacts and never recomputes them. The one exception is the live
lane, which runs the same engine modules in the browser through Pyodide on data it generates there,
and which is available only for cases that have a first-principles generator, since a file-loaded
case's source is not shipped. See [the gate](../docs/architecture/03_the-gate.md).

## Provenance and licences

Every source is declared in `data-pipeline/symlab/io/sources.py` with its citation, its licence and
its redistribution terms, and each of those travels into the artifact. Public derived artifacts are
committed; raw sources stay in the vault outside the repository. Per-case provenance is in
[`docs/cases/`](../docs/cases/) and in the Context tab of each case in the app.
