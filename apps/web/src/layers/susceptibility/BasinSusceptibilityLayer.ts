/**
 * BasinSusceptibilityLayer: the first Cascade-DERIVED thing the globe itself says.
 *
 * Until now the map carried only official categories and cartographic outlines; the platform's own
 * susceptibility index lived in a panel. This renders it as a restrained wash over the basin
 * polygon, in the experimental register.
 *
 * **Why this is a separate layer from `basins`.** That layer is `cartographic` and draws
 * boundaries. Tinting its outlines by a derived value would put two truth classes in one element,
 * which VISUAL_TRUTH_DOCTRINE forbids outright ("Never intentionally blur classes"). A separate
 * layer also means the user can turn the index off and still see the Earth, and that it drops
 * first under quality tiers without taking the geography with it.
 *
 * All presentation decisions — tone, alpha, stripe, the UNKNOWN treatment — live in `style.ts` and
 * are tested there against the doctrine. This file only diffs entities and applies the result.
 */
import {
  Cartesian3,
  Color,
  ColorMaterialProperty,
  CustomDataSource,
  Entity,
  PolygonHierarchy,
  StripeMaterialProperty,
  StripeOrientation,
  type Viewer,
} from 'cesium';
import type { ConfidenceLabel, GeoFeature, SurfaceLevel } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { outerRings } from '../geojson';
import { susceptibilityFill, type SusceptibilityFill } from './style';

export interface BasinSusceptibility {
  state: SurfaceLevel;
  confidence: ConfidenceLabel;
  experimental: boolean;
  reason: string | null;
}

export interface BasinSusceptibilityLayerData {
  /** The same state-LOD geometry the basins layer draws, so the two never disagree on shape. */
  geometry: Record<string, GeoFeature>;
  surfaces: Record<string, BasinSusceptibility>;
}

interface FillRecord { basinId: string; entities: Entity[] }

const TAG_PREFIX = 'basin_susceptibility|';
const hslToColor = (c: { h: number; s: number; l: number }, alpha: number) =>
  Color.fromHsl(c.h / 360, c.s / 100, c.l / 100, alpha);

/** A basin with no surface at all is UNKNOWN, not absent — the doctrine's incomplete state. */
const MISSING: BasinSusceptibility = {
  state: 'unknown',
  confidence: 'unknown',
  experimental: true,
  reason: 'no susceptibility surface for this basin',
};

export class BasinSusceptibilityLayer implements SceneLayer<BasinSusceptibilityLayerData> {
  readonly id = 'basin_susceptibility' as const;
  // 'Cascade-derived susceptibility', never 'the Cascade index': `cascade_index` is the
  // contract's reserved name for CALIBRATED Phase 7 intelligence (it is null everywhere
  // today), and borrowing it for an uncalibrated surface would promise a calibration
  // nobody has done.
  readonly displayName = 'Basin susceptibility (Cascade-derived, EXPERIMENTAL)';
  //` cascade_derived` is the truth class the contract already assigns this surface; the layer
  // repeats it rather than inventing one, so the inspector and the map agree.
  readonly truthClass = 'cascade_derived' as const;
  // A wash for the overview bands, gone by the time reaches and gauges own the frame.
  readonly bands: SceneLayer['bands'] = {
    orbital: 'full', state: 'full', basin: 'reduced', river: 'hidden', local: 'hidden',
  };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  private viewer: Viewer | null = null;
  private readonly source = new CustomDataSource('basin_susceptibility');
  private readonly fills = new Map<string, FillRecord>();
  private surfaces: Record<string, BasinSusceptibility> = {};
  private band: Band = 'orbital';
  private selection: SelectionState = { basinId: null, forecastPointId: null, hovered: null };
  private visible = true;
  private disposed = false;

  mount(scene: SceneHandle): void {
    this.viewer = viewerOf(scene);
    if (!this.viewer.dataSources.contains(this.source)) void this.viewer.dataSources.add(this.source);
  }

  unmount(): void {
    if (this.viewer?.dataSources.contains(this.source)) this.viewer.dataSources.remove(this.source, false);
    this.viewer = null;
  }

  dispose(): void {
    this.unmount();
    this.source.entities.removeAll();
    this.fills.clear();
    this.disposed = true;
  }

  setVisible(visible: boolean): void {
    this.visible = visible;
    this.source.show = visible;
  }

  setBand(band: Band): void {
    this.band = band;
    this.restyle();
  }

  setSelection(selection: SelectionState): void {
    this.selection = selection;
    this.restyle();
  }

  setMotion(_motion: MotionPreference): void {
    // Nothing to do: this layer has no animation. A wash that pulsed would be a cinematic effect
    // attached to a scientific value, which is exactly what the doctrine separates.
  }

  setData(data: BasinSusceptibilityLayerData): void {
    if (this.disposed) return;
    this.surfaces = data.surfaces;
    const wanted = new Set<string>();
    for (const [basinId, feature] of Object.entries(data.geometry)) {
      wanted.add(basinId);
      if (this.fills.has(basinId)) continue;
      const entities = outerRings(feature).map((ring, index) =>
        this.source.entities.add({
          id: `${TAG_PREFIX}${basinId}|${index}`,
          polygon: {
            hierarchy: new PolygonHierarchy(Cartesian3.fromDegreesArray(ring.flatMap((p) => [p[0], p[1]]))),
            // Draped on the terrain rather than extruded: the index is information ABOUT the
            // basin, not a physical quantity with a height.
            classificationType: undefined,
          },
        }),
      );
      this.fills.set(basinId, { basinId, entities });
    }
    for (const [basinId, record] of this.fills) {
      if (wanted.has(basinId)) continue;
      record.entities.forEach((e) => this.source.entities.remove(e));
      this.fills.delete(basinId);
    }
    const total = Object.keys(data.geometry).length;
    const known = Object.values(data.surfaces).filter((s) => s.state !== 'unknown').length;
    this.status = total === 0 ? 'loading' : known === 0 ? 'unknown' : known < total ? 'partial' : 'current';
    this.statusReason =
      total === 0 ? 'awaiting geometry'
      : known === 0 ? 'no basin has a susceptibility value'
      : known < total ? `${total - known} of ${total} basins have no value`
      : null;
    this.restyle();
  }

  hitTest(rendererTag: string): LayerHit | null {
    if (!rendererTag.startsWith(TAG_PREFIX)) return null;
    const basinId = rendererTag.slice(TAG_PREFIX.length).split('|')[0] ?? null;
    return basinId ? { layerId: this.id, entityId: basinId, basinId } : null;
  }

  private restyle(): void {
    for (const record of this.fills.values()) {
      const surface = this.surfaces[record.basinId] ?? MISSING;
      const style = susceptibilityFill({
        state: surface.state,
        experimental: surface.experimental,
        confidence: surface.confidence,
        band: this.band,
        selected: record.basinId === this.selection.basinId,
        reason: surface.reason,
      });
      record.entities.forEach((entity) => this.apply(entity, style));
    }
    this.viewer?.scene.requestRender();
  }

  private apply(entity: Entity, style: SusceptibilityFill): void {
    const polygon = entity.polygon;
    if (!polygon) return;
    // `outlineOnly` is the UNKNOWN treatment: the basin is drawn as incomplete rather than filled,
    // so a refused value can never be mistaken for a calm one.
    entity.show = style.show && this.visible && !style.outlineOnly;
    if (!entity.show) return;
    const base = hslToColor(style.color, style.alpha);
    polygon.material = style.striped
      // The stripe is the mandatory non-colour carrier (§7.2): it survives a greyscale screenshot,
      // which is how an experimental wash stays distinguishable from an official category fill.
      ? new StripeMaterialProperty({
          evenColor: base,
          oddColor: Color.TRANSPARENT,
          repeat: 36,
          orientation: StripeOrientation.VERTICAL,
        })
      : new ColorMaterialProperty(base);
  }
}
