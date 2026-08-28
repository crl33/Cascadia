/**
 * River marker styling: the trend note, and the refusal semantics it must respect.
 *
 * `trend` is `method:rate-of-rise@2.0.0`, which REFUSES on tidal or unmeasured gauges rather than
 * guessing — so the marker's obligations are as much about absence as presence: a refused trend
 * prints nothing, and a printed trend always carries a word beside its glyph (§7.2: never a
 * colour or a bare symbol as the only carrier).
 */
import { describe, expect, it } from 'vitest';
import { riverMarker, type MarkerSemantic } from './style';

const base = (over: Partial<MarkerSemantic> = {}): MarkerSemantic => ({
  name: 'Skagit River near Mount Vernon',
  category: 'none',
  freshness: 'current',
  selected: true,
  hovered: false,
  trend: null,
  ...over,
});

describe('river marker trend note', () => {
  it('prints glyph, word and rate together — never the glyph alone', () => {
    const style = riverMarker(base({ trend: { direction: 'rising', rate: { value: 0.31, unit: 'ft/h' } } }));
    expect(style.labelText).toContain('↗ rising 0.31 ft/h');
  });

  it('a falling trend prints its own glyph and word', () => {
    const style = riverMarker(base({ trend: { direction: 'falling', rate: { value: -0.12, unit: 'ft/h' } } }));
    expect(style.labelText).toContain('↘ falling 0.12 ft/h');
    expect(style.labelText).not.toContain('-0.12'); // the direction word carries the sign
  });

  it('steady prints as steady, not as silence', () => {
    const style = riverMarker(base({ trend: { direction: 'steady', rate: { value: 0.01, unit: 'ft/h' } } }));
    expect(style.labelText).toContain('→ steady');
  });

  it('a REFUSED trend prints nothing — an absent statement stays absent', () => {
    // rate-of-rise refuses on tidal gauges rather than reporting a tide as a rise. The label must
    // not say "unknown" in that slot: a note on every quiet marker trains readers to ignore it.
    for (const trend of [null, { direction: 'unknown' as const, rate: null }]) {
      const style = riverMarker(base({ trend }));
      expect(style.labelText).not.toMatch(/↗|↘|→|unknown trend/);
    }
  });

  it('a trend with no rate still prints direction, without inventing a number', () => {
    const style = riverMarker(base({ trend: { direction: 'rising', rate: null } }));
    expect(style.labelText).toContain('↗ rising');
    expect(style.labelText).not.toMatch(/rising \d/);
  });

  it('the category word survives beside the trend — neither replaces the other', () => {
    const style = riverMarker(base({ category: 'action', trend: { direction: 'rising', rate: { value: 0.5, unit: 'ft/h' } } }));
    expect(style.labelText).toMatch(/ACTION/i);
    expect(style.labelText).toContain('rising');
  });
});
