import { describe, expect, it } from 'vitest';
import { loadFixtures } from '../../dev/stub-load.mjs';
import { isErrorResult, route } from '../../dev/stub-router.mjs';
import { RunsListSchema, StationSeriesSchema } from './schemas';

const fx = loadFixtures();
const EVENT_WINDOW = 'start=2025-12-03T08:00:00Z&end=2025-12-23T08:00:00Z';

describe('stub router', () => {
  it('serves /basins and /system/health', () => {
    const basins = route(fx, '/basins', new URLSearchParams()) as { items: unknown[] };
    expect(isErrorResult(basins)).toBe(false);
    expect(basins.items).toHaveLength(6);
    const health = route(fx, '/system/health', new URLSearchParams()) as { status: string };
    expect(health.status).toBeDefined();
  });

  it('rejects unknown paths and bad lod', () => {
    const missing = route(fx, '/nope', new URLSearchParams());
    expect(isErrorResult(missing) && missing.status).toBe(404);
    const badLod = route(fx, '/basins/basin:skagit/geometry', new URLSearchParams('lod=orbit'));
    expect(isErrorResult(badLod) && badLod.status).toBe(400);
  });

  it('serves the Event Zero archived window: series by valid time (parsed by the client schema)', () => {
    const result = route(fx, '/stations/station:usgs:12200500/series', new URLSearchParams(`variable=stage&${EVENT_WINDOW}`));
    expect(isErrorResult(result)).toBe(false);
    const series = StationSeriesSchema.parse(result);
    expect(series.points.length).toBeGreaterThan(0);
    expect(series.points.every((p) => Date.parse(p.t) >= Date.parse('2025-12-03T08:00:00Z'))).toBe(true);
    expect(series.points.every((p) => p.quality?.includes('backfilled'))).toBe(true);
    // The documented crest survives the fixture round trip (EVENT_ZERO §3).
    expect(Math.max(...series.points.map((p) => p.v ?? -Infinity))).toBe(37.73);
    // A narrower window filters by valid time.
    const early = StationSeriesSchema.parse(route(fx, '/stations/station:usgs:12200500/series', new URLSearchParams('variable=stage&start=2025-12-03T08:00:00Z&end=2025-12-10T00:00:00Z')));
    expect(early.points).toHaveLength(1);
  });

  it('serves the Event Zero runs list: 9 golden issuances ascending, supersedes chain intact', () => {
    const result = route(fx, '/forecast-points/MVEW1/runs', new URLSearchParams(EVENT_WINDOW));
    expect(isErrorResult(result)).toBe(false);
    const runs = RunsListSchema.parse(result);
    expect(runs.items.length).toBe(9);
    expect(runs.items[0]!.points[0]!.stage).toBe(36.9);
    expect(runs.items[8]!.points[0]!.stage).toBe(38.1);
    expect(runs.items[0]!.supersedes_run_id).toBeNull();
    for (let i = 1; i < runs.items.length; i += 1) {
      expect(runs.items[i]!.supersedes_run_id).toBe(runs.items[i - 1]!.run_id);
      expect(Date.parse(runs.items[i]!.issued_at)).toBeGreaterThan(Date.parse(runs.items[i - 1]!.issued_at));
    }
    const early = RunsListSchema.parse(route(fx, '/forecast-points/MVEW1/runs', new URLSearchParams('start=2025-12-03T08:00:00Z&end=2025-12-10T00:00:00Z')));
    expect(early.items.length).toBe(1);
  });

  it('rejects a lone start, a reversed window, and a missing window on the runs list', () => {
    const lone = route(fx, '/forecast-points/MVEW1/runs', new URLSearchParams('start=2025-12-03T08:00:00Z'));
    expect(isErrorResult(lone) && lone.status).toBe(400);
    const reversed = route(fx, '/stations/station:usgs:12200500/series', new URLSearchParams('variable=stage&start=2025-12-23T08:00:00Z&end=2025-12-03T08:00:00Z'));
    expect(isErrorResult(reversed) && reversed.status).toBe(400);
    const missing = route(fx, '/forecast-points/MVEW1/runs', new URLSearchParams());
    expect(isErrorResult(missing) && missing.status).toBe(400);
    const unknownLid = route(fx, '/forecast-points/RNTW1/runs', new URLSearchParams(EVENT_WINDOW));
    expect(isErrorResult(unknownLid) && unknownLid.status).toBe(404);
  });
});
