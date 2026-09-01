import { describe, expect, it } from 'vitest';
import { bootPercent, createBootProgress, sceneVisualReady, type BootState } from './boot-progress';

const state = (over: Partial<BootState>): BootState => ({
  renderer: false,
  groundProgress: 0,
  groundComposed: false,
  dataTasksDone: 0,
  dataTasksTotal: 4,
  liveSettled: false,
  regionalDone: 0,
  regionalTotal: 260,
  deviceMeasured: false,
  ...over,
});

describe('boot manifest — a percentage that corresponds to real work', () => {
  it('nothing done is 0; everything done is 100; weights are the documented split', () => {
    expect(bootPercent(state({}))).toBe(0);
    const done = state({ renderer: true, groundProgress: 1, groundComposed: true, dataTasksDone: 4, liveSettled: true, regionalDone: 260, deviceMeasured: true });
    expect(bootPercent(done)).toBe(100);
    // renderer alone = 5; data alone = 25; live alone = 10; device alone = 5
    expect(bootPercent(state({ renderer: true }))).toBeCloseTo(5);
    expect(bootPercent(state({ dataTasksDone: 4 }))).toBeCloseTo(25);
    expect(bootPercent(state({ liveSettled: true }))).toBeCloseTo(10);
    expect(bootPercent(state({ deviceMeasured: true }))).toBeCloseTo(5);
  });

  it('a transiently-empty tile queue cannot claim the full ground slice — composed is the gate', () => {
    const transient = bootPercent(state({ renderer: true, groundProgress: 1, groundComposed: false }));
    const composed = bootPercent(state({ renderer: true, groundProgress: 1, groundComposed: true }));
    expect(transient).toBeLessThan(composed);
  });

  it('a delayed critical resource delays 100 — ready is all-critical, not most', () => {
    const missingGround = state({ renderer: true, groundProgress: 1, dataTasksDone: 4, liveSettled: true, regionalDone: 260 });
    expect(sceneVisualReady(missingGround)).toBe(false);
    const missingData = state({ renderer: true, groundComposed: true, dataTasksDone: 3, liveSettled: true, regionalDone: 260 });
    expect(sceneVisualReady(missingData)).toBe(false);
    // the regional map is CRITICAL: without complete availability, scrolling is patchwork
    const missingRegional = state({ renderer: true, groundComposed: true, dataTasksDone: 4, liveSettled: true, regionalDone: 100, deviceMeasured: true });
    expect(sceneVisualReady(missingRegional)).toBe(false);
    // the device measurement is the LAST stage: everything else done is still not ready
    const missingDevice = state({ renderer: true, groundComposed: true, dataTasksDone: 4, liveSettled: true, regionalDone: 260 });
    expect(sceneVisualReady(missingDevice)).toBe(false);
  });

  it('an optional live failure degrades and completes — the bar never parks at 94 %', () => {
    // liveSettled is success OR error by construction upstream; here it simply completes.
    const degraded = state({ renderer: true, groundComposed: true, groundProgress: 1, dataTasksDone: 4, liveSettled: true, regionalDone: 260, deviceMeasured: true });
    expect(sceneVisualReady(degraded)).toBe(true);
    expect(bootPercent(degraded)).toBe(100);
  });

  it('published progress is monotonic even when the tile queue grows (raw regresses)', () => {
    const publish = createBootProgress();
    const p1 = publish(state({ renderer: true, groundProgress: 0.8 })).percent;
    const p2 = publish(state({ renderer: true, groundProgress: 0.4 })).percent; // queue grew
    const p3 = publish(state({ renderer: true, groundProgress: 0.9 })).percent;
    expect(p2).toBeGreaterThanOrEqual(p1 - 0); // never below what was shown
    expect(p2).toBe(p1);
    expect(p3).toBeGreaterThanOrEqual(p2);
  });

  it('only SCENE_VISUAL_READY publishes 100 — 99 is the cap while anything is outstanding', () => {
    const publish = createBootProgress();
    const almost = publish(
      state({ renderer: true, groundProgress: 1, groundComposed: true, dataTasksDone: 4, liveSettled: false, regionalDone: 260, deviceMeasured: true }),
    );
    expect(almost.percent).toBeLessThanOrEqual(99);
    expect(almost.ready).toBe(false);
    const done = publish(
      state({ renderer: true, groundProgress: 1, groundComposed: true, dataTasksDone: 4, liveSettled: true, regionalDone: 260, deviceMeasured: true }),
    );
    expect(done.percent).toBe(100);
    expect(done.ready).toBe(true);
  });
});
