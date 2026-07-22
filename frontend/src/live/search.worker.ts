/**
 * The live search worker: the offline Python engine, loaded into the browser under Pyodide.
 *
 * Runs off the main thread so a search that takes seconds never freezes the page. The engine source
 * is fetched from the served copy of the package, so the browser executes the same modules the bake
 * executed rather than a parallel implementation that would have to be kept in agreement forever.
 *
 * Two things were wrong in the first version, and are recorded so they are not reintroduced:
 *
 * 1. **A module worker cannot use `importScripts`.** That function exists only in classic workers;
 *    calling it in a module worker throws "Module scripts don't support importScripts()". Pyodide
 *    ships an ESM build (`pyodide.mjs`) for exactly this case, so the runtime is brought in with a
 *    dynamic `import()` instead.
 * 2. **The engine source has to be SERVED.** Fetching `symlab/model/expr.py` from the site only
 *    works because the build copies those files into `public/engine/`. Without that step every
 *    module fetch 404s after the runtime finishes loading, which reads as a Pyodide failure and is
 *    not one.
 */
const PYODIDE_VERSION = '0.28.3';
const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

interface PyodideInterface {
  loadPackage(names: string[]): Promise<void>;
  runPythonAsync(code: string): Promise<unknown>;
  FS: { mkdirTree(path: string): void; writeFile(path: string, data: string): void };
}

/** The package modules the live lane needs. The offline-only stages are deliberately absent. */
/**
 * The engine modules are NOT listed here.
 *
 * They used to be, in a hand-maintained array that had to agree with the one in `copy-data.mjs`.
 * Adding the non-evolutionary arm to the copier and not to this file produced a browser that
 * served `sparse.py` with HTTP 200 and still raised
 * `ModuleNotFoundError: No module named 'symlab.search.sparse'`, because nothing fetched it into
 * the Pyodide filesystem. Two lists that must agree eventually will not.
 *
 * The copier writes `engine/modules.json` describing what it actually put on disk, and this worker
 * loads exactly that. The build step is the only party that knows what exists, so it is the one
 * that gets to say.
 */
async function engineModules(base: string): Promise<string[]> {
  const response = await fetch(`${base}modules.json`);
  if (!response.ok) {
    throw new Error(
      `engine manifest returned ${response.status}. Run copy-data.mjs: the build did not stage the ` +
        'package source into public/engine/.',
    );
  }
  const parsed = (await response.json()) as { modules?: unknown };
  if (!Array.isArray(parsed.modules) || parsed.modules.length === 0) {
    throw new Error('engine manifest is empty or malformed');
  }
  return parsed.modules as string[];
}

let pyodide: PyodideInterface | null = null;

async function boot(post: (message: unknown) => void): Promise<PyodideInterface> {
  if (pyodide) return pyodide;

  post({ kind: 'status', text: 'loading the Python runtime, about 10 MB, once per session' });
  // Dynamic ESM import, NOT importScripts: this is a module worker.
  const pyodideModule = await import(/* @vite-ignore */ `${PYODIDE_INDEX_URL}pyodide.mjs`);
  const runtime: PyodideInterface = await pyodideModule.loadPyodide({ indexURL: PYODIDE_INDEX_URL });

  post({ kind: 'status', text: 'loading numpy' });
  await runtime.loadPackage(['numpy']);

  post({ kind: 'status', text: 'loading the engine source' });
  const base = `${self.location.origin}/engine/`;
  for (const module of await engineModules(base)) {
    const response = await fetch(`${base}${module}`);
    if (!response.ok) {
      throw new Error(
        `engine module ${module} returned ${response.status}. The build did not copy the package ` +
          'source into public/engine/.',
      );
    }
    const source = await response.text();
    const directory = `/engine/${module.split('/').slice(0, -1).join('/')}`;
    runtime.FS.mkdirTree(directory);
    runtime.FS.writeFile(`/engine/${module}`, source);
  }

  await runtime.runPythonAsync('import sys; sys.path.insert(0, "/engine")');
  pyodide = runtime;
  return runtime;
}

self.onmessage = async (event: MessageEvent) => {
  const post = (message: unknown) => (self as unknown as Worker).postMessage(message);
  const { generatorId, population, generations, seed, method = 'gp' } = event.data as {
    generatorId: string;
    population: number;
    generations: number;
    seed: number;
    /** Which search family to run. "gp" is the ladder engine; "sparse" the non-evolutionary arm. */
    method?: 'gp' | 'sparse';
  };

  try {
    const runtime = await boot(post);
    post({ kind: 'status', text: 'running the search in your browser' });

    const code = `
import json, time
from dataclasses import replace
from symlab.cases.generators import GENERATORS, make_dataset
from symlab.search.engine import Engine, LADDER
from symlab.search.sparse import SparseRegressionSearch
from symlab.model.expr import to_infix
from symlab.model.latex import to_latex

generator = GENERATORS.get(${JSON.stringify(generatorId)}) or GENERATORS["monod-saturation"]
X, y = make_dataset(generator, n_rows=240, seed=${seed})

config = replace(
    LADDER["r4-multi-objective"],
    population=${population},
    generations=${generations},
    primitive_set=generator.suggested_primitives,
)
started = time.perf_counter()
# The family is chosen by the caller. The sparse arm ignores population and generations, because it
# has neither, and reporting the ladder's numbers for it would describe a search it never ran.
if ${JSON.stringify(method)} == "sparse":
    result = SparseRegressionSearch(config).run(X, y, seed=${seed})
else:
    result = Engine(config).run(X, y, seed=${seed})
elapsed = time.perf_counter() - started
best = result.best

json.dumps({
    "generator": generator.name,
    "truth": generator.truth_latex,
    "latex": to_latex(best.expression, display_names=[i.display for i in generator.inputs]),
    "infix": to_infix(best.expression, generator.input_keys),
    "complexity": int(best.complexity),
    "mse": float(best.loss),
    "seconds": float(elapsed),
    "front_size": len(result.pareto),
    "evaluations": int(result.counters.get("evaluations", 0)),
    "method": ${JSON.stringify(method)},
    "generations": ${generations} if ${JSON.stringify(method)} != "sparse" else None,
    "population": ${population} if ${JSON.stringify(method)} != "sparse" else None,
})
`;
    const raw = (await runtime.runPythonAsync(code)) as string;
    post({ kind: 'result', result: JSON.parse(raw) });
  } catch (error) {
    post({ kind: 'error', text: String(error) });
  }
};

export {};
