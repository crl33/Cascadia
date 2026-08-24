/**
 * TimelineController (C5 core at P1 scope): turns scrub intent into knowledge-time state.
 * Owns the rAF coalescing — any number of scrub calls collapse to at most ONE store `asOf`
 * commit per animation frame — and aborts in-flight requests keyed to a superseded asOf
 * (their AbortSignal fires via TanStack cancelQueries). Plain TS; React renders TimelineBar,
 * this class decides. The scheduler and clock are injectable so tests are deterministic.
 */
import type { QueryClient } from '@tanstack/react-query';
import { asOfOfKey } from '../api/keys';
import type { SceneStoreApi } from '../state/store';
import { clampToWindow, truncateToMinute, windowEndingAt } from './window';

export interface FrameScheduler {
  request(callback: () => void): number;
  cancel(handle: number): void;
}

const rafScheduler: FrameScheduler = {
  request: (callback) => window.requestAnimationFrame(() => callback()),
  cancel: (handle) => window.cancelAnimationFrame(handle),
};

export class TimelineController {
  private pendingIso: string | null = null;
  private frameHandle: number | null = null;

  constructor(
    private readonly store: SceneStoreApi,
    private readonly queryClient: QueryClient,
    private readonly scheduler: FrameScheduler = rafScheduler,
    private readonly nowIso: () => string = () => new Date().toISOString(),
  ) {}

  /** Scrub intent at any rate; the latest value wins, committed once on the next frame. */
  scrub(iso: string): void {
    this.pendingIso = iso;
    if (this.frameHandle === null) this.frameHandle = this.scheduler.request(this.flush);
  }

  /** Back to live: mode 'now', window re-anchored at now, replay requests aborted. */
  snapToNow(): void {
    this.cancelPendingFrame();
    this.pendingIso = null;
    this.store.getState().setTimeline({ mode: 'now', asOf: null, window: windowEndingAt(this.nowIso()) });
    this.abortSuperseded(null);
  }

  dispose(): void {
    this.cancelPendingFrame();
    this.pendingIso = null;
  }

  private readonly flush = (): void => {
    this.frameHandle = null;
    const iso = this.pendingIso;
    this.pendingIso = null;
    if (iso === null) return;
    const state = this.store.getState();
    const asOf = clampToWindow(truncateToMinute(iso), state.timeline.window);
    if (asOf === state.timeline.asOf) return;
    state.setTimeline({ mode: 'past', asOf, window: state.timeline.window });
    this.abortSuperseded(asOf);
  };

  /** Cancels every in-flight query whose key names a different knowledge time than the current one. */
  private abortSuperseded(currentAsOf: string | null): void {
    const keep = currentAsOf ?? 'now';
    void this.queryClient.cancelQueries({
      predicate: (query) => {
        const asOf = asOfOfKey(query.queryKey);
        return asOf !== null && asOf !== keep;
      },
    });
  }

  private cancelPendingFrame(): void {
    if (this.frameHandle !== null) {
      this.scheduler.cancel(this.frameHandle);
      this.frameHandle = null;
    }
  }
}
