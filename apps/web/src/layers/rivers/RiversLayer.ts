/**
 * RiversLayer: forecast-point markers (RiverVisualizationState items with a location) as point
 * entities with hover/selection labels. Visible at basin/river/local bands. Pickable: the
 * renderer tag is `rivers|<entity id>`; SceneController resolves it through hitTest.
 */
import { Cartesian2, Cartesian3, Color, CustomDataSource, Entity, LabelStyle, VerticalOrigin, type Viewer } from 'cesium';
import type { RiverEnvelope, RiverVisualizationState } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { riverMarker } from './style';
import { COLOR } from '../../design-system/tokens';

const TAG_PREFIX = 'rivers|';
const hslToColor = (c: { h: number; s: number; l: number }, alpha = 1) => Color.fromHsl(c.h / 360, c.s / 100, c.l / 100, alpha);

interface MarkerRecord { item: RiverVisualizationState; freshness: RiverEnvelope['provenance_refs'][string]['freshness']['state']; entity: Entity }

export class RiversLayer implements SceneLayer<RiverEnvelope> {
  readonly id = 'rivers' as const;
  readonly displayName = 'Forecast points (NWPS) with observed category';
  readonly truthClass = 'observation' as const;
  readonly bands: SceneLayer['bands'] = { orbital: 'hidden', state: 'hidden', basin: 'full', river: 'full', local: 'full' };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  private viewer: Viewer | null = null;
  private readonly source = new CustomDataSource('rivers');
  private readonly markers = new Map<string, MarkerRecord>();
  private selection: SelectionState = { basinId: null, forecastPointId: null, hovered: null };
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
    this.markers.clear();
    this.disposed = true;
  }

  setVisible(visible: boolean): void {
    this.source.show = visible;
    this.viewer?.scene.requestRender();
  }

  setBand(_band: Band): void { /* markers have one LOD in the spike */ }

  setSelection(selection: SelectionState): void {
    this.selection = selection;
    this.restyle();
  }

  setMotion(_motion: MotionPreference): void { /* no animated channel in the spike */ }

  setData(doc: RiverEnvelope): void {
    if (this.disposed) return;
    if (doc.contract !== 'RiverVisualizationState') {
      this.status = 'error';
      this.statusReason = `unexpected contract ${doc.contract}`;
      return;
    }
    const wanted = new Set<string>();
    let unknownCount = 0;
    for (const item of doc.items) {
      if (!item.location) continue;
      wanted.add(item.id);
      const freshness = (item.observed && doc.provenance_refs[item.observed.prov]?.freshness.state) ?? 'missing';
      if ((item.observed_category ?? 'unknown') === 'unknown') unknownCount += 1;
      const existing = this.markers.get(item.id);
      if (existing) {
        existing.item = item;
        existing.freshness = freshness;
        existing.entity.position = Cartesian3.fromDegrees(item.location[0], item.location[1]) as never;
        continue;
      }
      const entity = this.source.entities.add({
        id: `${TAG_PREFIX}${item.id}`,
        position: Cartesian3.fromDegrees(item.location[0], item.location[1]),
        point: { pixelSize: 10, disableDepthTestDistance: Number.POSITIVE_INFINITY },
        label: {
          text: item.name, font: '13px system-ui, sans-serif', style: LabelStyle.FILL_AND_OUTLINE, outlineWidth: 3,
          verticalOrigin: VerticalOrigin.BOTTOM, pixelOffset: new Cartesian2(0, -14), show: false,
          disableDepthTestDistance: Number.POSITIVE_INFINITY, showBackground: true,
        },
      });
      this.markers.set(item.id, { item, freshness, entity });
    }
    for (const [id, record] of this.markers) {
      if (wanted.has(id)) continue;
      this.source.entities.remove(record.entity);
      this.markers.delete(id);
    }
    this.status = this.markers.size === 0 ? 'missing' : unknownCount === this.markers.size ? 'unknown' : unknownCount > 0 ? 'partial' : 'current';
    this.statusReason = this.status === 'current' ? null : `${unknownCount} of ${this.markers.size} points have an UNKNOWN observed category`;
    this.restyle();
  }

  hitTest(rendererTag: string): LayerHit | null {
    if (!rendererTag.startsWith(TAG_PREFIX)) return null;
    const entityId = rendererTag.slice(TAG_PREFIX.length);
    const record = this.markers.get(entityId);
    return record ? { layerId: this.id, entityId, basinId: record.item.basin_id } : null;
  }

  private restyle(): void {
    for (const { item, freshness, entity } of this.markers.values()) {
      const style = riverMarker({
        name: item.name,
        category: item.observed_category ?? 'unknown',
        freshness,
        selected: item.id === this.selection.forecastPointId,
        hovered: item.id === this.selection.hovered,
        trend: item.trend
          ? { direction: item.trend.direction, rate: item.trend.rate ?? null }
          : null,
      });
      if (entity.point) {
        entity.point.pixelSize = style.pixelSize as never;
        entity.point.color = hslToColor(style.color) as never;
        entity.point.outlineColor = hslToColor(style.outline) as never;
        entity.point.outlineWidth = style.outlineWidthPx as never;
      }
      if (entity.label) {
        entity.label.text = style.labelText as never;
        entity.label.show = style.labelVisible as never;
        entity.label.fillColor = hslToColor(style.color) as never;
        entity.label.outlineColor = hslToColor(COLOR.canvas) as never;
        entity.label.backgroundColor = hslToColor(COLOR.canvas, 0.8) as never;
      }
    }
    this.viewer?.scene.requestRender();
  }
}
