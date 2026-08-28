/**
 * BasinPanel: renders one BasinVisualizationState — name, regulation class, the four surfaces
 * (state + value + spread + confidence + reason + source-kind badge + freshness), official alerts
 * and the headline drivers. It computes nothing; UNKNOWN is shown as UNKNOWN with its reason.
 * Every value's badge opens the per-value provenance popover (inspector v1), including alert and
 * driver rows.
 *
 * Two rules this file exists to keep:
 *
 * 1. **An UNKNOWN always shows its reason.** That includes model agreement, whose `reason` the
 *    contract has carried since 1.1.0 and which this panel did not display: "UNKNOWN" alone reads
 *    as "the forecasts agree" (docs/DATA_DOCTRINE.md §12).
 * 2. **A number is never rendered without its unit and its provenance.** Driver values, surface
 *    headline values and spread points all print their unit and carry a source-kind + freshness
 *    badge. Labels are the contract's own feature ids made readable — nothing is relabelled: a
 *    `pointwise_p90` stays pointwise, because a basin mean of a per-cell percentile is not a
 *    basin-scale 90th percentile.
 */
import type { ReactNode } from 'react';
import { useBasinReservoirs, useBasinState } from '../api/hooks';
import { useSceneStore } from '../state/store';
import { Badge } from '../design-system/Badge';
import { CATEGORY_BADGE } from '../design-system/badges';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import type { BasinVisualizationState, ProvenanceRef, TruthClass } from '../contracts/schemas';
import { ProvenanceLine } from './ProvenanceLine';
import { Tier0Section } from './Tier0Section';
import { formatNumber, formatQuantity, formatUtc, words } from './format';

type Surfaces = BasinVisualizationState['surfaces'];
type SurfaceState = Surfaces['forcing'];
type Driver = NonNullable<BasinVisualizationState['headline_drivers']>[number];
type ModelProbability = NonNullable<Surfaces['hazard']['model_probability']>;

interface SurfaceRowProps {
  title: string;
  state: string;
  reason: string | null | undefined;
  provKey: string;
  refs: Record<string, ProvenanceRef | undefined>;
  truth: TruthClass | null;
  testId: string;
  extra?: ReactNode;
  /** Rendered BELOW this surface's own provenance line, so a trailing badge is never misread as
   *  belonging to the block after it. Tier 0 uses this: its statements carry their own badges. */
  after?: ReactNode;
}

function SurfaceRow({ title, state, reason, provKey, refs, truth, testId, extra, after }: SurfaceRowProps) {
  return (
    <div className="row" data-testid={testId}>
      <div className="row-head">
        <span className="row-title">{title}</span>
        <span className={`state-word state-${state}`} data-testid={`${testId}-state`}>{words(state).toUpperCase()}</span>
      </div>
      {extra}
      {reason ? <p className="reason" data-testid={`${testId}-reason`}>{reason}</p> : null}
      <ProvenanceLine provKey={provKey} prov={refs[provKey]} truth={truth} testId={`${testId}-badge`} />
      {after}
    </div>
  );
}

/**
 * The headline quantity a surface was banded from, its named spread points and its confidence.
 * Absent when the surface has no value — an UNKNOWN surface prints its reason instead, never a
 * blank number.
 */
function SurfaceValue({ surface, testId }: { surface: SurfaceState; testId: string }) {
  const spread = surface.spread ? Object.entries(surface.spread) : [];
  if (!surface.value && spread.length === 0) return null;
  const unit = surface.value?.unit ?? '';
  return (
    <p className="value-line" data-testid={testId}>
      {surface.value ? <span className="value" data-testid={`${testId}-quantity`}>{formatQuantity(surface.value, 1)}</span> : null}
      {spread.map(([key, value]) => (
        <span key={key} className="muted mono">{words(key)} {formatNumber(value)} {unit}</span>
      ))}
      <span className="muted">confidence {words(surface.confidence)}</span>
    </p>
  );
}

/**
 * The one honestly probabilistic number the platform prints: a count of model members over an
 * official threshold, said as a count. Never a percentage, never "probability of flooding".
 */
function modelProbabilityText(probability: ModelProbability): string {
  const { model, exceeds, exceeding, members } = probability;
  if (typeof exceeding === 'number' && typeof members === 'number' && typeof exceeds === 'string') {
    return `${exceeding} of ${members} ${typeof model === 'string' ? model : 'model'} members crest at or above ${exceeds}`;
  }
  return JSON.stringify(probability); // an unrecognised shape is shown verbatim, not summarised
}

function DriverRow({ driver, refs }: { driver: Driver; refs: Record<string, ProvenanceRef | undefined> }) {
  const unavailable = driver.value == null;
  return (
    <li className="driver" data-testid={`driver-${driver.feature}`}>
      <div className="driver-head">
        <span className="driver-name" title={driver.feature}>{words(driver.feature)}</span>
        <span className="driver-value mono" data-testid={`driver-${driver.feature}-value`}>
          {unavailable ? 'UNAVAILABLE' : `${formatNumber(driver.value)} ${driver.unit ?? ''}`.trim()}
        </span>
      </div>
      <span className="driver-direction mono">{words(driver.direction)}</span>
      <ProvenanceLine provKey={driver.prov} prov={refs[driver.prov]} truth={null} testId={`driver-${driver.feature}-badge`} />
    </li>
  );
}

type AntecedentEntry = NonNullable<BasinVisualizationState['antecedent_precip']>[number];

/**
 * Observed trailing-window precipitation. Three honesty rules travel from the contract to the
 * screen intact: the window ends at the newest OBSERVED hour (printed, so nobody reads it as
 * "the last N hours on the clock"); a partial sum keeps its `reason` beside the number, because
 * the number alone is a known underestimate; and an absent total prints its reason, never 0 mm —
 * zero rain and unknown rain are different facts.
 */
export function AntecedentSection({ entries, refs }: { entries: AntecedentEntry[]; refs: Record<string, ProvenanceRef | undefined> }) {
  if (entries.length === 0) return null;
  const anchor = entries.find((e) => e.window_end != null);
  return (
    <div className="row" data-testid="antecedent-precip">
      <div className="row-head">
        <span className="row-title">Antecedent precipitation</span>
        {anchor ? <span className="muted mono" data-testid="antecedent-window-end">to {formatUtc(anchor.window_end)}</span> : null}
      </div>
      <ul>
        {entries.map((e) => (
          <li key={e.window_h} className="mono" data-testid={`antecedent-${e.window_h}h`}>
            {e.window_h} h · {e.total ? `${formatQuantity(e.total, 1)} (${e.hours_present}/${e.hours_expected} hours)` : 'UNKNOWN'}
            {e.reason ? <span className="reason" data-testid={`antecedent-${e.window_h}h-reason`}> — {e.reason}</span> : null}
          </li>
        ))}
      </ul>
      <ProvenanceLine provKey={entries[0].prov} prov={refs[entries[0].prov]} truth={entries[0].truth} testId="antecedent-badge" />
    </div>
  );
}

const VARIABLE_LABEL: Record<string, string> = {
  forebay_elevation: 'forebay', storage: 'storage', inflow: 'inflow', outflow: 'outflow',
};

/**
 * Reservoir state for a regulated basin: the latest observation per (dam, variable), verbatim.
 * Long-form units are the provider's own and stay unabbreviated; a forebay elevation renders
 * with its no-datum caveat, because a number on an unstated datum invites false comparison;
 * an unregulated basin renders nothing at all — no section, no empty shell.
 */
export function ReservoirsSection({ basinId }: { basinId: string }) {
  const query = useBasinReservoirs(basinId);
  const doc = query.data;
  if (!doc || doc.reservoirs.length === 0) return null;
  const refs = doc.provenance_refs;
  return (
    <div className="row" data-testid="reservoirs">
      <div className="row-head"><span className="row-title">Reservoirs</span></div>
      <ul>
        {doc.reservoirs.map((r) => (
          <li key={r.station_id} data-testid={`reservoir-${r.lid}`}>
            <div className="driver-head">
              <span className="driver-name">{r.name}</span>
              {r.prov ? <ProvenancePopover provKey={r.prov} prov={refs[r.prov]} truth={null} /> : null}
            </div>
            {Object.keys(r.variables).length > 0 ? (
              <p className="value-line mono" data-testid={`reservoir-${r.lid}-values`}>
                {Object.entries(r.variables).map(([name, v]) => (
                  <span key={name}>
                    {VARIABLE_LABEL[name] ?? words(name)} {v.value === null ? 'UNKNOWN' : formatNumber(v.value)} {v.unit}
                    {name === 'forebay_elevation' ? <span className="muted"> (datum unstated)</span> : null}
                  </span>
                ))}
              </p>
            ) : (
              <p className="reason">No series served for this dam at this knowledge time.</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function BasinPanel() {
  const selectedBasinId = useSceneStore((s) => s.selectedBasinId);
  const query = useBasinState(selectedBasinId);

  if (!selectedBasinId) return null;
  if (query.isPending) return <section className="panel" data-testid="basin-panel"><p className="muted">Loading basin state…</p></section>;
  if (query.isError) return <section className="panel" data-testid="basin-panel"><p className="error">Basin state unavailable: {query.error.message}</p></section>;

  const item: BasinVisualizationState | undefined = query.data.items[0];
  const refs = query.data.provenance_refs;
  if (!item) return <section className="panel" data-testid="basin-panel"><p className="muted">No basin item in the document.</p></section>;

  const { susceptibility, forcing, hazard, agreement } = item.surfaces;
  const hazardProv = hazard.official_prov ?? hazard.prov;
  const drivers = item.headline_drivers ?? [];

  return (
    <section className="panel" data-testid="basin-panel" aria-label="Basin panel">
      <header className="panel-header">
        <span className="eyebrow">BASIN · {item.id}</span>
        <h2 data-testid="basin-panel-name">{item.name}</h2>
        <p className="muted">regulation: <span className="mono">{words(item.regulation_class)}</span> · valid {formatUtc(query.data.time.valid)} ({query.data.time.mode})</p>
      </header>

      <SurfaceRow
        title="Basin susceptibility"
        state={susceptibility.state}
        reason={susceptibility.reason}
        provKey={susceptibility.prov}
        refs={refs}
        truth={susceptibility.truth}
        testId="surface-susceptibility"
        extra={<SurfaceValue surface={susceptibility} testId="surface-susceptibility-value" />}
        // Tier 0 lives INSIDE the susceptibility row because it answers questions about the same
        // river state — but AFTER the band's own provenance line, so the band keeps its badge and
        // Tier 0's separately-provenanced statements keep theirs. It is never folded into the
        // banded index above it, which is unchanged and is still the level state.
        after={
          <Tier0Section
            state={item.hydrologic_state}
            changes={item.state_change}
            refs={refs}
            surfaceReason={susceptibility.reason}
          />
        }
      />
      <SurfaceRow
        title={`Meteorological forcing${forcing.horizon_h ? ` · ${forcing.horizon_h} h` : ''}`}
        state={forcing.state}
        reason={forcing.reason}
        provKey={forcing.prov}
        refs={refs}
        truth={forcing.truth}
        testId="surface-forcing"
        extra={<SurfaceValue surface={forcing} testId="surface-forcing-value" />}
      />
      <AntecedentSection entries={item.antecedent_precip ?? []} refs={refs} />
      <ReservoirsSection basinId={item.id} />
      <SurfaceRow
        title={`Flood hazard · ${hazard.horizon_h} h`}
        state={hazard.official_category}
        reason={hazard.reason}
        provKey={hazardProv}
        refs={refs}
        truth={hazard.truth}
        testId="surface-hazard"
        extra={
          <p className="value-line">
            official category <Badge badge={CATEGORY_BADGE[hazard.official_category]} testId="hazard-category" />
            {hazard.model_probability
              ? <span className="muted" data-testid="hazard-model-probability">· {modelProbabilityText(hazard.model_probability)}</span>
              : <span className="muted">· no model member count at this point</span>}
          </p>
        }
      />
      <div className="row" data-testid="surface-agreement">
        <div className="row-head">
          <span className="row-title">Model agreement</span>
          <span className={`state-word state-${agreement.state}`} data-testid="surface-agreement-state">{agreement.state.toUpperCase()}</span>
        </div>
        {/* The contract carries this reason and the panel must print it: an UNKNOWN or a LOW
            agreement is only meaningful with the sentence that says which forecast is missing
            or how the two differ. Neither forecast is corrected by the other. */}
        {agreement.reason ? (
          <p className="reason" data-testid="surface-agreement-reason">{agreement.reason}</p>
        ) : agreement.state === 'unknown' ? (
          <p className="reason" data-testid="surface-agreement-reason">
            Model agreement is UNKNOWN and this document carries no reason for it. UNKNOWN is not
            “the forecasts agree”.
          </p>
        ) : null}
        {agreement.prov && agreement.prov.length > 0 ? (
          agreement.prov.map((key) => <ProvenanceLine key={key} provKey={key} prov={refs[key]} truth={null} testId={`surface-agreement-${key}`} />)
        ) : (
          <p className="reason">No forecast is referenced for this comparison.</p>
        )}
      </div>

      <div className="row">
        <div className="row-head"><span className="row-title">Official alerts</span></div>
        {item.official_alerts && item.official_alerts.length > 0 ? (
          <ul>
            {item.official_alerts.map((a) => (
              <li key={a.id} className="mono">
                {a.issuer}: {a.event} {a.severity ?? ''} (onset {formatUtc(a.onset)}){' '}
                <ProvenancePopover provKey={a.prov} prov={refs[a.prov]} truth={null} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="reason" data-testid="alerts-empty">No official alerts for this basin at this knowledge time. Watches and warnings are issued by the National Weather Service and polled every five minutes; an empty list means none of the active ones cover this basin.</p>
        )}
      </div>
      <div className="row" data-testid="headline-drivers">
        <div className="row-head"><span className="row-title">Headline drivers</span></div>
        {drivers.length > 0 ? (
          <ul className="drivers">
            {drivers.map((d) => <DriverRow key={d.feature} driver={d} refs={refs} />)}
          </ul>
        ) : (
          <p className="reason" data-testid="drivers-empty">No headline drivers in this document: no surface produced one at this knowledge time.</p>
        )}
      </div>
      {item.outlet_forecast_point_id ? <p className="muted">outlet forecast point: <span className="mono">{item.outlet_forecast_point_id}</span></p> : null}
    </section>
  );
}
