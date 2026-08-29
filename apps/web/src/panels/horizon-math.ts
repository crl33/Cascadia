/**
 * Pure datum logic for the HorizonStrip (production find 2026-08-29: five cells each
 * repeating "ft (NAVD88)" overlapped in the real panel — the stub fixture carries no
 * horizons, so only production could show it).
 *
 * When every quantity in the strip shares ONE datum, that datum is hoisted to the strip's
 * register line and the cells render bare; a mixed- or no-datum strip keeps full per-cell
 * labels so no value is ever separated from a datum that differs from its neighbours'.
 */
import type { Quantity } from '../contracts/schemas';

export function sharedDatum(quantities: readonly (Quantity | null | undefined)[]): string | null {
  const present = quantities.filter((q): q is Quantity => q != null);
  if (present.length === 0) return null;
  const datums = new Set(present.map((q) => q.datum ?? null));
  if (datums.size !== 1) return null;
  return [...datums][0];
}
