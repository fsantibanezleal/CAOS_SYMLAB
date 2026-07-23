# The live-vs-precompute gate

The app offers two ways to see a search. **Replay** renders a committed artifact, and every case can be
replayed. **Live** runs the engine in the reader's browser through Pyodide and shows the result of a search
that has never been run before, and not every case can do that. The gate decides which, per case, and records
the verdict with its reasons in the manifest.

`data-pipeline/symlab/core/gate.py :: classify_lane()` is called from `stages/export.py :: build_manifest`, so
`manifest["gate"]` and `manifest["lane"]` are written from the same call and cannot disagree.

## What actually decides it

One thing, and it is narrower than it looks:

> **The browser must be able to produce the data.** The live lane ships the `symlab` modules and regenerates
> the inputs in-process from a first-principles generator. A case loaded from a file cannot run live, because
> the file is not shipped.

That last clause is a size decision with a measurement behind it: the flotation source alone is 737,453 rows,
and publishing the raw sources beside the app to enable an in-browser re-fit would multiply the download by
orders of magnitude for a feature nobody asked for. So a case runs live if and only if it has a generator: 16
of the 25 registry entries do, and the measured-data cases do not.

The wheel set is recorded alongside (`LIVE_WHEELS = {"numpy"}`) because it is a real constraint on what the
engine may ever depend on. No case has come close to violating it: the engine is pure Python plus numpy, with
no compiled extension and no model weights, which is exactly what lets the same modules run in the browser.

## What the gate deliberately does NOT measure

There is no runtime budget, and its absence is a decision rather than an omission. The live lane runs a
**reduced** configuration on purpose (240 rows, a small population, few generations) so that it returns inside
an interaction budget. Gating cases on the wall-clock of the full offline bake would therefore have measured
the wrong search, and would have excluded cases that run live perfectly well.

## What this page used to say

An earlier version of this module scored `pure_python`, the wheel set, a 1500 ms `RUN_MS_GATE` and a 256 KiB
`TRACE_BYTES_GATE`, and its docstring declared that the verdict "goes into the manifest, and CI fails on
mislabeling. This is a MEASUREMENT, never a hand-wave."

None of that was true. `classify_lane` had no caller anywhere in the repository, `build_manifest` wrote
`"lane": "precompute"` as a literal for every case, and the assertion in `scripts/check_artifacts.py` reads
`m.get("gate", {}).get("lane") not in (None, m.get("lane"))`, so with no `gate` key on any manifest it passed
vacuously on all 39 artifacts. Its numbers were wrong for this product too: numpy is the only wheel and every
lane uses it, and the smallest committed artifact is several times the 256 KiB budget it would have failed
everything against.

Both halves exist now. The gate decides from the one criterion that applies here, and the CI check has
something to compare.

Independently of the gate, a committed artifact always exists for every case, so the site replays instantly on
first paint (ADR-0054). See the [live lane](04_live-lane-pyodide.md) for what the browser actually runs.
