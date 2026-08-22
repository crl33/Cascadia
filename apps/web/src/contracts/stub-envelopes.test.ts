import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import Ajv2020 from 'ajv/dist/2020';
import addFormats from 'ajv-formats';
import { describe, expect, it } from 'vitest';
import { buildVizBasins, buildVizRivers, buildRiverState, buildSceneSummary } from '../../dev/stub-data.mjs';
import { loadFixtures, REPO_ROOT } from '../../dev/stub-load.mjs';
import { BasinEnvelopeSchema, RiverEnvelopeSchema, SceneSummarySchema } from './schemas';

const schemaDir = resolve(REPO_ROOT, 'packages/contracts/schema');
const schema = (name: string) => JSON.parse(readFileSync(resolve(schemaDir, `${name}.json`), 'utf8'));
const ajv = new Ajv2020({ strict: false, allErrors: true });
addFormats(ajv);
const validateEnvelope = ajv.compile(schema('ContractEnvelope'));
const validateScene = ajv.compile(schema('SceneSummary'));
const fx = loadFixtures();

describe('dev stub envelopes validate against the JSON Schema', () => {
  it('/viz/basins: six basins, Skagit from the fixture, the rest UNKNOWN with reasons', () => {
    const env = buildVizBasins(fx) as { items: { id: string; surfaces: { hazard: { official_category: string; reason: string | null } } }[] };
    expect(validateEnvelope(env)).toBe(true);
    expect(env.items).toHaveLength(6);
    const parsed = BasinEnvelopeSchema.parse(env);
    const nooksack = parsed.items.find((i) => i.id === 'basin:nooksack')!;
    expect(nooksack.surfaces.hazard.official_category).toBe('unknown');
    expect(nooksack.surfaces.hazard.reason).toMatch(/unknown/);
    expect(parsed.provenance_refs[nooksack.surfaces.hazard.prov]?.source_kind).toBe('UNKNOWN');
    expect(parsed.items.find((i) => i.id === 'basin:skagit')!.surfaces.hazard.official_category).toBe('none');
  });
  it('/viz/rivers and /forecast-points/{LID}/state for seed points', () => {
    const skagit = buildVizRivers(fx, 'basin:skagit');
    expect(validateEnvelope(skagit)).toBe(true);
    expect(RiverEnvelopeSchema.parse(skagit).items[0]?.id).toBe('fp:nwps:MVEW1');
    const cedar = buildRiverState(fx, 'RNTW1');
    expect(validateEnvelope(cedar)).toBe(true);
    const item = RiverEnvelopeSchema.parse(cedar).items[0]!;
    expect(item.observed).toBeNull();
    expect(item.observed_category).toBe('unknown');
  });
  it('/scene/summary per band', () => {
    const orbital = buildSceneSummary(fx, 'orbital', null);
    expect(validateScene(orbital)).toBe(true);
    expect(SceneSummarySchema.parse(orbital).rivers).toBeNull();
    const basin = buildSceneSummary(fx, 'basin', 'basin:skagit');
    expect(validateScene(basin)).toBe(true);
    expect(SceneSummarySchema.parse(basin).rivers?.items).toHaveLength(1);
  });
});
