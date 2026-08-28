import { describe, expect, it } from 'vitest';
import { BAND_BUDGET, selectLabels, type LabelEntry } from './select';

const entry = (over: Partial<LabelEntry> & { name: string }): LabelEntry => ({
  kind: 'town', tier: 2, lon: -122, lat: 48, ...over,
});

describe('selectLabels', () => {
  it('orbital shows basin names only — orientation, nothing else', () => {
    const labels = [
      entry({ name: 'Skagit', kind: 'basin', tier: 1, lon: -121.5 }),
      entry({ name: 'Seattle', kind: 'city', tier: 1, lon: -122.33, lat: 47.6 }),
      entry({ name: 'Skagit River', kind: 'river', tier: 2, lon: -121.8 }),
    ];
    expect(selectLabels(labels, 'orbital', null).map((l) => l.name)).toEqual(['Skagit']);
  });

  it('band eligibility follows the editorial tier: a tier-3 town waits for the river band', () => {
    const labels = [entry({ name: 'Sultan', tier: 3 })];
    expect(selectLabels(labels, 'basin', null)).toEqual([]);
    expect(selectLabels(labels, 'river', null).map((l) => l.name)).toEqual(['Sultan']);
  });

  it('spacing drops the later candidate, and class priority decides who is later', () => {
    // a river and a town at the same anchor: the river (P3) beats the town (P4)
    const labels = [
      entry({ name: 'Carnation', kind: 'town', tier: 2, lon: -121.914, lat: 47.648 }),
      entry({ name: 'Snoqualmie River', kind: 'river', tier: 2, lon: -121.915, lat: 47.649 }),
    ];
    expect(selectLabels(labels, 'basin', null).map((l) => l.name)).toEqual(['Snoqualmie River']);
  });

  it('the selected basin\'s labels outrank the same class elsewhere', () => {
    const labels = [
      entry({ name: 'Green River', kind: 'river', tier: 2, basin_id: 'basin:green-duwamish', lon: -122.2, lat: 47.3 }),
      entry({ name: 'Skagit River', kind: 'river', tier: 2, basin_id: 'basin:skagit', lon: -122.21, lat: 47.31 }),
    ];
    const chosen = selectLabels(labels, 'basin', 'basin:skagit');
    expect(chosen.map((l) => l.name)).toEqual(['Skagit River']); // spacing keeps one; selection decides which
  });

  it('never exceeds the band budget, whatever the candidate count', () => {
    const many = Array.from({ length: 60 }, (_, i) =>
      entry({ name: `Town ${i}`, tier: 1, lon: -124 + i * 0.5, lat: 46 + (i % 7) * 0.5 }),
    );
    for (const band of ['state', 'basin', 'river', 'local'] as const) {
      expect(selectLabels(many, band, null).length).toBeLessThanOrEqual(BAND_BUDGET[band]);
    }
  });

  it('is deterministic: the same inputs give the same labels in the same order', () => {
    const labels = Array.from({ length: 20 }, (_, i) =>
      entry({ name: `P${i}`, tier: 2, lon: -123 + i * 0.3, lat: 47 + (i % 5) * 0.3 }),
    );
    const a = selectLabels(labels, 'basin', null);
    const b = selectLabels([...labels].reverse(), 'basin', null);
    expect(a).toEqual(b);
  });
});
