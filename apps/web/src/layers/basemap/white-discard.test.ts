import { describe, expect, it } from 'vitest';
import { samplesAreWhite } from './white-discard';

const rgba = (pixels: number[][]): Uint8ClampedArray =>
  new Uint8ClampedArray(pixels.flatMap(([r, g, b]) => [r!, g!, b!, 255]));

describe('samplesAreWhite — a void is uniform white; real ground never is', () => {
  it('a service void (uniform 255, with JPEG ringing down to 254) discards', () => {
    expect(samplesAreWhite(rgba(Array.from({ length: 9 }, () => [255, 255, 255])))).toBe(true);
    expect(samplesAreWhite(rgba(Array.from({ length: 9 }, () => [254, 255, 254])))).toBe(true);
  });

  it('one shadowed region keeps the tile — snowfields have texture', () => {
    const snow = Array.from({ length: 9 }, () => [252, 252, 253]);
    snow[4] = [231, 236, 241]; // a crevasse shadow in the center ninth
    expect(samplesAreWhite(rgba(snow))).toBe(false);
  });

  it('ordinary ground is nowhere near the floor', () => {
    expect(samplesAreWhite(rgba(Array.from({ length: 9 }, () => [92, 118, 77])))).toBe(false);
  });

  it('an empty read never discards', () => {
    expect(samplesAreWhite(new Uint8ClampedArray(0))).toBe(false);
  });
});
