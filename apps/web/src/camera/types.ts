/** Camera vocabulary (docs/CAMERA_SYSTEM.md §2–§3), spike subset. No renderer types. */
import type { Band } from '../scene/bands';
import type { MotionPreference } from '../design-system/motion';

export type FlightReason = 'selection' | 'search' | 'deep-link' | 'restore';
export type InterruptReason = 'user-input' | 'superseded' | 'reduced-motion-change' | 'dispose';

export interface GeoPoint { lon: number; lat: number }
export type Bbox = readonly [west: number, south: number, east: number, north: number];

export interface FlightOptions {
  reason: FlightReason;
  /** Force a cut (deep-link load) regardless of motion preference. */
  cut?: boolean;
  pitchDeg?: number;
  headingDeg?: number;
}

export interface FlightResult { outcome: 'settled' | 'interrupted'; band: Band; cut: boolean }

export interface FlightHandle {
  id: string;
  settled: Promise<FlightResult>;
  interrupt(reason?: InterruptReason): void;
}

export interface CameraEvents {
  started: { flightId: string; durationMs: number; cut: boolean; reason: FlightReason };
  settled: { flightId: string; cut: boolean };
  interrupted: { flightId: string; reason: InterruptReason };
}

export type { MotionPreference };
