/**
 * LabelsLayer: the app-owned place-name hierarchy — CARTOGRAPHIC register, the world's own
 * names over the world's own imagery (design direction 2026-08-28: never borrow the label
 * hierarchy from a road-map raster).
 *
 * Data is the static /geo/labels document (GNIS names + editorial tiers, built by
 * scripts/build_labels.py). WHAT shows is decided by the pure `selectLabels` (band budgets,
 * priority, spacing — SEMANTIC_ZOOM §6 subset) and HOW it looks by `style.ts`; this file only
 * diffs the Cesium LabelCollection when band, selection or data change. Nothing runs per
 * frame; a full rebuild moves ≤ 22 labels (the largest band budget).
 *
 * V1 simplification, documented: labels are clamped to ground but NOT terrain-occluded
 * (disableDepthTestDistance ∞). The doctrine wants anchors behind terrain hidden; at this
 * app's camera pitches a ridge-hidden anchor is rare, and depth-tested clamped labels
 * z-fight into the hillsides. Revisit with the oblique-camera work.
 */
import {
  Cartesian2,
  Cartesian3,
  Color,
  HeightReference,
  HorizontalOrigin,
  LabelCollection,
  LabelStyle as CesiumLabelStyle,
  SceneTransforms,
  VerticalOrigin,
  type Viewer,
} from 'cesium';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { selectLabels, type LabelEntry, type ScreenProjection } from './select';
import { displayText, LABEL_STYLE } from './style';

export interface LabelSet {
  labels: LabelEntry[];
}

const rgba = (c: { r: number; g: number; b: number; a: number }) => new Color(c.r, c.g, c.b, c.a);

export class LabelsLayer implements SceneLayer<LabelSet> {
  readonly id = 'labels' as const;
  readonly displayName = 'Place names (GNIS)';
  readonly truthClass = 'cartographic' as const;
  readonly bands: SceneLayer['bands'] = {
    orbital: 'reduced', state: 'full', basin: 'full', river: 'full', local: 'full',
  };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  private viewer: Viewer | null = null;
  private collection: LabelCollection | null = null;
  private data: LabelSet | null = null;
  private band: Band = 'orbital';
  private selection: SelectionState = { basinId: null, forecastPointId: null, hovered: null };
  private visible = true;
  private disposed = false;

  private detachMoveEnd: (() => void) | null = null;

  mount(scene: SceneHandle): void {
    this.viewer = viewerOf(scene);
    this.collection = new LabelCollection({ scene: this.viewer.scene });
    this.viewer.scene.primitives.add(this.collection);
    // Re-place on camera settle: collision is SCREEN-space (the doctrine's 28-40 px, not a
    // ground-distance guess), so a settled camera re-evaluates which names fit. moveEnd is a
    // coarse semantic event — nothing here runs per frame.
    const onMoveEnd = () => this.rebuild();
    this.viewer.camera.moveEnd.addEventListener(onMoveEnd);
    this.detachMoveEnd = () => this.viewer?.camera.moveEnd.removeEventListener(onMoveEnd);
    this.rebuild();
  }

  unmount(): void {
    this.detachMoveEnd?.();
    this.detachMoveEnd = null;
    if (this.viewer && this.collection) {
      this.viewer.scene.primitives.remove(this.collection); // remove destroys the collection
    }
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

  setSelection(selection: SelectionState): void {
    if (selection.basinId === this.selection.basinId) {
      this.selection = selection;
      return; // labels only react to the BASIN half of the selection
    }
    this.selection = selection;
    this.rebuild();
  }

  setMotion(_motion: MotionPreference): void {
    // Label fades are cinematic and not implemented in v1; nothing to configure.
  }

  setData(data: LabelSet): void {
    if (this.disposed) return;
    this.data = data;
    this.status = data.labels.length === 0 ? 'unknown' : 'current';
    this.statusReason = data.labels.length === 0 ? 'the label document holds no labels' : null;
    this.rebuild();
  }

  hitTest(_rendererTag: string): LayerHit | null {
    return null; // names are not selectable entities
  }

  private projection(): ScreenProjection | undefined {
    const viewer = this.viewer;
    if (!viewer) return undefined;
    const canvas = viewer.scene.canvas;
    const scratch = new Cartesian2();
    return {
      width: canvas.clientWidth,
      height: canvas.clientHeight,
      project: (lon, lat) => {
        const p = SceneTransforms.worldToWindowCoordinates(viewer.scene, Cartesian3.fromDegrees(lon, lat), scratch);
        return p ? { x: p.x, y: p.y } : null;
      },
    };
  }

  private rebuild(): void {
    if (!this.collection || !this.data) return;
    this.collection.removeAll();
    const chosen = selectLabels(this.data.labels, this.band, this.selection.basinId, this.projection());
    for (const entry of chosen) {
      const style = LABEL_STYLE[entry.kind];
      this.collection.add({
        position: Cartesian3.fromDegrees(entry.lon, entry.lat),
        text: displayText(entry.name, entry.kind),
        font: style.font,
        fillColor: rgba(style.fill),
        outlineColor: rgba(style.outline),
        outlineWidth: style.outlineWidth,
        style: CesiumLabelStyle.FILL_AND_OUTLINE,
        horizontalOrigin: HorizontalOrigin.CENTER,
        verticalOrigin: VerticalOrigin.BOTTOM,
        pixelOffset: new Cartesian2(0, -4),
        heightReference: HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      });
    }
    this.collection.show = this.visible;
    this.viewer?.scene.requestRender();
  }
}
