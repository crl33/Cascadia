/**
 * SemanticZoomController: the only module that converts camera geometry into meaning. Pure band
 * derivation with multiplicative hysteresis (exported for tests) plus a tiny class that takes
 * throttled CameraSamples and emits `bandChanged` only when the band actually changes. Holds no
 * renderer types.
 */
import { BANDS, BAND_CONFIG, type Band, type BandConfig } from './bands';

export interface CameraSample {
  heightAboveTerrainM: number;
  approximate: boolean;        // true while the height is ellipsoid-based
  pitchDeg: number;            // −90 straight down … 0 horizon
  settled: boolean;
}

export interface BandChanged { prev: Band; next: Band; cause: 'descend' | 'ascend' | 'jump'; effectiveHeightM: number }

const SIN_PITCH_MIN = 0.34;

/** Pitch widens the view: effectiveHeight = h / clamp(sin|pitch|, 0.34, 1). */
export const effectiveHeight = (heightM: number, pitchDeg: number): number =>
  heightM / Math.min(1, Math.max(SIN_PITCH_MIN, Math.sin((Math.abs(pitchDeg) * Math.PI) / 180)));

const index = (band: Band) => BANDS.indexOf(band);
/** Top of `band` (the boundary above it); orbital has none. */
const boundaryAbove = (band: Band, cfg: BandConfig): number => cfg.boundaries[index(band) - 1] ?? Number.POSITIVE_INFINITY;
/** Bottom of `band` (the boundary below it); local has none. */
const boundaryBelow = (band: Band, cfg: BandConfig): number => cfg.boundaries[index(band)] ?? 0;

export function deriveBand(prev: Band, effectiveHeightM: number, cfg: BandConfig = BAND_CONFIG): Band {
  let band = prev;
  while (band !== 'local' && effectiveHeightM < boundaryBelow(band, cfg) * (1 - cfg.hysteresis)) band = BANDS[index(band) + 1]!;
  while (band !== 'orbital' && effectiveHeightM > boundaryAbove(band, cfg) * (1 + cfg.hysteresis)) band = BANDS[index(band) - 1]!;
  return band;
}

type Handler = (event: BandChanged) => void;

export class SemanticZoomController {
  private current: Band;
  private readonly handlers = new Set<Handler>();

  constructor(private readonly cfg: BandConfig = BAND_CONFIG, initial: Band = 'orbital') {
    this.current = initial;
  }

  get band(): Band { return this.current; }

  onCameraSample(sample: CameraSample): void {
    const effective = effectiveHeight(sample.heightAboveTerrainM, sample.pitchDeg);
    const next = deriveBand(this.current, effective, this.cfg);
    if (next === this.current) return;
    const distance = Math.abs(index(next) - index(this.current));
    const cause: BandChanged['cause'] = distance > 1 ? 'jump' : index(next) > index(this.current) ? 'descend' : 'ascend';
    const event: BandChanged = { prev: this.current, next, cause, effectiveHeightM: effective };
    this.current = next;
    this.handlers.forEach((h) => h(event));
  }

  on(_event: 'bandChanged', handler: Handler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }
}
