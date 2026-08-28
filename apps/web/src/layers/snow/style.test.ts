import { describe, expect, it } from 'vitest';
import { snowPixel } from './style';

describe('snowPixel', () => {
  it('bare ground is transparent — no veil IS the rendering of 0 mm SWE', () => {
    expect(snowPixel(0).a).toBe(0);
    expect(snowPixel(0.9).a).toBe(0); // sub-millimetre patchiness is analysis noise
  });
  it('unknown is transparent: painting would claim an analysis that does not exist', () => {
    expect(snowPixel(null).a).toBe(0);
    expect(snowPixel(Number.NaN).a).toBe(0);
  });
  it('the ramp is monotone and saturates at deep pack', () => {
    const dusting = snowPixel(5);
    const pack = snowPixel(100);
    const deep = snowPixel(400);
    const extreme = snowPixel(2000);
    expect(dusting.a).toBeGreaterThan(0);
    expect(pack.a).toBeGreaterThan(dusting.a);
    expect(deep.a).toBeGreaterThan(pack.a);
    expect(extreme.a).toBe(deep.a);
    expect(deep.a).toBeLessThanOrEqual(140); // a veil, never a curtain
  });
  it('stays cold — white-blue at every depth, blue never below the other channels', () => {
    for (const mm of [2, 50, 400, 2000]) {
      const px = snowPixel(mm);
      expect(px.b).toBeGreaterThanOrEqual(px.r);
      expect(px.b).toBeGreaterThanOrEqual(px.g);
    }
  });
});
