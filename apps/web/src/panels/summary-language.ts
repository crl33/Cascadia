/**
 * summary-language: contract values → the sentences a first-time reader understands
 * (mission §16–17). Pure and total; every sentence is derived from the document, never
 * invented. UNKNOWN keeps its own words — a missing value must never read as calm.
 *
 * The forensic numbers do not disappear: they move one fold deeper (WHY) and into each
 * line's hover title; this module only decides the 5-second read.
 */
import type { BasinVisualizationState } from '../contracts/schemas';

type Surfaces = BasinVisualizationState['surfaces'];
type Level = NonNullable<BasinVisualizationState['hydrologic_state']>;
type Change = NonNullable<BasinVisualizationState['state_change']>[number];

const SUSCEPTIBILITY_PHRASE: Record<string, string> = {
  low: 'Low flood susceptibility',
  moderate: 'Moderate flood susceptibility',
  high: 'High flood susceptibility',
  very_high: 'Very high flood susceptibility',
  unknown: 'Flood susceptibility unknown',
};

export function susceptibilityHeadline(state: Surfaces['susceptibility']['state']): string {
  return SUSCEPTIBILITY_PHRASE[state] ?? SUSCEPTIBILITY_PHRASE.unknown;
}

/** "River steady · well below seasonal high flows" — the CURRENT sentence. */
export function currentSentence(level: Level | null, change24: Change | null): string | null {
  const parts: string[] = [];
  if (change24) {
    const verb = change24.direction === 'rising' ? 'rising' : change24.direction === 'falling' ? 'falling' : 'steady';
    parts.push(`River ${verb}`);
  }
  const multiple = level?.multiple?.multiple;
  if (typeof multiple === 'number') {
    const vs =
      multiple < 0.5 ? 'well below seasonal high flows'
      : multiple < 0.9 ? 'below seasonal high flows'
      : multiple <= 1.1 ? 'near seasonal high flows'
      : 'above seasonal high flows';
    parts.push(vs);
  }
  if (parts.length === 0) return null;
  return parts.join(' · ');
}

/** "Little rain expected — 11.6 mm over 72 h" — the NEXT sentence, from the forcing surface. */
export function forcingSentence(forcing: Surfaces['forcing']): string {
  const amount = forcing.value ? `${forcing.value.value.toFixed(1)} ${forcing.value.unit}` : null;
  const window = `${forcing.horizon_h ?? 72} h`;
  switch (forcing.state) {
    case 'low':
      return amount ? `Little rain expected — ${amount} over ${window}` : `Little rain expected over ${window}`;
    case 'moderate':
      return amount ? `Moderate rain expected — ${amount} over ${window}` : `Moderate rain expected over ${window}`;
    case 'high':
    case 'very_high':
      return amount ? `Heavy rain expected — ${amount} over ${window}` : `Heavy rain expected over ${window}`;
    default:
      return forcing.reason ?? 'Rain outlook unknown';
  }
}

/** "No flood stages forecast" / "MINOR flooding forecast" — the official outlook sentence. */
export function hazardSentence(hazard: Surfaces['hazard']): string {
  switch (hazard.official_category) {
    case 'none':
      return 'No flood stages forecast';
    case 'unknown':
      return hazard.reason ?? 'Official outlook unknown';
    default:
      return `${hazard.official_category.charAt(0).toUpperCase()}${hazard.official_category.slice(1)} flooding forecast`;
  }
}
