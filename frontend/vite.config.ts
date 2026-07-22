import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  // Absolute root base, because this site is served from a custom domain at the root path. A
  // relative base ('./') makes import.meta.env.BASE_URL equal './', which React Router cannot use as
  // a basename: it fails to match any route and renders an empty page. That failure survives a green
  // build and a successful deploy, which is exactly why every route is screenshot-verified.
  base: '/',
  plugins: [react()],
  test: { environment: 'node', globals: true },
});
