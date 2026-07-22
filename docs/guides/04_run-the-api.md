# Guide, run the API (only if `app/` is activated)

The `app/` FastAPI backend is **DORMANT** by default, most products are static deterministic-replay and never
need it. Activate ONLY on an ADR-0002 trigger (server-side processing of uploaded data, auth-gated private data,
paid heavy compute).

To activate:
1. Pin deps in `requirements-api.txt` (`fastapi`, `uvicorn[standard]`, …) and install into `.venv`.
2. `uvicorn app.main:app --reload` (or `scripts/dev.{sh,ps1}` auto-starts it when `app/` is active).
3. Endpoints (`GET /api/cases`, `/api/cases/{id}/manifest`, `/api/cases/{id}/trace`, `/health`) serve the SAME
   committed `data/derived` artifacts read-only, a thin layer over `data/`, never a re-implementation of the
   engine. Deploy via the dormant VPS configuration in `deploy/`. SymLab itself ships as a static replay and does not run
this API in production; the deploy decision and its trigger conditions are recorded in the deployment doc.

Keep the data-pipeline + contract discipline even with a backend: the API serves what the pipeline baked.
