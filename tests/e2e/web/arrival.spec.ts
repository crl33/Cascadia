/**
 * Film rule 3 — the arrival is the shot; the flight is the cut between shots
 * (docs/research/cesium-cinematic-plan-2026-09-01.md rows 1 and 3; exit tests E1.6, E1.7).
 *
 *   (a) The basin panel is never in the DOM while data-flight-state reads 'flying', and it
 *       first appears ≥ ARRIVAL_HOLD_MS (400 ms) after the state reads 'settled'.
 *   (b) No weather-field setData reaches the renderer between a flight's 'started' and its
 *       'settled' — observed through the store-free stamps SceneDataBridge writes on <html>:
 *       data-weather-set-data (count of applied documents) and data-weather-deferred.
 *   (c) The flight apex on a Nooksack → Puyallup hop, logged from data-flight-max-height on
 *       the scene container (CameraController samples preRender), never exceeds
 *       ZOOM_CEILING_M = 1,250,000 m.
 *
 * Camera behaviour is only observable when the renderer booted (WebGL available); each test
 * skips on the static fallback, the same convention as skagit-flight.spec.ts.
 */
import { expect, test, type Page } from '@playwright/test';

const ARRIVAL_HOLD_MS = 400;
const ZOOM_CEILING_M = 1_250_000;

interface FlightRecord { t: number; flight: string | null; panel: boolean; weather: string | null }

declare global {
  interface Window { __arrival?: FlightRecord[] }
}

async function rendererState(page: Page): Promise<'ready' | 'unavailable'> {
  const scene = page.getByTestId('scene');
  await expect(scene).toHaveAttribute('data-scene-state', /ready|unavailable/, { timeout: 30_000 });
  return (await scene.getAttribute('data-scene-state')) as 'ready' | 'unavailable';
}

/** Record, from inside the page, every flight-state flip, every change under the panels host
 * and every weather stamp change — each with a timestamp and a snapshot of the other two. */
async function installRecorder(page: Page): Promise<void> {
  await page.evaluate(() => {
    const flight = document.querySelector('[data-testid="flight-state"]');
    const panels = document.querySelector('[data-occlusion="panels"]');
    if (!flight || !panels) throw new Error('flight-state stamp or panels host missing');
    const records: FlightRecord[] = [];
    window.__arrival = records;
    const snapshot = () => records.push({
      t: performance.now(),
      flight: flight.getAttribute('data-flight-state'),
      panel: document.querySelector('[data-testid="basin-panel"]') !== null,
      weather: document.documentElement.getAttribute('data-weather-set-data'),
    });
    snapshot();
    new MutationObserver(snapshot).observe(flight, { attributes: true, attributeFilter: ['data-flight-state'] });
    new MutationObserver(snapshot).observe(panels, { childList: true, subtree: true });
    new MutationObserver(snapshot).observe(document.documentElement, { attributes: true, attributeFilter: ['data-weather-set-data', 'data-weather-deferred'] });
  });
}

const readRecords = (page: Page) => page.evaluate(() => window.__arrival ?? []);

async function flyViaSearch(page: Page, query: string, expectName: string): Promise<void> {
  await page.getByTestId('search-input').fill(query);
  const first = page.getByTestId('search-result').first();
  await expect(first).toContainText(expectName);
  await expect(first).toContainText('basin');
  await first.click();
}

test('(a) the basin panel is absent while flying and mounts ≥ 400 ms after settle', async ({ page }) => {
  await page.goto('/');
  const renderer = await rendererState(page);
  test.skip(renderer !== 'ready', 'renderer unavailable in this environment; flights cannot be observed');
  await expect(page.getByTestId('band-indicator')).toHaveText('ORBITAL');
  await installRecorder(page);

  await flyViaSearch(page, 'Skagit', 'Skagit');
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 20_000 });
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Skagit', { timeout: 10_000 });

  const records = await readRecords(page);
  const flying = records.filter((r) => r.flight === 'flying');
  expect(flying.length).toBeGreaterThan(0);                         // a real flight happened
  for (const r of flying) expect(r.panel, `panel present at t=${r.t.toFixed(0)} while flying`).toBe(false);

  const settledAt = records.find((r, i) => r.flight === 'settled' && i > 0 && records[i - 1]?.flight === 'flying')?.t;
  const panelAt = records.find((r) => r.panel && r.t > (settledAt ?? Infinity))?.t;
  expect(settledAt, 'no flying→settled transition recorded').toBeDefined();
  expect(panelAt, 'panel never appeared after settle').toBeDefined();
  const gap = (panelAt ?? 0) - (settledAt ?? 0);
  console.log(`arrival (a): panel mounted ${gap.toFixed(0)} ms after settle`);
  expect(gap).toBeGreaterThanOrEqual(ARRIVAL_HOLD_MS);
});

test('(b) no weather setData between a flight\'s started and settled', async ({ page }) => {
  // Deep-link load is a cut (Skagit is framed and settled on arrival); the next selection is a
  // full-motion flight away from it.
  await page.goto('/?basin=basin:skagit');
  const renderer = await rendererState(page);
  test.skip(renderer !== 'ready', 'renderer unavailable in this environment; flights cannot be observed');
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Skagit');
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 20_000 });
  // The weather stamps exist once the fields have been offered at least once (stub serves both).
  await expect.poll(() => page.evaluate(() => document.documentElement.getAttribute('data-weather-set-data')), { timeout: 20_000 }).not.toBeNull();
  await installRecorder(page);

  await flyViaSearch(page, 'Puyallup', 'Puyallup');
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'flying', { timeout: 10_000 });
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 20_000 });
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Puyallup / White', { timeout: 10_000 });

  const records = await readRecords(page);
  const startIdx = records.findIndex((r) => r.flight === 'flying');
  const settleIdx = records.findIndex((r, i) => i > startIdx && r.flight === 'settled');
  expect(startIdx).toBeGreaterThanOrEqual(0);
  expect(settleIdx).toBeGreaterThan(startIdx);
  const during = records.slice(startIdx, settleIdx + 1);
  const counts = new Set(during.map((r) => r.weather));
  console.log(`arrival (b): weather setData count ${records[startIdx]?.weather} at start, ${records[settleIdx]?.weather} at settle`);
  expect(counts.size, 'weather setData count changed between started and settled').toBe(1);
  // Nothing may still be held once the flight has settled and the panel is up.
  await expect.poll(() => page.evaluate(() => document.documentElement.hasAttribute('data-weather-deferred'))).toBe(false);
});

test('(c) Nooksack → Puyallup flight apex stays ≤ 1,250,000 m', async ({ page }) => {
  await page.goto('/?basin=basin:nooksack');
  const renderer = await rendererState(page);
  test.skip(renderer !== 'ready', 'renderer unavailable in this environment; flights cannot be observed');
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Nooksack');
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 20_000 });

  await flyViaSearch(page, 'Puyallup', 'Puyallup');
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'flying', { timeout: 10_000 });
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 20_000 });

  const raw = await page.locator('.scene-canvas').getAttribute('data-flight-max-height');
  expect(raw, 'CameraController did not stamp data-flight-max-height').not.toBeNull();
  const apexM = Number(raw);
  console.log(`arrival (c): Nooksack → Puyallup apex ${apexM.toLocaleString('en-US')} m (ceiling ${ZOOM_CEILING_M.toLocaleString('en-US')} m)`);
  expect(Number.isFinite(apexM)).toBe(true);
  expect(apexM).toBeGreaterThan(0);
  expect(apexM).toBeLessThanOrEqual(ZOOM_CEILING_M);
});
