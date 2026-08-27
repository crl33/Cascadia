import { describe, expect, it } from 'vitest';
import { formatCount, formatMultiplier, formatOrdinal } from './format';

describe('Tier 0 display formatting preserves the statement', () => {
  it('renders growth as a multiplier at two decimals', () => {
    expect(formatMultiplier(1.3726)).toBe('1.37×');
    expect(formatMultiplier(2.0997)).toBe('2.10×');
    expect(formatMultiplier(1)).toBe('1.00×');
  });

  it('renders a rank as an ordinal, including the English teens', () => {
    expect(formatOrdinal(1)).toBe('1st');
    expect(formatOrdinal(2)).toBe('2nd');
    expect(formatOrdinal(3)).toBe('3rd');
    expect(formatOrdinal(4)).toBe('4th');
    expect(formatOrdinal(11)).toBe('11th');
    expect(formatOrdinal(12)).toBe('12th');
    expect(formatOrdinal(13)).toBe('13th');
    expect(formatOrdinal(21)).toBe('21st');
    expect(formatOrdinal(101)).toBe('101st');
    expect(formatOrdinal(111)).toBe('111th');
    expect(formatOrdinal(2651)).toBe('2,651st');
    expect(formatOrdinal(34957)).toBe('34,957th');
  });

  it('never rounds a sample size', () => {
    expect(formatCount(34957)).toBe('34,957');
    expect(formatCount(491)).toBe('491');
  });
});
