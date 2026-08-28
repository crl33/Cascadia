# Label sources for app-owned geographic labels — verification evidence

**Date:** 2026-08-28
**Scope:** Authoritative sources for Washington State place-name labels the app will own:
cities/towns (with population priority), rivers, lakes/reservoirs, mountains/peaks, valleys.
**Method:** Every claim below is tagged VERIFIED (endpoint or page fetched today, 2026-08-28,
URL + probe result recorded), REPORTED (stated by a page fetched today, not independently
confirmed), or UNVERIFIED (could not confirm today). Keyless probes only; no credentials sent.

---

## Verdict (summary)

- **GNIS Domestic Names** lives as bimonthly-refreshed pipe-delimited text on The National
  Map S3 (WA file refreshed today); current format has feature class, county, decimal
  coordinates — **no elevation, no population**. A live keyless queryable API exists
  (carto.nationalmap.gov `geonames` ArcGIS REST service, queried successfully today).
- **City priority**: Census 2025 Gazetteer WA place file (points + legal class, includes
  CDPs) joined on GEOID to Vintage-2025 sub-county estimates (incorporated places only).
  Both are single-URL keyless downloads verified today. The Census *API* now rejects
  keyless requests.
- **Natural Earth**: public domain (verified) but only 16 WA places, missing Bellevue and
  22 of 23 corridor candidates — context fallback only.
- **All 23 corridor candidates are real**: 21 incorporated (20 cities + Concrete town),
  2 CDPs (Fall City, Deming). The three anchor peaks are in GNIS with feature_ids.
- Pipeline: one offline script → one committed provenance-carrying JSON fixture; pin
  feature_ids/GEOIDs, never names (4 different "Baker Lake" rows in WA alone).

## 1. USGS GNIS (Geographic Names Information System)

### 1.1 Distribution: staged text files on The National Map S3 — VERIFIED

The current bulk-download route for GNIS Domestic Names is the National Map staged-products
S3 bucket. Both probes returned HTTP 200 today (curl -I, 2026-08-28):

| File | URL | Probe result |
|---|---|---|
| WA state file | `https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_WA_Text.zip` | 200, **Last-Modified: Fri, 28 Aug 2026 15:28:01 GMT** (refreshed the same day as this probe — the staged files are actively maintained), zip 974,863 bytes |
| National file | `https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_National_Text.zip` | 200, Last-Modified: Fri, 28 Aug 2026 15:27:55 GMT (multipart ETag — larger file) |

VERIFIED by downloading and unzipping the WA file (2026-08-28): the zip contains
`Text/DomesticNames_WA.txt` (pipe-delimited, 3,539,016 bytes, 22,875 lines incl. header,
UTF-8 with BOM) plus an FGDC metadata `.xml` and a thumbnail `.jpg`.

### 1.2 Fields in the current format — VERIFIED (read from the downloaded file, 2026-08-28)

Header of `DomesticNames_WA.txt`, exactly as downloaded today:

```
feature_id|feature_name|feature_class|state_name|state_numeric|county_name|county_numeric|map_name|date_created|date_edited|bgn_type|bgn_authority|bgn_date|prim_lat_dms|prim_long_dms|prim_lat_dec|prim_long_dec|source_lat_dms|source_long_dms|source_lat_dec|source_long_dec
```

So: feature class YES, decimal coordinates YES (`prim_lat_dec`/`prim_long_dec`, plus a
source point for linear features), county YES (`county_name`/`county_numeric`), state YES.
**Absent from the current format: elevation and population.** (The pre-restructure GNIS
format carried `ELEV_IN_M`/`ELEV_IN_FT` and a population column; the file downloaded today
has neither. Peak elevations and city populations must come from elsewhere.)

Feature-class census of the WA file (rows with `state_name = Washington`), counted today:
Stream 6,296 · Lake 3,004 · Populated Place 2,673 · Summit 2,647 · Valley 1,138 ·
Reservoir 483 · Census 416 (CDP-like records) · plus Spring/Civil/Cape/Ridge/Bay/etc.
Everything the label layer needs (populated places, lakes, reservoirs, summits, valleys,
streams) is present as a feature class.

### 1.3 The three anchor peaks — VERIFIED (rows read from the file today)

| feature_id | feature_name | class | county | lat | lon |
|---|---|---|---|---|---|
| 1516062 | Mount Baker | Summit | Whatcom | 48.7766298 | -121.8144732 |
| 1519988 | Glacier Peak | Summit | Snohomish | 48.1117373 | -121.1129474 |
| 1533614 | Mount Rainier | Summit | Pierce | 46.8528267 | -121.7604408 |

No elevation in these rows (see 1.2) — elevations for the three peak labels need a separate
cited source or a one-time manual entry with provenance.

### 1.4 Official route statement — VERIFIED (USGS page fetched 2026-08-28)

`https://www.usgs.gov/us-board-on-geographic-names/download-gnis-data` (fetched today)
directs downloads to The National Map Staged Products Directory
(`https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/GeographicNames/`,
probed 200 today) with folders: DomesticNames (per-state + national TXT), Topical
(Populated Places, Historical Features, Government Units, All Names — TXT), FullModel
(GDB/GPKG), FederalCodes, Antarctica. The page states data products are refreshed every
other month — consistent with the WA file's Last-Modified of today. Topical file probed:
`https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/Topical/PopulatedPlaces_National_Text.zip`
— 200 today, Last-Modified 2026-07-02.

### 1.5 Queryable API today — VERIFIED (probed 2026-08-28)

**Yes — the ArcGIS REST "geonames" service on The National Map is live and queryable,
keyless.** Probes run today:

- Service info: `https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer?f=json`
  → 200; service description says it is The National Map Gazetteer (ANSI INCITS 446-2008)
  based on GNIS.
- Layers (from `/layers?f=json` today): 0 Places (group) · 1 Incorporated Places (Civil) ·
  2 Unincorporated Places (Census) · 3 Populated Places · 4 Physical Points (group) ·
  5 Landforms · 6 Streams (Mouth) · 7 Other Hydrographic Features · 8 Antarctica ·
  9–14 Cultural/Crossings/Historical.
- Layer fields (from `/3?f=json` and `/5?f=json` today): `gaz_id, gaz_name,
  gaz_featureclass, fcode, state_alpha, county_name, shape` (+ OBJECTID bookkeeping).
  Coordinates come back as geometry, not attribute columns.
- Live query, executed today:
  `https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer/5/query?where=gaz_name='Mount Rainier' AND state_alpha='WA'&outFields=gaz_id,gaz_name,gaz_featureclass,county_name&returnGeometry=true&outSR=4326&f=json`
  → `{gaz_id: 1533614, gaz_name: "Mount Rainier", gaz_featureclass: "Summit",
  county_name: "Pierce"}`, geometry `[-121.76045..., 46.85283...]` — matching the staged
  file's row for feature 1533614. A layer-3 query for `Mount Vernon` likewise returned
  gaz_id 1512485 (Populated Place). Caution: requesting a non-existent outField returns a
  bare `400 Failed to execute query` — keep outFields to the schema above.
- The interactive GNIS Domestic Names Search application
  (`https://edits.nationalmap.gov/apps/gaz-domestic/public/search/names`, probed 200 today)
  is an SPA for humans; USGS's download page says it can export up to 2,000 features to CSV
  (REPORTED — export not exercised today). Its `/gaz-record/{id}` path returns the SPA
  shell, not JSON — it is not a keyless JSON API.

### 1.6 GNIS name ambiguity — VERIFIED, and it matters for the fixture

Grepping today's WA file for candidate lake names: **"Baker Lake" appears 4 times**
(a Lake in Kittitas, a Lake in Okanogan, a Lake in Pend Oreille — and the real upper-Baker
impoundment, feature 1516055, class Reservoir, Whatcom, 48.7271/-121.6296) and **"Ross
Lake" twice** (a Lake in Snohomish County at 48.09/-122.23, plus the real one, feature
1525222, class Reservoir, Whatcom). Any pipeline that selects by name will grab the wrong
water body. The fixture must pin `feature_id`s, never names.

Also verified today: the Census Gazetteer's `ANSICODE` for an incorporated place links to
the GNIS **Civil** feature, not the Populated Place — Mount Vernon city has ANSICODE
02411183 → GNIS 2411183 "City of Mount Vernon" (Civil), while the community point is GNIS
1512485 "Mount Vernon" (Populated Place). Same name, two GNIS records, different
coordinates semantics.

## 2. Census Bureau places — population + coordinates

### 2.1 Gazetteer files (coordinates + legal/statistical class) — VERIFIED

The Census "Gazetteer Files" give every place (incorporated cities/towns AND CDPs) with an
internal point. Probed and downloaded today:

- `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_gaz_place_53.txt`
  — 200, text/plain, 65,800 bytes, **pipe-delimited**, 640 lines (639 WA places + header).
- `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_gaz_place_53.txt`
  — 200, 128,630 bytes, tab-delimited (padded). Same 640 lines. The 2025 vintage switched
  from padded tab-delimited to pipe-delimited and added a `GEOIDFQ` column — parse per
  vintage, do not assume a stable delimiter.

2025 header, exactly as downloaded: `USPS|GEOID|GEOIDFQ|ANSICODE|NAME|LSAD|FUNCSTAT|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG`

`NAME` carries the legal/statistical suffix ("Everett city", "Concrete town", "Fall City
CDP"), `LSAD` encodes it (25 = city, 43 = town, 57 = CDP), `ANSICODE` is the GNIS feature
ID linkage, `INTPTLAT/INTPTLONG` is the label point. **No population column** — population
joins on GEOID from the estimates file below.

### 2.2 Population: Vintage 2025 sub-county estimates — VERIFIED

- `https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/cities/totals/sub-est2025.csv`
  — 200 today, text/csv, 7,464,556 bytes. Downloaded and parsed.
- Header: `SUMLEV,STATE,COUNTY,PLACE,COUSUB,CONCIT,PRIMGEO_FLAG,FUNCSTAT,NAME,STNAME,ESTIMATESBASE2020,POPESTIMATE2020..POPESTIMATE2025`.
- Filter `SUMLEV=162, STATE=53` → one row per WA incorporated place; join key is
  STATE+PLACE = gazetteer GEOID.
- Top WA cities by POPESTIMATE2025 (computed from the file today): Seattle 784,777 ·
  Spokane 230,783 · Tacoma 229,816 · Vancouver 199,698 · Bellevue 154,193 · Kent 134,871 ·
  Everett 113,567 · Spokane Valley 108,405 · Renton 104,975 · Federal Way 99,729 ·
  Yakima 97,458 · Kirkland 97,410.

**Limitation, VERIFIED today:** sub-est2025.csv contains incorporated places only — grep for
Fall City and Deming (both CDPs) returns no rows. CDP population needs ACS 5-year
(B01003) or the 2020 Decennial count instead (probe below).

### 2.3 Census API requires a key now — VERIFIED (probed 2026-08-28)

A keyless request to `https://api.census.gov/data/2023/acs/acs5?get=NAME,B01003_001E&for=place:23200&in=state:53`
returned **HTTP 302 with header `X-DataWebAPI-KeyError: 1`, redirecting to
`https://api.census.gov/data/missing_key.html`** (same for the 2024 ACS5 endpoint). So the
Census API is not a keyless route today; the flat files on www2.census.gov (2.1, 2.2) are,
and they are the recommended route. (A free key would unlock the API; not needed for this
pipeline.)

Consequence for the two CDPs (Fall City, Deming): their population is not in
sub-est2025.csv (verified absent today) and the keyless API route is closed. The keyless
decennial fallback exists — `https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/Washington/wa2020.pl.zip`
probed 200 today, application/zip, 36,824,364 bytes — but parsing PL 94-171 segments for
two rows is disproportionate. Recommendation in §5: CDP population = UNKNOWN in the
fixture (legitimate state per doctrine); their inclusion is corridor-driven, not
population-driven.

## 3. Natural Earth populated places — license and suitability

**License — VERIFIED** (`https://www.naturalearthdata.com/about/terms-of-use/`, fetched
2026-08-28): all Natural Earth raster + vector data is stated to be **public domain**; no
permission needed, crediting optional. License is not the problem.

**Content — VERIFIED unsuitable for this app's needs** by downloading
`https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places_simple.zip`
(200 today, 652,145 bytes, Last-Modified **2022-05-13**) and parsing the DBF (7,342 records,
31 fields):

- Washington State has only **16 rows**: Seattle, Tacoma, Vancouver, Everett, Spokane,
  Olympia, Bremerton, Kennewick, Bellingham, Yakima, Longview, Wenatchee, Walla Walla,
  Richland, Aberdeen, Centralia.
- **Missing: Bellevue** (WA's 5th-largest city) and **every one of the 23 flood-corridor
  candidates** except Everett. No Mount Vernon, no Kent, no Renton, no Puyallup.
- `pop_max` values are agglomeration-scale and stale (Seattle 3,074,000; Everett 486,903 —
  the city's Vintage-2025 estimate is 113,567), so they cannot serve as label priority.
- Useful bits if ever needed: `min_zoom`/`scalerank` label-priority hints for world-scale
  basemaps, and public-domain points for non-US context. For WA labels it adds nothing the
  Census/GNIS route doesn't do better.

**Verdict: fine as a global-context fallback, not usable as the WA label source.**

## 4. Candidate flood-corridor towns — existence verification

All 23 candidates verified today against the Census **2025** Gazetteer WA place file
(§2.1) — every one exists as an incorporated place or CDP. `NAME` and coordinates exactly
as in the file; POPESTIMATE2025 joined from sub-est2025.csv (§2.2); CDPs have no estimate
row (UNKNOWN).

| Candidate | Legal/statistical class | GEOID | ANSICODE | INTPT lat, lon | Pop 2025 est |
|---|---|---|---|---|---|
| Mount Vernon | city | 5347560 | 02411183 | 48.417071, -122.311832 | 35,193 |
| Concrete | **town** | 5314380 | 02413237 | 48.532617, -121.755155 | 822 |
| Sedro-Woolley | city | 5363210 | 02411859 | 48.511436, -122.232241 | 13,308 |
| Burlington | city | 5308920 | 02409947 | 48.466355, -122.328882 | 11,356 |
| Monroe | city | 5346685 | 02411137 | 47.859793, -121.984006 | 20,025 |
| Snohomish | city | 5365170 | 02411913 | 47.928866, -122.092684 | 10,719 |
| Everett | city | 5322640 | 02410469 | 47.965413, -122.189895 | 113,567 |
| Duvall | city | 5319035 | 02410377 | 47.735512, -121.972224 | 9,440 |
| Carnation | city | 5310215 | 02409989 | 47.644188, -121.900670 | 2,471 |
| Fall City | **CDP** | 5323200 | 02408111 | 47.569379, -121.913699 | UNKNOWN (no sub-est row) |
| Snoqualmie | city | 5365205 | 02411915 | 47.543245, -121.868645 | 13,640 |
| North Bend | city | 5349485 | 02411270 | 47.487967, -121.768786 | 8,758 |
| Renton | city | 5357745 | 02410926 | 47.479190, -122.194613 | 104,975 |
| Auburn | city | 5303180 | 02409755 | 47.304657, -122.210696 | 86,301 |
| Kent | city | 5335415 | 02410185 | 47.390008, -122.213528 | 134,871 |
| Tukwila | city | 5372625 | 02412106 | 47.476289, -122.275740 | 22,003 |
| Pacific | city | 5352495 | 02411349 | 47.261974, -122.252429 | 7,056 |
| Sumner | city | 5368435 | 02412001 | 47.227215, -122.236264 | 10,871 |
| Puyallup | city | 5356695 | 02411504 | 47.179046, -122.291523 | 42,682 |
| Orting | city | 5352005 | 02411339 | 47.096936, -122.211687 | 8,884 |
| Ferndale | city | 5323620 | 02410498 | 48.853366, -122.590232 | 17,559 |
| Lynden | city | 5340805 | 02410899 | 48.949920, -122.454803 | 16,881 |
| Deming | **CDP** | 5317495 | 02408656 | 48.830359, -122.236134 | UNKNOWN (no sub-est row) |

Major-city anchor set (top WA incorporated places by POPESTIMATE2025, computed from the
file today): Seattle 784,777 · Spokane 230,783 · Tacoma 229,816 · Vancouver 199,698 ·
Bellevue 154,193 · Kent 134,871 · Everett 113,567 · Spokane Valley 108,405 · Renton
104,975 · Federal Way 99,729. (For the western-WA viewport, Kent/Everett/Renton already
overlap the corridor list.)

## 5. Recommended minimal pipeline

One offline script, one committed fixture, zero runtime dependencies. Every label row
carries provenance (source URL, source Last-Modified, retrieval date, source ID).

**Inputs (all verified keyless downloads today):**

1. `2025_gaz_place_53.txt` (Census Gazetteer, §2.1) — the single source for ALL
   city/town/CDP label points and legal class. Pipe-delimited; use `INTPTLAT/INTPTLONG`,
   `NAME`, `LSAD`, `GEOID`.
2. `sub-est2025.csv` (Vintage 2025 estimates, §2.2) — population joined on
   `STATE+PLACE == GEOID` where `SUMLEV=162`; CDPs stay UNKNOWN.
3. `DomesticNames_WA_Text.zip` (GNIS, §1.1) — the single source for physical-feature
   labels: Lake / Reservoir / Summit / Valley (and Stream if river label points are ever
   wanted; river names themselves already exist in the repo).

**Selection:**

- ~10 major cities: top-N of §4's anchor set filtered to the map viewport, priority =
  POPESTIMATE2025.
- Corridor towns: the 23 GEOIDs of §4 pinned explicitly (inclusion is corridor-driven;
  population is priority-within-tier only, so CDP UNKNOWN populations are harmless).
- Lakes/reservoirs, peaks, valleys: pinned GNIS `feature_id` lists (never name matching —
  see §1.6; e.g. Baker Lake must be 1516055, Ross Lake 1525222). Verified-present anchors:
  peaks 1516062 / 1519988 / 1533614 (§1.3); lakes/reservoirs incl. Lake Washington 1531534,
  Lake Sammamish 1531115, Baker Lake 1516055, Lake Shannon 1525616, Ross Lake 1525222,
  Riffe Lake 1528606, Alder Lake 1515791, Mud Mountain Lake 1523486, Spada Lake 1529336,
  Lake Whatcom 1531537 (all read from today's file); valleys "Skagit Valley" and "Puyallup
  Valley" confirmed present in the 1,138-row Valley class (fetch their feature_ids at
  curation time).

**Output:** a static, versioned JSON fixture (e.g. `packages/geo` asset) with, per label:
name, kind (city/town/CDP/lake/reservoir/summit/valley), lat/lon, priority (population or
curated tier), source (`census_gazetteer_2025` / `census_popest_v2025` / `gnis_domestic_wa`),
source id (GEOID or feature_id), source Last-Modified, retrieval date. Peak elevation:
UNKNOWN unless separately cited (GNIS no longer carries it, §1.2).

**Refresh:** manual re-run at most bimonthly (GNIS staged-file cadence) / annually
(Gazetteer + popest vintages). The carto geonames ArcGIS API (§1.5) is for spot
verification only, never a runtime dependency.

**Fit with doctrine:** every displayed label answers where/when/which version via the
fixture's provenance fields; the two CDP populations and the three peak elevations are
honest UNKNOWNs, not fabrications.

## Could not verify (today)

- **CSV export of the GNIS search application** (limit "up to 2,000 features") — REPORTED
  by the USGS download page fetched today; the export itself was not exercised (SPA,
  browser-driven).
- **Peak elevations** — absent from the current GNIS Domestic Names format (verified,
  §1.2); no authoritative machine-readable elevation source was probed today. Needs a
  separate cited source before any elevation is displayed.
- **Fall City / Deming CDP populations** — no keyless machine-readable route verified
  today short of parsing the 36.8 MB PL 94-171 state file (§2.3, existence verified,
  content not parsed). Left UNKNOWN by recommendation.
- **2025 Gazetteer national record-layout documentation page** — the layout above is taken
  directly from the downloaded WA file's header (stronger evidence), but the Census
  reference page describing the 2025 layout was not fetched.
- **Whether `NAME`/`LSAD` semantics changed between vintages** beyond the observed
  delimiter + GEOIDFQ changes — only the 2024 and 2025 WA files were compared (both 640
  lines).
