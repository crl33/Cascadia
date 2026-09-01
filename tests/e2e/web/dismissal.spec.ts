/**
 * Click-away dismissal is a design-system standard (mission §12): a pinned camera preview
 * closes on Escape, closes on a click on empty map (the pick pipeline's onEmptyClick),
 * and does NOT close when the interaction is inside the card. The provenance inspector
 * follows the same primitive (covered by its own flows elsewhere); this spec pins the
 * camera card, the audit's original offender (F11).
 */
import { expect, test } from '@playwright/test';

const PIN = 'pin=cam%3Ausgs%3AWA_Skagit_River_near_Mount_Vernon';

async function settled(page: import('@playwright/test').Page): Promise<void> {
  await page.waitForSelector('[data-testid="loading-veil"]', { state: 'detached', timeout: 60_000 });
  await page
    .waitForFunction(() => document.querySelector('.scene-canvas')?.getAttribute('data-tiles-pending') === '0', undefined, { timeout: 60_000 })
    .catch(() => {});
}

test('Escape dismisses a pinned camera preview', async ({ page }) => {
  await page.goto(`/?sel=basin:skagit&motion=reduced&${PIN}`);
  await settled(page);
  const card = page.getByTestId('camera-card-cam:usgs:WA_Skagit_River_near_Mount_Vernon');
  await expect(card).toBeVisible({ timeout: 15_000 });
  await page.keyboard.press('Escape');
  await expect(card).toHaveCount(0);
});

test('a click on empty map dismisses the card; a click inside does not', async ({ page }) => {
  await page.goto(`/?sel=basin:skagit&motion=reduced&${PIN}`);
  await settled(page);
  const card = page.getByTestId('camera-card-cam:usgs:WA_Skagit_River_near_Mount_Vernon');
  await expect(card).toBeVisible({ timeout: 15_000 });

  // inside the card: opening the reasons disclosure must not dismiss it
  await card.getByText('Why this camera?').click();
  await expect(card).toBeVisible();

  // empty ocean, far from any marker/panel: the map's own click-away
  await page.mouse.click(120, 640);
  await expect(card).toHaveCount(0, { timeout: 5_000 });
});
