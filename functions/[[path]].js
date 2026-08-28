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
import riverNetwork from './fixtures/river_network.json';
import fieldPrecip from './fixtures/field_precip_observed.json';
import fieldSnow from './fixtures/field_snow_cover.json';
import labels from './fixtures/labels.json';
import cameras from './fixtures/cameras.json';

const fx = { basinLod, stateLod, basinEnvelope, riverEnvelope, samples, tier0, riverNetwork, fieldPrecip, fieldSnow, labels, cameras };

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

  // USGS camera frames (public-domain HIVIS imagery on a CORS-open S3 bucket): redirect to
  // the NEWEST frame for a camera. Keys embed capture time lexicographically
  // (<camId>___YYYY-MM-DDTHH-MM-SSZ.jpg), so an S3 list with start-after = now-3h returns
  // recent frames in order and the last key is the latest. The redirect costs the gateway no
  // image bandwidth; 60 s caching keeps a busy viewer at ~1 list/min/camera. A camera with no
  // frame in 48 h answers 404 — the card says "frame unavailable", never shows a stale frame
  // as current (the Kent lesson: HTTP 200 is not freshness).
  let camMatch;
  if ((camMatch = url.pathname.match(/^\/cameras\/usgs\/([A-Za-z0-9_.-]{1,120})\/latest\.jpg$/))) {
    const camId = camMatch[1];
    const bucket = 'https://usgs-nims-images.s3.amazonaws.com';
    const stamp = (msAgo) => new Date(Date.now() - msAgo).toISOString().slice(0, 19).replaceAll(':', '-') + 'Z';
    try {
      for (const windowMs of [3 * 3600e3, 48 * 3600e3]) {
        const listUrl = `${bucket}/?list-type=2&prefix=${encodeURIComponent(`overlay/${camId}/`)}&start-after=${encodeURIComponent(`overlay/${camId}/${camId}___${stamp(windowMs)}`)}`;
        const resp = await fetch(listUrl, { signal: AbortSignal.timeout(15000) });
        if (!resp.ok) break;
        const xml = await resp.text();
        const keys = [...xml.matchAll(/<Key>([^<]+)<\/Key>/g)].map((m) => m[1]).filter((k) => k.endsWith('.jpg'));
        if (keys.length > 0) {
          const latest = keys[keys.length - 1];
          return new Response(null, {
            status: 302,
            headers: { Location: `${bucket}/${latest}`, 'Cache-Control': 'public, max-age=60' },
          });
        }
      }
      return json(404, { detail: `no frame for ${camId} in the last 48 h — instrument likely offline` });
    } catch (err) {
      console.error('camera frame lookup failed', err && err.message);
      return json(503, { detail: 'camera frame lookup unavailable', source: 'gateway' });
    }
  }

  // Terrain tiles (ADR-0021): static public-domain artifacts on their own R2 public domain,
  // proxied here so the app stays same-origin (no CORS, no second hostname in the client).
  // Immutable by construction — a DEM pyramid does not change; v-bumps change the prefix.
  if (url.pathname.startsWith('/terrain/')) {
    // The default is the deployed pyramid's own public bucket domain — public static assets,
    // the same standing as the OSM tile URL in the client (the API token cannot edit Pages
    // env vars, so config-in-code with an env override is the honest arrangement). Set
    // TERRAIN_ORIGIN to move it; set it to 'off' to disable terrain entirely.
    const terrainOrigin = (env && env.TERRAIN_ORIGIN) || 'https://pub-1145121e012145ac8173711ab278c913.r2.dev';
    if (terrainOrigin === 'off') return json(404, { detail: 'terrain is disabled on this deployment' });
    try {
      const resp = await fetch(`${terrainOrigin}${url.pathname}`, {
        headers: { 'User-Agent': 'CascadiaPapsukkal-gateway/0.1' },
        signal: AbortSignal.timeout(30000),
      });
      const headers = new Headers(resp.headers);
      headers.set('X-Content-Type-Options', 'nosniff');
      // Tiles are immutable (a DEM pyramid does not change; v-bumps change the prefix).
      // layer.json is the one file a republish rewrites in place — five minutes, not a year.
      headers.set('Cache-Control', url.pathname.endsWith('.terrain')
        ? 'public, max-age=31536000, immutable'
        : 'public, max-age=300');
      // ctb -C gzipped every tile at build time, and R2 kept the Content-Type but dropped the
      // Content-Encoding on upload — so the gateway states it. Without this header Cesium
      // parses gzip bytes as mesh and every tile fails to decode.
      if (resp.ok && url.pathname.endsWith('.terrain')) headers.set('Content-Encoding', 'gzip');
      return new Response(resp.body, { status: resp.status, headers });
    } catch (err) {
      console.error('terrain proxy failed', err && err.message);
      return json(503, { detail: 'terrain origin unavailable', source: 'gateway' });
    }
  }

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
      // The backend's Content-Type survives the security-header stamp. Stamping it too served
      // the SSE stream as application/json and EventSource aborted the connection — live
      // invalidation was silently dead in production while every test passed against the
      // stub, whose own SSE path sets text/event-stream correctly (found 2026-08-28 by
      // reading the browser console on the deployed site).
      const upstreamType = resp.headers.get('Content-Type');
      if (upstreamType) headers.set('Content-Type', upstreamType);
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
