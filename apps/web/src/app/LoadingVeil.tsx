/**
 * LoadingVeil: the cinematic cold start, now with a REAL percentage (mission §7–8).
 *
 * The number is the boot manifest's weighted aggregate (`boot-progress.ts`): renderer 5 %,
 * tile-queue drain 55 %, discrete boot queries 25 %, live envelope 15 %. Every point is
 * measured work; the module clamps it monotonic and reserves 100 for SCENE_VISUAL_READY
 * (renderer + sustained-empty tile queue + all queries settled + live settled-or-degraded).
 *
 * Reveal: 100 % → a short settle beat → one fade. The hard timeout stays as the honesty
 * valve — a degraded world that says so beats an eternal veil — but with the bar showing
 * real progress it is a last resort, not the usual path.
 *
 * Reduced motion: the fade becomes a cut; the bar still fills (width is information).
 */
import { useEffect, useRef, useState } from 'react';
import { useBasins, useCameras, useFloodGeography, useLabels, useRiverNetwork, useVizBasins } from '../api/hooks';
import { warmDomainDeep, warmDomainForBoot } from '../layers/basemap/domain-warmer';
import type { SceneController } from '../scene/SceneController';
import { createBootProgress } from './boot-progress';

const REVEAL_TIMEOUT_MS = 30_000;
const SETTLE_BEAT_MS = 400;
const FADE_MS = 700;

const STAGE_TEXT = {
  earth: 'STARTING RENDERER',
  terrain: 'COMPOSING TERRAIN',
  regional: 'PREPARING REGIONAL MAP',
  hydrography: 'LOADING HYDROGRAPHY',
  live: 'CHECKING LIVE CONDITIONS',
  ready: 'READY',
} as const;

const settled = (q: { isSuccess: boolean; isError: boolean }) => q.isSuccess || q.isError;

export function LoadingVeil({ controller }: { controller: SceneController | null }) {
  const [ground, setGround] = useState(false);
  const [groundProgress, setGroundProgress] = useState(0);
  const [regional, setRegional] = useState<{ done: number; total: number }>({ done: 0, total: 1 });
  const [leaving, setLeaving] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const publishRef = useRef<ReturnType<typeof createBootProgress> | null>(null);
  publishRef.current ??= createBootProgress();

  const basins = useBasins();
  const labels = useLabels();
  const network = useRiverNetwork();
  const cameras = useCameras();
  const flood = useFloodGeography();
  const viz = useVizBasins();

  useEffect(() => {
    if (!controller) return;
    const offComposed = controller.onGroundComposed(() => setGround(true));
    const offProgress = controller.onGroundProgress((p) => setGroundProgress(p));
    return () => {
      offComposed();
      offProgress();
    };
  }, [controller]);

  // The availability stage: the whole PNW pyramid z5–z9 into the HTTP cache, with REAL
  // counts. Runs once; near-instant when the cache is already warm.
  useEffect(() => {
    const aborter = new AbortController();
    void warmDomainForBoot((done, total) => setRegional({ done, total }), aborter.signal);
    return () => aborter.abort();
  }, []);

  const dataTasks = [basins, labels, network, cameras, flood];
  const publish = publishRef.current;
  const { percent, ready } = publish({
    renderer: controller !== null,
    groundProgress,
    groundComposed: ground,
    dataTasksDone: dataTasks.filter(settled).length,
    dataTasksTotal: dataTasks.length,
    liveSettled: settled(viz),
    regionalDone: regional.done,
    regionalTotal: regional.total,
  });

  useEffect(() => {
    if (revealed) return;
    const timeout = window.setTimeout(() => setLeaving(true), REVEAL_TIMEOUT_MS);
    return () => window.clearTimeout(timeout);
  }, [revealed]);
  useEffect(() => {
    if (!ready || leaving) return;
    const beat = window.setTimeout(() => setLeaving(true), SETTLE_BEAT_MS);
    return () => window.clearTimeout(beat);
  }, [ready, leaving]);
  useEffect(() => {
    if (!leaving || revealed) return;
    const fade = window.setTimeout(() => setRevealed(true), FADE_MS);
    return () => window.clearTimeout(fade);
  }, [leaving, revealed]);
  // Post-reveal deep warm: z10 across the domain, quietly — within the first minute the
  // whole basin-band working area is local too.
  useEffect(() => {
    if (!revealed) return;
    const aborter = new AbortController();
    const start = window.setTimeout(() => { void warmDomainDeep(aborter.signal); }, 6_000);
    return () => {
      window.clearTimeout(start);
      aborter.abort();
    };
  }, [revealed]);

  if (revealed) return null;
  const stage =
    controller === null ? 'earth'
    : !ground ? 'terrain'
    : regional.done < regional.total ? 'regional'
    : dataTasks.filter(settled).length < dataTasks.length ? 'hydrography'
    : !settled(viz) ? 'live'
    : 'ready';
  return (
    <div className={`loading-veil${leaving ? ' leaving' : ''}`} data-testid="loading-veil" role="status" aria-live="polite">
      {/* One composed glass object (owner 2026-09-01): the loading menu is the same
          material as every other surface — system glass, sheet squircle, specular rim. */}
      <div className="loading-veil-card glass-surface glass-panel shape-sheet">
        <div className="loading-veil-mark">
          <span className="loading-veil-word">CASCADIA</span>
          <span className="loading-veil-sub">PAPSUKKAL</span>
        </div>
        <span className="loading-veil-percent mono" data-testid="loading-percent">{percent}%</span>
        <span className="loading-veil-stage">{STAGE_TEXT[stage]}</span>
        <span className="loading-veil-track" aria-hidden="true">
          <span className="loading-veil-fill" style={{ width: `${percent}%` }} />
        </span>
      </div>
    </div>
  );
}
