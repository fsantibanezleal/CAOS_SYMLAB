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

## Template residue, removed
Instantiation replaced the example lab but left six modules from it in the tree, all describing an SIR
epidemic example, none imported by `pipeline.py`, the stages, the search or the frontend. The only imports
among them were internal to the group, which is how they survived: `core/manifest.py` read `core/trace.py`,
which read `io/schema.py`, and `io/contract.py` read `io/schema.py` as well. Each carried a docstring
asserting a role it did not have, `core/rng.py` claiming to be "the single RNG factory ... always thread one
made here" while nothing threaded one.

Five are deleted (`core/trace.py`, `core/manifest.py`, `core/rng.py`, `io/contract.py`, `io/schema.py`), along
with four tracked directories containing nothing but `.gitkeep` that shadowed the real package layout
(`data-pipeline/{cases,config,src,stages}/`). The sixth, `core/gate.py`, was rewritten around the criterion
that actually applies here and wired into the manifest: see [the gate](03_the-gate.md).

Everything under `symlab/` now runs. The pages that follow describe it.
