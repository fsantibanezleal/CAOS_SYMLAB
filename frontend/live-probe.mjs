import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage();
const errs = [];
p.on('pageerror', e => errs.push(String(e)));
p.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
await p.goto('http://localhost:4296/?case=monod-saturation', { waitUntil: 'networkidle' });
await p.waitForTimeout(1500);
await p.getByRole('tab', { name: /live \(your browser\)/i }).click();
await p.waitForTimeout(800);
await p.locator('.sym-live-method select').selectOption('sparse');
await p.waitForTimeout(400);
const popShown = await p.locator('.sym-live-controls label', { hasText: 'population' }).isVisible().catch(() => false);
const famShown = await p.locator('.sym-live-method').isVisible();
console.log('family control visible :', famShown);
console.log('population hidden      :', !popShown);
await p.getByRole('button', { name: /^run|ejecutar/i }).first().click();
console.log('running in Pyodide...');
let out = null;
for (let i = 0; i < 60; i++) {
  await p.waitForTimeout(3000);
  const t = await p.locator('.sym-live').innerText();
  const m = t.match(/(mse|MSE)[^\n]*/i);
  if (m || /failed|Traceback|ModuleNotFound/i.test(t)) { out = t; break; }
}
if (out) {
  const lines = out.split('\n').filter(l => /mse|seconds|complexity|front|method|fail|error/i.test(l));
  console.log('result lines:', lines.slice(0, 8).join(' | ').slice(0, 300));
} else console.log('no result within the timeout');
console.log('console errors:', errs.length ? errs.slice(0,2) : 'none');
await b.close();
