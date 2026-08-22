# ADR-0009: Units and datums policy

- Status: Accepted
- Date: 2026-08-22

## Context
Providers mix units (ft vs m, cfs vs kcfs vs m³/s, in vs mm, acre-ft) and vertical datums (NGVD29 vs NAVD88; gauge datum for stage). NWPS defines some thresholds in flow and some in stage (FACT, live 2026-08-22: Green/White in cfs). Comparing across datums or units silently is the classic failure.

## Decision
Store values in provider-native units with the unit recorded; the Variable registry defines a canonical SI unit; conversions use `pint` and produce DERIVED values with lineage. Stage series and thresholds record `vertical_datum`; the hazard function refuses stage comparisons with mismatched or missing datums and flow comparisons with mismatched units. Display follows official-threshold units (ft, cfs/kcfs) with SI alongside where useful; units are always printed.

## Evidence (retrieved 2026-08-22)
- NWPS lists 126 WA gauges with NGVD29 datums vs 61 with NAVD88, while USGS `monitoring-locations` now publishes NAVD88 altitudes; NGS NCAT/VERTCON 3.0 gives NAVD88 = NGVD29 + 1.07–1.20 m (3.50–3.93 ft) across Puget Sound gauges (FACT, `docs/research/static-geospatial-foundations.json`). Example: the MVEW1 gauge datum is 0 ft NGVD29 while USGS gives the site altitude as 3.8 ft NAVD88 — the same zero point, two datums. A datum-blind comparison is therefore wrong by ~3.5–3.9 ft, i.e. by more than the gap between NWS flood categories at several points.
- NWPS flow-defined categories (AUBW1/WRAW1) and kcfs observed/forecast flow units (FACT, `docs/research/v1-live-verification-2026-08-22.json`).

## Consequences
Slightly more storage and one conversion step; in exchange, V1-class mistakes (kcfs vs cfs, datum-blind comparisons) become type/constraint errors.
