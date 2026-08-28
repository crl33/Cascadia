/**
 * FloodMappingNote: what the STATIC flood mapping can and cannot say for this basin — the
 * place the Skagit gap is stated instead of papered over. Text derives from the flood
 * geography document\'s own availability field; the caveat language follows the verified
 * FEMA terms (docs/research/flood-geography-sources-2026-08-28.md §5.3).
 */
import { useFloodGeography } from '../api/hooks';

const CAVEATS: Record<string, string> = {
  covered:
    'FEMA-mapped zones shown are regulatory boundaries from the effective NFHL (study-vintage). ' +
    'They reflect the underlying flood study, not current conditions or any forecast; areas outside a zone also flood.',
  partial_edges_only:
    'FEMA has NO digital flood-zone data for this basin\'s valley floor; zones visible near the edges ' +
    'belong to neighboring coastal studies. Absence of shading here is absence of DATA, not absence of hazard.',
  no_digital_data:
    'FEMA has no digital flood-zone data for this basin. Absence of shading is absence of DATA, not absence of hazard.',
};

export function FloodMappingNote({ basinId }: { basinId: string }) {
  const flood = useFloodGeography();
  if (flood.isError) {
    return (
      <p className="flood-mapping-note" data-testid="flood-mapping-note">
        Static flood mapping: not available in this deployment.
      </p>
    );
  }
  if (!flood.data) return null;
  const entry = flood.data.basins[basinId];
  const availability = entry?.availability ?? 'no_digital_data';
  const levees = entry?.levees.length ?? 0;
  return (
    <p className="flood-mapping-note" data-testid="flood-mapping-note" data-availability={availability}>
      {CAVEATS[availability]}
      {levees > 0 ? ` ${levees} NLD levee system${levees === 1 ? '' : 's'} mapped (locations, never a statement of protection).` : ''}
    </p>
  );
}
