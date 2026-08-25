/**
 * Cloudflare Pages Function: same SPIKE API SPEC as apps/web/dev/stub-api.mjs.
 * Invoked only for API paths listed in apps/web/public/_routes.json.
 *
 * Two modes:
 *  - env.BACKEND_ORIGIN set (production): reverse-proxy the read-only API to the deployed
 *    backend (Railway), preserving path + query. GET/OPTIONS only; everything else 405.
 *  - no BACKEND_ORIGIN (previews, local `wrangler pages dev`): fixture-backed stub, so the
 *    static preview keeps working with zero credentials. Never calls a provider either way.
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
  const { request, env } = context;
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: { ...HEADERS, 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'Accept, Content-Type' },
    });
  }
  if (request.method !== 'GET') return json(405, { detail: 'read-only API' });

  let url;
  try {
    url = new URL(request.url);
    decodeURIComponent(url.pathname);
  } catch {
    return json(400, { detail: 'bad path' });
  }
  if (url.pathname.length > 256) return json(414, { detail: 'path too long' });

  const origin = (env && env.BACKEND_ORIGIN) || '';
  if (origin) {
    const upstream = new URL(origin);
    upstream.pathname = url.pathname;
    upstream.search = url.search;
    try {
      const resp = await fetch(upstream, {
        method: 'GET',
        headers: { Accept: 'application/json', 'User-Agent': 'CascadiaPapsukkal-gateway/0.1' },
        // 60 s: /viz/basins computes three intelligence surfaces for six basins and measured
        // 21.8 s in production on 2026-08-25 (single basin 4.6 s), which the previous 20 s
        // abort turned into a 503 the moment P3 landed. The timeout is a backstop against a
        // hung backend, not a latency budget — the latency itself is recorded as the top P4
        // performance item in docs/NEXT_STEPS.md and belongs in the API, not here.
        signal: AbortSignal.timeout(60000),
      });
      const headers = new Headers(resp.headers);
      for (const [k, v] of Object.entries(HEADERS)) headers.set(k, v);
      headers.delete('Access-Control-Allow-Origin'); // same-origin via the gateway; CORS not needed
      return new Response(resp.body, { status: resp.status, headers });
    } catch (err) {
      console.error('backend proxy failed', err && err.message);
      return json(503, { detail: 'backend unavailable', source: 'gateway' });
    }
  }

  // Fixture-backed stub (previews without a configured backend).
  let result;
  try {
    result = route(fx, decodeURIComponent(url.pathname), url.searchParams);
  } catch (err) {
    console.error(err);
    return json(500, { detail: 'stub error' });
  }
  return isErrorResult(result) ? json(result.status, result.body) : json(200, result);
}
