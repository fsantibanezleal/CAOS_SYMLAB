# The live-vs-precompute gate

`data-pipeline/symlab/core/gate.py :: classify_lane()`. A case runs **live** in the browser (Pyodide) iff , 
by MEASUREMENT, never by hand-wave:

- it is **pure-Python**, AND
- its wheels are a subset of the Pyodide-safe set (`LIVE_WHEELS`, e.g. `{numpy}`), AND
- `run_ms ≤ RUN_MS_GATE` (interaction budget), AND
- `trace_bytes ≤ TRACE_BYTES_GATE` (small artifact).

Otherwise the case is **precompute**: the offline pipeline bakes the artifact and the SPA replays it. Either way,
a committed artifact always exists, so the site replays instantly on first paint (ADR-0054).

The verdict + the measured numbers are written into the manifest (`gate` field) and CI fails if `manifest.lane`
disagrees with the gate, so a heavy model can never be mislabeled "live". Every SymLab case is classified `live`: the engine is pure Python plus numpy, with no compiled extension and
no model weights, which is exactly what lets the same modules run in the browser through Pyodide at a reduced
budget. The gate is still enforced rather than assumed, because a future rung that reached for a compiled
solver would have to be reclassified rather than silently shipped as live.
