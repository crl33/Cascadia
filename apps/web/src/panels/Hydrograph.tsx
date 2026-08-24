/**
 * Hydrograph: hand-rolled SVG chart for one forecast point — the observed series on the
 * point's declared basis (stage or flow, resolveBasis), the official forecast run as a
 * visually distinct dashed series badged OFFICIAL FORECAST with issuer and issued time,
 * official threshold lines labeled with category, unit and datum, and the official crest
 * marker. Every number arrives from the API; this component only positions what the backend
 * declared (hydrograph-math.ts) and prints the refusal reason instead of mixing bases, units
 * or datums. A missing series renders an explicit empty state with its reason — never a flat
 * fake line. No entrance animation: the reduced-motion path is identical to the full one.
 */
import { useLatestRun, useStationSeries } from '../api/hooks';
import type { ProvenanceRef, RiverVisualizationState } from '../contracts/schemas';
import { ProvenanceLine } from './ProvenanceLine';
import { formatNumber, formatUtc } from './format';
import {
  crestMarker, forecastSeriesFor, formatTickUtc, linearScale, niceTicks, resolveBasis,
  seriesPath, thresholdOverlay, timeDomain, timeTicks, valueDomain,
  type TimeValuePoint,
} from './hydrograph-math';
import './hydrograph.css';

const WIDTH = 384;
const HEIGHT = 208;
const MARGIN = { top: 14, right: 10, bottom: 24, left: 46 } as const;
const DOT_SERIES_MAX_POINTS = 8;

interface PlottedPoint {
  t: number;
  v: number;
}

const isPlotted = (p: TimeValuePoint): p is PlottedPoint => p.v != null && Number.isFinite(p.v) && Number.isFinite(p.t);

/** Keep the crest label inside the viewBox when the crest sits near either edge. */
const CREST_LABEL_EDGE_PX = 30;
const crestLabelAnchor = (cx: number): 'start' | 'middle' | 'end' => {
  if (cx > WIDTH - MARGIN.right - CREST_LABEL_EDGE_PX) return 'end';
  if (cx < MARGIN.left + CREST_LABEL_EDGE_PX) return 'start';
  return 'middle';
};

interface HydrographProps {
  item: RiverVisualizationState;
  refs: Record<string, ProvenanceRef | undefined>;
}

export function Hydrograph({ item, refs }: HydrographProps) {
  const basisChoice = resolveBasis(item);
  const seriesQuery = useStationSeries(item.station_id ?? null, basisChoice.basis);
  const runQuery = useLatestRun(item.id);
  const basis = basisChoice.basis;

  if (basis == null) {
    return (
      <div className="row hydrograph" data-testid="hydrograph">
        <div className="row-head"><span className="row-title">Hydrograph</span></div>
        <p className="reason" data-testid="hydrograph-empty">Basis UNKNOWN — {basisChoice.reason}</p>
      </div>
    );
  }

  if (seriesQuery.isLoading || runQuery.isLoading) {
    return (
      <div className="row hydrograph" data-testid="hydrograph">
        <div className="row-head"><span className="row-title">Hydrograph</span></div>
        <p className="muted">Loading series…</p>
      </div>
    );
  }

  const series = seriesQuery.data ?? null;
  const run = runQuery.data ?? null;
  const thresholds = item.thresholds;

  const axisUnit =
    series?.unit
    ?? (thresholds && thresholds.basis === basis ? thresholds.unit : null)
    ?? (run && run.primary === basis ? run.unit : null);
  const axisDatum = series?.datum ?? (basis === 'stage' && thresholds && thresholds.basis === basis ? thresholds.datum ?? null : null);

  const observedPoints: TimeValuePoint[] = series ? series.points.map((p) => ({ t: Date.parse(p.t), v: p.v })) : [];
  const forecastChoice = forecastSeriesFor(run, basis, axisUnit, axisDatum);
  const forecastPoints = forecastChoice.points ?? [];
  const overlay = thresholdOverlay(thresholds, basis, axisUnit, axisDatum);
  const crest = crestMarker(item.official_forecast, basis, axisUnit, axisDatum);

  const observedValid = observedPoints.filter(isPlotted);
  const forecastValid = forecastPoints.filter(isPlotted);
  const values = [...observedValid, ...forecastValid].map((p) => p.v);
  const times = [...observedValid, ...forecastValid].map((p) => p.t);
  if (crest.marker) {
    values.push(crest.marker.v);
    times.push(crest.marker.t);
  }
  const vDomain = valueDomain(values, overlay.lines.map((line) => line.value));
  const tDomain = timeDomain(times);

  const seriesReason =
    item.station_id == null ? 'This point carries no station id; an observed series cannot be requested.'
    : seriesQuery.isError ? `Observed series unavailable: ${seriesQuery.error.message}`
    : series && series.points.length === 0 ? 'The observed series response contains no points.'
    : null;
  const runReason = runQuery.isError ? `Official forecast run unavailable: ${runQuery.error.message}` : forecastChoice.reason;

  if (!vDomain || !tDomain) {
    return (
      <div className="row hydrograph" data-testid="hydrograph">
        <div className="row-head"><span className="row-title">Hydrograph</span></div>
        <p className="reason" data-testid="hydrograph-empty">No chartable series for this point.</p>
        {seriesReason ? <p className="reason">{seriesReason}</p> : null}
        {runReason ? <p className="reason">{runReason}</p> : null}
      </div>
    );
  }

  const x = linearScale(tDomain, MARGIN.left, WIDTH - MARGIN.right);
  const y = linearScale(vDomain, HEIGHT - MARGIN.bottom, MARGIN.top);
  const yTicks = niceTicks(vDomain.min, vDomain.max, 5);
  const { ticks: xTicks, stepMs } = timeTicks(tDomain, 5);
  const observedPath = seriesPath(observedPoints, x, y);
  const forecastPath = seriesPath(forecastPoints, x, y);
  const forecastBoundaryT = forecastValid.length > 0 ? forecastValid[0]!.t : null;

  const axisUnitLabel = `${axisUnit ?? 'unit UNKNOWN'}${basis === 'stage' ? ` (${axisDatum ?? 'datum UNKNOWN'})` : ''}`;
  const ariaLabel =
    `Hydrograph for ${item.name}: ${basis} in ${axisUnitLabel}. ${observedValid.length} observed points`
    + (run && forecastValid.length > 0 ? `; official forecast by ${run.issuer} issued ${formatUtc(run.issued_at)} with ${forecastValid.length} points` : '')
    + (overlay.lines.length > 0 ? `; official thresholds ${overlay.lines.map((line) => line.category).join(', ')}` : '')
    + '. Time axis in UTC.';

  const pointTitle = (t: number, v: number) =>
    `${formatUtc(new Date(t).toISOString())} · local ${new Date(t).toLocaleString()} · ${v} ${axisUnit ?? ''}`;

  return (
    <div className="row hydrograph" data-testid="hydrograph">
      <div className="row-head">
        <span className="row-title">Hydrograph</span>
        <span className="muted mono">{basis} · {axisUnitLabel}</span>
      </div>
      <svg className="hydrograph-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={ariaLabel} data-testid="hydrograph-svg">
        <rect className="hg-frame" x={MARGIN.left} y={MARGIN.top} width={WIDTH - MARGIN.left - MARGIN.right} height={HEIGHT - MARGIN.top - MARGIN.bottom} />
        {yTicks.map((tick) => (
          <g key={`y-${tick}`}>
            <line className="hg-grid" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(tick)} y2={y(tick)} />
            <text className="hg-axis-text" x={MARGIN.left - 5} y={y(tick) + 3} textAnchor="end">{tick}</text>
          </g>
        ))}
        {xTicks.map((tick) => (
          <g key={`x-${tick}`}>
            <line className="hg-grid" x1={x(tick)} x2={x(tick)} y1={HEIGHT - MARGIN.bottom} y2={HEIGHT - MARGIN.bottom + 4} />
            <text className="hg-axis-text" x={x(tick)} y={HEIGHT - 10} textAnchor="middle">{formatTickUtc(tick, stepMs)}</text>
          </g>
        ))}
        <text className="hg-axis-unit" x={MARGIN.left} y={MARGIN.top - 4} data-testid="hydrograph-axis-unit">{axisUnitLabel}</text>
        <text className="hg-axis-text" x={WIDTH - MARGIN.right} y={HEIGHT - 10} textAnchor="end">UTC</text>
        {overlay.lines.map((line) => (
          <g key={line.category} data-testid={`hydrograph-threshold-${line.category}`}>
            <line className={`hg-threshold hg-th-${line.category}`} x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(line.value)} y2={y(line.value)} data-testid="hydrograph-threshold-line" />
            <text className={`hg-threshold-text hg-th-${line.category}-text`} x={WIDTH - MARGIN.right - 2} y={y(line.value) - 2} textAnchor="end" data-testid="hydrograph-threshold-label">
              {line.category} {formatNumber(line.value)} {axisUnitLabel}
            </text>
          </g>
        ))}
        {forecastBoundaryT != null ? (
          <g data-testid="hydrograph-register-boundary">
            <line className="hg-boundary" x1={x(forecastBoundaryT)} x2={x(forecastBoundaryT)} y1={MARGIN.top} y2={HEIGHT - MARGIN.bottom} />
            <text className="hg-boundary-text" x={x(forecastBoundaryT) + 2} y={MARGIN.top + 8}>forecast →</text>
          </g>
        ) : null}
        {observedPath ? <path className="hg-observed" d={observedPath} data-testid="hydrograph-series-observed" /> : null}
        {observedValid.length <= DOT_SERIES_MAX_POINTS
          ? observedValid.map((p) => <circle key={`od-${p.t}`} className="hg-observed-dot" cx={x(p.t)} cy={y(p.v)} r={2.4} />)
          : null}
        {forecastPath ? <path className="hg-forecast" d={forecastPath} data-testid="hydrograph-series-forecast" /> : null}
        {forecastValid.length <= DOT_SERIES_MAX_POINTS
          ? forecastValid.map((p) => <circle key={`fd-${p.t}`} className="hg-forecast-dot" cx={x(p.t)} cy={y(p.v)} r={2.4} />)
          : null}
        {crest.marker ? (
          <g data-testid="hydrograph-crest">
            <circle className="hg-crest-marker" cx={x(crest.marker.t)} cy={y(crest.marker.v)} r={3} />
            <text
              className="hg-crest-text"
              x={x(crest.marker.t)}
              y={y(crest.marker.v) - 5}
              textAnchor={crestLabelAnchor(x(crest.marker.t))}
            >
              crest {formatNumber(crest.marker.v)}
            </text>
          </g>
        ) : null}
        {observedValid.map((p) => (
          <circle key={`oh-${p.t}`} className="hg-hit" cx={x(p.t)} cy={y(p.v)} r={5}>
            <title>{pointTitle(p.t, p.v)}</title>
          </circle>
        ))}
        {forecastValid.map((p) => (
          <circle key={`fh-${p.t}`} className="hg-hit" cx={x(p.t)} cy={y(p.v)} r={5}>
            <title>{`${pointTitle(p.t, p.v)} · OFFICIAL FORECAST`}</title>
          </circle>
        ))}
      </svg>
      <div className="hg-legend">
        {series ? (
          <p className="value-line">
            <svg className="hg-swatch" viewBox="0 0 18 6" aria-hidden="true"><line className="hg-swatch-observed" x1="0" y1="3" x2="18" y2="3" /></svg>
            <span>observed {basis}</span>
            <ProvenanceLine provKey="series:observed" prov={series.provenance} truth="observation" testId="hydrograph-observed-badge" />
          </p>
        ) : null}
        {run && forecastChoice.points ? (
          <p className="value-line">
            <svg className="hg-swatch" viewBox="0 0 18 6" aria-hidden="true"><line className="hg-swatch-forecast" x1="0" y1="3" x2="18" y2="3" /></svg>
            <span>{run.issuer} · issued {formatUtc(run.issued_at)}</span>
            <ProvenanceLine provKey={`run:${run.run_id}`} prov={run.provenance} truth="authoritative_model" testId="hydrograph-forecast-badge" />
          </p>
        ) : null}
        {overlay.lines.length > 0 && thresholds ? (
          <p className="value-line">
            <span>official thresholds · {thresholds.unit}{thresholds.datum ? ` (${thresholds.datum})` : ''}</span>
            <ProvenanceLine provKey={thresholds.prov} prov={refs[thresholds.prov]} truth="authoritative_model" testId="hydrograph-thresholds-badge" />
          </p>
        ) : null}
      </div>
      {seriesReason ? <p className="reason" data-testid="hydrograph-notes">{seriesReason}</p> : null}
      {runReason ? <p className="reason">{runReason}</p> : null}
      {overlay.refusal ? <p className="reason">{overlay.refusal}</p> : null}
      {crest.reason ? <p className="reason">{crest.reason}</p> : null}
    </div>
  );
}
