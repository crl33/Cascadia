/**
 * Shared SPIKE API SPEC router for the Node stub server and the Cloudflare Pages Function.
 * Pure: takes preloaded fixtures, a pathname, and search params; returns a body or {status, body}.
 */
import {
  buildBasins, buildGeometry, buildBasinState, buildVizBasins, buildVizRivers, buildRiverState,
  buildRunsLatest, buildSeries, buildSceneSummary, buildSearch, buildHealth,
} from './stub-data.mjs';

const BAND_RE = /^(orbital|state|basin|river)$/;

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
  if ((m = pathname.match(/^\/stations\/([^/]+)\/series$/))) {
    const variable = params.get('variable') ?? 'stage';
    if (!/^(stage|flow)$/.test(variable)) return { status: 400, body: { detail: 'variable must be stage|flow' } };
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
