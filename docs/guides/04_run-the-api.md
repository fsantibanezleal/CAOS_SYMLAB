# Guide, run the API (only if `app/` is activated)

The `app/` FastAPI backend is **DORMANT** by default, most products are static deterministic-replay and never
need it. `requirements-api.txt` ships fully commented out, which is what `scripts/dev.{sh,ps1}` reads to decide
whether the lane is on. Activate ONLY on an ADR-0002 trigger (server-side processing of uploaded data,
auth-gated private data, paid heavy compute).

To activate:
1. Pin deps in `requirements-api.txt` (`fastapi`, `uvicorn[standard]`, …) and install into `.venv`.
2. `uvicorn app.main:app --reload` (or `scripts/dev.{sh,ps1}`, which starts uvicorn on port 8000 in the
   background once `requirements-api.txt` has an uncommented line and `app/main.py` exists).
3. The routes are `GET /api/cases` (the index), `GET /api/cases/{id}/manifest`, `GET /api/cases/{id}/trace`
   and `GET /health` (aliased `/healthz`). All are read-only, GET-only, CORS restricted to GET, and they serve
   the SAME committed `data/derived` and `manifests` files the static site reads. `/trace` returns the case's
   `run.json` (the route name predates the rename of the artifact) and 404s when the case id is unknown or the
   artifact is missing. This is a thin layer over `data/`, never a re-implementation of the engine. Deploy via
   the dormant VPS configuration in `deploy/`.

SymLab itself ships as a static replay on GitHub Pages and does not run this API in production; the deploy
decision is [architecture/07](../architecture/07_deploy.md) and the ADR-0002 trigger conditions are the ones
listed above.

Keep the data-pipeline + contract discipline even with a backend: the API serves what the pipeline baked.
