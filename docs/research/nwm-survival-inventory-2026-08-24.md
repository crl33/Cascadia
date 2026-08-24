# NWM Event Zero survival inventory — 2026-08-24

Companion to `nwm-survival-inventory-2026-08-24.json` (the full per-day, per-product,
per-kind manifest with byte counts and LastModified ranges, produced by
`scripts/inventory_nwm_event_zero.py` via anonymous read-only S3 listing).

## 1. Findings (FACT, from the listing)

- **The entire Event Zero window survives on `noaa-nwm-pds`**: all 22 day directories
  `nwm.20251201/` … `nwm.20251222/`, 69 product families each, **1,210,264 files, 25.44 TB**.
  No missing days, no missing products.
- **These are the original operational uploads, not re-uploads**: LastModified stamps fall
  within ~45 minutes of each cycle time (e.g. `analysis_assim` 2025-12-01T00:45:49Z …
  2025-12-22T23:49:50Z; `short_range` first cycle written 01:46:59Z). The `available_at`
  values EVENT_ZERO.md §7 needs can therefore be taken from object stamps.
- The operational bucket's documented retention has plainly not been enforced for this
  window, but nothing guarantees that continues — the copy should happen soon.

## 2. What Event Zero actually needs (EVENT_ZERO.md §8 T6)

The 25 TB total is dominated by products irrelevant to a Washington hindcast (Alaska,
Hawaii, Puerto Rico, coastal Atlantic/Gulf domains, `long_range`, and the `forcing_*`
NetCDFs — forcing is reconstructed separately from MRMS/NBM/HRRR archives per T6).
Relevant: CONUS analysis states (channel + land + reservoir), forecast channel/reservoir
files, and `usgs_timeslices` (the DA input record, 2.6 GB — trivially worth keeping).

| Component (22 days) | Files | Size |
|---|---|---|
| `analysis_assim` CONUS, all kinds | 6,336 | 299.0 GB |
| `analysis_assim_extend` CONUS, all kinds | 2,464 | 118.6 GB |
| `short_range` channel_rt + reservoir | 19,008 | 125.5 GB |
| `medium_range` channel_rt + reservoir, blend + mem1–6 | 264,000 | 1,750.0 GB |
| `medium_range` channel_rt, blend + mem1 only | 42,240 | 554.6 GB |
| `usgs_timeslices` | 2,112 | 2.6 GB |

## 3. Copy tiers (decision needed — monthly cost is the owner's)

| Tier | Contents | Files | Size | R2 storage | One-time writes |
|---|---|---|---|---|---|
| **FULL** (recommended) | AnA + AnA-extend all kinds; SR + MR channel_rt/reservoir with **all 6 members (mem1–mem6) + blend**; timeslices | 293,920 | **2.30 TB** | **$34.43/mo** | ~$1.32 |
| LEAN | as FULL but medium_range blend + mem1 only | 72,160 | 1.10 TB | $16.50/mo | ~$0.32 |

Recommendation: **FULL**. The doctrine treats model disagreement as information
(`HYDROLOGY.md`); dropping members 2–6 permanently destroys the ensemble-spread signal the
hindcast is supposed to evaluate, for ~$18/mo of difference. LEAN is acceptable if cost
rules; nothing else in FULL is safely shrinkable.

Egress note: reading the archive back out of R2 is free (R2 has zero egress fees), and the
source bucket is AWS Open Data (NOAA pays egress), so the copy itself moves no paid bytes.

## 3c. DECISION 2026-08-24 (owner): bulk copy PARKED

No LEAN/FULL copy for now. Instead: independently verify the same Dec 1-22 products
(incl. medium_range mem2-7) remain retrievable from the long-term Google Cloud
(gs://national-water-model) and Azure (noaanwm.blob.core.windows.net/nwm) operational NWM
archives - **verified 2026-08-24: both mirrors byte-exact, retrieval paths tested** (see `nwm-alternate-archives-2026-08-24.md`). The 2.55 GB usgs_timeslices
archive in R2 is kept. Revisit LEAN/FULL/extracted-WA-archive when Event Zero ensemble
hindcasting is actually being implemented; the preferred end-state is an extracted
Cascadia/Washington-specific analytical archive, not raw CONUS replication.

## 4. Copy mechanics — revised 2026-08-24 after live checks

Constraints discovered:
- **Super Slurper is out**: dashboard-only and requires source credentials; it cannot read an
  anonymous public bucket like AWS Open Data (docs checked 2026-08-24).
- **Local relay is out**: measured throughput from this machine is ~1.5 MB/s down / 4.6 MB/s
  up - LEAN would take weeks and saturate the connection.
- **Budget doctrine (owner, 2026-08-24): stay mindful of free tiers.** R2 free tier is
  10 GB-month; both tiers exceed it by 100x+. Therefore NO bulk copy proceeds without an
  explicit owner cost approval naming a tier.

Viable mechanics when a tier is approved:
1. **Cloudflare Worker copy pump** (server-side, no egress anywhere): a Worker with an R2
   binding streams anonymous S3 GET -> R2 put, driven from the manifest key list. On the
   free Workers plan a cron-fed pump moves ~40 objects/min (subrequest cap) - LEAN in ~2-5
   days; the $5/mo paid plan with Queues does it in hours. 
2. Any VM relay pays provider egress (~$0.09/GB) and is a last resort.

Free-tier-compatible now (no approval needed, ~3 GB total): `usgs_timeslices` (2.6 GB, the
DA input record) - can be pumped within the free Workers plan and free R2 tier.

## 4b. Original copy-mechanics notes (superseded)

1. **R2 Super Slurper (recommended):** Cloudflare's server-side migration service pulls
   from public S3 buckets directly — no compute of ours, no local bandwidth. One job per
   prefix; ~130 prefixes (22 days × 6 product dirs) driven via API. Kind-level filtering
   (channel_rt vs land) needs the object-key manifest we already have; where Slurper can
   only take whole prefixes, slurp the prefix and delete the excluded kinds after, or fall
   back to (2) for mixed prefixes.
2. **Worker copy pump:** a queue-driven Cloudflare Worker streaming S3 GET → R2 put from
   the manifest key list. Fully filterable, ~294k messages, no egress cost, needs the $5
   Workers paid plan.
3. **VM relay (avoid):** any non-Cloudflare VM pays internet egress uploading to R2
   (≈$0.09/GB ⇒ ~$200 for FULL) unless run inside AWS us-east-1 with R2's S3 API — still
   pays AWS egress. Only sensible as a last resort.

Blocked on: R2 enablement on the Cloudflare account (API code 10042, 2026-08-24) and an
R2-scoped token; then the tier decision above.

## 5. Verification once copied

Per-object sha256 or ETag comparison against this manifest; store the manifest alongside
the archive (`_manifest/` prefix); record source `LastModified` as object metadata
(`x-amz-meta-source-last-modified`) so `available_at` survives the copy.

## 3b. Tier contents in detail (owner decision aid, 2026-08-24)

> Correction 2026-08-24: operational NWM v3.x medium_range comprises blend + mem1–mem6.
> `medium_range_mem7` exists in NO archive (AWS, GCS) for this window — it was never
> produced, not lost. Earlier '7 members' wording was a label error; all byte/file counts
> were computed from real listings and are unchanged.


Window for every line: nwm.20251201 – nwm.20251222 (22 days, all cycles present).

| Component | Config / cycles | In LEAN | In FULL | Files | Size |
|---|---|---|---|---|---|
| analysis_assim (channel_rt+land+reservoir+terrain, tm00-02) | hourly, 24/day | yes | yes | 6,336 | 299 GB |
| analysis_assim_extend (same kinds, tm00-27) | daily 16Z | yes | yes | 2,464 | 119 GB |
| short_range channel_rt + reservoir (18-h leads) | hourly, 24/day | yes | yes | 19,008 | 126 GB |
| usgs_timeslices (DA input record) | continuous | already copied | already copied | 2,112 | 2.6 GB |
| medium_range channel_rt: blend + mem1 (240-h leads) | 4/day (00/06/12/18Z) | yes | yes | 42,240 | 555 GB |
| medium_range reservoir: blend + mem1 | 4/day | yes | yes | 42,240 | 5.5 GB |
| medium_range channel_rt: mem2–mem6 (204-h leads) | 4/day | no | yes | 89,760 | 1,178 GB |
| medium_range reservoir: mem2–mem6 | 4/day | no | yes | 89,760 | 11.6 GB |
| **LEAN total** | | | | **112,288** | **1.11 TB ($16.6/mo)** |
| **FULL total** | | | | **291,808** | **2.30 TB ($34.4/mo)** |

LEAN enables: full AnA reconstruction (streamflow analysis + land states incl. soil/SWE at
every WA reach), the deterministic operational forecast record (blend = the official NBM-forced
best blend; mem1 = GFS-forced control), per-reach hindcast hydrographs, NWM-vs-NWRFC forecast
evolution and error analysis, reservoir module outputs for regulated reaches, and the DA input
record. LEAN cannot reconstruct: ensemble spread. FULL adds the five additional GEFS-forced members (mem2–mem6) —
member agreement/disagreement per reach per cycle, hindcastable exceedance fractions, and
spread-vs-error calibration (e.g. whether the Dec 9–10 Skagit over-forecast was flagged by
member divergence). The Model Agreement risk surface's NWM component can only ever be
hindcast against Event Zero with FULL; deleting mem2–7 from the source bucket is permanent.
