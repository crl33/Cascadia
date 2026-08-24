import { describe, expect, it } from 'vitest';
import { buildRunsLatest, buildSeries } from '../../dev/stub-data.mjs';
import { loadFixtures } from '../../dev/stub-load.mjs';
import { ForecastRunSchema, StationSeriesSchema } from './schemas';

const fx = loadFixtures();

describe('station series and forecast run stub responses validate against the client schemas', () => {
  it('/stations/{id}/series for stage and flow', () => {
    const stage = StationSeriesSchema.parse(buildSeries(fx, 'station:usgs:12200500', 'stage'));
    expect(stage.variable).toBe('stage');
    expect(stage.unit).toBe('ft');
    expect(stage.datum).toBe('NGVD29');
    expect(stage.points.length).toBeGreaterThan(0);
    expect(stage.provenance.source_kind).toBe('OBSERVED');
    const flow = StationSeriesSchema.parse(buildSeries(fx, 'station:usgs:12200500', 'flow'));
    expect(flow.unit).toBe('cfs');
    expect(flow.datum).toBeNull();
  });
  it('/forecast-points/MVEW1/runs/latest; other seed points honestly have none', () => {
    const run = ForecastRunSchema.parse(buildRunsLatest(fx, 'MVEW1'));
    expect(run.primary).toBe('stage');
    expect(run.issuer).toBe('NWRFC');
    expect(run.stage_unit).toBe('ft');
    expect(run.stage_datum).toBe('NGVD29');
    expect(run.points.length).toBeGreaterThan(0);
    expect(run.provenance.source_kind).toBe('OFFICIAL_FORECAST');
    expect(buildRunsLatest(fx, 'RNTW1')).toBeNull();
  });
  it('a run with no stage column declares no stage datum (ADR-0014)', () => {
    const run = ForecastRunSchema.parse(buildRunsLatest(fx, 'AUBW1'));
    expect(run.primary).toBe('flow');
    expect(run.unit).toBe('cfs');
    expect(run.flow_unit).toBe('cfs');
    // This capture carries no secondary stage series, so there is nothing for a datum to describe.
    expect(run.points.every((p) => p.stage == null)).toBe(true);
    expect(run.stage_unit).toBeNull();
    expect(run.stage_datum).toBeNull();
  });
});
