/**
 * The live lane and the offline lane must return the SAME expression.
 *
 * The Live tab tells a reader it runs the same engine as the offline bake. That was asserted for a
 * long time and never checked, and when it was finally checked it was false: the two returned
 * different expressions because `make_dataset` seeded its RNG with the builtin `hash()`, which
 * Python randomises per process. Two lanes are two processes.
 *
 * With stable hashing they agree exactly, which is worth keeping true. This runs both halves and
 * compares, so a regression fails here rather than in a reader's browser.
 *
 * Requires a served build (`cd frontend && npm run build && npx vite preview`). Usage, from the
 * repository root:
 *   SYMLAB_BASE=http://localhost:4173 node tools/verify/live-parity-check.mjs
 */
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const BASE = process.env.SYMLAB_BASE ?? 'http://localhost:4299';
const CASE = process.env.PARITY_CASE ?? 'monod-saturation';
const PYTHON =
  process.env.SYMLAB_PYTHON ??
  (process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');

// --- the offline half -------------------------------------------------------------------------
const offlineRaw = execFileSync(
  PYTHON,
  [join(HERE, 'live-parity-offline.py'), '--case', CASE],
  { encoding: 'utf8' },
);
const offline = JSON.parse(offlineRaw).offline;

// --- the browser half -------------------------------------------------------------------------
const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(String(e).slice(0, 200)));

await page.goto(`${BASE}/?case=${CASE}`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await page.getByRole('tab', { name: /live \(your browser\)/i }).click();
await page.waitForTimeout(600);
await page.getByRole('button', { name: /^\s*run/i }).first().click();

let live = null;
for (let attempt = 0; attempt < 90; attempt += 1) {
  await page.waitForTimeout(2500);
  if ((await page.locator('.sym-live-result').count()) > 0) {
    live = await page.evaluate(() => {
      const root = document.querySelector('.sym-live-result');
      const values = [...root.querySelectorAll('dd')].map((d) => d.textContent.trim());
      return {
        infix: root.querySelector('.sym-live-expression')?.textContent?.trim() ?? null,
        complexity: Number(values[0]),
      };
    });
    break;
  }
}
await browser.close();

// --- compare ----------------------------------------------------------------------------------
const failures = [];
if (!live) {
  failures.push('the live lane produced no result');
} else {
  if (live.infix !== offline.infix) {
    failures.push(
      `expressions differ:\n    live    ${live.infix}\n    offline ${offline.infix}`,
    );
  }
  if (live.complexity !== offline.complexity) {
    failures.push(`complexity differs: live ${live.complexity}, offline ${offline.complexity}`);
  }
}
if (errors.length) failures.push(`console errors: ${errors.slice(0, 2).join(' // ')}`);

if (failures.length) {
  console.log('LIVE PARITY FAIL');
  failures.forEach((f) => console.log('  - ' + f));
  console.log(
    '\n  The usual cause is something process-dependent leaking into the sampling or the search.\n' +
      '  Check tests/test_cross_process_determinism.py first.',
  );
  process.exit(1);
}
console.log(`LIVE PARITY OK: both lanes return ${offline.infix} at complexity ${offline.complexity}`);
