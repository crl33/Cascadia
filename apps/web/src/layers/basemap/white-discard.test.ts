import { describe, expect, it } from 'vitest';
import { samplesAreWhite } from './white-discard';

const rgba = (pixels: number[][]): Uint8ClampedArray =>
  new Uint8ClampedArray(pixels.flatMap(([r, g, b]) => [r!, g!, b!, 255]));

describe('samplesAreWhite — a tile with a SUBSTANTIAL void falls back whole (2026-09-01 rule)', () => {
  it('a full service void discards', () => {
    expect(samplesAreWhite(rgba(Array.from({ length: 9 }, () => [255, 255, 255])))).toBe(true);
  });

  it('a HALF-void coastal tile discards whole — soft parent beats fringes/blocks', () => {
    const half = Array.from({ length: 9 }, (_, i) => (i < 4 ? [255, 255, 255] : [40, 70, 110]));
    expect(samplesAreWhite(rgba(half))).toBe(true);
  });

  it('one lone blown-bright region keeps the tile — a cloud must not soften real land', () => {
    const cloudCorner = Array.from({ length: 9 }, () => [120, 140, 100]);
    cloudCorner[0] = [255, 255, 255];
    expect(samplesAreWhite(rgba(cloudCorner))).toBe(false);
  });

  it('textured snow keeps the tile — shadows pull the regions below the floor', () => {
    expect(samplesAreWhite(rgba(Array.from({ length: 9 }, () => [246, 248, 251])))).toBe(false);
  });

  it('ordinary ground is nowhere near the floor; an empty read never discards', () => {
    expect(samplesAreWhite(rgba(Array.from({ length: 9 }, () => [92, 118, 77])))).toBe(false);
    expect(samplesAreWhite(new Uint8ClampedArray(0))).toBe(false);
  });
});
