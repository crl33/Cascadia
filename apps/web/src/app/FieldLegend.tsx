/**
 * FieldLegend: the map's weather washes named, timed and provenance-chipped.
 *
 * Doctrine, not chrome: the washes are rendered scientific values, and "every rendered
 * scientific value shows its source_kind badge and freshness" (react-quality §4). The basin
 * panel cannot carry this — a field is scene-scoped, selected-basin or none. One compact
 * strip, one entry per field the scene currently draws, each with the same ProvenancePopover
 * every panel value gets. A field the API refuses (404, "nothing current to draw") simply has
 * no entry: the legend never advertises what the map is not showing.
 */
import { useVizField } from '../api/hooks';
import type { FieldRasterState } from '../contracts/schemas';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import { formatUtc } from '../panels/format';

interface LegendEntry {
  layer: string;
  label: string;
  doc: FieldRasterState;
}

export function FieldLegend() {
  const precip = useVizField('precip_observed');
  const snow = useVizField('snow_cover');
  const entries: LegendEntry[] = [];
  if (precip.data) entries.push({ layer: 'precip_observed', label: 'RAIN', doc: precip.data });
  if (snow.data) entries.push({ layer: 'snow_cover', label: 'SNOW', doc: snow.data });
  if (entries.length === 0) return null;
  return (
    <div className="field-legend" data-testid="field-legend" aria-label="Weather field layers">
      {entries.map(({ layer, label, doc }) => (
        <span key={layer} className="field-legend-entry" data-testid={`field-legend-${layer}`}>
          <span className={`field-swatch field-swatch-${layer}`} aria-hidden="true" />
          <span className="field-legend-label">{label}</span>
          <span className="field-legend-time">{formatUtc(doc.valid_time)}</span>
          <ProvenancePopover provKey={doc.prov} prov={doc.provenance_refs[doc.prov]} truth={doc.truth} />
        </span>
      ))}
    </div>
  );
}
