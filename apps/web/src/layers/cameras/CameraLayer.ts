/**
 * CameraLayer: geospatial markers for the curated flood-observation cameras. The markers live
 * HERE (Cesium billboards, picked through the standard hitTest pipeline); the preview WINDOWS
 * live in the DOM (app/CameraPreviewHost) — Cesium never holds an <img>, React never holds a
 * billboard, and the bridge between them is the store's `pinnedCameraId` plus a projected
 * screen position the host reads imperatively.
 *
 * Markers are a generated glyph (a small camera badge drawn once on canvas per size/pinned
 * combination) rather than an icon asset: no bundle bytes, crisp at device pixel ratio, and
 * the pinned state is a different glyph, not a color-only change.
 */
import {
  BillboardCollection,
  Cartesian3,
  HeightReference,
  VerticalOrigin,
  type Viewer,
} from 'cesium';
import type { CameraRecord } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { cameraMarker, type CameraTier } from './style';

export interface CameraSetData {
  cameras: CameraRecord[];
  pinnedCameraId: string | null;
  /** basin id -> official attention (attention.ts); presentation only, official register. */
  attention: Record<string, { kind: string; detail: string }>;
}

const TAG_PREFIX = 'cameras|';
const glyphCache = new Map<string, HTMLCanvasElement>();

/** The camera mark, redrawn for satellite ground (2026-08-29): a dark backing disc with a
 * bright halo ring and a white camera silhouette — unmistakable over snow, forest, ocean or
 * bright urban imagery alike. Pinned inverts (white disc, dark glyph); official attention
 * adds an outer ring. Drawn once per (size, state) at 2x for HiDPI. */
function cameraGlyph(sizePx: number, pinned: boolean, ring: boolean): HTMLCanvasElement {
  const key = `${sizePx}|${pinned}|${ring}`;
  const cached = glyphCache.get(key);
  if (cached) return cached;
  const scale = 2;
  const s = sizePx * scale;
  const canvas = document.createElement('canvas');
  canvas.width = s;
  canvas.height = s;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    const cx = s / 2;
    const cy = s / 2;
    const disc = s * 0.42;
    // halo ring: the legibility guarantee over any ground
    ctx.beginPath();
    ctx.arc(cx, cy, disc, 0, Math.PI * 2);
    ctx.fillStyle = pinned ? 'rgba(255,255,255,0.96)' : 'rgba(8,14,22,0.88)';
    ctx.fill();
    ctx.lineWidth = s * 0.055;
    ctx.strokeStyle = pinned ? 'rgba(8,14,22,0.9)' : 'rgba(255,255,255,0.92)';
    ctx.stroke();
    // camera silhouette: body + lens + viewfinder nub
    const ink = pinned ? 'rgba(8,14,22,0.92)' : 'rgba(255,255,255,0.95)';
    ctx.fillStyle = ink;
    const bw = s * 0.42;
    const bh = s * 0.28;
    ctx.beginPath();
    ctx.roundRect(cx - bw / 2, cy - bh / 2 + s * 0.02, bw, bh, s * 0.05);
    ctx.fill();
    ctx.fillRect(cx - s * 0.08, cy - bh / 2 - s * 0.035, s * 0.16, s * 0.06);
    ctx.beginPath();
    ctx.arc(cx, cy + s * 0.02, s * 0.075, 0, Math.PI * 2);
    ctx.fillStyle = pinned ? 'rgba(255,255,255,0.95)' : 'rgba(8,14,22,0.9)';
    ctx.fill();
    if (ring) {
      // official attention: an additional outer ring, never a colour change
      ctx.strokeStyle = pinned ? 'rgba(8,14,22,0.85)' : 'rgba(255,255,255,0.95)';
      ctx.lineWidth = s * 0.035;
      ctx.beginPath();
      ctx.arc(cx, cy, s * 0.48, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  glyphCache.set(key, canvas);
  return canvas;
}

export class CameraLayer implements SceneLayer<CameraSetData> {
  readonly id = 'cameras' as const;
  readonly displayName = 'Flood-observation cameras';
  readonly truthClass = 'cartographic' as const;
  readonly bands: SceneLayer['bands'] = {
    orbital: 'hidden', state: 'hidden', basin: 'reduced', river: 'full', local: 'full',
  };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  private viewer: Viewer | null = null;
  private collection: BillboardCollection | null = null;
  private data: CameraSetData | null = null;
  private band: Band = 'orbital';
  private visible = true;
  private disposed = false;

  mount(scene: SceneHandle): void {
    this.viewer = viewerOf(scene);
    this.collection = new BillboardCollection({ scene: this.viewer.scene });
    this.viewer.scene.primitives.add(this.collection);
    this.rebuild();
  }

  unmount(): void {
    if (this.viewer && this.collection) this.viewer.scene.primitives.remove(this.collection);
    this.collection = null;
    this.viewer = null;
  }

  dispose(): void {
    this.unmount();
    this.disposed = true;
  }

  setVisible(visible: boolean): void {
    this.visible = visible;
    if (this.collection) this.collection.show = visible;
    this.viewer?.scene.requestRender();
  }

  setBand(band: Band): void {
    if (band === this.band) return;
    this.band = band;
    this.rebuild();
  }

  setSelection(_selection: SelectionState): void {
    // pinning arrives through setData (the bridge pushes pinnedCameraId with the catalogue)
  }

  setMotion(_motion: MotionPreference): void {}

  setData(data: CameraSetData): void {
    if (this.disposed) return;
    this.data = data;
    this.status = data.cameras.length === 0 ? 'unknown' : 'current';
    this.statusReason = data.cameras.length === 0 ? 'no cameras in the curated set' : null;
    this.rebuild();
  }

  hitTest(rendererTag: string): LayerHit | null {
    if (!rendererTag.startsWith(TAG_PREFIX)) return null;
    const camId = rendererTag.slice(TAG_PREFIX.length);
    const record = this.data?.cameras.find((c) => c.id === camId);
    return { layerId: this.id, entityId: camId, basinId: record?.basin_id ?? null };
  }

  private rebuild(): void {
    if (!this.collection || !this.data) return;
    this.collection.removeAll();
    let shown = 0;
    const hiddenByBand: Record<string, number> = { A: 0, B: 0, C: 0 };
    for (const cam of this.data.cameras) {
      const pinned = cam.id === this.data.pinnedCameraId;
      const attention = cam.basin_id !== null && cam.basin_id in this.data.attention;
      const style = cameraMarker({ tier: cam.tier as CameraTier, band: this.band, pinned, attention });
      if (!style.show) {
        hiddenByBand[cam.tier] += 1;
        continue;
      }
      shown += 1;
      const billboard = this.collection.add({
        position: Cartesian3.fromDegrees(cam.lon, cam.lat),
        image: cameraGlyph(style.sizePx, pinned, style.ring),
        width: style.sizePx,
        height: style.sizePx,
        verticalOrigin: VerticalOrigin.BOTTOM,
        heightReference: HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      });
      (billboard as { id?: unknown }).id = `${TAG_PREFIX}${cam.id}`;
      billboard.color = billboard.color.withAlpha(style.alpha);
    }
    this.collection.show = this.visible;
    // The visibility diagnostic (mission §6): the layer SAYS why cameras are absent instead
    // of leaving it to guesswork — surfaced through statusReason (inspector/dev tooling).
    this.statusReason = shown === this.data.cameras.length
      ? null
      : `${shown}/${this.data.cameras.length} shown at ${this.band} band; hidden by band gate — A:${hiddenByBand.A} B:${hiddenByBand.B} C:${hiddenByBand.C}`;
    if (import.meta.env.DEV) console.info(`[cameras] ${this.statusReason ?? `all ${shown} shown`}`);
    this.viewer?.scene.requestRender();
  }
}
