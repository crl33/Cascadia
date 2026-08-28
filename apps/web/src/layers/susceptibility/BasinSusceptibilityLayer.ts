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
  Cartesian2,
  Cartesian3,
  Color,
  ColorMaterialProperty,
  CustomDataSource,
  Entity,
  ImageMaterialProperty,
  PolygonHierarchy,
  type Viewer,
} from 'cesium';
import type { ConfidenceLabel, GeoFeature, SurfaceLevel } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { outerRings } from '../geojson';
import { HATCH_SPACING_DEG, susceptibilityFill, type SusceptibilityFill } from './style';

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

interface FillRecord {
  basinId: string;
  entities: Entity[];
  /** lon/lat extent of the basin's rings, so hatch density normalises across basin sizes:
   *  polygon texture space is per-polygon, and a fixed repeat drew broad bands on the Skagit
   *  and fine ones on the Cedar. */
  extentDeg: number;
}

const TAG_PREFIX = 'basin_susceptibility|';
const HATCH_TILE_PX = 32;
const HATCH_LINE_PX = 1.5;
const hslToColor = (c: { h: number; s: number; l: number }, alpha: number) =>
  Color.fromHsl(c.h / 360, c.s / 100, c.l / 100, alpha);

const cssRgba = (c: { h: number; s: number; l: number }, alpha: number) =>
  `hsla(${c.h}, ${c.s}%, ${c.l}%, ${alpha})`;

/**
 * One seamless hatch tile: the restrained wash as the ground, one fine 45° line as the
 * carrier (drawn thrice so the diagonal wraps cleanly). Cached — six basins share at most a
 * handful of (tone, wash, hatch) combinations per restyle.
 */
const tileCache = new Map<string, HTMLCanvasElement>();
function hatchTile(color: { h: number; s: number; l: number }, washAlpha: number, hatchAlpha: number): HTMLCanvasElement | null {
  const key = `${color.h}|${color.s}|${color.l}|${washAlpha.toFixed(3)}|${hatchAlpha.toFixed(3)}`;
  const cached = tileCache.get(key);
  if (cached) return cached;
  const canvas = document.createElement('canvas');
  canvas.width = HATCH_TILE_PX;
  canvas.height = HATCH_TILE_PX;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  ctx.fillStyle = cssRgba(color, washAlpha);
  ctx.fillRect(0, 0, HATCH_TILE_PX, HATCH_TILE_PX);
  ctx.strokeStyle = cssRgba(color, hatchAlpha);
  ctx.lineWidth = HATCH_LINE_PX;
  ctx.lineCap = 'butt';
  for (const offset of [-HATCH_TILE_PX, 0, HATCH_TILE_PX]) {
    ctx.beginPath();
    ctx.moveTo(offset - HATCH_LINE_PX, HATCH_TILE_PX + HATCH_LINE_PX);
    ctx.lineTo(offset + HATCH_TILE_PX + HATCH_LINE_PX, -HATCH_LINE_PX);
    ctx.stroke();
  }
  tileCache.set(key, canvas);
  return canvas;
}

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
      const rings = outerRings(feature);
      const entities = rings.map((ring, index) =>
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
      let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
      for (const ring of rings) {
        for (const [lon, lat] of ring) {
          if (lon < minLon) minLon = lon;
          if (lon > maxLon) maxLon = lon;
          if (lat < minLat) minLat = lat;
          if (lat > maxLat) maxLat = lat;
        }
      }
      const extentDeg = Math.max(maxLon - minLon, maxLat - minLat, HATCH_SPACING_DEG);
      this.fills.set(basinId, { basinId, entities, extentDeg });
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
      record.entities.forEach((entity) => this.apply(entity, style, record.extentDeg));
    }
    this.viewer?.scene.requestRender();
  }

  private apply(entity: Entity, style: SusceptibilityFill, extentDeg: number): void {
    const polygon = entity.polygon;
    if (!polygon) return;
    // `outlineOnly` is the UNKNOWN treatment: the basin is drawn as incomplete rather than filled,
    // so a refused value can never be mistaken for a calm one.
    entity.show = style.show && this.visible && !style.outlineOnly;
    if (!entity.show) return;
    const base = hslToColor(style.color, style.alpha);
    if (!style.striped) {
      polygon.material = new ColorMaterialProperty(base);
      return;
    }
    // The hatch is the mandatory non-colour carrier (§7.2): it survives a greyscale screenshot,
    // which is how an experimental wash stays distinguishable from an official category fill.
    // It is a FINE texture over a restrained wash — the old repeat-36 vertical bands read as a
    // debugging mask and were the loudest thing on screen (design direction 2026-08-28). The
    // repeat normalises by basin extent, so the Skagit and the Cedar carry the same line spacing.
    const tile = hatchTile(style.color, style.alpha, style.hatchAlpha);
    if (tile === null) {
      polygon.material = new ColorMaterialProperty(base); // no canvas (headless): wash only
      return;
    }
    const repeat = Math.max(1, Math.round(extentDeg / HATCH_SPACING_DEG));
    polygon.material = new ImageMaterialProperty({
      image: tile,
      repeat: new Cartesian2(repeat, repeat),
      transparent: true,
    });
  }
}
