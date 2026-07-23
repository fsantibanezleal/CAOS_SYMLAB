/**
 * The five content pages, which the workbench harness never touched.
 *
 * They read the same artifacts the App does and quote statistics from them, so a change to what the
 * pipeline exports can leave a page quoting a number that no longer exists, or rendering "null" and
 * "undefined" into prose. Both are invisible to a build.
 */
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const BASE = process.env.SYMLAB_BASE ?? 'http://localhost:4293';
// Screenshots land in a scratch directory OUTSIDE the repository, so a verification run can never
// leave images in a commit. Override with SYMLAB_SHOTS; the default is the system temp directory
// rather than a path that only exists on one machine.
const OUT = process.env.SYMLAB_SHOTS ?? join(tmpdir(), 'symlab-shots');
mkdirSync(OUT, { recursive: true });

const ROUTES = ['introduction', 'methodology', 'implementation', 'experiments', 'benchmark'];
const COMBOS = [
  { theme: 'light', lang: 'en' },
  { theme: 'dark', lang: 'es' },
];

const failures = [];
const note = (m) => failures.push(m);
const browser = await chromium.launch();

for (const { theme, lang } of COMBOS) {
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));

  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
  await page.evaluate(([t, l]) => {
    localStorage.setItem('caos.theme', t);
    localStorage.setItem('caos.lang', l);
  }, [theme, lang]);

  for (const route of ROUTES) {
    await page.goto(`${BASE}/${route}`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);

    const applied = await page.evaluate(() => document.documentElement.dataset.theme ?? null);
    if (applied !== theme) note(`${theme}/${lang}/${route}: theme did not apply (${applied})`);

    const body = await page.evaluate(() => document.body.innerText);

    // A statistic that stopped existing renders as a JavaScript artifact, in prose, silently.
    //
    // The first version of this check flagged the bare word "undefined", which fired on two pieces
    // of legitimate prose: "rejects undefined candidates before evaluating them" and
    // "1/x undefined". A check that cries wolf on correct copy gets ignored, so it now looks for
    // shapes that prose does not produce: a value position, or a token standing alone as an
    // entire text node.
    const artifacts = await page.evaluate(() => {
      const suspicious = [];
      const VALUE_POSITION = /(?::|=|is\s|\(|,)\s*(undefined|NaN|null|Infinity|-Infinity|\[object Object\])/;
      const ALONE = /^(undefined|NaN|null|Infinity|\[object Object\])$/;
      const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walk.nextNode())) {
        const text = node.textContent.trim();
        if (!text) continue;
        if (ALONE.test(text) || VALUE_POSITION.test(text)) {
          suspicious.push(text.slice(0, 90));
        }
      }
      return suspicious;
    });
    if (artifacts.length) {
      note(`${theme}/${lang}/${route}: JavaScript artifact in rendered text: ${artifacts.slice(0, 2).join(' // ')}`);
    }
    if (/\bnot found\b/i.test(body) || /does not exist in this application/i.test(body)) {
      note(`${theme}/${lang}/${route}: resolved to the not-found page`);
    }

    const chars = await page.evaluate(() => {
      const main = document.querySelector('main') ?? document.body;
      return main.innerText.trim().length;
    });
    if (chars < 600) note(`${theme}/${lang}/${route}: only ${chars} characters of content`);

    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (overflow > 2) note(`${theme}/${lang}/${route}: overflows horizontally by ${overflow}px`);

    // Every figure must have rendered something, not reserved empty space.
    const emptyFigures = await page.evaluate(() =>
      [...document.querySelectorAll('figure')].filter((f) => {
        const box = f.getBoundingClientRect();
        return box.height < 24 || f.innerText.trim().length + f.querySelectorAll('svg,img,canvas').length === 0;
      }).length);
    if (emptyFigures > 0) note(`${theme}/${lang}/${route}: ${emptyFigures} empty figure(s)`);

    await page.screenshot({ path: `${OUT}/page-${theme}-${lang}-${route}.png`, fullPage: true });
  }

  if (errors.length) note(`${theme}/${lang}: console errors: ${errors.slice(0, 3).join(' // ')}`);
  await ctx.close();
}

await browser.close();
if (failures.length) {
  console.log(`FAIL (${failures.length})`);
  failures.forEach((f) => console.log('  - ' + f));
  process.exit(1);
}
console.log(`PASS: ${ROUTES.length} content pages x ${COMBOS.length} combinations`);
