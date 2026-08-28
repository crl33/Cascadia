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
    primary: 'stage', unit: 'ft', stage_datum: 'NGVD29',
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
  it('refuses to chart the secondary column — the run is issued on its primary', () => {
    const choice = forecastSeriesFor(run, 'flow', 'cfs', null);
    expect(choice.points).toBeNull();
    expect(choice.reason).toMatch(/issued on stage/);
  });
  it('refuses unit and datum mismatches; absent run is silent', () => {
    expect(forecastSeriesFor(run, 'stage', 'm', 'NGVD29').reason).toMatch(/never converted/);
    expect(forecastSeriesFor(run, 'stage', 'ft', 'NAVD88').reason).toMatch(/datum/);
    expect(forecastSeriesFor(null, 'stage', 'ft', 'NGVD29')).toEqual({ points: null, reason: null });
  });
  it('refuses a stage overlay when the run declares no datum — a datum is never assumed', () => {
    const undeclared = { ...run, stage_datum: null };
    const choice = forecastSeriesFor(undeclared, 'stage', 'ft', 'NGVD29');
    expect(choice.points).toBeNull();
    expect(choice.reason).toMatch(/never assumed/);
  });
  it('charts a flow-primary run on the flow axis; its stage datum is irrelevant there', () => {
    // AUBW1 shape: issued on flow in cfs, with a stage column riding along in NGVD29. The datum
    // describes that stage column only and must not gate the flow overlay (ADR-0014).
    const flowRun = {
      primary: 'flow', unit: 'cfs', stage_datum: 'NGVD29',
      points: [
        { t: '2026-08-24T18:00:00Z', stage: 56.8, flow: 293.34 },
        { t: '2026-08-25T00:00:00Z', stage: 56.8, flow: 292.66 },
      ],
    };
    const choice = forecastSeriesFor(flowRun, 'flow', 'cfs', null);
    expect(choice.reason).toBeNull();
    expect(choice.points).toEqual([
      { t: Date.parse('2026-08-24T18:00:00Z'), v: 293.34 },
      { t: Date.parse('2026-08-25T00:00:00Z'), v: 292.66 },
    ]);
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

/* ---- HEFS exceedance band ---- */

import { bandPath, hefsBand } from './hydrograph-math';

const LADDER = {
  unit: 'CFS',
  parameter_id: 'QINE',
  exceedance_levels: [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
  rows: [
    { valid_time: '2026-08-28T12:00:00Z', values: [900, 800, 700, 600, 500, 420, 400] },
    { valid_time: '2026-08-28T18:00:00Z', values: [950, 820, 710, 610, 505, 425, 405] },
    { valid_time: '2026-09-20T12:00:00Z', values: [990, 830, 715, 615, 510, 430, 410] },
  ],
};
const UNTIL = Date.parse('2026-08-31T00:00:00Z');

describe('hefsBand', () => {
  it('draws the 5/50/95 band on a matching flow axis, case-insensitively, clipping and counting', () => {
    const b = hefsBand(LADDER, 'flow', 'cfs', UNTIL);
    expect(b.reason).toBeNull();
    expect(b.levels).toEqual([0.05, 0.5, 0.95]);
    expect(b.band).toHaveLength(2);
    expect(b.band![0]).toEqual({ t: Date.parse('2026-08-28T12:00:00Z'), lo: 400, hi: 900 });
    expect(b.median![0]).toEqual({ t: Date.parse('2026-08-28T12:00:00Z'), v: 600 });
    expect(b.clipped).toBe(1); // the 30-day tail must not stretch a 72-hour chart — and is counted
  });

  it('refuses a stage axis and a genuinely different unit, with the reason', () => {
    expect(hefsBand(LADDER, 'stage', 'ft', UNTIL).reason).toContain('flow');
    const kcfs = { ...LADDER, unit: 'KCFS' };
    expect(hefsBand(kcfs, 'flow', 'cfs', UNTIL).reason).toContain('never converted');
  });

  it('refuses a ladder without the exact levels — never interpolated', () => {
    const coarse = { ...LADDER, exceedance_levels: [0.1, 0.5, 0.9] };
    expect(hefsBand(coarse, 'flow', 'cfs', UNTIL).reason).toContain('never interpolated');
  });

  it('bandPath closes the polygon along both bounds', () => {
    const b = hefsBand(LADDER, 'flow', 'cfs', UNTIL);
    const path = bandPath(b.band!, (t) => (t - b.band![0]!.t) / 3_600_000, (v) => 1000 - v);
    expect(path.startsWith('M0 100')).toBe(true); // hi bound first
    expect(path.endsWith('Z')).toBe(true);
    expect(path).toContain('L0 600'); // back along the lo bound to the first instant
  });
});
