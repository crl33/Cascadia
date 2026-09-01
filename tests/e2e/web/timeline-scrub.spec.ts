/**
 * P1 timeline/replay, end to end — written against the feature CONTRACT (docs/NEXT_STEPS.md P1
 * "Timeline/replay controls driving as_of across every query"; docs/CINEMATIC_ROADMAP.md §10 C5;
 * docs/VISUAL_TRUTH_DOCTRINE.md §8 "Replay scenes show the knowledge time prominently; nothing
 * in a replay is styled as live"). Runs against the fixture stub that playwright.config.ts
 * boots. EXPECTED TO FAIL until the P1 timeline is integrated.
 *
 * data-testids the integrator must wire (kebab-case, per apps/web/AGENTS.md conventions):
 *   timeline            the timeline control cluster, present whenever the app shell is
 *   timeline-scrubber   keyboard-operable scrub control (role="slider" or <input type="range">);
 *                       ArrowLeft steps knowledge time into the past, ArrowRight toward now;
 *                       it can never move past now
 *   as-of-banner        visible ONLY in replay; reads "AS OF <knowledge time, UTC>" prominently
 *   snap-to-now         control that restores live mode: banner removed, as_of dropped from the
 *                       URL, panels render the live document again
 * Reused existing testids: river-panel-name.
 *
 * URL contract: replay serializes `as_of=<ISO 8601 UTC>` into the query string (deep-link
 * grammar extension); live mode never carries as_of; a deep link with as_of boots straight
 * into replay (load is always a cut).
 *
 * Data contract: in replay every state query carries `as_of=` — the backend is a pure function
 * of as_of and the client NEVER recomputes science on scrub (query keys are
 * [entity, ..., asOf]). Snap-to-now may legitimately serve the live document from the query
 * cache, so the way back is asserted on DOM state only, never on a network request.
 */
import { expect, test } from '@playwright/test';

const MVEW1_STATE = '/forecast-points/MVEW1/state';
const SCRUB_STEPS = 5;

test('scrub into the past: AS OF banner appears, as_of enters the URL, the panel refetches keyed by as_of', async ({ page }) => {
  await page.goto('/?basin=basin:skagit&fp=MVEW1&motion=reduced');
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');
  // Live mode: no replay banner, no as_of anywhere.
  await expect(page.getByTestId('as-of-banner')).toBeHidden();
  expect(page.url()).not.toMatch(/[?&]as_of=/);

  // Arm the interception BEFORE scrubbing: the panel must re-render from an as_of-keyed request.
  const asOfRequest = page.waitForRequest(
    (request) => request.url().includes(MVEW1_STATE) && new URL(request.url()).searchParams.has('as_of'),
  );
  // ...and so must the weather FIELD: scrubbing is timeline-driven spatial change (C3b) —
  // the map's precipitation must be re-asked at the scrubbed knowledge time, not frozen at now.
  const fieldAsOfRequest = page.waitForRequest(
    (request) => request.url().includes('/viz/fields/precip_observed') && new URL(request.url()).searchParams.has('as_of'),
  );

  const scrubber = page.getByTestId('timeline-scrubber');
  await scrubber.focus();
  for (let step = 0; step < SCRUB_STEPS; step += 1) await scrubber.press('ArrowLeft');

  const banner = page.getByTestId('as-of-banner');
  await expect(banner).toBeVisible();
  await expect(banner).toContainText('AS OF');
  await expect(page).toHaveURL(/[?&]as_of=/);

  const request = await asOfRequest;
  await fieldAsOfRequest;
  const requestAsOf = new URL(request.url()).searchParams.get('as_of') ?? '';
  const requestKnowledgeTime = new Date(requestAsOf);
  expect(Number.isNaN(requestKnowledgeTime.getTime())).toBe(false);
  expect(requestKnowledgeTime.getTime()).toBeLessThan(Date.now()); // into the past, never ahead

  // The URL carries a valid past knowledge time too (it is the deep link for this replay view).
  const urlAsOf = new URL(page.url()).searchParams.get('as_of') ?? '';
  const urlKnowledgeTime = new Date(urlAsOf);
  expect(Number.isNaN(urlKnowledgeTime.getTime())).toBe(false);
  expect(urlKnowledgeTime.getTime()).toBeLessThan(Date.now());

  // The panel re-rendered from the as_of document, not from a client-side recompute.
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');
});

test('snap-to-now restores live mode: banner gone, as_of dropped from the URL', async ({ page }) => {
  await page.goto('/?basin=basin:skagit&fp=MVEW1&motion=reduced');
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');

  const scrubber = page.getByTestId('timeline-scrubber');
  await scrubber.focus();
  for (let step = 0; step < 3; step += 1) await scrubber.press('ArrowLeft');
  await expect(page.getByTestId('as-of-banner')).toBeVisible();
  await expect(page).toHaveURL(/[?&]as_of=/);

  await page.getByTestId('snap-to-now').click();
  await expect(page.getByTestId('as-of-banner')).toBeHidden();
  // The URL write lands in an effect the renderer can starve on 2-core CI (software GL tile
  // decode pegs the main thread after the live refetch) — give it renderer-load headroom.
  await expect(page).not.toHaveURL(/[?&]as_of=/, { timeout: 30_000 });
  await expect(page.getByTestId('river-panel-name')).toHaveText('Skagit River near Mount Vernon');
});

test('a deep link carrying as_of boots directly into replay with an as_of-keyed request', async ({ page }) => {
  const AS_OF = '2026-08-22T06:00:00Z';
  const stateRequest = page.waitForRequest((request) => {
    if (!request.url().includes(MVEW1_STATE)) return false;
    const asOf = new URL(request.url()).searchParams.get('as_of');
    return asOf !== null && asOf.startsWith('2026-08-22T06:00');
  });
  await page.goto(`/?basin=basin:skagit&fp=MVEW1&motion=reduced&as_of=${encodeURIComponent(AS_OF)}`);
  await stateRequest;
  const banner = page.getByTestId('as-of-banner');
  await expect(banner).toBeVisible();
  await expect(banner).toContainText('AS OF');
  // The banner speaks local time; the exact UTC instant rides the hover title (§21).
  await expect(banner.locator('[title]')).toHaveAttribute('title', /2026-08-22 06:00 UTC/);
  await expect(page).toHaveURL(/[?&]as_of=/);
});
