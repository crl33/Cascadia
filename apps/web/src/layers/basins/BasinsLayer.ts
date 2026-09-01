/**
 * BasinsLayer: terrain-following basin outlines as ground polylines in a CustomDataSource.
 * Data in: state-LOD features for every basin, the basin-LOD feature for the selected basin,
 * and the official hazard category per basin (for the edge tone). Diffs by (basinId, lod).
 * Presentation comes only from style.ts; fades are CallbackProperties (no React involved).
 */
import { CallbackProperty, Cartesian3, Color, ColorMaterialProperty, CustomDataSource, Entity, PolylineDashMaterialProperty, type Viewer } from 'cesium';
import type { FloodCategory, GeoFeature } from '../../contracts/schemas';
import { MOTION, type MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { outerRings } from '../geojson';
import { basinEdge, type EdgeStyle } from './style';

export interface BasinsLayerData {
  stateLod: Record<string, GeoFeature>;
  basinLod: Record<string, GeoFeature>;
  categories: Record<string, FloodCategory>;
  /** basins with at least one active NWS alert; rendered as a dashed edge (non-colour channel). */
  alerted: Record<string, boolean>;
}

interface OutlineRecord { basinId: string; lod: 'state' | 'basin'; entities: Entity[]; shownSince: number | null }

const TAG_PREFIX = 'basins|';
const hslToColor = (c: { h: number; s: number; l: number }, alpha: number) => Color.fromHsl(c.h / 360, c.s / 100, c.l / 100, alpha);

export class BasinsLayer implements SceneLayer<BasinsLayerData> {
  readonly id = 'basins' as const;
  readonly displayName = 'Basin boundaries (WBD HUC8, display geometry)';
  readonly truthClass = 'cartographic' as const;
  readonly bands: SceneLayer['bands'] = { orbital: 'full', state: 'full', basin: 'reduced', river: 'reduced', local: 'reduced' };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  private viewer: Viewer | null = null;
  private readonly source = new CustomDataSource('basins');
  private readonly outlines = new Map<string, OutlineRecord>();
  private categories: Record<string, FloodCategory> = {};
  private alerted: Record<string, boolean> = {};
  private band: Band = 'orbital';
  private selection: SelectionState = { basinId: null, forecastPointId: null, hovered: null };
  private visible = true;
  private motion: MotionPreference = 'full';
  private disposed = false;
  /** Explicit rendering: a fade is time-driven, so the layer pumps frames until it ends. */
  private fadeUntil = 0;
  private pumping = false;

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
    this.outlines.clear();
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

  setMotion(motion: MotionPreference): void {
    this.motion = motion;
  }

  setData(data: BasinsLayerData): void {
    if (this.disposed) return;
    this.categories = data.categories;
    this.alerted = data.alerted ?? {};
    const wanted = new Set<string>();
    const upsert = (lod: 'state' | 'basin', features: Record<string, GeoFeature>) => {
      for (const [basinId, feature] of Object.entries(features)) {
        const key = `${lod}:${basinId}`;
        wanted.add(key);
        if (this.outlines.has(key)) continue;
        const entities = outerRings(feature).map((ring, index) =>
          this.source.entities.add({
            id: `${TAG_PREFIX}${basinId}|${lod}|${index}`,
            polyline: { positions: Cartesian3.fromDegreesArray(ring.flatMap((p) => [p[0], p[1]])), clampToGround: true, width: 1 },
          }),
        );
        this.outlines.set(key, { basinId, lod, entities, shownSince: null });
      }
    };
    upsert('state', data.stateLod);
    upsert('basin', data.basinLod);
    for (const [key, record] of this.outlines) {
      if (wanted.has(key)) continue;
      record.entities.forEach((e) => this.source.entities.remove(e));
      this.outlines.delete(key);
    }
    const total = Object.keys(data.stateLod).length;
    this.status = total === 0 ? 'loading' : 'current';
    this.statusReason = total === 0 ? 'awaiting geometry' : null;
    this.restyle();
  }

  hitTest(rendererTag: string): LayerHit | null {
    if (!rendererTag.startsWith(TAG_PREFIX)) return null;
    const basinId = rendererTag.slice(TAG_PREFIX.length).split('|')[0] ?? null;
    return basinId ? { layerId: this.id, entityId: basinId, basinId } : null;
  }

  private restyle(): void {
    const now = performance.now();
    for (const record of this.outlines.values()) {
      const style = basinEdge({
        lod: record.lod,
        band: this.band,
        selected: record.basinId === this.selection.basinId,
        hovered: record.basinId === this.selection.hovered,
        category: this.categories[record.basinId] ?? 'unknown',
        alerted: this.alerted[record.basinId] ?? false,
        hasBasinLod: this.outlines.has(`basin:${record.basinId}`),
      });
      const wasShown = record.shownSince !== null;
      if (style.show && !wasShown) record.shownSince = now;
      if (!style.show) record.shownSince = null;
      const fadeStart = style.fadeIn && this.motion === 'full' && !wasShown ? now : null;
      if (fadeStart !== null) this.fadeUntil = Math.max(this.fadeUntil, fadeStart + MOTION.duration.state);
      record.entities.forEach((entity) => this.apply(entity, style, fadeStart));
    }
    this.viewer?.scene.requestRender();
    this.pumpFade();
  }

  /** One rAF loop per layer, alive only while a fade is in flight — each frame asks the
   * scene to render so the CallbackProperty is sampled (requestRenderMode renders nothing
   * on its own once the camera is still). */
  private pumpFade(): void {
    if (this.pumping || performance.now() >= this.fadeUntil) return;
    this.pumping = true;
    const tick = () => {
      if (this.disposed || !this.viewer) { this.pumping = false; return; }
      this.viewer.scene.requestRender();
      if (performance.now() < this.fadeUntil) window.requestAnimationFrame(tick);
      else this.pumping = false;
    };
    window.requestAnimationFrame(tick);
  }

  private apply(entity: Entity, style: EdgeStyle, fadeStart: number | null): void {
    const polyline = entity.polyline;
    if (!polyline) return;
    entity.show = style.show && this.visible;
    // PolylineGraphics.width must be > 0 even when hidden (Cesium DeveloperError otherwise).
    polyline.width = Math.max(style.widthPx, 0.5) as never;
    const base = hslToColor(style.color, style.alpha);
    // The dash carries "an official advisory names this basin"; colour stays the category.
    const material = (color: Color | CallbackProperty) =>
      style.dashed
        ? new PolylineDashMaterialProperty({ color: color as never, dashLength: 12 })
        : new ColorMaterialProperty(color as never);
    if (fadeStart === null) {
      polyline.material = material(base);
      return;
    }
    const duration = MOTION.duration.state;
    const faded = new Color();
    polyline.material = material(
      new CallbackProperty(() => {
        const t = Math.min(1, (performance.now() - fadeStart) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        return Color.fromAlpha(base, style.alpha * eased, faded);
      }, false),
    );
  }
}
