/**
 * Source-kind badge + freshness badge + age for one value. The source-kind badge opens the
 * per-value provenance popover (inspector v1); a missing ref renders the UNKNOWN badge whose
 * popover explains that the document is incomplete.
 */
import { Badge } from '../design-system/Badge';
import { FRESHNESS_BADGE } from '../design-system/badges';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import type { ProvenanceRef, TruthClass } from '../contracts/schemas';
import { formatFreshness } from './format';

interface ProvenanceLineProps {
  provKey: string;
  prov: ProvenanceRef | undefined;
  truth?: TruthClass | null;
  testId?: string;
}

export function ProvenanceLine({ provKey, prov, truth = null, testId }: ProvenanceLineProps) {
  return (
    <span className="prov-line">
      <ProvenancePopover provKey={provKey} prov={prov} truth={truth} testId={testId} />
      {prov ? (
        <>
          <Badge badge={FRESHNESS_BADGE[prov.freshness.state]} title={formatFreshness(prov.freshness)} />
          <span className="prov-age mono">{formatFreshness(prov.freshness)}</span>
        </>
      ) : null}
    </span>
  );
}
