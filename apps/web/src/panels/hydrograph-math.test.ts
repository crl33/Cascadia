import { describe, expect, it } from 'vitest';
import {
  crestMarker, forecastSeriesFor, formatTickUtc, linearScale, niceStep, niceTicks, resolveBasis,
  seriesPath, thresholdOverlay, timeDomain, timeTicks, valueDomain,
} from './hydrograph-math';

const T0 = Date.parse('2026-08-22T00:00:00Z');
const HOUR = 3_600_000;

describe('resolveBasis', () => {
  it('prefers the official thresholds basis (flow-basis Green/White points chart flow)', () => {
    const choice = resolveBasis({
      thresholds: { basis: 'flow', unit: 'cfs', datum: null, action: 6000, minor: 9000, moderate: 12000, major: 14000, prov: 'p' },
      headroom: null,
      observed: { prov: 'o', truth: 'observation', stage: { value: 56.8, unit: 'ft', datum: 'NGVD29' }, flow: { value: 293, unit: 'cfs' }, valid_time: '2026-08-22T00:00:00Z' },
    });
    expect(choice).toEqual({ basis: 'flow', source: 'thresholds', reason: null });
  });
  it('falls back to headroom basis, then to the observed quantity', () => {
    expect(resolveBasis({
      thresholds: null,
      headroom: { basis: 'flow', to_category: 'action', value: null, prov: 'p' },
      observed: null,
    }).basis).toBe('flow');
    expect(resolveBasis({
      thresholds: null, headroom: null,
      observed: { prov: 'o', truth: 'observation', stage: { value: 10.5, unit: 'ft', datum: 'NGVD29' }, flow: null, valid_time: '2026-08-22T00:00:00Z' },
    })).toEqual({ basis: 'stage', source: 'observed', reason: null });
    expect(resolveBasis({
      thresholds: null, headroom: null,
      observed: { prov: 'o', truth: 'observation', stage: null, flow: { value: 293, unit: 'cfs' }, valid_time: '2026-08-22T00:00:00Z' },
    }).basis).toBe('flow');
  });
  it('declares UNKNOWN with a reason when nothing states a basis', () => {
    const choice = resolveBasis({ thresholds: null, headroom: null, observed: null });
    expect(choice.basis).toBeNull();
    expect(choice.reason).toMatch(/basis/i);
  });
});

describe('niceStep and niceTicks', () => {
  it('steps on the 1/2/5 ladder', () => {
    expect(niceStep(0.7)).toBe(1);
    expect(niceStep(1.2)).toBe(2);
    expect(niceStep(3.9)).toBe(5);
    expect(niceStep(6.4)).toBe(10);
    expect(niceStep(0.032)).toBeCloseTo(0.05, 10);
  });
  it('produces round ticks inside the domain', () => {
    expect(niceTicks(0, 32, 5)).toEqual([0, 10, 20, 30]);
    expect(niceTicks(10.2, 11.4, 5)).toEqual([10.5, 11]);
    expect(niceTicks(5, 5, 5)).toEqual([]);
  });
  it('covers the flood-stage range: the domain unions series values with thresholds', () => {
    const domain = valueDomain([10.53, 10.6, 10.64, 11.1], [23.5, 28, 30, 32]);
    expect(domain).not.toBeNull();
    expect(domain!.min).toBeLessThanOrEqual(10.53);
    expect(domain!.max).toBeGreaterThanOrEqual(32);
    const ticks = niceTicks(domain!.min, domain!.max, 5);
    expect(ticks).toEqual([10, 15, 20, 25, 30]);
    expect(ticks[ticks.length - 1]!).toBeLessThanOrEqual(domain!.max);
  });
  it('pads a degenerate single-value domain instead of collapsing', () => {
    const domain = valueDomain([6660], []);
    expect(domain!.min).toBeLessThan(6660);
    expect(domain!.max).toBeGreaterThan(6660);
    expect(valueDomain([], [])).toBeNull();
  });
});

describe('time axis', () => {
  it('domain spans all instants and pads a single instant', () => {
    expect(timeDomain([T0, T0 + 6 * HOUR])).toEqual({ min: T0, max: T0 + 6 * HOUR });
    const single = timeDomain([T0]);
    expect(single!.max - single!.min).toBe(2 * HOUR);
    expect(timeDomain([])).toBeNull();
  });
  it('ticks align to UTC boundaries with a ladder step', () => {
    const { ticks, stepMs } = timeTicks({ min: T0, max: T0 + 24 * HOUR }, 5);
    expect(stepMs).toBe(6 * HOUR);
    expect(ticks).toEqual([T0, T0 + 6 * HOUR, T0 + 12 * HOUR, T0 + 18 * HOUR, T0 + 24 * HOUR]);
  });
  it('labels are UTC: date at midnight or daily steps, time of day otherwise', () => {
    expect(formatTickUtc(T0, 6 * HOUR)).toBe('08-22');
    expect(formatTickUtc(T0 + 6 * HOUR, 6 * HOUR)).toBe('06:00');
    expect(formatTickUtc(T0 + 6 * HOUR, 24 * HOUR)).toBe('08-22');
  });
});

describe('seriesPath', () => {
  const x = linearScale({ min: 0, max: 10 }, 0, 100);
  const y = linearScale({ min: 0, max: 10 }, 100, 0);
  it('emits M/L commands in pixel space', () => {
    expect(seriesPath([{ t: 0, v: 0 }, { t: 5, v: 5 }, { t: 10, v: 10 }], x, y)).toBe('M0 100 L50 50 L100 0');
  });
  it('a null value breaks the line — a gap is never bridged', () => {
    expect(seriesPath([{ t: 0, v: 0 }, { t: 2, v: null }, { t: 5, v: 5 }, { t: 10, v: 10 }], x, y)).toBe('M0 100 M50 50 L100 0');
  });
  it('empty input renders nothing', () => {
    expect(seriesPath([], x, y)).toBe('');
  });
});

describe('thresholdOverlay honesty', () => {
  const flowThresholds = { basis: 'flow' as const, unit: 'cfs', datum: null, action: 6000, minor: 9000, moderate: 12000, major: 14000, prov: 'p' };
  it('draws matching-basis thresholds in order, skipping null categories', () => {
    const overlay = thresholdOverlay({ ...flowThresholds, moderate: null }, 'flow', 'cfs', null);
    expect(overlay.refusal).toBeNull();
    expect(overlay.lines).toEqual([
      { category: 'action', value: 6000 },
      { category: 'minor', value: 9000 },
      { category: 'major', value: 14000 },
    ]);
  });
  it('refuses a basis mismatch instead of converting', () => {
    const overlay = thresholdOverlay(flowThresholds, 'stage', 'ft', 'NGVD29');
    expect(overlay.lines).toEqual([]);
    expect(overlay.refusal).toMatch(/never converted/);
  });
  it('refuses a unit mismatch and a stage datum mismatch', () => {
    expect(thresholdOverlay(flowThresholds, 'flow', 'kcfs', null).refusal).toMatch(/kcfs/);
    const stageThresholds = { basis: 'stage' as const, unit: 'ft', datum: 'NGVD29', action: 23.5, minor: 28, moderate: 30, major: 32, prov: 'p' };
    expect(thresholdOverlay(stageThresholds, 'stage', 'ft', 'NAVD88').refusal).toMatch(/datum/);
    expect(thresholdOverlay(stageThresholds, 'stage', 'ft', 'NGVD29').lines).toHaveLength(4);
  });
  it('absent thresholds draw nothing and refuse nothing', () => {
    expect(thresholdOverlay(null, 'stage', 'ft', 'NGVD29')).toEqual({ lines: [], refusal: null });
  });
});

describe('forecastSeriesFor honesty', () => {
  const run = {
    primary: 'stage', unit: 'ft', datum: 'NGVD29',
    points: [
      { t: '2026-08-22T00:00:00Z', stage: 10.53, flow: 6550 },
      { t: '2026-08-22T06:00:00Z', stage: 10.6, flow: 6670 },
    ],
  };
  it('charts the run on its declared primary, unit and datum', () => {
    const choice = forecastSeriesFor(run, 'stage', 'ft', 'NGVD29');
    expect(choice.reason).toBeNull();
    expect(choice.points).toEqual([
      { t: Date.parse('2026-08-22T00:00:00Z'), v: 10.53 },
      { t: Date.parse('2026-08-22T06:00:00Z'), v: 10.6 },
    ]);
  });
  it('refuses to chart the secondary variable — its unit is not declared', () => {
    const choice = forecastSeriesFor(run, 'flow', 'cfs', null);
    expect(choice.points).toBeNull();
    expect(choice.reason).toMatch(/issued on stage/);
  });
  it('refuses unit and datum mismatches; absent run is silent', () => {
    expect(forecastSeriesFor(run, 'stage', 'm', 'NGVD29').reason).toMatch(/never converted/);
    expect(forecastSeriesFor(run, 'stage', 'ft', 'NAVD88').reason).toMatch(/datum/);
    expect(forecastSeriesFor(null, 'stage', 'ft', 'NGVD29')).toEqual({ points: null, reason: null });
  });
});

describe('crestMarker honesty', () => {
  const forecast = {
    prov: 'p', truth: 'authoritative_model' as const, issued_at: '2026-08-21T15:05:00Z', issuer: 'NWRFC',
    crest: { value: 11.1, unit: 'ft', datum: 'NGVD29' }, crest_valid_time: '2026-08-24T00:00:00Z', category: 'none' as const, points: 31,
  };
  it('marks the crest at its valid time on a matching axis', () => {
    const choice = crestMarker(forecast, 'stage', 'ft', 'NGVD29');
    expect(choice.reason).toBeNull();
    expect(choice.marker).toEqual({ t: Date.parse('2026-08-24T00:00:00Z'), v: 11.1 });
  });
  it('refuses unit mismatch and explains a missing crest', () => {
    expect(crestMarker(forecast, 'stage', 'm', 'NGVD29').marker).toBeNull();
    expect(crestMarker({ ...forecast, crest: null }, 'stage', 'ft', 'NGVD29').reason).toMatch(/no crest/);
    expect(crestMarker(null, 'stage', 'ft', 'NGVD29')).toEqual({ marker: null, reason: null });
  });
});
