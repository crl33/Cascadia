/**
 * The doctrine limits on the first Cascade-derived thing the globe says, as tests.
 *
 * These are not style preferences. VISUAL_TRUTH_DOCTRINE §7.1 makes the red-family rule
 * non-negotiable ("the A/B-only rule is not negotiable"), §7.2 makes a non-colour carrier
 * mandatory, and the unknown register forbids a missing value reading as a calm one. Each gets a
 * test that fails if the rule is relaxed.
 */
import { describe, expect, it } from 'vitest';
import { susceptibilityFill, type SusceptibilitySemantic } from './style';
import { COLOR } from '../../design-system/tokens';
import type { SurfaceLevel } from '../../contracts/schemas';
import type { Band } from '../../scene/bands';

const LEVELS: SurfaceLevel[] = ['low', 'moderate', 'high', 'very_high', 'unknown'];
const BANDS: Band[] = ['orbital', 'state', 'basin', 'river', 'local'];

const base = (over: Partial<SusceptibilitySemantic> = {}): SusceptibilitySemantic => ({
  state: 'moderate',
  experimental: true,
  confidence: 'moderate',
  band: 'state',
  selected: false,
  reason: null,
  ...over,
});

describe('susceptibility fill', () => {
  it('never reaches the red family, at any level or confidence', () => {
    // §7.1: "C-class values — and EXPERIMENTAL above all — never reach the red family." An
    // official `major` on the same basin IS red; if this surface could reach it too, the globe
    // would show an uncalibrated index and an official warning in the same colour.
    for (const state of LEVELS) {
      for (const confidence of ['high', 'moderate', 'low', 'unknown'] as const) {
        for (const selected of [true, false]) {
          const fill = susceptibilityFill(base({ state, confidence, selected }));
          expect(fill.color).not.toEqual(COLOR.floodRed);
          expect(fill.color.h).not.toBeCloseTo(COLOR.floodRed.h, 0);
        }
      }
    }
  });

  it('escalates only as far as amber, and stops', () => {
    expect(susceptibilityFill(base({ state: 'low' })).color).toEqual(COLOR.cyan);
    expect(susceptibilityFill(base({ state: 'moderate' })).color).toEqual(COLOR.amberWatch);
    expect(susceptibilityFill(base({ state: 'high' })).color).toEqual(COLOR.amberElevated);
    // `very_high` shares the tone with `high` deliberately: the palette runs out before red.
    expect(susceptibilityFill(base({ state: 'very_high' })).color).toEqual(COLOR.amberElevated);
  });

  it('the hatch is the ATTENTION texture; the experimental register always keeps its words', () => {
    // Owner pass 2026-08-31: a LOW basin under a full diagonal grid was scene-wide noise.
    // §7.2 still holds — every experimental level carries its badge and label words (the
    // non-colour carriers); the map hatch is reserved for levels that demand attention.
    for (const state of LEVELS.filter((l) => l !== 'unknown')) {
      const fill = susceptibilityFill(base({ state }));
      const demandsAttention = state === 'moderate' || state === 'high' || state === 'very_high';
      expect(fill.striped).toBe(demandsAttention);
      expect(fill.hatchAlpha > 0).toBe(demandsAttention);
      expect(fill.badge).toBe('Cascadia assessment');
      expect(fill.labelText).toContain('EXPERIMENTAL');
    }
  });

  it('never formats itself as a probability', () => {
    // The label may — and does — say the words "not a probability". What it must never do is
    // present a NUMBER that reads as one, which is what §"experimental" forbids: "never a number
    // formatted as a probability". So the check is on the numerals, not on the vocabulary.
    for (const state of LEVELS) {
      const { labelText } = susceptibilityFill(base({ state }));
      expect(labelText).not.toMatch(/\d/);
      expect(labelText).not.toMatch(/\b(chance|likelihood|odds)\b/i);
    }
    expect(susceptibilityFill(base()).labelText).toContain('not a probability');
  });

  it('renders unknown as incomplete, never as calm', () => {
    // The unknown register: "neutral, incomplete-looking ... no fill saturation ... never calm,
    // green or zero". A basin the backend refused must not be indistinguishable from a quiet one.
    const fill = susceptibilityFill(base({ state: 'unknown', reason: 'no day-of-year climatology stored' }));
    expect(fill.alpha).toBe(0);
    expect(fill.outlineOnly).toBe(true);
    expect(fill.color).toEqual(COLOR.neutralUnknown);
    expect(fill.color).not.toEqual(COLOR.cyan); // cyan is the NOMINAL tone — unknown is not nominal
    expect(fill.labelText).toContain('unknown');
  });

  it('prints the backend reason rather than inventing one', () => {
    const reason = 'no daily mean within 6 h of 2026-08-25T07:00:00+00:00';
    expect(susceptibilityFill(base({ state: 'unknown', reason })).labelText).toContain(reason);
    // and says nothing extra when the backend gave no reason
    expect(susceptibilityFill(base({ state: 'unknown', reason: null })).labelText).not.toContain('—');
  });

  it('fades with confidence without ever restating the level as a tone', () => {
    const tones = new Set<string>();
    let previous = Infinity;
    for (const confidence of ['high', 'moderate', 'low', 'unknown'] as const) {
      const fill = susceptibilityFill(base({ confidence }));
      expect(fill.alpha).toBeLessThan(previous);
      previous = fill.alpha;
      tones.add(JSON.stringify(fill.color));
    }
    expect(tones.size).toBe(1); // confidence moves alpha only
  });

  it('is a wash for the overview bands and yields close in', () => {
    for (const band of BANDS) {
      const fill = susceptibilityFill(base({ band }));
      const overview = band === 'orbital' || band === 'state' || band === 'basin';
      expect(fill.show).toBe(overview);
    }
  });

  it('stays inside a wash — it never becomes an opaque fill that hides the Earth', () => {
    // §7.1: "The Earth still looks like Earth ... Risk modifies the information layer ... never
    // the landscape's own colour."
    for (const state of LEVELS) {
      for (const confidence of ['high', 'moderate', 'low', 'unknown'] as const) {
        expect(susceptibilityFill(base({ state, confidence, selected: true })).alpha).toBeLessThanOrEqual(0.4);
      }
    }
  });

  it('is total: every level and band produces a fill without throwing', () => {
    for (const state of LEVELS) {
      for (const band of BANDS) {
        expect(() => susceptibilityFill(base({ state, band }))).not.toThrow();
      }
    }
  });
});

describe('the restrained treatment (design direction 2026-08-28)', () => {
  it('where the hatch appears it stays stronger than the wash; the wash never masks', () => {
    for (const state of ['moderate', 'high', 'very_high'] as const) {
      for (const confidence of ['high', 'moderate', 'low', 'unknown'] as const) {
        const fill = susceptibilityFill(base({ state, confidence }));
        expect(fill.hatchAlpha).toBeGreaterThan(fill.alpha); // attention levels: carrier over wash
      }
    }
    for (const state of ['low', 'moderate', 'high', 'very_high'] as const) {
      for (const confidence of ['high', 'moderate', 'low', 'unknown'] as const) {
        expect(susceptibilityFill(base({ state, confidence })).alpha).toBeLessThanOrEqual(0.20 * 1.25);
      }
    }
  });
  it('gives UNKNOWN no hatch either — outline-only stays the whole treatment', () => {
    const fill = susceptibilityFill(base({ state: 'unknown' }));
    expect(fill.hatchAlpha).toBe(0);
    expect(fill.outlineOnly).toBe(true);
  });
});
