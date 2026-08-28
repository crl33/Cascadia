import type { BasinVisualizationState, ProvenanceRef } from '../contracts/schemas';
import { Badge } from '../design-system/Badge';
import { CATEGORY_BADGE } from '../design-system/badges';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import { formatMultiplier, formatQuantity, words } from './format';

/**
 * The at-a-glance block (design direction 2026-08-28): state words and key figures instantly
 * legible; sample counts, reference windows and cadence prose one disclosure deeper. Doctrine
 * holds in compact form — every line keeps its provenance chip, the OFFICIAL hazard category
 * is always here (never behind a fold), an active alert is never hidden, and an UNKNOWN
 * susceptibility surfaces its reason right here (incomplete, never calm).
 */
export function BasinSummary({ item, refs }: { item: BasinVisualizationState; refs: Record<string, ProvenanceRef | undefined> }) {
  const { susceptibility, forcing, hazard } = item.surfaces;
  const level = item.hydrologic_state;
  const change24 = (item.state_change ?? []).find((c) => c.window_h === 24) ?? null;
  const alerts = item.official_alerts ?? [];
  const changeGlyph = change24?.direction === 'rising' ? '↗' : change24?.direction === 'falling' ? '↘' : '↔';
  return (
    <div className="basin-summary" data-testid="basin-summary">
      <p className="summary-line" data-testid="summary-susceptibility">
        <span className={`summary-state state-${susceptibility.state}`}>{words(susceptibility.state).toUpperCase()} SUSCEPTIBILITY</span>
        {susceptibility.value ? <span className="summary-key muted">{formatQuantity(susceptibility.value, 0)}</span> : null}
        <ProvenancePopover provKey={susceptibility.prov} prov={refs[susceptibility.prov]} truth={susceptibility.truth} />
      </p>
      {susceptibility.state === 'unknown' && susceptibility.reason ? (
        <p className="reason" data-testid="summary-susceptibility-reason">{susceptibility.reason}</p>
      ) : null}
      {level ? (
        <p className="summary-line" data-testid="summary-level">
          <span className="summary-tag">level</span>
          <span className="summary-key">{formatQuantity(level.observed, 0)}</span>
          {level.multiple ? (
            <span className="muted">{formatMultiplier(level.multiple.multiple)} seasonal p{level.multiple.reference_percentile} reference</span>
          ) : null}
          <ProvenancePopover provKey={level.prov} prov={refs[level.prov]} truth={level.truth} />
        </p>
      ) : null}
      {change24 ? (
        <p className="summary-line" data-testid="summary-change">
          <span className="summary-tag">change</span>
          <span className="summary-key">
            {changeGlyph} {words(change24.direction)}
            {change24.growth != null ? ` · ${formatMultiplier(change24.growth)} / 24 h` : ''}
          </span>
          <ProvenancePopover provKey={change24.prov} prov={refs[change24.prov]} truth={null} />
        </p>
      ) : null}
      <p className="summary-line" data-testid="summary-forcing">
        <span className="summary-tag">forcing</span>
        <span className={`summary-state state-${forcing.state}`}>{words(forcing.state).toUpperCase()}</span>
        {forcing.value ? <span className="summary-key muted">{formatQuantity(forcing.value, 1)} / {forcing.horizon_h ?? 72} h</span> : null}
        <ProvenancePopover provKey={forcing.prov} prov={refs[forcing.prov]} truth={forcing.truth} />
      </p>
      <p className="summary-line" data-testid="summary-hazard">
        <span className="summary-tag">hazard</span>
        <Badge badge={CATEGORY_BADGE[hazard.official_category]} testId="summary-hazard-category" />
        <span className="muted">official · {hazard.horizon_h} h</span>
        <ProvenancePopover provKey={hazard.official_prov ?? hazard.prov} prov={refs[hazard.official_prov ?? hazard.prov]} truth={hazard.truth} />
      </p>
      {alerts.length > 0 ? (
        <p className="summary-line" data-testid="summary-alerts">
          <span className="summary-tag">alerts</span>
          <span className="summary-key">{alerts.length} active — {alerts.map((a) => a.event).join(', ')}</span>
        </p>
      ) : null}
    </div>
  );
}

