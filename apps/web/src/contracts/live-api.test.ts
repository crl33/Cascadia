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
  ForecastRunSchema,
  GeoFeatureSchema,
  HealthSchema,
  RiverEnvelopeSchema,
  RunsListSchema,
  SceneSummarySchema,
  SearchResultsSchema,
  StationSeriesSchema,
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
  it('GET /stations/{id}/series and /forecast-points/{LID}/runs/latest', async () => {
    const stage = StationSeriesSchema.parse(await get('/stations/station:usgs:12200500/series?variable=stage'));
    expect(stage.variable).toBe('stage');
    expect(stage.points.length).toBeGreaterThan(0);
    const run = ForecastRunSchema.parse(await get('/forecast-points/MVEW1/runs/latest'));
    expect(run.provenance.source_kind).toBe('OFFICIAL_FORECAST');
    expect(run.points.length).toBeGreaterThan(0);
    // A datum is declared for the stage column and named for it — never for a flow value, and
    // never as a bare `datum` a reader could attach to the primary variable (ADR-0014). Asserted
    // on the raw body: zod strips unknown keys, so a parsed object could not show a stale one.
    const rawAubw1 = await get('/forecast-points/AUBW1/runs/latest');
    expect(rawAubw1).not.toHaveProperty('datum');
    const aubw1 = ForecastRunSchema.parse(rawAubw1);
    if (aubw1.points.some((p) => p.stage != null)) expect(aubw1.stage_unit).not.toBeNull();
    else expect(aubw1.stage_datum ?? null).toBeNull();
  });
  it('GET /forecast-points/{LID}/runs — every archived run answers its own provenance question', async () => {
    // The Event Zero window: reconstructed December-2025 runs, where borrowed provenance would be
    // easiest to miss and worst to have. Parsed with the STRICT RunListItemSchema, in which
    // `provenance` is required — an item without one fails here rather than rendering unattributed.
    const runs = RunsListSchema.parse(
      await get('/forecast-points/MVEW1/runs?start=2025-12-03T08:00:00Z&end=2025-12-23T08:00:00Z'),
    );
    expect(runs.lid).toBe('MVEW1');
    expect(runs.items.length).toBeGreaterThan(0);
    // ascending by issuance, superseded runs retained (nothing is deleted from the record)
    const issued = runs.items.map((r) => Date.parse(r.issued_at));
    expect([...issued].sort((a, b) => a - b)).toEqual(issued);

    for (const item of runs.items) {
      const prov = item.provenance;
      expect(prov.source_kind, item.run_id).toBe('OFFICIAL_FORECAST');
      // identity is read from the run's OWN SourceProduct: a run reconstructed from archived WFO
      // text must not inherit the identity of a live NWPS forecast sitting next to it in the list
      expect(prov.product_id, item.run_id).toBe(item.product_id);
      if (item.product_label != null) expect(prov.label, item.run_id).toBe(item.product_label);
      // the stored bytes the crest was parsed from — a claim with nothing behind it fails here
      expect(prov.raw_artifact_id ?? '', item.run_id).not.toBe('');
      expect(prov.issued_at?.slice(0, 16), item.run_id).toBe(item.issued_at.slice(0, 16));
      expect(prov.freshness.state, item.run_id).not.toBe('unknown');
    }
    // the backfilled surface, stated rather than flagged: issued in the past, retrieved long after
    const reconstructed = runs.items.filter((r) => r.available_at != null && r.retrieved_at != null);
    for (const item of reconstructed) {
      expect(Date.parse(item.retrieved_at!), item.run_id).toBeGreaterThan(Date.parse(item.issued_at));
    }
  });
  it('as_of before ingestion yields UNKNOWN with a reason, never a value', async () => {
    const env = RiverEnvelopeSchema.parse(await get('/forecast-points/MVEW1/state?as_of=2026-01-01T00:00:00Z'));
    const item = env.items[0]!;
    expect(item.observed ?? null).toBeNull();
    expect(item.observed_category).toBe('unknown');
    expect(item.observed_category_reason ?? '').not.toBe('');
  });
});
