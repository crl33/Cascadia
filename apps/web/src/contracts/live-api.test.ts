/**
 * Live-API contract check: validates a running Cascadia Papsukkal API (the real FastAPI app, or the
 * stub) against the client's zod schemas, endpoint by endpoint, using the seed Skagit / MVEW1 /
 * AUBW1 ids. Offline by default: the whole suite is skipped unless CASCADE_LIVE_API_BASE is set
 * (e.g. `CASCADE_LIVE_API_BASE=http://localhost:8000 npx vitest run src/contracts/live-api.test.ts`).
 * No fixture values are asserted here; only shapes and doctrine invariants (thresholds basis /
 * datum, UNKNOWN-with-reason at a knowledge time before ingestion).
 */
import { describe, expect, it } from 'vitest';
import {
  BasinEnvelopeSchema,
  BasinListSchema,
  GeoFeatureSchema,
  HealthSchema,
  RiverEnvelopeSchema,
  SceneSummarySchema,
  SearchResultsSchema,
} from './schemas';

const base = process.env['CASCADE_LIVE_API_BASE']?.replace(/\/$/, '');

async function get(path: string): Promise<unknown> {
  const response = await fetch(`${base}${path}`, { headers: { Accept: 'application/json' } });
  expect(response.status, path).toBe(200);
  return (await response.json()) as unknown;
}

describe.skipIf(!base)('live API responses validate against the client zod schemas', () => {
  it('GET /basins', async () => {
    const list = BasinListSchema.parse(await get('/basins'));
    expect(list.items.map((b) => b.id)).toContain('basin:skagit');
  });
  it('GET /basins/basin:skagit/geometry?lod=state|basin', async () => {
    for (const lod of ['state', 'basin']) GeoFeatureSchema.parse(await get(`/basins/basin:skagit/geometry?lod=${lod}`));
  });
  it('GET /basins/basin:skagit/state and /viz/basins', async () => {
    const one = BasinEnvelopeSchema.parse(await get('/basins/basin:skagit/state'));
    expect(one.items).toHaveLength(1);
    expect(one.items[0]?.id).toBe('basin:skagit');
    const all = BasinEnvelopeSchema.parse(await get('/viz/basins'));
    expect(all.items.length).toBeGreaterThanOrEqual(6);
  });
  it('GET /viz/rivers and /forecast-points/{LID}/state carry basis-consistent thresholds', async () => {
    RiverEnvelopeSchema.parse(await get('/viz/rivers?basin=basin:skagit'));
    const mvew1 = RiverEnvelopeSchema.parse(await get('/forecast-points/MVEW1/state')).items[0]!;
    expect(mvew1.id).toBe('fp:nwps:MVEW1');
    if (mvew1.thresholds) {
      expect(mvew1.thresholds.basis).toBe('stage');
      expect(mvew1.thresholds.datum).toBe('NGVD29');
    }
    const aubw1 = RiverEnvelopeSchema.parse(await get('/forecast-points/AUBW1/state')).items[0]!;
    if (aubw1.thresholds) {
      expect(aubw1.thresholds.basis).toBe('flow');
      expect(aubw1.thresholds.unit).toBe('cfs');
    }
  });
  it('GET /scene/summary for every band', async () => {
    for (const band of ['orbital', 'state', 'basin', 'river']) {
      const summary = SceneSummarySchema.parse(await get(`/scene/summary?band=${band}&basin=basin:skagit`));
      expect(summary.band).toBe(band);
      expect(summary.basins).not.toBeNull();
    }
  });
  it('GET /search and /system/health', async () => {
    const results = SearchResultsSchema.parse(await get('/search?q=ska'));
    expect(results.items.some((r) => r.id === 'basin:skagit')).toBe(true);
    HealthSchema.parse(await get('/system/health'));
  });
  it('as_of before ingestion yields UNKNOWN with a reason, never a value', async () => {
    const env = RiverEnvelopeSchema.parse(await get('/forecast-points/MVEW1/state?as_of=2026-01-01T00:00:00Z'));
    const item = env.items[0]!;
    expect(item.observed ?? null).toBeNull();
    expect(item.observed_category).toBe('unknown');
    expect(item.observed_category_reason ?? '').not.toBe('');
  });
});
