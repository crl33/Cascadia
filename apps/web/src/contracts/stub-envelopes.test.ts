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
  it('/viz/basins: all six basins carry the REAL captured envelope, not fabricated unknowns', () => {
    // The fixture is a live production capture (2026-08-28, contract 1.3.0). Until then the stub
    // served a pre-P3 envelope where five basins were hand-written UNKNOWN with a "not
    // implemented in the spike" reason — which by 2026-08-28 was a false statement about the
    // platform, and hid every rendering path except the unknown treatment from the dev loop.
    const env = buildVizBasins(fx) as { items: { id: string; surfaces: { hazard: { official_category: string; reason: string | null } } }[] };
    expect(validateEnvelope(env)).toBe(true);
    expect(env.items).toHaveLength(6);
    const parsed = BasinEnvelopeSchema.parse(env);
    for (const item of parsed.items) {
      const s = item.surfaces.susceptibility;
      expect(s.state).not.toBe('unknown'); // real values at capture time, all six basins
      expect(s.experimental).toBe(true);
      expect(s.reason).toBeNull();
      // every surface's provenance resolves inside the same envelope
      expect(parsed.provenance_refs[s.prov]).toBeDefined();
    }
    expect(parsed.items.find((i) => i.id === 'basin:skagit')!.surfaces.hazard.official_category).toBe('none');
    // the capture carries the rain-exposed fraction driver with its HUC8-union caveat
    const cedar = env.items.find((i) => i.id === 'basin:cedar')! as unknown as { headline_drivers: { feature: string; prov: string }[] };
    const rain = cedar.headline_drivers.find((d) => d.feature === 'basin_rain_exposed_fraction')!;
    expect(rain).toBeDefined();
    expect(parsed.provenance_refs[rain.prov]?.label).toMatch(/HUC8-union/);
  });

  it('a basin absent from the envelope still degrades to an honest UNKNOWN, never silence', () => {
    // The fallback path the old fixture exercised by accident is kept covered on purpose: if the
    // geometry ever names a basin the envelope lacks, the stub must say UNKNOWN with a reason.
    const envelope = fx.basinEnvelope as unknown as { items: { id: string }[] };
    const poisoned = {
      ...fx,
      basinEnvelope: { ...envelope, items: envelope.items.filter((i) => i.id !== 'basin:nooksack') },
    } as typeof fx;
    const env = buildVizBasins(poisoned);
    expect(validateEnvelope(env)).toBe(true);
    const parsed = BasinEnvelopeSchema.parse(env);
    const nooksack = parsed.items.find((i) => i.id === 'basin:nooksack')!;
    expect(nooksack.surfaces.hazard.official_category).toBe('unknown');
    expect(nooksack.surfaces.hazard.reason).toMatch(/unknown|No NWPS/i);
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
