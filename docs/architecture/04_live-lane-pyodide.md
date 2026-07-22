# The live (Pyodide) lane

Optional client-side recompute: `frontend/src/live/search.worker.ts` loads Pyodide 0.28.3 from jsDelivr as a
module worker, loads the `numpy` wheel, fetches the engine source served under `/engine/`, writes it into the
Pyodide filesystem and runs a real search there. The worker uses a dynamic ESM `import()` rather than
`importScripts`, which a module worker does not support.

The served engine is produced by `frontend/copy-data.mjs`, which copies 18 named modules from
`data-pipeline/symlab/` into `frontend/public/engine/` (`model/`, `search/`, `cases/generators.py`, and the two
package `__init__.py` files) and throws if any of them is missing, so the build fails rather than shipping a
lane whose every module fetch would 404. The offline-only stages, the `io` layer and `pipeline.py` are
deliberately not copied. The copier also writes `engine/modules.json` listing exactly what it staged, and the
worker fetches that list rather than keeping a second hand-maintained copy: the two lists disagreeing is what
once served `sparse.py` with HTTP 200 while the browser still raised `ModuleNotFoundError`.

What the worker actually runs, from `symlab.cases.generators`, `symlab.search.engine` and
`symlab.search.sparse`:

```
X, y = make_dataset(generator, n_rows=240, seed=<seed>)
config = replace(LADDER["r4-multi-objective"], population=<n>, generations=<n>,
                 primitive_set=generator.suggested_primitives)
result = SparseRegressionSearch(config).run(...) if family == "sparse" else Engine(config).run(...)
```

Key points:

- The live engine is the SAME code the offline bake runs, not a JavaScript reimplementation. Two engines that
  must agree forever is the defect this avoids.
- It is **not** the same run. The rung is fixed at `r4-multi-objective`, the row count is 240 and the budget is
  whatever the reader sets, so the expression it returns is expected to be simpler than the Expression tab's,
  and its numbers are not comparable to the baked ones.
- It is **not** the same data for a measured case. The worker resolves the case id against `GENERATORS` and
  falls back to `monod-saturation` when there is no match, so opening the Live tab on `ccpp-derating` or any
  Feynman case silently searches the Monod generator instead. 16 of the 25 registry cases have a generator of
  the same id; the other 9 do not. That fallback is a defect in `search.worker.ts`, recorded here rather than
  glossed.
- Nothing starts automatically. Loading a Python runtime and running an evolutionary search on page view would
  spend a reader's battery on a result they did not ask for.
- **Replay is always the fallback** (ADR-0054): the lane can be dormant and the product stays fully functional.

`frontend/src/pyodide/` is an empty directory and `frontend/public/pyodide/sources.json` is untracked template
residue (it inlines the archetype's example-lab sources, not this package); neither is referenced by any code
in this repo. The served engine is `public/engine/`, described above.
