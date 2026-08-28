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
import { useHefsLatest, useLatestRun, useRunsList, useSeriesWindow, useStationSeries } from '../api/hooks';
import type { ForecastRun, ProvenanceRef, RiverVisualizationState, RunListItem } from '../contracts/schemas';
import { Badge } from '../design-system/Badge';
import { BACKFILLED_BADGE } from '../design-system/badges';
import { currentRunAt, filterSeriesAt, runIsBackfilled, seriesIsBackfilled } from '../event/event-filter';
import { eventById } from '../event/registry';
import { useSceneStore } from '../state/store';
import { ProvenanceLine } from './ProvenanceLine';
import { formatNumber, formatUtc } from './format';
import {
  crestMarker, forecastSeriesFor, formatTickUtc, linearScale, niceTicks, resolveBasis,
  seriesPath, thresholdOverlay, timeDomain, timeTicks, valueDomain,
  type TimeValuePoint,
  bandPath,
  hefsBand,
} from './hydrograph-math';
import './hydrograph.css';

/** A 404 from /hefs/latest is an ANSWER (no ladder known at this knowledge time), not a
 *  failure to report; anything else — 500, timeout, a schema refusal — must say so. */
const hefsErrorIsAbsence = (error: unknown): boolean =>
  error instanceof Error && /\b404\b/.test(error.message);

const WIDTH = 384;
const HEIGHT = 208;
const MARGIN = { top: 14, right: 10, bottom: 24, left: 46 } as const;
const DOT_SERIES_MAX_POINTS = 8;

/** Archived runs-list items (event mode) carry product identity; live /runs/latest bodies do not. */
const isArchivedRun = (run: ForecastRun | RunListItem): run is RunListItem => 'product_id' in run;

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
  const timeline = useSceneStore((s) => s.timeline);
  const event = timeline.mode === 'event' && timeline.eventId !== null ? eventById(timeline.eventId) : null;
  // Live/past mode reads the as_of-keyed hooks; event mode fetches the archived window ONCE
  // (no as_of — ADR-0010) and the EVENT-time cursor filters client-side. Hook order is fixed;
  // the unused pair is disabled via null arguments.
  const seriesQuery = useStationSeries(event === null ? item.station_id ?? null : null, basisChoice.basis);
  const runQuery = useLatestRun(event === null ? item.id : null);
  const hefsQuery = useHefsLatest(event === null ? item.id : null);
  const windowSeriesQuery = useSeriesWindow(event !== null ? item.station_id ?? null : null, basisChoice.basis, event?.window ?? null);
  const runsQuery = useRunsList(event !== null ? item.id : null, event?.window ?? null);
  const basis = basisChoice.basis;

  if (basis == null) {
    return (
      <div className="row hydrograph" data-testid="hydrograph">
        <div className="row-head"><span className="row-title">Hydrograph</span></div>
        <p className="reason" data-testid="hydrograph-empty">Basis UNKNOWN — {basisChoice.reason}</p>
      </div>
    );
  }

  if (event === null ? seriesQuery.isLoading || runQuery.isLoading : windowSeriesQuery.isLoading || runsQuery.isLoading) {
    return (
      <div className="row hydrograph" data-testid="hydrograph">
        <div className="row-head"><span className="row-title">Hydrograph</span></div>
        <p className="muted">Loading series…</p>
      </div>
    );
  }

  const series = event !== null ? filterSeriesAt(windowSeriesQuery.data ?? null, timeline.at) : seriesQuery.data ?? null;
  const run = event !== null ? currentRunAt(runsQuery.data?.items ?? [], timeline.at) : runQuery.data ?? null;
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
  // In event mode the LIVE official_forecast summary (issued now, not during the event) must
  // not stretch the chart to the present: the replay-selected run's crest point is the marker.
  // the MAXIMUM of the replayed run, not its first point: correct-by-accident for the
  // single-point FLS reconstructions, wrong the day a multi-point archived run lands
  // (adversarial review 2026-08-28)
  const replayCandidates = event !== null ? forecastPoints.filter((p) => p.v != null && Number.isFinite(p.v) && Number.isFinite(p.t)) : [];
  const replayCrest = replayCandidates.length > 0
    ? replayCandidates.reduce((best, p) => (p.v! > best.v! ? p : best))
    : null;
  const crest = event !== null
    ? { marker: replayCrest === null ? null : { t: replayCrest.t, v: replayCrest.v! }, reason: null }
    : crestMarker(item.official_forecast, basis, axisUnit, axisDatum);

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
    : event === null && seriesQuery.isError ? `Observed series unavailable: ${seriesQuery.error.message}`
    : event !== null && windowSeriesQuery.isError ? `Archived series unavailable: ${windowSeriesQuery.error.message}`
    : event !== null && windowSeriesQuery.data && series && series.points.length === 0 ? 'No observation at or before this event time.'
    : series && series.points.length === 0 ? 'The observed series response contains no points.'
    : null;
  const runReason =
    event === null && runQuery.isError ? `Official forecast run unavailable: ${runQuery.error.message}`
    : event !== null && runsQuery.isError ? `Archived forecast runs unavailable: ${runsQuery.error.message}`
    : event !== null && runsQuery.data && run === null ? 'No forecast issued at or before this event time.'
    : forecastChoice.reason;

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

  // HEFS band AFTER the domains: untilMs is the chart's own window, so a 30-day ladder can
  // never stretch a 72-hour axis — rows beyond it are clipped and counted in the legend.
  const hefs = event === null ? hefsQuery.data ?? null : null;
  const hefsChoice = hefsBand(hefs, basis, axisUnit, tDomain.min, tDomain.max);
  const hefsBandD = hefsChoice.band ? bandPath(hefsChoice.band, linearScale(tDomain, MARGIN.left, WIDTH - MARGIN.right), linearScale(vDomain, HEIGHT - MARGIN.bottom, MARGIN.top)) : '';
  const hefsMedianD = hefsChoice.median ? seriesPath(hefsChoice.median, linearScale(tDomain, MARGIN.left, WIDTH - MARGIN.right), linearScale(vDomain, HEIGHT - MARGIN.bottom, MARGIN.top)) : '';

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
        <defs>
          {/* The band's 5 %-exceedance bound can exceed the value domain — precisely during a
              flood watch — and must clip to the plot area, not paint over the axes. The domain
              itself is NOT stretched by a modeled band; the frame is the honest boundary. */}
          <clipPath id="hg-plot-clip">
            <rect x={MARGIN.left} y={MARGIN.top} width={WIDTH - MARGIN.left - MARGIN.right} height={HEIGHT - MARGIN.top - MARGIN.bottom} />
          </clipPath>
        </defs>
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
        {hefsBandD ? <path className="hg-hefs-band" d={hefsBandD} clipPath="url(#hg-plot-clip)" data-testid="hydrograph-hefs-band" /> : null}
        {hefsMedianD ? <path className="hg-hefs-median" d={hefsMedianD} clipPath="url(#hg-plot-clip)" data-testid="hydrograph-hefs-median" /> : null}
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
            {seriesIsBackfilled(series) ? (
              <Badge badge={BACKFILLED_BADGE} title="Backfilled from the archive; available_at is the retrieval time, not the historical instant (ADR-0010)." testId="hydrograph-backfilled" />
            ) : null}
            <ProvenanceLine provKey="series:observed" prov={series.provenance} truth="observation" testId="hydrograph-observed-badge" />
          </p>
        ) : null}
        {run && forecastChoice.points ? (
          <p className="value-line">
            <svg className="hg-swatch" viewBox="0 0 18 6" aria-hidden="true"><line className="hg-swatch-forecast" x1="0" y1="3" x2="18" y2="3" /></svg>
            <span>{run.issuer} · issued {formatUtc(run.issued_at)}</span>
            {isArchivedRun(run) && runIsBackfilled(run) ? (
              <Badge badge={BACKFILLED_BADGE} title="Reconstructed from archived NWS text; the knowledge time is the retrieval, not the issuance (ADR-0010)." testId="hydrograph-forecast-backfilled" />
            ) : null}
            <ProvenanceLine provKey={`run:${run.run_id}`} prov={run.provenance} truth="authoritative_model" testId="hydrograph-forecast-badge" />
          </p>
        ) : null}
        {hefs && hefsChoice.band ? (
          <p className="value-line" data-testid="hydrograph-hefs-legend">
            <svg className="hg-swatch" viewBox="0 0 18 6" aria-hidden="true"><rect className="hg-swatch-hefs" x="0" y="0" width="18" height="6" /></svg>
            <span>
              HEFS exceedance {hefsChoice.levels![0]}–{hefsChoice.levels![2]} band, median dashed · cycle {formatUtc(hefs.issued_at)}
              {hefsChoice.clipped > 0 ? ` · ${hefsChoice.clipped} rows beyond the charted window not drawn` : ''}
            </span>
            <ProvenanceLine provKey="hefs:latest" prov={hefs.provenance} truth="authoritative_model" testId="hydrograph-hefs-badge" />
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
      {hefsChoice.reason ? <p className="reason" data-testid="hydrograph-hefs-reason">{hefsChoice.reason}</p> : null}
      {event === null && hefsQuery.isError && !hefsErrorIsAbsence(hefsQuery.error) ? (
        <p className="reason" data-testid="hydrograph-hefs-error">
          Official probabilistic guidance unavailable: {hefsQuery.error.message}
        </p>
      ) : null}
      {crest.reason ? <p className="reason">{crest.reason}</p> : null}
    </div>
  );
}
