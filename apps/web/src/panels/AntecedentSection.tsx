import type { BasinVisualizationState, ProvenanceRef } from '../contracts/schemas';
import { ProvenanceLine } from './ProvenanceLine';
import { formatQuantity, formatUtc } from './format';

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

