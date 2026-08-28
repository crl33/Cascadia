/**
 * RiverNetworkLayer: the hydrologic skeleton of Cascadia's world — river polylines, clamped
 * to the ground, CARTOGRAPHIC register (where the rivers ARE; every state stays on the
 * truth-classed markers and panels). Geometry is the offline OSM derivation served at
 * /geo/rivers (`method:river-network-osm@1.0.0`, clipped to the seeded HUC8-union basins —
 * the caveat travels in the payload's provenance).
 *
 * All presentation lives in style.ts and is tested there; this file diffs entities and
 * applies the result — the same discipline as every other layer.
 */
import { Cartesian3, CustomDataSource, ColorMaterialProperty, Color, type Viewer } from 'cesium';
import type { RiverNetwork } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { riverLine } from './style';

interface LineRecord { basinId: string; mainstem: boolean; entityIds: string[] }

const TAG_PREFIX = 'river_network|';
const hslToColor = (c: { h: number; s: number; l: number }, alpha: number) =>
  Color.fromHsl(c.h / 360, c.s / 100, c.l / 100, alpha);

export class RiverNetworkLayer implements SceneLayer<RiverNetwork> {
  readonly id = 'river_network' as const;
  readonly displayName = 'River network (cartographic)';
  readonly truthClass = 'cartographic' as const;
  readonly bands: SceneLayer['bands'] = {
    orbital: 'reduced', state: 'full', basin: 'full', river: 'full', local: 'full',
  };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  private viewer: Viewer | null = null;
  private readonly source = new CustomDataSource('river_network');
  private readonly records: LineRecord[] = [];
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
    this.records.length = 0;
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
    // Rivers do not animate here: flow is a state, and state is not this layer's register.
  }

  setData(data: RiverNetwork): void {
    if (this.disposed) return;
    this.source.entities.removeAll();
    this.records.length = 0;
    let lines = 0;
    for (const [basinId, basin] of Object.entries(data.basins)) {
      for (const [riverIndex, river] of basin.rivers.entries()) {
        const entityIds: string[] = [];
        for (const [pathIndex, path] of river.paths.entries()) {
          if (path.length < 2) continue;
          const id = `${TAG_PREFIX}${basinId}|${riverIndex}|${pathIndex}`;
          this.source.entities.add({
            id,
            polyline: {
              positions: Cartesian3.fromDegreesArray(path.flat()),
              clampToGround: true,
              width: 1,
            },
          });
          entityIds.push(id);
          lines += 1;
        }
        this.records.push({ basinId, mainstem: river.mainstem, entityIds });
      }
    }
    this.status = lines === 0 ? 'unknown' : 'current';
    this.statusReason = lines === 0 ? 'the network document holds no drawable rivers' : null;
    this.restyle();
  }

  hitTest(rendererTag: string): LayerHit | null {
    if (!rendererTag.startsWith(TAG_PREFIX)) return null;
    const basinId = rendererTag.slice(TAG_PREFIX.length).split('|')[0] ?? null;
    return basinId ? { layerId: this.id, entityId: basinId, basinId } : null;
  }

  private restyle(): void {
    for (const record of this.records) {
      const style = riverLine({
        mainstem: record.mainstem,
        band: this.band,
        inSelectedBasin: record.basinId === this.selection.basinId,
      });
      for (const id of record.entityIds) {
        const entity = this.source.entities.getById(id);
        const polyline = entity?.polyline;
        if (!entity || !polyline) continue;
        entity.show = style.show && this.visible;
        if (!entity.show) continue;
        polyline.width = Math.max(style.widthPx, 0.5) as never;
        polyline.material = new ColorMaterialProperty(hslToColor(style.color, style.alpha));
      }
    }
    this.viewer?.scene.requestRender();
  }
}
