/**
 * Shared SPIKE API SPEC router for the Node stub server and the Cloudflare Pages Function.
 * Pure: takes preloaded fixtures, a pathname, and search params; returns a body or {status, body}.
 */
import {
  buildBasins, buildGeometry, buildBasinState, buildVizBasins, buildVizRivers, buildRiverState,
  buildRunsLatest, buildRunsList, buildSeries, buildSeriesWindow, buildSceneSummary, buildSearch, buildHealth,
} from './stub-data.mjs';

const BAND_RE = /^(orbital|state|basin|river)$/;
const MAX_WINDOW_MS = 45 * 24 * 3_600_000;

/**
 * start=&end= absolute window (P2 Event Zero): null when absent, {error} when malformed —
 * both-or-neither, ISO-8601, end after start, span ≤ 45 days (mirrors the API validation).
 */
function parseWindow(params) {
  const start = params.get('start');
  const end = params.get('end');
  if (start === null && end === null) return null;
  if (start === null || end === null) return { error: 'start and end must be given together' };
  const startMs = Date.parse(start);
  const endMs = Date.parse(end);
  if (!Number.isFinite(startMs) || !Number.isFinite(endMs)) return { error: 'start/end must be ISO-8601 instants' };
  if (endMs <= startMs) return { error: 'end must be after start' };
  if (endMs - startMs > MAX_WINDOW_MS) return { error: 'window must be 45 days or shorter' };
  return { startMs, endMs };
}

export function route(fx, pathname, params) {
  const asOf = params.get('as_of');
  let m;
  if (pathname === '/basins') return buildBasins(fx);
  if ((m = pathname.match(/^\/basins\/([^/]+)\/geometry$/))) {
    const lod = params.get('lod') ?? 'state';
    if (!/^(state|basin)$/.test(lod)) return { status: 400, body: { detail: 'lod must be state|basin' } };
    return buildGeometry(fx, m[1], lod) ?? { status: 404, body: { detail: `unknown basin ${m[1]}` } };
  }
  if ((m = pathname.match(/^\/basins\/([^/]+)\/state$/))) return buildBasinState(fx, m[1], asOf) ?? { status: 404, body: { detail: `unknown basin ${m[1]}` } };
  if (pathname === '/viz/basins') return buildVizBasins(fx, asOf);
  if (pathname === '/viz/rivers') {
    const basin = params.get('basin');
    if (!basin) return { status: 400, body: { detail: 'basin is required' } };
    return buildVizRivers(fx, basin, asOf);
  }
  if ((m = pathname.match(/^\/forecast-points\/([A-Z0-9]+)\/state$/))) return buildRiverState(fx, m[1], asOf) ?? { status: 404, body: { detail: `unknown forecast point ${m[1]}` } };
  if ((m = pathname.match(/^\/forecast-points\/([A-Z0-9]+)\/runs\/latest$/))) return buildRunsLatest(fx, m[1]) ?? { status: 404, body: { detail: `no forecast run for ${m[1]} in the stub fixtures` } };
  if ((m = pathname.match(/^\/forecast-points\/([A-Z0-9]+)\/runs$/))) {
    const window = parseWindow(params);
    if (window === null) return { status: 400, body: { detail: 'start and end are required' } };
    if (window.error) return { status: 400, body: { detail: window.error } };
    return buildRunsList(fx, m[1], window.startMs, window.endMs)
      ?? { status: 404, body: { detail: `no archived forecast runs for ${m[1]} in the stub fixtures` } };
  }
  if ((m = pathname.match(/^\/stations\/([^/]+)\/series$/))) {
    const variable = params.get('variable') ?? 'stage';
    if (!/^(stage|flow)$/.test(variable)) return { status: 400, body: { detail: 'variable must be stage|flow' } };
    const window = parseWindow(params);
    if (window && window.error) return { status: 400, body: { detail: window.error } };
    if (window) {
      return buildSeriesWindow(fx, m[1], variable, window.startMs, window.endMs)
        ?? { status: 404, body: { detail: `no archived series for ${m[1]} in the stub fixtures` } };
    }
    return buildSeries(fx, m[1], variable) ?? { status: 404, body: { detail: `no series for ${m[1]} in the stub fixtures` } };
  }
  if (pathname === '/scene/summary') {
    const band = params.get('band') ?? 'orbital';
    if (!BAND_RE.test(band)) return { status: 400, body: { detail: 'band must be orbital|state|basin|river' } };
    return buildSceneSummary(fx, band, params.get('basin'), asOf);
  }
  if (pathname === '/search') return buildSearch(fx, params.get('q') ?? '');
  if (pathname === '/system/health') return buildHealth(fx);
  return { status: 404, body: { detail: 'not found' } };
}

export function isErrorResult(result) {
  return result && typeof result === 'object' && 'status' in result && 'body' in result && typeof result.status === 'number';
}
