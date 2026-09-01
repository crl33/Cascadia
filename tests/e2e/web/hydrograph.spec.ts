/**
 * P1 hydrograph panel, end to end — written against the feature CONTRACT (docs/NEXT_STEPS.md P1
 * "Hydrograph panel (observed + official forecast + thresholds with datum)";
 * docs/VISUAL_TRUTH_DOCTRINE.md §2: observed and forecast never share a register and the
 * boundary between them is marked). Runs against the fixture stub that playwright.config.ts
 * boots. EXPECTED TO FAIL until the P1 hydrograph is integrated.
 *
 * data-testids the integrator must wire (kebab-case, per apps/web/AGENTS.md conventions):
 *   hydrograph                   the hydrograph block inside the river panel
 *   hydrograph-svg               the chart itself: a hand-rolled inline <svg> (no chart library —
 *                                bundle caps are doctrine; assert tag name, not pixels)
 *   hydrograph-threshold-line    one per official flood category in the document (MVEW1: 4)
 *   hydrograph-threshold-label   label per line: category word + value + unit (+ datum when
 *                                basis=stage) — a number never appears without unit and datum
 *   hydrograph-series-observed   the observed series mark (observed register)
 *   hydrograph-series-forecast   the OFFICIAL FORECAST series mark, visually distinct register
 *   hydrograph-forecast-badge    OFFICIAL FORECAST source-kind badge adjacent to the forecast series
 *   hydrograph-register-boundary the marked observed/forecast valid-time boundary (doctrine §2)
 *   hydrograph-axis-unit         y-axis unit label: "ft (NGVD29)" for stage basis; "cfs" (no
 *                                datum) for flow basis
 * Reused existing testids: river-panel-name, observed-flow, thresholds, threshold-action, headroom.
 *
 * Data contract: MVEW1 is a stage-basis point (ft, NGVD29); AUBW1 (Green River near Auburn) is a
 * FLOW-basis point — official categories 6,000/9,000/12,000/14,000 cfs, no datum. The AUBW1
 * fixtures come from apps/web/dev/fixtures/mvew1-samples.json (`aubw1_*` keys; real 2026-08-22
 * NWPS/USGS captures). With E2E_LIVE_API=1, observed values differ from the committed fixtures,
 * so only their shape is asserted; the official thresholds are identical either way.
 */
import { expect, test } from '@playwright/test';
import { resolve } from 'node:path';

const screenshots = resolve(__dirname, '../__screenshots__');
const live = process.env['E2E_LIVE_API'] === '1';
const aubw1ObservedFlow = live ? /^[\d,]+ cfs$/ : '297 cfs';

test('MVEW1: SVG hydrograph with labeled threshold lines (unit + datum) and an OFFICIAL FORECAST series', async ({ page }) => {
  await page.goto('/?basin=basin:skagit&fp=MVEW1&motion=reduced');
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');

  const hydrograph = page.getByTestId('hydrograph');
  await expect(hydrograph).toBeVisible();
  // Hand-rolled SVG, not a canvas or a chart library.
  const chart = page.getByTestId('hydrograph-svg');
  await expect(chart).toBeVisible();
  expect(await chart.evaluate((el) => el.tagName.toLowerCase())).toBe('svg');

  // All four official categories are drawn and labeled with value + unit + datum.
  await expect(page.getByTestId('hydrograph-threshold-line')).toHaveCount(4);
  const labels = page.getByTestId('hydrograph-threshold-label');
  await expect(labels).toHaveCount(4);
  const labelText = (await labels.allTextContents()).join(' ');
  for (const word of ['action', 'minor', 'moderate', 'major']) expect(labelText.toLowerCase()).toContain(word);
  expect(labelText).toContain('23.5');       // official action stage
  expect(labelText).toContain('ft');         // unit
  expect(labelText).toContain('NGVD29');     // datum — a stage number never appears without it
  await expect(page.getByTestId('hydrograph-axis-unit')).toContainText('ft');
  await expect(page.getByTestId('hydrograph-axis-unit')).toContainText('NGVD29');

  // Observed and official forecast are distinct series; the forecast carries its badge and the
  // observed/forecast boundary is marked (registers never blur — doctrine §2).
  await expect(page.getByTestId('hydrograph-series-observed')).toHaveCount(1);
  await expect(page.getByTestId('hydrograph-series-forecast')).toHaveCount(1);
  await expect(page.getByTestId('hydrograph-forecast-badge')).toContainText('Official forecast');
  await expect(page.getByTestId('hydrograph-register-boundary')).toHaveCount(1);

  await page.screenshot({ path: resolve(screenshots, 'mvew1-hydrograph.png'), fullPage: false });
});

test('AUBW1: the flow-basis point renders its hydrograph and thresholds in cfs, without a datum', async ({ page }) => {
  await page.goto('/?basin=basin:green-duwamish&fp=AUBW1&motion=reduced');
  await expect(page.getByTestId('river-panel-name')).toHaveText('Green River near Auburn');

  // Panel: observed flow with unit, thresholds table on the flow basis in cfs, datum "n/a (flow)".
  await expect(page.getByTestId('observed-flow')).toHaveText(aubw1ObservedFlow);
  const thresholds = page.getByTestId('thresholds');
  await expect(thresholds).toContainText('flow');
  await expect(thresholds).toContainText('cfs');
  await expect(thresholds).toContainText('n/a (flow)');
  await expect(page.getByTestId('threshold-action')).toHaveText('6,000');
  await expect(page.getByTestId('headroom')).toContainText('flow');

  // Hydrograph: flow axis in cfs; threshold labels carry the flow values and unit, never a datum.
  await expect(page.getByTestId('hydrograph')).toBeVisible();
  await expect(page.getByTestId('hydrograph-threshold-line')).toHaveCount(4);
  const labelText = (await page.getByTestId('hydrograph-threshold-label').allTextContents()).join(' ');
  expect(labelText).toContain('6,000');
  expect(labelText).toContain('cfs');
  expect(labelText).not.toContain('NGVD29');
  const axisUnit = page.getByTestId('hydrograph-axis-unit');
  await expect(axisUnit).toContainText('cfs');
  await expect(axisUnit).not.toContainText('NGVD29');
});
