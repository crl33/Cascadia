import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { BasinEnvelopeSchema, RiverEnvelopeSchema, ContractEnvelopeSchema } from './schemas';

const fixtures = resolve(__dirname, '../../../../packages/contracts/fixtures');
const load = (name: string) => JSON.parse(readFileSync(resolve(fixtures, name), 'utf8')) as unknown;

describe('canonical fixture envelopes validate against the client schemas', () => {
  it('viz_basins_envelope.json', () => {
    const env = BasinEnvelopeSchema.parse(load('viz_basins_envelope.json'));
    expect(env.contract).toBe('BasinVisualizationState');
    expect(env.items[0]?.surfaces.hazard.official_category).toBe('none');
    expect(env.provenance_refs['nwps-forecast-mvew1']?.source_kind).toBe('OFFICIAL_FORECAST');
    expect(ContractEnvelopeSchema.safeParse(load('viz_basins_envelope.json')).success).toBe(true);
  });
  it('river_mvew1_envelope.json', () => {
    const env = RiverEnvelopeSchema.parse(load('river_mvew1_envelope.json'));
    const item = env.items[0]!;
    expect(item.observed?.stage?.value).toBe(10.59);
    expect(item.observed?.stage?.datum).toBe('NGVD29');
    expect(item.thresholds?.basis).toBe('stage');
    expect(item.thresholds?.action).toBe(23.5);
    expect(env.provenance_refs['usgs-iv-12200500']?.quality).toEqual(['provisional']);
  });
  it('rejects an envelope whose prov key does not resolve', () => {
    const env = load('river_mvew1_envelope.json') as { provenance_refs: Record<string, unknown> };
    delete env.provenance_refs['cascade-trend-6h'];
    expect(RiverEnvelopeSchema.safeParse(env).success).toBe(false);
  });
  it('rejects stage thresholds without a datum', () => {
    const env = load('river_mvew1_envelope.json') as { items: { thresholds: { datum: string | null } }[] };
    env.items[0]!.thresholds.datum = null;
    expect(RiverEnvelopeSchema.safeParse(env).success).toBe(false);
  });
});
