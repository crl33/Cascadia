import { describe, expect, it } from 'vitest';
import { riverLine } from './style';

const base = { mainstem: false, band: 'state' as const, inSelectedBasin: false, intensity: null };

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
  it('flow intensity swells presence — width and alpha, never hue', () => {
    const calm = riverLine({ ...base, mainstem: true, intensity: 0.1 });
    const swollen = riverLine({ ...base, mainstem: true, intensity: 0.95 });
    expect(swollen.widthPx).toBeGreaterThan(calm.widthPx);
    expect(swollen.alpha).toBeGreaterThan(calm.alpha);
    expect(swollen.color).toEqual(calm.color); // the non-colour carrier rule (§7.2)
    expect(swollen.alpha).toBeLessThanOrEqual(0.95);
  });
  it('null intensity IS the cartographic base — unknown never renders as calm or as anything', () => {
    expect(riverLine(base)).toEqual(riverLine({ ...base, intensity: null }));
    // and a zero-intensity river (a defensible p0) sits exactly on the base too: the base
    // width is the "nothing to add" appearance, so p0 must not shrink below the map
    expect(riverLine({ ...base, intensity: 0 }).widthPx).toBe(riverLine(base).widthPx);
  });
  it('intensity outside 0-1 is clamped, not amplified', () => {
    const over = riverLine({ ...base, mainstem: true, intensity: 4 });
    expect(over.widthPx).toBe(riverLine({ ...base, mainstem: true, intensity: 1 }).widthPx);
    expect(riverLine({ ...base, intensity: -1 }).widthPx).toBe(riverLine(base).widthPx);
  });

  it('two registers, separated (§10): geometry is the water hue, and it never changes', () => {
    const s = riverLine({ mainstem: true, band: 'local', inSelectedBasin: true, intensity: 0.95 });
    expect(s.color).toEqual({ h: 203, s: 62, l: 52 }); // COLOR.water — physical register
  });

  it('glow is STATE, not proximity: an unselected calm mainstem near the ground stays plain', () => {
    const calm = riverLine({ mainstem: true, band: 'river', inSelectedBasin: false, intensity: 0.3 });
    expect(calm.glow).toBe(false);
    const swollen = riverLine({ mainstem: true, band: 'river', inSelectedBasin: false, intensity: 0.8 });
    expect(swollen.glow).toBe(true); // high day-of-year percentile earns presence
    const selected = riverLine({ mainstem: true, band: 'local', inSelectedBasin: true, intensity: null });
    expect(selected.glow).toBe(true); // selection earns it too
  });

  it('at LOCAL the photography carries the channel — the annotation steps back', () => {
    const river = riverLine({ mainstem: true, band: 'river', inSelectedBasin: false, intensity: null });
    const local = riverLine({ mainstem: true, band: 'local', inSelectedBasin: false, intensity: null });
    expect(local.alpha).toBeLessThan(river.alpha);
  });
});
