/**
 * Playwright E2E for the web spike: headless Chromium with software WebGL (SwiftShader), the
 * fixture-backed stub API on :8000 and `vite preview` on :4173. No live data, no clock
 * dependence (the fixtures carry fixed timestamps). Run from apps/web: `npm run e2e`.
 */
import { defineConfig, devices } from '@playwright/test';
import { resolve } from 'node:path';

// Playwright transpiles this file to CommonJS (no package.json here), so __dirname is available.
const here = __dirname;
const webDir = resolve(here, '../../apps/web');

export default defineConfig({
  testDir: resolve(here, 'web'),
  outputDir: resolve(here, '.results'),
  timeout: 90_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:4173',
    headless: true,
    viewport: { width: 1280, height: 800 },
    trace: 'retain-on-failure',
    // Software WebGL. `--use-gl=swiftshader` alone is deprecated in Chromium ≥ 110 and, in the
    // bundled Chromium 151, yields a context that is immediately lost; ANGLE-on-SwiftShader is the
    // supported path and renders the production build headless.
    launchOptions: { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } } }],
  webServer: [
    { command: 'node dev/stub-api.mjs', cwd: webDir, url: 'http://localhost:8000/system/health', reuseExistingServer: true, timeout: 30_000 },
    { command: 'npm run preview', cwd: webDir, url: 'http://localhost:4173', reuseExistingServer: true, timeout: 60_000 },
  ],
});
