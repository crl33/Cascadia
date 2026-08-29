import { describe, expect, it } from 'vitest';
import { sharedDatum } from './horizon-math';

const ft = (value: number, datum: string | null = 'NAVD88') => ({ value, unit: 'ft', datum });

describe('sharedDatum — the strip states one datum once, or every cell keeps its own', () => {
  it('hoists the single shared datum', () => {
    expect(sharedDatum([ft(44.4), ft(44.2), null, ft(44.3)])).toBe('NAVD88');
  });

  it('refuses to hoist when datums differ — a value must never lose a datum that is not its neighbours\'', () => {
    expect(sharedDatum([ft(44.4, 'NAVD88'), ft(12.1, 'NGVD29')])).toBeNull();
  });

  it('refuses to hoist when only some quantities carry a datum', () => {
    expect(sharedDatum([ft(44.4), ft(500, null)])).toBeNull();
  });

  it('flow-only strips have nothing to hoist', () => {
    expect(sharedDatum([{ value: 500, unit: 'cfs' }, null])).toBeNull();
    expect(sharedDatum([null, undefined])).toBeNull();
  });
});
