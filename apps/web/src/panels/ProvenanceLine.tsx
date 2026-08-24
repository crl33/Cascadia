/**
 * Source-kind badge + freshness badge + age for one value. The source-kind badge opens the
 * per-value provenance popover (inspector v1); a missing ref renders the UNKNOWN badge whose
 * popover explains that the document is incomplete.
 */
import { Badge } from '../design-system/Badge';
import { ARCHIVED_BADGE, FRESHNESS_BADGE } from '../design-system/badges';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import { formatArchiveAge, provIsArchived } from '../design-system/provenance-record';
import type { ProvenanceRef, TruthClass } from '../contracts/schemas';
import { formatFreshness } from './format';

interface ProvenanceLineProps {
  provKey: string;
  prov: ProvenanceRef | undefined;
  truth?: TruthClass | null;
  testId?: string;
}

export function ProvenanceLine({ provKey, prov, truth = null, testId }: ProvenanceLineProps) {
  // An archived value takes the ARCHIVED badge and an age said as distance from today. STALE
  // would be a category error here (it means ingestion fell behind) and, worse, beside an event
  // cursor it reads as the value's age at that moment. Decided per value, never per app mode.
  const archived = prov !== undefined && provIsArchived(prov);
  return (
    <span className="prov-line">
      <ProvenancePopover provKey={provKey} prov={prov} truth={truth} testId={testId} />
      {prov ? (
        archived ? (
          <>
            <Badge
              badge={ARCHIVED_BADGE}
              title={`Archived record: ${formatArchiveAge(prov.freshness)}. Ages are measured from today's clock, not from the event time being replayed.`}
            />
            <span className="prov-age mono">{formatArchiveAge(prov.freshness)}</span>
          </>
        ) : (
          <>
            <Badge badge={FRESHNESS_BADGE[prov.freshness.state]} title={formatFreshness(prov.freshness)} />
            <span className="prov-age mono">{formatFreshness(prov.freshness)}</span>
          </>
        )
      ) : null}
    </span>
  );
}
