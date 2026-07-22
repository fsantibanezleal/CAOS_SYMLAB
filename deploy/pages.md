# Deploy, GitHub Pages (default, static deterministic-replay)

The default deploy for this archetype (ADR-0055 Pages-first): the SPA and the committed artifacts are
served statically, and there is **no backend** at request time. What the browser can compute live, it
computes in the browser through Pyodide; everything else is a replay of a committed artifact.

What `.github/workflows/deploy-pages.yml` actually does:

1. **verifies** the committed artifacts against their manifests (`python scripts/check_artifacts.py`):
   every declared byte count matches disk, no artifact is empty, the lane matches the gate verdict, and
   nothing on disk is missing from the index;
2. builds the frontend (`cd frontend && npm ci && npm run build`, where `copy-data.mjs` overlays
   `data/derived` and the engine modules into `public/`);
3. copies `index.html` to `404.html`, so a deep link or a refresh does not 404 on static hosting;
4. uploads `frontend/dist` and deploys to Pages.

Step 1 is a verification, not a bake. This file used to claim the workflow "regenerates the artifacts
deterministically (`python -m symlab.pipeline all`) so the site replays fresh, audited outputs", which was
wrong twice over. The workflow has never run the pipeline; and it should not, because a full bake at
published budgets is a multi-hour run on this case matrix, so a job timeout would silently ship a partial
index. The artifacts are committed and reviewed, and what CI checks is that what is committed is
internally consistent, which is the property a replay viewer actually depends on. (`pipeline all` would
also have failed as written: the two benchmark suites need `--expand`.)

Enable once per product: repo **Settings, Pages, Source = GitHub Actions**. Custom domain: set it with
`gh api PUT repos/<owner>/<repo>/pages -f cname=<sub>.fasl-work.com`, because the CNAME file alone does not
set the domain on Actions deploys.

The VPS path (the systemd and nginx templates in this directory) stays **dormant** unless the `app/`
backend is activated (ADR-0002).
