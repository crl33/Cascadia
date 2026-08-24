/**
 * P1 search, end to end — written against the feature CONTRACT (docs/NEXT_STEPS.md P1 "search";
 * docs/SEMANTIC_ZOOM.md §9). Runs against the fixture stub that playwright.config.ts boots.
 * EXPECTED TO FAIL until the P1 search affordances are integrated.
 *
 * Expectations the integrator must satisfy on top of the existing spike behaviour:
 *   - Pressing "/" anywhere OUTSIDE an editable element focuses the search box and does not
 *     type a "/" into it (preventDefault). "/" inside an input keeps its normal meaning.
 *   - Typing "skag" (≥ 2 chars) opens the results list with the Skagit basin in it.
 *   - Enter selects the first result: the camera flies (full motion), the semantic band events
 *     fire IN ORDER — the band indicator walks ORBITAL → … → BASIN monotonically inward, never
 *     oscillating (bands are coarse semantic events, never per-frame state) — and the
 *     BasinPanel opens.
 * Reused existing testids: search-input, search-results, search-result, band-indicator,
 * flight-state, basin-panel-name, scene (data-scene-state), scene-fallback.
 *
 * Camera/band assertions are made only when the renderer booted (WebGL available); otherwise
 * the static fallback must be present and search + panel must still work (same convention as
 * skagit-flight.spec.ts).
 */
import { expect, test, type Page } from '@playwright/test';

async function rendererState(page: Page): Promise<'ready' | 'unavailable'> {
  const scene = page.getByTestId('scene');
  await expect(scene).toHaveAttribute('data-scene-state', /ready|unavailable/, { timeout: 30_000 });
  return (await scene.getAttribute('data-scene-state')) as 'ready' | 'unavailable';
}

/** Band depth order; a flight inward must visit bands in non-decreasing depth. */
const BAND_DEPTH: Record<string, number> = { ORBITAL: 0, STATE: 1, BASIN: 2, RIVER: 3, LOCAL: 4 };

test('slash focuses search, "skag" lists the Skagit basin, Enter flies (band events in order) and opens the panel', async ({ page }) => {
  await page.goto('/');
  const renderer = await rendererState(page);

  // "/" focuses the search input without typing into it.
  await page.keyboard.press('/');
  const searchInput = page.getByTestId('search-input');
  await expect(searchInput).toBeFocused();
  await expect(searchInput).toHaveValue('');

  await page.keyboard.type('skag');
  await expect(searchInput).toHaveValue('skag');
  await expect(page.getByTestId('search-results')).toBeVisible();
  const first = page.getByTestId('search-result').first();
  await expect(first).toContainText('Skagit');
  await expect(first).toContainText('basin');

  // Record every band-indicator transition from inside the page. The indicator only changes on
  // coarse semantic band events, so the observed sequence IS the event order.
  await page.evaluate(() => {
    const target = document.querySelector('[data-testid="band-indicator"]');
    // The recorder rides on window so the test can read it back; cast keeps tsc strict happy.
    const recorder = window as unknown as { __bandSequence: string[] };
    recorder.__bandSequence = target?.textContent ? [target.textContent] : [];
    if (!target) return;
    new MutationObserver(() => {
      recorder.__bandSequence.push(target.textContent ?? '');
    }).observe(target, { childList: true, characterData: true, subtree: true });
  });

  await page.keyboard.press('Enter');

  // The panel opens on the selection and the URL carries the deep link.
  await expect(page.getByTestId('basin-panel-name')).toHaveText('Skagit');
  await expect(page).toHaveURL(/sel=basin%3Askagit/);

  if (renderer === 'ready') {
    await expect(page.getByTestId('flight-state')).toHaveAttribute('data-flight-state', 'settled', { timeout: 15_000 });
    await expect(page.getByTestId('band-indicator')).toHaveText('BASIN', { timeout: 15_000 });

    const sequence = await page.evaluate(() => (window as unknown as { __bandSequence: string[] }).__bandSequence);
    const depths = sequence.filter((band) => band in BAND_DEPTH).map((band) => BAND_DEPTH[band]);
    expect(depths.length).toBeGreaterThanOrEqual(2);                    // at least one transition
    expect(depths[0]).toBe(BAND_DEPTH['ORBITAL']);                     // started orbital
    expect(depths[depths.length - 1]).toBe(BAND_DEPTH['BASIN']);       // landed at basin
    for (let i = 1; i < depths.length; i += 1) {
      expect(depths[i]).toBeGreaterThanOrEqual(depths[i - 1] ?? 0);    // in order, no oscillation
    }
  } else {
    await expect(page.getByTestId('scene-fallback')).toBeVisible();
  }
});
