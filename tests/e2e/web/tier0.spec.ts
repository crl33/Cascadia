/**
 * Tier 0 in the browser: the level, the change and the historical context of that change, as
 * three distinct statements — and the replay cursor moving between knowledge times without
 * leaving a later position's values on screen.
 *
 * This file exists because of a specific regression class. Tier 0 shipped in contract 1.3.0 and
 * was invisible in the client for a day: the generated types had it, the runtime zod schemas did
 * not, and minor-version tolerance stripped it silently. A green unit suite did not notice,
 * because nothing rendered it. These assertions run through the real parser, the real component
 * and the real replay path.
 *
 * Deterministic and offline: `functions/fixtures/basin_tier0.json` carries MEASURED Event Zero
 * values keyed by knowledge time, served by the same stub the other specs use.
 */
import { expect, test } from '@playwright/test';

// The Event Zero position the fixture populates, and one before any reference was stored.
const POPULATED = '2025-12-11T12:00:00Z';
const BEFORE_ANY_REFERENCE = '1999-01-01T00:00:00Z';
const url = (basin: string, asOf: string) =>
  `/?basin=${encodeURIComponent(basin)}&as_of=${encodeURIComponent(asOf)}&motion=reduced`;

test('the below-p90 growth rank reaches the screen', async ({ page }) => {
  // THE regression this spec exists for. snohomish-snoqualmie sits at p72.4 — below the level's
  // p90 read edge — with a real 24 h rise. Before 595fc92 the growth rank inherited that edge and
  // was absent exactly here; a client-side `percentile >= 90` guard would reintroduce it.
  await page.goto(url('basin:snohomish-snoqualmie', POPULATED));
  const level = page.getByTestId('tier0-level');
  await expect(level).toBeVisible();
  await expect(page.getByTestId('tier0-level-observed')).toContainText('6,110 cfs');

  // the LEVEL rank is deliberately not read below p90 — that policy is unchanged and stated
  await expect(page.getByTestId('tier0-level-rank-absent')).toContainText('Exact rank not read');

  // ...and the GROWTH rank is present anyway
  const change = page.getByTestId('tier0-change-24h');
  await expect(change.getByTestId('tier0-change-24h-growth')).toContainText('2.10×');
  await expect(change.getByTestId('tier0-change-24h-growth')).toContainText('rising');
  const rank = page.getByTestId('tier0-change-24h-rank');
  await expect(rank).toBeVisible();
  await expect(rank).toContainText('759th');
  await expect(rank).toContainText('34,957');
});

test('a clamped level reads as a bound, with its exact rank and the record it beat', async ({ page }) => {
  await page.goto(url('basin:skagit', POPULATED));
  await expect(page.getByTestId('tier0-level-clamped')).toContainText('At or above the stored p95 limit');
  await expect(page.getByTestId('tier0-level-multiple')).toContainText('4.99×');
  await expect(page.getByTestId('tier0-level-multiple')).toContainText('12,550 cfs');
  const rank = page.getByTestId('tier0-level-rank');
  await expect(rank).toContainText('1st');
  await expect(rank).toContainText('491');
  await expect(rank).toContainText('37,400 cfs');
  // the boundary is a CONDITION about the sample, never a confidence or a probability
  const boundary = page.getByTestId('tier0-level-boundary');
  await expect(boundary).toContainText('Sampling error is not quantified here');
  await expect(boundary).not.toContainText(/confidence|probability|%/);
});

test('a MODERATE band and a large, high-ranked change coexist without collapsing', async ({ page }) => {
  // The exact situation the design exists for: the level is unremarkable, the CHANGE is not, and
  // the reader must be able to hold both without the UI implying Cascadia has declared a flood.
  await page.goto(url('basin:snohomish-snoqualmie', POPULATED));
  await expect(page.getByTestId('surface-susceptibility-state')).toHaveText('MODERATE');
  await expect(page.getByTestId('tier0-change-24h-growth')).toContainText('2.10×');
  await expect(page.getByTestId('tier0-change-24h-rank')).toContainText('759th');

  const panel = page.getByTestId('basin-panel');
  // no alert vocabulary anywhere, and no fourth number summarising the three statements
  await expect(panel).not.toContainText(/flood warning|imminent|dangerous|extreme|severe/i);
  // the band is the ONLY thing wearing a state word; Tier 0 adds none of its own
  await expect(panel.locator('.state-word')).toHaveCount(4); // the four surfaces, unchanged
  await expect(page.getByTestId('tier0').locator('.state-word')).toHaveCount(0);
  // and the derived statements are not painted in the alarm register reserved for flood category
  const alarmColoured = await page.getByTestId('tier0').evaluate((el) =>
    [...el.querySelectorAll('*')].some((n) => {
      const c = getComputedStyle(n as HTMLElement).color;
      const m = /rgba?\((\d+), (\d+), (\d+)/.exec(c);
      if (!m) return false;
      const [r, g, b] = [Number(m[1]), Number(m[2]), Number(m[3])];
      return r > 180 && g < 130 && b < 110; // the red/amber family
    }));
  expect(alarmColoured, 'a Cascade-derived statement is painted in the alarm register').toBe(false);
});

test('every Tier 0 refusal keeps the backend reason instead of a generic Unavailable', async ({ page }) => {
  await page.goto(url('basin:cedar', POPULATED));
  const absent = page.getByTestId('tier0-change-24h-absent');
  await expect(absent).toContainText('No 24 h change');
  // the specific reason is one interaction away, not several, and is the backend's own sentence
  await absent.getByText('why').click();
  await expect(page.getByTestId('tier0-change-24h-absent-reason')).toContainText('no daily mean within 6 h');

  await page.goto(url('basin:green-duwamish', POPULATED));
  await expect(page.getByTestId('tier0-change-24h-growth')).toContainText('1.34×');
  const notRanked = page.getByTestId('tier0-change-24h-rank-absent');
  await expect(notRanked).toContainText('Not ranked');
  await notRanked.getByText('why').click();
  await expect(page.getByTestId('tier0-change-24h-rank-absent-reason')).toContainText('build_climatology');
});

test('moving the replay cursor never leaves a later knowledge time on screen', async ({ page }) => {
  await page.goto(url('basin:skagit', POPULATED));
  await expect(page.getByTestId('tier0-level-observed')).toContainText('62,600 cfs');

  // step back to a knowledge time before any reference existed: the surface must REFUSE, and
  // the populated values must be gone rather than left stale
  await page.goto(url('basin:skagit', BEFORE_ANY_REFERENCE));
  await expect(page.getByTestId('tier0-absent')).toBeVisible();
  await expect(page.getByTestId('tier0-absent-reason')).toContainText('No level or change statement at this knowledge time');
  await expect(page.getByTestId('tier0-level-observed')).toHaveCount(0);
  await expect(page.getByTestId('tier0-change-24h')).toHaveCount(0);
  await expect(page.getByTestId('basin-panel')).not.toContainText('62,600');

  // and forward again restores it
  await page.goto(url('basin:skagit', POPULATED));
  await expect(page.getByTestId('tier0-level-observed')).toContainText('62,600 cfs');
});

test('each Tier 0 statement carries its own provenance, reachable by keyboard', async ({ page }) => {
  await page.goto(url('basin:skagit', POPULATED));
  const levelBadge = page.getByTestId('tier0-level-badge');
  const changeBadge = page.getByTestId('tier0-change-24h-badge');
  await expect(levelBadge).toBeVisible();
  await expect(changeBadge).toBeVisible();

  await levelBadge.click();
  const inspector = page.getByTestId('layer-inspector');
  await expect(inspector).toContainText('method:streamflow-tail-state@0.1.0');
  await page.keyboard.press('Escape');

  // a DIFFERENT statement resolves to a DIFFERENT method — not one badge over the section
  await changeBadge.click();
  await expect(page.getByTestId('layer-inspector')).toContainText('method:streamflow-state-change@0.1.0');
  await page.keyboard.press('Escape');
});

test('the refusal disclosure is keyboard operable and does not overflow at mobile width', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(url('basin:cedar', POPULATED));
  const summary = page.getByTestId('tier0-change-24h-absent').locator('summary');
  await summary.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByTestId('tier0-change-24h-absent-reason')).toBeVisible();

  // the long backend sentence must wrap inside the panel, not widen or clip it
  const panel = page.getByTestId('basin-panel');
  const panelBox = await panel.boundingBox();
  const reasonBox = await page.getByTestId('tier0-change-24h-absent-reason').boundingBox();
  expect(panelBox).not.toBeNull();
  expect(reasonBox).not.toBeNull();
  expect(reasonBox!.width).toBeLessThanOrEqual(panelBox!.width + 1);
  const overflows = await panel.evaluate((el) => el.scrollWidth > el.clientWidth + 1);
  expect(overflows, 'the panel scrolls horizontally at 390px').toBe(false);
});
