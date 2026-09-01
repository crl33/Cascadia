/**
 * Two experiences over four tiers (owner 2026-09-01; PERFORMANCE.md §3.2). The e2e build
 * pins the probe off (VITE_QUALITY_PROBE=off), so "automatic" resolves to BALANCED and the
 * switch is the only thing that moves the tier. The effective tier is observable on
 * <html data-quality> — the same attribute the glass system reads.
 */
import { expect, test } from '@playwright/test';

async function revealed(page: import('@playwright/test').Page): Promise<void> {
  await expect(page.getByTestId('loading-veil')).toHaveCount(0, { timeout: 60_000 });
}

test('automatic is BALANCED without a probe; the switch moves the tier both ways and persists', async ({ page }) => {
  await page.goto('/');
  await revealed(page);
  await expect(page.locator('html')).toHaveAttribute('data-quality', 'balanced');

  await page.getByTestId('settings-button').click();
  await expect(page.getByTestId('experience-essential')).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByTestId('experience-cinematic')).toHaveAttribute('aria-pressed', 'false');
  await expect(page.getByTestId('experience-status')).toContainText('Automatic');

  await page.getByTestId('experience-cinematic').click();
  await expect(page.locator('html')).toHaveAttribute('data-quality', 'high');
  await expect(page.getByTestId('experience-cinematic')).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByTestId('experience-status')).toContainText('Your choice');

  // the choice survives a reload (per-browser preference)
  await page.reload();
  await revealed(page);
  await expect(page.locator('html')).toHaveAttribute('data-quality', 'high');

  await page.getByTestId('settings-button').click();
  await page.getByTestId('experience-auto').click();
  await expect(page.locator('html')).toHaveAttribute('data-quality', 'balanced');
  await expect(page.getByTestId('experience-status')).toContainText('Automatic');
});

test('explicit rendering still answers input: a zoom gesture changes the band', async ({ page }) => {
  await page.goto('/');
  await revealed(page);
  const scene = page.getByTestId('scene');
  const before = await page.getByTestId('band-indicator').textContent().catch(() => null);
  const box = await scene.boundingBox();
  if (!box) throw new Error('scene has no box');
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  for (let i = 0; i < 12; i += 1) {
    await page.mouse.wheel(0, -400);
    await page.waitForTimeout(80);
  }
  await expect.poll(async () => page.getByTestId('band-indicator').textContent().catch(() => null), { timeout: 15_000 }).not.toBe(before);
});
