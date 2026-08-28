# ADR-0010: Every value carries knowledge time (`available_at`); replay uses it exclusively

- Status: Accepted (amended by ADR-0018: backfilled `available_at` is the RETRIEVAL instant;
  the provider's publication time lives on the separate `knowable_at` clock)
- Date: 2026-08-22

## Context
Hindcasting must avoid look-ahead bias: at clock T the system may use only what was retrievable by T, and only the revision that existed at T. Providers republish (provisional→approved; re-gridded QPE; superseding forecast runs).

## Decision
All value tables carry `valid_time`, `issued_at` (nullable), `retrieved_at`, and `available_at = max(issued_at or valid_time, retrieved_at)`; revisions are rows linked by `revision_of`; forecast runs link `supersedes_run_id`. A single helper `as_known_at(T)` is the only permitted replay access path; API read endpoints accept `as_of`. Before the platform has its own retrieval history (backfill), `available_at` for backfilled data is set to the provider's publication time when known and otherwise flagged `backfilled=true` so hindcasts can report the approximation.

## Consequences
Honest replays and forecast-evolution views come for free from the write model. Backfilled history is explicitly second-class for hindcast purposes — a known limitation, documented per product.
