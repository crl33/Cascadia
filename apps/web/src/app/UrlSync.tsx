/**
 * Mirrors selection, motion, replay time (knowledge as_of, or event id + EVENT-time cursor)
 * and (when captured) the camera pose into the URL (replaceState, trailing-debounced so a
 * scrub rewrites the URL at most every 200 ms), so a reload reproduces the view
 * (docs/CAMERA_SYSTEM.md §7).
 */
import { useEffect } from 'react';
import { shallow } from 'zustand/shallow';
import { useSceneStore } from '../state/store';
import { serializeDeepLink } from './deep-link';

const URL_DEBOUNCE_MS = 200;
const URL_MAX_LATENCY_MS = 1_000;

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
        eventId: s.timeline.eventId,
        at: s.timeline.at,
        cam: s.cameraPose,
        pinnedCameraId: s.pinnedCameraId,
      });
      const next = `${window.location.pathname}${qs}`;
      if (next !== `${window.location.pathname}${window.location.search}`) window.history.replaceState(null, '', next);
    };
    // Trailing debounce WITH a hard deadline: camera-pose churn under a slow renderer can
    // reschedule the trailing timer indefinitely (observed as a CI-only "as_of never left
    // the URL" flake) — after MAX_LATENCY the write happens regardless.
    let deadline: number | null = null;
    const flush = () => {
      deadline = null;
      if (timer !== null) window.clearTimeout(timer);
      timer = null;
      write();
    };
    const schedule = () => {
      if (timer !== null) window.clearTimeout(timer);
      timer = window.setTimeout(flush, URL_DEBOUNCE_MS);
      if (deadline === null) deadline = window.setTimeout(flush, URL_MAX_LATENCY_MS);
    };
    write();
    const unsubscribe = useSceneStore.subscribe(
      (s) => [s.selectedBasinId, s.selectedForecastPointId, s.motionSetting, s.timeline.asOf, s.timeline.eventId, s.timeline.at, s.cameraPose, s.pinnedCameraId] as const,
      schedule,
      { equalityFn: shallow },
    );
    return () => {
      if (timer !== null) window.clearTimeout(timer);
      if (deadline !== null) window.clearTimeout(deadline);
      unsubscribe();
    };
  }, []);
  return null;
}
