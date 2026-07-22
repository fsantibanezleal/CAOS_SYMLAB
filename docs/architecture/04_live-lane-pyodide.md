# The live (Pyodide) lane

Optional client-side recompute, like SimLab: load Pyodide in a web worker, load the inlined engine sources
(`frontend/public/pyodide/sources.json`, produced by `copy-data.mjs`), and call
`symlab.live.run_trace_json(case_id|params, seed)`, which uses ONLY `symlab/model/` (pure-Python,
Pyodide-safe), so the live engine shares the offline code path.

Key points:
- The live engine **may be a reduced/surrogate model**, not the full offline SOTA one, that's expected.
- Eligibility is decided by the [gate](03_the-gate.md); a case the gate marks `precompute` is replayed from the
  committed artifact instead.
- **Replay is always the fallback** (ADR-0054): a product can ship with this lane dormant and still be fully
  functional. In SymLab the lane is wired and live: `frontend/src/live/search.worker.ts` loads Pyodide as a module worker and
imports the same engine modules the offline pipeline runs, copied into `public/engine/` at build time by
`copy-data.mjs`, which fails the build if one of them is missing. The worker uses a dynamic ESM import rather
than `importScripts`, which a module worker does not support.
