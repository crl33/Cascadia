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
