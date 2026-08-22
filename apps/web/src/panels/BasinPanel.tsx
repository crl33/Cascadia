/**
 * BasinPanel: renders one BasinVisualizationState — name, regulation class, the four surfaces
 * (state + reason + source-kind badge + freshness), official alerts and drivers with honest empty
 * states. It computes nothing; UNKNOWN is shown as UNKNOWN with its reason.
 */
import { useState } from 'react';
import { useBasinState } from '../api/hooks';
import { useSceneStore } from '../state/store';
import { Badge } from '../design-system/Badge';
import { CATEGORY_BADGE } from '../design-system/badges';
import type { BasinVisualizationState, ProvenanceRef, TruthClass } from '../contracts/schemas';
import { LayerInspector } from './LayerInspector';
import { ProvenanceLine } from './ProvenanceLine';
import { formatUtc, words } from './format';

interface SurfaceRowProps {
  title: string;
  state: string;
  reason: string | null | undefined;
  provKey: string;
  refs: Record<string, ProvenanceRef>;
  onInspect: (key: string) => void;
  testId: string;
  extra?: React.ReactNode;
}

function SurfaceRow({ title, state, reason, provKey, refs, onInspect, testId, extra }: SurfaceRowProps) {
  return (
    <div className="row" data-testid={testId}>
      <div className="row-head">
        <span className="row-title">{title}</span>
        <span className={`state-word state-${state}`} data-testid={`${testId}-state`}>{words(state).toUpperCase()}</span>
      </div>
      {extra}
      {reason ? <p className="reason">{reason}</p> : null}
      <ProvenanceLine provKey={provKey} prov={refs[provKey]} onInspect={onInspect} testId={`${testId}-badge`} />
    </div>
  );
}

export function BasinPanel() {
  const selectedBasinId = useSceneStore((s) => s.selectedBasinId);
  const query = useBasinState(selectedBasinId);
  const [inspected, setInspected] = useState<{ key: string; truth: TruthClass | null } | null>(null);

  if (!selectedBasinId) return null;
  if (query.isPending) return <section className="panel" data-testid="basin-panel"><p className="muted">Loading basin state…</p></section>;
  if (query.isError) return <section className="panel" data-testid="basin-panel"><p className="error">Basin state unavailable: {query.error.message}</p></section>;

  const item: BasinVisualizationState | undefined = query.data.items[0];
  const refs = query.data.provenance_refs;
  if (!item) return <section className="panel" data-testid="basin-panel"><p className="muted">No basin item in the document.</p></section>;

  const { susceptibility, forcing, hazard, agreement } = item.surfaces;
  const hazardProv = hazard.official_prov ?? hazard.prov;
  const inspect = (truth: TruthClass | null) => (key: string) => setInspected({ key, truth });

  return (
    <section className="panel" data-testid="basin-panel" aria-label="Basin panel">
      <header className="panel-header">
        <span className="eyebrow">BASIN · {item.id}</span>
        <h2 data-testid="basin-panel-name">{item.name}</h2>
        <p className="muted">regulation: <span className="mono">{words(item.regulation_class)}</span> · valid {formatUtc(query.data.time.valid)} ({query.data.time.mode})</p>
      </header>

      <SurfaceRow title="Basin susceptibility" state={susceptibility.state} reason={susceptibility.reason} provKey={susceptibility.prov} refs={refs} onInspect={inspect(susceptibility.truth)} testId="surface-susceptibility" />
      <SurfaceRow title={`Meteorological forcing${forcing.horizon_h ? ` · ${forcing.horizon_h} h` : ''}`} state={forcing.state} reason={forcing.reason} provKey={forcing.prov} refs={refs} onInspect={inspect(forcing.truth)} testId="surface-forcing" />
      <SurfaceRow
        title={`Flood hazard · ${hazard.horizon_h} h`}
        state={hazard.official_category}
        reason={hazard.reason}
        provKey={hazardProv}
        refs={refs}
        onInspect={inspect(hazard.truth)}
        testId="surface-hazard"
        extra={
          <p className="value-line">
            official category <Badge badge={CATEGORY_BADGE[hazard.official_category]} testId="hazard-category" />
            {hazard.model_probability ? <span className="muted"> · model: {JSON.stringify(hazard.model_probability)}</span> : <span className="muted"> · no model probability</span>}
          </p>
        }
      />
      <div className="row" data-testid="surface-agreement">
        <div className="row-head">
          <span className="row-title">Model agreement</span>
          <span className={`state-word state-${agreement.state}`}>{agreement.state.toUpperCase()}</span>
        </div>
        {agreement.prov && agreement.prov.length > 0 ? (
          agreement.prov.map((key) => <ProvenanceLine key={key} provKey={key} prov={refs[key]} onInspect={inspect(null)} />)
        ) : (
          <p className="reason">Agreement not computed: no second model ingested in the spike (UNKNOWN, not "agree").</p>
        )}
      </div>

      <div className="row">
        <div className="row-head"><span className="row-title">Official alerts</span></div>
        {item.official_alerts && item.official_alerts.length > 0 ? (
          <ul>{item.official_alerts.map((a) => <li key={a.id} className="mono">{a.issuer}: {a.event} {a.severity ?? ''} (onset {formatUtc(a.onset)})</li>)}</ul>
        ) : (
          <p className="reason" data-testid="alerts-empty">No official alerts in this document. Watches and warnings are issued by the National Weather Service; none were ingested for this basin.</p>
        )}
      </div>
      <div className="row">
        <div className="row-head"><span className="row-title">Headline drivers</span></div>
        {item.headline_drivers && item.headline_drivers.length > 0 ? (
          <ul>{item.headline_drivers.map((d) => <li key={d.feature} className="mono">#{d.rank} {d.feature} {d.value ?? '—'} {d.unit ?? ''} ({words(d.direction)})</li>)}</ul>
        ) : (
          <p className="reason" data-testid="drivers-empty">No headline drivers: the explanation engine is not part of the spike.</p>
        )}
      </div>
      {item.outlet_forecast_point_id ? <p className="muted">outlet forecast point: <span className="mono">{item.outlet_forecast_point_id}</span></p> : null}
      {inspected ? <LayerInspector provKey={inspected.key} prov={refs[inspected.key]} truth={inspected.truth} onClose={() => setInspected(null)} /> : null}
    </section>
  );
}
