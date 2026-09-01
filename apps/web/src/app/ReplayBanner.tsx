/**
 * Persistent replay-honesty banner: whenever the app is in past mode it states the knowledge
 * time on screen. Every freshness badge below it shows the REPLAYED freshness the server
 * returned for that knowledge time — never client-now math (docs/VISUAL_TRUTH_DOCTRINE.md).
 */
import { formatUtc } from '../panels/format';
import { useSceneStore } from '../state/store';

const localLabel = (iso: string): string =>
  new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });

export function ReplayBanner() {
  const timeline = useSceneStore((s) => s.timeline);
  if (timeline.mode !== 'past' || timeline.asOf === null) return null;
  // ONE temporal statement (mission §21): local time here, exact UTC on hover; the
  // timeline chip below stays a bare AS OF so the moment is never printed twice.
  return (
    <div className="replay-banner glass-surface glass-compact shape-capsule" role="status" data-testid="as-of-banner">
      <strong>AS OF <span className="mono" title={formatUtc(timeline.asOf)}>{localLabel(timeline.asOf)}</span></strong>
      {' '}— showing what was known then; nothing learned later is shown.
    </div>
  );
}
