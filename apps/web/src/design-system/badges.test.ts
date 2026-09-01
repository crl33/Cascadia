import { describe, expect, it } from 'vitest';
import { SOURCE_KIND_BADGE, CATEGORY_BADGE, FRESHNESS_BADGE, badgeForSourceKind } from './badges';
import { SourceKindSchema, FloodCategorySchema, FreshnessStateSchema } from '../contracts/schemas';

describe('badge mapping', () => {
  it('covers every source kind with a printed word and a glyph', () => {
    for (const kind of SourceKindSchema.options) {
      const badge = badgeForSourceKind(kind);
      expect(badge.label.length).toBeGreaterThan(0);
      expect(badge.glyph.length).toBeGreaterThan(0);
    }
    expect(Object.keys(SOURCE_KIND_BADGE).sort()).toEqual([...SourceKindSchema.options].sort());
  });
  it('prints the doctrine words', () => {
    expect(badgeForSourceKind('OBSERVED').label).toBe('Observed');
    expect(badgeForSourceKind('OFFICIAL_FORECAST').label).toBe('Official forecast');
    expect(badgeForSourceKind('UNKNOWN').tone).toBe('neutral');
  });
  it('never gives red to anything but moderate/major categories', () => {
    for (const [cat, badge] of Object.entries(CATEGORY_BADGE)) {
      if (badge.tone === 'flood-red') expect(['moderate', 'major']).toContain(cat);
    }
    for (const badge of Object.values(SOURCE_KIND_BADGE)) expect(badge.tone).not.toBe('flood-red');
    expect(Object.keys(CATEGORY_BADGE).sort()).toEqual([...FloodCategorySchema.options].sort());
    expect(Object.keys(FRESHNESS_BADGE).sort()).toEqual([...FreshnessStateSchema.options].sort());
  });
});
