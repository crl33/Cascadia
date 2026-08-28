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
import basinEnvelope from './fixtures/viz_basins_envelope.json';
import riverEnvelope from './fixtures/river_mvew1_envelope.json';
import samples from './fixtures/mvew1-samples.json';
import tier0 from './fixtures/basin_tier0.json';

const fx = { basinLod, stateLod, basinEnvelope, riverEnvelope, samples, tier0 };

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
    // The SSE stream is the one deliberately long-lived response: no abort backstop (the
    // heartbeat detects a dead backend within seconds) and the client's own Accept passes
    // through so the backend answers text/event-stream.
    const streaming = url.pathname === '/system/events';
    try {
      const resp = await fetch(upstream, {
        method: 'GET',
        headers: {
          Accept: streaming ? 'text/event-stream' : 'application/json',
          'User-Agent': 'CascadiaPapsukkal-gateway/0.1',
        },
        // 30 s backstop against a hung backend — NOT a latency budget. /viz/basins was 21.8 s
        // when P3 landed (120 round trips) and forced a temporary 60 s abort; the read path was
        // batched to 13 statements and it now measures ~2.6-2.8 s in production, so 30 s is ~10x
        // headroom over normal behaviour. The residual is ~195 ms per query of cross-region round
        // trip, not amplification (docs/NEXT_STEPS.md).
        signal: streaming ? undefined : AbortSignal.timeout(30000),
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
  if (url.pathname === '/system/events') {
    // The fixture stub never ingests: an event stream with only a retry hint and heartbeats
    // is the truth. TransformStream keeps the response open without buffering.
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const enc = new TextEncoder();
    writer.write(enc.encode('retry: 15000\n\n'));
    const beat = setInterval(() => writer.write(enc.encode(': keep-alive\n\n')).catch(() => clearInterval(beat)), 15000);
    return new Response(readable, { status: 200, headers: { ...HEADERS, 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store' } });
  }
  let result;
  try {
    result = route(fx, decodeURIComponent(url.pathname), url.searchParams);
  } catch (err) {
    console.error(err);
    return json(500, { detail: 'stub error' });
  }
  return isErrorResult(result) ? json(result.status, result.body) : json(200, result);
}
