/**
 * The Skagit flight spike, end to end against the fixture stub. Panels are the assertion
 * surface; camera/band assertions are made only when the renderer booted (WebGL available),
 * otherwise the static fallback must be present and the panels must still work.
 */
import { expect, test, type Page } from '@playwright/test';
import { resolve } from 'node:path';

const screenshots = resolve(__dirname, '../__screenshots__');

// E2E_LIVE_API=1 runs the same suite against the real API on :8000 (start it with
// CASCADE_CORS_ORIGINS=http://localhost:4173 so the preview origin is allowed). Live values differ
// from the committed fixtures, so only their *shape* (unit + datum) is asserted in that mode; the
// official thresholds are identical either way.
const live = process.env['E2E_LIVE_API'] === '1';
const observedStage = live ? /^\d+\.\d{2} ft \(NGVD29\)$/ : '10.59 ft (NGVD29)';
const observedFlow = live ? /^[\d,]+ cfs$/ : '6,660 cfs';
const forecastCrest = live ? /^\d+\.\d{2} ft \(NGVD29\)$/ : '11.10 ft (NGVD29)';

async function rendererState(page: Page): Promise<'ready' | 'unavailable'> {
  const scene = page.getByTestId('scene');
  await expect(scene).toHaveAttribute('data-scene-state', /ready|unavailable/, { timeout: 30_000 });
  return (await scene.getAttribute('data-scene-state')) as 'ready' | 'unavailable';
}

test('search Skagit → basin selected → BasinPanel shows Skagit with an OFFICIAL FORECAST badge', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('disclaimer')).toContainText('Not an official alert authority');
  const renderer = await rendererState(page);
  await expect(page.getByTestId('band-indicator')).toHaveText('ORBITAL');

  await page.getByTestId('search-input').fill('Skagit');
  const first = page.getByTestId('search-result').first();
  await expect(first).toContainText('Skagit');
  await first.click();

  await expect(page.getByTestId('basin-panel-name')).toHaveText('Skagit');
  await expect(page.getByTestId('surface-hazard-badge')).toContainText('OFFICIAL FORECAST');
  // The stub serves a REAL production capture (2026-08-28) since the pre-P3 envelope was
  // retired: the surfaces carry live values, and the EXPERIMENTAL badge must ride along.
  await expect(page.getByTestId('surface-susceptibility-state')).toHaveText('LOW');
  await expect(page.getByTestId('surface-forcing-state')).toHaveText('LOW');
  await expect(page.getByTestId('surface-susceptibility-badge')).toContainText('EXPERIMENTAL');
  await expect(page.getByTestId('hazard-category')).toContainText('NONE');
  await expect(page).toHaveURL(/sel=basin%3Askagit/);

  if (renderer === 'ready') {
    await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 15_000 });
    await expect(page.getByTestId('band-indicator')).toHaveText('BASIN');
  } else {
    await expect(page.getByTestId('scene-fallback')).toBeVisible();
  }
});

test('deep link ?basin=basin:skagit&fp=MVEW1&motion=reduced → RiverPanel shows observed stage and official thresholds', async ({ page }) => {
  await page.goto('/?basin=basin:skagit&fp=MVEW1&motion=reduced');
  const renderer = await rendererState(page);

  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');
  await expect(page.getByTestId('observed-stage')).toHaveText(observedStage);
  await expect(page.getByTestId('observed-flow')).toHaveText(observedFlow);
  await expect(page.getByTestId('observed-badge')).toContainText('OBSERVED');
  await expect(page.getByTestId('observed')).toContainText('provisional');
  await expect(page.getByTestId('threshold-action')).toHaveText('23.5');
  await expect(page.getByTestId('thresholds')).toContainText('NGVD29');
  await expect(page.getByTestId('thresholds-badge')).toContainText('OFFICIAL FORECAST');
  await expect(page.getByTestId('forecast-crest')).toHaveText(forecastCrest);
  await expect(page.getByTestId('forecast-badge')).toContainText('OFFICIAL FORECAST');
  await expect(page.getByTestId('trend-badge')).toContainText('DERIVED');
  await expect(page.getByTestId('headroom-badge')).toContainText('DERIVED');
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Skagit');
  await expect(page).toHaveURL(/sel=fp%3Anwps%3AMVEW1&basin=basin%3Askagit&motion=reduced/);

  // Badge → inspector shows the provenance lines.
  await page.getByTestId('observed-badge').click();
  const inspector = page.getByTestId('layer-inspector');
  await expect(inspector).toContainText('src:usgs-nwis-iv');
  await expect(inspector).toContainText('n/a (observation)');

  if (renderer === 'ready') {
    await expect(page.getByTestId('band-indicator')).toHaveText('RIVER', { timeout: 15_000 });
    await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled');
  }
});

test('reduced motion: a selection cuts and settles immediately', async ({ page }) => {
  await page.goto('/?motion=reduced');
  const renderer = await rendererState(page);
  test.skip(renderer !== 'ready', 'renderer unavailable in this environment; camera behaviour cannot be observed');

  await expect(page.getByTestId('motion-toggle')).toHaveAttribute('data-motion', 'reduced');
  await page.getByTestId('search-input').fill('Skagit');
  await page.getByTestId('search-result').first().click();
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Skagit');
  // A cut settles within the same tick; allow only the data round-trip, never a flight duration.
  await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 2_000 });
  await expect(page.getByTestId('band-indicator')).toHaveText('BASIN', { timeout: 2_000 });
});

test('screenshot of the basin scene', async ({ page }) => {
  await page.goto('/?basin=basin:skagit&motion=reduced');
  const renderer = await rendererState(page);
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Skagit');
  if (renderer === 'ready') await expect(page.getByTestId('band-indicator')).toHaveText('BASIN', { timeout: 15_000 });
  await page.waitForTimeout(2_500); // let tiles and the outline fade settle (no pixel comparison is made)
  await page.screenshot({ path: resolve(screenshots, 'skagit-basin-scene.png'), fullPage: false });
  await page.goto('/?basin=basin:skagit&fp=MVEW1&motion=reduced');
  await expect(page.getByTestId('observed-stage')).toHaveText(observedStage);
  if (renderer === 'ready') await expect(page.getByTestId('band-indicator')).toHaveText('RIVER', { timeout: 15_000 });
  await page.waitForTimeout(2_500);
  await page.screenshot({ path: resolve(screenshots, 'mvew1-river-scene.png'), fullPage: false });
});
