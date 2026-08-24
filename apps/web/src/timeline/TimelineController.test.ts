import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';
import { keys } from '../api/keys';
import { createSceneStore } from '../state/store';
import { TimelineController, type FrameScheduler } from './TimelineController';
import type { TimelineWindow } from './window';

const WINDOW: TimelineWindow = ['2026-08-21T12:00:00Z', '2026-08-24T12:00:00Z'];
const NOW = '2026-08-24T12:00:00Z';

/** Deterministic frame scheduler: callbacks run only when tick() is called (one frame). */
function makeScheduler() {
  const callbacks = new Map<number, () => void>();
  let seq = 0;
  const scheduler: FrameScheduler = {
    request: (callback) => {
      callbacks.set(++seq, callback);
      return seq;
    },
    cancel: (handle) => void callbacks.delete(handle),
  };
  const tick = () => {
    const pending = [...callbacks.values()];
    callbacks.clear();
    pending.forEach((callback) => callback());
  };
  return { scheduler, tick, pendingCount: () => callbacks.size };
}

function makeController() {
  const store = createSceneStore({ timeline: { mode: 'now', asOf: null, window: WINDOW } });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const frames = makeScheduler();
  const controller = new TimelineController(store, queryClient, frames.scheduler, () => NOW);
  let commits = 0;
  store.subscribe((s) => s.timeline, () => { commits += 1; });
  return { store, queryClient, frames, controller, commits: () => commits };
}

/** A queryFn that never resolves but records its AbortSignal. */
const hanging = (signals: AbortSignal[]) => ({ signal }: { signal: AbortSignal }) => {
  signals.push(signal);
  return new Promise<never>((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')));
  });
};

describe('TimelineController', () => {
  it('commits at most one asOf per animation frame, with the latest scrub value', () => {
    const { store, frames, controller, commits } = makeController();
    controller.scrub('2026-08-22T01:00:00Z');
    controller.scrub('2026-08-22T02:00:00Z');
    controller.scrub('2026-08-22T03:00:30Z');
    expect(commits()).toBe(0);                       // nothing lands before the frame
    frames.tick();
    expect(commits()).toBe(1);                       // one frame → one commit
    expect(store.getState().timeline).toEqual({ mode: 'past', asOf: '2026-08-22T03:00:00Z', window: WINDOW });
    frames.tick();
    expect(commits()).toBe(1);                       // an empty frame commits nothing
    controller.scrub('2026-08-22T04:00:00Z');
    frames.tick();
    expect(commits()).toBe(2);
    expect(store.getState().timeline.asOf).toBe('2026-08-22T04:00:00Z');
  });

  it('clamps scrubs to the window and skips no-op commits', () => {
    const { store, frames, controller, commits } = makeController();
    controller.scrub('2020-01-01T00:00:00Z');
    frames.tick();
    expect(store.getState().timeline.asOf).toBe(WINDOW[0]);
    controller.scrub('2020-06-01T00:00:00Z');        // clamps to the same window start
    frames.tick();
    expect(commits()).toBe(1);                       // same asOf → no second commit
  });

  it('snapToNow returns to live, re-anchors the window and drops a pending scrub', () => {
    const { store, frames, controller } = makeController();
    controller.scrub('2026-08-22T01:00:00Z');
    frames.tick();
    controller.scrub('2026-08-22T02:00:00Z');        // pending, never flushed
    controller.snapToNow();
    frames.tick();
    expect(frames.pendingCount()).toBe(0);
    expect(store.getState().timeline).toEqual({ mode: 'now', asOf: null, window: WINDOW });
  });

  it('aborts in-flight requests for a superseded asOf and keeps the current one', async () => {
    const { queryClient, frames, controller } = makeController();
    const oldSignals: AbortSignal[] = [];
    const liveSignals: AbortSignal[] = [];
    const currentSignals: AbortSignal[] = [];
    queryClient.fetchQuery({ queryKey: keys.riverState('fp:nwps:MVEW1', '2026-08-22T01:00:00Z'), queryFn: hanging(oldSignals) }).catch(() => {});
    queryClient.fetchQuery({ queryKey: keys.vizBasins(null), queryFn: hanging(liveSignals) }).catch(() => {});
    queryClient.fetchQuery({ queryKey: keys.vizRivers('basin:skagit', '2026-08-22T02:00:00Z'), queryFn: hanging(currentSignals) }).catch(() => {});
    controller.scrub('2026-08-22T02:00:00Z');
    frames.tick();
    await vi.waitFor(() => {
      expect(oldSignals[0]?.aborted).toBe(true);     // superseded asOf → aborted
      expect(liveSignals[0]?.aborted).toBe(true);    // live 'now' key is superseded too
    });
    expect(currentSignals[0]?.aborted).toBe(false);  // the committed asOf keeps its request
  });

  it('snapToNow aborts replay requests', async () => {
    const { queryClient, controller } = makeController();
    const signals: AbortSignal[] = [];
    queryClient.fetchQuery({ queryKey: keys.basinState('basin:skagit', '2026-08-22T01:00:00Z'), queryFn: hanging(signals) }).catch(() => {});
    controller.snapToNow();
    await vi.waitFor(() => expect(signals[0]?.aborted).toBe(true));
  });
});
