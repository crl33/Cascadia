/** Mirrors the selection and motion setting into the URL (replaceState) so a reload reproduces the view. */
import { useEffect } from 'react';
import { useSceneStore } from '../state/store';
import { serializeDeepLink } from './deep-link';

export function UrlSync() {
  useEffect(() => {
    const write = () => {
      const s = useSceneStore.getState();
      const qs = serializeDeepLink({ basinId: s.selectedBasinId, forecastPointId: s.selectedForecastPointId, motion: s.motionSetting, band: null });
      const next = `${window.location.pathname}${qs}`;
      if (next !== `${window.location.pathname}${window.location.search}`) window.history.replaceState(null, '', next);
    };
    write();
    return useSceneStore.subscribe((s) => [s.selectedBasinId, s.selectedForecastPointId, s.motionSetting] as const, write, { equalityFn: (a, b) => a[0] === b[0] && a[1] === b[1] && a[2] === b[2] });
  }, []);
  return null;
}
