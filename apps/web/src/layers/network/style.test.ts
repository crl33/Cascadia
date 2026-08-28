import { describe, expect, it } from 'vitest';
import { riverLine } from './style';

const base = { mainstem: false, band: 'state' as const, inSelectedBasin: false };

describe('riverLine', () => {
  it('draws mainstems from orbit and the full network from the state band down', () => {
    expect(riverLine({ ...base, band: 'orbital' }).show).toBe(false);
    expect(riverLine({ ...base, band: 'orbital', mainstem: true }).show).toBe(true);
    expect(riverLine(base).show).toBe(true);
    expect(riverLine({ ...base, band: 'basin' }).show).toBe(true);
  });
  it('weights the spine over the tributaries, structurally not chromatically', () => {
    const stem = riverLine({ ...base, mainstem: true });
    const trib = riverLine(base);
    expect(stem.widthPx).toBeGreaterThan(trib.widthPx);
    expect(stem.alpha).toBeGreaterThan(trib.alpha);
    expect(stem.color).toEqual(trib.color); // one hue: cartographic water, no state encoded
  });
  it('brightens the selected basin without ever saturating past legibility', () => {
    const out = riverLine({ ...base, mainstem: true, inSelectedBasin: true });
    expect(out.alpha).toBeGreaterThan(riverLine({ ...base, mainstem: true }).alpha);
    expect(out.alpha).toBeLessThanOrEqual(0.95);
  });
});
