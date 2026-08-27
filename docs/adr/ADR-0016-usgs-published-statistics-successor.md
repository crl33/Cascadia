# ADR-0016 — A separate product for the published day-of-year cross-check

- **Status.** Accepted, 2026-08-27.
- **Context.** `nwis/stat` on `waterservices.usgs.gov` was Cascadia's last call to a service USGS
  decommissions in Q1 2027. It supplies the published day-of-year percentile ladder used to
  cross-check the Cascade-built climatology — a confidence input, never a value.
- **Completes ADR-0015**, which migrated the instantaneous path and explicitly deferred this one.

## The decision

**Migrate to the OGC statistics API's `observationNormals`, under a NEW source, product and
method id** — `src:usgs-wdfn-normals`, `product:usgs-doy-normals`,
`method:usgs-published-doy-stats@2.0.0`.

This is the opposite of ADR-0015's ruling on the same-looking question, on the same evidence
standard. There, one product spanned two transports because parity was measured exact:
1,754/1,754 semantic rows identical. Here parity was measured and found **absent**:

- p50 is exactly equal on **1,213 of 2,196** day pairs across the six susceptibility gauges.
- The rest differ by published precision or by **record membership**. At 12113000 the successor
  computes over **6–26 more years**; p50 differs by a median of 4.3 %, a maximum of 25.2 %, and
  crosses the 10 % cross-check threshold on **53 days**.
- The successor publishes **no period of record at all** — only `sample_count` — so the
  provenance ref carries `n<min>-<max>` and never a year span.

A shared id would have fused two genuinely different statistics into one series and let a ref
claim years its source never published. Two ids keep both true.

**The retired identifiers stay registered.** `product:usgs-daily-stats` and
`src:usgs-wdfn-statistics` remain in the registry with a RETIRED label and an entry in
`UNSCHEDULED_PRODUCTS`, so historical rows keep a valid `product_id` and resolve to the service
that actually produced them. `PRODUCT_WRITERS` is derived from `JOBS`, so removing the product
from the job spec is what drops it out of `/system/health` — no hand-maintained list to forget.

**No fallback.** A cross-check failure yields `no_published_cross_check`, the state the surface
already had. `stats_jobs.py` may not import or name the retired service, pinned by a test written
after a mutation proved nothing was stopping it.

## What this does not decide

- **The cross-check's meaning is unchanged and still overstated in one respect.** It is not
  independent evidence about the river: both sides derive from USGS daily values, so it tests how
  the ladder was CONSTRUCTED. The provenance label now says this. The threshold that lowers
  confidence when Cascadia's record is *longer* than the comparator's is a calibration question,
  deliberately left alone here.
- **Coverage regressed at 12200500**, which `nwis/stat` covered and the successor does not. No
  basin reads a climatology there — the Skagit's susceptibility gauge is the Sauk — so nothing is
  lost today. A future phase that gives Mount Vernon its own climatology must say it has no
  published cross-check rather than borrow one.
- **The legacy RDB parser is kept**, like the instantaneous comparator in ADR-0015, so archived
  artifacts and `@1.0.0` rows remain readable.

## Consequences

- Zero production call sites for `waterservices.usgs.gov`. Both hosts stay in the fetch ceiling
  for the ADR-0015 comparator alone, pinned by
  `test_no_production_module_calls_the_decommissioning_legacy_service`.
- `parameter_code=00060` is required on every request: unfiltered the response is 2.4–3.6 MB
  against ~415 KB filtered, for the same single number.
- Downstream bodies changed in exactly four provenance fields per gauge; no percentile, band,
  score, rank, seasonal multiple, velocity, driver value or confidence moved.

Evidence: [research/nwis-stat-successor-2026-08-27.md](../research/nwis-stat-successor-2026-08-27.md).
