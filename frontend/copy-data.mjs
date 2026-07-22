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
console.log(`copy-data: copied ${copied} tree(s) into frontend/public/data`);
