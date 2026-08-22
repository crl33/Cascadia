/**
 * Cloudflare Pages Function: same SPIKE API SPEC as apps/web/dev/stub-api.mjs, fixture-backed.
 * Invoked only for API paths listed in apps/web/public/_routes.json. Never calls a provider.
 */
import { isErrorResult, route } from '../apps/web/dev/stub-router.mjs';
import basinLod from './fixtures/basins_seed_basin_lod.json';
import stateLod from './fixtures/basins_seed_state_lod.json';
import basinEnvelope from './fixtures/basin_skagit_envelope.json';
import riverEnvelope from './fixtures/river_mvew1_envelope.json';
import samples from './fixtures/mvew1-samples.json';

const fx = { basinLod, stateLod, basinEnvelope, riverEnvelope, samples };

const HEADERS = {
  'Content-Type': 'application/json; charset=utf-8',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Cache-Control': 'no-store',
};

function json(status, body) {
  return new Response(JSON.stringify(body), { status, headers: HEADERS });
}

export async function onRequest(context) {
  const { request } = context;
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: { ...HEADERS, 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'Accept, Content-Type' },
    });
  }
  if (request.method !== 'GET') return json(405, { detail: 'read-only API' });

  let pathname;
  try {
    pathname = decodeURIComponent(new URL(request.url).pathname);
  } catch {
    return json(400, { detail: 'bad path' });
  }
  if (pathname.length > 256) return json(414, { detail: 'path too long' });

  let result;
  try {
    result = route(fx, pathname, new URL(request.url).searchParams);
  } catch (err) {
    console.error(err);
    return json(500, { detail: 'stub error' });
  }
  return isErrorResult(result) ? json(result.status, result.body) : json(200, result);
}
