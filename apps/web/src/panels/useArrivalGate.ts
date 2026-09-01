/**
 * useArrivalGate: the React face of the arrival gate (arrival-gate.ts). Returns 'hold' while
 * the store's coarse flightState is 'flying' and for ARRIVAL_HOLD_MS after it settles, else
 * 'show'. The 'flying' branch is read straight from the render so the panel never paints the
 * one frame between the store flip and the effect. Reduced motion collapses the hold to 0:
 * its flights are cuts and the panel must not wait on a settled picture that is already there.
 */
import { useEffect, useState, useSyncExternalStore } from 'react';
import { resolveMotion } from '../design-system/motion';
import { useSceneStore } from '../state/store';
import { ARRIVAL_HOLD_MS, createArrivalGate, type ArrivalGate } from './arrival-gate';

export function useArrivalGate(): ArrivalGate {
  const flightState = useSceneStore((s) => s.flightState);
  const reduced = useSceneStore((s) => resolveMotion(s.motionSetting, s.systemReducedMotion) === 'reduced');
  const [machine] = useState(() => createArrivalGate());
  useEffect(() => () => machine.dispose(), [machine]);
  useEffect(() => { machine.setHoldMs(reduced ? 0 : ARRIVAL_HOLD_MS); }, [machine, reduced]);
  useEffect(() => { machine.update(flightState); }, [machine, flightState]);
  const gate = useSyncExternalStore(machine.subscribe, machine.gate, machine.gate);
  return flightState === 'flying' ? 'hold' : gate;
}
