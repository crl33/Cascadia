import type { BasinVisualizationState, ProvenanceRef } from '../contracts/schemas';
import { Badge } from '../design-system/Badge';
import { CATEGORY_BADGE } from '../design-system/badges';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import { formatMultiplier, formatQuantity } from './format';
import { currentSentence, forcingSentence, hazardSentence, susceptibilityHeadline } from './summary-language';

/**
 * The 1-second / 5-second read (mission §16): four short human statements, each still
 * carrying its provenance chip (doctrine — a value never sheds its source affordance):
 *
 *   headline   Cascadia's assessment as a plain phrase        [Cascadia assessment]
 *   CURRENT    river direction + seasonal standing            [Derived]
 *   NEXT       the forcing sentence over its window           [Cascadia assessment]
 *   OFFICIAL   the NWS outlook sentence + category chip       [Official forecast]
 *
 * The forensic figures (percentiles, multiples, cfs) live in each line's hover title and
 * one fold deeper in WHY — moved, never removed. The OFFICIAL category and active alerts
 * are never behind a fold; an UNKNOWN surfaces its reason right here.
 */
export function BasinSummary({ item, refs }: { item: BasinVisualizationState; refs: Record<string, ProvenanceRef | undefined> }) {
  const { susceptibility, forcing, hazard } = item.surfaces;
  const level = item.hydrologic_state;
  const change24 = (item.state_change ?? []).find((c) => c.window_h === 24) ?? null;
  const alerts = item.official_alerts ?? [];
  const current = currentSentence(level ?? null, change24);
  const currentDetail = [
    level ? `observed ${formatQuantity(level.observed, 0)}` : null,
    level?.multiple ? `${formatMultiplier(level.multiple.multiple)} of the seasonal p${level.multiple.reference_percentile} reference` : null,
    change24?.growth != null ? `${formatMultiplier(change24.growth)} over 24 h` : null,
  ].filter(Boolean).join(' · ');

  return (
    <div className="basin-summary" data-testid="basin-summary">
      <p className="summary-line" data-testid="summary-susceptibility">
        <span className={`summary-state state-${susceptibility.state}`}>{susceptibilityHeadline(susceptibility.state)}</span>
        <ProvenancePopover provKey={susceptibility.prov} prov={refs[susceptibility.prov]} truth={susceptibility.truth} />
      </p>
      {susceptibility.state === 'unknown' && susceptibility.reason ? (
        <p className="reason" data-testid="summary-susceptibility-reason">{susceptibility.reason}</p>
      ) : null}
      {current ? (
        <p className="summary-line" data-testid="summary-level">
          <span className="summary-tag">current</span>
          <span className="summary-sentence" title={currentDetail}>{current}</span>
          {level ? <ProvenancePopover provKey={level.prov} prov={refs[level.prov]} truth={level.truth} /> : null}
        </p>
      ) : null}
      <p className="summary-line" data-testid="summary-forcing">
        <span className="summary-tag">next {forcing.horizon_h ?? 72} h</span>
        <span className="summary-sentence">{forcingSentence(forcing)}</span>
        <ProvenancePopover provKey={forcing.prov} prov={refs[forcing.prov]} truth={forcing.truth} />
      </p>
      <p className="summary-line" data-testid="summary-hazard">
        <span className="summary-tag">official</span>
        <span className="summary-sentence">{hazardSentence(hazard)}</span>
        <Badge badge={CATEGORY_BADGE[hazard.official_category]} testId="summary-hazard-category" />
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
