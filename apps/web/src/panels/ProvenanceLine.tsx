/** Source-kind badge + freshness badge + age for one value; clicking the badge opens the inspector. */
import { Badge } from '../design-system/Badge';
import { FRESHNESS_BADGE, badgeForSourceKind } from '../design-system/badges';
import type { ProvenanceRef } from '../contracts/schemas';
import { formatFreshness } from './format';

interface ProvenanceLineProps {
  provKey: string;
  prov: ProvenanceRef | undefined;
  onInspect: (provKey: string) => void;
  testId?: string;
}

export function ProvenanceLine({ provKey, prov, onInspect, testId }: ProvenanceLineProps) {
  if (!prov) {
    return <Badge badge={badgeForSourceKind('UNKNOWN')} title={`provenance ref "${provKey}" missing from the document`} testId={testId} />;
  }
  return (
    <span className="prov-line">
      <Badge badge={badgeForSourceKind(prov.source_kind)} title={`${prov.label} — click for provenance`} testId={testId} onClick={() => onInspect(provKey)} />
      <Badge badge={FRESHNESS_BADGE[prov.freshness.state]} title={formatFreshness(prov.freshness)} />
      <span className="prov-age mono">{formatFreshness(prov.freshness)}</span>
    </span>
  );
}
