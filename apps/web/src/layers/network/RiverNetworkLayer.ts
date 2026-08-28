/**
 * RiverNetworkLayer: the hydrologic skeleton of Cascadia's world — river polylines, clamped
 * to the ground. Geometry is CARTOGRAPHIC (the offline OSM derivation served at /geo/rivers,
 * `method:river-network-osm@1.0.0`, clipped to the seeded HUC8-union basins — the caveat
 * travels in the payload's provenance). On top of it, `intensities` carries the contract's
 * per-river `flow_visual_intensity` join (match.ts): rivers RESPOND by width and alpha only
 * — presence, never hue — and a river with no defensible number renders at the cartographic
 * base (style.ts documents the register boundary).
 *
 * All presentation lives in style.ts and is tested there; this file diffs entities and
 * applies the result — the same discipline as every other layer. A data push whose network
 * is the SAME object only restyles: intensity refreshes arrive on query cadence and must not
 * rebuild thousands of polylines.
 */
import { Cartesian3, CustomDataSource, ColorMaterialProperty, Color, type Viewer } from 'cesium';
import type { RiverNetwork } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { riverIntensityKey } from './match';
import { riverLine } from './style';

interface LineRecord { basinId: string; name: string; mainstem: boolean; entityIds: string[] }

export interface RiverNetworkDisplay {
  network: RiverNetwork;
  /** riverIntensityKey(basinId, riverName) -> flow_visual_intensity (0-1). */
  intensities: Record<string, number>;
}

const TAG_PREFIX = 'river_network|';
const hslToColor = (c: { h: number; s: number; l: number }, alpha: number) =>
  Color.fromHsl(c.h / 360, c.s / 100, c.l / 100, alpha);

export class RiverNetworkLayer implements SceneLayer<RiverNetworkDisplay> {
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
  private lastNetwork: RiverNetwork | null = null;
  private intensities: Record<string, number> = {};
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

  setData(data: RiverNetworkDisplay): void {
    if (this.disposed) return;
    this.intensities = data.intensities;
    if (data.network === this.lastNetwork) {
      this.restyle(); // intensity refresh only; the geometry is the same document
      return;
    }
    this.lastNetwork = data.network;
    this.source.entities.removeAll();
    this.records.length = 0;
    let lines = 0;
    for (const [basinId, basin] of Object.entries(data.network.basins)) {
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
        this.records.push({ basinId, name: river.name, mainstem: river.mainstem, entityIds });
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
        intensity: this.intensities[riverIntensityKey(record.basinId, record.name)] ?? null,
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
