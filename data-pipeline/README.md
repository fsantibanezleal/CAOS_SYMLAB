# data-pipeline/, the offline engine (`symlab`)

The **single source of algorithm truth**. `frontend/` and `app/` consume what this produces and never
re-implement it. Installed into the repository's single venv, `.venv`, from
`requirements-precompute.txt`; there is no separate heavy-engine venv, because the search is
hand-written numpy so the same modules can run in the browser.

## Layout

The package lives directly under `data-pipeline/`.

| Path | What |
|---|---|
| `symlab/pipeline.py` | orchestrator and CLI: `python -m symlab.pipeline [all\|<case>] [--seed N] [--expand] [--quick] [--noise F] [--list]`. `all` needs `--expand`, or it fails on the two benchmark suites. |
| `symlab/cases/` | `registry.py` (the cases, grouped by category), `generators.py` (18 first-principles generators), `physics_truths.py` (the machine-comparable laws) |
| `symlab/io/` | `sources.py` (provenance, licences, recorded defects), `loaders.py` (one loader per source, including everything a source lies about) |
| `symlab/core/` | `contract.py` (**CONTRACT 2**, the frozen artifact schema), `gate.py` (the live-vs-replay verdict) |
| `symlab/model/` | the shared pure-Python core, Pyodide-safe: `expr.py`, `complexity.py`, `latex.py`, `scaling.py`, `intervals.py`, `units.py` |
| `symlab/search/` | `engine.py` (the GP ladder), `sparse.py` (the non-evolutionary arm), `exhaustive.py` (bounded enumeration), plus `generate.py`, `select.py`, `tune.py`, `variation.py` |
| `symlab/stages/` | the pipeline in order: `preprocess`, `feature_extraction`, `train`, `infer`, `evaluate`, `export` |

**CONTRACT 1**, the ingestion gate, is not a module of its own. It is `stages/preprocess.py ::
_contract_check`, and it runs on every dataset before any search does. See
[`../data/README.md`](../data/README.md).

Setup and run: `scripts/setup.{sh,ps1}` then `scripts/precompute.{sh,ps1} all --expand`. See
[../docs/architecture/05_precompute-pipeline.md](../docs/architecture/05_precompute-pipeline.md).
