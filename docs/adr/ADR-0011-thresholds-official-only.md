# ADR-0011: Only official thresholds participate in category and hazard computation

- Status: Accepted
- Date: 2026-08-22

## Context
All four of V1's configured fallback thresholds were wrong versus NWPS (FACT, `docs/V1_AUDIT.md` §4.2). V1's gate prevented their use — the gate worked; the existence of the values was the risk.

## Decision
Thresholds used for any category, headroom or hazard computation must have `source_kind=OFFICIAL_FORECAST` (NWPS). CONFIGURED thresholds may exist only as explicitly badged display metadata (e.g. a county "Phase" level with its source) and are rejected by the hazard function's type signature. If official thresholds are unavailable for a point, the category is UNKNOWN with the reason; the platform does not invent values. NWPS thresholds are re-fetched on a schedule and versioned.

## Consequences
Some points may be UNKNOWN for category; the platform still shows observations, percentiles and official forecasts for them. Honesty over coverage.
