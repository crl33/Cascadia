import { describe, expect, it } from 'vitest';
import { loadFixtures } from '../../dev/stub-load.mjs';
import { isErrorResult, route } from '../../dev/stub-router.mjs';

const fx = loadFixtures();

describe('stub router', () => {
  it('serves /basins and /system/health', () => {
    const basins = route(fx, '/basins', new URLSearchParams()) as { items: unknown[] };
    expect(isErrorResult(basins)).toBe(false);
    expect(basins.items).toHaveLength(6);
    const health = route(fx, '/system/health', new URLSearchParams()) as { status: string };
    expect(health.status).toBeDefined();
  });

  it('rejects unknown paths and bad lod', () => {
    const missing = route(fx, '/nope', new URLSearchParams());
    expect(isErrorResult(missing) && missing.status).toBe(404);
    const badLod = route(fx, '/basins/basin:skagit/geometry', new URLSearchParams('lod=orbit'));
    expect(isErrorResult(badLod) && badLod.status).toBe(400);
  });
});
