/**
 * Copy the committed artifacts into the served public/ tree.
 *
 * The canonical copy lives in data/derived and manifests at the repository root, next to the
 * pipeline that writes it. The frontend serves a COPY, so the served tree can be regenerated and is
 * never the thing the pipeline has to know about.
 */
import { cp, mkdir, rm, stat } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..');
const target = join(here, 'public', 'data');

async function exists(path) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });

let copied = 0;
for (const [from, to] of [
  [join(repoRoot, 'data', 'derived'), join(target, 'derived')],
  [join(repoRoot, 'manifests'), join(target, 'manifests')],
]) {
  if (await exists(from)) {
    await cp(from, to, { recursive: true });
    copied += 1;
  } else {
    console.warn(`copy-data: ${from} does not exist yet; the app will show an honest empty state.`);
  }
}
// The live lane executes the SAME package source the offline bake ran, so that source has to be
// served. Without this step every module fetch 404s after Pyodide finishes loading, which reads as a
// runtime failure and is not one. Only the browser-safe subset is copied: the offline-only stages,
// the io layer and the pipeline never reach the browser and must not be shipped to it.
const ENGINE_MODULES = [
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

const engineOut = join(here, 'public', 'engine');
await rm(engineOut, { recursive: true, force: true });
let engineCopied = 0;
for (const module of ENGINE_MODULES) {
  const from = join(repoRoot, 'data-pipeline', module);
  if (!(await exists(from))) {
    throw new Error(`copy-data: engine module missing: ${from}`);
  }
  const to = join(engineOut, module);
  await mkdir(dirname(to), { recursive: true });
  await cp(from, to);
  engineCopied += 1;
}

console.log(`copy-data: copied ${copied} data tree(s) and ${engineCopied} engine modules into frontend/public`);
