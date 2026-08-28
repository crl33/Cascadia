/**
 * Basin susceptibility fill: pure, total mapping from a Cascade-derived surface state to
 * presentation. No renderer calls, no hydrology.
 *
 * This is the first Cascade-DERIVED thing the globe itself says, and VISUAL_TRUTH_DOCTRINE puts
 * three hard limits on it that the tests beside this file enforce one by one:
 *
 * 1. **Never the red family.** §7.1: "Red is earned, not assumed. Justified only by class A or B
 *    evidence ... C-class values — and EXPERIMENTAL above all — never reach the red family." A
 *    `very_high` susceptibility is still an uncalibrated index; it may reach amber, which §7.1
 *    explicitly assigns to "elevated susceptibility/forcing states", and it stops there. An
 *    official `major` category on the same basin is red. The two must never collide.
 * 2. **A non-colour carrier is mandatory.** §7.2: "Scientific meaning is never encoded solely
 *    through hue or saturation ... a greyscale screenshot still distinguishes observed / official
 *    / modeled / derived / experimental." The stripe is that carrier, and it is on whenever the
 *    surface is experimental — not only when the value is high.
 * 3. **UNKNOWN is neutral and incomplete, never calm.** §"unknown / missing": "neutral,
 *    incomplete-looking (hatched/outlined, no fill saturation); reason text; never calm, green or
 *    zero." A basin with no susceptibility must not read as a safe basin.
 *
 * The fill is also deliberately a SEPARATE layer from `basins`, which is `cartographic`. Tinting
 * the cartographic outline layer by a derived value would blur two registers into one element,
 * which §"Rules that apply across registers" forbids outright.
 */
import { COLOR, type Hsl } from '../../design-system/tokens';
import type { ConfidenceLabel, SurfaceLevel } from '../../contracts/schemas';
import type { Band } from '../../scene/bands';

export interface SusceptibilitySemantic {
  /** The band the surface reports. `unknown` means the backend refused, and says why. */
  state: SurfaceLevel;
  /** `true` for every Cascade-derived susceptibility today. Kept as an input rather than assumed. */
  experimental: boolean;
  confidence: ConfidenceLabel;
  band: Band;
  selected: boolean;
  /** The backend's own reason when there is no value. Rendered, never invented here. */
  reason: string | null;
}

export interface SusceptibilityFill {
  show: boolean;
  color: Hsl;
  /** The restrained transparent WASH under the carrier — deliberately faint: the index must
   *  contextualise the geography, never obscure the towns, rivers and terrain it sits over. */
  alpha: number;
  /** The mandatory non-colour carrier (§7.2). On for every experimental fill. */
  striped: boolean;
  /** The carrier's own opacity: a fine hatch slightly stronger than the wash, so a greyscale
   *  screenshot still separates experimental from official — without the carrier becoming the
   *  loudest thing on screen (design direction 2026-08-28: the old broad vertical bands read
   *  as a debugging mask). */
  hatchAlpha: number;
  /** Outline-only, no saturated fill — the UNKNOWN treatment. */
  outlineOnly: boolean;
  /** Printed on the label. Never null while `experimental` is true. */
  badge: 'EXPERIMENTAL' | null;
  labelText: string;
}

/** One hatch line about every this-many degrees of basin extent (~3 km here): fine enough to
 *  read as texture rather than banding on every seed basin, from the Cedar to the Skagit. */
export const HATCH_SPACING_DEG = 0.04;
/** The carrier's opacity — above every wash alpha (the greyscale separation lives here). */
export const HATCH_ALPHA = 0.30;

/**
 * Level → tone. Cyan for nominal, amber as tension rises, and nothing beyond amber.
 *
 * `very_high` sharing `amberElevated` with `high` is the point, not an oversight: the palette
 * runs out deliberately before red, because the next tone up is reserved for evidence this
 * surface does not have. The stripe and the printed level word carry the distinction instead.
 */
const LEVEL_TONE: Record<SurfaceLevel, Hsl> = {
  low: COLOR.cyan,
  moderate: COLOR.amberWatch,
  // `high` and `very_high` share a tone on purpose: the palette runs out deliberately before red,
  // because the next tone up is reserved for evidence this surface does not have.
  high: COLOR.amberElevated,
  very_high: COLOR.amberElevated,
  unknown: COLOR.neutralUnknown,
};

const LEVEL_WORD: Record<SurfaceLevel, string> = {
  low: 'low',
  moderate: 'moderate',
  high: 'high',
  very_high: 'very high',
  unknown: 'unknown',
};

/** Lower confidence reads fainter — it never changes the tone, which would restate the level.
 *  Halved 2026-08-28: the wash is context under a fine hatch now, not the statement itself. */
const CONFIDENCE_ALPHA: Record<ConfidenceLabel, number> = {
  high: 0.15,
  moderate: 0.12,
  low: 0.09,
  unknown: 0.07,
};

export function susceptibilityFill(s: SusceptibilitySemantic): SusceptibilityFill {
  const badge = s.experimental ? ('EXPERIMENTAL' as const) : null;
  const suffix = s.experimental ? ' · EXPERIMENTAL index, not a probability' : '';

  // Only the overview bands carry a basin-wide wash. Closer in, the basin fill would sit under
  // the reaches and gauges it is meant to contextualise and compete with them for the same pixels.
  const overview = s.band === 'orbital' || s.band === 'state' || s.band === 'basin';

  if (s.state === 'unknown') {
    return {
      show: overview || s.selected,
      color: COLOR.neutralUnknown,
      alpha: 0,           // no saturation: an unknown basin must not look like a calm one
      striped: false,
      hatchAlpha: 0,
      outlineOnly: true,  // incomplete-looking, per the unknown register
      badge,
      labelText: `Susceptibility unknown${s.reason ? ` — ${s.reason}` : ''}${suffix}`,
    };
  }

  const alpha = CONFIDENCE_ALPHA[s.confidence] * (s.selected ? 1.25 : 1);
  return {
    show: overview,
    color: LEVEL_TONE[s.state],
    alpha: Math.min(alpha, 0.20),
    striped: s.experimental,
    hatchAlpha: s.experimental ? HATCH_ALPHA : 0,
    outlineOnly: false,
    badge,
    labelText: `Susceptibility ${LEVEL_WORD[s.state]} · confidence ${s.confidence}${suffix}`,
  };
}
