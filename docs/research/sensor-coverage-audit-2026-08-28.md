# Sensor-coverage audit — six Puget Sound basins — 2026-08-28

Retrieval date for every probe in this file: **2026-08-28**. All probes keyless (no credentials
sent). Labels follow house convention: **VERIFIED** = fetched/probed live today by this audit;
**REPORTED** = claimed by a page fetched today but not independently exercised; **UNVERIFIED** =
could not be confirmed today.

Scope: signals NOT already ingested (see `docs/DATA_SOURCES.md` inventory 2026-08-22, esp. P9
King County HIC, P10 SPU, R16 county flood-warning systems, R1/R2 USACE CDA/A2W, G12 CO-OPS
datums). This file audits the plausible gaps: (1) King County hydrologic data, (2) Snohomish
County flood gauges, (3) Pierce County flood gauges, (4) WA Ecology flow network,
(5) WSDOT RWIS, (6) NOAA CO-OPS tide gauges for tidal reaches, (7) USACE CWMS/A2W beyond the
NWRFC SHEF path, (8) CoCoRaHS community rainfall.

Status: IN PROGRESS — sections are appended as probes complete.

---

## 1. King County hydrologic data (HIC / flood warning)

Basins touched: Cedar, Green-Duwamish, Snohomish-Snoqualmie (King County reaches), Puyallup-White (White below Mud Mountain).

- **VERIFIED 2026-08-28** — `https://green2.kingcounty.gov/hydrology/` is alive: HTTP 200,
  `text/html`, 72,811 B. The HIC has NOT moved to a successor host.
- **VERIFIED 2026-08-28** — `https://green2.kingcounty.gov/hydrology/DataDownload.aspx` is HTTP
  200 (182,083 B). The page's only form `action` is `DataDownload.aspx` itself (ASP.NET
  `__VIEWSTATE` postback); grep of the served HTML found **no** REST/CSV href, no `api/` route.
  Download remains a stateful browser flow — same web-only conclusion as `DATA_SOURCES.md` P9.
- **VERIFIED 2026-08-28** — the ASP.NET page method `POST
  https://green2.kingcounty.gov/hydrology/GaugeMap.aspx/GetDischargeInfo` (Content-Type
  application/json, body `{}`) answers with the ASP.NET error envelope
  `{"Message":"There was an error processing the request."…}` — the web method exists but is an
  undocumented page-internal RPC, not an API (parameter contract unknown, UNVERIFIED).
- **VERIFIED 2026-08-28** — `https://api.kingcounty.gov/floodwarning/v1/rivers` returns HTTP 401
  `application/json`: *"Access denied due to missing subscription key"* (Azure APIM). The keyed
  flood-warning API of R16 is still gated; no public signup route was found today (the
  developer-portal existence is UNVERIFIED).
- **VERIFIED 2026-08-28** — `https://flood.kingcounty.gov/` HTTP 200 (42,451 B) — the phase
  display documented in R16 is still the public face.
- **VERIFIED 2026-08-28** — Socrata record
  `https://data.kingcounty.gov/api/views/pzrb-xkes.json` ("Rain Gage Data", license **Public
  Domain**, attribution King County) is `assetType: "href"` — an external LINK record pointing
  back at the HIC, not hosted data; `viewLastModified` 1613510631 (2021-02-16). Confirms the
  license claim in P9 but provides no machine route.

**Conclusion.** No change since the 2026-08-22 inventory: King County rain/river gauges remain
**missing** from any keyless machine route. The realistic paths are (a) an APIM subscription key
for `api.kingcounty.gov/floodwarning/v1` (derived phases + gauge list, ~10-min cadence per R16),
or (b) a data agreement / bulk export with WLRD (HIC contact listed on the page). Value if
obtained: HIGH for lowland rainfall (densest network in Cedar / Green-Duwamish / Snoqualmie
lowlands, MRMS bias-check) — but the river-stage signal itself is largely REDUNDANT with USGS,
whose gauges King County's own flood phases are derived from (R16, REPORTED 2026-08-22).

## 2. Snohomish County flood warning gauges

Basin touched: Snohomish-Snoqualmie (plus Stillaguamish, outside the six-basin seed).

- **VERIFIED 2026-08-28** — `https://snohomish.onerain.com/` still answers HTTP 302 →
  `/login/?status=300&message=Redirection:+Multiple+Choices` — the OneRain Contrail portal is
  still login-gated at the root, exactly as on 2026-08-22 (R16).
- **VERIFIED 2026-08-28** — the standard Contrail public export route
  `https://snohomish.onerain.com/export/file/?site_id=10&device_id=2&mime=txt` returns a
  Contrail "Page Not Found" HTML (errno 412) — the public data-export feature is disabled on
  this instance, not merely hidden.
- **VERIFIED 2026-08-28** — `https://www.snohomishcountywa.gov/894/River-Levels-Flood-Stages`
  HTTP 200 (102,752 B): the county's public river page. Per R16 (REPORTED 2026-08-22) its gauge
  links point at NWPS LIDs (snaw1, mrow1, glbw1, wchw1), all of which the platform already
  ingests via H3.

**Conclusion.** **No public machine-readable county feed exists** for Snohomish County today;
the county's own public display rides on NWPS gauges already ingested. Ingestion status:
missing, and effectively REDUNDANT unless a Contrail login is granted (the marginal gauges are
county rain/stage sensors not in USGS/NWPS — count and identity UNVERIFIED, invisible behind
the login).

## 3. Pierce County / Puyallup basin flood gauges

Basin touched: Puyallup-White. **This is the audit's headline find: a live, keyless,
documented-protocol machine API not in `DATA_SOURCES.md` at all.**

- **VERIFIED 2026-08-28** — Pierce County Surface Water Management runs a **KISTERS KiWIS**
  water-data portal. Canonical host `https://waterquality.piercecountywa.gov/` (the `.org`
  spelling that circulates 301-redirects there). Service info:
  `https://waterquality.piercecountywa.gov/KiWIS/KiWIS?datasource=0&service=kisters&type=queryServices&request=getrequestinfo&format=json`
  → HTTP 200, `application/json`, "KISTERS QueryServices" **version 1.11.11**, all commands GET
  and POST, no auth, no key.
- **VERIFIED 2026-08-28** — `request=getStationList` → **338 stations** (name, number, id,
  lat/lon in WGS84).
- **VERIFIED 2026-08-28** — `request=getTimeseriesList&stationparameter_name=Precip*` → 253
  precipitation series, **123 current into 2026-08 at 26 stations** (1-h/3-h/6-h/day/month
  rollups plus 15-min published series). `parametertype_name=Q` → 99 discharge series, **70
  current at 30 stations**.
- **VERIFIED 2026-08-28** — Puyallup-White coverage, current to within ~10–30 min of the
  22:55:57Z probe (15-minute cadence, `100.RawData`): PW_PuyallupRiver at river miles 6.56,
  8.61, 10.70, 12.05, 25.67, 41.18; PW_WhiteRiver at RM 7.62, 22.76, 32.86; PW_CarbonRiver
  16.29; PW_GreenwaterRiver 1.34; PW_ClearwaterRiver 2.65; PW_SouthPrairieCreek 6.03 (period of
  record 1987-10-01→today); PW_HuckleberryCreek 1.82; PW_MineralCreek 0.67; PW_ClarksCreek 1.29;
  **PW_LakeTapps_Diversion** and **PW_WhiteRiverFlume** (the R13 Lake Tapps signals, live).
  Some series are dead (PW_WhiteRiver 6.35 ends 2009; 26.78 ends 2003; BoiseCreek ends 2025-05).
- **VERIFIED 2026-08-28** — value shape and units:
  `request=getTimeseriesValues&ts_id=47097010&period=PT6H` returns
  `{ts_id, rows, columns: "Timestamp,Value,Quality Code", data: [["2026-08-28T22:45:00.000Z", 29.2, 3], …]}`;
  units via `returnfields=ts_unitname,ts_unitsymbol`: `cubic foot per second` / `ft³/s`.
  Timestamps are UTC ISO-8601. Quality code `3` observed on every row — the instance's
  quality-code vocabulary was NOT retrieved today (UNVERIFIED; KiWIS exposes
  `request=getQualityCodes` on some instances, untried).
- **UNVERIFIED** — rate limits, redistribution terms, provisional/revision semantics, and
  whether the county considers the feed operationally supported. No terms page was found on the
  KiWIS host today.

**Conclusion.** Ingestion status **missing → possible now** (adapter-grade API, keyless).
Value: **HIGH** for Puyallup-White — mainstem discharge at six river miles plus the flashy
tributaries (South Prairie, Greenwater, Carbon) that bracket the NWPS forecast points, and the
Lake Tapps diversion/return signals R13 currently lists as web-grade. Rain network value MEDIUM
(26 current stations, lowland Pierce County, MRMS bias-check). Overlap warning: several sites
duplicate USGS gauges (e.g. Puyallup at Puyallup) — de-duplicate by location before counting
coverage as new.

## 4. WA Ecology river & stream flow monitoring

- **VERIFIED 2026-08-28** — the legacy network home `https://fortress.wa.gov/ecy/eap/flows/regions/state.asp`
  301-redirects to the new app `https://apps.ecology.wa.gov/continuousflowandwq/` (HTTP 200).
  Station pages: `/continuousflowandwq/StationDetails?sta=<id>`; WRIA station lists verified
  today: WRIA 03 Lower Skagit-Samish 9 stations, **WRIA 04 Upper Skagit 0**, WRIA 07 Snohomish
  9 (incl. co-op 12155500), WRIA 08 Cedar-Sammamish 3, WRIA 09 Duwamish-Green 4, WRIA 10
  Puyallup-White 5.
- **VERIFIED 2026-08-28** — bulk export is a plain keyless GET:
  `https://apps.ecology.wa.gov/continuousflowandwq/StationDetails/ExportData?stationCD=09B150&isAllYears=false&isAllParams=false&startYear=2026&endYear=2026&paramArray=_DSG&paramArray=_STG&SplitWaterYears=false`
  → HTTP 200 `application/zip` (1.04 MB) containing `09B150_DSG_FM.TXT` (15-minute discharge),
  `_DSG_DV.TXT` (daily), `_STG_*` (stage), HYDAY monthly tables, chart PNGs, and a README PDF.
  Quality codes in-file (1 good reviewed, 10 above rating, 140 not yet checked, 255 incomplete
  day). Param codes observed: `_DSG` discharge, `_STG` stage, `_PCP` precip, `_ATM` air temp,
  `_WTM`, `_CND`, `_DSO`, `_PH`.
- **VERIFIED 2026-08-28** — **the export is an archive, not a live feed**: for 09B150 (Big Soos
  Cr) the newest 15-minute row is `10/10/2024 10:30` and the newest daily row Sep 2025 — one to
  two YEARS behind, published after QC.
- **VERIFIED 2026-08-28** — the only live machine route found is the ArcGIS layer behind the
  station map:
  `https://gis.ecology.wa.gov/serverext/rest/services/EAP/FlowMonitoringStations/MapServer/0/query`
  (keyless, `f=json`). `FlowMonitoring=1 AND Status='Active'` → **83 active telemetry flow
  stations statewide, only 8 in the six seed-basin WRIAs** (01C070 Hutchinson Cr, 01N060
  Bertrand Cr, 01Q070 Dakota Cr, 03C060 Friday Cr, 03G100 EF Nookachamps Cr, 03J100 Hansen Cr,
  07A090 Snohomish R @ Snohomish PUD, 07D050 Snoqualmie R nr Monroe). Latest values arrive as an
  HTML display STRING (`StationMessage`: "Latest values as of 8/28/2026 1:30:00 PM: … Stage =
  0.89ft. Discharge = 2.5cfs …") — 15-minute timestamps, observed ~2.5–5 h behind the 22:55Z
  probe. Structured per-value JSON does not exist on any route probed today.
- **UNVERIFIED** — no documented real-time API, no rate limits, no terms for the app/ArcGIS
  routes; note `DATA_SOURCES.md` G10 records Ecology's site-wide **non-commercial clause** as an
  OPEN QUESTION, which presumably attaches to these servers too.

**Conclusion.** Ingestion status **missing**; value **LOW for 6–120 h flood prediction**
(archive export is years stale; the live route is a display string at 2–5 h latency covering 8
mostly small-creek stations in-domain). The one genuinely interesting signal is **03G100 EF
Nookachamps** (lower-Skagit backwater area) and the two lowland Nooksack creeks — worth a
watch-list note, not an adapter. Re-evaluate if Ecology ships a structured API.

## 5. WSDOT RWIS road-weather stations

- **VERIFIED 2026-08-28** — the Traveler Information API portal `https://wsdot.wa.gov/Traffic/api/`
  is HTTP 200 and lists three weather interfaces: **WeatherInformation**, **WeatherStations**,
  and "More Weather Information" at an `api/Scanweb` path (Scanweb = the RWIS network).
- **VERIFIED 2026-08-28** — keyless probes are refused:
  `…/WeatherInformation/WeatherInformationREST.svc/GetCurrentWeatherInformationAsJson?AccessCode=`
  → HTTP 401 "The supplied access code was missing or invalid";
  `…/WeatherStations/WeatherStationsREST.svc/GetCurrentStationsAsJson?AccessCode=` → 401;
  `https://wsdot.wa.gov/traffic/api/api/Scanweb?AccessCode=` → HTTP 403 (controller exists,
  refuses without code; the shorter `/traffic/api/Scanweb` is 404).
- **REPORTED 2026-08-28** (portal page, fetched today) — the access code is free and issued by
  an automated email form ("enter your email address to receive your code"); terms are a general
  WSDOT disclaimer, no redistribution text found on the portal.
- **UNVERIFIED** — station count, cadence, latency, and variable list for the Puget passes
  (Snoqualmie, Stevens, Cayuse/Chinook, SR-542 Mt Baker) — cannot be checked without a key.
  RWIS data also flows into Synoptic (`DATA_SOURCES.md` P5, commercial-token, open question).

**Conclusion.** Ingestion status **possible** (free key, trivially obtained, but a key
nonetheless — the platform's first keyed weather provider if adopted). Value **LOW-MEDIUM**:
pass-elevation air temperature/precip could sharpen snow-level verification (`method:basin-snow-level`),
but NBM/SNOTEL/ASOS already triangulate that; RWIS adds mid-elevation road-corridor points the
other networks miss (e.g. US-2 Stevens corridor for Skykomish, SR-410 for the White). Not a
flood signal by itself.

## 6. NOAA CO-OPS tide gauges for tidal reaches

- **VERIFIED 2026-08-28** — station inventory
  `https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=waterlevels` →
  **16 active WA water-level stations**. The Puget Sound set relevant to the six basins:
  **Seattle 9447130** (NWLON — Duwamish estuary / Green-Duwamish tidal reach), **Tacoma
  9446484** (PORTS — Commencement Bay / Puyallup mouth), **Cherry Point 9449424** (NWLORTS —
  nearest to the Nooksack delta, ~10 km west of the Ferndale reach), plus Port Townsend 9444900,
  Friday Harbor 9449880, Bremerton 9445958 as regional context.
- **VERIFIED 2026-08-28** — the honest negative: **there is NO active CO-OPS station at Everett
  (Snohomish estuary) and NONE in Skagit Bay** — the two seed basins with the strongest
  tide-backwater interaction at their forecast points (Snohomish at Snohomish, Skagit at Mount
  Vernon) have no local observed tide. The nearest gauges (Seattle, resp. Port Townsend/Cherry
  Point) require a tide-model transfer (subordinate-station offsets or ESTOFS surge) before any
  backwater statement is made.
- **VERIFIED 2026-08-28** — data API live and keyless: `…/api/prod/datagetter?station=9447130&product=water_level&datum=MLLW&time_zone=gmt&units=english&date=latest&format=json`
  → Seattle `8.348 ft MLLW at 2026-08-28 22:54Z` (probe 23:02Z → **~8 min latency, 6-minute
  cadence**, sigma + quality flags in-row, `q:"p"` preliminary). Same shape verified for Tacoma
  (8.678 ft) and Cherry Point (5.164 ft).
- Datum context already in the registry: G12 holds Seattle/Tacoma NAVD88↔MLLW offsets (FACT,
  2026-08-22); CO-OPS `datums.json` per station converts to the NAVD88 frame the gauges use.

**Conclusion.** Ingestion status **missing → possible** (known-good federal API, public
domain). Value: **MEDIUM-HIGH for Green-Duwamish and Puyallup-White lowland flooding**
(coincident high-tide + high-flow is the compound-flood mode for the Duwamish and lower
Puyallup), **MEDIUM for Nooksack** (Cherry Point transfer), **indirect for Skagit/Snohomish**
(no local gauge — the value there is prediction + surge anomaly transferred, and that must be
labeled MODELED, not OBSERVED). Cadence PT6M, latency ~8 min, `product=predictions` gives the
astronomical baseline so the surge anomaly (obs − pred) is computable per doctrine.

## 7. USACE reservoir data beyond NWRFC SHEF

`DATA_SOURCES.md` R1 (CWMS Data API) and R2 (A2W) were "researched, independent verification
pending" as of 2026-08-22. This audit re-exercised both keylessly today — **both pass**.

- **VERIFIED 2026-08-28** — CDA catalog:
  `https://cwms-data.usace.army.mil/cwms-data/catalog/TIMESERIES?office=NWDP&like=HAH.Elev-Forebay.*`
  (with `Accept: application/json;version=2`) → HTTP 200; `HAH.Elev-Forebay.Ave.1Hour.1Hour.IRIDIUM-REV`
  extents `2024-10-15 → 2026-08-28T22:00Z`, `last-update 2026-08-28T23:01:37Z` — i.e. the
  22:00Z hour landed at 23:01Z (**~1 h publication latency**, matching R1's estimate). Catalog
  default units still SI (`m`) — R1's "always set `unit`" rule still required.
- **VERIFIED 2026-08-28** — CDA timeseries:
  `…/timeseries?office=NWDP&name=HAH.Elev-Forebay.Ave.1Hour.1Hour.IRIDIUM-REV&begin=2026-08-28T00:00:00Z&end=2026-08-28T23:00:00Z&timezone=UTC&unit=ft`
  → 23 rows, `[epoch_ms, value, quality]`, last `2026-08-28T22:00Z = 1154.13 ft`, quality 0.
- **VERIFIED 2026-08-28** — project coverage by catalog count (office=NWDP): `ROS.Elev-Forebay.*`
  5 series (Ross), `UBK.*` 13 (Upper Baker), `SHA.*` **31 (Lake Shannon / Lower Baker — the
  project R4 records as having NO NWRFC/NWPS station; CDA is its only machine route)**,
  `MMD.Elev-Forebay.*` 8 (Mud Mountain).
- **VERIFIED 2026-08-28** — A2W:
  `https://water.usace.army.mil/cda/reporting/providers/nws/locations/hah` → HTTP 200, no
  Accept header needed; returns project metadata (NIDID WA00298, vertical_datum NGVD29) plus
  per-series latest values (`HAH.Flow-In…COMPUTED-REV` = 158.46 cfs at 2026-08-28T22:00Z,
  `delta24hr` included). Still undocumented (OPEN QUESTION on support stands).
- **UNVERIFIED today** — rate limits and data-use terms for both routes (R1/R2 OPEN QUESTIONs
  unchanged); the `RFC-FCST` forecast series were not re-pulled today.

**Conclusion.** Ingestion status: NWRFC SHEF observations already ingest (R4); the CDA/A2W
routes are **missing but adapter-ready**, and their marginal value over R4 is concrete:
15-min/1-h REV series with decades of history, **storage and computed inflow**, quality codes,
operating levels (A2W), and the only machine route for **Lake Shannon (SHA)** and sub-daily
Baker data. Several R4 series were measured EMPTY on capture day (DIAW1 entirely) — CDA is the
natural backfill. Value **HIGH** for Green-Duwamish (HAH) and Puyallup-White (MMD) flood-buffer
statements, **MEDIUM-HIGH** for Skagit (ROS/UBK/SHA regulate the mainstem and the Baker
tributary).

## 8. CoCoRaHS community rainfall

- **VERIFIED 2026-08-28** — the CSV export is live and keyless:
  `https://data.cocorahs.org/cocorahs/export/exportreports.aspx?ReportType=Daily&dtf=1&Format=CSV&State=WA&ReportDateType=reportdate&Date=08/27/2026&TimesInGMT=False`
  → HTTP 200 `text/csv`, 269 WA daily reports for 2026-08-27; columns ObservationDate/Time,
  EntryDateTime, StationNumber, name, lat/lon, TotalPrecipAmt (in), snow depth/SWE, timestamp.
- **VERIFIED 2026-08-28** — Puget-county density that day (StationNumber prefix): King (WA-KG)
  30, Snohomish (WA-SN) 23, Pierce (WA-PR) 19, Whatcom (WA-WC) 18, Skagit (WA-SG) 18.
- **VERIFIED 2026-08-28** (in the same payload) — the noise character: observation times are
  observer-chosen mornings (04:10–07:00 local seen), and `EntryDateTime` shows some reports
  entered a day and a half after observation — knowledge time is entry time, not obs time.
- **UNVERIFIED** — redistribution/terms page not fetched today; XML variant and historic bulk
  routes untested.

**Conclusion.** Value **LOW for the 6–120 h operational problem** (daily cadence, morning-only,
entry lag, manual gauges) — MRMS QPE (ingesting) plus the telemetered county networks dominate
it for nowcasting. Its real use is **daily-scale MRMS/QPE bias verification** with ~100+
independent points across the six basins per storm day — a Phase 6 verification asset, not a
Phase 2/3 ingest. Judgment: skip now; note for the verification harness.

## 9. Coverage matrix (JSON)

(pending)

## 10. What could NOT be verified today

(pending)
