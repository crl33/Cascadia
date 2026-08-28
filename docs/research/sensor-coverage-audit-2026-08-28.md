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

**Headline findings.** (1) Pierce County runs a live, keyless **KISTERS KiWIS API**
(`waterquality.piercecountywa.gov`) with 15-minute discharge on the Puyallup mainstem at six
river miles plus the flashy tributaries and the Lake Tapps signals — not in `DATA_SOURCES.md`
at all; the audit's one adapter-grade discovery. (2) NOAA CO-OPS covers Seattle/Tacoma/Cherry
Point at 6-min/8-min latency but has **no station at Everett or in Skagit Bay** — the two most
tide-affected forecast reaches have no observed tide. (3) USACE CDA and A2W both re-verified
live today (~1 h latency; Lake Shannon `SHA.*` = 31 series, its only machine route).
(4) King County and Snohomish County remain closed (APIM key / OneRain login) — unchanged.
(5) Ecology's flow network has no structured live route (an ArcGIS display-string at 2.5–5 h);
its bulk export is 1–2 years stale. (6) WSDOT RWIS is key-gated (free email signup), untestable
keylessly. (7) CoCoRaHS works keyless but is daily/manual — verification-grade, not
operational.

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

Rows are (basin × gap signal) for the eight audited areas only — signals already in
`DATA_SOURCES.md` are not re-listed (their ids appear in `notes` where a gap signal is
redundant with them). `verified` = probed live today. `value` is for the 6–120 h flood
problem per `docs/HYDROLOGY.md`; "verification" in a value string means Phase 6 QPE/forecast
verification, not operational nowcasting.

```json
{
  "audit_date": "2026-08-28",
  "basins": ["skagit", "snohomish-snoqualmie", "cedar", "green-duwamish", "puyallup-white", "nooksack"],
  "rows": [
    {"basin": "cedar", "signal": "lowland_rain_15min", "provider": "King County WLRD HIC", "variable": "precip (15-min), stage", "cadence": "PT15M", "latency": "~PT10M (REPORTED)", "api_route": "none keyless: green2.kingcounty.gov ASP.NET postback only; api.kingcounty.gov/floodwarning/v1 = 401 without APIM key", "ingestion_status": "missing", "value": "high (rain; MRMS bias-check)", "terms": "Public Domain per KC Socrata record pzrb-xkes", "verified": true},
    {"basin": "green-duwamish", "signal": "lowland_rain_15min", "provider": "King County WLRD HIC", "variable": "precip (15-min), stage", "cadence": "PT15M", "latency": "~PT10M (REPORTED)", "api_route": "same as cedar row", "ingestion_status": "missing", "value": "high (rain); stage redundant with H2/H3", "terms": "Public Domain per KC Socrata record", "verified": true},
    {"basin": "snohomish-snoqualmie", "signal": "lowland_rain_15min", "provider": "King County WLRD HIC (WRIA 7 share)", "variable": "precip (15-min)", "cadence": "PT15M", "latency": "~PT10M (REPORTED)", "api_route": "same as cedar row", "ingestion_status": "missing", "value": "medium", "terms": "Public Domain per KC Socrata record", "verified": true},
    {"basin": "cedar", "signal": "county_flood_phase", "provider": "King County floodwarning API", "variable": "derived phase 0-4", "cadence": "~PT10M", "latency": "~PT10M", "api_route": "https://api.kingcounty.gov/floodwarning/v1/river/gauge/ (Ocp-Apim-Subscription-Key required; 401 verified today)", "ingestion_status": "missing", "value": "redundant (derived from USGS/NWS already ingested; display context only per DATA_DOCTRINE §7)", "terms": "county terms, unpublished", "verified": true},
    {"basin": "snohomish-snoqualmie", "signal": "county_gauges", "provider": "Snohomish County / OneRain Contrail", "variable": "county rain+stage sensors", "cadence": "unknown", "latency": "unknown", "api_route": "none public: snohomish.onerain.com 302->/login/ verified today; /export/file/ disabled (errno 412)", "ingestion_status": "missing", "value": "redundant for public display (rides NWPS LIDs already ingested); marginal sensors invisible behind login", "terms": "unknown", "verified": true},
    {"basin": "puyallup-white", "signal": "county_discharge_15min", "provider": "Pierce County SWM (KISTERS KiWIS)", "variable": "discharge ft³/s (15-min), stage; Puyallup RM 6.56-41.18, White RM 7.62-32.86, Carbon, Greenwater, Clearwater, South Prairie Cr, Lake Tapps diversion+flume", "cadence": "PT15M", "latency": "~PT10M-PT30M (observed 22:45Z value at 22:55Z probe)", "api_route": "https://waterquality.piercecountywa.gov/KiWIS/KiWIS?datasource=0&service=kisters&type=queryServices&request=getTimeseriesValues&ts_id=<id>&period=PT6H&format=json (keyless)", "ingestion_status": "possible", "value": "high (mainstem spatial density between NWPS points; flashy tributaries; R13 Lake Tapps signals live)", "terms": "UNVERIFIED (no terms page found)", "verified": true},
    {"basin": "puyallup-white", "signal": "county_rain_15min", "provider": "Pierce County SWM (KiWIS)", "variable": "precip 15-min + 1h/3h/6h/day rollups, 26 current stations", "cadence": "PT15M-PT1H", "latency": "<PT1H (observed)", "api_route": "KiWIS getTimeseriesList stationparameter_name=Precip* -> getTimeseriesValues", "ingestion_status": "possible", "value": "medium (lowland MRMS bias-check)", "terms": "UNVERIFIED", "verified": true},
    {"basin": "nooksack", "signal": "state_flow_live", "provider": "WA Ecology flow network", "variable": "stage+discharge display string (Hutchinson Cr, Bertrand Cr, Dakota Cr)", "cadence": "PT15M timestamps", "latency": "PT2H30M-PT5H (observed)", "api_route": "https://gis.ecology.wa.gov/serverext/rest/services/EAP/FlowMonitoringStations/MapServer/0/query (StationMessage string; keyless)", "ingestion_status": "missing", "value": "low (small creeks, string-scrape, hours late)", "terms": "Ecology non-commercial clause OPEN QUESTION (see G10)", "verified": true},
    {"basin": "skagit", "signal": "state_flow_live", "provider": "WA Ecology flow network", "variable": "stage+discharge display string (Friday Cr, EF Nookachamps Cr, Hansen Cr)", "cadence": "PT15M timestamps", "latency": "PT2H30M-PT5H (observed)", "api_route": "same MapServer query", "ingestion_status": "missing", "value": "low-medium (EF Nookachamps is lower-Skagit backwater context)", "terms": "as above", "verified": true},
    {"basin": "snohomish-snoqualmie", "signal": "state_flow_live", "provider": "WA Ecology flow network", "variable": "stage display string (Snohomish R @ Snohomish PUD, Snoqualmie R nr Monroe)", "cadence": "PT15M timestamps", "latency": "PT2H30M-PT5H (observed)", "api_route": "same MapServer query", "ingestion_status": "missing", "value": "low (mainstem redundant with H2/H3)", "terms": "as above", "verified": true},
    {"basin": "ALL", "signal": "state_flow_archive", "provider": "WA Ecology ContinuousFlowAndWQ export", "variable": "15-min discharge/stage TXT in zip, QC codes", "cadence": "static (published archive)", "latency": "1-2 YEARS (verified: 09B150 15-min ends 2024-10-10)", "api_route": "https://apps.ecology.wa.gov/continuousflowandwq/StationDetails/ExportData?stationCD=<id>&paramArray=_DSG&... (keyless GET, application/zip)", "ingestion_status": "missing", "value": "low operational; medium for hindcast once target water years publish", "terms": "as above", "verified": true},
    {"basin": "ALL", "signal": "road_weather", "provider": "WSDOT RWIS via Traveler API", "variable": "air temp, precip, wind at road/pass stations", "cadence": "UNVERIFIED", "latency": "UNVERIFIED", "api_route": "https://wsdot.wa.gov/Traffic/api/ WeatherInformation + WeatherStations + api/Scanweb; free AccessCode by email form (401/403 keyless, verified)", "ingestion_status": "possible (first keyed weather provider if adopted)", "value": "low-medium (pass-elevation temp for snow-level verification)", "terms": "WSDOT general disclaimer (REPORTED)", "verified": true},
    {"basin": "green-duwamish", "signal": "tide_water_level", "provider": "NOAA CO-OPS Seattle 9447130 (NWLON)", "variable": "water level (MLLW), sigma, quality; predictions for surge anomaly", "cadence": "PT6M", "latency": "~PT8M (verified: 22:54Z value at 23:02Z)", "api_route": "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station=9447130&product=water_level&datum=MLLW&format=json (keyless)", "ingestion_status": "possible", "value": "high (compound tide+flow flooding, lower Duwamish)", "terms": "US Gov public domain", "verified": true},
    {"basin": "puyallup-white", "signal": "tide_water_level", "provider": "NOAA CO-OPS Tacoma 9446484 (PORTS)", "variable": "water level (MLLW)", "cadence": "PT6M", "latency": "~PT8M (verified)", "api_route": "same, station=9446484", "ingestion_status": "possible", "value": "high (lower Puyallup / Commencement Bay)", "terms": "US Gov public domain", "verified": true},
    {"basin": "nooksack", "signal": "tide_water_level", "provider": "NOAA CO-OPS Cherry Point 9449424 (NWLORTS)", "variable": "water level (MLLW)", "cadence": "PT6M", "latency": "~PT8M (verified)", "api_route": "same, station=9449424", "ingestion_status": "possible", "value": "medium (~10 km transfer to Nooksack delta)", "terms": "US Gov public domain", "verified": true},
    {"basin": "skagit", "signal": "tide_water_level", "provider": "NONE (no CO-OPS station in Skagit Bay)", "variable": "n/a — nearest are Port Townsend 9444900 / Friday Harbor 9449880", "cadence": "n/a", "latency": "n/a", "api_route": "n/a", "ingestion_status": "missing (no provider exists)", "value": "gap: Mount Vernon tidal reach needs modeled transfer (predictions/ESTOFS), labeled MODELED", "terms": "n/a", "verified": true},
    {"basin": "snohomish-snoqualmie", "signal": "tide_water_level", "provider": "NONE (no CO-OPS station at Everett)", "variable": "n/a — nearest is Seattle 9447130 ~40 km S", "cadence": "n/a", "latency": "n/a", "api_route": "n/a", "ingestion_status": "missing (no provider exists)", "value": "gap: Snohomish estuary backwater needs modeled transfer, labeled MODELED", "terms": "n/a", "verified": true},
    {"basin": "green-duwamish", "signal": "reservoir_subdaily", "provider": "USACE CDA office=NWDP (Howard Hanson)", "variable": "forebay elev, storage, computed inflow, outflow; 15-min/1-h REV; history 1991->", "cadence": "PT1H (PT15M some)", "latency": "~PT1H (verified: 22:00Z value, last-update 23:01Z)", "api_route": "https://cwms-data.usace.army.mil/cwms-data/timeseries?office=NWDP&name=HAH.*&unit=ft (Accept: application/json;version=2, keyless)", "ingestion_status": "possible", "value": "high (flood-buffer statement; backfills empty SHEF series)", "terms": "US Gov; terms page OPEN QUESTION", "verified": true},
    {"basin": "puyallup-white", "signal": "reservoir_subdaily", "provider": "USACE CDA (Mud Mountain)", "variable": "MMD elev/storage series (8 Elev-Forebay series verified)", "cadence": "PT1H", "latency": "~PT1H", "api_route": "same, like=MMD.*", "ingestion_status": "possible", "value": "high", "terms": "as above", "verified": true},
    {"basin": "skagit", "signal": "reservoir_subdaily", "provider": "USACE CDA (Ross/Diablo/Gorge; Upper Baker UBK 13 series; Lake Shannon SHA 31 series)", "variable": "forebay elev, flows; SHA has NO other machine route (R4: no NWRFC/NWPS station)", "cadence": "PT1H", "latency": "~PT1H", "api_route": "same, like=ROS.*|UBK.*|SHA.*", "ingestion_status": "possible", "value": "medium-high (regulated mainstem + Baker tributary; SHA exclusive)", "terms": "as above", "verified": true},
    {"basin": "cedar", "signal": "reservoir_latest", "provider": "USACE A2W (Chester Morse via `mor`, per R11)", "variable": "latest values + operating levels", "cadence": "PT1H", "latency": "~PT1H (verified at hah today)", "api_route": "https://water.usace.army.mil/cda/reporting/providers/nws/locations/<slug> (keyless, undocumented)", "ingestion_status": "possible", "value": "medium (levels are CONFIGURED context; obs largely redundant with R5 USGS)", "terms": "as above; undocumented API, support OPEN QUESTION", "verified": true},
    {"basin": "ALL", "signal": "community_rain_daily", "provider": "CoCoRaHS", "variable": "24-h precip at morning obs time; snow depth/SWE", "cadence": "P1D", "latency": "hours to >1 day (EntryDateTime lag verified in payload)", "api_route": "https://data.cocorahs.org/cocorahs/export/exportreports.aspx?ReportType=Daily&Format=CSV&State=WA&Date=<M/D/Y> (keyless)", "ingestion_status": "possible", "value": "low operational; medium for daily MRMS/QPE verification (KG 30, SN 23, PR 19, WC 18, SG 18 reports on 2026-08-27)", "terms": "UNVERIFIED (terms page not fetched)", "verified": true}
  ]
}
```

## 10. What could NOT be verified today

- King County: the APIM developer-portal signup path, per-river phase thresholds (cfs), HIC
  history depth and QA semantics — all still OPEN (as in P9/R16); the `GetDischargeInfo` web
  method's parameter contract.
- Snohomish County: anything behind the OneRain login — sensor count, cadence, whether a
  keyed export exists for account holders.
- Pierce County KiWIS: quality-code vocabulary, rate limits, redistribution terms,
  provisional/revision semantics, whether `getGroupList` exposes a curated flood-gauge group.
- Ecology: any structured real-time API (none found — absence of evidence after probing the
  app, its JS, and the ArcGIS layer; not proof none exists); applicability of the
  non-commercial clause to these endpoints.
- WSDOT: everything behind the AccessCode — station inventory, cadence, latency, formats of
  the Scanweb payload.
- CO-OPS: nothing material — the API behaved as documented; ESTOFS surge guidance for the
  Skagit/Snohomish transfer was NOT probed today.
- USACE: rate limits and terms for CDA/A2W (unchanged OPEN QUESTIONs); `RFC-FCST` forecast
  series not re-pulled.
- CoCoRaHS: terms-of-use page; XML and bulk-historic routes.

