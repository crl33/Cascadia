import { describe, expect, it } from 'vitest';
import { cameraMarker } from './style';

describe('cameraMarker', () => {
  it('cameras are invisible from orbit and state — local evidence, not orientation', () => {
    for (const band of ['orbital', 'state'] as const) {
      expect(cameraMarker({ tier: 'A', band, pinned: false }).show).toBe(false);
      expect(cameraMarker({ tier: 'A', band, pinned: true }).show).toBe(false);
    }
  });
  it('tier gates the bands: A from basin, B from river, C local only', () => {
    expect(cameraMarker({ tier: 'A', band: 'basin', pinned: false }).show).toBe(true);
    expect(cameraMarker({ tier: 'B', band: 'basin', pinned: false }).show).toBe(false);
    expect(cameraMarker({ tier: 'B', band: 'river', pinned: false }).show).toBe(true);
    expect(cameraMarker({ tier: 'C', band: 'river', pinned: false }).show).toBe(false);
    expect(cameraMarker({ tier: 'C', band: 'local', pinned: false }).show).toBe(true);
  });
  it('a pinned camera stays visible below state band regardless of tier', () => {
    expect(cameraMarker({ tier: 'C', band: 'basin', pinned: true }).show).toBe(true);
  });
  it('pinning grows the marker; nothing turns red anywhere', () => {
    const idle = cameraMarker({ tier: 'A', band: 'local', pinned: false });
    const pinned = cameraMarker({ tier: 'A', band: 'local', pinned: true });
    expect(pinned.sizePx).toBeGreaterThan(idle.sizePx);
    expect(pinned.alpha).toBeGreaterThanOrEqual(idle.alpha);
  });
});
