/**
 * Zustand store: client semantic state only (selection, altitude band, motion preference,
 * active layers, time fixed to 'now', quality tier, coarse flight state). No renderer types,
 * no server data (TanStack Query owns that), nothing updated per frame. scene/bridge.ts is the
 * only module that subscribes this store to the controllers.
 */
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type { MotionSetting } from '../design-system/motion';
import type { Band } from '../scene/bands';

export type EntityId = string;
export type LayerId = 'basemap' | 'basins' | 'rivers';
export type QualityTier = 'ultra' | 'high' | 'balanced' | 'low';
export type FlightState = 'idle' | 'flying' | 'settled';

export interface SceneState {
  selectedBasinId: EntityId | null;
  selectedForecastPointId: EntityId | null;
  altitudeBand: Band;
  motionSetting: MotionSetting;
  systemReducedMotion: boolean;
  activeLayers: readonly LayerId[];
  time: { valid: 'now' };
  qualityTier: QualityTier;
  flightState: FlightState;
}

export interface SceneActions {
  selectBasin(id: EntityId | null): void;
  selectForecastPoint(id: EntityId | null, basinId?: EntityId | null): void;
  setAltitudeBand(band: Band): void;
  setMotionSetting(setting: MotionSetting): void;
  setSystemReducedMotion(reduced: boolean): void;
  setLayerActive(layer: LayerId, active: boolean): void;
  setFlightState(state: FlightState): void;
}

export type SceneStore = SceneState & SceneActions;

export const DEFAULT_STATE: SceneState = {
  selectedBasinId: null,
  selectedForecastPointId: null,
  altitudeBand: 'orbital',
  motionSetting: 'system',
  systemReducedMotion: false,
  activeLayers: ['basemap', 'basins', 'rivers'],
  time: { valid: 'now' },
  qualityTier: 'balanced',
  flightState: 'idle',
};

export function createSceneStore(initial: Partial<SceneState> = {}) {
  return create<SceneStore>()(
    subscribeWithSelector((set) => ({
      ...DEFAULT_STATE,
      ...initial,
      selectBasin: (id) => set({ selectedBasinId: id, selectedForecastPointId: null }),
      selectForecastPoint: (id, basinId) =>
        set((s) => ({ selectedForecastPointId: id, selectedBasinId: basinId === undefined ? s.selectedBasinId : basinId })),
      setAltitudeBand: (band) => set({ altitudeBand: band }),
      setMotionSetting: (setting) => set({ motionSetting: setting }),
      setSystemReducedMotion: (reduced) => set({ systemReducedMotion: reduced }),
      setLayerActive: (layer, active) =>
        set((s) => ({ activeLayers: active ? [...new Set([...s.activeLayers, layer])] : s.activeLayers.filter((l) => l !== layer) })),
      setFlightState: (state) => set({ flightState: state }),
    })),
  );
}

export type SceneStoreApi = ReturnType<typeof createSceneStore>;

/** The app-wide store. main.tsx seeds it from the deep link before the first render. */
export const useSceneStore: SceneStoreApi = createSceneStore();
