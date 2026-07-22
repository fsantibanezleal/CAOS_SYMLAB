# Architecture, overview

This product is an instance of the **CAOS product-repo archetype** (ADR-0057): offline-pipeline-heavy,
backend-optional, deploying as a static deterministic-replay viewer. The base is **frozen** (instantiated, never
re-litigated); per-product rework lives only in the **core**, models/algorithms, visualization, content.

## The lanes (and what runs where)
| Lane | Where | Deps | Notes |
|---|---|---|---|
| **Offline (precompute)** | `data-pipeline/symlab/`, `.venv` | `requirements-precompute.txt` (`data-pipeline/requirements.txt` is a one-line pointer at it) | bakes the committed artifacts |
| **Live (client-side)** | `frontend/src/live/search.worker.ts` + the copy of `symlab/{model,search,cases}` staged into `frontend/public/engine/` | `requirements.txt` (numpy only, Pyodide-safe) | optional recompute in the browser at a reduced budget |
| **Replay** | `frontend/` | n/a | always present; the fallback (ADR-0054) |
| **API (backend)** | `app/` (FastAPI) | `requirements-api.txt` | DORMANT; activate only on an ADR-0002 trigger |

The [gate](03_the-gate.md) module exists and states the live-vs-replay criteria, but nothing in this pipeline
calls it: every case is baked offline and every manifest records `lane: "precompute"`. That page says so
explicitly rather than describing a decision the code does not take.

## The flow
`data/raw` to **[CONTRACT 1](08_data-contracts.md)** (`stages/preprocess.py :: _contract_check`) to the staged
pipeline (preprocess to feature_extraction to train to infer to evaluate to export) to
**[CONTRACT 2](08_data-contracts.md)** (`core/contract.py` for the payload shape, `stages/export.py` for the
writing) to `data/derived/<case>/run.json` plus `manifests/<case>.json` (both committed) to `frontend/`, which
replays them.

## Frozen base vs rework
- **Frozen:** the folder layout, the two contracts, the staged pipeline names, the manifest/index, the two-venv
  split, the cases-by-category mechanism, CI guards. Any area may be **dormant** (with a README).
- **Rework (the only per-product surface):** the engine in `search/` + `model/` and the stage bodies (the
  science), the `frontend/` visualizations, and the cases + content + calibration.

## Template residue still on disk
Instantiation replaced the example lab but left six modules from it in the tree, and they are dead code rather
than product: `core/trace.py`, `core/manifest.py`, `core/gate.py`, `core/rng.py`, `io/contract.py` and
`io/schema.py` all describe an SIR epidemic example. Nothing in `pipeline.py`, the stages, the search or the
frontend imports any of them; the only imports among them are internal to the group (`core/manifest.py` reads
`core/trace.py`, which reads `io/schema.py`, and `io/contract.py` reads `io/schema.py`). They are named here so
a reader who opens one does not mistake it for the pipeline; the pages that follow describe the modules that
actually run.
