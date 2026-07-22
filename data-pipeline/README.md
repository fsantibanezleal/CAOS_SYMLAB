# data-pipeline/, the offline engine (`symlab`)

Rename `symlab` → `<slug>lab` per product. The **single source of physics/algorithm truth**; `frontend/` and
`app/` consume it, never re-implement it. Installed into the repository's single venv, `.venv`, from `requirements-precompute.txt`. There is no separate heavy-engine venv: the search is hand-written numpy so the same modules run in the browser.

## Layout (the package lives directly under `data-pipeline/`)
- `symlab/pipeline.py`, orchestrator + CLI (`python -m symlab.pipeline [all|<case>] [--seed N]`)
- `symlab/registry.py`, cases grouped by CATEGORY · `symlab/live.py`, Pyodide live entrypoint
- `symlab/io/`, `contract.py` (**CONTRACT 1**) · `formats.py` (standard readers/writers) · `schema.py` (types)
- `symlab/core/`, `rng.py` (seeded determinism) · `trace.py` · `manifest.py` (**CONTRACT 2**) · `gate.py`
- `symlab/model/`, the shared pure-Python core (Pyodide-safe); EXAMPLE = SIR
- `symlab/stages/`, `preprocess → feature_extraction → train → infer → evaluate → export`
- `symlab/cases/`, documented cases

Setup + run: `scripts/setup.{sh,ps1}` then `scripts/precompute.{sh,ps1}`. See
[../docs/architecture/05_precompute-pipeline.md](../docs/architecture/05_precompute-pipeline.md).
