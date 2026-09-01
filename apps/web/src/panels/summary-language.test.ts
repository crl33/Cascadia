import { describe, expect, it } from 'vitest';
import { currentSentence, forcingSentence, hazardSentence, susceptibilityHeadline } from './summary-language';

describe('summary language — sentences a first-time reader understands, derived never invented', () => {
  it('susceptibility states become plain headlines; unknown stays unknown', () => {
    expect(susceptibilityHeadline('low')).toBe('Low flood susceptibility');
    expect(susceptibilityHeadline('very_high')).toBe('Very high flood susceptibility');
    expect(susceptibilityHeadline('unknown')).toBe('Flood susceptibility unknown');
  });

  it('the CURRENT sentence combines direction and seasonal standing', () => {
    const level = { multiple: { multiple: 0.29, reference_percentile: 95 } } as never;
    const change = { direction: 'steady', window_h: 24 } as never;
    expect(currentSentence(level, change)).toBe('River steady · well below seasonal high flows');
    expect(currentSentence(null, { direction: 'rising', window_h: 24 } as never)).toBe('River rising');
    expect(currentSentence(null, null)).toBeNull();
  });

  it('seasonal standing bands are honest about the multiple', () => {
    const at = (m: number) => currentSentence({ multiple: { multiple: m, reference_percentile: 95 } } as never, null);
    expect(at(0.29)).toContain('well below');
    expect(at(0.7)).toContain('below');
    expect(at(1.0)).toContain('near');
    expect(at(1.5)).toContain('above');
  });

  it('forcing speaks amounts, and unknown keeps the document reason', () => {
    expect(forcingSentence({ state: 'low', value: { value: 11.6, unit: 'mm' }, horizon_h: 72 } as never)).toBe(
      'Little rain expected — 11.6 mm over 72 h',
    );
    expect(forcingSentence({ state: 'unknown', reason: 'QPF missing for this window' } as never)).toBe(
      'QPF missing for this window',
    );
  });

  it('the official outlook keeps official words', () => {
    expect(hazardSentence({ official_category: 'none' } as never)).toBe('No flood stages forecast');
    expect(hazardSentence({ official_category: 'minor' } as never)).toBe('Minor flooding forecast');
    expect(hazardSentence({ official_category: 'unknown', reason: 'no forecast at this point' } as never)).toBe(
      'no forecast at this point',
    );
  });
});
