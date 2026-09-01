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
import { useBasinState, useVizRivers } from '../api/hooks';
import { useSceneStore } from '../state/store';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import type { BasinVisualizationState } from '../contracts/schemas';
import { Badge } from '../design-system/Badge';
import { CATEGORY_BADGE } from '../design-system/badges';
import { AntecedentSection } from './AntecedentSection';
import { FloodMappingNote } from './FloodMappingNote';
import { BasinSummary } from './BasinSummary';
import { HorizonStrip } from './HorizonStrip';
import { Disclosure } from './Disclosure';
import { DriverRow } from './DriverRow';
import { ProvenanceLine } from './ProvenanceLine';
import { ReservoirsSection } from './ReservoirsSection';
import { SurfaceRow } from './SurfaceRow';
import { SurfaceValue } from './SurfaceValue';
import { Tier0Section } from './Tier0Section';
import { formatUtc, words } from './format';

type Surfaces = BasinVisualizationState['surfaces'];
type ModelProbability = NonNullable<Surfaces['hazard']['model_probability']>;

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

export function BasinPanel() {
  const selectedBasinId = useSceneStore((s) => s.selectedBasinId);
  const query = useBasinState(selectedBasinId);
  // The outlet's river state rides the same query the map's responding-rivers already make.
  const rivers = useVizRivers(selectedBasinId);

  if (!selectedBasinId) return null;
  if (query.isPending) return <section className="panel glass-surface glass-panel shape-panel" data-testid="basin-panel"><p className="muted">Loading basin state…</p></section>;
  if (query.isError) return <section className="panel glass-surface glass-panel shape-panel" data-testid="basin-panel"><p className="error">Basin state unavailable: {query.error.message}</p></section>;

  const item: BasinVisualizationState | undefined = query.data.items[0];
  const outlet = rivers.data?.items.find((r) => r.id === item?.outlet_forecast_point_id) ?? null;
  const refs = query.data.provenance_refs;
  if (!item) return <section className="panel glass-surface glass-panel shape-panel" data-testid="basin-panel"><p className="muted">No basin item in the document.</p></section>;

  const { susceptibility, forcing, hazard, agreement } = item.surfaces;
  const hazardProv = hazard.official_prov ?? hazard.prov;
  const drivers = item.headline_drivers ?? [];

  return (
    <section className="panel glass-surface glass-panel shape-panel" data-testid="basin-panel" aria-label="Basin panel">
      <header className="panel-header">
        {/* Internal ids and validity plumbing are inspector material, not headline chrome
            (mission §17): the id rides the title attribute; regulation and the document's
            valid time live in the Context fold below. */}
        <span className="eyebrow" title={item.id}>BASIN</span>
        <h2 data-testid="basin-panel-name">{item.name}</h2>
      </header>

      <BasinSummary item={item} refs={refs} />
      {outlet ? <HorizonStrip outlet={outlet} /> : null}

      <Disclosure id="why" label="Why?" hint={`${drivers.length} drivers`}>
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
      </Disclosure>

      <Disclosure id="forecasts" label="Forecasts" hint={`${(item.official_alerts ?? []).length} alerts`}>
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
      </Disclosure>

      <Disclosure id="context" label="Context">
        <p className="reason" data-testid="basin-context-meta">
          Regulation: {words(item.regulation_class)} · document valid {formatUtc(query.data.time.valid)} ({query.data.time.mode})
          {item.outlet_forecast_point_id ? <> · outlet <span className="mono">{item.outlet_forecast_point_id}</span></> : null}
        </p>
        <AntecedentSection entries={item.antecedent_precip ?? []} refs={refs} />
        <ReservoirsSection basinId={item.id} />
        <FloodMappingNote basinId={item.id} />
      </Disclosure>
    </section>
  );
}
