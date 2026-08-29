import { describe, expect, it } from 'vitest';
import { BAND_BUDGET, selectLabels, type LabelEntry, type ScreenProjection } from './select';

const entry = (over: Partial<LabelEntry> & { name: string }): LabelEntry => ({
  kind: 'town', tier: 2, lon: -122, lat: 48, ...over,
});

describe('selectLabels — class semantics', () => {
  it('orbital shows basin names only — orientation, nothing else', () => {
    const labels = [
      entry({ name: 'Skagit', kind: 'basin', tier: 1, lon: -121.5 }),
      entry({ name: 'Seattle', kind: 'city', tier: 1, lon: -122.33, lat: 47.6 }),
      entry({ name: 'Skagit River', kind: 'river', tier: 2, lon: -121.8 }),
    ];
    expect(selectLabels(labels, 'orbital', null).map((l) => l.name)).toEqual(['Skagit']);
  });

  it('A BASIN IS NOT A PLACE: basin labels vanish at river and local bands — the river wins its valley', () => {
    const labels = [
      entry({ name: 'Skagit', kind: 'basin', tier: 1, lon: -121.3, lat: 48.62 }),
      entry({ name: 'Skagit River', kind: 'river', tier: 2, lon: -121.8, lat: 48.45 }),
    ];
    for (const band of ['river', 'local'] as const) {
      const kinds = selectLabels(labels, band, null).map((l) => l.kind);
      expect(kinds).not.toContain('basin');
      expect(kinds).toContain('river');
    }
    // …while at basin band both may coexist (their anchors are curated apart)
    expect(selectLabels(labels, 'basin', null).map((l) => l.kind).sort()).toEqual(['basin', 'river']);
  });

  it('collision standing: the basin loses to everything, the city to nothing', () => {
    // all four at the SAME anchor — only the strongest survives spacing
    const at = { lon: -122.2, lat: 47.6 };
    const labels = [
      entry({ name: 'Cedar / Lake Washington', kind: 'basin', tier: 1, ...at }),
      entry({ name: 'Seattle', kind: 'city', tier: 1, ...at }),
      entry({ name: 'Cedar River', kind: 'river', tier: 2, ...at }),
      entry({ name: 'Renton', kind: 'town', tier: 2, ...at }),
    ];
    expect(selectLabels(labels, 'basin', null).map((l) => l.name)).toEqual(['Seattle']);
  });

  it('lakes are water, shown from river band on their own feature', () => {
    const lake = entry({ name: 'Lake Washington', kind: 'water', tier: 2, lon: -122.25, lat: 47.62 });
    expect(selectLabels([lake], 'basin', null)).toEqual([]);
    expect(selectLabels([lake], 'river', null).map((l) => l.name)).toEqual(['Lake Washington']);
  });

  it('screen projection culls off-viewport anchors and the chrome bands', () => {
    const projection: ScreenProjection = {
      width: 1000,
      height: 800,
      project: (lon) => (lon < -122.5 ? null : { x: 500, y: lon > -121 ? 780 : 400 }),
    };
    const labels = [
      entry({ name: 'OffGlobe', kind: 'city', tier: 1, lon: -123 }),
      entry({ name: 'InChrome', kind: 'city', tier: 1, lon: -120.5 }),
      entry({ name: 'Visible', kind: 'city', tier: 1, lon: -122 }),
    ];
    expect(selectLabels(labels, 'state', null, projection).map((l) => l.name)).toEqual(['Visible']);
  });

  it('projected spacing keeps 38 px between accepted anchors, resolved by class standing', () => {
    const projection: ScreenProjection = {
      width: 1000,
      height: 800,
      project: (_lon, lat) => ({ x: 500, y: 400 + (lat - 48) * 100 }), // 0.1° = 10 px
    };
    const labels = [
      entry({ name: 'Skagit', kind: 'basin', tier: 1, lat: 48.0 }),
      entry({ name: 'Mount Vernon', kind: 'town', tier: 2, lat: 48.2 }), // 20 px away — collides
    ];
    expect(selectLabels(labels, 'basin', null, projection).map((l) => l.name)).toEqual(['Mount Vernon']);
  });

  it('never exceeds the band budget', () => {
    const many = Array.from({ length: 60 }, (_, i) =>
      entry({ name: `Town ${i}`, tier: 2, lon: -124 + i * 0.5, lat: 46 + (i % 7) * 0.5 }),
    );
    for (const band of ['state', 'basin', 'river', 'local'] as const) {
      expect(selectLabels(many, band, null).length).toBeLessThanOrEqual(BAND_BUDGET[band]);
    }
  });

  it('is deterministic without a projection', () => {
    const labels = Array.from({ length: 20 }, (_, i) =>
      entry({ name: `P${i}`, tier: 2, lon: -123 + i * 0.3, lat: 47 + (i % 5) * 0.3 }),
    );
    expect(selectLabels(labels, 'basin', null)).toEqual(selectLabels([...labels].reverse(), 'basin', null));
  });
});
