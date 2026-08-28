import { describe, expect, it } from 'vitest';
import { basinEdge } from './style';
import { COLOR } from '../../design-system/tokens';
import { FloodCategorySchema } from '../../contracts/schemas';

const base = { lod: 'state' as const, band: 'orbital' as const, selected: false, hovered: false, category: 'none' as const, alerted: false, hasBasinLod: false };

describe('basinEdge', () => {
  it('is subtle at overview bands and hidden below them unless selected', () => {
    expect(basinEdge(base).alpha).toBeLessThan(0.4);
    expect(basinEdge({ ...base, band: 'basin' }).show).toBe(false);
    expect(basinEdge({ ...base, band: 'river', selected: true }).show).toBe(true);
  });
  it('lets the basin-LOD outline replace the state-LOD one for the selected basin', () => {
    expect(basinEdge({ ...base, selected: true, hasBasinLod: true }).show).toBe(false);
    const strong = basinEdge({ ...base, lod: 'basin', selected: true, band: 'basin', hasBasinLod: true });
    expect(strong.show).toBe(true);
    expect(strong.alpha).toBeGreaterThan(0.8);
    expect(strong.fadeIn).toBe(true);
    expect(basinEdge({ ...base, lod: 'basin', selected: false }).show).toBe(false);
  });
  it('carries an active alert as a DASH, never as a colour', () => {
    // presence: an alerted basin is dashed wherever its edge shows, and slightly firmer at rest
    const rest = basinEdge({ ...base, alerted: true });
    expect(rest.dashed).toBe(true);
    expect(rest.widthPx).toBeGreaterThan(basinEdge(base).widthPx);
    expect(basinEdge({ ...base, alerted: true, selected: true }).dashed).toBe(true);
    expect(basinEdge({ ...base, lod: 'basin', selected: true, band: 'basin', alerted: true }).dashed).toBe(true);
    // and the colour channel is untouched: an Air Quality Alert must not paint flood-amber —
    // the alerted edge keeps exactly the category colour of the un-alerted one
    for (const category of FloodCategorySchema.options) {
      expect(basinEdge({ ...base, alerted: true, category }).color)
        .toBe(basinEdge({ ...base, category }).color);
    }
    // no alert, no dash
    expect(basinEdge(base).dashed).toBe(false);
    expect(basinEdge({ ...base, selected: true }).dashed).toBe(false);
  });
  it('earns red only from moderate/major and renders unknown as neutral, never calm', () => {
    for (const category of FloodCategorySchema.options) {
      const style = basinEdge({ ...base, category });
      if (style.color === COLOR.floodRed) expect(['moderate', 'major']).toContain(category);
      if (category === 'unknown') expect(style.color).toBe(COLOR.neutralUnknown);
    }
  });
});
