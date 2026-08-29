import { describe, expect, it } from 'vitest';
import { cameraMarker } from './style';

describe('cameraMarker', () => {
  it('cameras are invisible from orbit and state — local evidence, not orientation', () => {
    for (const band of ['orbital', 'state'] as const) {
      expect(cameraMarker({ tier: 'A', band, pinned: false, attention: false }).show).toBe(false);
      expect(cameraMarker({ tier: 'A', band, pinned: true, attention: false }).show).toBe(false);
    }
  });
  it('tier gates the bands: A and B from basin (the network must read as one), C local only', () => {
    expect(cameraMarker({ tier: 'A', band: 'basin', pinned: false, attention: false }).show).toBe(true);
    expect(cameraMarker({ tier: 'B', band: 'basin', pinned: false, attention: false }).show).toBe(true);
    expect(cameraMarker({ tier: 'B', band: 'river', pinned: false, attention: false }).show).toBe(true);
    expect(cameraMarker({ tier: 'C', band: 'river', pinned: false, attention: false }).show).toBe(false);
    expect(cameraMarker({ tier: 'C', band: 'local', pinned: false, attention: false }).show).toBe(true);
  });
  it('a pinned camera stays visible below state band regardless of tier', () => {
    expect(cameraMarker({ tier: 'C', band: 'basin', pinned: true, attention: false }).show).toBe(true);
  });
  it('pinning grows the marker; nothing turns red anywhere', () => {
    const idle = cameraMarker({ tier: 'A', band: 'local', pinned: false, attention: false });
    const pinned = cameraMarker({ tier: 'A', band: 'local', pinned: true, attention: false });
    expect(pinned.sizePx).toBeGreaterThan(idle.sizePx);
    expect(pinned.alpha).toBeGreaterThanOrEqual(idle.alpha);
  });
});


describe('official attention', () => {
  it('promotes the corridor one band and rings the glyph — official evidence only', () => {
    const idle = cameraMarker({ tier: 'C', band: 'river', pinned: false, attention: false });
    const noticed = cameraMarker({ tier: 'C', band: 'river', pinned: false, attention: true });
    expect(idle.show).toBe(false);
    expect(noticed.show).toBe(true);
    expect(noticed.ring).toBe(true);
    expect(noticed.sizePx).toBeGreaterThan(cameraMarker({ tier: 'A', band: 'river', pinned: false, attention: false }).sizePx);
  });
  it('attention never reaches orbital or state — cameras stay local evidence', () => {
    expect(cameraMarker({ tier: 'A', band: 'state', pinned: false, attention: true }).show).toBe(false);
  });
});
