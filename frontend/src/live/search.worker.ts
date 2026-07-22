/**
 * The live search worker: the offline Python engine, loaded into the browser under Pyodide.
 *
 * Runs off the main thread so a search that takes seconds never freezes the page. The engine source
 * is fetched from the served copy of the package, so the browser executes the same modules the bake
 * executed rather than a parallel implementation that would have to be kept in agreement forever.
 *
 * Pyodide is loaded from a pinned CDN version, matching the pattern the sibling labs already use, so
 * the runtime and its scientific wheels are not part of this site payload.
 */
const PYODIDE_VERSION = '0.28.3';
const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

declare function importScripts(...urls: string[]): void;
declare const loadPyodide: (options: { indexURL: string }) => Promise<PyodideInterface>;

interface PyodideInterface {
  loadPackage(names: string[]): Promise<void>;
  runPythonAsync(code: string): Promise<unknown>;
  FS: { mkdirTree(path: string): void; writeFile(path: string, data: string): void };
}

let pyodide: PyodideInterface | null = null;

/** The package modules the live lane needs. The offline-only stages are deliberately absent. */
const MODULES = [
  'symlab/__init__.py',
  'symlab/model/__init__.py',
  'symlab/model/expr.py',
  'symlab/model/units.py',
  'symlab/model/intervals.py',
  'symlab/model/scaling.py',
  'symlab/model/complexity.py',
  'symlab/model/latex.py',
  'symlab/search/__init__.py',
  'symlab/search/generate.py',
  'symlab/search/variation.py',
  'symlab/search/select.py',
  'symlab/search/tune.py',
  'symlab/search/engine.py',
  'symlab/search/exhaustive.py',
  'symlab/cases/__init__.py',
  'symlab/cases/generators.py',
];

async function boot(post: (message: unknown) => void): Promise<PyodideInterface> {
  if (pyodide) return pyodide;
  post({ kind: 'status', text: 'loading the Python runtime' });
  importScripts(`${PYODIDE_INDEX_URL}pyodide.js`);
  const runtime = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
  post({ kind: 'status', text: 'loading numpy' });
  await runtime.loadPackage(['numpy']);

  post({ kind: 'status', text: 'loading the engine source' });
  const base = `${self.location.origin}${self.location.pathname.replace(/\/[^/]*$/, '')}/engine`;
  for (const module of MODULES) {
    const response = await fetch(`${base}/${module}`);
    if (!response.ok) throw new Error(`engine module ${module} returned ${response.status}`);
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
  const { caseId, population, generations, seed } = event.data as {
    caseId: string;
    population: number;
    generations: number;
    seed: number;
  };

  try {
    const runtime = await boot(post);
    post({ kind: 'status', text: 'running the search' });

    const code = `
import json, time
import numpy as np
from dataclasses import replace
from symlab.cases.generators import GENERATORS, make_dataset
from symlab.search.engine import Engine, LADDER
from symlab.model.expr import to_infix, size
from symlab.model.latex import to_latex

case_id = ${JSON.stringify(caseId)}
generator = GENERATORS.get(case_id)
if generator is None:
    generator = GENERATORS["monod-saturation"]
X, y = make_dataset(generator, n_rows=240, seed=${seed})

config = replace(
    LADDER["r4-multi-objective"],
    population=${population}, generations=${generations},
    primitive_set=generator.suggested_primitives,
)
started = time.perf_counter()
result = Engine(config).run(X, y, seed=${seed})
elapsed = time.perf_counter() - started

best = result.best
json.dumps({
    "latex": to_latex(best.expression, display_names=[i.display for i in generator.inputs]),
    "infix": to_infix(best.expression, generator.input_keys),
    "complexity": int(best.complexity),
    "mse": float(best.loss),
    "seconds": float(elapsed),
    "generations": ${generations},
    "population": ${population},
})
`;
    const raw = (await runtime.runPythonAsync(code)) as string;
    post({ kind: 'result', result: JSON.parse(raw) });
  } catch (error) {
    post({ kind: 'error', text: String(error) });
  }
};

export {};
