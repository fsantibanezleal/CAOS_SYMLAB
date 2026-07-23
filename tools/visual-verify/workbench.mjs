/**
 * Verify the SymLab workbench by RENDERING it, not by reading it.
 *
 * Every interface defect in this product so far survived a green build and a successful deploy, and
 * every one of them would have been visible on opening the page. So this harness opens each tab in
 * both themes, and asserts the things a build cannot see:
 *
 *   - no console error, and no unstyled class rendering as raw text
 *   - the expression tab shows BOTH sides of the comparison, each with its provenance label
 *   - the case navigator offers dropdowns, and the case dropdown actually has options
 *   - no horizontal page overflow at either width
 *   - no panel is empty when the artifact says it has content
 */
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const BASE = process.env.SYMLAB_BASE ?? 'http://localhost:4183';
// Screenshots land in a scratch directory OUTSIDE the repository, so a verification run can never
// leave images in a commit. Override with SYMLAB_SHOTS; the default is the system temp directory
// rather than a path that only exists on one machine.
const OUT = process.env.SYMLAB_SHOTS ?? join(tmpdir(), 'symlab-shots');
mkdirSync(OUT, { recursive: true });

const TABS = ['expression', 'structure', 'validation', 'live', 'front', 'context'];

const failures = [];
const backgrounds = new Map();
const note = (m) => failures.push(m);

const browser = await chromium.launch();

// Both themes AND both languages. The product is bilingual by ADR floor, and a panel that only
// ever gets screenshotted in English can ship a Spanish string that overflows, an untranslated
// fragment, or a number formatted for the wrong locale.
const COMBOS = [
  { theme: 'light', lang: 'en' },
  { theme: 'dark', lang: 'en' },
  { theme: 'light', lang: 'es' },
  { theme: 'dark', lang: 'es' },
];

for (const { theme, lang } of COMBOS) {
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));

  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
  await page.evaluate(([t, l]) => {
    // The shell's own storage keys. 'caos-theme' was a guess and it silently did nothing, so
    // after the reload every "light" run was actually rendering dark and the light theme was
    // never verified at all.
    localStorage.setItem('caos.theme', t);
    localStorage.setItem('caos.lang', l);
    document.documentElement.dataset.theme = t;
  }, [theme, lang]);
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForTimeout(1400);

  // Assert the theme and language actually took, rather than trusting the write. A verification
  // harness that silently runs the same combination four times is worse than no harness.
  // Strict, with no escape hatch. The first version of this check fell back to reading a
  // background colour when data-theme was unset, which made "theme did not apply at all" look
  // identical to "theme applied", and every light run was silently rendering dark.
  const applied = await page.evaluate(() => ({
    theme: document.documentElement.dataset.theme ?? null,
    lang: localStorage.getItem('caos.lang'),
    bg: getComputedStyle(document.body).backgroundColor,
  }));
  if (applied.lang !== lang) {
    note(`${theme}/${lang}: language did not apply, page reports ${applied.lang}`);
  }
  if (applied.theme !== theme) {
    note(`${theme}/${lang}: theme did not apply, data-theme is ${applied.theme ?? 'unset'}`);
  }
  backgrounds.set(`${theme}/${lang}`, applied.bg);

  // --- the navigator must be dropdowns, populated ---------------------------------------------
  const selects = await page.locator('.sym-nav .sym-select').count();
  if (selects < 2) note(`${theme}/${lang}: expected category and case dropdowns, found ${selects}`);
  const caseOptions = await page.locator('.sym-nav .sym-select').last().locator('option').count();
  if (caseOptions < 1) note(`${theme}/${lang}: the case dropdown has no options`);
  const lanes = await page.locator('.sym-lane-button').count();
  if (lanes < 1) note(`${theme}/${lang}: no source lane control`);

  for (const tab of TABS) {
    const TAB_NAMES = {
      expression: /expression|expresion/i,
      structure: /structure|estructura/i,
      validation: /parity and residuals|paridad y residuos/i,
      live: /live \(your browser\)|en vivo/i,
      front: /front and search|frente y busqueda/i,
      context: /context|contexto/i,
    };
    const button = page.getByRole('tab', { name: TAB_NAMES[tab] });
    if (await button.count()) {
      await button.first().click();
      await page.waitForTimeout(900);
    }

    // A class written into JSX and never given a rule is how "rows2,550 inputs4" reached the
    // screen: the markup was right and the layout simply never existed. Rather than guessing from
    // the rendered text, collect every class the panel actually uses and confirm the stylesheets
    // define it. This is exact, and it catches the defect before a human has to notice it.
    const unstyled = await page.evaluate(() => {
      const main = document.querySelector('.symlab-main');
      if (!main) return [];
      const used = new Set();
      main.querySelectorAll('[class]').forEach((el) => {
        el.classList.forEach((c) => { if (c.startsWith('sym') || c.startsWith('page-')) used.add(c); });
      });
      const defined = new Set();
      for (const sheet of document.styleSheets) {
        let rules;
        try { rules = sheet.cssRules; } catch { continue; }
        const walk = (list) => {
          for (const rule of list) {
            if (rule.selectorText) {
              for (const m of rule.selectorText.matchAll(/\.([A-Za-z0-9_-]+)/g)) defined.add(m[1]);
            }
            if (rule.cssRules) walk(rule.cssRules);
          }
        };
        walk(rules);
      }
      return [...used].filter((c) => !defined.has(c));
    });
    if (unstyled.length) note(`${theme}/${lang}/${tab}: classes used but never styled: ${unstyled.join(', ')}`);

    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (overflow > 2) note(`${theme}/${lang}/${tab}: page overflows horizontally by ${overflow}px`);

    const filled = await page.evaluate(() => {
      const main = document.querySelector('.symlab-main');
      return main ? main.innerText.trim().length : 0;
    });
    if (filled < 200) note(`${theme}/${lang}/${tab}: main area has only ${filled} characters of content`);

    if (lang === 'es') {
      // Untranslated fragments are the standing risk on a bilingual page: the tab renders, the
      // build passes, and an English sentence sits in the middle of a Spanish panel.
      const englishLeak = await page.evaluate(() => {
        const main = document.querySelector('.symlab-main');
        if (!main) return null;
        // Provenance records written by the pipeline stay in English on purpose and are marked
        // lang="en", so they are excluded here. What this checks is INTERFACE copy that failed to
        // translate, which is a genuine defect rather than a deliberate verbatim quote.
        const clone = main.cloneNode(true);
        clone.querySelectorAll('[lang="en"]').forEach((el) => el.remove());
        const text = clone.innerText;
        const markers = [
          'the search', 'Each point is', 'Hover a', 'Showing ', 'the expression',
          'training support', 'was baked before', 'rows used', 'no published',
          'Predicted against', 'A flat, structureless', 'The shaded band',
        ];
        const hit = markers.find((m) => text.includes(m));
        return hit ?? null;
      });
      if (englishLeak) note(`${theme}/${lang}/${tab}: untranslated English fragment: "${englishLeak}"`);
    }

    await page.screenshot({ path: `${OUT}/${theme}-${lang}-${tab}.png`, fullPage: true });
  }

  // --- the expression tab must make provenance unmissable --------------------------------------
  const expr = page.getByRole('tab', { name: /expression|expresion/i });
  if (await expr.count()) { await expr.first().click(); await page.waitForTimeout(800); }
  const tags = await page.locator('.sym-tag').allInnerTexts();
  const hasFound = tags.some((t) =>
    lang === 'es' ? /ENCONTRADO POR LA BUSQUEDA/i.test(t) : /FOUND BY THE SEARCH/i.test(t));
  const hasTruth = tags.some((t) =>
    lang === 'es' ? /LA RELACION ESPERADA/i.test(t) : /THE RELATIONSHIP WE EXPECTED/i.test(t));
  if (!hasFound) note(`${theme}/${lang}: the discovered expression carries no provenance label`);
  if (!hasTruth) note(`${theme}/${lang}: the reference side carries no label`);
  const mathBoxes = await page.locator('.sym-math .katex').count();
  if (mathBoxes < 1) note(`${theme}/${lang}: no rendered mathematics in the expression tab`);
  const verdict = await page.locator('.sym-verdict').count();
  if (verdict < 1) note(`${theme}/${lang}: no verdict shown between the two expressions`);

  if (errors.length) note(`${theme}/${lang}: console errors: ${errors.slice(0, 3).join(' // ')}`);
  await context.close();
}

// A light run and a dark run that paint the same background mean one of them did not take,
// whatever the attribute claims.
const lightBg = backgrounds.get('light/en');
const darkBg = backgrounds.get('dark/en');
if (lightBg && darkBg && lightBg === darkBg) {
  note(`light and dark render the same background (${lightBg}), so one theme never applied`);
}

await browser.close();

if (failures.length) {
  console.log(`FAIL (${failures.length})`);
  failures.forEach((f) => console.log('  - ' + f));
  process.exit(1);
}
console.log(`PASS: ${TABS.length} tabs x ${COMBOS.length} theme/language combinations rendered, provenance labels present, no overflow`);
