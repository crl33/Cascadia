# NWM long-term mirror verification — 2026-08-24

Companion to `nwm-alternate-archives-2026-08-24.json` (produced by
`scripts/verify_nwm_alternate_archives.py`, read-only anonymous listings + range-GETs).
Purpose: the owner parked the LEAN/FULL R2 bulk copy on condition that the Dec 1–22 2025
operational NWM products (incl. the medium-range ensemble) are independently retrievable from
long-term mirrors. **Condition met.**

## Verdict (FACT, verified 2026-08-24)

| Check | Result |
|---|---|
| GCS `gs://national-water-model` — all 22 days × 12 products, file counts + byte sums vs the AWS manifest | **22/22 days byte-exact, 0 real mismatches** |
| Azure `noaanwm.blob.core.windows.net/nwm` — sample days 20251201/20251212/20251222, same comparison | **3/3 days byte-exact, 0 mismatches** (18,224 files each) |
| Cross-cloud content (first KB, AWS vs GCS vs Azure) — mem2, mem6, analysis_assim, short_range objects | **identical on both mirrors** |
| `medium_range_mem7` | exists in NO archive (AWS, GCS, Azure): never produced. Operational NWM v3.x medium-range = **blend + mem1–mem6** |

## Tested retrieval paths

- **GCS** (JSON API listing + HTTPS objects, anonymous):
  `https://storage.googleapis.com/national-water-model/nwm.YYYYMMDD/<product>/<file>`
  listing: `https://storage.googleapis.com/storage/v1/b/national-water-model/o?prefix=…`
- **Azure** (container list + HTTPS objects, anonymous):
  `https://noaanwm.blob.core.windows.net/nwm/nwm.YYYYMMDD/<product>/<file>`
  listing: `…/nwm?restype=container&comp=list&prefix=…` (transient errors observed once;
  retry with backoff)
- AWS operational (`noaa-nwm-pds`) remains the manifest of record
  (`nwm-survival-inventory-2026-08-24.json`, original LastModified stamps).

## Consequences

1. **No bulk copy now** (owner decision 2026-08-24): no new Event Zero storage cost. The
   2.55 GB `usgs_timeslices` R2 archive is kept (DA input record + our `_manifest/` stamps).
2. Revisit when ensemble hindcasting is implemented: preferred end-state is an **extracted
   Cascadia/Washington analytical archive** (WA reaches only, ~0.4 % of CONUS channel bytes)
   built by streaming from GCS — not raw CONUS replication.
3. Residual risk: mirrors are operated by Google/Microsoft under NOAA open-data programs;
   none of the three archives carries a retention guarantee for this window. A quarterly
   canary re-running this script's day-sum comparison (cheap, read-only) detects erosion
   while the copy question is parked.
