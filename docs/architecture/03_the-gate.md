# The live-vs-precompute gate

`data-pipeline/symlab/core/gate.py :: classify_lane()` states the criteria under which a case could run **live**
in the browser (Pyodide), by MEASUREMENT rather than by hand-wave:

- it is **pure-Python**, AND
- its wheels are a subset of the Pyodide-safe set (`LIVE_WHEELS = {"numpy"}`), AND
- `run_ms <= RUN_MS_GATE` (1500 ms, an interaction budget), AND
- `trace_bytes <= TRACE_BYTES_GATE` (256 KiB, a small artifact).

**Nothing in this repo calls it.** `classify_lane` has no caller in the pipeline, the stages, the tests or the
frontend, and `stages/export.py :: build_manifest` writes `"lane": "precompute"` as a literal. All 39 committed
manifests therefore record `precompute`, and none carries the `gate` field the module returns. The gate is a
stated criterion here, not an enforced one.

That has a consequence worth naming, because a previous version of this page claimed the opposite. Every case
is baked offline and replayed; the [live lane](04_live-lane-pyodide.md) is an extra tab a reader starts by
hand, not a per-case verdict. `scripts/check_artifacts.py` does contain a lane-versus-gate assertion, but it is
written as `m.get("gate", {}).get("lane") not in (None, m.get("lane"))`, so with no `gate` key on any manifest
the check passes vacuously on every case. It would catch a future disagreement; today it catches nothing.

What is true regardless: a committed artifact always exists for every case, so the site replays instantly on
first paint (ADR-0054). The engine is pure Python plus numpy, with no compiled extension and no model weights,
which is what lets the same modules run in the browser through Pyodide at a reduced budget. Wiring the gate to
the manifest, so that a future rung reaching for a compiled solver has to be reclassified rather than silently
shipped, is open work rather than shipped behaviour.
