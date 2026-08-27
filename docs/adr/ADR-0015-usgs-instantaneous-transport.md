# ADR-0015 — One product for USGS instantaneous observations, across two transports

- **Status.** Accepted, 2026-08-27.
- **Context.** The live stage/flow path read legacy `waterservices.usgs.gov/nwis/iv/`, which USGS
  is decommissioning in Q1 2027 with degradation possible from August 2026. The successor is the
  Water Data OGC API `continuous` collection, already used by the Event Zero backfill.
- **Supersedes nothing.** Extends ADR-0010 (bitemporal honesty) and ADR-0009 (datum) rather than
  changing either.

## The decision

**One scientific product across both transports.** `product:usgs-iv` continues to identify USGS
instantaneous observations whether they arrived over NWIS IV or the OGC API. **Which transport
supplied a given row is answered per row**, by `observation.raw_artifact_id` →
`raw_artifact.request_url`, which already records the exact endpoint and the retrieval time.

## Why not a second product

Because the observation is the same measurement. This is not an assumption — it was measured
before cutover (`research/usgs-ogc-instantaneous-parity-2026-08-27.md`): over the same seven
gauges and the same windows, 814 of 814 semantic rows matched on station, variable, valid time,
value, unit, datum and quality, with **zero rows present on only one side**. The single difference
is that the OGC API spells an approval status `"Provisional"` where NWIS spelled it `"P"`.

A second product id would fragment one continuous observation series into two, break the freshness
anchor, and force every downstream read — `latest_observation`, the trend, the daily-mean
climatology, Event Zero replay — to know about a distinction that is not scientific. That is a
large cost for a difference the measurement says does not exist.

## Why the id still says "iv"

Renaming `product:usgs-iv` would orphan the `product_id` foreign key on every stored observation.
The id is **historical** and the registry label names the transport actually in use. The job was
renamed — `usgs.fetch_iv` → `usgs.fetch_instantaneous` — because a job name is operational rather
than referential, and the new one is transport-NEUTRAL so it does not become wrong again at the
next migration. Run history under the old name is not migrated; health reports `pending` (which
reads `unknown`, not `degraded`) until the first run.

## What a reader can determine, and how

| question | answered by |
|---|---|
| which API supplied this row | `raw_artifact.request_url` via `observation.raw_artifact_id` |
| when it was retrieved | `observation.retrieved_at` |
| the raw bytes | `raw_artifact.object_key` (content-addressed) |
| what instant it describes | `observation.valid_time` |
| when the platform could first have known it | `observation.available_at` (ADR-0010) |
| USGS status and quality | `observation.quality` (mapped) + `qualifier_raw` (verbatim) |
| which parser produced it | `qualifier_raw`: `"P"` is the NWIS vocabulary, `"Provisional"` the OGC one |

The last row is a consequence rather than a design, and it is worth stating: because
`qualifier_raw` is verbatim source text, a stored row says which vocabulary — and therefore which
parser — produced it, without joining anything.

## Consequences

- **Cutover writes no revisions.** `jobs.py` compares value and quality for idempotency and not
  `qualifier_raw`. Quality is identical across transports, so the first OGC poll skips every
  observation the legacy path had already stored. Asserted by
  `test_the_only_difference_is_how_the_source_spells_its_own_approval`.
- **No silent fallback, ever.** If the OGC API fails the job fails and `/system/health` says so.
  A transport that switches itself under failure makes both provenance and outage interpretation
  ambiguous. `jobs.py` does not import the legacy client; a test fails if that changes.
- **The archive costs more.** The OGC API is per-site and serves GeoJSON at ~752 B per
  observation where NWIS packed a series into one array. The live window was reduced 72 h → 3 h
  on that measurement: 72 h would have cost 106 GB/year against a 10 GB R2 free tier, and at a
  15-minute cadence it was 288× redundant anyway. Three hours still recovers twelve consecutive
  missed polls and costs 4.4 GB/year.
- **The legacy adapter survives as a comparator only**, marked RETIRED in its own docstring, so
  the parity test and `scripts/compare_usgs_iv_ogc.py` remain runnable.
- **`nwis/stat` is NOT covered by this decision.** The published day-of-year statistics
  cross-check (`stats_client.py`, `product:usgs-daily-stats`) still calls
  `waterservices.usgs.gov` and is a separate migration on the same deadline.
  **Done 2026-08-27 in ADR-0016**, which reached the OPPOSITE conclusion on product identity —
  and for the reason this ADR gives: one product was right here because parity was measured
  exact, and two are right there because it was measured absent.
