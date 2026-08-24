import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';
import { keys } from '../api/keys';
import { createSceneStore } from '../state/store';
import { TimelineController, type FrameScheduler } from './TimelineController';
import type { TimelineWindow } from './window';

const WINDOW: TimelineWindow = ['2026-08-21T12:00:00Z', '2026-08-24T12:00:00Z'];
const NOW = '2026-08-24T12:00:00Z';
const EVENT_WINDOW: TimelineWindow = ['2025-12-03T08:00:00Z', '2025-12-23T08:00:00Z'];
const EVENT_ID = 'event-zero-2025-12';

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

function makeController(timeline = { mode: 'now' as const, asOf: null, window: WINDOW, eventId: null, at: null }) {
  const store = createSceneStore({ timeline });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const frames = makeScheduler();
  const controller = new TimelineController(store, queryClient, frames.scheduler, () => NOW);
  let commits = 0;
  store.subscribe((s) => s.timeline, () => { commits += 1; });
  return { store, queryClient, frames, controller, commits: () => commits };
}

const makeEventController = () =>
  makeController({ mode: 'event' as never, asOf: null, window: EVENT_WINDOW, eventId: EVENT_ID as never, at: '2025-12-09T17:01:00Z' as never });

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
    expect(store.getState().timeline).toEqual({ mode: 'past', asOf: '2026-08-22T03:00:00Z', window: WINDOW, eventId: null, at: null });
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
    expect(store.getState().timeline).toEqual({ mode: 'now', asOf: null, window: WINDOW, eventId: null, at: null });
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

describe('TimelineController in event mode (P2 Event Zero)', () => {
  it('scrubEvent commits the EVENT cursor once per frame, minute-truncated and clamped to the event window', () => {
    const { store, frames, controller, commits } = makeEventController();
    controller.scrubEvent('2025-12-12T06:00:00Z');
    controller.scrubEvent('2025-12-12T08:15:30Z');
    expect(commits()).toBe(0);
    frames.tick();
    expect(commits()).toBe(1);
    expect(store.getState().timeline).toEqual({
      mode: 'event', asOf: null, window: EVENT_WINDOW, eventId: EVENT_ID, at: '2025-12-12T08:15:00Z',
    });
    controller.scrubEvent('2027-01-01T00:00:00Z');   // beyond the event → clamps to the window end
    frames.tick();
    expect(store.getState().timeline.at).toBe(EVENT_WINDOW[1]);
    controller.scrubEvent('2027-06-01T00:00:00Z');   // clamps to the same instant → no commit
    frames.tick();
    expect(commits()).toBe(2);
  });

  it('event scrubs abort nothing: event-mode queries are keyed by the window, not the cursor', async () => {
    const { queryClient, frames, controller } = makeEventController();
    const windowSignals: AbortSignal[] = [];
    const asOfSignals: AbortSignal[] = [];
    queryClient.fetchQuery({ queryKey: keys.runs('fp:nwps:MVEW1', EVENT_WINDOW[0], EVENT_WINDOW[1]), queryFn: hanging(windowSignals) }).catch(() => {});
    queryClient.fetchQuery({ queryKey: keys.riverState('fp:nwps:MVEW1', '2026-08-22T01:00:00Z'), queryFn: hanging(asOfSignals) }).catch(() => {});
    controller.scrubEvent('2025-12-12T08:15:00Z');
    frames.tick();
    await Promise.resolve();                          // let any (wrong) cancelation propagate
    expect(windowSignals[0]?.aborted).toBe(false);
    expect(asOfSignals[0]?.aborted).toBe(false);      // an event scrub is not a knowledge-time change
  });

  it('snapToNow exits event replay back to live', () => {
    const { store, frames, controller } = makeEventController();
    controller.scrubEvent('2025-12-12T08:15:00Z');
    controller.snapToNow();
    frames.tick();
    expect(store.getState().timeline).toEqual({ mode: 'now', asOf: null, window: WINDOW, eventId: null, at: null });
  });
});
