/**
 * Arrival gate (film rule 3, cesium-cinematic-plan-2026-09-01 row 1 / step 1.6): a panel is
 * part of the ARRIVAL, never of the flight. While the camera is flying the gate holds; when
 * the flight settles it keeps holding for ARRIVAL_HOLD_MS so the ground lands first and the
 * panel arrives as the second beat, not as chrome sliding over a globe in motion.
 *
 * Pure state machine — no React, no DOM — so the timing is unit-testable with fake timers.
 * A cut the observer never saw as 'flying' (deep-link load, reduced motion) has nothing to
 * hold: 'settled' with the gate already open is a no-op, and a hold of 0 ms releases
 * synchronously (reduced motion adds nothing beyond the frame that already happened).
 */
import type { FlightState } from '../state/store';

export const ARRIVAL_HOLD_MS = 400;

export type ArrivalGate = 'hold' | 'show';

export interface ArrivalGateMachine {
  /** Feed the coarse flight state (from the store's subscription or a React effect). */
  update(flightState: FlightState): void;
  /** The post-settle hold length; 0 releases synchronously on settle. */
  setHoldMs(ms: number): void;
  gate(): ArrivalGate;
  subscribe(listener: () => void): () => void;
  /** Cancels a pending release; the gate keeps its last value. */
  dispose(): void;
}

export function createArrivalGate(holdMs: number = ARRIVAL_HOLD_MS): ArrivalGateMachine {
  let gate: ArrivalGate = 'show';
  let hold = holdMs;
  let timer: ReturnType<typeof setTimeout> | null = null;
  const listeners = new Set<() => void>();

  const set = (next: ArrivalGate) => {
    if (next === gate) return;
    gate = next;
    listeners.forEach((l) => l());
  };
  const cancel = () => {
    if (timer === null) return;
    clearTimeout(timer);
    timer = null;
  };

  return {
    update(flightState) {
      if (flightState === 'flying') {
        cancel();
        set('hold');
        return;
      }
      if (flightState === 'idle') {
        cancel();
        set('show');
        return;
      }
      // settled: only a gate that was closed by a flight has a hold to serve.
      if (gate === 'show' || timer !== null) return;
      if (hold <= 0) {
        set('show');
        return;
      }
      timer = setTimeout(() => {
        timer = null;
        set('show');
      }, hold);
    },
    setHoldMs(ms) { hold = ms; },
    gate: () => gate,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    dispose: cancel,
  };
}
