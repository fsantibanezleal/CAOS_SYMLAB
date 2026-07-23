# tools/

Verification harnesses. Everything here checks a claim the build cannot check for itself, which is
why each one lives in this repository rather than on the machine that happened to run it: a claim a
reader cannot re-run is a claim they have to take on trust.

| Harness | Asserts |
|---|---|
| `verify/live-parity-check.mjs` | The browser lane and the offline lane return the SAME expression for the same case, seed and budget. Drives both and compares. |
| `verify/live-parity-offline.py` | The offline half of that comparison, callable on its own. |
| `visual-verify/workbench.mjs` | The App renders: six tabs in both themes, both provenance labels present, dropdowns populated, no horizontal overflow, no console error, no unstyled class rendering as raw text, no panel empty where the artifact says it has content. |
| `visual-verify/verify.mjs` | Every route loads in both themes with no page error, and the panels a reader came for are in the DOM rather than merely reserved by CSS. |
| `visual-verify/pages.mjs` | The published pages, checked against the same standards as the App. |

All of them need a served build:

```bash
cd frontend && npm run build && npx vite preview --port 4183
```

then, from the repository root:

```bash
SYMLAB_BASE=http://localhost:4183 node tools/visual-verify/workbench.mjs
SYMLAB_BASE=http://localhost:4183 node tools/verify/live-parity-check.mjs
```

Screenshots go to a scratch directory outside the repository (`SYMLAB_SHOTS`, defaulting to the
system temp directory), so a verification run can never leave images in a commit.

Playwright needs a browser once: `npx playwright install chromium`.
