/**
 * P2 Event Zero replay, end to end — written against the feature CONTRACT (docs/NEXT_STEPS.md
 * P2; docs/CINEMATIC_ROADMAP.md §11 at P2 scope): entering the event by deep link, the
 * timeline anchored to the event window in EVENT time (no as_of anywhere — ADR-0010: a
 * backfilled row's knowledge time is its 2026 retrieval, so a knowledge-time replay inside
 * the event would honestly render UNKNOWN), the hydrograph showing the archived observed
 * series up to the cursor plus the forecast run the replay clock selects, and the
 * forecast-evolution view listing runs with superseded runs visibly superseded and the
 * backfilled flag surfaced. Runs against the fixture stub that playwright.config.ts boots
 * (fixtures: apps/web/dev/fixtures/mvew1-samples.json `event_zero_mvew1` — FACT values from
 * docs/EVENT_ZERO.md §3/§5/§8; the golden chain is 36.9 → 41.5 → 41.5 → 42.3 → 42.1 → 39.1 →
 * 39.1 → 38.3 → 38.1 vs the observed crest 37.73 ft at 2025-12-12T08:15Z).
 *
 * data-testids wired by the event slice: event-banner, forecast-evolution, evolution-run
 * (+ data-superseded), evolution-status-current/-superseded, evolution-empty,
 * evolution-backfilled, evolution-observed-crest, hydrograph-backfilled.
 * Reused: river-panel-name, timeline (+ data-mode), timeline-mode-chip, timeline-scrubber,
 * timeline-window-start/end, snap-to-now, as-of-banner, hydrograph-series-*, hydrograph-crest.
 */
import { expect, test, type Page } from '@playwright/test';

const EVENT_URL = '/?event=event-zero-2025-12&motion=reduced';

/** Scrub the timeline range input to an instant (deterministic; React sees an input event). */
async function scrubTo(page: Page, iso: string): Promise<void> {
  await page.getByTestId('timeline-scrubber').evaluate((el, value) => {
    const input = el as HTMLInputElement;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
    setter.call(input, value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }, String(Date.parse(iso)));
}

test('deep link enters Event Zero: event banner, event-anchored window, no as_of, one run at the boot cursor', async ({ page }) => {
  await page.goto(EVENT_URL);
  // Default framing from the registry: MVEW1, with no sel= in the link.
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');
  const banner = page.getByTestId('event-banner');
  await expect(banner).toBeVisible();
  await expect(banner).toContainText('EVENT REPLAY');
  await expect(banner).toContainText('reconstructed');
  // Event time is not a knowledge time: no AS-OF banner, no as_of anywhere.
  await expect(page.getByTestId('as-of-banner')).toBeHidden();
  expect(page.url()).not.toMatch(/[?&]as_of=/);
  await expect(page).toHaveURL(/[?&]event=event-zero-2025-12/);
  // Timeline anchored to the event window (Dec 3–23 2025 UTC bounds), in event mode.
  await expect(page.getByTestId('timeline')).toHaveAttribute('data-mode', 'event');
  await expect(page.getByTestId('timeline-mode-chip')).toContainText('EVENT REPLAY');
  await expect(page.getByTestId('timeline-window-start')).toHaveText('2025-12-03 08:00 UTC');
  await expect(page.getByTestId('timeline-window-end')).toHaveText('2025-12-23 08:00 UTC');
  // Boot cursor = the first MVEW1 FLW issuance: exactly that run, current, 36.9 ft, backfilled.
  const rows = page.getByTestId('evolution-run');
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText('36.9 ft');
  await expect(page.getByTestId('evolution-status-current')).toHaveText('CURRENT');
  await expect(page.getByTestId('evolution-backfilled').first()).toBeVisible();
});

test('scrubbing the event clock changes the selected forecast run with zero look-ahead; superseded runs stay, marked', async ({ page }) => {
  await page.goto(EVENT_URL);
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');
  await expect(page.getByTestId('evolution-run')).toHaveCount(1);

  // Forward past the second issuance (12-10T01:24Z): two runs; 41.5 ft current; the first FLW
  // visibly superseded — never deleted.
  await scrubTo(page, '2025-12-10T02:00:00Z');
  const rows = page.getByTestId('evolution-run');
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(1)).toContainText('41.5 ft');
  await expect(rows.nth(1)).toHaveAttribute('data-superseded', 'false');
  await expect(rows.nth(0)).toContainText('36.9 ft');
  await expect(rows.nth(0)).toHaveAttribute('data-superseded', 'true');
  await expect(rows.nth(0)).toContainText('SUPERSEDED');
  // The hydrograph's forecast series is the replay-selected run (crest 41.5), not the first one.
  await expect(page.getByTestId('hydrograph-series-forecast')).toHaveCount(1);
  await expect(page.getByTestId('hydrograph-crest')).toContainText('41.5');
  // The URL round-trips the event cursor — never as_of.
  await expect(page).toHaveURL(/[?&]at=2025-12-10T02%3A00%3A00Z/);
  expect(page.url()).not.toMatch(/[?&]as_of=/);

  // Back before the first issuance: no forecast yet (UNKNOWN, no fabricated line) and no
  // observed point after the cursor (the archive's first point is 12-09T16:15Z).
  await scrubTo(page, '2025-12-08T00:00:00Z');
  await expect(page.getByTestId('evolution-run')).toHaveCount(0);
  await expect(page.getByTestId('evolution-empty')).toBeVisible();
  await expect(page.getByTestId('hydrograph-series-forecast')).toHaveCount(0);
  await expect(page.getByTestId('hydrograph-series-observed')).toHaveCount(0);

  // Full window: all 9 golden issuances, 38.1 ft current; the observed crest line appears only
  // once the cursor has passed it, with the BACKFILLED flag surfaced on the observed series.
  await scrubTo(page, '2025-12-23T08:00:00Z');
  await expect(page.getByTestId('evolution-run')).toHaveCount(9);
  const last = page.getByTestId('evolution-run').nth(8);
  await expect(last).toContainText('38.1 ft');
  await expect(last).toHaveAttribute('data-superseded', 'false');
  await expect(page.getByTestId('evolution-observed-crest')).toContainText('37.73 ft');
  await expect(page.getByTestId('hydrograph-backfilled')).toBeVisible();
});

test('NOW exits event replay to live: banner gone, event and at dropped from the URL', async ({ page }) => {
  await page.goto(EVENT_URL);
  await expect(page.getByTestId('event-banner')).toBeVisible();
  await page.getByTestId('snap-to-now').click();
  await expect(page.getByTestId('event-banner')).toBeHidden();
  await expect(page.getByTestId('timeline')).toHaveAttribute('data-mode', 'now');
  await expect(page).not.toHaveURL(/[?&]event=/);
  await expect(page).not.toHaveURL(/[?&]at=/);
  await expect(page.getByTestId('as-of-banner')).toBeHidden();
});
