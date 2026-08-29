/**
 * LoadingVeil: the cinematic cold start (visual-continuity pass 2026-08-29). The world no
 * longer assembles in front of the user — a composed dark veil holds until the OPENING FRAME
 * is coherent, then fades once, revealing an already-built Earth.
 *
 * Readiness is real, never a fake percentage. Stages advance on actual events:
 *   INITIALIZING EARTH   — renderer constructing
 *   COMPOSING TERRAIN    — globe tile queue draining toward the first composed frame
 *   LOADING HYDROGRAPHY  — basins + labels + river geometry fetched
 *   LOADING LIVE STATE   — the first hydrologic envelope resolved (or honestly failed)
 * The veil reveals when the ground is composed AND hydrography settled; live state may
 * finish after the reveal (it has its own UNKNOWN honesty). A hard 18 s timeout reveals
 * regardless — a degraded world that says so beats an eternal veil.
 *
 * Reduced motion: the fade becomes a cut. The veil never returns after the first reveal;
 * in-app transitions have their own (existing) treatments.
 */
import { useEffect, useState } from 'react';
import { useIsFetching } from '@tanstack/react-query';
import { useBasins, useLabels, useRiverNetwork, useVizBasins } from '../api/hooks';
import type { SceneController } from '../scene/SceneController';

const REVEAL_TIMEOUT_MS = 18_000;

type Stage = 'earth' | 'terrain' | 'hydrography' | 'live' | 'revealed';

const STAGE_TEXT: Record<Exclude<Stage, 'revealed'>, string> = {
  earth: 'INITIALIZING EARTH',
  terrain: 'COMPOSING TERRAIN',
  hydrography: 'LOADING HYDROGRAPHY',
  live: 'LOADING LIVE STATE',
};

export function LoadingVeil({ controller }: { controller: SceneController | null }) {
  const [ground, setGround] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const basins = useBasins();
  const labels = useLabels();
  const network = useRiverNetwork();
  const viz = useVizBasins();
  const fetching = useIsFetching();

  useEffect(() => {
    if (!controller) return;
    return controller.onGroundComposed(() => setGround(true));
  }, [controller]);

  const settled = (q: { isSuccess: boolean; isError: boolean }) => q.isSuccess || q.isError;
  const hydrography = settled(basins) && settled(labels) && settled(network);
  const liveSettled = settled(viz);
  const ready = controller !== null && ground && hydrography;

  useEffect(() => {
    if (revealed) return;
    const timeout = window.setTimeout(() => setLeaving(true), REVEAL_TIMEOUT_MS);
    return () => window.clearTimeout(timeout);
  }, [revealed]);
  useEffect(() => {
    if (ready && !leaving) setLeaving(true);
  }, [ready, leaving]);
  useEffect(() => {
    if (!leaving || revealed) return;
    const fade = window.setTimeout(() => setRevealed(true), 700);
    return () => window.clearTimeout(fade);
  }, [leaving, revealed]);

  if (revealed) return null;
  const stage: Exclude<Stage, 'revealed'> =
    controller === null ? 'earth' : !ground ? 'terrain' : !hydrography ? 'hydrography' : 'live';
  const stageText = stage === 'live' && liveSettled ? 'REVEALING' : STAGE_TEXT[stage];
  return (
    <div className={`loading-veil${leaving ? ' leaving' : ''}`} data-testid="loading-veil" role="status" aria-live="polite">
      <div className="loading-veil-mark">
        <span className="loading-veil-word">CASCADIA</span>
        <span className="loading-veil-sub">PAPSUKKAL</span>
      </div>
      <div className="loading-veil-capsule">
        <span className="loading-veil-stage">{stageText}</span>
        <span className="loading-veil-shimmer" aria-hidden="true" data-active={fetching > 0 || !ground} />
      </div>
    </div>
  );
}
