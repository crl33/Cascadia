/**
 * Display formatting only: quantities with unit + datum, ISO instants as UTC, ages and
 * cadences. Nothing here computes a hydrologic quantity or a freshness state — those arrive in
 * the contract.
 */
import type { Freshness, Quantity } from '../contracts/schemas';

export const formatQuantity = (q: Quantity | null | undefined, digits = 2): string => {
  if (!q) return 'UNKNOWN';
  const value = Number.isInteger(q.value) ? q.value.toLocaleString('en-US') : q.value.toFixed(digits);
  return q.datum ? `${value} ${q.unit} (${q.datum})` : `${value} ${q.unit}`;
};

/** Value + unit WITHOUT the datum — for dense rows whose shared datum is stated once nearby.
 * Never use where the datum is not visibly carried by the surrounding context. */
export const formatQuantityBare = (q: Quantity | null | undefined, digits = 2): string => {
  if (!q) return 'UNKNOWN';
  const value = Number.isInteger(q.value) ? q.value.toLocaleString('en-US') : q.value.toFixed(digits);
  return `${value} ${q.unit}`;
};

export const formatNumber = (n: number | null | undefined, digits = 1): string =>
  n == null ? '—' : Number.isInteger(n) ? n.toLocaleString('en-US') : n.toFixed(digits);

export const formatUtc = (iso: string | null | undefined): string => {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${d.toISOString().slice(0, 16).replace('T', ' ')} UTC`;
};

export const formatAge = (seconds: number | null | undefined): string => {
  if (seconds == null) return 'unknown';
  if (seconds < 90) return `${seconds} s`;
  if (seconds < 5400) return `${Math.round(seconds / 60)} min`;
  if (seconds < 172800) return `${(seconds / 3600).toFixed(1)} h`;
  return `${(seconds / 86400).toFixed(1)} d`;
};

export const formatFreshness = (f: Freshness): string => {
  const parts = [`age ${formatAge(f.age_seconds)}`];
  if (f.expected_cadence_seconds != null) parts.push(`cadence ${formatAge(f.expected_cadence_seconds)}`);
  return parts.join(' · ');
};

export const words = (s: string | null | undefined): string => (s ?? 'unknown').replace(/_/g, ' ');

/**
 * `2.0997` → `2.10×`. Two decimals because a growth of 1.37 and one of 1.38 are different
 * statements at this scale, and a third decimal is precision the daily mean does not carry.
 */
export const formatMultiplier = (n: number): string => `${n.toFixed(2)}×`;

/**
 * `2651` → `2,651st`. An ORDINAL, because that is what a rank is — deliberately not converted
 * to a percentile or a percentage. "the 2,651st largest of 34,957" states its own denominator;
 * "top 7.6 %" would advertise a resolution the count does not have and would invite comparison
 * with the day-of-year percentile, which is a different quantity against a different sample.
 */
export const formatOrdinal = (n: number): string => {
  const abs = Math.abs(n);
  const lastTwo = abs % 100;
  const last = abs % 10;
  const suffix = lastTwo >= 11 && lastTwo <= 13 ? 'th' : last === 1 ? 'st' : last === 2 ? 'nd' : last === 3 ? 'rd' : 'th';
  return `${n.toLocaleString('en-US')}${suffix}`;
};

/** `34957` → `34,957`. Grouped for reading; never rounded — a sample size is a count. */
export const formatCount = (n: number): string => n.toLocaleString('en-US');
