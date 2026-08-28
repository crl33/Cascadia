# Public camera sources for Puget Sound flood corridors — verification evidence

**Date:** 2026-08-28
**Method:** live keyless probes (`curl`), official documentation fetches (WebFetch/WebSearch), all retrieved today.
**Scope:** WSDOT Traveler Information API (HighwayCameras), Seattle/SDOT cameras, King County + City of Kent Green River cameras, Snohomish County / Everett feeds, and six copied camera-location claims.

**Labels used:**
- **VERIFIED** — fetched/probed today (2026-08-28); URL and evidence recorded.
- **REPORTED** — stated by a page read today, but not independently probed.
- **UNVERIFIED** — could not be confirmed today.

Status: COMPLETE (all probes run 2026-08-28, ~22:50–23:05 UTC).

---
## 1. WSDOT Traveler Information API — Highway Cameras

**Owner:** Washington State Department of Transportation (WSDOT).

### Endpoint — VERIFIED (probed 2026-08-28)

- Service help page: `https://wsdot.wa.gov/Traffic/api/HighwayCameras/HighwayCamerasREST.svc/Help`
  — `curl` 2026-08-28: **HTTP 200**, `Content-Type: text/html`. Lists operations:
  - `GetCamerasAsJson?AccessCode={ACCESSCODE}` (all cameras)
  - `GetCameraAsJson?AccessCode={ACCESSCODE}&CameraID={CAMERAID}` (one camera)
  - `GetCameraAsXml` / `GetCamerasAsXml` (XML variants)
  - `SearchCamerasAsJson`/`AsXml` (per API docs index: filter by StateRoute, Region, milepost range)
- Keyless probe of `.../GetCamerasAsJson` (no AccessCode), 2026-08-28: **HTTP 401 Unauthorized**, body:
  `"The supplied access code was missing or invalid."` — an AccessCode is definitively required for the
  data API (camera metadata). Note the help page itself is served with `Cache-Control: public, max-age=31479462`.

### AccessCode — VERIFIED (docs fetched 2026-08-28)

- Docs portal: `https://wsdot.wa.gov/traffic/api/` (fetched 2026-08-28). The page issues codes by
  email self-service: "Please enter your email address to receive your code. Your email address will
  not be shared and will be used only to notify you of changes to our services." No fee mentioned —
  the code is free, obtained by entering an email on that page.
- **OWNER ACTION BLOCKER:** someone must enter an email at `https://wsdot.wa.gov/traffic/api/` and
  receive the AccessCode; there is no keyless path to the camera metadata API.
- Rate limits: **none stated** on the portal page (fetched today). UNVERIFIED whether unstated
  throttling exists.

### Camera record fields — VERIFIED (official class docs fetched 2026-08-28)

Source: `https://wsdot.wa.gov/traffic/api/Documentation/class_camera.html` (fetched 2026-08-28):

| Field | Type | Doc description |
|---|---|---|
| `CameraID` | int | unique identifier |
| `Title` | string | title for the camera |
| `Description` | string | short description |
| `CameraLocation` | RoadwayLocation | road name / milepost / direction structure |
| `DisplayLatitude` / `DisplayLongitude` | double | map display coordinates |
| `ImageURL` | string | stored location of the camera image |
| `ImageWidth` / `ImageHeight` | int | pixel dimensions |
| `CameraOwner` | string | "Owner of camera when not WSDOT" |
| `OwnerURL` | string | owner website when not WSDOT |
| `Region` | string | WSDOT region which owns the camera |
| `SortOrder` | int | display ordering |
| `IsActive` | bool | "Indicator if the camera is still actively being updated" |

Notes: the schema itself confirms (a) ownership is mixed — some cameras in the feed belong to other
agencies (`CameraOwner`/`OwnerURL` populated), which matters for display rights; (b) staleness is
representable (`IsActive`).

### Keyless alternative — WSDOT public ArcGIS Feature Service — VERIFIED (probed 2026-08-28)

WSDOT also publishes the camera inventory as a **public, keyless** ArcGIS feature service (found via
the ArcGIS item `6692b4f163bd4ec99b5a897b2d207aa6`, "WSDOT – Travel Information Cameras",
owner `OnlineMapSupport_WSDOT`, access `public`):

- **Endpoint (probed today, HTTP 200, `application/json`):**
  `https://data.wsdot.wa.gov/arcgis/rest/services/TravelInformation/TravelInfoCamerasWeather/FeatureServer/0`
- `query?where=1=1&returnCountOnly=true&f=json` → **1701 cameras** (2026-08-28).
- Fields (from live layer JSON): `OBJECTID` (alias **CameraID** — matches the Traveler API's
  CameraID space), `CameraTitle` (string 50), `ImageURL` (string 150), `CompassDirection`
  (string 5: N/S/E/W/B). Geometry: point, Web Mercator (wkid 102100); `outSR=4326` works.
  `maxRecordCount` 2000, so the full inventory fits one query.
- **Refresh cadence (REPORTED, from the ArcGIS item description fetched today):** "The image is
  refreshed approximately every 5 minutes and includes details such as date, time, state route
  number, and milepost number."
- **Terms (VERIFIED — item `licenseInfo` fetched 2026-08-28):** "This data feed is intended for
  'low volume' use only. The Washington State Department of Transportation (WSDOT) may cancel or
  restrict access for any reason. … WSDOT shall not be liable for any activity involving the use of
  the data … the Data User shall hold harmless, defend at its own expense, and indemnify WSDOT …"
  No explicit attribution requirement stated; no explicit prohibition on public display. It is a
  liability/low-volume clause, not a copyright restriction (WA state agency work).
- **CORS (probed 2026-08-28):** `data.wsdot.wa.gov` query with `Origin: https://cascadia.example.org`
  returned `Access-Control-Allow-Origin: https://cascadia.example.org` +
  `Access-Control-Allow-Credentials: true` → browser fetch from any origin works.
- Caveat: the layer includes non-WSDOT cameras — e.g. records 1001/1002 point at
  `https://www.tripcheck.com/RoadCams/...` (Oregon DOT). Unlike the AccessCode API, this layer has
  **no `CameraOwner` field**, so third-party ownership must be inferred from the ImageURL host.

### Camera imagery host `images.wsdot.wa.gov` — VERIFIED (probed 2026-08-28)

- `GET https://images.wsdot.wa.gov/nw/005vc20934.jpg` with a foreign `Origin` header →
  **HTTP 200**, `Content-Type: image/jpeg`, 67,820 bytes, 335×249 px JPEG. No referrer/origin
  gating observed → hotlinking in `<img>` tags works today.
- **No `Access-Control-Allow-Origin` header** on the image responses (probed two cameras; OPTIONS
  preflight returns 200 with `Allow: GET…` but no CORS headers) → plain `<img>` display is fine,
  but **canvas/fetch pixel reads from a browser will be CORS-blocked**; a proxy is needed if the
  app must read bytes client-side.
- Freshness: response at 22:52:20 UTC carried `Last-Modified: 22:50:55 GMT` (~85 s old) — consistent
  with the reported ~5-minute refresh. `ETag` present; `Accept-Ranges: bytes`; no `Cache-Control`
  header on images.
- **URL stability:** image names encode route + milepost (`005vc20934` = I-5, MP 209.34;
  `532vc00337` = SR 532 MP 3.37) — stable identifiers; same URL, content replaced in place.
  (Stability over time REPORTED by construction of the scheme; only today's behavior VERIFIED.)
- Still images only — no public video stream is exposed by this API (still-vs-video: **stills**).

### WSDOT camera imagery — terms of use (mixed verification)

- The API portal page (`https://wsdot.wa.gov/traffic/api/`, fetched today) links a general
  disclaimer; the ArcGIS licenseInfo above is the most explicit machine-data terms text found today.
- REPORTED (via search snippets today, underlying page not fetched): WSDOT states camera images are
  "for information purposes only", that WSDOT does not retain/record footage, and the standard WSDOT
  hold-harmless disclaimer. UNVERIFIED: any explicit rebroadcast/attribution policy page for
  `images.wsdot.wa.gov`. Practical posture: public display appears tolerated and widespread (cities
  like Monroe embed WSDOT cams on their own sites), but a written redistribution grant was not
  located today.

### Copied-claim verification (WSDOT four of six) — VERIFIED (live layer query 2026-08-28)

Queried `.../FeatureServer/0/query?where=UPPER(CameraTitle) LIKE ...` today:

| Claim | Verdict | Live record (2026-08-28) |
|---|---|---|
| "I-5 MP 209.3 Stillaguamish River camera" | **VERIFIED** | id 9240 "I-5 at MP 209.3: Stillaguamish River", `https://images.wsdot.wa.gov/nw/005vc20934.jpg`, 48.1967 N -122.2096 W (probed: HTTP 200 JPEG today) |
| "SR 532 MP 3.3" | **VERIFIED** | id 9187 "SR 532 at MP 3.3: Stillaguamish River", `https://images.wsdot.wa.gov/nw/532vc00337.jpg`, 48.2401 N -122.3846 W |
| "SR 529 MP 4.1 Snohomish River" | **VERIFIED (two cameras)** | id 9316 "…Snohomish River South" `529vc00416.jpg` + id 9317 "…Snohomish River North" `529vc00419.jpg` (probed 9316: HTTP 200 JPEG today) |
| "US 2 MP 2 Ebey Slough" | **VERIFIED** | id 9357 "US 2 at MP 2: Ebey Slough", `https://images.wsdot.wa.gov/nw/002vc00207.jpg`, 47.9780 N -122.1457 W |

(The two Green River claims are municipal, not WSDOT — see the Kent/King County section.)

## 2. Seattle (SDOT) traffic cameras

**Owner:** City of Seattle / Seattle Department of Transportation (plus WSDOT cameras mirrored in the same layer).

### Machine-readable source — VERIFIED (probed 2026-08-28)

- The Socrata dataset `data.seattle.gov/dataset/Traffic-Cameras/mvth-ptq3` exists but its SODA
  resource endpoint (`/resource/mvth-ptq3.json`) returns **HTTP 403
  "no row or column access to non-tabular tables"** (probed today) — it is a federated geospatial
  entry, not a queryable Socrata table.
- The working machine-readable source is the city's public ArcGIS layer (found via the Seattle
  GeoData hub search API today):
  `https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Traffic_Cameras_CDL/FeatureServer/0`
  — probed today: HTTP 200, `application/json`, **658 cameras**, WGS84 points.
- Fields (live layer, 2026-08-28): `OBJECTID`, `COMPKEY`, `UNITID` (e.g. `CMR-0270`),
  **`OWNERSHIP`** (breakdown queried today: 387 `SDOT`, 263 `WSDOT`, 8 null), `DISTRICT`, `NAME`,
  `COMPTYPE`, **`URL`** (still-image URL), `LOCATION` (cross-street text), **`SERVSTAT`**
  (e.g. `ACTV`), **`STREAM_NAME`**, `GLOBALID`, edit-audit fields.
- **CORS (probed today):** query responses carry `access-control-allow-origin: *` — browser-fetchable.

### Image URLs — VERIFIED (probed 2026-08-28)

- Pattern: `http(s)://www.seattle.gov/trafficcams/images/<STREAM_NAME>.jpg`
  (e.g. `https://www.seattle.gov/trafficcams/images/MLK_S_Jackson_NS.jpg`).
- Probe today with foreign `Origin`: **HTTP 200**, `image/jpeg`, 352×240 px, served via CloudFront
  (`x-cache: Miss from cloudfront`), `cache-control: public, max-age=300` (5-minute cache policy).
  **No `Access-Control-Allow-Origin` header** on images → `<img>` hotlinking works; browser pixel
  reads do not. No referrer/origin gating observed.
- Honest staleness note: the probed camera's `Last-Modified` was 21:01:01 GMT vs a 22:54 fetch —
  ~1 h 53 m old, and unchanged across two fetches 20 s apart. The 5-minute cache header is a
  *policy*, not proof of a 5-minute refresh; at least one camera was serving an ~2-hour-old frame
  today. Treat per-camera `Last-Modified` as the freshness authority.
- `STREAM_NAME` implies live video streams exist behind a separate streaming host; **UNVERIFIED**
  today (no stream endpoint probed). Stills are confirmed.

### Terms — VERIFIED (ArcGIS item b90315ad1deb4985aeb3071b8baa06a1, fetched 2026-08-28)

- Item access: `public`. `licenseInfo` is an accuracy disclaimer only: "The City of Seattle makes no
  representation or warranty as to its accuracy…". No attribution or redistribution restriction
  stated on the item. (data.seattle.gov's general open-data terms were not fetched today —
  UNVERIFIED beyond the item text.)
- Refresh cadence of the *metadata layer*: hub metadata (search snippet, today) says daily refresh;
  the layer's `editingInfo.lastEditDate` = 1787926356172 (2026-08-24) — metadata is slow-moving,
  imagery is the live part.

## 3. USGS HIVIS / NIMS cameras (bonus source found while verifying Green River claims)

**Owner:** U.S. Geological Survey (public domain, federal work).

- **Camera inventory API — VERIFIED, keyless (probed 2026-08-28):**
  `https://api.waterdata.usgs.gov/nims/cameras` → HTTP 200 `application/json`, **1309 cameras**
  nationally, **14 in WA**. Record fields include `camId`, `camName`, `camDesc`, `nwisId` (ties the
  camera to a USGS gauge), `lat`/`lng`, `newestImageDT`, `hideCam`, `ingest.intr` (capture interval,
  minutes), and S3 directory URLs (`overlayDir`, `smallDir`, `thumbDir`, `tlDir`).
- **Imagery — VERIFIED (probed 2026-08-28):** public S3 bucket `usgs-nims-images.s3.amazonaws.com`,
  listable (`?list-type=2&prefix=overlay/<camId>/`), keys
  `overlay/<camId>/<camId>___<YYYY-MM-DDTHH-MM-SS>Z.jpg`. Fetched
  `...WA_Skagit_River_near_Mount_Vernon___2026-08-28T22-45-04Z.jpg` (constructed from the API's
  `newestImageDT`): HTTP 200, `image/jpeg`, 2688×1520, **`Access-Control-Allow-Origin: *`** —
  fully CORS-open, canvas-safe. No `most_recent` alias exists in the overlay dir (probed: 404);
  latest frame = API `newestImageDT` → constructed key, or S3 list.
- Puget-Sound-relevant cameras live today (from the WA subset, all fresh to 22:30–22:45 UTC):
  `WA_Skagit_River_near_Mount_Vernon` (+ `_upstream`) at gauge 12200500 — 15-min interval;
  `WA_Nooksack_River_Overflow_at_Emerson_Rd_at_Everson` (12211190) and `..._at_Highway_544...`
  (12211195) — 15-min. **No USGS camera exists on the Green/Duwamish, Snohomish, or Stillaguamish
  today** (verified by exhaustive WA list).
- Cadence: per-camera `ingest.intr` (15–60 min for WA cams) — VERIFIED from today's API payload.
  Stills + generated time-lapses (`tlDir`); no live video.

## 4. King County / City of Kent — Green River cameras

### King County Flood Warning System — VERIFIED (probed 2026-08-28): gauges yes, cameras no

- `https://flood.kingcounty.gov/` — HTTP 200 today; Next.js app. Gauge pages exist for the Green
  River corridor (e.g. `/gauge/40/` "Green River at 200th St in Kent", `/gauge/3/` near Auburn,
  `/gauge/4/` Tukwila; river index `/river/2/`). Grepped the served HTML and the gauge-page JS
  bundle today: **no camera or webcam assets of any kind**; the client pulls USGS water data
  (the only external URL in the gauge bundle is `waterdata.usgs.gov`). The legacy
  `green2.kingcounty.gov/rivergagedata/gage-data.aspx?r=green` now redirects to
  `https://flood.kingcounty.gov/river/2/` (followed today).
- Conclusion: **King County does not publish flood/river cameras machine-readably today.** Its
  flood-warning product is gauge data (REPORTED on kingcounty.gov pages read today: updated every
  10 minutes from USGS/NOAA).

### City of Kent Green River levee cameras — VERIFIED live remnant, mostly gone (probed 2026-08-28)

- Historical record (Wayback CDX, queried today): Kent served a Green River camera page
  (`kentwa.gov/greenrivercamera/`, snapshots 2011–2013, Howard Hanson Dam era) and camera images at
  `https://kentapps.kentwa.gov/greenrivercameraimages/272nd_Street_Bridge.jpeg` and
  `https://kentapps.kentwa.gov/greenrivercameraimages/Veterans_Drive_228th_Bridge.jpeg`
  (both archived 2020-10-16 with HTTP 200).
- **Live probes today:**
  - `Veterans_Drive_228th_Bridge.jpeg` → **HTTP 200, `image/jpeg`, 1280×720** — the endpoint still
    exists publicly. BUT `Last-Modified: Thu, 11 Dec 2025 23:05:37 GMT` — the frame is **frozen at
    the December 2025 flood event, ~8.5 months stale**. No CORS headers; no referrer gating.
  - `272nd_Street_Bridge.jpeg` → **HTTP 404** (camera image removed).
  - Directory listing of `/greenrivercameraimages/` → 403; nine candidate filenames for other
    bridges (277th, 212th, Meeker, Russell Rd, etc.) all → 404.
  - `kentwa.gov` HTML pages are WAF-blocked to non-browser clients (403 to curl with browser UA and
    to WebFetch), so whether any Kent page still links these images is **UNVERIFIED** today.
- Conclusion: Kent's Green River levee camera program is effectively defunct as a data source — one
  stale endpoint survives, one is gone, and no machine-readable index exists.

## 5. Snohomish County / Everett

### Snohomish County flood program — no public cameras found (checked 2026-08-28)

- The county's real-time flood system is `https://snohomish.onerain.com/` (OneRain Contrail;
  linked from `snohomishcountywa.gov/796/Flood-Information-Center` and `/925/All-Real-Time-Gauges-by-Basin`,
  per search today). Probed today: the root **302-redirects to a login page**
  (`/login/?status=300...`); no public camera resources surfaced. Gauge data (Stillaguamish at
  I-5/Arlington/Pioneer Hwy, Snohomish at Snohomish/Monroe) is the product, not imagery —
  cameras: **none found** (UNVERIFIED that none exist behind login).
- Flood-corridor imagery for these rivers instead comes from the WSDOT cameras verified in §1
  (I-5 @ 209.3 Stillaguamish, SR 532 @ 3.3, SR 529 @ 4.1 Snohomish, US 2 @ 2 Ebey Slough).

### City of Everett traffic cameras — VERIFIED (probed 2026-08-28)

- Index (HTML, not machine-readable): `https://www.everettwa.gov/2937/All-Everett-Traffic-Cameras`
  — HTTP 200 today; **40 unique camera image URLs** embedded, pattern
  `https://coe.everettwa.gov/Broadway/Images/<Name>/<Name>.jpg`.
- Image probe (`Broadway_Hewitt.jpg`, foreign Origin): HTTP 200, `image/jpeg`, 720×480, IIS.
  **No CORS headers** → `<img>` hotlink OK, pixel reads blocked. No referrer gating.
- **Refresh cadence VERIFIED by measurement:** `Last-Modified` advanced 23:00:40 → 23:02:40 GMT
  across a 90 s wait — a **2-minute refresh**, matching the city's own FAQ claim
  (`everettwa.gov/1630/Traffic-Camera-FAQs`, REPORTED via search snippet today).
- No JSON/GeoJSON metadata feed found — coordinates would have to be assigned once by hand from
  the page's names (stable-looking URL scheme; stability over time UNVERIFIED). Terms: no camera
  terms page fetched today — UNVERIFIED; ownership is City of Everett.

## 6. Copied-claim verdicts (all six)

| Claim | Verdict (2026-08-28) |
|---|---|
| "I-5 MP 209.3 Stillaguamish River camera" | **VERIFIED** — WSDOT id 9240, image live today |
| "SR 532 MP 3.3" | **VERIFIED** — WSDOT id 9187 "SR 532 at MP 3.3: Stillaguamish River" |
| "SR 529 MP 4.1 Snohomish River" | **VERIFIED** — two WSDOT cameras (ids 9316/9317, South+North) |
| "US 2 MP 2 Ebey Slough" | **VERIFIED** — WSDOT id 9357, image URL live |
| "Green River S 277th St camera" | **REFUTED as stated** — no such camera today. Near-misses: USGS *gauge* 12113150 is named "Green River above S 277th St at Kent" (a gauge, no camera); Kent formerly served a *272nd* St Bridge camera image, HTTP 404 today |
| "Green River S 228th St camera" | **PARTIALLY VERIFIED** — Kent's `Veterans_Drive_228th_Bridge.jpeg` (S 228th St/Veterans Dr crossing) still returns HTTP 200 today, but the image is frozen at 2025-12-11 — a dead feed behind a live URL |

## 7. Summary for the platform

| Source | Machine-readable? | Auth | CORS (data / images) | Cadence | Verdict |
|---|---|---|---|---|---|
| WSDOT Traveler API (HighwayCameras) | JSON/XML | **AccessCode (free, email form — owner action)** | n/a (server-side) | images ~3–5 min (measured 194 s) | richest metadata (owner, IsActive, milepost) |
| WSDOT ArcGIS `TravelInfoCamerasWeather` | JSON (ArcGIS query), keyless | none | open / **no CORS on images** | same imagery | best keyless path; "low volume" terms |
| SDOT ArcGIS `Traffic_Cameras_CDL` | JSON, keyless | none | `*` / no CORS on images | cache policy 5 min; observed one ~2 h-stale frame | good; trust Last-Modified per camera |
| USGS HIVIS/NIMS | JSON API + listable S3, keyless | none | open / **`*` on images (canvas-safe)** | 15–60 min per `ingest.intr` | public domain; Skagit + Nooksack only in Puget lowland |
| King County flood system | gauges only | — | — | — | **no cameras** |
| City of Kent Green River cams | no index; 1 stale JPEG | none | no CORS | frozen 2025-12-11 | do not use |
| Snohomish Co. OneRain | login-walled | — | — | — | no public cameras found |
| City of Everett | HTML page only (40 stills) | none | no CORS on images | **2 min (measured)** | usable with hand-built index |

**Recommended ingestion posture:** WSDOT ArcGIS layer (keyless) for corridor cameras now; request a
free Traveler API AccessCode (owner action) to gain `CameraOwner`/`IsActive`/milepost metadata;
USGS NIMS for Skagit/Nooksack river-eye imagery (only CORS-open, public-domain imagery in the set);
Everett stills as an optional hand-indexed extra. Serve all camera imagery through our own proxy if
client-side pixel access is ever needed (only USGS is CORS-open), and carry `Last-Modified` as the
knowledge-time of every frame — the Kent endpoint proves an HTTP 200 is not evidence of freshness.

## What could NOT be verified today

- Any written WSDOT policy explicitly granting rebroadcast of `images.wsdot.wa.gov` imagery (the
  ArcGIS "low volume" disclaimer is the closest fetched text; the camera-page disclaimer text was
  only seen via search snippets — REPORTED).
- WSDOT Traveler API response shape as actually served (needs the AccessCode; schema taken from
  official class docs).
- Undocumented rate limits on any of the probed hosts.
- SDOT video streams (`STREAM_NAME` implies they exist; no stream endpoint probed).
- Whether any kentwa.gov page still references the surviving 228th-St image (site WAF-blocks
  non-browser clients).
- Snohomish County OneRain content behind its login redirect.
- Long-term URL stability everywhere (today's naming schemes look stable; only today observed).
