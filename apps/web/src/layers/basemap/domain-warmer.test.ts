import { describe, expect, it } from 'vitest';
import { bootTiles, domainTiles } from './domain-warmer';

describe('domain warmer — the whole bounded pyramid is enumerable and small', () => {
  it('tiles at a zoom cover the domain and only the domain', () => {
    const z8 = domainTiles(8);
    expect(z8.length).toBeGreaterThan(20);
    expect(z8.length).toBeLessThan(120);
    for (const t of z8) {
      expect(t.z).toBe(8);
      expect(t.x).toBeGreaterThanOrEqual(0);
      expect(t.y).toBeGreaterThanOrEqual(0);
      expect(t.x).toBeLessThan(2 ** 8);
      expect(t.y).toBeLessThan(2 ** 8);
    }
  });

  it('deeper zooms have ~4x the tiles — the math is a real pyramid', () => {
    const a = domainTiles(8).length;
    const b = domainTiles(9).length;
    expect(b / a).toBeGreaterThan(3);
    expect(b / a).toBeLessThan(5);
  });

  it('the BOOT set (z5–z9) is bounded: complete availability at a one-time cost', () => {
    const tiles = bootTiles();
    // ~10–15 MB at ~40 KB/tile — a real but honest loading-screen stage
    expect(tiles.length).toBeGreaterThan(150);
    expect(tiles.length).toBeLessThan(450);
    expect(new Set(tiles.map((t) => `${t.z}/${t.y}/${t.x}`)).size).toBe(tiles.length); // no dupes
  });
});
