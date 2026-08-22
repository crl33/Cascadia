/**
 * Semantic altitude bands and their boundaries — the only file that knows a band's height.
 * The doc boundaries (SEMANTIC_ZOOM.md §1: 100/30/5/1 km) are ASSUMPTIONs tuned for HUC8-scale
 * views; the spike frames whole seed basins (Skagit ≈ 150 km across ⇒ ~300 km effective height),
 * so the tops are retuned here: state 900 km, basin 450 km, river 90 km, local 8 km. Hysteresis ±12 %.
 */
export const BANDS = ['orbital', 'state', 'basin', 'river', 'local'] as const;
export type Band = (typeof BANDS)[number];
/** The band value the SceneSummary API accepts (local collapses into river in the spike). */
export type DataBand = Exclude<Band, 'local'>;

export interface BandConfig {
  /** Tops of state, basin, river, local (metres of effective height). */
  boundaries: readonly [number, number, number, number];
  hysteresis: number;
}

export const BAND_CONFIG: BandConfig = { boundaries: [900_000, 450_000, 90_000, 8_000], hysteresis: 0.12 };
