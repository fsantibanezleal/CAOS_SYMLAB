/** The single source of truth for routes: the router and the header nav both read this, so they
 *  cannot drift. The six pages are fixed by the product standard; nothing else becomes a nav entry. */
import type { ShellRoute } from '@fasl-work/caos-app-shell';

export const ROUTES: ShellRoute[] = [
  { path: '/', en: 'App', es: 'App' },
  { path: '/introduction', en: 'Introduction', es: 'Introduccion' },
  { path: '/methodology', en: 'Methodology', es: 'Metodologia' },
  { path: '/implementation', en: 'Implementation', es: 'Implementacion' },
  { path: '/experiments', en: 'Experiments', es: 'Experimentos' },
  { path: '/benchmark', en: 'Benchmark', es: 'Benchmark' },
];
