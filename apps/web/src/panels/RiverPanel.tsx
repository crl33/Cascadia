/**
 * RiverPanel: renders one RiverVisualizationState — observed stage/flow (unit + datum, quality,
 * freshness), observed category with reason, the hydrograph (observed series + official
 * forecast run + thresholds + crest), trend, headroom with basis, official forecast summary,
 * thresholds table with basis/unit/datum, topology and regulation. Every value is badged;
 * every badge opens the per-value provenance popover (inspector v1).
 */
import { useRiverState } from '../api/hooks';
import { useSceneStore } from '../state/store';
import { Badge } from '../design-system/Badge';
import { CATEGORY_BADGE } from '../design-system/badges';
import type { ProvenanceRef } from '../contracts/schemas';
import { Hydrograph } from './Hydrograph';
import { ProvenanceLine } from './ProvenanceLine';
import { formatNumber, formatQuantity, formatUtc, words } from './format';

export function RiverPanel() {
  const forecastPointId = useSceneStore((s) => s.selectedForecastPointId);
  const query = useRiverState(forecastPointId);

  if (!forecastPointId) return null;
  if (query.isPending) return <section className="panel glass-surface glass-panel shape-panel" data-testid="river-panel"><p className="muted">Loading forecast point…</p></section>;
  if (query.isError) return <section className="panel glass-surface glass-panel shape-panel" data-testid="river-panel"><p className="error">Forecast point unavailable: {query.error.message}</p></section>;

  const item = query.data.items[0];
  const refs: Record<string, ProvenanceRef> = query.data.provenance_refs;
  if (!item) return <section className="panel glass-surface glass-panel shape-panel" data-testid="river-panel"><p className="muted">No forecast point item in the document.</p></section>;
  const observedQuality = item.observed ? refs[item.observed.prov]?.quality ?? [] : [];
  const { observed, trend, headroom, official_forecast: forecast, thresholds } = item;

  return (
    <section className="panel glass-surface glass-panel shape-panel" data-testid="river-panel" aria-label="River panel">
      <header className="panel-header">
        <span className="eyebrow">FORECAST POINT · {item.id}</span>
        <h2 data-testid="river-panel-name">{item.name}</h2>
        <p className="muted mono">{item.station_id ?? 'no station'} · {item.reach_id ?? 'no reach'} · {item.basin_id}</p>
      </header>

      <div className="row" data-testid="observed">
        <div className="row-head"><span className="row-title">Observed</span><span className="muted">{observed ? formatUtc(observed.valid_time) : ''}</span></div>
        {observed ? (
          <>
            <p className="value-line">stage <span className="mono value" data-testid="observed-stage">{formatQuantity(observed.stage)}</span></p>
            <p className="value-line">flow <span className="mono value" data-testid="observed-flow">{formatQuantity(observed.flow, 0)}</span></p>
            {observedQuality.length ? <p className="muted">quality: <span className="mono">{observedQuality.join(', ')}</span></p> : null}
            <ProvenanceLine provKey={observed.prov} prov={refs[observed.prov]} truth={observed.truth} testId="observed-badge" />
          </>
        ) : (
          <p className="reason">No observation in this document (UNKNOWN).</p>
        )}
        <p className="value-line">observed category <Badge badge={CATEGORY_BADGE[item.observed_category ?? 'unknown']} testId="observed-category" /></p>
        {item.observed_category_reason ? <p className="reason">{item.observed_category_reason}</p> : null}
      </div>

      <Hydrograph item={item} refs={refs} />

      <div className="row" data-testid="trend">
        <div className="row-head"><span className="row-title">Trend</span></div>
        {trend ? (
          <>
            <p className="value-line">{trend.direction.toUpperCase()} · {trend.rate ? <span className="mono">{formatQuantity(trend.rate)}</span> : 'rate unknown'} over {trend.window_h} h</p>
            <ProvenanceLine provKey={trend.prov} prov={refs[trend.prov]} truth={trend.truth} testId="trend-badge" />
          </>
        ) : <p className="reason">Trend not available (UNKNOWN).</p>}
      </div>

      <div className="row" data-testid="headroom">
        <div className="row-head"><span className="row-title">Headroom</span></div>
        {headroom ? (
          <>
            <p className="value-line">
              to <Badge badge={CATEGORY_BADGE[headroom.to_category]} /> by {headroom.basis}: <span className="mono value">{formatQuantity(headroom.value)}</span>
              {' · '}time to threshold: <span className="mono">{headroom.time_to_threshold_h == null ? 'UNKNOWN' : `${formatNumber(headroom.time_to_threshold_h)} h`}</span>
            </p>
            {headroom.reason ? <p className="reason">{headroom.reason}</p> : null}
            <ProvenanceLine provKey={headroom.prov} prov={refs[headroom.prov]} truth="cascade_derived" testId="headroom-badge" />
          </>
        ) : <p className="reason">Headroom not available: requires official thresholds on the same basis and datum.</p>}
      </div>

      <div className="row" data-testid="official-forecast">
        <div className="row-head"><span className="row-title">Official forecast</span></div>
        {forecast ? (
          <>
            <p className="value-line">{forecast.issuer} · issued {formatUtc(forecast.issued_at)} · {forecast.points} points</p>
            <p className="value-line">crest <span className="mono value" data-testid="forecast-crest">{formatQuantity(forecast.crest)}</span> at {formatUtc(forecast.crest_valid_time)} · category <Badge badge={CATEGORY_BADGE[forecast.category]} /></p>
            <ProvenanceLine provKey={forecast.prov} prov={refs[forecast.prov]} truth={forecast.truth} testId="forecast-badge" />
          </>
        ) : <p className="reason">No official forecast in this document (UNKNOWN). Official forecasts come from NWRFC via NWPS.</p>}
      </div>

      <div className="row" data-testid="thresholds">
        <div className="row-head"><span className="row-title">Official flood categories</span></div>
        {thresholds ? (
          <>
            <p className="muted">basis <span className="mono">{thresholds.basis}</span> · unit <span className="mono">{thresholds.unit}</span> · datum <span className="mono">{thresholds.datum ?? 'n/a (flow)'}</span></p>
            <table className="thresholds">
              <thead><tr><th>action</th><th>minor</th><th>moderate</th><th>major</th></tr></thead>
              <tbody><tr>
                <td className="mono" data-testid="threshold-action">{formatNumber(thresholds.action)}</td>
                <td className="mono" data-testid="threshold-minor">{formatNumber(thresholds.minor)}</td>
                <td className="mono" data-testid="threshold-moderate">{formatNumber(thresholds.moderate)}</td>
                <td className="mono" data-testid="threshold-major">{formatNumber(thresholds.major)}</td>
              </tr></tbody>
            </table>
            <ProvenanceLine provKey={thresholds.prov} prov={refs[thresholds.prov]} truth="authoritative_model" testId="thresholds-badge" />
          </>
        ) : <p className="reason">No official NWPS thresholds in this document; categories are UNKNOWN (configured values are never used).</p>}
      </div>

      <div className="row" data-testid="topology">
        <div className="row-head"><span className="row-title">Topology & regulation</span></div>
        <p className="value-line mono">upstream: {item.topology?.upstream?.length ? item.topology.upstream.join(', ') : '—'} · downstream: {item.topology?.downstream?.length ? item.topology.downstream.join(', ') : '—'}</p>
        <p className="value-line">regulation <span className="mono">{words(item.regulation?.class)}</span>{item.regulation?.regulated_by?.length ? <span className="mono"> · by {item.regulation.regulated_by.join(', ')}</span> : null}</p>
      </div>
    </section>
  );
}
