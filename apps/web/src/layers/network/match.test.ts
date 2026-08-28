import { describe, expect, it } from 'vitest';
import type { RiverNetwork } from '../../contracts/schemas';
import { riverIntensities, riverIntensityKey } from './match';

const network: RiverNetwork = {
  _provenance: {},
  basins: {
    'basin:skagit': {
      rivers: [
        { name: 'Skagit River', length_deg: 3.2, mainstem: true, paths: [] },
        { name: 'Sauk River', length_deg: 1.4, mainstem: true, paths: [] },
        { name: '(unnamed)', length_deg: 0.1, mainstem: false, paths: [] },
      ],
    },
    'basin:green-duwamish': {
      rivers: [{ name: 'Green River', length_deg: 1.1, mainstem: true, paths: [] }],
    },
  },
};

describe('riverIntensities', () => {
  it('joins by the river name inside the station name, within the same basin', () => {
    const out = riverIntensities(network, [
      { basin_id: 'basin:skagit', name: 'Skagit River near Mount Vernon', flow_visual_intensity: 0.53 },
    ]);
    expect(out).toEqual({ [riverIntensityKey('basin:skagit', 'Skagit River')]: 0.53 });
  });
  it('a station naming no network river intensifies nothing; a null hint contributes nothing', () => {
    expect(riverIntensities(network, [
      { basin_id: 'basin:skagit', name: 'Baker River at Concrete', flow_visual_intensity: 0.9 },
      { basin_id: 'basin:skagit', name: 'Sauk River near Sauk', flow_visual_intensity: null },
    ])).toEqual({});
  });
  it('cross-basin names never leak: the Green stays cartographic on a Skagit station', () => {
    const out = riverIntensities(network, [
      { basin_id: 'basin:skagit', name: 'Green River lookalike gauge', flow_visual_intensity: 0.8 },
    ]);
    expect(out[riverIntensityKey('basin:green-duwamish', 'Green River')]).toBeUndefined();
  });
  it('two gauges on one river read as the busier reach — the max, erring toward visibility', () => {
    const out = riverIntensities(network, [
      { basin_id: 'basin:skagit', name: 'Skagit River near Concrete', flow_visual_intensity: 0.31 },
      { basin_id: 'basin:skagit', name: 'Skagit River near Mount Vernon', flow_visual_intensity: 0.74 },
    ]);
    expect(out[riverIntensityKey('basin:skagit', 'Skagit River')]).toBe(0.74);
  });
  it('unnamed fragments never match anything, whatever a station is called', () => {
    const out = riverIntensities(network, [
      { basin_id: 'basin:skagit', name: 'Somewhere (unnamed) station', flow_visual_intensity: 0.5 },
    ]);
    expect(Object.keys(out)).toEqual([]);
  });
});
