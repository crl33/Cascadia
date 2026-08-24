import { describe, expect, it } from 'vitest';
import type { ProvenanceRef, RunListItem, StationSeries } from '../contracts/schemas';
import {
  currentRunAt, filterSeriesAt, observedCrest, runIsBackfilled, runsIssuedAtOrBefore, seriesIsBackfilled,
} from './event-filter';

const prov = (over: Partial<ProvenanceRef> = {}): ProvenanceRef => ({
  source_id: 'src:nws-afos',
  source_kind: 'OFFICIAL_FORECAST',
  product_id: 'product:nws-fls-crest',
  freshness: { state: 'stale' },
  label: 'NWRFC crest via WFO FLW/FLS text (reconstructed)',
  ...over,
});

const run = (issuedAt: string, crest: number, supersedes: string | null): RunListItem => ({
  run_id: `run:afos:MVEW1:${issuedAt}`,
  product_id: 'product:nws-fls-crest',
  issued_at: issuedAt,
  issuer: 'NWRFC via KSEW',
  primary: 'stage',
  unit: 'ft',
  datum: 'NGVD29',
  supersedes_run_id: supersedes,
  points: [{ t: '2025-12-12T12:00:00Z', stage: crest, flow: null }],
  provenance: prov({ issued_at: issuedAt, retrieved_at: '2026-08-24T12:00:00Z', quality: ['backfilled'] }),
});

/** The MVEW1 golden chain (docs/EVENT_ZERO.md §8): 9 issuances, 36.9 → … → 38.1. */
const ISSUANCES: readonly (readonly [string, number])[] = [
  ['2025-12-09T17:01:00Z', 36.9],
  ['2025-12-10T01:24:00Z', 41.5],
  ['2025-12-10T09:24:00Z', 41.5],
  ['2025-12-10T23:14:00Z', 42.3],
  ['2025-12-11T01:15:00Z', 42.1],
  ['2025-12-11T10:04:00Z', 39.1],
  ['2025-12-11T18:17:00Z', 39.1],
  ['2025-12-12T01:12:00Z', 38.3],
  ['2025-12-12T08:50:00Z', 38.1],
];
const CHAIN: RunListItem[] = ISSUANCES.map(([iso, crest], i) =>
  run(iso, crest, i === 0 ? null : `run:afos:MVEW1:${ISSUANCES[i - 1]![0]}`));

const crestOf = (r: RunListItem | null): number | null => r?.points[0]?.stage ?? null;

describe('run selection by the replay clock (EVENT_ZERO §8 look-ahead audit item 5)', () => {
  it('selects the latest run issued at or before the cursor', () => {
    // At T = §5 #47 (the 42.3 ft peak forecast) the current crest is 42.3 …
    expect(crestOf(currentRunAt(CHAIN, '2025-12-10T23:14:00Z'))).toBe(42.3);
    expect(crestOf(currentRunAt(CHAIN, '2025-12-11T00:00:00Z'))).toBe(42.3);
    // … and at T = §5 #63 it is 39.1 — never a later value.
    expect(crestOf(currentRunAt(CHAIN, '2025-12-11T10:04:00Z'))).toBe(39.1);
    expect(crestOf(currentRunAt(CHAIN, '2025-12-12T09:00:00Z'))).toBe(38.1);
  });
  it('returns null (UNKNOWN) before the first issuance and for a null cursor', () => {
    expect(currentRunAt(CHAIN, '2025-12-09T17:00:00Z')).toBeNull();
    expect(currentRunAt(CHAIN, null)).toBeNull();
    expect(runsIssuedAtOrBefore(CHAIN, null)).toEqual([]);
  });
  it('issuance boundary is inclusive and the visible list grows one run per crossed issuance', () => {
    expect(runsIssuedAtOrBefore(CHAIN, '2025-12-09T17:01:00Z')).toHaveLength(1);
    expect(runsIssuedAtOrBefore(CHAIN, '2025-12-10T02:00:00Z')).toHaveLength(2);
    expect(runsIssuedAtOrBefore(CHAIN, '2025-12-23T08:00:00Z')).toHaveLength(9);
  });
  it('does not trust input order: an unsorted list selects the same run', () => {
    const shuffled = [CHAIN[4]!, CHAIN[0]!, CHAIN[8]!, CHAIN[2]!, CHAIN[6]!, CHAIN[1]!, CHAIN[7]!, CHAIN[3]!, CHAIN[5]!];
    expect(crestOf(currentRunAt(shuffled, '2025-12-11T02:00:00Z'))).toBe(42.1);
    expect(runsIssuedAtOrBefore(shuffled, '2025-12-23T08:00:00Z').map((r) => r.issued_at)).toEqual(ISSUANCES.map(([iso]) => iso));
  });
});

const series: StationSeries = {
  station_id: 'station:usgs:12200500',
  variable: 'stage',
  unit: 'ft',
  datum: 'NGVD29',
  points: [
    { t: '2025-12-09T16:15:00Z', v: 25.3, quality: ['approved', 'backfilled'] },
    { t: '2025-12-12T00:15:00Z', v: 35.8, quality: ['approved', 'backfilled'] },
    { t: '2025-12-12T08:15:00Z', v: 37.73, quality: ['approved', 'backfilled'] },
    { t: '2025-12-18T04:15:00Z', v: 30.92, quality: ['approved', 'backfilled'] },
  ],
  provenance: prov({ source_kind: 'OBSERVED', product_id: 'product:usgs-iv', quality: ['approved', 'backfilled'] }),
};

describe('series filtering by the replay clock', () => {
  it('keeps only points at or before the cursor (boundary kept, gap never bridged)', () => {
    expect(filterSeriesAt(series, '2025-12-12T08:15:00Z')?.points.map((p) => p.v)).toEqual([25.3, 35.8, 37.73]);
    expect(filterSeriesAt(series, '2025-12-09T00:00:00Z')?.points).toEqual([]);
    expect(filterSeriesAt(series, null)).toBe(series);
    expect(filterSeriesAt(null, '2025-12-12T08:15:00Z')).toBeNull();
  });
  it('observed crest is the first occurrence of the maximum', () => {
    expect(observedCrest(series)).toEqual({ t: '2025-12-12T08:15:00Z', v: 37.73 });
    expect(observedCrest(null)).toBeNull();
    expect(observedCrest({ ...series, points: [] })).toBeNull();
  });
});

describe('backfilled surfacing (ADR-0010)', () => {
  it('flags series via provenance or point quality', () => {
    expect(seriesIsBackfilled(series)).toBe(true);
    expect(seriesIsBackfilled({ ...series, provenance: prov({ source_kind: 'OBSERVED', quality: ['provisional'] }), points: [{ t: '2025-12-09T16:15:00Z', v: 25.3, quality: ['provisional'] }] })).toBe(false);
    expect(seriesIsBackfilled(null)).toBe(false);
  });
  it('flags runs by quality, product identity, or retrieval long after issuance', () => {
    expect(runIsBackfilled(CHAIN[0]!)).toBe(true);
    const liveRun = {
      product_id: 'product:nwps-stageflow-forecast',
      issued_at: '2026-08-21T15:05:00Z',
      provenance: prov({ product_id: 'product:nwps-stageflow-forecast', retrieved_at: '2026-08-21T15:30:00Z', quality: [] }),
    };
    expect(runIsBackfilled(liveRun)).toBe(false);
    expect(runIsBackfilled({ ...liveRun, provenance: { ...liveRun.provenance, retrieved_at: '2026-11-01T00:00:00Z' } })).toBe(true);
  });
});
