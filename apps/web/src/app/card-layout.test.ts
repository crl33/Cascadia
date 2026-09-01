import { describe, expect, it } from 'vitest';
import { placeCard, type Rect } from './card-layout';

const VIEWPORT = { width: 1440, height: 900 };
const CARD = { width: 232, height: 210 };
const SAFE = 8;

const inViewport = (p: { left: number; top: number }): boolean =>
  p.left >= SAFE && p.top >= SAFE && p.left + CARD.width <= VIEWPORT.width - SAFE && p.top + CARD.height <= VIEWPORT.height - SAFE;

/** Deterministic LCG — the §21 property test must be reproducible, never flaky. */
const lcg = (seed: number) => () => {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 2 ** 32;
};

describe('placeCard — spatial placement is deterministic and mathematically closed (§13, §21)', () => {
  it('an anchor near the TOP edge places the card BELOW, fully on-screen', () => {
    const p = placeCard({ x: 720, y: 30 }, CARD, VIEWPORT, []);
    expect(p.top).toBeGreaterThan(30);
    expect(inViewport(p)).toBe(true);
  });

  it('an anchor near the RIGHT edge opens LEFT (§30 journey requirement)', () => {
    const p = placeCard({ x: 1420, y: 450 }, CARD, VIEWPORT, []);
    expect(p.left + CARD.width).toBeLessThanOrEqual(1420);
    expect(inViewport(p)).toBe(true);
  });

  it('PROPERTY: 500 seeded anchors, including off-edge ones — zero viewport overflow, ever', () => {
    const rand = lcg(0xCA5CAD1A);
    for (let i = 0; i < 500; i += 1) {
      const anchor = { x: rand() * (VIEWPORT.width + 200) - 100, y: rand() * (VIEWPORT.height + 200) - 100 };
      const p = placeCard(anchor, CARD, VIEWPORT, []);
      expect(inViewport(p), `anchor ${anchor.x.toFixed(0)},${anchor.y.toFixed(0)} → ${p.name}`).toBe(true);
    }
  });

  it('avoids occlusion regions when a free candidate exists', () => {
    const panel: Rect = { left: 1010, top: 60, right: 1432, bottom: 700 }; // the basin panel
    const p = placeCard({ x: 980, y: 400 }, CARD, VIEWPORT, [panel]);
    const rect = { left: p.left, top: p.top, right: p.left + CARD.width, bottom: p.top + CARD.height };
    const overlap = Math.max(0, Math.min(rect.right, panel.right) - Math.max(rect.left, panel.left)) *
      Math.max(0, Math.min(rect.bottom, panel.bottom) - Math.max(rect.top, panel.top));
    expect(overlap).toBe(0);
    expect(inViewport(p)).toBe(true);
  });

  it('is deterministic: identical inputs give identical placements', () => {
    const a = placeCard({ x: 300, y: 300 }, CARD, VIEWPORT, []);
    const b = placeCard({ x: 300, y: 300 }, CARD, VIEWPORT, []);
    expect(a).toEqual(b);
  });

  it('is sticky: the previous placement survives small anchor drift', () => {
    const first = placeCard({ x: 700, y: 500 }, CARD, VIEWPORT, []);
    const drifted = placeCard({ x: 707, y: 493 }, CARD, VIEWPORT, [], first.name);
    expect(drifted.name).toBe(first.name);
  });

  it('a phone viewport with a mid-screen anchor still fits (or honestly clamps)', () => {
    const phone = { width: 390, height: 844 };
    const card = { width: 200, height: 190 };
    const p = placeCard({ x: 195, y: 400 }, card, phone, []);
    expect(p.left).toBeGreaterThanOrEqual(SAFE);
    expect(p.left + card.width).toBeLessThanOrEqual(phone.width - SAFE);
    expect(p.top).toBeGreaterThanOrEqual(SAFE);
    expect(p.top + card.height).toBeLessThanOrEqual(phone.height - SAFE);
  });
});
