/**
 * P1 per-value provenance popover, end to end — written against the feature CONTRACT
 * (docs/NEXT_STEPS.md P1 "layer inspector with per-value provenance";
 * docs/VISUAL_TRUTH_DOCTRINE.md §6 inspector specification). Runs against the fixture stub
 * that playwright.config.ts boots. EXPECTED TO FAIL until the P1 popover is integrated.
 *
 * Contract: clicking a value's source-kind badge opens the provenance popover for exactly that
 * value. The popover keeps the existing container testid and gains per-row testids so the
 * doctrine fields stay individually assertable:
 *   layer-inspector      the popover container (existing)
 *   inspector-source     SOURCE row: source_id · product_id — label
 *   inspector-freshness  FRESHNESS row: state word + age + cadence (never a decimal score)
 *   inspector-issued     ISSUED row: issued time for forecasts; "n/a (observation)" for observed
 *   inspector-retrieved  RETRIEVED row: always shown
 *   inspector-close      the popover's close control
 * Reused existing testids: river-panel-name, observed-badge, forecast-badge.
 *
 * Expected values come from the committed fixture
 * packages/contracts/fixtures/river_mvew1_envelope.json (served by the stub): observed ref
 * usgs-iv-12200500 (current, age 2700 s → "45 min", cadence 900 s → "15 min", retrieved
 * 2026-08-22T08:26:43Z), forecast ref nwps-forecast-mvew1 (issued 2026-08-21T15:05:00Z).
 * With E2E_LIVE_API=1 the live ages/times differ, so only their shape is asserted.
 */
import { expect, test } from '@playwright/test';

const live = process.env['E2E_LIVE_API'] === '1';
const UTC_MINUTE = /\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC/;

test('clicking the observed value badge opens the popover with source, freshness and issued lines', async ({ page }) => {
  await page.goto('/?basin=basin:skagit&fp=MVEW1&motion=reduced');
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');
  await expect(page.getByTestId('layer-inspector')).toBeHidden(); // nothing inspected yet

  await page.getByTestId('observed-badge').click();
  const popover = page.getByTestId('layer-inspector');
  await expect(popover).toBeVisible();

  await expect(page.getByTestId('inspector-source')).toContainText('src:usgs-nwis-iv');
  await expect(page.getByTestId('inspector-source')).toContainText('product:usgs-iv-00065-00060');

  const freshness = page.getByTestId('inspector-freshness');
  await expect(freshness).toContainText('current');
  if (live) {
    await expect(freshness).toContainText(/age /);
  } else {
    await expect(freshness).toContainText('age 45 min');
    await expect(freshness).toContainText('cadence 15 min');
  }

  // Observations are never "issued" — the doctrine line is explicit.
  await expect(page.getByTestId('inspector-issued')).toHaveText('n/a (observation)');
  await expect(page.getByTestId('inspector-retrieved')).toContainText(live ? UTC_MINUTE : '2026-08-22 08:26 UTC');
});

test('the official forecast badge opens its own popover with the issued time from the fixture', async ({ page }) => {
  await page.goto('/?basin=basin:skagit&fp=MVEW1&motion=reduced');
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');

  // Open the observed popover first, close it, then open the forecast one: the popover always
  // shows the value that was clicked, never a stale record.
  await page.getByTestId('observed-badge').click();
  await expect(page.getByTestId('layer-inspector')).toBeVisible();
  await page.getByTestId('inspector-close').click();
  await expect(page.getByTestId('layer-inspector')).toBeHidden();

  await page.getByTestId('forecast-badge').click();
  await expect(page.getByTestId('layer-inspector')).toBeVisible();
  await expect(page.getByTestId('inspector-source')).toContainText('src:nwps-v1');
  await expect(page.getByTestId('inspector-source')).toContainText('product:nwps-stageflow-forecast');
  await expect(page.getByTestId('inspector-issued')).toContainText(live ? UTC_MINUTE : '2026-08-21 15:05 UTC');
  const freshness = page.getByTestId('inspector-freshness');
  await expect(freshness).toContainText('current');
  if (!live) {
    await expect(freshness).toContainText('age 17.9 h');
    await expect(freshness).toContainText('cadence 24.0 h');
  }
});
