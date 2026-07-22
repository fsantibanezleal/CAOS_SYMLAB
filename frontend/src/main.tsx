import { AppShell, CitationsProvider, applyTheme, readTheme } from '@fasl-work/caos-app-shell';
import '@fasl-work/caos-app-shell/styles.css';
import 'katex/dist/katex.min.css';
import { FlaskConical } from 'lucide-react';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import './symlab.css';
import './symlab-workbench.css';
import { ARCHITECTURE } from './architecture';
import { CITATIONS } from './data/citations';
import { EXTERNAL_LINKS, VERSION } from './lib/links';
import { ROUTES } from './lib/routes';
import AppPage from './pages/AppPage';
import Benchmark from './pages/Benchmark';
import Experiments from './pages/Experiments';
import Implementation from './pages/Implementation';
import Introduction from './pages/Introduction';
import Methodology from './pages/Methodology';
import NotFound from './pages/NotFound';

/**
 * Apply the persisted theme BEFORE the first paint.
 *
 * The header toggle writes `caos.theme` and sets `data-theme` at runtime, but nothing read it back
 * on load, so a reader who chose light got dark again on every reload and on every deep link. The
 * shell exports `readTheme` and `applyTheme` for exactly this, and the consumer has to call them:
 * the choice is persisted by the shell and applied by the app.
 */
applyTheme(readTheme());

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <CitationsProvider items={CITATIONS}>
      <BrowserRouter>
        <AppShell
          config={{
            product: { name: 'SymLab', mark: <FlaskConical size={20} /> },
            routes: ROUTES,
            links: EXTERNAL_LINKS,
            version: VERSION,
            architecture: ARCHITECTURE,
            footer: {
              provenance: {
                en: 'Data: PMLB (MIT), OpenML 43311 (CC0), UCI (CC BY 4.0) · Evaluator: sreval (MIT)',
                es: 'Datos: PMLB (MIT), OpenML 43311 (CC0), UCI (CC BY 4.0) · Evaluador: sreval (MIT)',
              },
              disclaimer: {
                en: 'Every number is replayed from a committed artifact produced by a seeded offline run. The live lane runs the same engine in your browser at a reduced budget.',
                es: 'Cada numero se reproduce desde un artefacto versionado generado por una ejecucion offline con semilla fija. El panel en vivo ejecuta el mismo motor en tu navegador con presupuesto reducido.',
              },
            },
          }}
        >
          <Routes>
            <Route path="/" element={<AppPage />} />
            <Route path="/introduction" element={<Introduction />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/implementation" element={<Implementation />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/benchmark" element={<Benchmark />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </CitationsProvider>
  </StrictMode>,
);
