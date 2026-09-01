/**
 * Weather layer controls (mission §22): clicking "Rain" SHOWS/HIDES rain. That is the whole
 * primary interaction — the audit caught the old chip dumping a raw provenance record over
 * half the screen when the user just wanted the layer off.
 *
 * Layout per entry: [☑ toggle] [swatch] [human name] [quiet source · local time] [badge ⓘ].
 * The badge is still the provenance inspector trigger (doctrine: every rendered scientific
 * value carries its source affordance) — but it is the SECONDARY affordance, it opens a
 * compact card UPWARD from this bottom-anchored strip, and it dismisses like everything
 * else. The formal truth class lives inside the inspector, not in the strip.
 *
 * A field the API refuses has no entry: the legend never advertises what the map is not
 * showing. A toggled-off layer keeps its entry (unchecked) — that state is user intent.
 */
import { useVizField } from '../api/hooks';
import type { FieldRasterState } from '../contracts/schemas';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import { useSceneStore, type LayerId } from '../state/store';

interface LegendEntry {
  layer: LayerId;
  label: string;
  source: string;
  doc: FieldRasterState;
}

const localLabel = (iso: string): string =>
  new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });

export function FieldLegend() {
  const precip = useVizField('precip_observed');
  const snow = useVizField('snow_cover');
  const activeLayers = useSceneStore((s) => s.activeLayers);
  const setLayerActive = useSceneStore((s) => s.setLayerActive);

  const entries: LegendEntry[] = [];
  if (precip.data) entries.push({ layer: 'precip_observed', label: 'Rain', source: 'radar', doc: precip.data });
  if (snow.data) entries.push({ layer: 'snow_cover', label: 'Snow', source: 'model', doc: snow.data });
  const activeSet = new Set(activeLayers);
  if (entries.length === 0) return null;

  return (
    <div className="field-legend glass-surface glass-compact shape-control" data-occlusion="field-legend" data-testid="field-legend" aria-label="Weather layers">
      <span className="field-legend-heading">Weather</span>
      {entries.map(({ layer, label, source, doc }) => {
        const active = activeSet.has(layer);
        return (
          <span key={layer} className="field-legend-entry" data-testid={`field-legend-${layer}`}>
            <label className="field-legend-toggle">
              <input
                type="checkbox"
                checked={active}
                onChange={(e) => setLayerActive(layer, e.currentTarget.checked)}
                aria-label={`Show ${label.toLowerCase()}`}
                data-testid={`field-toggle-${layer}`}
              />
              <span className={`field-swatch field-swatch-${layer}`} aria-hidden="true" />
              <span className="field-legend-label">{label}</span>
            </label>
            <span className="field-legend-time" title={doc.valid_time}>
              {source} · {localLabel(doc.valid_time)}
            </span>
            <ProvenancePopover provKey={doc.prov} prov={doc.provenance_refs[doc.prov]} truth={doc.truth} />
          </span>
        );
      })}
    </div>
  );
}
