# Deploy

Default = **GitHub Pages, static** (ADR-0055): `.github/workflows/deploy-pages.yml` runs on a push to `main`,
verifies the committed artifacts with `scripts/check_artifacts.py`, builds the SPA (`npm run build`, whose
`prebuild` step runs `copy-data.mjs` to stage `data/derived` and `manifests` into `frontend/public/data/`),
copies `dist/index.html` to `dist/404.html` so deep links survive static hosting, and deploys `frontend/dist`.
No backend at request time. See [`deploy/pages.md`](../../deploy/pages.md), which still describes step 1 as
regenerating the artifacts with `python -m symlab.pipeline all`; that step was removed from the workflow and
this page is the current description.

The artifacts are **not** regenerated in the deploy job. A full bake at published budgets is a multi-hour run
on this case matrix, and a timeout there would silently ship a partial index; the job verifies internal
consistency instead, which is the property a replay viewer actually depends on.

The VPS path (systemd + nginx, in `deploy/`) is **dormant**, activated only when `app/` is (an ADR-0002
trigger). `ci.yml` keeps the base honest on every push and pull request, in three jobs:

- **test**: ruff over `data-pipeline` and `tests`, pytest, a pipeline smoke that regenerates `monod-saturation`,
  then `check_artifacts.py` (CONTRACT 2).
- **guards**: fails on a tracked `.env`, a tracked venv or native/heavy binary (`.dll`, `.so`, `.dylib`, `.pt`,
  `.pth`), tracked raw/heavy data (`.parquet`, `.h5`, `.hdf5`, `.nc`, `.mat`, `.npy`) or a leaked local machine
  path, then runs `check_template_residue.py` and `check_content_standards.py` (ADR-0067, no em-dash, no emoji).
- **frontend**: `npm ci`, `copy-data.mjs`, `npm run build` (`tsc --noEmit` then vite) on Node 20, the same major
  the Pages deploy uses. This job exists because the frontend was once built only by the deploy workflow, so a
  TypeScript error passed CI on the pull request and failed after the merge.
