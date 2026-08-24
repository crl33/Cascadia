/**
 * Pure builders for the dev stub API (no server, no I/O besides loadFixtures).
 * Owns: turning the committed fixtures (geo LOD GeoJSON, the Skagit/MVEW1 contract envelopes,
 * the MVEW1 live-capture subset) into SPIKE API SPEC responses. Everything not covered by a
 * fixture is emitted as UNKNOWN with an explicit reason — never as calm, zero or a made-up value.
 * The vitest suite validates buildVizBasins() against the JSON Schema with ajv.
 *
 * Node-only I/O (`loadFixtures`, `REPO_ROOT`) lives in stub-load.mjs so the Cloudflare
 * Pages Function can import these builders without `node:fs`.
 */

/** Verified seed stations (docs/V1_AUDIT.md §8, 2026-08-22). Not scientific values: ids, names, coordinates. */
export const SEED_POINTS = [
  { id: 'fp:nwps:RNTW1', lid: 'RNTW1', name: 'Cedar River at Renton', station_id: 'station:usgs:12119000', basin_id: 'basin:cedar', location: [-122.2025, 47.4825], regulation: { class: 'partially_regulated', regulated_by: ['reservoir:chester-morse'] } },
  { id: 'fp:nwps:CRNW1', lid: 'CRNW1', name: 'Snoqualmie River near Carnation', station_id: 'station:usgs:12149000', basin_id: 'basin:snohomish-snoqualmie', location: [-121.9242, 47.6656], regulation: { class: 'natural', regulated_by: [] } },
  { id: 'fp:nwps:MVEW1', lid: 'MVEW1', name: 'Skagit River near Mount Vernon', station_id: 'station:usgs:12200500', basin_id: 'basin:skagit', location: [-122.3342, 48.4453], regulation: { class: 'regulated', regulated_by: ['reservoir:ross-lake', 'reservoir:baker'] } },
  { id: 'fp:nwps:NKSW1', lid: 'NKSW1', name: 'Nooksack River at Ferndale', station_id: 'station:usgs:12213100', basin_id: 'basin:nooksack', location: [-122.5897, 48.8467], regulation: { class: 'natural', regulated_by: [] } },
  { id: 'fp:nwps:AUBW1', lid: 'AUBW1', name: 'Green River near Auburn', station_id: 'station:usgs:12113000', basin_id: 'basin:green-duwamish', location: [-122.2017, 47.3081], regulation: { class: 'regulated', regulated_by: ['reservoir:howard-hanson'] } },
  { id: 'fp:nwps:WRAW1', lid: 'WRAW1', name: 'White River at R St near Auburn', station_id: 'station:usgs:12100490', basin_id: 'basin:puyallup-white', location: [-122.2317, 47.295], regulation: { class: 'regulated', regulated_by: ['reservoir:mud-mountain'] } },
];

export function buildBasins(fx) {
  const items = fx.basinLod.features.map((f) => {
    const p = f.properties;
    return {
      id: p.id, name: p.name, regulation_class: p.regulation_class, outlet_forecast_point_id: p.outlet_forecast_point_id,
      centroid: p.centroid, bbox: p.bbox, area_km2_wbd_sum: p.area_km2_wbd_sum, huc8: p.huc8,
    };
  });
  return { items, provenance: fx.basinLod.provenance };
}

export function buildGeometry(fx, id, lod) {
  const coll = lod === 'basin' ? fx.basinLod : fx.stateLod;
  const feature = coll.features.find((f) => f.id === id || f.properties?.id === id);
  if (!feature) return null;
  return { ...feature, properties: { ...feature.properties, provenance: coll.provenance } };
}

const UNKNOWN_SURFACE = (prov, reason, horizon) => ({
  state: 'unknown', ...(horizon ? { horizon_h: horizon } : {}), prov, truth: 'cascade_derived',
  confidence: 'unknown', experimental: true, reason,
});

/** A BasinVisualizationState item that is honestly UNKNOWN everywhere (no fixture for it). */
export function unknownBasinItem(basinFeature) {
  const p = basinFeature.properties;
  const hazardProv = `unknown-hazard-${p.id.split(':')[1]}`;
  return {
    item: {
      id: p.id, name: p.name, regulation_class: p.regulation_class,
      surfaces: {
        susceptibility: UNKNOWN_SURFACE('cascade-susceptibility', 'Susceptibility index not implemented in the spike (ROADMAP Phase 3).'),
        forcing: UNKNOWN_SURFACE('cascade-forcing', 'Meteorological forcing not ingested in the spike (ROADMAP Phase 2).', 72),
        hazard: {
          horizon_h: 72, official_category: 'unknown', official_prov: null, prov: hazardProv, truth: 'authoritative_model',
          model_probability: null, cascade_index: null,
          reason: `No NWPS forecast for ${p.outlet_forecast_point_id} in the spike fixtures; official category unknown.`,
        },
        agreement: { state: 'unknown', explanation_ref: null, prov: [] },
      },
      tension: null, headline_drivers: [], official_alerts: [],
      outlet_forecast_point_id: p.outlet_forecast_point_id,
      geometry_ref: { lod: 'basin', feature_id: p.id, url: `/basins/${p.id}/geometry?lod=basin` },
      label_priority: 2,
    },
    provenance_refs: {
      [hazardProv]: {
        source_id: 'src:nwps-v1', source_kind: 'UNKNOWN', product_id: 'product:nwps-stageflow-forecast',
        freshness: { state: 'missing' }, quality: ['missing'], label: 'NWPS official forecast not loaded in the dev stub',
      },
    },
  };
}

export function buildVizBasins(fx, asOf = null) {
  const env = fx.basinEnvelope;
  const items = [];
  const provenance_refs = {};
  const fixtureById = new Map(env.items.map((i) => [i.id, i]));
  for (const f of fx.basinLod.features) {
    const fixtureItem = fixtureById.get(f.properties.id);
    if (fixtureItem) {
      items.push(fixtureItem);
      Object.assign(provenance_refs, env.provenance_refs);
    } else {
      const u = unknownBasinItem(f);
      items.push(u.item);
      Object.assign(provenance_refs, {
        'cascade-susceptibility': env.provenance_refs['cascade-susceptibility'],
        'cascade-forcing': env.provenance_refs['cascade-forcing'],
      }, u.provenance_refs);
    }
  }
  return { ...env, as_of: asOf ?? env.as_of, items, provenance_refs };
}

export function buildBasinState(fx, id, asOf = null) {
  const all = buildVizBasins(fx, asOf);
  const item = all.items.find((i) => i.id === id);
  if (!item) return null;
  return { ...all, items: [item], provenance_refs: pruneRefs([item], all.provenance_refs) };
}

/** RiverVisualizationState for a seed point with no fixture: observed/thresholds/forecast absent, category UNKNOWN. */
export function unknownRiverItem(point) {
  return {
    id: point.id, name: point.name, station_id: point.station_id, reach_id: null, basin_id: point.basin_id,
    observed: null, observed_category: 'unknown',
    observed_category_reason: `No USGS observation or NWPS thresholds for ${point.lid} in the spike fixtures.`,
    trend: null, headroom: null, official_forecast: null, thresholds: null,
    topology: { upstream: [], downstream: [] }, regulation: point.regulation, location: point.location, flow_visual_intensity: null,
  };
}

/**
 * AUBW1 (flow-basis) fixture extension: item + provenance refs + samples live in
 * dev/fixtures/mvew1-samples.json (`aubw1_*` keys) so the Pages Function bundle picks them up
 * without a code change there. Guarded: an fx bundled before the extension falls back to the
 * honest UNKNOWN item.
 */
const aubw1State = (fx) => fx.samples?.aubw1_state ?? null;

/** Resolve one seed point's RiverVisualizationState item and the provenance refs it may use. */
function riverItemFor(fx, point) {
  const env = fx.riverEnvelope;
  const fixtureItem = env.items.find((i) => i.id === point.id);
  if (fixtureItem) return { item: fixtureItem, refs: env.provenance_refs };
  const aub = aubw1State(fx);
  if (aub && aub.item.id === point.id) return { item: aub.item, refs: { ...env.provenance_refs, ...aub.provenance_refs } };
  return { item: unknownRiverItem(point), refs: env.provenance_refs };
}

export function buildRiverState(fx, lid, asOf = null) {
  const env = fx.riverEnvelope;
  const point = SEED_POINTS.find((p) => p.lid === lid);
  if (!point) return null;
  const { item, refs } = riverItemFor(fx, point);
  return { ...env, as_of: asOf ?? env.as_of, items: [item], provenance_refs: pruneRefs([item], refs) };
}

export function buildVizRivers(fx, basinId, asOf = null) {
  const env = fx.riverEnvelope;
  const items = [];
  const refs = { ...env.provenance_refs };
  for (const p of SEED_POINTS) {
    if (p.basin_id !== basinId) continue;
    const resolved = riverItemFor(fx, p);
    items.push(resolved.item);
    Object.assign(refs, resolved.refs);
  }
  return { ...env, as_of: asOf ?? env.as_of, items, provenance_refs: pruneRefs(items, refs) };
}

function pruneRefs(items, refs) {
  const used = new Set();
  const visit = (o) => {
    if (Array.isArray(o)) return o.forEach(visit);
    if (o && typeof o === 'object') {
      for (const [k, v] of Object.entries(o)) {
        if ((k === 'prov' || k === 'official_prov') && typeof v === 'string') used.add(v);
        else if (k === 'prov' && Array.isArray(v)) v.forEach((x) => used.add(x));
        else visit(v);
      }
    }
  };
  visit(items);
  return Object.fromEntries(Object.entries(refs).filter(([k]) => used.has(k)));
}

export function buildSceneSummary(fx, band, basinId, asOf = null) {
  const as_of = asOf ?? fx.basinEnvelope.as_of;
  if (band === 'orbital' || band === 'state') return { band, as_of, basins: buildVizBasins(fx, asOf), rivers: null };
  const basins = basinId ? buildBasinState(fx, basinId, asOf) : buildVizBasins(fx, asOf);
  const rivers = basinId ? buildVizRivers(fx, basinId, asOf) : null;
  return { band, as_of, basins, rivers };
}

export function buildSearch(fx, q) {
  const needle = (q ?? '').trim().toLowerCase();
  if (!needle) return { items: [] };
  const hit = (...fields) => fields.some((f) => String(f ?? '').toLowerCase().includes(needle));
  const items = [];
  for (const f of fx.basinLod.features) {
    const p = f.properties;
    if (hit(p.id, p.name)) items.push({ id: p.id, kind: 'basin', name: p.name, basin_id: p.id, location: p.centroid });
  }
  for (const p of SEED_POINTS) {
    if (hit(p.id, p.name, p.lid)) items.push({ id: p.id, kind: 'forecast_point', name: p.name, basin_id: p.basin_id, location: p.location });
    if (hit(p.station_id)) items.push({ id: p.station_id, kind: 'station', name: `USGS ${p.station_id.split(':')[2]} (${p.name})`, basin_id: p.basin_id, location: p.location });
  }
  return { items: items.slice(0, 20) };
}

/** Official NWRFC forecast runs from the live-capture subsets (partial point counts stated in the labels). */
export function buildRunsLatest(fx, lid) {
  if (lid === 'MVEW1') {
    const sf = fx.samples.mvew1_stageflow;
    const ref = fx.riverEnvelope.provenance_refs['nwps-forecast-mvew1'];
    return {
      run_id: `run:nwps:MVEW1:${sf.issued}`, issued_at: sf.issued, issuer: 'NWRFC', primary: 'stage', unit: 'ft', datum: 'NGVD29',
      points: sf.data.map((d) => ({ t: d.validTime, stage: d.primary, flow: d.secondary == null ? null : Math.round(d.secondary * 1000) })),
      provenance: { ...ref, label: `${ref.label} — dev stub: first ${sf.data.length} of 31 points (kcfs converted to cfs)` },
    };
  }
  const aub = aubw1State(fx);
  if (lid === 'AUBW1' && aub && fx.samples.aubw1_stageflow) {
    // Flow-primary point; the flat `datum` rides along for stage values (spike-report-2026-08-22.md
    // finding 3) — the primary values here are flow in cfs (kcfs × 1000, 2 decimals kept).
    const sf = fx.samples.aubw1_stageflow;
    const ref = aub.provenance_refs['nwps-forecast-aubw1'];
    return {
      run_id: `run:nwps:AUBW1:${sf.issued}`, issued_at: sf.issued, issuer: 'NWRFC', primary: 'flow', unit: 'cfs', datum: 'NGVD29',
      points: sf.data.map((d) => ({ t: d.validTime, stage: null, flow: Math.round(d.primary * 1000 * 100) / 100 })),
      provenance: { ...ref, label: `${ref.label} — dev stub: first ${sf.data.length} of 40 points (kcfs converted to cfs)` },
    };
  }
  return null;
}

/** USGS IV latest values from the live-capture subsets; one point per variable per station. */
export function buildSeries(fx, stationId, variable) {
  if (stationId === 'station:usgs:12200500') {
    const code = variable === 'flow' ? '00060' : '00065';
    const rows = fx.samples.usgs_latest.filter((r) => r.parameter_code === code);
    const ref = fx.riverEnvelope.provenance_refs['usgs-iv-12200500'];
    return {
      station_id: stationId, variable, unit: variable === 'flow' ? 'cfs' : 'ft', datum: variable === 'flow' ? null : 'NGVD29',
      points: rows.map((r) => ({ t: new Date(r.time).toISOString(), v: Number(r.value), quality: [r.approval_status.toLowerCase()] })),
      provenance: { ...ref, label: `${ref.label} — dev stub: latest value only` },
    };
  }
  const aub = aubw1State(fx);
  if (stationId === 'station:usgs:12113000' && variable === 'flow' && aub && fx.samples.aubw1_usgs_latest) {
    const rows = fx.samples.aubw1_usgs_latest.filter((r) => r.parameter_code === '00060');
    const ref = aub.provenance_refs['usgs-iv-12113000'];
    return {
      station_id: stationId, variable, unit: 'cfs', datum: null,
      points: rows.map((r) => ({ t: new Date(r.time).toISOString(), v: Number(r.value), quality: [r.approval_status.toLowerCase()] })),
      provenance: { ...ref, label: `${ref.label} — dev stub: latest value only` },
    };
  }
  return null;
}

const SECONDS = (a, b) => Math.max(0, Math.round((a.getTime() - b.getTime()) / 1000));
const freshnessAt = (validTime, cadence, grace, now) => {
  if (!validTime) return { age_seconds: null, state: 'missing' };
  const age = SECONDS(now, new Date(validTime));
  return { age_seconds: age, state: age > cadence + grace ? 'stale' : 'current' };
};

/** Freshness computed at read time from fixture timestamps and cadences (docs/DATA_DOCTRINE.md §5). */
export function buildHealth(fx, now = new Date()) {
  const refs = fx.riverEnvelope.provenance_refs;
  const usgs = refs['usgs-iv-12200500'];
  const fc = refs['nwps-forecast-mvew1'];
  const th = refs['nwps-thresholds-mvew1'];
  const freshness = {
    'product:usgs-iv': freshnessAt(usgs.valid_time, 900, 4500, now),
    'product:nwps-forecast': freshnessAt(fc.issued_at, 86400, 64800, now),
    'product:nwps-thresholds': freshnessAt(th.retrieved_at, 21600, 43200, now),
  };
  const anyStale = Object.values(freshness).some((f) => f.state !== 'current');
  return {
    status: anyStale ? 'degraded' : 'ok',
    providers: {
      usgs: { state: 'healthy', last_success_at: usgs.retrieved_at, last_error: null },
      nwps: { state: 'healthy', last_success_at: fc.retrieved_at, last_error: null },
    },
    freshness,
  };
}

/* ---- Event Zero archived-window endpoints (P2) ----
   Backed by `event_zero_mvew1` in dev/fixtures/mvew1-samples.json (FACT values from
   docs/EVENT_ZERO.md — see the fixture _note). Guarded: an fx bundled before this extension
   404s honestly instead of fabricating. */
const eventZero = (fx) => fx.samples?.event_zero_mvew1 ?? null;

/** GET /stations/{id}/series?start=&end= — the archived series, filtered by valid time. */
export function buildSeriesWindow(fx, stationId, variable, startMs, endMs) {
  const ev = eventZero(fx);
  if (!ev || stationId !== ev.series.station_id || variable !== ev.series.variable) return null;
  const points = ev.series.points.filter((p) => {
    const t = Date.parse(p.t);
    return t >= startMs && t <= endMs;
  });
  return { ...ev.series, points };
}

/** GET /forecast-points/{lid}/runs?start=&end= — every run issued in the window, ascending. */
export function buildRunsList(fx, lid, startMs, endMs) {
  const ev = eventZero(fx);
  if (!ev || lid !== ev.lid) return null;
  const items = ev.runs.filter((r) => {
    const t = Date.parse(r.issued_at);
    return t >= startMs && t <= endMs;
  });
  return {
    lid,
    fp_id: `fp:nwps:${lid}`,
    start: new Date(startMs).toISOString().replace('.000Z', 'Z'),
    end: new Date(endMs).toISOString().replace('.000Z', 'Z'),
    items,
  };
}
