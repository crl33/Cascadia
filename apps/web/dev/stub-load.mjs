/**
 * Node-only fixture loader for the stub API. Cloudflare Pages Functions must not import this
 * file (it uses node:fs); they assemble the same `fx` object from bundled JSON instead.
 */
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = resolve(here, '../../..');

const readJson = (p) => JSON.parse(readFileSync(p, 'utf8'));

export function loadFixtures(root = REPO_ROOT) {
  return {
    basinLod: readJson(resolve(root, 'tests/fixtures/geo/basins_seed_basin_lod.geojson')),
    stateLod: readJson(resolve(root, 'tests/fixtures/geo/basins_seed_state_lod.geojson')),
    basinEnvelope: readJson(resolve(root, 'packages/contracts/fixtures/viz_basins_envelope.json')),
    riverEnvelope: readJson(resolve(root, 'packages/contracts/fixtures/river_mvew1_envelope.json')),
    fieldPrecip: readJson(resolve(root, 'packages/contracts/fixtures/field_precip_observed.json')),
    samples: readJson(resolve(here, 'fixtures/mvew1-samples.json')),
    tier0: readJson(resolve(root, 'functions/fixtures/basin_tier0.json')),
    riverNetwork: JSON.parse(gunzipSync(readFileSync(resolve(root, 'tests/fixtures/geo/river_network.json.gz'))).toString('utf8')),
  };
}
