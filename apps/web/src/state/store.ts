/**
 * Zustand store: client semantic state only (selection, altitude band, motion preference,
 * active layers, knowledge time, quality tier, coarse flight state, deep-linkable camera pose).
 * No renderer types, no server data (TanStack Query owns that), nothing updated per frame —
 * timeline scrubs are rAF-coalesced by timeline/TimelineController before they land here.
 * scene/bridge.ts is the only module that subscribes this store to the controllers.
 */
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type { MotionSetting } from '../design-system/motion';
import type { Band } from '../scene/bands';
import { windowEndingAt, type TimelineWindow } from '../timeline/window';

export type EntityId = string;
export type LayerId = 'basemap' | 'basins' | 'rivers' | 'basin_susceptibility' | 'river_network' | 'precip_observed' | 'snow_cover' | 'labels';
export type QualityTier = 'ultra' | 'high' | 'balanced' | 'low';
export type FlightState = 'idle' | 'flying' | 'settled';
export type TimelineMode = 'now' | 'past' | 'event';

/**
 * Knowledge-time state (C5 core, P1 scope) plus event replay (P2 Event Zero): 'now' streams
 * live; 'past' replays knowledge time `asOf`; 'event' replays an archived event window in
 * EVENT time — `at` is a valid/issued-time cursor, `asOf` stays null and queries carry NO
 * as_of (ADR-0010: a backfilled row's knowledge time is its 2026 retrieval, so a
 * knowledge-time replay inside the event would honestly render UNKNOWN).
 */
export interface TimelineState {
  mode: TimelineMode;
  /** ISO 8601 UTC knowledge time, minute-aligned; non-null exactly when mode is 'past'. */
  asOf: string | null;
  /** The scrubbable window: [T−72h, T] live/past, or the event window in event mode. */
  window: TimelineWindow;
  /** The event being replayed (event/registry id); non-null exactly when mode is 'event'. */
  eventId: string | null;
  /** EVENT-time cursor, minute-aligned; non-null exactly when mode is 'event'. */
  at: string | null;
}

/**
 * Semantic camera pose for deep links (docs/CAMERA_SYSTEM.md §7): ids and numbers only, no
 * renderer types. Written only on flight settle by the scene bridge (integration point for the
 * camera workstream via setCameraPose) — never per frame. Any selection change invalidates it
 * so the URL never claims a view that is not shown.
 */
export interface CameraPose {
  anchor: { kind: 'entity'; id: EntityId } | { kind: 'geo'; lat: number; lon: number };
  rangeM: number;
  headingDeg: number;
  pitchDeg: number;
  mode: 'free' | 'orbit' | 'follow';
}

export interface SceneState {
  selectedBasinId: EntityId | null;
  selectedForecastPointId: EntityId | null;
  altitudeBand: Band;
  motionSetting: MotionSetting;
  systemReducedMotion: boolean;
  activeLayers: readonly LayerId[];
  time: { valid: 'now' };
  timeline: TimelineState;
  cameraPose: CameraPose | null;
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
  /** Written only by timeline/TimelineController (rAF-coalesced) and boot seeding. */
  setTimeline(timeline: TimelineState): void;
  setCameraPose(pose: CameraPose | null): void;
}

export type SceneStore = SceneState & SceneActions;

export const DEFAULT_STATE: SceneState = {
  selectedBasinId: null,
  selectedForecastPointId: null,
  altitudeBand: 'orbital',
  motionSetting: 'system',
  systemReducedMotion: false,
  activeLayers: ['basemap', 'snow_cover', 'precip_observed', 'basin_susceptibility', 'river_network', 'basins', 'rivers', 'labels'],
  time: { valid: 'now' },
  timeline: { mode: 'now', asOf: null, window: windowEndingAt(new Date().toISOString()), eventId: null, at: null },
  cameraPose: null,
  qualityTier: 'balanced',
  flightState: 'idle',
};

export function createSceneStore(initial: Partial<SceneState> = {}) {
  return create<SceneStore>()(
    subscribeWithSelector((set) => ({
      ...DEFAULT_STATE,
      ...initial,
      // A new selection reframes the camera, so a previously captured pose no longer describes the view.
      selectBasin: (id) => set({ selectedBasinId: id, selectedForecastPointId: null, cameraPose: null }),
      selectForecastPoint: (id, basinId) =>
        set((s) => ({ selectedForecastPointId: id, selectedBasinId: basinId === undefined ? s.selectedBasinId : basinId, cameraPose: null })),
      setAltitudeBand: (band) => set({ altitudeBand: band }),
      setMotionSetting: (setting) => set({ motionSetting: setting }),
      setSystemReducedMotion: (reduced) => set({ systemReducedMotion: reduced }),
      setLayerActive: (layer, active) =>
        set((s) => ({ activeLayers: active ? [...new Set([...s.activeLayers, layer])] : s.activeLayers.filter((l) => l !== layer) })),
      setFlightState: (state) => set({ flightState: state }),
      setTimeline: (timeline) => set({ timeline }),
      setCameraPose: (pose) => set({ cameraPose: pose }),
    })),
  );
}

export type SceneStoreApi = ReturnType<typeof createSceneStore>;

/** The app-wide store. main.tsx seeds it from the deep link before the first render. */
export const useSceneStore: SceneStoreApi = createSceneStore();
