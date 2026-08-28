import { describe, expect, it } from 'vitest';
import { precipPixel } from './style';

describe('precipPixel', () => {
  it('dry is transparent — no texture IS the rendering of 0.0 mm measured', () => {
    expect(precipPixel(0).a).toBe(0);
    expect(precipPixel(0.04).a).toBe(0); // below half a quantization step
  });
  it('unknown is transparent too: painting a colour would claim a measurement', () => {
    expect(precipPixel(null).a).toBe(0);
    expect(precipPixel(Number.NaN).a).toBe(0);
  });
  it('the ramp is monotone in alpha and saturates instead of claiming precision', () => {
    const trace = precipPixel(0.2);
    const light = precipPixel(1);
    const heavy = precipPixel(8);
    const extreme = precipPixel(40);
    expect(trace.a).toBeGreaterThan(0);
    expect(light.a).toBeGreaterThan(trace.a);
    expect(heavy.a).toBeGreaterThan(light.a);
    expect(extreme.a).toBe(heavy.a); // saturated: 40 mm/h does not pretend to out-render 8
    expect(heavy.a).toBeLessThanOrEqual(150); // a wash, not a curtain
  });
  it('stays in the blue-teal family at every intensity — observed rain is never red', () => {
    for (const mm of [0.1, 0.5, 2, 8, 40]) {
      const px = precipPixel(mm);
      expect(px.b).toBeGreaterThan(px.r);
      expect(px.g).toBeGreaterThan(px.r);
    }
  });
});
