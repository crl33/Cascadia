/** Thin top strip: wordmark, search, band indicator, motion toggle, flight state, health dot. */
import { useHealth } from '../api/hooks';
import { resolveMotion, type MotionSetting } from '../design-system/motion';
import { SearchBox } from '../interactions/SearchBox';
import { useSceneStore } from '../state/store';

const NEXT_MOTION: Record<MotionSetting, MotionSetting> = { system: 'reduced', reduced: 'full', full: 'system' };

export function TopStrip() {
  const band = useSceneStore((s) => s.altitudeBand);
  const motionSetting = useSceneStore((s) => s.motionSetting);
  const systemReduced = useSceneStore((s) => s.systemReducedMotion);
  const setMotionSetting = useSceneStore((s) => s.setMotionSetting);
  const flightState = useSceneStore((s) => s.flightState);
  const health = useHealth();
  const resolved = resolveMotion(motionSetting, systemReduced);
  const healthState = health.isError ? 'down' : health.data?.status ?? 'unknown';

  return (
    <header className="top-strip">
      <span className="wordmark">Cascadia Papsukkal</span>
      <SearchBox />
      <span className="band-indicator" data-testid="band-indicator" title="semantic altitude band">{band.toUpperCase()}</span>
      <span className="flight-state" data-testid="flight-state" data-flight-state={flightState}>{flightState === 'flying' ? 'flying…' : flightState}</span>
      <button
        type="button"
        className="motion-toggle"
        data-testid="motion-toggle"
        data-motion={resolved}
        title={`motion: ${motionSetting} (resolved ${resolved}); click to change`}
        onClick={() => setMotionSetting(NEXT_MOTION[motionSetting])}
      >
        motion {motionSetting === 'system' ? `system→${resolved}` : motionSetting}
      </button>
      <span className={`health-dot health-${healthState}`} data-testid="health-dot" title={`API health: ${healthState}`} role="status">
        <span className="visually-hidden">API health {healthState}</span>
      </span>
    </header>
  );
}
