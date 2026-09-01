/**
 * The loading bar is real (mission §28): the percentage corresponds to completed work,
 * never decreases, waits for delayed critical resources, degrades past failed optional
 * ones, and the world reveals only after SCENE_VISUAL_READY. The weighting itself is
 * mutation-tested at unit level (boot-progress.test.ts); this spec proves the wiring
 * against a live renderer with controlled network conditions.
 */
import { expect, test } from '@playwright/test';

async function samplePercents(page: import('@playwright/test').Page, timeoutMs: number): Promise<number[]> {
  const samples: number[] = [];
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const veil = page.getByTestId('loading-veil');
    if ((await veil.count()) === 0) break;
    const text = await page.getByTestId('loading-percent').textContent().catch(() => null);
    if (text) samples.push(Number.parseInt(text, 10));
    await page.waitForTimeout(200);
  }
  return samples;
}

test('percentage is monotonic and the reveal happens only at 100', async ({ page }) => {
  await page.goto('/');
  const samples = await samplePercents(page, 60_000);
  expect(samples.length).toBeGreaterThan(2);
  for (let i = 1; i < samples.length; i += 1) {
    expect(samples[i]).toBeGreaterThanOrEqual(samples[i - 1]!);
  }
  // the last visible frame of the veil said 100 — the reveal is gated on readiness
  expect(samples[samples.length - 1]).toBe(100);
  await expect(page.getByTestId('loading-veil')).toHaveCount(0);
});

test('a delayed critical resource delays 100%', async ({ page }) => {
  // Hold hydrography (labels) for 6 s: the bar must sit below 100 until it lands.
  await page.route('**/geo/labels*', async (route) => {
    await new Promise((r) => setTimeout(r, 6_000));
    await route.continue();
  });
  await page.goto('/');
  await page.waitForTimeout(2_500);
  const early = Number.parseInt((await page.getByTestId('loading-percent').textContent()) ?? '100', 10);
  expect(early).toBeLessThan(100);
  // and it still completes once the resource arrives
  await expect(page.getByTestId('loading-veil')).toHaveCount(0, { timeout: 60_000 });
});

test('a failed optional resource degrades and still reaches the reveal', async ({ page }) => {
  await page.route('**/viz/basins*', (route) => route.fulfill({ status: 500, body: 'down' }));
  await page.goto('/');
  // the live envelope is optional: its failure must not park the bar short of done
  await expect(page.getByTestId('loading-veil')).toHaveCount(0, { timeout: 60_000 });
});
