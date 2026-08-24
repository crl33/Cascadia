/**
 * Mirrors selection, motion, knowledge time and (when captured) the camera pose into the URL
 * (replaceState, trailing-debounced so a scrub rewrites the URL at most every 200 ms), so a
 * reload reproduces the view (docs/CAMERA_SYSTEM.md §7).
 */
import { useEffect } from 'react';
import { shallow } from 'zustand/shallow';
import { useSceneStore } from '../state/store';
import { serializeDeepLink } from './deep-link';

const URL_DEBOUNCE_MS = 200;

export function UrlSync() {
  useEffect(() => {
    let timer: number | null = null;
    const write = () => {
      timer = null;
      const s = useSceneStore.getState();
      const qs = serializeDeepLink({
        basinId: s.selectedBasinId,
        forecastPointId: s.selectedForecastPointId,
        motion: s.motionSetting,
        band: null,
        asOf: s.timeline.asOf,
        cam: s.cameraPose,
      });
      const next = `${window.location.pathname}${qs}`;
      if (next !== `${window.location.pathname}${window.location.search}`) window.history.replaceState(null, '', next);
    };
    const schedule = () => {
      if (timer !== null) window.clearTimeout(timer);
      timer = window.setTimeout(write, URL_DEBOUNCE_MS);
    };
    write();
    const unsubscribe = useSceneStore.subscribe(
      (s) => [s.selectedBasinId, s.selectedForecastPointId, s.motionSetting, s.timeline.asOf, s.cameraPose] as const,
      schedule,
      { equalityFn: shallow },
    );
    return () => {
      if (timer !== null) window.clearTimeout(timer);
      unsubscribe();
    };
  }, []);
  return null;
}
