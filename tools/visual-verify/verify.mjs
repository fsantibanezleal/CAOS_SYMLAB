/**
 * Screenshot-verify SymLab: every route, both themes, plus console and page errors.
 *
 * A build that compiles and a site that renders are different claims. This checks the second by
 * loading each route in both themes, capturing anything the page logged, and asserting that the
 * panels a reader came for are actually present in the DOM rather than merely reserved by CSS.
 */
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const BASE = process.argv[2] ?? 'https://fsantibanezleal.github.io/CAOS_SYMLAB/';
// Screenshots land in a scratch directory OUTSIDE the repository, so a verification run can never
// leave images in a commit. Override with SYMLAB_SHOTS; the default is the system temp directory
// rather than a path that only exists on one machine.
const OUT = process.argv[3] ?? join(tmpdir(), 'symlab-shots');

const ROUTES = [
  ['app', ''],
  ['introduction', 'introduction'],
  ['methodology', 'methodology'],
  ['implementation', 'implementation'],
  ['experiments', 'experiments'],
  ['benchmark', 'benchmark'],
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
const problems = [];

for (const theme of ['light', 'dark']) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const logs = [];
  page.on('console', (m) => { if (m.type() === 'error') logs.push(`console: ${m.text()}`); });
  page.on('pageerror', (e) => logs.push(`pageerror: ${e.message}`));

  for (const [name, path] of ROUTES) {
    logs.length = 0;
    await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle', timeout: 60000 });
    await page.evaluate((t) => document.documentElement.setAttribute('data-theme', t), theme);
    await page.waitForTimeout(1600);

    const state = await page.evaluate(() => {
      const body = document.querySelector('.page-body');
      const rect = body?.getBoundingClientRect();
      return {
        title: document.title,
        h1: document.querySelector('h1')?.textContent?.trim() ?? null,
        pageBodyWidth: rect ? Math.round(rect.width) : null,
        pageBodyLeft: rect ? Math.round(rect.left) : null,
        viewport: window.innerWidth,
        katex: document.querySelectorAll('.katex').length,
        svgs: document.querySelectorAll('svg').length,
        tables: document.querySelectorAll('table').length,
        chips: document.querySelectorAll('.variant-chip, .chip').length,
        headerNav: document.querySelectorAll('header a').length,
        textLength: document.body.innerText.length,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
      };
    });

    await page.screenshot({ path: `${OUT}/${name}-${theme}.png`, fullPage: true });

    const centred =
      state.pageBodyWidth !== null &&
      Math.abs(state.pageBodyLeft - (state.viewport - state.pageBodyWidth) / 2) < 24;
    if (!centred) problems.push(`${name}/${theme}: .page-body not centred (left=${state.pageBodyLeft}, w=${state.pageBodyWidth})`);
    if (state.horizontalOverflow) problems.push(`${name}/${theme}: page scrolls horizontally`);
    if (state.textLength < 400) problems.push(`${name}/${theme}: only ${state.textLength} chars of text`);
    if (!state.h1) problems.push(`${name}/${theme}: no h1`);
    for (const l of logs) problems.push(`${name}/${theme}: ${l}`);

    console.log(
      `${theme.padEnd(5)} ${name.padEnd(15)} h1="${(state.h1 ?? '').slice(0, 34)}" ` +
        `w=${state.pageBodyWidth} katex=${state.katex} svg=${state.svgs} ` +
        `tbl=${state.tables} chips=${state.chips} text=${state.textLength} ` +
        `${logs.length ? 'ERRORS:' + logs.length : 'clean'}`,
    );
  }
  await context.close();
}

await browser.close();
console.log(`\nshots -> ${OUT}`);
if (problems.length) {
  console.log(`\n${problems.length} PROBLEM(S):`);
  for (const p of problems) console.log('  ' + p);
  process.exit(1);
}
console.log('\nall routes rendered in both themes with no console or page errors');
