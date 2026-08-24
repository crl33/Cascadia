/**
 * ForecastEvolution: the EVENT_ZERO §8 table rendered live from stored rows — one row per
 * forecast run whose issuance the event cursor has crossed (rows appear as the scrub crosses
 * each issued_at). The replay-selected run is marked CURRENT; every earlier run stays visible,
 * marked SUPERSEDED — superseded runs are shown as superseded, never deleted. Crest timing is
 * the product's crest time BIN, never a precise prediction. Once the cursor passes the
 * observed crest, the error column shows forecast − observed: plain arithmetic on two
 * displayed FACT values, both provenances shown. Reconstructed/backfilled runs carry the
 * BACKFILLED badge (ADR-0010: their knowledge time is the 2026 retrieval, not the 2025
 * issuance). No narrative, no dramatization — a table.
 */
import { useRiverState, useRunsList, useSeriesWindow } from '../api/hooks';
import type { RunListItem } from '../contracts/schemas';
import { Badge } from '../design-system/Badge';
import { BACKFILLED_BADGE } from '../design-system/badges';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import { resolveBasis } from '../panels/hydrograph-math';
import { ProvenanceLine } from '../panels/ProvenanceLine';
import { formatQuantity, formatUtc } from '../panels/format';
import { useSceneStore } from '../state/store';
import { observedCrest, runIsBackfilled, runsIssuedAtOrBefore, seriesIsBackfilled } from './event-filter';
import { eventById } from './registry';

/** Fixed-offset PST label (UTC−8; no DST in December — docs/EVENT_ZERO.md convention). */
const pstLabel = (iso: string): string => {
  const shifted = new Date(Date.parse(iso) - 8 * 3_600_000);
  return `${shifted.toISOString().slice(5, 16).replace('T', ' ')} PST`;
};

const crestOf = (run: RunListItem): { text: string; t: string | null } => {
  const point = run.points[0];
  if (!point) return { text: 'UNKNOWN', t: null };
  const value = run.primary === 'stage' ? point.stage : point.flow;
  if (value == null) return { text: 'UNKNOWN', t: point.t };
  return {
    text: formatQuantity({ value, unit: run.unit, datum: run.primary === 'stage' ? run.stage_datum ?? null : null }, 1),
    t: point.t,
  };
};

export function ForecastEvolution() {
  const timeline = useSceneStore((s) => s.timeline);
  const forecastPointId = useSceneStore((s) => s.selectedForecastPointId);
  const event = timeline.mode === 'event' && timeline.eventId !== null ? eventById(timeline.eventId) : null;
  const stateQuery = useRiverState(event !== null ? forecastPointId : null);
  const item = stateQuery.data?.items[0] ?? null;
  const basis = item !== null ? resolveBasis(item).basis : null;
  const runsQuery = useRunsList(event !== null ? forecastPointId : null, event?.window ?? null);
  const seriesQuery = useSeriesWindow(event !== null && item !== null ? item.station_id ?? null : null, basis, event?.window ?? null);

  if (event === null || forecastPointId === null) return null;

  const runs = runsQuery.data?.items ?? [];
  const visible = runsIssuedAtOrBefore(runs, timeline.at);
  const current = visible.length > 0 ? visible[visible.length - 1]! : null;
  const series = seriesQuery.data ?? null;
  const crest = observedCrest(series);
  const crestPassed = crest !== null && timeline.at !== null && Date.parse(timeline.at) >= Date.parse(crest.t);

  // Error only on a matching basis, unit and (for stage) datum — never converted, never mixed.
  const errorFor = (run: RunListItem): string => {
    if (!crestPassed || crest === null || series === null) return '—';
    const point = run.points[0];
    const value = run.primary === 'stage' ? point?.stage : point?.flow;
    if (value == null) return '—';
    if (run.primary !== series.variable || run.unit !== series.unit) return '—';
    // A stage error is a comparison, so an undeclared datum refuses exactly like a mismatched
    // one — a datum is never assumed (ADR-0009). `stage_datum` describes the run's stage column.
    if (run.primary === 'stage' && (run.stage_datum == null || series.datum == null || run.stage_datum !== series.datum)) return '—';
    const error = value - crest.v;
    return `${error >= 0 ? '+' : '−'}${Math.abs(error).toFixed(2)} ${run.unit}`;
  };

  return (
    <section className="panel" data-testid="forecast-evolution" aria-label="Forecast evolution">
      <header className="panel-header">
        <span className="eyebrow">FORECAST EVOLUTION · {event.label}</span>
        <h2>Runs vs observed crest</h2>
        <p className="muted">
          Official forecast crests as issued, in issuance order. Crest timing is the product's crest
          time bin, not a precise prediction. Superseded runs stay visible — nothing is deleted.
        </p>
      </header>
      {runsQuery.isPending ? <p className="muted">Loading archived forecast runs…</p> : null}
      {runsQuery.isError ? <p className="error">Forecast runs unavailable: {runsQuery.error.message}</p> : null}
      {runsQuery.isSuccess && runs.length === 0 ? (
        <p className="reason">No forecast runs in the archive for this window (UNKNOWN — the reconstruction has not been ingested).</p>
      ) : null}
      {runsQuery.isSuccess && runs.length > 0 && visible.length === 0 ? (
        <p className="reason" data-testid="evolution-empty">
          No forecast issued yet at this event time ({formatUtc(timeline.at)}).
        </p>
      ) : null}
      {visible.length > 0 ? (
        <div className="evolution-table-wrap">
          <table className="thresholds evolution-table">
            <thead>
              <tr>
                <th>issued (UTC)</th>
                <th>issued (PST)</th>
                <th>forecast crest</th>
                <th>crest bin</th>
                <th>error vs observed</th>
                <th>status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((run) => {
                const c = crestOf(run);
                const isCurrent = current !== null && run.run_id === current.run_id;
                return (
                  <tr
                    key={run.run_id}
                    data-testid="evolution-run"
                    data-superseded={isCurrent ? 'false' : 'true'}
                    className={isCurrent ? 'evolution-current' : 'evolution-superseded'}
                  >
                    <td className="mono">{formatUtc(run.issued_at)}</td>
                    <td className="mono muted">{pstLabel(run.issued_at)}</td>
                    <td className="mono value" data-testid="evolution-crest">{c.text}</td>
                    <td className="mono muted">{c.t ? formatUtc(c.t) : '—'}</td>
                    <td className="mono" data-testid="evolution-error">{errorFor(run)}</td>
                    <td>
                      <span
                        className={`state-word ${isCurrent ? 'state-none' : 'state-unknown'}`}
                        data-testid={isCurrent ? 'evolution-status-current' : 'evolution-status-superseded'}
                      >
                        {isCurrent ? 'CURRENT' : 'SUPERSEDED'}
                      </span>{' '}
                      <ProvenancePopover provKey={run.run_id} prov={run.provenance} truth="authoritative_model" testId="evolution-run-badge" />
                      {runIsBackfilled(run) ? (
                        <Badge
                          badge={BACKFILLED_BADGE}
                          title="Reconstructed from archived NWS text; the knowledge time is the 2026 retrieval, not the 2025 issuance (ADR-0010)."
                          testId="evolution-backfilled"
                        />
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
      {visible.length > 0 ? (
        crestPassed && crest !== null && series !== null ? (
          <p className="value-line" data-testid="evolution-observed-crest">
            observed crest{' '}
            <span className="mono value">{formatQuantity({ value: crest.v, unit: series.unit, datum: series.datum ?? null }, 2)}</span>
            {' at '}
            <span className="mono">{formatUtc(crest.t)}</span>
            {seriesIsBackfilled(series) ? (
              <Badge badge={BACKFILLED_BADGE} title="Backfilled 2026-08 from the USGS archive; available_at is the retrieval time (ADR-0010)." />
            ) : null}
            <ProvenanceLine provKey="series:event-window" prov={series.provenance} truth="observation" testId="evolution-observed-badge" />
          </p>
        ) : (
          <p className="reason">Observed crest not yet reached at this event time; the error column fills once it is.</p>
        )
      ) : null}
      <p className="muted">error = forecast crest − observed crest (plain arithmetic on the two values shown).</p>
    </section>
  );
}
