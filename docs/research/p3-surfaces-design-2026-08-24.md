# P3 — LIVE INTELLIGENCE SURFACES v0: design and verified data paths (2026-08-24)

Read-only scouting report and build design for ROADMAP Phase 3 / NEXT_STEPS **P3**: replace the
three UNKNOWN basin surfaces (`susceptibility`, `forcing`, `agreement`) with honest computed
values that carry provenance, are badged EXPERIMENTAL where derived, and stay UNKNOWN with a
reason where inputs are genuinely missing.

Every external claim below is labeled **FACT** (fetched by this session on 2026-08-24, URL
given), **ASSUMPTION**, **INFERENCE**, or **OPEN QUESTION**, per `docs/DATA_SOURCES.md`
conventions. Nothing in the repository was modified except this file.

Binding owner constraint honored throughout: *no recurring infrastructure cost unless required
for functionality actively being built.* Every surface below is costed in bytes/day, R2
growth/month, Neon row growth/month and worker CPU. §8 is the roll-up.

---

## 0. Verdict in one page

| Surface | Verdict | Chosen path | Recurring cost |
|---|---|---|---|
| **Forcing v0** | **BUILDABLE, cheap** | NBM v5.0 `qmd` APCP percentiles + `core` SNOWLVL percentiles, spatially subset **server-side** by NOMADS `filter_blend.pl` to a WA-basin box, decoded with `eccodes`, area-weighted over full-resolution basin polygons | **9.4 MB/day** ingest → ~285 MB/month R2, ~4 MB/month Neon, ~16 s CPU/day |
| **Susceptibility v0** | **BUILDABLE, near-free, but narrow** | Outlet (and unregulated-proxy) **streamflow day-of-year percentile** against a Cascade-built climatology from USGS OGC `daily`, cross-checked against the USGS statistics table; SNOTEL SWE + antecedent precipitation carried as **unscored context drivers** | **~25 KB/day** → ~0.8 MB/month R2, ~0.2 MB/month Neon, <1 s CPU/day |
| **Agreement v0** | **BUILDABLE at 5 of 6 points** | NWM v3.1 medium-range **ensemble as JSON from the NWPS `/reaches/{id}/streamflow` API** vs the NWRFC official run, compared on **flow** | **3.8 MB/day** → ~114 MB/month R2, ~10 MB/month Neon, negligible CPU |

Three findings drove the design and each saves an order of magnitude:

1. **NOMADS `filter_blend.pl` server-side subsetting beats GRIB2 byte-range subsetting** for this
   use case. Byte-range subsetting *does* work (verified, §1.2) but a GRIB2 record is spatially
   monolithic, so one CONUS QPF percentile record costs 1.4–4.3 MB. The NOMADS CGI returns the
   same records clipped to a 99×142 WA box at **~2–6.5 KB per record** — a 1/600 reduction
   against the whole file and ~1/20 against byte-ranged whole records.
2. **The NWM ensemble is already served as JSON per reach** by NWPS
   (`/reaches/{reachId}/streamflow?series=medium_range`, 157 KB, mean + 6 members × 240 hours).
   No CONUS NetCDF, no Zarr/kerchunk, no per-reach index build is needed for agreement v0.
3. **USGS OGC `daily` returns a station's entire daily-mean record in one request**
   (31,373 rows / 903 KB / 1.5 s for the Skagit). The platform can build its own day-of-year
   percentile climatology, exactly as `DATA_DOCTRINE.md` §8 requires, and is therefore immune to
   the Q1-2027 WaterServices decommission.

And one hard limit that must be stated in the product, not hidden: **v0 makes no soil claim.**
SNOTEL SMS is the only mountain soil observation available and it does not survive inspection
(§2.2). Soil stays UNKNOWN with a reason until SMAP L4 or NWM land lands.

---

## 1. FORCING v0 — basin-scale precipitation forcing

### 1.1 What was verified live

All fetched 2026-08-24, User-Agent `CascadiaPapsukkal/0.1 (+https://cascadia.papsukkal.com)`.

**FACT — the NBM v5.0 archive is live and structured as `DATA_SOURCES.md` W2 says.**
`https://noaa-nbm-grib2-pds.s3.amazonaws.com/?list-type=2&delimiter=/&prefix=blend.20260824/12/`
lists `core/`, `qmd/`, `text/` for the 12Z cycle; the 18Z cycle (fetched at ~20:00Z) had only
`core/` and `text/` — i.e. **`qmd` exists only for the 00/06/12/18Z cycles and lands hours
later**, exactly as documented.

**FACT — cycle latency, measured from S3 `Last-Modified` at 21:18:55Z:**

| Object | Last-Modified | Latency after cycle | Size (CONUS) |
|---|---|---|---|
| `blend.20260824/12/qmd/blend.t12z.qmd.f024.co.grib2` | 19:15:35Z | **+7 h 16 m** | 623,837,557 B |
| `blend.20260824/12/qmd/blend.t12z.qmd.f072.co.grib2` | 19:19:49Z | **+7 h 20 m** | 785,216,268 B |
| `blend.20260824/18/core/blend.t18z.core.f024.co.grib2` | 18:44:44Z | **+44 m** | 191,890,621 B |
| `blend.20260824/20/core/blend.t20z.core.f024.co.grib2` | 20:42:06Z | **+42 m** | 163,811,514 B |

This confirms `product:nbm-v5-qmd` · cadence PT6H · grace PT8H and `product:nbm-v5-core` ·
PT1H · PT1H are the right freshness declarations. It also means **the QPF percentile field a
user sees can legitimately be 7–13 h old**; the freshness badge must show that, and the design
does not paper over it (§1.4).

**FACT — QPF percentiles and their accumulation windows.** From the `.idx` sidecars
(`…/blend.20260824/12/qmd/blend.t12z.qmd.f0{24,48,72}.co.grib2.idx`, 24,176 / 26,499 / 28,820 B):

| File | APCP accumulation windows present |
|---|---|
| `qmd.f024` | `23-24 hour`, `18-24 hour`, `12-24 hour`, **`0-1 day`** |
| `qmd.f048` | `47-48`, `42-48`, `36-48`, `1-2 day`, **`0-2 day`** |
| `qmd.f072` | `71-72`, `66-72`, `60-72`, `2-3 day`, `1-3 day`, **`0-3 day`** |

Each window carries **percentile levels 0 % → 100 % in 5 % steps (21 fields)**, a bare
deterministic field, and exceedance probabilities (`prob >0.254` … `>203.2` mm). The
`0-N day` cumulative fields are what the 24/48/72-h horizons need: **one file per horizon, not
one file per forecast hour.**

**FACT — SNOWLVL lives in `core`, with 15 percentiles, and needs no `qmd` fetch.**
`…/blend.20260824/18/core/blend.t18z.core.f024.co.grib2.idx` (16,731 B, 211 records) contains
`SNOWLVL:surface` at percentile levels 1, 5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99
plus `SNOWLVL:0 m above mean sea level` (the deterministic field; that string is the GRIB fixed-
surface descriptor, not a unit). `core` APCP is deterministic 1-h and 6-h plus `prob >0.254`
only — **no QPF percentiles in `core`**, which is why the percentile spread must come from
`qmd` and inherits its 7-hour latency.

### 1.2 Byte-range subsetting: established as FACT, then deliberately not used

The task asked for this to be settled either way. It is settled: **it works.**

```
GET https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20260824/18/core/blend.t18z.core.f024.co.grib2
Range: bytes=97709842-98855676          # record 97 from the .idx: APCP:surface:23-24 hour acc fcst
→ HTTP 206, 1,145,835 bytes
```

Verified by parsing the returned bytes (FACT):

- magic `47 52 49 42` = `GRIB`, trailer `37 37 37 37` = `7777`;
- Section 0 total-length field = 1,145,835 = the exact number of bytes returned;
- Section 3: grid template **30** (Lambert conformal), nx 2345 × ny 1597 = **3,744,965 points**,
  la1 19.229 N, lo1 233.7234 E, dx = dy = 2,539.703 m — the documented NBM CONUS grid;
- Section 4: product template 8, category 1, number 8 (= APCP);
- Section 5: DRS template **3** (complex packing with spatial differencing), 3,744,965 points;
- Sections 6 and 7 present and self-consistent.

So `.idx` + ranged GET is a **valid, working backfill and fallback path** and should be built as
such. It is *not* the primary path because GRIB2 records are spatially monolithic — a ranged GET
gets you a whole-CONUS field or nothing. Measured cost of the twelve records forcing v0 would
need (deterministic + p10 + p50 + p90, for the `0-1`/`0-2`/`0-3 day` windows), computed from
`.idx` offsets:

| Window | p10 | p50 | p90 | deterministic | subtotal |
|---|---|---|---|---|---|
| `0-1 day` (f024) | 1.401 MB | 2.180 MB | 3.548 MB | 2.874 MB | **10.00 MB** |
| `0-2 day` (f048) | 1.751 MB | 2.779 MB | 4.203 MB | 3.347 MB | **12.08 MB** |
| `0-3 day` (f072) | 2.107 MB | 3.153 MB | 4.292 MB | 3.522 MB | **13.07 MB** |
| | | | | **total/cycle** | **35.2 MB** |

35.2 MB/cycle × 4 = **141 MB/day = 4.2 GB/month**. That is the "quietly adds tens of GB" design
the brief warns about. Rejected as the primary path.

### 1.3 The chosen path — NOMADS server-side lat/lon subsetting

**FACT — `filter_blend.pl` (NCEP `g2subset`) is live, works, and clips spatially.**
Verified request shape (`%2F` encoding of the `dir` is required):

```
https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl
  ?dir=%2Fblend.20260824%2F12%2Fqmd
  &file=blend.t12z.qmd.f072.co.grib2
  &var_APCP=on
  &subregion=&toplat=49.40&leftlon=-122.90&rightlon=-120.55&bottomlat=46.70
```

**FACT — measured returns for the six-basin box** (`toplat 49.40, bottomlat 46.70,
leftlon −122.90, rightlon −120.55`, chosen as the union of the seed basin bboxes rounded out;
union is lon −122.7155…−120.6546, lat 46.7823…49.3134). Every returned message carries grid
**99 × 142 = 14,058 points**, la1 46.395, lo1 −122.805 — same Lambert projection, clipped:

| Request | Bytes | Messages | B/message |
|---|---|---|---|
| `qmd.f024`, `var_APCP` | 214,318 | 97 | 2,209 |
| `qmd.f048`, `var_APCP` | 556,896 | 129 | 4,317 |
| `qmd.f072`, `var_APCP` | 1,045,326 | 161 | 6,492 |
| `core.f024`, `var_SNOWLVL` | 171,727 | 16 | 10,733 |
| `core.f024`, `var_APCP`+`var_SNOWLVL` | 179,857 | 21 | 8,565 |

`qmd.f072` clipped is **1.05 MB against a 785 MB source file — a factor of 751.** The full
21-percentile CDF for every window comes along for free at this size, which is why v0 archives
the whole `var_APCP` subset rather than hand-picking records.

**FACT — the 403 is path-specific, not User-Agent-specific.** A direct GET of
`https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.20260824/18/qmd/…​.idx` returned
403, and the `…/prod/` directory listing returned HTTP 200 with a zero-byte body. The CGI filter
returned HTTP 200 and identical bytes under four different User-Agents (`CascadiaPapsukkal/0.1`,
the contact-bearing variant, a Mozilla-prefixed variant, and bare `curl/8.7.1`). **INFERENCE:**
NOMADS blocks automated traversal of the raw file tree but not the filter CGI. Consequence: the
S3 PDS bucket is the archive/backfill origin (2020-05-18 →, `.idx` + ranged GET), NOMADS is the
live low-cost origin (1–2 day retention, 120 hits/min per IP, SCN 21-32).

**FACT — GRIB2 decoding works from pip wheels, and SNOWLVL must be selected by GRIB identifiers,
not by name.** In an isolated venv, `pip install eccodes` pulled `eccodes` 2.48.0 bindings plus
`eccodeslib` (46 MB) and `eckitlib` (9.9 MB); `codes_get_api_version()` returned 2.48.0. Decoding
the 161-message `qmd.f072` WA subset took **0.55 s**. Key facts for the parser:

| Variable | `discipline` | `parameterCategory` | `parameterNumber` | PDT | eccodes `shortName` |
|---|---|---|---|---|---|
| APCP | 0 | 1 | 8 | 8 (statistical) / 9 (probability) | `tp`, units `kg m**-2` |
| SNOWLVL percentiles | 0 | **19** | **236** | 6 | **`unknown`**, units `unknown` |
| SNOWLVL deterministic | 0 | 19 | 236 | 0 (`typeOfFirstFixedSurface` 102) | `unknown` |

SNOWLVL is an NCEP local-table parameter that eccodes 2.48 does not name. **The parser must
match on `(discipline, parameterCategory, parameterNumber, typeOfFirstFixedSurface,
productDefinitionTemplateNumber, percentileValue)` and never on `shortName`.** This confirms
`DATA_SOURCES.md` open item 12 and turns it from a worry into a specification.

`percentileValue` is readable on both APCP and SNOWLVL percentile messages; for the WA `qmd.f072`
subset the values present were 0, 5, 10, …, 100 (FACT).

### 1.4 Derivation method — `method:basin-qpf@1.0.0` and `method:forcing-assessment@0.1.0`

**Step 1 — basin masks (precomputed once, not per cycle).**
For each basin, intersect the NBM WA subgrid cells with the **full-resolution** basin polygon
from `tests/fixtures/geo/basins_seed_full.geojson.gz` and store a fractional area weight per
cell. This is not a detail: measured this session (FACT), cell-centre containment against the
**display-LOD** geometry gave a Skagit footprint of 1,544 cells ≈ 9,961 km² against a WBD area
of 8,275 km² — a **20 % over-count**. The full-resolution geometries reproduce WBD areas to
within 1 %:

| basin | full-res area | WBD sum | parts |
|---|---|---|---|
| skagit | 8,213 km² | 8,275.4 | 8 |
| nooksack | 2,619 | 2,639.2 | 1 |
| snohomish-snoqualmie | 4,680 | 4,714.3 | 1 |
| cedar | 1,561 | 1,572.3 | 1 |
| green-duwamish | 1,249 | 1,257.9 | 1 |
| puyallup-white | 2,516 | 2,534.0 | 1 |

The mask is a function of `(basin_id, grid_definition_hash)` and is stored as a small artifact.
`grid_definition_hash` = sha256 over Section 3 of any message, so **a silent grid change
invalidates the mask instead of silently mis-aggregating** — a required invariant.

**Step 2 — basin aggregation.** For each `(window ∈ {24,48,72} h, percentile ∈ {10,25,50,75,90},
deterministic)`, compute the area-weighted mean over the mask:
`Q_basin = Σ(w_i · v_i) / Σ(w_i)`, in mm (`kg m-2 ≡ mm` for water equivalent, per
`DATA_SOURCES.md` §units). Snow level: the same weighted mean of the `SNOWLVL` p10/p50/p90
fields, in m MSL.

**Step 3 — the forcing state.** A banded function of the **p50 basin-mean QPF for the 72-h
window**, with the band table stored as a versioned parameter (never hard-coded):

| state | 72-h basin p50 QPF |
|---|---|
| `low` | < 25 mm |
| `moderate` | 25 – 75 mm |
| `high` | 75 – 150 mm |
| `very_high` | ≥ 150 mm |
| `unknown` | no usable cycle, or mask/grid mismatch |

> **ASSUMPTION**, and it must be labeled as one in the method row: these boundaries are a
> defensible first cut for western-Washington basins (75 mm/72 h is roughly the scale at which
> Cascade foothill basins begin producing action-stage responses), **not a calibrated
> threshold**. They are stored in a `Method` parameter block with this sentence attached, and the
> exit test only checks that the banding is monotone and reproducible — never that it is right.
> Calibration is Phase 7 work behind hindcast evaluation (ADR-0008).

`score` = the p50 72-h QPF mapped onto [0,1] by the same band table (piecewise-linear, capped at
200 mm), so the client has a continuous hint that is explicitly *not* a probability, per the
`SurfaceState.score` docstring.

**What the spread claim is, exactly.** NBM percentile fields are **pointwise**: the p90 field is
the 90th percentile *at each grid cell independently*. The area-weighted mean of a p90 field is
therefore **"the basin mean of the pointwise 90th percentile"**, which is *not* the 90th
percentile of basin-mean QPF (that would require the joint spatial distribution, which the
product does not carry). This is the single most likely place for the platform to overclaim.
The rule:

- the driver feature ids are `basin_qpf_72h_pointwise_p90` etc., never `basin_qpf_72h_p90`;
- the human label rendered from the structure is *"basin mean of NBM pointwise 90th-percentile
  QPF"*;
- `ConfidenceLabel` for the forcing surface is at most `moderate` while this is the spread
  method, and the method row records the limitation verbatim.

### 1.5 Contract mapping

`BasinSurfaces.forcing : SurfaceState` gains real values:

| field | v0 value |
|---|---|
| `state` | banded from p50 72-h basin QPF (table above) |
| `horizon_h` | `72` |
| `score` | band-mapped [0,1]; `null` if state is `unknown` |
| `confidence` | `moderate` when the cycle is `current`; `low` when the qmd cycle is `stale`; `unknown` when the surface is `unknown` |
| `experimental` | `true` — the *assessment* is a Cascade derivation (the QPF itself is MODELED and is provenance-referenced separately through the drivers) |
| `truth` | `cascade_derived` |
| `prov` | `nbm-forcing-<basin-slug>` → `ProvenanceRef(source_id="src:nbm-v5", source_kind=MODELED, product_id="product:nbm-v5-qmd", method_id="method:forcing-assessment@0.1.0", issued_at=<cycle>, valid_time=<cycle+72h>, retrieved_at=…, freshness=<computed>, label="NBM v5.0 basin-mean QPF, 72 h, percentile spread")` |
| `reason` | set **only** when `state == unknown`, e.g. `"No NBM qmd cycle known at this knowledge time"`, `"NBM grid definition changed (mask <hash> stale); basin mean refused rather than approximated"` |

The numbers ride in `BasinVisualizationState.headline_drivers` as `Driver` rows, which the
implemented contract already supports:

```
{feature: "basin_qpf_72h_p50",            value: 142.0, unit: "mm", direction: "increases_forcing",       rank: 1, prov: "nbm-forcing-skagit"}
{feature: "basin_qpf_72h_pointwise_p90",  value: 211.0, unit: "mm", direction: "increases_forcing",       rank: 2, prov: "nbm-forcing-skagit"}
{feature: "basin_qpf_72h_pointwise_p10",  value:  88.0, unit: "mm", direction: "decreases_forcing",       rank: 3, prov: "nbm-forcing-skagit"}
{feature: "basin_mean_snow_level_p50",    value: 2100.0, unit: "m",  direction: "context_not_scored",      rank: 4, prov: "nbm-snowlvl-skagit"}
```

**Contract decision (needs an explicit choice).** `docs/VISUALIZATION_CONTRACTS.md` §2 shows the
forcing surface carrying `qpf_mm` and `spread: {p10, p90}` directly, but the implemented
`SurfaceState` in `packages/contracts/src/cascade_contracts/visualization.py` has neither. Two
options:

- **(A) recommended — additive contract bump to 1.2.0**: add `value: Quantity | None = None` and
  `spread: dict[str, float] | None = None` to `SurfaceState`. Additive, so 1.1.0 consumers keep
  validating (`VISUALIZATION_CONTRACTS.md` §10 rule 4). Costs: bump `CONTRACT_VERSION`,
  regenerate `apps/web/src/contracts/generated.ts`, add fixtures.
- **(B) zero-change**: carry every number in `headline_drivers` only.

Recommendation: **(A)**, because it makes the doc and the code agree, and drivers should be the
*explanation*, not the only place the headline number exists. If a builder wants to avoid the
version bump on day one, (B) is complete and correct on its own — the drivers above are the
whole payload.

### 1.6 Storage and schema

**No new tables are needed for the values.** `DOMAIN_MODEL.md` §2.3 already defines
`DerivedFeature`; the spike never implemented it, so P3 adds it. Migration sketch (Alembic
revision `0002`, `down_revision = "0001"`):

```python
op.create_table(
    "derived_feature",
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("feature", sa.String, nullable=False),            # basin_qpf_72h_p50 | streamflow_doy_percentile | ...
    sa.Column("scope_kind", sa.String, nullable=False),         # basin | forecast_point | station
    sa.Column("scope_id", sa.String, nullable=False),           # basin:skagit | fp:nwps:MVEW1
    sa.Column("window", sa.String, nullable=True),              # 24h | 48h | 72h | 14d | null
    sa.Column("valid_time", sa.DateTime(timezone=False), nullable=False),
    sa.Column("issued_at", sa.DateTime(timezone=False), nullable=True),   # model cycle, null for observed-derived
    sa.Column("computed_at", sa.DateTime(timezone=False), nullable=False),
    sa.Column("available_at", sa.DateTime(timezone=False), nullable=False, index=True),
    sa.Column("method_id", sa.String, nullable=False),          # method:basin-qpf@1.0.0
    sa.Column("value", sa.Float, nullable=True),
    sa.Column("unit", sa.String, nullable=False),
    sa.Column("percentile", sa.Float, nullable=True),
    sa.Column("climatology_ref", sa.String, nullable=True),
    sa.Column("confidence_label", sa.String, nullable=False, server_default="unknown"),
    sa.Column("quality", postgresql.JSONB, nullable=False, server_default="[]"),
    sa.Column("inputs", postgresql.JSONB, nullable=False, server_default="[]"),   # [{"table":"raw_artifact","id":123}]
    sa.Column("raw_artifact_id", sa.BigInteger, sa.ForeignKey("raw_artifact.id"), nullable=True),
    sa.UniqueConstraint("method_id","feature","scope_id","window","valid_time","issued_at",
                        name="uq_derived_feature_identity"),
    sa.CheckConstraint("confidence_label IN ('high','moderate','low','unknown')",
                       name="ck_derived_feature_confidence"),
)
op.create_index("ix_derived_feature_scope_time", "derived_feature",
                ["scope_id","feature","valid_time"])
```

Append-only, like the value tables: recomputation under a new `method_id` is a new row
(`DATA_DOCTRINE.md` §8). **Not partitioned in v0** — at the volumes in §8 it will not need it
this decade, and ADR-0013 says partition when measured, not before.

Also add (small, same revision):

```python
op.create_table(
    "grid_mask",                       # basin × grid definition → fractional weights
    sa.Column("basin_id", sa.String, sa.ForeignKey("basin.id"), primary_key=True),
    sa.Column("grid_definition_hash", sa.String, primary_key=True),   # sha256 of GRIB2 Section 3
    sa.Column("method_id", sa.String, nullable=False),                # method:basin-grid-mask@1.0.0
    sa.Column("cells", postgresql.JSONB, nullable=False),             # [[flat_index, weight], ...]
    sa.Column("cell_count", sa.Integer, nullable=False),
    sa.Column("masked_area_km2", sa.Float, nullable=False),
    sa.Column("polygon_source", sa.String, nullable=False),           # basins_seed_full.geojson.gz@<sha>
    sa.Column("computed_at", sa.DateTime(timezone=False), nullable=False),
)
```

Registry additions in `packages/core/src/cascade_core/registry.py`:

```
SRC_NBM = "src:nbm-v5"                        # authority NOAA/NWS MDL via NODD, kind MODELED
PRODUCT_NBM_QMD  = "product:nbm-v5-qmd"       # PT6H  / grace PT8H   (measured +7 h 16 m)
PRODUCT_NBM_CORE = "product:nbm-v5-core"      # PT1H  / grace PT1H   (measured +42–44 m)
```

Raw archive: the NOMADS subset bytes are the `RawArtifact` (suffix `.grib2`), content-addressed
as today. Object keys should be prefixed `nbm/` so a single R2 lifecycle rule can bound them
(§8).

`ArchivingFetcher` needs two small changes for this provider: the hard-coded
`Accept: application/json` header must become a per-call parameter, and
`nomads.ncep.noaa.gov` + `noaa-nbm-grib2-pds.s3.amazonaws.com` join the allowlist. `max_bytes`
(8,000,000 default) already comfortably clears the 1.05 MB worst case.

### 1.7 Cost

Per 6-hourly `qmd` cycle: 214,318 + 556,896 + 1,045,326 = **1,816,540 B** (APCP, three horizons).
Per cycle `core` SNOWLVL at the same three lead times: ~3 × 171,727 = **515,181 B**.

| Metric | Value |
|---|---|
| Ingest bytes/day | 4 cycles × 2.33 MB = **9.4 MB/day** |
| R2 growth/month | **~285 MB** (~3.4 GB/yr) |
| Neon rows/month | 6 basins × (5 percentiles + 1 det) × 3 windows × 4 cycles × 30 = 12,960 QPF rows + ~2,160 snow-level rows ≈ **15 k rows/month ≈ 3–4 MB** |
| Worker CPU | decode 0.55 s/file + mask apply ~0.05 s (mask precomputed) → **~4 s/cycle, ~16 s/day** |
| Requests | 24 NOMADS requests/day against a 120/min limit — 0.03 % of budget |
| Egress | none (R2 egress is free; NOMADS is the source) |

Against the R2 10 GB free tier this is **2.8 %/month**. Recommendation in §8: set a 90-day
lifecycle rule on the `nbm/` prefix from day one, which caps the steady state at ~850 MB and is
explicitly sanctioned by `DATA_DOCTRINE.md` §13 ("rolling window (e.g. 90 d) for all cycles;
basin aggregates indefinite").

### 1.8 What forcing v0 deliberately does NOT do

- **No rain-exposed basin fraction and no rain-on-snow exposed fraction.** Both require
  hypsometry (3DEP area-by-elevation per basin), which does not exist in the store
  (`NEXT_STEPS.md` gap 6). SNOWLVL is ingested and shown as a basin-mean elevation driver only.
  `SnowVisualizationState.rain_exposed_fraction` stays absent, not zero.
- **No precipitation intensity or duration.** Those need the 1-h and 6-h windows across every
  forecast hour (f001…f072), which multiplies the fetch by ~12× and the archive by more. Deferred
  with a stated cost.
- **No IVT, no AR scale, no AR presence.** GEFS `pgrb2a`+`pgrb2b` per member per hour is 62
  files/hour (`DATA_SOURCES.md` W5) — categorically outside a free-tier v0.
- **No MRMS antecedent QPE.** MRMS is GRIB2 template 5.41 PNG-packed with no byte-range
  subsetting and no NOMADS spatial filter (`DATA_SOURCES.md` P1) — decode-then-clip on full-CONUS
  0.01° files. Out of scope.
- **No claim that the pointwise percentile spread is a basin-scale percentile** (§1.4).
- **No HRRR nowcast blend.** One model, one method, one badge in v0.

---

## 2. SUSCEPTIBILITY v0 — antecedent wetness

### 2.1 What was verified live

**FACT — the legacy USGS daily-statistics service is live and gives a full day-of-year
percentile climatology.**
`https://waterservices.usgs.gov/nwis/stat/?format=rdb&sites=12200500&statReportType=daily&statTypeCd=all&parameterCd=00060`
→ HTTP 200, 48,241 B, 366 rows, columns `month_nu, day_nu, begin_yr, end_yr, count_nu,
max_va_yr, max_va, min_va_yr, min_va, mean_va, p05_va, p10_va, p20_va, p25_va, p50_va, p75_va,
p80_va, p90_va, p95_va`. All seven relevant sites verified:

| site | forecast point | rows | period | years |
|---|---|---|---|---|
| 12119000 | RNTW1 Cedar at Renton | 366 | 1946–2025 | 80 |
| 12149000 | CRNW1 Snoqualmie nr Carnation | 366 | 1930–2024 | 95 |
| 12200500 | MVEW1 Skagit nr Mount Vernon | 366 | 1941–2026 | 86 |
| 12213100 | NKSW1 Nooksack at Ferndale | 366 | 1967–2026 | 59 |
| 12113000 | AUBW1 Green nr Auburn | 366 | 1962–2026 | 65 |
| 12100490 | WRAW1 White at R St | 366 | 2010–2026 | **17** |
| 12189500 | *(Sauk, unregulated Skagit tributary)* | 366 | 1929–2026 | 98 |

The service carries its own disclaimer, which must be reproduced in the method row: *the
statistics are based on approved daily-mean data and may not match official USGS publications.*

**FACT — a modern statistics API exists but does not (yet) serve discharge normals at our sites.**
`https://api.waterdata.usgs.gov/statistics/v0/openapi.json` describes "USGS Water Data Statistics
API - BETA" with `GET /statistics/v0/observationNormals` (`normal_type` ∈ {DOY, MOY}) and
`/observationIntervals` (`interval_type` ∈ {M, CY, WY}). A `percentile` record has exactly the
shape we want:

```json
{"time_of_year":"01-24","time_of_year_type":"day_of_year",
 "values":["11.545","13.371","14.52","15.8","17.235","20.379","21.318"],
 "percentiles":["5","10","25","50","75","90","95"],
 "sample_count":36,"approval_status":"approved","computation":"percentile"}
```

But at `USGS-12200500` the normals cover parameter codes **80154, 00065, 63680, 00010, 80155 —
not 00060**, and `parameter_code=00060` returns zero features; `/observationIntervals` returned
an empty collection for that site. **OPEN QUESTION:** whether discharge normals are backfilled
before WaterServices is decommissioned in Q1 2027, and whether the `parameter_code` filter is
simply broken in BETA (it also returned zero for a code that *is* present). Re-probe quarterly.

**FACT — the platform can build its own climatology in one request per site.**
`https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?monitoring_location_id=USGS-12200500&parameter_code=00060&statistic_id=00003&f=csv&skipGeometry=true&limit=50000&properties=time,value,approval_status`
→ HTTP 200, **903,170 B, 31,374 lines (31,373 daily means), 1.5 s**, each row carrying
`approval_status`. `latest-daily` gives the previous complete day with the same field
(`{"time":"2026-08-23","value":"6720","approval_status":"Provisional"}`).

**FACT — AWDB SNOTEL is live and cheap.** 78 active WA SNTL stations (34,719 B). A single
`data` call for the 30 Puget-basin sites listed in `DATA_SOURCES.md` S1, `elements=WTEQ`,
`duration=DAILY`, 30 days, `periodRef=END`, `centralTendencyType=MEDIAN`, `returnFlags=true`
→ **69,834 B in 1.87 s**, per-value shape `{"date","value","qcFlag","qaFlag","median"}`.

**FACT — and here is the negative result. SNOTEL soil moisture does not support a v0 soil claim.**
`elements=SMS:*` for the eleven sites documented as having soil probes returned **9** sites, with:

- **no `median` key at all** even with `centralTendencyType=MEDIAN` (so no percent-of-median, and
  certainly no percentile);
- inconsistent depth sets per site (−2, −4, −8, −20, −40 in, varying);
- `qcFlag: "N"` (*no profile*) on most returned sites;
- physically incoherent profiles, e.g. Rainy Pass (711) reading `−2 in: 10.1 %`, `−4 in: 0.0 %`,
  `−8 in: 24.9 %`, `−20 in: 10.1 %` on the same day; Beaver Pass (990) reading `0.0 %` at −2 and
  −4 in beside `40.6 %` at −20 in.

There is no honest way to turn that into a basin soil-saturation percentile. `DATA_SOURCES.md`
§4 already records that Washington has no other mountain soil network. **Soil stays UNKNOWN.**

### 2.2 Derivation method — `method:streamflow-doy-climatology@1.0.0` + `method:susceptibility-index@0.1.0`

**The claim v0 makes, stated exactly:** *the river that drains this basin is currently at the Nth
percentile of its own recorded flow for this day of the year.* That is an observed-derived
integrator of soil water, groundwater and channel storage — the standard antecedent-wetness
proxy — and nothing more. It is **not** a soil-moisture estimate, **not** a snow statement, and
**not** a forecast.

**Step 1 — build the climatology (one job, annual cadence).** For each basin's *susceptibility
gauge* (§2.3), pull the entire approved daily-mean record from USGS OGC `daily`, keep rows with
`approval_status == "Approved"`, group by `(month, day)` with a ±2-day window to stabilize small
samples, and compute p05/p10/p25/p50/p75/p90/p95 plus `sample_count`, `begin_year`, `end_year`.
Store as `derived_feature` rows with `feature="streamflow_doy_climatology"`,
`method_id="method:streamflow-doy-climatology@1.0.0"`, `climatology_ref="usgs-ogc-daily:<site>:<begin>-<end>"`.
Recompute annually; a recomputation is new rows, never an update.

**Step 2 — cross-check, do not fuse.** Also fetch the USGS `nwis/stat` table (and, where it
exists, `observationNormals`) and store it as a *separate* climatology under
`method_id="method:usgs-published-doy-stats@1.0.0"`. If the Cascade p50 and the USGS p50 differ
by more than 10 % on the current day of year, the surface's `confidence` drops one level and a
driver records the disagreement. `DATA_DOCTRINE.md` §10: disagreement is reported, never
averaged.

**Step 3 — today's percentile.** Take the most recent complete daily mean known at `as_of` from
OGC `latest-daily`/`daily`, linearly interpolate its rank within the stored DOY percentile ladder
(clamped to [0,100] with `quality=["outside_climatology_range"]` beyond p05/p95), and write
`feature="streamflow_doy_percentile"`, `percentile=<p>`, `window=null`.

> Using a **daily mean** against a **daily-mean** climatology is the correct comparison. The
> 15-minute instantaneous value we already ingest is *not* interchangeable with it and must not be
> substituted; when the latest daily mean is older than 48 h the surface goes `unknown` with the
> reason rather than falling back to the instantaneous value.

**Step 4 — the state.**

| state | streamflow DOY percentile |
|---|---|
| `low` | < 25 |
| `moderate` | 25 – 74 |
| `high` | 75 – 89 |
| `very_high` | ≥ 90 |
| `unknown` | no daily mean ≤ 48 h old, or no climatology for the gauge |

`score` = percentile / 100. **ASSUMPTION**: the band boundaries are conventional
(the USGS WaterWatch convention of 25/75/90 for below-normal / above-normal / much-above-normal),
stored as a versioned parameter with that citation, and not calibrated to flood response.

**Step 5 — context drivers that are shown and never scored.** Per `HYDROLOGY.md` §7, more SWE is
not more risk, and per §8 soil is declining storage. So:

```
{feature:"basin_swe_percent_of_median", value: 118, unit:"pct", direction:"context_not_scored", rank:2, prov:"awdb-swe-<basin>"}
{feature:"snotel_precip_14d_percent_of_median", value: 143, unit:"pct", direction:"context_not_scored", rank:3, prov:"awdb-prec-<basin>"}
{feature:"soil_saturation_percentile", value: null, unit:"pct", direction:"unavailable", rank:4, prov:"cascade-soil-unavailable"}
```

The SWE driver is the area-unweighted mean of `value/median` across the basin's mapped SNOTEL
sites (a point-network statistic, labeled as such, with `n` sites and their elevations in the
provenance label). The soil driver exists precisely so that the absence is *visible* rather than
silently omitted, with a `ProvenanceRef(source_kind=UNKNOWN, label="No basin soil-moisture
product ingested; SNOTEL SMS rejected — see p3-surfaces-design §2.1")`.

### 2.3 Which gauge measures a basin's wetness — the regulation problem

`HYDROLOGY.md` §2 and §9: on a regulated reach, flow is an operator decision, not a basin state.
Three of six seed basins are regulated above their outlet. v0 therefore configures a
`susceptibility_gauge` per basin, distinct from the outlet forecast point:

| basin | regulation | susceptibility gauge | confidence ceiling | note |
|---|---|---|---|---|
| `basin:nooksack` | natural | 12213100 (NKSW1) | `high` | tidally influenced at Ferndale — **OPEN QUESTION** whether the daily mean is materially tide-contaminated; flag until checked |
| `basin:snohomish-snoqualmie` | natural | 12149000 (CRNW1) | `high` | |
| `basin:cedar` | partially regulated | 12119000 (RNTW1) | `moderate` | Chester Morse is water supply, limited flood role |
| `basin:skagit` | regulated upper | **12189500 (Sauk)** | `moderate` | Sauk is unregulated and often the dominant flood contributor (HYDROLOGY §2); 98-year record |
| `basin:green-duwamish` | regulated | 12113000 (AUBW1) | **`low`** | below Howard Hanson — the percentile partly measures USACE operations |
| `basin:puyallup-white` | regulated | 12100490 (WRAW1) | **`low`** | below Mud Mountain **and** only a 17-year record |

Each of those notes becomes a driver or the `reason` text, never a silent adjustment. **OPEN
QUESTION for the owner/Phase 3.1:** whether to add unregulated inflow gauges above Howard Hanson
and Mud Mountain as the Green/White susceptibility gauges — that is a seed-data decision, not a
code decision, and would raise those two from `low` to `moderate`.

### 2.4 Contract mapping

| field | v0 value |
|---|---|
| `state` | banded percentile (table in §2.2 step 4) |
| `horizon_h` | `null` — susceptibility is a present-state surface, not a horizon surface |
| `score` | percentile / 100 |
| `confidence` | `min(gauge ceiling from §2.3, freshness-derived, climatology-agreement-derived)` |
| `experimental` | `true` |
| `truth` | `cascade_derived` |
| `prov` | `cascade-susceptibility-<slug>` → `ProvenanceRef(source_id="src:cascade", source_kind=EXPERIMENTAL, method_id="method:susceptibility-index@0.1.0", valid_time=<daily mean date>, freshness=…, label="Cascade experimental susceptibility index from USGS daily-mean flow percentile (12189500, 1929–2026, n=98)")` |
| `reason` | `"Latest approved/provisional daily mean is older than 48 h"` · `"No day-of-year climatology stored for station:usgs:<id>"` · `"Basin has no susceptibility gauge configured"` |

The USGS observation itself gets its own `ProvenanceRef` (`source_kind=OBSERVED`,
`product_id="product:usgs-ogc-daily"`) referenced from the percentile driver, so the chain
observation → climatology → index is walkable in the layer inspector.

### 2.5 Storage and cost

Reuses `derived_feature` from §1.6. Climatology rows: 366 days × 6 gauges = 2,196 rows if the
seven percentiles are columns of one row (recommended: put them in the `quality`-adjacent JSONB
or add a `values jsonb` column) — one-time, recomputed annually. Daily rows: 6 basins × ~3
features = 18 rows/day.

| Metric | Value |
|---|---|
| One-time ingest | 6 × ~900 KB OGC `daily` CSV = **5.4 MB**; 7 × ~45 KB `nwis/stat` = **0.3 MB** |
| Ingest bytes/day | `latest-daily` 6 sites ≈ 15 KB + AWDB WTEQ/PREC latest day ≈ 10 KB = **~25 KB/day** |
| R2 growth/month | **~0.8 MB** |
| Neon rows/month | ~540 derived rows ≈ **0.1 MB**; plus 2,196 climatology rows/year |
| Worker CPU | < 1 s/day (climatology build: ~2 s per site, annually) |
| Requests | ~10/day, well inside USGS keyed 4,000/h and AWDB's undocumented budget |

### 2.6 What susceptibility v0 deliberately does NOT do

- **No soil claim of any kind** (§2.1). `soil_saturation_percentile` is emitted as `null` with an
  explicit unavailability provenance, never omitted and never inferred from SWE or API.
- **No baseflow separation.** A digital-filter baseflow index is easy to compute and hard to
  defend without evaluation; deferred.
- **No SWE contribution to the index.** SWE is context only — doctrine, not laziness.
- **No basin-average antecedent precipitation index.** The only cheap precipitation observations
  are SNOTEL points at 2,250–6,490 ft, which are systematically unrepresentative of basin-mean
  rainfall. The 14-day SNOTEL accumulation is shown as a **point-network** driver with `n` and
  elevations, and is never called "basin API".
- **No reservoir buffer term.** Phase 4.
- **No fusion of disagreeing climatologies.** They are stored separately and their disagreement
  lowers confidence.

---

## 3. AGREEMENT v0 — model agreement at forecast points

### 3.1 What was verified live — and why the CONUS NetCDF question is moot

The brief asked what it really costs to extract one reach from a CONUS NetCDF. The answer is:
**you do not have to.**

**FACT — NWPS serves the NWM per-reach series as JSON.** All fetched 2026-08-24 ~21:10Z:

| Request (`https://api.water.noaa.gov/nwps/v1/reaches/24270288/streamflow?series=…`) | Bytes | Shape | `referenceTime` |
|---|---|---|---|
| `short_range` | 2,724 | `shortRange.series.data[18]`, units `ft³/s` | 2026-08-24T18:00Z |
| `medium_range` | **157,346** | `mediumRange.{mean, member1…member6}`, `mean`/`member1` `data[240]`, `member2–6` `data[204]` | 2026-08-24T12:00Z |
| `medium_range_blend` | 25,755 | `mediumRangeBlend.series.data[240]` | 2026-08-24T12:00Z |
| `long_range` | 64,055 | `longRange.{mean, member1…member4}`, `data[120]` | 2026-08-24T06:00Z |
| `analysis_assimilation` | 13,316 | `analysisAssimilation.series.data[120]` | 2026-08-24T16:00Z |

`https://api.water.noaa.gov/nwps/v1/reaches/24270288` (541 B) returns `name`, lat/lon, the list
of available series, and `route.{upstream,downstream}` reach ids with stream order.

**FACT — `mean` is not a copy of `member1`.** Verified numerically: identical for roughly the
first 48 forecast hours (all members share the same forcing early), diverging by lead 100 h
(mean 5832.45 vs member1 5832.22 vs member2 5832.57) and clearly by lead 200 h (mean 5912.26;
members 5910.26 / 5926.15 / 5907.79 / 5910.97 / 5909.20 / 5909.20). So `mean` is usable as a
central member-derived series, but per `DATA_DOCTRINE.md` §9 the **members are stored as members**
and the mean is labeled as a read-time average produced by NWPS.

**FACT — every seed forecast point has a `reachId`, and five of six are missing from the seed
file.** From `https://api.water.noaa.gov/nwps/v1/gauges/{lid}`:

| LID | usgsId | reachId | in `seed/stations.json` today |
|---|---|---|---|
| RNTW1 | 12119000 | 24537890 | `null` |
| CRNW1 | 12149000 | 23970199 | `null` |
| MVEW1 | 12200500 | 24270288 | `reach:nwm:24270288` |
| NKSW1 | 12213100 | 23955772 | `null` |
| AUBW1 | 12113000 | 23977634 | `null` |
| WRAW1 | 12100490 | 23981235 | `null` |

These match the `RouteLink` crosswalk already recorded in `DATA_SOURCES.md` H8 for
12119000/12149000/12200500/12213100/12113000/12100490. **Seeding these five is a P3
prerequisite** (a one-line-per-point data edit plus a re-seed; `ForecastPoint.reach_id` already
exists in the ORM).

**FACT — the official run's flow column is the comparison basis, and it is missing at one point.**
Six `/gauges/{lid}/stageflow/forecast` runs (issued 15:10–15:30Z, 40 points each):

| LID | primary | secondary | usable secondary points |
|---|---|---|---|
| RNTW1 | Stage / ft | Flow / kcfs | **40 / 40** |
| CRNW1 | Stage / ft | Flow / kcfs | **0 / 40** — every value is the `−999` sentinel |
| MVEW1 | Stage / ft | Flow / kcfs | 40 / 40 |
| NKSW1 | Stage / ft | Flow / kcfs | 40 / 40 |
| AUBW1 | River Discharge / kcfs | Stage / ft | 40 / 40 |
| WRAW1 | River Discharge / kcfs | Stage / ft | 40 / 40 |

**FACT — official flow thresholds exist at only two points.** From the same `/gauges/{lid}`
payloads:

| LID | action | minor | moderate | major | basis |
|---|---|---|---|---|---|
| MVEW1 | 23.5 ft | 28 | 30 | 32 | stage (flow all `−9999`) |
| CRNW1 | 50.7 ft | 54 | 56 | 58 | stage (flow all `−9999`) |
| NKSW1 | 15 ft | 18 | 20.5 | 23 | stage (flow all `−9999`) |
| RNTW1 | 10.4 ft | 13 | 14.5 | 16 | stage (flow all `−9999`) |
| **AUBW1** | 6,000 cfs | 9,000 | 12,000 | 14,000 | **flow** |
| **WRAW1** | 5,500 cfs | 7,500 | 10,000 | 12,000 | **flow** |

**FACT — official rating tables are available** if a later phase wants stage↔flow conversion:
`/gauges/MVEW1/ratings` → 198,545 B, `/gauges/CRNW1/ratings` → 104,766 B, both
`stageUnits: ft`, `flowUnits: cfs`, dense 0.01-ft tables. Not used in v0 (§3.5).

**Alternatives considered and rejected for v0** (each is a real path, all cost more):
- **NWM CONUS NetCDF byte extraction.** `channel_rt` is ~12.5 MB/timestep and NetCDF4/HDF5
  chunking would let a ranged read pull one reach, but it needs an HDF5 reader plus the
  `feature_id` → array-index map from the 269 MB `RouteLink_CONUS.nc`, re-derived on every NWM
  version change (v3.1 landed 2026-08-18 with RouteLink `to` changes). Weeks of work to
  reproduce a 157 KB JSON call. **INFERENCE:** strictly worse for six reaches.
- **`noaa-nodd-kerchunk-pds` / Zarr references.** Same conclusion, plus a `zarr`+`fsspec`+
  `kerchunk` dependency stack.
- **NWPS HEFS API** (`/hefs/v1/ensembles/`, 45 members, 137 WA locations, ~10-day retention).
  This is the *right* second opinion eventually and `ROADMAP.md` Phase 5 already owns it — but
  HEFS is NWRFC-produced, so comparing HEFS to the NWRFC deterministic run measures ensemble
  spread, **not independence**. NWM is a genuinely independent model. v0 uses NWM; the HEFS
  archive-from-day-one recommendation in `ROADMAP.md` Phase 5 stands unchanged.

### 3.2 Derivation method — `method:model-agreement@0.1.0`

Compared quantity: **crest flow inside the 72-h hazard horizon**, i.e. the same window
`(as_of − 6 h, as_of + 72 h]` that `surfaces.forecast_crest` already uses, so hazard and
agreement are talking about the same event.

1. **Official crest** `C_off` = max of the NWRFC run's **flow** column in the window (kcfs → cfs
   at ingest; `ForecastRun.flow_unit` is already "always cfs after normalization"). If the run
   has no usable flow column → `AgreementState(state=UNKNOWN, reason=…)`, stop.
2. **NWM crests** `C_m` for `m ∈ {member1…member6}` = max flow in the same window from the
   `medium_range` run whose `referenceTime` is the latest known at `as_of`. `C_nwm` = median of
   `{C_m}` (a member statistic, labeled; **never** a blend of NWM with the official forecast).
3. **Magnitude divergence** `Δ = (C_nwm − C_off) / max(C_off, floor)` where `floor` is the
   basin's official `action` flow if defined, else the climatological p50 flow from §2 (so a
   ratio on a near-zero denominator cannot manufacture disagreement). Recorded signed.
4. **Timing divergence** `Δt = |t(C_nwm) − t(C_off)|` in hours, using the median member's crest
   time.
5. **Category divergence** — computed **only at AUBW1 and WRAW1**, where official flow thresholds
   exist: `categorize(C_off)` vs `categorize(C_nwm)`, difference in ordinal steps.
6. **State:**

| state | condition |
|---|---|
| `high` | \|Δ\| ≤ 0.25 **and** Δt ≤ 6 h **and** (category difference 0, or not computable) |
| `moderate` | \|Δ\| ≤ 0.60 **and** Δt ≤ 18 h **and** category difference ≤ 1 |
| `low` | anything worse |
| `unknown` | no official flow column, or no NWM run known at `as_of`, or the horizons do not overlap |

> **ASSUMPTION**: the 0.25/0.60 and 6 h/18 h boundaries are a stated first cut, stored as method
> parameters with this sentence. They are not calibrated. The exit test checks reproducibility
> and the UNKNOWN paths, not correctness of the bands.

7. **Model probability** (`HazardState.model_probability`), emitted **only at AUBW1/WRAW1**:
   `{"model": "nwm-v3.1-medium-range", "exceeds": "<category>", "fraction": k/6}` — the literal
   empirical fraction of the six members whose crest exceeds the official flow threshold, which is
   exactly the form `DATA_DOCTRINE.md` §9(b) permits ("11 of 21 GEFS-driven members exceed
   minor"). Elsewhere `null` with `HazardState.reason` naming the stage-only thresholds.

### 3.3 Contract mapping

`AgreementState` needs no schema change — it already carries `state`, `reason`,
`explanation_ref` and `prov: tuple[str, ...]`:

```
AgreementState(
  state = AgreementLevel.MODERATE,
  reason = None,                                    # set on LOW/UNKNOWN
  explanation_ref = "/explanations/basin:skagit/agreement?as_of=…",
  prov = ("nwps-forecast-mvew1", "nwm-mr-mvew1"),
)
```

with two provenance refs of **different kinds** — this is the point of the surface:

```
"nwps-forecast-mvew1": ProvenanceRef(source_id="src:nwps-v1",  source_kind=OFFICIAL_FORECAST,
                                     product_id="product:nwps-forecast", label="NWRFC official river forecast via NOAA NWPS")
"nwm-mr-mvew1":        ProvenanceRef(source_id="src:nwm-v3.1", source_kind=MODELED,
                                     product_id="product:nwm-mr-via-nwps",
                                     label="NWM v3.1 medium-range ensemble (6 members) via NWPS /reaches")
```

The divergence numbers ride as drivers on the basin item:

```
{feature:"agreement_crest_flow_official",   value: 132700, unit:"cfs", direction:"reference",           rank:1, prov:"nwps-forecast-mvew1"}
{feature:"agreement_crest_flow_nwm_median", value: 158100, unit:"cfs", direction:"model_exceeds_official", rank:2, prov:"nwm-mr-mvew1"}
{feature:"agreement_crest_timing_delta_h",  value: 9.0,    unit:"h",   direction:"model_later",          rank:3, prov:"nwm-mr-mvew1"}
```

Per-point, `RiverVisualizationState.agreement` (the contract has `AgreementLevel` on the river
item too — currently unpopulated) gets the same state, and `model_forecasts` in the doc's §3
shape is a natural later addition.

### 3.4 Storage, and two blocking defects in the current read path

The NWM run fits `ForecastRun`/`ForecastValue` **without a schema change**: `UNIQUE(product_id,
fp_id, issued_at)` accommodates it with `product_id="product:nwm-mr-via-nwps"`,
`primary_variable="flow"`, `unit="cfs"`, `flow_unit="cfs"`, `stage_unit=None`, `datum=None`
(ADR-0014: flow values never have a datum). **But putting a second forecast product into that
table breaks two things that must be fixed first:**

1. **`packages/core/src/cascade_core/knowledge.py::latest_forecast_run(fp_id)` does not filter by
   product.** It orders by `issued_at desc` over every run at the point. The NWM run is issued at
   12:00Z and the NWRFC run at ~15:10Z today, but on any cycle where NWM is newer, the **official
   forecast surface would silently start rendering an NWM run as the NWRFC forecast.** This is a
   doctrine violation of the first order. Fix: add `product_ids: frozenset[str] | None = None`
   to `latest_forecast_run` and `forecast_runs`, and have `assemble.assess_point` pass the
   official set explicitly.
2. **`packages/hydrology/src/cascade_hydrology/assemble.py::forecast_run_ref` hard-codes
   `source_kind=SourceKind.OFFICIAL_FORECAST`** for every run it describes. An NWM run described
   through that function would be badged OFFICIAL. Fix: resolve the kind from
   `DataSource.kind` via `SourceProduct.source_id` (the `products` dict is already threaded
   through), defaulting to `UNKNOWN` rather than to OFFICIAL when the lookup misses.

Both are small, both are on the critical path, and both belong to **one owner** (see §6).

Registry additions:

```
SRC_NWM = "src:nwm-v3.1"                       # NOAA/NWS OWP, kind MODELED
PRODUCT_NWM_MR = "product:nwm-mr-via-nwps"     # PT6H / grace PT8H
```

**Volume control.** Storing all seven series × 240 hours × 6 reaches = 10,080 `forecast_value`
rows per cycle = **1.2 M rows/month**, which would consume the Neon free tier's 0.5 GB in months.
v0 therefore stores, per reach per cycle: **one `ForecastRun` with the `mean` series truncated to
the 72-h hazard window (72 points)**, plus the member crest summary as `derived_feature` rows
(6 members × 1 crest + 1 timing = 7 rows). The full 240-hour, 7-series JSON stays in R2 as the
raw artifact and is re-derivable. Result: 6 × 72 = 432 forecast_value rows + ~42 derived rows per
cycle → **~57 k rows/month ≈ 10 MB/month**.

### 3.5 Cost

| Metric | Value |
|---|---|
| Ingest bytes/day | 6 reaches × 157,346 B × 4 cycles = **3.8 MB/day** |
| R2 growth/month | **~114 MB** uncompressed |
| Neon rows/month | ~57 k rows ≈ **10 MB** |
| Worker CPU | JSON parse + max over 6×72 points — **< 0.5 s/cycle** |
| Requests | 24/day against an undocumented NWPS budget; the existing per-host token bucket covers it |

If the owner wants this smaller: `medium_range_blend` is 25,755 B instead of 157,346 B
(6.1× cheaper, **0.62 MB/day**) but it is a single deterministic series, so `model_probability`
and any member-fraction statement become impossible and agreement degrades to
magnitude+timing only. **Recommendation: keep the full ensemble** — the member fraction at
AUBW1/WRAW1 is the only genuinely probabilistic number v0 can honestly print. A gzip-at-archive
option (§8) reduces the ensemble path to ~14 MB/month and is the better lever.

### 3.6 What agreement v0 deliberately does NOT do

- **No agreement at CRNW1.** The NWRFC run there carries no usable flow column (0/40 points) and
  NWM produces flow only. `AgreementState(state=UNKNOWN, reason="The NWRFC forecast for CRNW1
  carries no flow column (all secondary values are the −999 sentinel); NWM produces flow only, so
  the two cannot be compared without a rating conversion (not in v0).")`
- **No stage↔flow conversion through the official rating**, even though the tables were verified
  as available. That is `method:nwps-rating-conversion@1.0.0`, a P3.1 item with its own DERIVED
  badge and its own error discussion.
- **No category agreement at the four stage-threshold points** — official flow thresholds are
  `−9999` there, and ADR-0011 forbids inventing them.
- **No HEFS**, **no averaging of any kind**, **no "consensus" number**.
- **No skill or bias bookkeeping.** That needs history and is Phase 5/7.

---

## 4. Cross-cutting changes P3 requires

| # | Change | File | Why | Owner (§6) |
|---|---|---|---|---|
| 1 | `latest_forecast_run` / `forecast_runs` take a product filter | `packages/core/src/cascade_core/knowledge.py` | a second forecast product would otherwise be read as the official one (§3.4) | **C** |
| 2 | `forecast_run_ref` resolves `source_kind` from the registry | `packages/hydrology/src/cascade_hydrology/assemble.py` | prevents badging NWM as OFFICIAL (§3.4) | **C** |
| 3 | `derived_feature` + `grid_mask` tables | `infra/migrations/versions/0002_*.py` | `DOMAIN_MODEL.md` §2.3 finally implemented | **A** (both builders depend on it — land it first) |
| 4 | `SurfaceState.value` + `SurfaceState.spread`; `CONTRACT_VERSION` → `1.2.0` | `packages/contracts/src/cascade_contracts/{visualization,common}.py` | make the code match `VISUALIZATION_CONTRACTS.md` §2 (optional — see §1.5) | **A** |
| 5 | `ArchivingFetcher`: per-call `Accept` header; allowlist `nomads.ncep.noaa.gov`, `noaa-nbm-grib2-pds.s3.amazonaws.com`, `wcc.sc.egov.usda.gov` | `packages/core/src/cascade_core/fetch.py` | `Accept: application/json` is hard-coded; GRIB and RDB are not JSON | **A** |
| 6 | Seed `reach_id` for RNTW1/CRNW1/NKSW1/AUBW1/WRAW1; add `susceptibility_gauge` per basin (incl. the Sauk, `station:usgs:12189500`) | `packages/core/src/cascade_core/seed/stations.json` | prerequisites for §2.3 and §3.1 | **C** (agreement) / **B** (susceptibility) — coordinate: one PR, both edits |
| 7 | `eccodes` in the **worker** dependency set only | `pyproject.toml` (worker extra), `infra/Dockerfile` | ~94 MB of wheels (`eccodeslib` 46 MB, `eckitlib` 10 MB, numpy 37 MB); build-time only, **zero recurring cost**; the API image must not grow | **A** |
| 8 | Render `agreement.reason`; render drivers | `apps/web/src/panels/BasinPanel.tsx` | the field exists in the contract and is not displayed; UNKNOWN must always show its reason | **D** (or fold into A) |
| 9 | New `DATA_SOURCES.md` rows / edits for `src:nbm-v5` (NOMADS filter as primary access), `src:nwm-v3.1` (NWPS `/reaches` access), `src:usgs-wdfn-statistics` | `docs/DATA_SOURCES.md` | every provider lands with its row (ROADMAP cross-cutting) | each builder for their own row |

**Dependency decision to put to the owner (item 7).** Forcing v0 needs a GRIB2 decoder. `eccodes`
installs cleanly from pip wheels (verified) and adds ~94 MB to the *worker* image; it is a
build-time cost with no recurring charge, and the decode measured 0.55 s. **If that is refused**,
the documented fallback is the NWS API gridpoint path: `/gridpoints/{wfo}/{x},{y}` returns
`quantitativePrecipitation` (PT6H, mm) and `snowLevel` (PT3H, m) as JSON on the same 2.5 km grid,
is OFFICIAL_FORECAST rather than MODELED, and needs no binary dependency — but it carries **no
percentiles**, so `forcing` would ship with `spread: null` and `confidence: low`, and the surface
would sample K cells per basin instead of area-weighting ~1,500. That is a materially weaker
surface; the dependency is the better trade.

---

## 5. Exit tests

The P3 exit criterion in `NEXT_STEPS.md` is *"no surface shows UNKNOWN for reasons that are now
implemented; every value traces."* Per surface:

**Forcing**
1. `GET /viz/basins` returns `surfaces.forcing.state != "unknown"` for all six basins whenever an
   NBM `qmd` cycle within `cadence + grace` (6 h + 8 h) is stored; and returns `"unknown"` with
   the *specific* reason string when it is not. Both branches asserted.
2. Fixture test: the archived `qmd.f072` WA subset (checked in under
   `tests/fixtures/providers/nbm/`) decodes to 161 messages, and the Skagit basin-mean p50 QPF
   equals a golden value to 0.01 mm — deterministic, no network (`TESTING.md`).
3. Mask invariant: masked area per basin is within **3 %** of the WBD area in
   `basins_seed_full.geojson.gz` (measured margin today is ≤ 1 %); a mutated
   `grid_definition_hash` makes the job refuse and emit `state=unknown`, not a wrong number.
4. Provenance: every forcing driver resolves to a `ProvenanceRef` whose `source_kind` is
   `MODELED` for the QPF and `EXPERIMENTAL` for the assessment; the `ContractEnvelope` validator
   already fails on unresolved refs.
5. Replay: `?as_of=` one hour before the first NBM ingestion returns `unknown` with the
   "no cycle known" reason — the same knowledge-time boundary P1 already proved.

**Susceptibility**
1. All six basins return a non-`unknown` state with a `score` when a daily mean ≤ 48 h old exists;
   `"unknown"` with the 48-hour reason when it does not (test by advancing `as_of`).
2. Golden climatology test: the Cascade-built DOY percentiles for `12200500` from a checked-in
   OGC `daily` fixture reproduce a stored ladder exactly, and land within **10 %** of the
   `nwis/stat` p50 for at least 350 of 366 days.
3. `soil_saturation_percentile` is present in `headline_drivers` with `value: null` and an
   unavailability provenance — asserted, so it cannot be quietly dropped later.
4. Regulated basins (`green-duwamish`, `puyallup-white`) never report `confidence` above `low`;
   `skagit` uses `station:usgs:12189500` and says so in the provenance label.
5. No SWE driver ever carries a `direction` that scores it.

**Agreement**
1. `state != "unknown"` at MVEW1, NKSW1, RNTW1, AUBW1, WRAW1 when both a NWRFC run and an NWM
   `medium_range` run are known; `state == "unknown"` at **CRNW1** with the flow-column reason —
   asserted explicitly, because that UNKNOWN is correct and must not regress into a fabricated
   comparison.
2. `model_probability` is non-null **only** at AUBW1 and WRAW1, and its `fraction` denominator is
   6.
3. Regression test for defect §3.4(1): with both an NWRFC run and a *later-issued* NWM run stored
   at the same point, `official_forecast` still comes from the NWRFC product and its
   `ProvenanceRef.source_kind` is `OFFICIAL_FORECAST`; the NWM ref is `MODELED`. Property test:
   **no `ProvenanceRef` with `source_id == "src:nwm-v3.1"` may ever carry
   `source_kind == OFFICIAL_FORECAST`** — the exact shape of the existing fallback test in
   `DATA_DOCTRINE.md` §14.
4. Nothing in the agreement path computes a mean of official and model values (grep-level check
   plus review).

**Cross-cutting**
- `lint-imports` still passes (the new provider packages must not be importable from
  `cascade_api`).
- `pytest` green with **zero network**; three canaries (`nbm`, `nwm-via-nwps`, `awdb`) runnable
  separately and non-blocking.
- `contracts:check` passes; if §1.5 option (A) is taken, `generated.ts` is regenerated and the
  version is `1.2.0`.

---

## 6. Build order and file-ownership map (three parallel builders, zero overlaps)

**Stage 0 — Builder A alone (blocks everything, ~half the work of a surface).**

| Owner | Files | Deliverable |
|---|---|---|
| **A · foundation** | `infra/migrations/versions/0002_derived_feature_and_grid_mask.py`; `packages/core/src/cascade_core/registry.py`; `packages/core/src/cascade_core/fetch.py`; `packages/contracts/src/cascade_contracts/{visualization,common}.py`; `pyproject.toml`; `infra/Dockerfile`; `packages/core/src/cascade_core/knowledge.py` (add the `derived_features()` reader) | `derived_feature` + `grid_mask` tables; source/product registry ids for NBM, NWM, USGS statistics, AWDB; per-call `Accept` + allowlist; optional contract 1.2.0; `eccodes` in the worker extra |

Stage 0 ends when `alembic upgrade head` is green on a scratch PostGIS and `pytest` is green.

**Stage 1 — three builders in parallel. No file appears in two rows.**

| Owner | Owns exclusively | Must not touch |
|---|---|---|
| **A · forcing** | `packages/providers/nbm/**` (new: `client.py`, `parser.py`, `normalize.py`, `jobs.py`, `canary.py`, `fixtures/`); `packages/geo/**` (new: `masks.py` — grid-mask build from `basins_seed_full.geojson.gz`); `packages/hydrology/src/cascade_hydrology/forcing.py` (new); `tests/fixtures/providers/nbm/**`; `tests/unit/test_forcing.py`; the W2 row in `docs/DATA_SOURCES.md` | `assemble.py`, `knowledge.py`, `seed/stations.json` |
| **B · susceptibility** | `packages/providers/usgs/src/cascade_providers_usgs/{stats_client.py,stats_parser.py,climatology.py,stats_jobs.py}` (new files in the existing package); `packages/providers/awdb/**` (new); `packages/hydrology/src/cascade_hydrology/susceptibility.py` (new); `tests/fixtures/providers/{usgs-stats,awdb}/**`; `tests/unit/test_susceptibility.py`; the H2/S1 rows in `docs/DATA_SOURCES.md`; the `susceptibility_gauge` block of `seed/stations.json` | `assemble.py`, `knowledge.py`, existing USGS `jobs.py`/`client.py`/`parser.py` |
| **C · agreement + read-path fixes** | `packages/providers/nwps/src/cascade_providers_nwps/{reaches_client.py,reaches_parser.py,reaches_normalize.py,reaches_jobs.py}` (new files in the existing package); `packages/hydrology/src/cascade_hydrology/agreement.py` (new); **`packages/core/src/cascade_core/knowledge.py`** (product filter — §4 item 1); **`packages/hydrology/src/cascade_hydrology/assemble.py::forecast_run_ref`** (§4 item 2); `tests/fixtures/providers/nwm-via-nwps/**`; `tests/unit/test_agreement.py`; the H3/H6 rows in `docs/DATA_SOURCES.md`; the `reach_id` fields of `seed/stations.json` | `surfaces.py`, `forcing.py`, `susceptibility.py`, `packages/providers/nbm/**` |

> `seed/stations.json` is the one shared file. Resolve it by having **C** land the `reach_id`
> edits in Stage 0 alongside A's foundation work (they are five field values), and **B** add the
> `susceptibility_gauge` block afterwards. Or: B and C each write their block into a separate
> `seed/*.json` file and `seed.py` merges — cleaner, and `seed.py` is A's file.

**Stage 2 — integration, one owner (whoever finishes first, by agreement).**

| File | Change |
|---|---|
| `packages/hydrology/src/cascade_hydrology/surfaces.py` | replace `SUSCEPTIBILITY_REASON` / `FORCING_REASON` / `AGREEMENT_REASON` with the new reason *vocabularies* (they become functions of the missing input, not constants) |
| `packages/hydrology/src/cascade_hydrology/assemble.py::basin_envelope` | call `forcing.assess()`, `susceptibility.assess()`, `agreement.assess()`; drop `CASCADE_REFS`; populate `headline_drivers` |
| `apps/worker/src/cascade_worker/scheduler.py` + `queue.py` | register `nbm.fetch_qmd` (21600 s → `10 */6 * * *`), `nbm.fetch_core_snowlvl` (21600 s), `nwm.fetch_reach_medium_range` (21600 s), `usgs.fetch_daily` (86400 s), `awdb.fetch_daily` (86400 s), `usgs.build_climatology` (annual — run manually or via a `cron_for_cadence` extension; note `cron_for_cadence` currently raises for any cadence that is not a whole-minute divisor of an hour or a whole-hour divisor of a day, so an annual job needs an explicit cron string) |
| `apps/web/src/panels/BasinPanel.tsx` | render `agreement.reason`; render `headline_drivers` with units and provenance popovers |

**Stage 3 — verification.** Run the §5 exit tests; re-run the three canaries; update
`docs/NEXT_STEPS.md` P3 with the close-out note and the measured costs.

---

## 7. Could not verify / must stay UNKNOWN

**Could not verify this session**

1. **NBM `qmd` retention on NOMADS.** `DATA_SOURCES.md` says 1–2 days; not measured. If the
   worker is down longer than that, the cycle is only recoverable via S3 `.idx` + ranged GET at
   35 MB/cycle. **Mitigation is designed in** (the S3 path is a required fallback), but the
   retention number itself is INFERENCE.
2. **Whether `filter_blend.pl` survives NBM version changes unchanged.** v5.0 landed 2026-05-05;
   the CGI is not versioned in the URL. OPEN QUESTION — the canary must assert message count and
   grid dimensions, not just HTTP 200.
3. **NWPS `/reaches/{id}/streamflow` rate limits and stability.** NWPS publishes none and states
   the API "is not supported 24/7 and may be modified without advance notice". OPEN QUESTION.
4. **Whether NWM `medium_range` member count stays at 6** across NWM versions. Observed 6 today
   (mean + member1…6, member1 at 240 h and members 2–6 at 204 h). The parser must read the member
   list from the payload, never assume 6, and the `fraction` denominator must be the observed
   count.
5. **USGS `observationNormals` discharge coverage.** Verified absent at `USGS-12200500` today;
   whether it appears before WaterServices decommissions in Q1 2027 is an OPEN QUESTION. The
   design does not depend on it.
6. **NKSW1 tidal contamination of daily means.** Ferndale is tidally influenced
   (`HYDROLOGY.md` §2). Whether the USGS daily mean at 12213100 is materially tide-affected was
   not checked. Until it is, the Nooksack susceptibility confidence should be capped at
   `moderate`, not `high`.
7. **Current R2 and Neon consumption.** No credentials in this session, so §8 is *growth*, not
   *total*. The owner should read the actual figures before the first P3 deploy.
8. **AWDB polling policy.** No documented rate limit and no headers; `DATA_SOURCES.md` open item
   27 already asks for an agreed policy with NWCC. One call/day is conservative regardless.
9. **NBM v5.0 absolute cycle timing.** Only deltas are published; the four `Last-Modified`
   observations in §1.1 are a single day's sample, not a schedule (`DATA_SOURCES.md` open item
   12 already owns this).

**Must stay UNKNOWN until X — and the exact `reason` string each should carry**

| Quantity | Stays UNKNOWN until | Reason string to render |
|---|---|---|
| Basin soil-saturation percentile | SMAP L4 root-zone or NWM `land` `SOIL_M` is ingested (ROADMAP Phase 3 proper) | *"No basin soil-moisture product is ingested. SNOTEL SMS is the only mountain soil observation in Washington and returns no climatology, inconsistent depths and `no profile` quality flags at most sites — it cannot support a percentile."* |
| Rain-exposed basin fraction | 3DEP hypsometry per basin exists (`NEXT_STEPS.md` gap 6) | *"Requires basin area-by-elevation (hypsometry), not yet derived. NBM snow level is ingested and shown as a basin-mean elevation."* |
| Rain-on-snow exposed fraction | hypsometry **and** snow-covered area (SNODAS / VIIRS) | *"Requires hypsometry and snow-covered area; neither is ingested."* |
| Agreement at CRNW1 | the NWRFC run carries a flow column, **or** `method:nwps-rating-conversion` ships | *"The NWRFC forecast for CRNW1 carries no flow column (all secondary values are the −999 sentinel); NWM produces flow only."* |
| Category agreement at MVEW1 / NKSW1 / RNTW1 | official flow thresholds are published, **or** rating conversion ships | *"Official flood categories at this point are defined in stage; NWM produces flow. Magnitude and timing are compared; category is not."* |
| Any threshold-crossing **probability** from a Cascade method | hindcast evaluation publishes a reliability diagram (ADR-0008, `TESTING.md` §7) | `HazardState.cascade_index` stays `null`, always |
| Precipitation intensity / duration, IVT, AR scale | Phase 2 grid pipeline at full scope | not surfaced at all in v0 rather than surfaced as UNKNOWN noise |
| Reservoir flood-buffer as a susceptibility mitigator | Phase 4 (USACE CWMS) | not a v0 driver |

---

## 8. Cost roll-up and the one lifecycle decision

| Surface | Ingest/day | R2 growth/month | Neon rows/month | Neon bytes/month | Worker CPU/day |
|---|---|---|---|---|---|
| Forcing | 9.4 MB | ~285 MB | ~15 k | ~4 MB | ~16 s |
| Susceptibility | ~25 KB | ~0.8 MB | ~0.5 k | ~0.1 MB | < 1 s |
| Agreement | 3.8 MB | ~114 MB | ~57 k | ~10 MB | ~2 s |
| **P3 total** | **~13.2 MB/day** | **~400 MB/month** | **~73 k** | **~14 MB/month** | **~20 s/day** |
| One-time | 5.7 MB (climatology backfill) | — | ~2.2 k climatology rows | ~1 MB | ~15 s |

Against the free tiers in play:

- **R2 (10 GB free):** +400 MB/month = **4 %/month**. Unbounded, that is 4.8 GB/year and the free
  tier is gone in about two years. **Recommendation: set an R2 lifecycle rule of 90 days on the
  `nbm/` prefix on day one.** It is a console setting, costs nothing, is explicitly sanctioned by
  `DATA_DOCTRINE.md` §13 for gridded products, and caps the forcing contribution at ~850 MB
  steady-state — total P3 steady state ≈ **1.2 GB**, or 12 % of the free tier, forever. The
  `raw_artifact` row stays; the provenance popover must be able to say *"raw grid expired under
  the 90-day gridded-product retention policy"* rather than 404-ing, so add a
  `retention_class` string column to `raw_artifact` in migration 0002 (nullable; `null` = keep
  indefinitely) and set it to `"gridded-90d"` on NBM artifacts.
- **Neon (free compute, 0.5 GB storage):** P3 adds ~14 MB/month. Worth noting for the owner as a
  *pre-existing* matter, not a P3 one: USGS IV ingestion at 15-minute cadence for six stations ×
  two variables already writes ~138 k observation rows/month (~30 MB), which is the dominant
  consumer. P3 is ~half that.
- **Railway (~$5 Hobby credit):** P3 adds ~20 s of worker CPU per day and no new service. The
  worker **image** grows by ~94 MB from `eccodes` (build-time only). The API image must be built
  without the worker extra so it does not grow — worth an explicit check in the Dockerfile, since
  `infra/Dockerfile` is currently a single image.
- **USGS keyed 4,000 req/h:** P3 adds ~10 requests/day.
- **NOMADS 120 hits/min per IP:** P3 adds 24 requests/day.
- **NWPS:** P3 adds 24 requests/day for reaches plus the existing forecast/threshold jobs.

**Optional lever if the owner wants it smaller still:** gzip JSON payloads at archive time
(`objectstore.put(data, suffix=".json.gz")`, hashing the *original* bytes so content-addressing
and `sha256` semantics are unchanged). JSON compresses roughly 8×, which would take the agreement
path from ~114 MB/month to ~14 MB/month. `DATA_DOCTRINE.md` §13 already specifies raw provider
payloads are held "indefinite, **compressed**", so this closes an existing gap rather than adding
one. Not required for v0.

---

## 9. Sample URLs actually fetched (audit trail)

```
https://noaa-nbm-grib2-pds.s3.amazonaws.com/?list-type=2&delimiter=/&prefix=blend.20260824/12/
https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20260824/18/core/blend.t18z.core.f024.co.grib2.idx
https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20260824/18/core/blend.t18z.core.f024.co.grib2   [Range: bytes=97709842-98855676 → 206]
https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20260824/12/qmd/blend.t12z.qmd.f024.co.grib2.idx
https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20260824/12/qmd/blend.t12z.qmd.f048.co.grib2.idx
https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20260824/12/qmd/blend.t12z.qmd.f072.co.grib2.idx
https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl?dir=%2Fblend.20260824%2F12%2Fqmd&file=blend.t12z.qmd.f072.co.grib2&var_APCP=on&subregion=&toplat=49.40&leftlon=-122.90&rightlon=-120.55&bottomlat=46.70
https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl?dir=%2Fblend.20260824%2F12%2Fcore&file=blend.t12z.core.f024.co.grib2&var_SNOWLVL=on&subregion=&toplat=49.40&leftlon=-122.90&rightlon=-120.55&bottomlat=46.70
https://waterservices.usgs.gov/nwis/stat/?format=rdb&sites=12200500&statReportType=daily&statTypeCd=all&parameterCd=00060      [and 12119000, 12149000, 12213100, 12113000, 12100490, 12189500]
https://api.waterdata.usgs.gov/statistics/v0/openapi.json
https://api.waterdata.usgs.gov/statistics/v0/observationNormals?monitoring_location_id=USGS-12200500&normal_type=DOY
https://api.waterdata.usgs.gov/ogcapi/v0/collections?f=json
https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-daily/items?monitoring_location_id=USGS-12200500&parameter_code=00060&f=json&skipGeometry=true&limit=5
https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?monitoring_location_id=USGS-12200500&parameter_code=00060&statistic_id=00003&f=csv&skipGeometry=true&limit=50000&properties=time,value,approval_status
https://api.waterdata.usgs.gov/docs/ogcapi/migration/
https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?stationTriplets=*:WA:SNTL&activeOnly=true
https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data?stationTriplets=<30 Puget SNTL>&elements=WTEQ&duration=DAILY&beginDate=2026-07-26&endDate=2026-08-24&periodRef=END&centralTendencyType=MEDIAN&returnFlags=true
https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data?stationTriplets=<11 SMS sites>&elements=SMS:*&duration=DAILY&beginDate=2026-08-18&endDate=2026-08-24&periodRef=END&centralTendencyType=MEDIAN&returnFlags=true
https://api.water.noaa.gov/nwps/v1/reaches/24270288
https://api.water.noaa.gov/nwps/v1/reaches/24270288/streamflow?series={short_range,medium_range,medium_range_blend,long_range,analysis_assimilation}
https://api.water.noaa.gov/nwps/v1/gauges/{RNTW1,CRNW1,MVEW1,NKSW1,AUBW1,WRAW1}
https://api.water.noaa.gov/nwps/v1/gauges/{MVEW1,CRNW1,AUBW1,NKSW1,RNTW1,WRAW1}/stageflow/forecast
https://api.water.noaa.gov/nwps/v1/gauges/{MVEW1,CRNW1}/ratings
```

Local verification artifacts (scratchpad, not in the repository): the ranged GRIB2 record,
the four NOMADS WA subsets, the `eccodes` decode transcript, and the basin-mask area measurements.
