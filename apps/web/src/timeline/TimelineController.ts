/**
 * TimelineController (C5 core at P1 scope, plus P2 event replay): turns scrub intent into
 * timeline state. Owns the rAF coalescing — any number of scrub calls collapse to at most ONE
 * store commit per animation frame — and, for knowledge-time scrubs, aborts in-flight requests
 * keyed to a superseded asOf (their AbortSignal fires via TanStack cancelQueries). Event-mode
 * scrubs commit the EVENT-time cursor `at` instead and abort nothing: event queries are keyed
 * by the whole archived window, never by the cursor. Plain TS; React renders TimelineBar,
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

  /** Event-mode scrub: same coalescing; the flush commits the EVENT-time cursor instead. */
  scrubEvent(iso: string): void {
    this.scrub(iso);
  }

  /** Back to live: mode 'now' (exits knowledge-time AND event replay), replay requests aborted. */
  snapToNow(): void {
    this.cancelPendingFrame();
    this.pendingIso = null;
    this.store.getState().setTimeline({ mode: 'now', asOf: null, window: windowEndingAt(this.nowIso()), eventId: null, at: null });
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
    const timeline = state.timeline;
    if (timeline.mode === 'event') {
      const at = clampToWindow(truncateToMinute(iso), timeline.window);
      if (at === timeline.at) return;
      state.setTimeline({ ...timeline, at });
      return; // no aborts: event-mode queries are keyed by the archived window, not the cursor
    }
    const asOf = clampToWindow(truncateToMinute(iso), timeline.window);
    if (asOf === timeline.asOf) return;
    state.setTimeline({ mode: 'past', asOf, window: timeline.window, eventId: null, at: null });
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
