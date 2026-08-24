# EVENT_ZERO.md — December 2025 Western Washington floods: hindcast seed reconstruction

Status: seed document (2026-08-22). Evidence: `docs/research/event-zero-december-2025-western-washington-floods.json`
(cited below as **EZ**, with provider and evidence-row index, e.g. `EZ:NWS[6]`), plus the files and URLs in the
source key (§10). All local times are PST = UTC−8 (no DST in December; EZ `category`). Labels follow `CONTEXT.md`:
**FACT** (read on a fetched page or present in an evidence file), **INFERENCE**, **OPEN QUESTION**. Nothing here is
reconstructed from memory.

## 1. Purpose

Event Zero is the first hindcast dataset of Cascadia Papsukkal (`ROADMAP.md` Phase 6; `TESTING.md` §7). Every row it
seeds exists to answer one question:

> **What would Cascadia Papsukkal have known, and shown, at clock time T — using only what was retrievable by T?**

The look-ahead rule (`DATA_DOCTRINE.md` §11; `adr/ADR-0010`): a replay at T may read only rows with
`available_at ≤ T`, and must read the observation *revision* and the forecast *run* that existed at T. The only
permitted access path is `as_known_at(T)`. Backfilled history (this document's case) sets `available_at` to the
provider's publication time when known and is otherwise flagged `backfilled=true`, so a hindcast can report how much
of its input is approximated. Where the archive cannot recover a product as it existed at T (e.g. NWPS forecast
runs), Phase 6 degrades to "reconstructed from products, flagged backfilled" (`ROADMAP.md`, "What would change this
roadmap"). This document records, per product family, which case applies (§7).

Entities seeded: `HistoricalEvent` (one row), `EventTimelineEntry` (§5), `Observation`/`Threshold`/`ForecastRun`/
`ForecastValue`/`OfficialAlert`/`RawArtifact` (§8 tasks), `HindcastRun` (§8, harness). `DOMAIN_MODEL.md` §2.3–2.5.

## 2. Event summary (every sentence labeled)

- **FACT** — A three-AR sequence (Dec 3–5, Dec 7, Dec 8–11) culminated in an AR ranked AR4 on the WA/OR coast and
  AR3 in the western Cascade foothills; initial landfall early Dec 8, a second moisture pulse late Dec 9, AR
  conditions ~96 h in some locations persisting through Dec 11; snow levels near 9,000 ft during the second pulse;
  >10 in over the Olympics/Cascades; five gauges at record flooding and 16 more above major (CW3E event summary,
  published 2025-12-23; S8; EZ:CW3E[2]).
- **FACT** — CW3E's Dec 3 outlook already identified three ARs for Dec 3–10 with AR3 (Mon Dec 8–Wed Dec 10) carrying
  IVT ≥ 1000 kg m⁻¹ s⁻¹ and ≥ 72 h of continuous AR conditions possible; NWRFC indicated larger rises with ARs 1 and 3
  (S6; EZ:CW3E[0]).
- **FACT** — UW OWSC: main event Dec 8–11; early-December rains saturated soils ahead of it; snow levels
  6,000–9,000 ft; December began with near record-low statewide SWE (S43, S42; EZ:ANTE[1–2]).
- **FACT** — Later ARs: landfall Dec 14 with peak conditions Dec 15–16 (IVT > 750) and another AR late Dec 17 /
  early Dec 18 (AR3/AR4 coastal); second NWS Flood Watch issued 2025-12-13 14:18 PST (S9, S10, S4; EZ:CW3E[3–4],
  EZ:NWS[3]). USACE counted "six atmospheric river pulses over nearly two weeks" (S13; EZ:USACE[2]).
- **FACT** — Basins reaching major flood category include Skagit, Sauk, Nooksack, Stillaguamish, Snohomish/
  Skykomish/Snoqualmie, Cedar, White, Puyallup/Carbon, Cowlitz; the Governor's request letter counts 33 rivers above
  flood stage, 18 above major, and names the Skagit, Snohomish and Cedar as "highest levels in recorded history"
  (S25; EZ:DECL[7]; scratch `gov_pa_request.txt`).
- **FACT** — Headline outcomes: Skagit nr Mount Vernon 37.73 ft / ~133,000 cfs at 2025-12-12 00:15 PST (08:15Z),
  above the 1990 record 37.37 ft / 152,000 cfs (S2, S3; EZ:USGS[0], EZ:NWPS[0]); Snohomish at Snohomish record
  (34.15 ft NWPS / 34.45 ft USGS); Cedar at Renton 18.25 ft / 12,400 cfs record; White River at R St 117.07 ft /
  12,000–12,400 cfs record (dam-release driven, Dec 15) (EZ:USGS[3,7,9], EZ:NWPS[2,10,12]).
- **FACT** — Regulation dominated the Green, White/Puyallup and Skagit: USACE took Section 7 control of Ross and
  Upper Baker on Dec 8 (Ross outflow cut to 450 cfs vs ~50,000 cfs inflow Dec 11; peak pool 1,594.53 ft 04:00 PST
  Dec 12) and again 08:30 PST Dec 15; Howard Hanson reached a record pool 1,189.3 ft (77,700 af, ~75 %); Mud Mountain
  ~1,185 ft (74,600 af, ~70 %) (S11, S12, S13; EZ:USACE[0–2]).
- **FACT** — Levee incidents: Desimone levee (Green River, Tukwila) breach ~11:30 PST Mon Dec 15 with Flash Flood
  Warning 11:51 PST; White River HESCO levee failure in Pacific ~01:20–01:39 PST Tue Dec 16 (S34, S35, S4;
  EZ:LOCAL[8–9], EZ:NWS[10]).
- **FACT** — Evacuations: Skagit County Level 3 for the entire 100-year floodplain from 17:00 PST Dec 10 (~75,000
  people by 20:19 PST; ~78,000 by Dec 12); Sumas/Everson/Nooksack/Marietta/parts of Ferndale Dec 10; Snohomish
  County orders 07:41 PST Dec 11 (S27, S28, S30, S32, S33; EZ:LOCAL[0–3,5,7]).
- **FACT** — Declarations: Proclamation 25-07 at 14:14 PST Dec 10 (amended 25-07.1 Dec 16); FEMA EM-3629 declared
  2025-12-12 (incident period 2025-12-09..19); FEMA DR-4906 declared 2026-04-07 (incident period 2025-12-05..19)
  (S18–S22; EZ:DECL[0–4]; OpenFEMA fetch 2026-08-22).
- **FACT** — One Washington fatality (driver, ~01:30 PST Dec 16 near Snohomish) (S26; EZ:DECL[8]).
- **INFERENCE** — Because statewide SWE was near record-low and snow levels sat at 6,000–9,000 ft, the hydrologic
  response was rain on saturated soils rather than snowmelt (stated by OWSC and Valley Record; S43, S45;
  EZ:ANTE[2,4]) — the platform must reproduce this from basin hypsometry × snow level × SWE, not assert it.
- **OPEN QUESTION** — No NWS service assessment and no USGS formal peak-flow release existed as of 2026-08-22
  (EZ:ANTE[10]); all "record" labels below are preliminary (NWPS flag `P`) unless noted.

## 3. Outcome table (one row per gauge / forecast point)

Stage in ft at gauge datum; flow in cfs. "Cat" = NWS category reached, derived by comparing the observed crest with
the NWPS OFFICIAL thresholds in S3 (arithmetic on FACT values). "USGS q" = qualifier on the 15-min series as captured
2026-08-22 (scratch `usgs/<site>.json`, S2b): `A` approved, `P` provisional. "NWPS" = crest-table flag (`P`
preliminary / `O` official / `R` revised). Crest times: UTC then PST.

| LID | USGS | Crest (stage / flow) | Crest time UTC / PST | Cat | Record status | USGS q / NWPS | Src | Label |
|---|---|---|---|---|---|---|---|---|
| MVEW1 Skagit nr Mount Vernon | 12200500 | 37.73 ft / 133,000 (NWPS 132,717) | 12-12T08:15Z / 12-12 00:15 (flow 01:00) | major (≥32) | **Record**; prev 37.37 ft 1990-11-25 (R) at 152,000 cfs; 1995 37.34; 2021 37.32 | A / P | S2,S3 | FACT |
| CONW1 Skagit nr Concrete | 12194000 | 40.99 ft / 151,000 (NWPS 41.03 / 151,196) | 12-11T15:50Z / 12-11 07:50 (NWPS 15:45Z) | major (≥32.5) | Not a record: 42.21 ft 2003-10-21 (R); 41.57 ft 1995; Dec 2025 4th in table | A / P | S2,S3 | FACT |
| SNAW1 Snohomish at Snohomish | 12155500 | 34.45 ft USGS; 34.15 ft NWPS (stage only) | 12-12T01:35Z / 12-11 17:35 (NWPS "17:30Z") | major (≥29) | **Record**; prev 33.5 ft 1990-11-25 (O); 33.49 ft 2006 | A / R | S2,S3 | FACT (value conflict, §3 note a) |
| MROW1 Snohomish nr Monroe | 12150800 | 24.64 ft / 115,000 (NWPS 24.55 / 106,222) | 12-12T00:52Z / 12-11 16:52 (flow 17:00) | major (≥17) | 2nd; record 25.3 ft / 150,000 cfs 1990-11-25 | A / P | S2,S3 | FACT |
| CRNW1 Snoqualmie nr Carnation | 12149000 | 60.76 ft / 89,700 (NWPS 89,686) | 12-11T12:00Z / 12-11 04:00 | major (≥58) | 2nd by stage (record 62.21 ft 2009-01-08, R); highest flow in top-5 | P / P (duplicate entry, note b) | S2,S3 | FACT |
| SQUW1 Snoqualmie nr Snoqualmie Falls | 12144500 | 19.95 ft / 70,000 | 12-11T01:45Z / 12-10 17:45 | major (≥41,000 cfs) | 4th; record 21.55 ft / 78,800 cfs 1990-11-24 | stage A, flow P / P | S2,S3 | FACT |
| GLBW1 Skykomish nr Gold Bar | 12134500 | 24.01 ft / 115,000 (NWPS 24.03 / 114,215) | 12-11T00:15Z / 12-10 16:15 | major (≥19) | 2nd; record 24.51 ft / 129,000 cfs 2006-11-06 (R) | A / P | S2,S3 | FACT |
| ARLW1 Stillaguamish at Arlington | 12167400 | 20.17 ft reported at 07:05 PST Dec 11; NWS fcst 20.9 ft; crest not obtained | 12-11 morning (OPEN) | major (≥19; 20.17 > 19) | Below record 21.34 ft 2023-12-05 (P); NWPS table has no Dec 2025 entry (2026-08-22) | no USGS IV series for Dec 2025 / — | S2,S3,S33 | OPEN QUESTION (crest, time) |
| NRKW1 Nooksack at N Cedarville | 12210700 | 150.44 ft / 67,300 (NWPS 150.49 / 67,159) | 12-11T11:00Z / 12-11 03:00 (first-max 02:30 in S2b) | major (≥150) | **Conflict**: NWPS lists 2021-11-15 150.76 ft (O) above Dec 2025 (P); NWS products and media compared to 149.6 ft (2003) and called it a record | A / P | S2,S3,S47 | FACT (values); OPEN QUESTION (record status) |
| NKSW1 Nooksack at Ferndale | 12213100 | 22.42 ft / 44,300 | 12-12T06:15Z / 12-11 22:15 | moderate (20.5–23) | Not a record (31.23 ft 1951-02-10) | A / no Dec 2025 entry seen | S2,S3 | FACT |
| RNTW1 Cedar at Renton | 12119000 | 18.25 ft / 12,400 | 12-11T23:00Z / 12-11 15:00 | major (≥16) | **Record** by stage and flow; prev 17.13 ft / 10,600 cfs 1990-11-24 (R); NWPS table still not updated at 2026-08-22 13:17Z fetch | P / not entered | S2,S3b | FACT (USGS); OPEN QUESTION (NWPS entry) |
| AUBW1 Green nr Auburn | 12113000 | 68.67 ft / 12,100 | 12-13T15:15Z / 12-13 07:15 (flow 09:00; 2nd peak 11,500 cfs 12-14 08:45) | moderate (12,000–14,000 cfs) | 2nd-highest stage; record 69.75 ft / 28,100 cfs 1959 (pre-dam) | A / P | S2,S3 | FACT |
| WRAW1 White at R St nr Auburn | 12100490 | 117.07 ft / 12,000 USGS (NWPS 12,400) | 12-15T17:15Z / 12-15 09:15 | major (≥12,000 cfs) | **Record**; prev 115.47 ft / 8,230 cfs 2022-02-28 | A / P | S2,S3 | FACT (flow differs by 400 cfs between sources) |
| PUYW1 Puyallup at Puyallup | 12101500 | 28.67 ft / 44,400 | 12-12T01:00Z / 12-11 17:00 (flow 17:30) | minor (26.2–30) | Not a record (34.15 ft 1917); no Dec 2025 top-5 entry | A / — | S2,S3 | FACT |
| ORTW1 Puyallup nr Orting | 12093500 | 12.35 ft / 20,800 | 12-10T15:15Z / 12-10 07:15 | major (≥16,000 cfs) | 3rd; record 21,500 cfs 2006-11-06; also 16,800 (Dec 9) and 16,600 (Dec 11) entries | A / P | S2,S3 | FACT |
| (LID OPEN) Sauk nr Sauk | 12189500 | 16.97 ft / 84,800 | 12-11T12:30Z / 12-11 04:30 | OPEN (no NWPS thresholds captured; "SAUW1" returns 404) | ~17-yr (to 30-yr) event per OWSC | A / — | S2,S3,S44 | FACT (peak); OPEN QUESTION (LID/cat) |
| (LID OPEN) Sauk ab White Chuck | 12186000 | 11.80 ft / 23,800 | 12-11T04:45Z / 12-10 20:45 | OPEN | — | P / — | S2 | FACT (peak) |
| (LID OPEN) Skagit at Marblemount | 12181000 | 13.23 ft / 53,400 | 12-11T10:25Z / 12-11 02:25 | OPEN | Below Ross/Gorge — regulated | A / — | S2,S2b | FACT (peak) |
| (LID OPEN) Skagit nr Sedro-Woolley | 12199000 | 44.11 ft (stage only) | 12-12T07:30Z / 12-11 23:30 | OPEN | — | A / — | S2,S2b | FACT (peak) |
| PILW1? Pilchuck nr Snohomish | 12155300 | 17.67 ft / 6,410 | 12-11T15:15Z / 12-11 07:15 | OPEN | — | A / — | S2,S5 | FACT (peak); INFERENCE (LID from VTEC list) |
| (LID OPEN) NF Stillaguamish nr Arlington | 12167000 | 15.01 ft / 30,700 | 12-11T12:45Z / 12-11 04:45 (flow first-max 02:00 in S2b) | OPEN | ~3-yr event per OWSC | P / — | S2,S2b,S44 | FACT (peak) |
| SSFW1? SF Stillaguamish nr Granite Falls | 12161000 | 14.53 ft (stage only) | 12-09T06:45Z / 12-08 22:45 | OPEN | — | A / — | S2,S5 | FACT (peak); INFERENCE (LID) |
| LNDW1 Cedar nr Landsburg | 12117500 | 10.17 ft / 9,920 | 12-11T20:30Z / 12-11 12:30 | major per FLW (9.0 ft "MAJOR" issued 12-09 23:35 PST) | — | P / — | S2,S4 | FACT (peak); INFERENCE (category from warning text) |
| TOLW1 Tolt nr Carnation | 12148500 | 10.16 ft / 6,540 | 12-10T20:30Z / 12-10 12:30 | minor (5,000–7,000 cfs) | Record 17,400 cfs (1959); NWS had forecast MAJOR 9,867 cfs | A / no entry | S2,S3,S4 | FACT |
| RAWW1 Cowlitz at Randle | 14231000 | 24.17 ft / 36,656 | 12-11 (time OPEN) | major (≥22) | 3rd; record 25.24 ft 2006-11-07 | — / P | S3 | FACT (NWPS) |
| PACW1 Cowlitz at Packwood | OPEN | crest not obtained; FLW 12-08 16:04 PST forecast 13.9 ft "near-record" | OPEN | major (≥12) per forecast | Record 14.59 ft (2006); no Dec 2025 top-5 entry | — | S3,S4 | OPEN QUESTION |
| CGMW1 Chehalis nr Grand Mound | OPEN | 143.27 ft / 32,114 | 12-11 (time OPEN) | moderate (<144 major) | Record 147.26 ft 2007-12-04 | — / P | S3 | FACT (NWPS) |
| MMRW1 White at Mud Mtn Dam outflow | — | peak outflow not obtained | OPEN | — | Record outflow 15,200 cfs 1986-11-24 | — | S3 | OPEN QUESTION |

Second AR peaks (FACT, S2 late capture): MVEW1 30.92 ft / 81,500 cfs 12-17 20:15 PST (NWPS 30.93 ft, P); CONW1
31.39 ft / 80,800 cfs 12-16 01:15; SNAW1 27.77 ft 12-17 17:00; MROW1 16.0 ft / 62,100 cfs 12-17 13:30; CRNW1 56.72 ft
12-17 18:30; GLBW1 17.98 ft / 53,600 cfs 12-17 05:45; RNTW1 14.94 ft 12-14 02:00; NKSW1 17.07 ft 12-17; PUYW1
21,500 cfs 12-19 03:45. Third pulse Dec 21 reached only action/minor (MVEW1 24.05 ft 12-21 01:15 PST).

Notes on discrepancies (all FACT as to what each source says):
- (a) **SNAW1 34.45 vs 34.15 ft** — USGS IV 12155500 (stage only, now `A`) 34.45 ft at 17:35 PST; NWPS crest table
  34.15 ft (`R`) stamped "2025-12-11T17:30:00Z", which is 09:30 PST — the time-zone of NWPS crest stamps is
  inconsistent across sites (EZ:NWPS limitations). Unresolved whether a datum/sensor difference or a revision.
- (b) **CRNW1 duplicate** — NWPS lists two Dec 11 entries (60.76 ft / 89,686 cfs at "12:00Z" and 60.76 ft /
  89,700 cfs at "04:00Z", both `P`) (S3 scratch `CRNW1.json`).
- (c) **NRKW1 record status** — see row; EZ open question. The contemporaneous FLS of 02:23 PST Dec 11 cited a
  "prior crest of 149.6 ft 10/17/2003" (EZ:NWS[9]), i.e. the forecaster's ledger at T did not contain the 2021 value.
- (d) **RNTW1 / ARLW1 crest tables not updated** as of 2026-08-22 (S3b, S3) — NWPS crest history is not a reliable
  "outcome" source until updated; USGS IV (RNTW1) is the outcome of record here, and ARLW1 has no USGS IV series
  (observations are attributed to Snohomish County, S3 `dataAttribution`).
- (e) **Flat peaks** — first-occurrence-of-max times differ by capture (MVEW1 flow 00:00 vs 01:00 PST; NRKW1 02:30 vs
  03:00; NF Stillaguamish flow 02:00 vs 04:45; Green nr Auburn flow 06:30 vs 09:00). Store the full series, not a
  single crest time.

## 4. Antecedent state

- **FACT** — End of November 2025: statewide SWE lower than ~90 % of years on record; basin SWE % of median —
  Olympics 12 %, western Cascades 22–36 %, northern Cascades ~61 %; several Cascade stations at record-low November
  SWE; Olympics/SW Cascades November precipitation 60–80 % of normal in warm rain-dominant storms; D3 drought only in
  far SE Washington as of Dec 2 (OWSC, published 2025-12-06; S41; EZ:ANTE[0]).
- **FACT** — December began with near record-low statewide SWE; the warm Dec 8–11 AR drove statewide snowpack to the
  lowest on record by Dec 14–16 (OWSC 2026-01-12; S42; EZ:ANTE[1]).
- **FACT** — Summer 2025 drought declaration covered much of western/central WA; Yakima reservoirs 39 % of capacity
  on Dec 11 (Ecology 2026-01-06; S46; EZ:ANTE[5]).
- **FACT** — Dec 5–7 first AR produced 3–6 in over the Cascades/Olympics raising base flows; 87.5 % of SNOTEL sites
  with ≥ 20 years of data recorded their highest 14-day precipitation on record for Dec 6–19 (remaining 12.5 %
  second-highest); RFC QPE showed widespread 20–30 in totals (Governor's PA letter 2026-02-17; S25; EZ:DECL[7]).
- **FACT** — Soils were above normal from "the previous weekend's rain"; Paradise RS and Stampede Pass 15+ in in
  72 h (Valley Record; S45; EZ:ANTE[4]). Two-week IMERG totals > 15 in Olympics, > 24 in at a Cascades gauge
  (Dec 1–15; NASA GPM; S49; EZ:ANTE[8]).
- **FACT** — Harts Pass SNOTEL (515:WA:SNTL, 6,490 ft, N Cascades) daily WTEQ in inches vs POR median (AWDB via
  S51, qaFlag `P`, qcFlag `V`): Dec 1 14.0/11.7 · Dec 2 14.0/12.2 · Dec 3 14.2/12.3 · Dec 4 15.0/12.3 · Dec 5 16.4/12.8
  · Dec 6 17.4/13.0 · Dec 7 18.4/13.2 · Dec 8 20.8/13.4 · Dec 9 21.3/13.8 · Dec 10 26.4/14.0 · Dec 11 25.7/14.8 ·
  Dec 12 25.6/15.9 · Dec 15 27.8/16.4.
- **INFERENCE** — Harts Pass was *above* median (≈120 %) on Dec 1 and gained 12.4 in SWE Dec 1→15, the opposite of
  the statewide picture; the 5.1 in jump Dec 9→10 coincides with the 9,000-ft snow-level pulse and may be rain
  retained in the pack rather than snowfall. One high, east-slope pillow must not be used as a basin SWE proxy; the
  hindcast needs SNODAS/basin-aggregated SNOTEL (§7, §8 T5–T6).
- **OPEN QUESTION** — Exact statewide and per-basin SWE % on Dec 1 and Dec 8, and the Dec 3–7 gauge response
  (USGS IV captures here start Dec 8): see §9.

## 5. Forecast and warning timeline (seeds `EventTimelineEntry`)

Mapping of `kind` to `DOMAIN_MODEL.md` §2.5: outlook/forecast_crest → `forecast_issued`; watch/warning/
flash_flood_watch/flash_flood_warning → `warning_issued`; the rest map 1:1. `available_at` = product header time for
NWS text (FACT from the IEM AFOS archive, S4); for non-NWS rows it is the reported time or OPEN QUESTION. Scope:
basin / fp (forecast point) / county / state.

| # | at (UTC) | local (PST, UTC−8) | kind | scope | text | src | available_at |
|---|---|---|---|---|---|---|---|
| 1 | 2025-12-03 | Dec 3 | outlook | region | CW3E: three ARs Dec 3–10; AR3 Dec 8–10 with IVT ≥ 1000, ≥ 72 h AR possible; NWRFC: larger rises with ARs 1 and 3 | S6 | OPEN (date only) |
| 2 | 12-04T10:22Z | Dec 4 02:22 | outlook | region | WPC 7-day QPF (valid 12Z Dec 4–12Z Dec 11) approaching 15 in over WA/OR Coast and Cascade ranges | S50 | 10:22Z (issue time per write-up) |
| 3 | 12-04T20:56Z | Dec 4 12:56 | outlook | basin | ESF "THREAT OF RIVER FLOODING ACROSS WESTERN WASHINGTON EARLY NEXT WEEK"; snow levels ~5,000–6,000 ft | S4 | 20:56Z |
| 4 | 12-05T11:37Z | Dec 5 03:37 | outlook | basin | ESF update; snow levels 4,500–6,500 ft | S4 | 11:37Z |
| 5 | 12-05T23:46Z | Dec 5 15:46 | outlook | basin | ESF "THREAT OF RIVER FLOODING HAS INCREASED" | S4 | 23:46Z |
| 6 | 12-06T00:10Z | Dec 5 16:10 | watch | county | FFA FA.A.0012 NEW, in effect 251208T1200Z–251213T0000Z, 14 counties (Clallam…Whatcom) | S4 | 00:10Z (WMO 060010) |
| 7 | 12-06T09:37Z | Dec 6 01:37 | note | basin | AFD: "widespread river flooding event will commence late Monday and continue through much of the week" | S4 | 09:37Z |
| 8 | 2025-12-08 | Dec 8 | reservoir_action | basin | USACE RCC assumes Section 7 control of Ross (SCL) and Upper Baker (PSE) | S11 | OPEN (time) |
| 9 | 12-08T09:33Z | Dec 8 01:33 | note | basin | AFD: "widespread significant river flooding"; 6–10 in Olympics/Cascades, locally 12+; no "record" wording yet | S4 | 09:33Z |
| 10 | 2025-12-08 | Dec 8 | outlook | region | CW3E: > 90 % AR4+, > 50 % AR5 coastal WA; > 10 in Cascades; 10 gauges forecast major | S7 | OPEN (date only) |
| 11 | 2025-12-08 | Dec 8 | note | state | State EOC to Level 2 (Governor's letter) | S25 | OPEN (time) |
| 12 | 12-08T20:29Z | Dec 8 12:29 | warning | fp | First river FLW of the event: Skokomish at Potlatch (moderate) | S4 | 20:29Z |
| 13 | 12-09T00:04Z | Dec 8 16:04 | warning | fp | FLW Cowlitz at Packwood MAJOR 13.9 ft "near-record"; Randle MAJOR 23.7 ft | S4 | 00:04Z |
| 14 | 12-09T00:44Z | Dec 8 16:44 | warning | fp | FLW Puyallup nr Orting MAJOR 18,824 cfs; Carbon nr Fairfax; South Prairie Cr | S4 | 00:44Z |
| 15 | 12-09T01:18Z | Dec 8 17:18 | warning | fp | FLW Skykomish nr Gold Bar MAJOR 19.9 ft; SF Stillaguamish | S4 | 01:18Z |
| 16 | 12-09T02:16Z | Dec 8 18:16 | warning | fp | FLW Snoqualmie nr Snoqualmie Falls MAJOR 46,000 cfs; Tolt moderate 7,500 cfs | S4 | 02:16Z |
| 17 | 12-09T03:56Z | Dec 8 19:56 | warning | fp | FLW Carnation MAJOR 58.8 ft; Monroe MAJOR 18.8 ft; Snohomish at Snohomish MAJOR 31.9 ft | S4 | 03:56Z |
| 18 | 12-09T04:10Z | Dec 8 20:10 | warning | fp | FLW Stillaguamish at Arlington moderate 17.8 ft | S4 | 04:10Z |
| 19 | 12-09T06:15Z | Dec 8 22:15 | warning | fp | FLW Skagit nr Concrete MAJOR, crest 37.6 ft early Thu | S4 | 06:15Z |
| 20 | 12-09T06:45Z | Dec 8 22:45 | crest_observed | fp | SF Stillaguamish nr Granite Falls 14.53 ft (12161000) | S2 | valid+~15 min (backfilled) |
| 21 | 12-09T07:54Z | Dec 8 23:54 | warning | fp | FLW Puyallup at Puyallup minor 29 ft | S4 | 07:54Z |
| 22 | 12-09T10:07Z | Dec 9 02:07 | warning | fp | Tolt ab Carnation raised to MAJOR 9,867 cfs (observed peak later 6,540 cfs, minor) | S4 | 10:07Z |
| 23 | 12-09T11:16Z | Dec 9 03:16 | warning | fp | Green nr Auburn NEW minor 10,705 cfs | S4 | 11:16Z |
| 24 | 12-09T12:00Z | Dec 9 04:00 | note | fp | Puyallup nr Orting observed 17,600 cfs / 11.5 ft (major = 16,000 cfs) | S37 | OPEN (report time) |
| 25 | 12-09T17:01Z | Dec 9 09:01 | warning | fp | **MVEW1 FL.W.0042 NEW** (/O.NEW.KSEW.FL.W.0042.251210T0147Z-000000T0000Z/): stage 25.3 ft, MAJOR, crest 36.9 ft early Fri, "severe near record flooding from Sedro Woolley downstream through Mount Vernon"; Arlington extended to 18.8 ft | S4 | 17:01Z |
| 26 | 12-09T17:36Z | Dec 9 09:36 | warning | fp | Green nr Auburn raised to moderate 12,829 cfs | S4 | 17:36Z |
| 27 | 12-09T20:07Z | Dec 9 12:07 | warning | fp | White River at R St NEW MAJOR 12,644 cfs Thu | S4 | 20:07Z |
| 28 | 12-09T20:15Z | Dec 9 12:15 | reservoir_action | basin | Green at Palmer (HHD outflow reach, 12106700) 12,500 cfs — pre-storage release | S2 | valid+~15 min (backfilled) |
| 29 | 2025-12-09 | Dec 9 | evacuation | county | Skagit County Level 2 "prepare to evacuate"; NWS forecast Concrete 40.65 ft ~10:00 Dec 11, Mount Vernon 36.91 ft 04:00 Dec 12 | S27 (120925-3) | OPEN (time) |
| 30 | 12-10T01:24Z | Dec 9 17:24 | forecast_crest | fp | FLS: **MV 41.5 ft** early Fri "approaches the flood of record"; Concrete 47.4 ft early Thu; Arlington MAJOR 20.6 ft "near record" | S4 | 01:24Z |
| 31 | 12-10T02:25Z | Dec 9 18:25 | forecast_crest | fp | Snohomish at Snohomish 33.8 ft (record 33.5); Monroe 23.6 ft | S4 | 02:25Z |
| 32 | 12-10T02:58Z | Dec 9 18:58 | note | fp | KIRO7 snapshot of NWS forecasts: Concrete 47.36 ft; MV 41.54 ft; Monroe 26.77 ft; Snohomish 33.83 ft; Gold Bar obs 20.32 ft at 23:00 Dec 8 | S40 | 02:58Z |
| 33 | 2025-12-10 | Dec 9 evening | declaration | county | Snohomish County countywide emergency (Lewis County declared Dec 9 AM) | S24 | OPEN (time) |
| 34 | 12-10T06:23Z | Dec 9 22:23 | warning | fp | Nooksack at N Cedarville NEW moderate 148.4 ft | S4 | 06:23Z |
| 35 | 12-10T07:35Z | Dec 9 23:35 | warning | fp | Cedar nr Landsburg NEW MAJOR 9.0 ft; Elwha "approaches the flood of record" | S4 | 07:35Z |
| 36 | 12-10T09:24Z | Dec 10 01:24 | forecast_crest | fp | MV 41.5 ft; Concrete 47.7 ft (previous 47.6 ft 12/13/1921 cited) | S4 | 09:24Z |
| 37 | 12-10T10:17Z | Dec 10 02:17 | forecast_crest | fp | Snohomish 33.7 ft; Monroe 26.3 ft (above 25.3 record) | S4 | 10:17Z |
| 38 | 2025-12-10 | Dec 10 morning | note | basin | NOAA NWC: "Locally catastrophic flooding impacts are possible along Skagit and Snohomish Rivers… Major and/or record flooding is expected" | S53 | OPEN (time) |
| 39 | 12-10T16:10Z | Dec 10 08:10 | warning | fp | Cedar at Renton NEW MAJOR 16.3 ft | S4 | 16:10Z |
| 40 | 12-10T17:42Z | Dec 10 09:42 | warning | fp | Nooksack at Ferndale NEW moderate 21.4 ft | S4 | 17:42Z |
| 41 | 12-10T18:26Z | Dec 10 10:26 | warning | basin | Areal Flood Warning: "Nooksack River overflow at Everson imminent or occurring" (VTEC issue 18:26Z) | S4,S5 | 18:26Z |
| 42 | 12-10T20:10Z | Dec 10 12:10 | warning | basin | Areal FW South Fork Skykomish ("6 and 10 inches have fallen", 3–5 more) | S4 | 20:10Z |
| 43 | 12-10T20:30Z | Dec 10 12:30 | crest_observed | fp | Tolt nr Carnation 6,540 cfs / 10.16 ft (minor) | S2 | valid+~15 min (backfilled) |
| 44 | 12-10T20:40Z | Dec 10 12:40 | warning | county | Areal FW foothills (King/Skagit/Snohomish/Whatcom) | S4 | 20:40Z |
| 45 | 2025-12-10 | Dec 10 midday | levee_incident | basin | Ebey Island dikes overtopped; evacuation underway | S33 | OPEN (time) |
| 46 | 12-10T22:14Z | Dec 10 14:14 | declaration | state | Proclamation 25-07 statewide emergency; National Guard activated; expedited federal request | S18,S19 | 22:14Z |
| 47 | 12-10T23:14Z | Dec 10 15:14 | forecast_crest | fp | **MV 42.3 ft Fri AM — peak forecast of the event** | S4 | 23:14Z |
| 48 | 12-10T23:30Z | Dec 10 15:30 | note | state | State EOC Level 1 per HeraldNet (Governor's letter says Level 1 on Dec 9 — conflict, §9) | S19,S25 | 23:30Z |
| 49 | 12-11T00:15Z | Dec 10 16:15 | crest_observed | fp | Skykomish nr Gold Bar 24.01 ft / 115,000 cfs | S2 | valid+~15 min (backfilled) |
| 50 | 12-11T01:00Z | Dec 10 17:00 | evacuation | county | **Skagit County Level 3 GO**, Mount Vernon; entire 100-yr floodplain; forecasts Concrete 46.13 ft, MV 42.13 ft; shelters listed | S27,S28 | 01:00Z |
| 51 | 12-11T01:15Z | Dec 10 17:15 | forecast_crest | fp | MV 42.1 ft; Concrete 46.1 ft | S4 | 01:15Z |
| 52 | 12-11T01:29Z | Dec 10 17:29 | warning | basin | Areal FW: Skagit "high probability of overflowing at Sterling" (through 04:15 Sat) | S4,S5 | 01:29Z |
| 53 | 12-11T01:32Z | Dec 10 17:32 | forecast_crest | fp | Cedarville MAJOR 150 ft "approaching record" | S4 | 01:32Z |
| 54 | 12-11T01:45Z | Dec 10 17:45 | crest_observed | fp | Snoqualmie nr Snoqualmie Falls 19.95 ft / 70,000 cfs | S2 | valid+~15 min (backfilled) |
| 55 | 12-11T02:50Z | Dec 10 18:50 | reservoir_action | basin | Spada Lake reaches Culmback Dam spillway after a 15-ft rise in two days; Jackson project at full capacity | S16 | 02:50Z (reported) |
| 56 | 12-11T03:13Z | Dec 10 19:13 | flash_flood_watch | county | **FF.A.0002** potential failure of Skagit levees/dikes below Sedro-Woolley (251211T0313Z–251213T1200Z) | S4 | 03:13Z |
| 57 | 12-11T03:47Z | Dec 10 19:47 | warning | fp | Green nr Auburn moderate 12,184 cfs | S4 | 03:47Z |
| 58 | 12-11T04:12Z | Dec 10 20:12 | evacuation | county | Level 3 south Sedro-Woolley; ~75,000 people under orders by 20:19 PST (04:19Z) | S28 | 04:12Z |
| 59 | 12-11T04:45Z | Dec 10 20:45 | crest_observed | fp | Sauk ab White Chuck 23,800 cfs | S2 | valid+~15 min (backfilled) |
| 60 | 12-11T06:24Z | Dec 10 22:24 | forecast_crest | fp | Snohomish 33.4 ft; Monroe 24.9 ft | S4 | 06:24Z |
| 61 | 12-11T06:32Z | Dec 10 22:32 | forecast_crest | fp | Ferndale 22.3 ft; Cedarville 149.3 ft | S4 | 06:32Z |
| 62 | 12-11T06:50Z | Dec 10 22:50 | forecast_crest | fp | Cedar at Renton 17.5 ft "approaches the flood of record" | S4 | 06:50Z |
| 63 | 12-11T10:04Z | Dec 11 02:04 | forecast_crest | fp | **MV revised down to 39.1 ft** late Fri AM; Concrete "cresting now" 41.1 ft | S4 | 10:04Z |
| 64 | 12-11T10:07Z | Dec 11 02:07 | forecast_crest | fp | Arlington 20.9 ft late morning; Snohomish 33.6 ft | S4 | 10:07Z |
| 65 | 12-11T10:23Z | Dec 11 02:23 | forecast_crest | fp | Cedarville MAJOR 150.3 ft (prior crest 149.6 ft 10/17/2003 cited) | S4 | 10:23Z |
| 66 | 12-11T11:00Z | Dec 11 03:00 | crest_observed | fp | Nooksack at N Cedarville 150.44 ft / 67,300 cfs (NWPS 150.49 ft, 11:00Z) | S2,S3 | valid+~15 min (backfilled) |
| 67 | 12-11T12:00Z | Dec 11 04:00 | crest_observed | fp | Snoqualmie nr Carnation 60.76 ft / 89,700 cfs | S2 | valid+~15 min (backfilled) |
| 68 | 12-11T12:30Z | Dec 11 04:30 | crest_observed | fp | Sauk nr Sauk 84,800 cfs / 16.97 ft | S2 | valid+~15 min (backfilled) |
| 69 | 12-11T12:38Z | Dec 11 04:38 | evacuation | county | Lincoln Ave homes in Snohomish evacuated by kayak | S33 | OPEN (report time) |
| 70 | 12-11T12:45Z | Dec 11 04:45 | crest_observed | fp | NF Stillaguamish nr Arlington 15.01 ft / 30,700 cfs | S2 | valid+~15 min (backfilled) |
| 71 | 12-11T14:34Z | Dec 11 06:34 | note | basin | PNS 5-day totals: Bishop Quinault 16.58 in; Owl Mtn 14.44; Ohanapecosh 14.15; Skykomish 13.40; Cedar Falls 13.38; Paradise SNOTEL 11.70 | S4 | 14:34Z |
| 72 | 12-11T15:05Z | Dec 11 07:05 | note | fp | Arlington 20.17 ft reported (crest OPEN) | S33 | OPEN |
| 73 | 12-11T15:15Z | Dec 11 07:15 | crest_observed | fp | Pilchuck nr Snohomish 17.67 ft / 6,410 cfs | S2 | valid+~15 min (backfilled) |
| 74 | 12-11T15:41Z | Dec 11 07:41 | evacuation | county | Snohomish County orders: Three Rivers MHP (SR 522), Ebey Island, Tualco (SR 203) | S33 | 15:41Z |
| 75 | 12-11T15:50Z | Dec 11 07:50 | crest_observed | fp | Skagit nr Concrete 40.99 ft / 151,000 cfs (NWPS 41.03 ft at 15:45Z) | S2,S3 | valid+~15 min (backfilled) |
| 76 | 12-11T16:29Z | Dec 11 08:29 | note | fp | FLS: Snohomish at Snohomish 33.8 ft at 08:00 PST — above the 33.5 ft 1990 record | S4 | 16:29Z |
| 77 | 12-11T18:17Z | Dec 11 10:17 | forecast_crest | fp | FLS (EXT FL.W.0042): MV crest 39.1 ft; product cites observed 29.5 ft at 01:15 PST | S4b | 18:17Z |
| 78 | 12-11T18:40Z | Dec 11 10:40 | note | fp | Arlington 18.8 ft, falling | S4 | 18:40Z |
| 79 | 12-11T20:00Z | Dec 11 12:00 | evacuation | county | Level 3 downtown Mount Vernon, Fir Island, Conway; Whatcom Level 3 (Sumas, Nooksack, Everson, Marietta, parts of Ferndale) issued Dec 10 | S29,S32 | OPEN (exact times) |
| 80 | 12-11T23:00Z | Dec 11 15:00 | crest_observed | fp | **Cedar at Renton 18.25 ft / 12,400 cfs — record** | S2 | valid+~15 min (backfilled) |
| 81 | 12-12T00:52Z | Dec 11 16:52 | crest_observed | fp | Snohomish nr Monroe 24.64 ft (115,000 cfs at 17:00) | S2 | valid+~15 min (backfilled) |
| 82 | 12-12T01:00Z | Dec 11 17:00 | crest_observed | fp | Puyallup at Puyallup 28.67 ft (44,400 cfs at 17:30) — minor | S2 | valid+~15 min (backfilled) |
| 83 | 12-12T01:12Z | Dec 11 17:12 | forecast_crest | fp | FLS: MV observed 35.8 ft at 16:15; **crest 38.3 ft late tonight** (press reported 38.26 ft) | S4b,S29 | 01:12Z |
| 84 | 12-12T01:35Z | Dec 11 17:35 | crest_observed | fp | **Snohomish at Snohomish 34.45 ft USGS (34.15 ft NWPS) — record** | S2,S3 | valid+~15 min (backfilled) |
| 85 | 12-12T06:15Z | Dec 11 22:15 | crest_observed | fp | Nooksack at Ferndale 22.42 ft / 44,300 cfs (moderate) | S2 | valid+~15 min (backfilled) |
| 86 | 12-12T07:30Z | Dec 11 23:30 | crest_observed | fp | Skagit nr Sedro-Woolley 44.11 ft | S2b | valid+~15 min (backfilled) |
| 87 | 12-12T08:15Z | Dec 12 00:15 | crest_observed | fp | **MVEW1 37.73 ft (133,000 cfs at 01:00 PST) — record over 37.37 ft (1990-11-25)** | S2,S3 | valid+~15 min (backfilled) |
| 88 | 12-12T08:50Z | Dec 12 00:50 | forecast_crest | fp | FLS: MV 37.7 ft at 00:15, forecast 38.1 ft early this morning; Concrete crested 40.8; Snohomish 34.2; Monroe 24.6; Ferndale 22.4; Renton 18.2; Carnation 60.8 | S4,S4b | 08:50Z |
| 89 | 12-12T12:00Z | Dec 12 04:00 | reservoir_action | basin | Ross peak pool 1,594.53 ft; outflow 450 cfs vs ~50,000 cfs inflow on Dec 11 | S11 | 2025-12-13 (release date) |
| 90 | 2025-12-12 | Dec 12 morning | levee_incident | basin | Gages Slough (Burlington) flooded; Burlington evacuation order (partially lifted later); ~78,000 under Level 3 | S30 | OPEN (time) |
| 91 | 12-12T17:00Z | Dec 12 09:00 | reservoir_action | basin | Howard Hanson pool 1,189 ft / 77,000 af / 74 % (Dec 13 release); record 1,189.3 ft / 77,700 af / ~75 % (Jul 2026 analysis) | S12,S13 | 2025-12-13 |
| 92 | 12-12T17:30Z | Dec 12 09:30 | watch | county | FFA cancelled ("all rivers either under flood warnings or have receded"); FF.A.0002 extended to 251213T1600Z | S4 | 17:30Z |
| 93 | 2025-12-12 | Dec 12 | declaration | state | FEMA EM-3629 (declarationDate 2025-12-12; incidentBeginDate 2025-12-09, end 2025-12-19) | S21 | OPEN (time) |
| 94 | 12-13T00:28Z | Dec 12 16:28 | flash_flood_watch | county | FF.A.0002 cancelled | S4 | 00:28Z |
| 95 | 12-13T01:27Z | Dec 12 17:27 | outlook | basin | ESF: second AR; snow level 5,000 ft rising to 8,000–8,500 ft Mon Dec 15, dropping to 3,000–4,500 ft Tue (update 06:26 PST Dec 13) | S4 | 01:27Z |
| 96 | 12-13T04:00Z | Dec 12 20:00 | reservoir_action | basin | Mud Mountain peak pool ~1,185 ft / 74,600 af / 70 % | S12 | 2025-12-13 |
| 97 | 12-13T15:15Z | Dec 13 07:15 | crest_observed | fp | Green nr Auburn 68.67 ft (12,100 cfs at 09:00) — moderate, regulated | S2 | valid+~15 min (backfilled) |
| 98 | 12-13T22:18Z | Dec 13 14:18 | watch | county | **FFA FA.A.0013 NEW** 251215T1800Z–251219T0000Z, 12 counties, "preliminary liquid totals of 2 to 8 inches" | S4 | 22:18Z |
| 99 | 2025-12-14 | Dec 14 | note | region | AR landfall; peak Dec 15–16 (CW3E Dec 12/15 outlooks) | S9,S10 | OPEN |
| 100 | 12-15T16:30Z | Dec 15 08:30 | reservoir_action | basin | USACE reassumes Section 7 control of Ross/Upper Baker (natural flow forecast > 90,000 cfs at Concrete within 8 h) | S11 | 2025-12-13 release / S14 Dec 15 |
| 101 | 12-15T17:15Z | Dec 15 09:15 | crest_observed | fp | White River at R St 12,000 cfs / 117.07 ft — record (MMD drawdown) | S2 | valid+~15 min (backfilled) |
| 102 | 12-15T19:30Z | Dec 15 ~11:30 | levee_incident | basin | **Desimone levee (Green River, Tukwila) breach**; King County "GO NOW" 11:51; > 500 evacuated; industrial areas flooded | S34,S38 | OPEN (exact time) |
| 103 | 12-15T19:51Z | Dec 15 11:51 | flash_flood_warning | county | **FF.W.0001** "Failure of Green River Levee" (251215T1951Z–251216T0500Z), corrected 12:11 PST | S4 | 19:51Z |
| 104 | 2025-12-15 | Dec 15 | reservoir_action | basin | HHD releases cut by 1,000 cfs after the breach (target had been 10,000 cfs at Auburn) | S15 | OPEN (time) |
| 105 | 12-16T09:20Z | Dec 16 ~01:20 | levee_incident | basin | **White River HESCO levee failure, Pacific**; ~100 rescued, ~220 homes evacuated; NWS alerts 01:35–01:39 | S35 | OPEN (exact time) |
| 106 | 12-16T09:30Z | Dec 16 ~01:30 | note | county | First WA fatality (driver, submerged car near Snohomish) | S26 | OPEN |
| 107 | 12-16T09:39Z | Dec 16 01:39 | flash_flood_warning | county | **FF.W.0002** "Levee Failure on the White River", City of Pacific (to 251216T1545Z) | S4 | 09:39Z |
| 108 | 2025-12-16 | Dec 16 | declaration | state | Proclamation 25-07.1 amended: 14 counties, $3.5 M relief; > 1,200 rescues/evacuations | S20 | OPEN (time) |
| 109 | 12-16T20:00Z | Dec 16 12:00 | reservoir_action | basin | HHD 10,000-cfs target restored; reservoir down 26 ft from peak; MMD release increases delayed then stepped by 500 cfs | S15,S38 | 2025-12-17 |
| 110 | 12-18T04:15Z | Dec 17 20:15 | crest_observed | fp | MVEW1 second crest 30.92 ft / 81,500 cfs (NWPS 30.93 ft "04:00Z", P) | S2,S3 | valid+~15 min (backfilled) |
| 111 | 12-21T09:15Z | Dec 21 01:15 | crest_observed | fp | MVEW1 third pulse 24.05 ft (action/minor) | S2 | valid+~15 min (backfilled) |
| 112 | 2025-12-23 | Dec 23 | note | region | CW3E event summary published (AR4/AR3, ~96 h) | S8 | 2025-12-23 |
| 113 | 12-31T00:55Z | Dec 30 16:55 | note | county | King County Flood Warning Center closed; 22-day event (Dec 8–30); 43 Flood Alerts | S38 | 2026-02 (report) |
| 114 | 2026-04-07 | — | declaration | state | FEMA DR-4906 declared; incident period 2025-12-05..19 | S21,S22 | 2026-04-07 |
| 115 | 2026-07-20 | — | note | basin | USACE preliminary damages-prevented analysis (~$8.7 B total) | S13 | 2026-07-20 |

## 6. Reservoir and flood-control operations

- **FACT** — Ross (SCL) and Upper Baker (PSE): USACE Reservoir Control Center assumed Section 7 control Dec 8; Ross
  inflow peaked ~50,000 cfs Dec 11 while outflow was cut to 450 cfs; peak pool 1,594.53 ft at 04:00 PST Dec 12;
  control reassumed 08:30 PST Dec 15; Concrete ~56,000 cfs on Dec 17 (S11; EZ:USACE[0]). KUOW/OPB reported the USACE
  preliminary estimate that Skagit operations shaved 4–5 ft off the ~37-ft peak and that Ross held back ~99 % of
  inflow (S14; EZ:USACE[3]). Section 7 reservoirs (Ross, Upper Baker, Wynoochee) ~$746 M damages prevented (S13).
- **INFERENCE** — The "~99 %" is consistent with 450 / 50,000 cfs; it is a reported estimate, not a measured series.
  A Skagitonians claim of 7–8 ft held back is unverified (EZ:USACE[3]) — do not use.
- **FACT** — Howard A. Hanson (Green): pool 1,189 ft / 77,000 af / 74 % at 09:00 PST Dec 12 (Dec 13 release);
  record pool 1,189.3 ft / 77,700 af / ~75 % of flood storage, Green River peak reduced ~58 % and stage > 5 ft,
  ~$7.8 B prevented (Jul 2026 analysis); normal flood-ops target 12,000 cfs at Auburn (S12, S13; EZ:USACE[1–2]).
  After the Desimone breach, releases were cut by 1,000 cfs (target had been 10,000 cfs at Auburn) and the 10,000-cfs
  target restored from noon Dec 16; reservoir 26 ft below peak by Dec 16 (S15; EZ:USACE[4]).
- **FACT** — Mud Mountain (White): peak pool ~1,185 ft / 74,600 af / 70 % at 20:00 PST Dec 12; ops release "as fast
  as possible" while keeping Puyallup at Puyallup below 50,000 cfs (S12); ~2 ft stage reduction through Puyallup,
  ~$215 M prevented (S13); after the Pacific HESCO breach, release increases were delayed and then stepped by 500 cfs
  (S38; EZ:USACE[4]). Consequence visible in §3: Puyallup at Puyallup stayed *minor* (28.67 ft) at 44,400 cfs, and the
  White River record at R St occurred on Dec 15 during drawdown, not during the AR peak.
- **FACT** — Spada Lake (Snohomish PUD) rose 15 ft in two days and reached the Culmback Dam spillway by 18:50 PST
  Dec 10; Jackson project run at full capacity; Sultan River rising from spill Dec 11 (S16; EZ:USACE[5]).
- **OPEN QUESTION** — Upper Baker / Baker Lake pool and outflow; Tolt Dam and Chester Morse / Masonry Dam operations
  (SPU): no quantitative data found (S17; EZ:USACE[6]). Candidate recovery paths: USGS IV 12191600 (Baker Lake
  elevation), 12193000 (Lake Shannon), 12175000 (Ross Lake), 12115900 (Chester Morse), 12147900 (SF Tolt) all
  reported elevation/storage on 2026-08-22 (S52-res), so Dec 2025 pool series are plausibly retrievable — INFERENCE
  until queried.
- **FACT** — Auburn Reporter's "44,400 acre-feet" for Howard Hanson conflicts with USACE's 77,000–77,700 af; the USACE
  figure is authoritative (EZ:USACE limitations).

## 7. Data-availability audit for the hindcast

"Recoverable" = can a product valid in Dec 2025 be retrieved on 2026-08-22. "available_at metadata" = what the archive
exposes about *when* the value became retrievable. Rule per ADR-0010: publication time known → use it; otherwise
`backfilled=true` with the stated approximation. Archive-depth facts are from the `historical_depth`/`latency` fields
of the research files (S52) unless cited otherwise.

| Product family | Dec 2025 recoverable? | From where | available_at metadata | Backfill rule |
|---|---|---|---|---|
| USGS IV stage/flow (15-min) | **Yes** — legacy IV 2007-10-01→present (decommission early 2027); OGC `continuous` capped at 3 years per request, so Dec 2025 is inside the window until ~Dec 2028 | `waterservices.usgs.gov/nwis/iv` (S2) → migrate to `api.waterdata.usgs.gov/ogcapi/v0/collections/continuous` | None for the *provisional* values as they existed in Dec 2025: today's series carry `A` for most sites and `P` for 12149000, 12144500 (flow), 12119000, 12117500, 12186000, 12167000 (S2b). OGC `last_modified` is a DB refresh time, not a change indicator; `time-series-revisions` collection exists (S51) — contents for Dec 2025 untested | Store current values as revision rows; `available_at = valid_time + 15 min` (observed IV latency ~15 min; S52-hyd), `backfilled=true`. Approved (`A`) values get `revision_of` → provisional and `available_at` = unknown approval time (OPEN) |
| USGS peaks (annual) | Not yet — WY2026 approved peaks unpublished (EZ:USGS historical_depth; EZ:ANTE[10]) | OGC `peaks` collection (added Jun 2026) | n/a | Outcome-only when published; never a replay input |
| NWPS gauge API (thresholds, crest table, impacts) | Thresholds/impacts: **current snapshot only**; crest table: **yes** (preliminary `P` entries; RNTW1/ARLW1 missing) | S3 | None ("no historical data other than crest and low water history"); crest entries appeared "within days" (EZ:NWPS latency) | `Threshold` rows with `retrieved_at` = 2026-08-22, `effective_from` unknown (INFERENCE that Dec 2025 thresholds equalled today's — verify against FLS "Flood stage is 28.0 feet" lines, S4b). Crest rows are outcomes only: `available_at = retrieved_at` |
| NWPS / NWRFC official forecast runs | **No** — NWPS serves only the latest forecast; HEFS serves ~10 days; NWRFC downloads keep only the last forecast per day for effective-local-flow | — | — | **Reconstruct from products**: every FLW/FLS crest statement becomes a `ForecastRun` (`product_id = nws_fls_crest`, `issued_at` = header time, `supersedes_run_id` chain per LID) with `ForecastValue` (crest stage, crest time bin). `backfilled=true` is *not* required (issuance time is FACT), but `model_version = "NWRFC via WFO text"` must flag that the 6-hourly hydrograph is lost |
| NWS text products (ESF/FFA/FLW/FLS/FFW/AFD/PNS) | **Yes** — IEM AFOS archive back to ~2001, issuance to the minute; api.weather.gov keeps ~7 days | S4 (`retrieve.py`), S5 (VTEC JSON) | Product header time (FACT); IEM VTEC `issue` reflects event begin, not transmission — use the header | `RawArtifact` per product; `OfficialAlert` with `issued_at` = header time; no backfill flag. Caveat: EZ summaries were LLM-extracted — re-parse raw text (T3) |
| MRMS QPE (RadarOnly 1H, MultiSensor Pass1/Pass2, RQI) | **Yes** — AWS `noaa-mrms-pds` from 2020-10-14; IEM mtarchive from 2014-11 (subset) | S52-precip | S3 object `LastModified` (observed today: Pass1 ~16 min, Pass2 ~57 min after valid). INFERENCE that Dec 2025 objects retain their original upload stamps | `GridProduct.issued_at` = LastModified; `backfilled=false` if stamp present, else `valid_time + 60 min`, `backfilled=true`. Beam blockage west of the crest: ingest RQI alongside |
| Stage IV QPE | **Yes** — NCAR EOL 2001-12-31→2026-05-31; NWPS daily since 2016-06-28; NOMADS ~7 days | S52-precip | None; western-RFC data appear only in re-issues (T+2–7 d) | Reanalysis product: `available_at = valid_time + 7 d`, `backfilled=true`; never a T-time forcing input |
| HRRR / NBM / GFS / GEFS | **Yes** — AWS: HRRR from 2014-07-30; NBM from 2020-05-18 (v4.3 was operational Dec 2025; v5.0 from 2026-05-05); GFS 0.25° from 2021-01-01; GEFS from 2017/2020 | S52-wx | S3 `LastModified` (observed today: HRRR +53–106 min, NBM +72–78 min, GFS +3.6–5.3 h, GEFS +3.8–6.6 h) — INFERENCE that Dec 2025 stamps are original | `ForecastRun.issued_at` = cycle; `available_at` = LastModified when present else cycle + observed lag, `backfilled=true` |
| WPC QPF / ERO | **No** — ftp listing ~2 weeks, shapefiles ~2 months | — | — | OPEN QUESTION (§9); the Dec 4 10:22Z 7-day QPF survives only as an image in S50 |
| CW3E AR scale / IVT outlooks | Pages only (Dec 3, 8, 12, 15, 17 outlooks; Dec 23 summary); no data archive | S6–S10 | Page dates (day resolution) | `EventTimelineEntry` notes, day-resolution `available_at`; Dec 5 outlook page not located |
| SNODAS | **Yes** — NSIDC G02158 2003-09-30→present; same-day publication (server stamp ~13:00Z for 06Z valid) | S52-snow | NSIDC directory file timestamps (INFERENCE that Dec 2025 stamps are original) | `GridProduct.available_at` = file stamp else `valid_time + 7 h`, `backfilled=true` |
| SNOTEL (AWDB) | **Yes** — full period of record served (Harts Pass hourly from 1979-10-01) | S51, S52-snow | None; hourly latency ~1 h; daily value D = 00:00 PST reading of D+1 (`periodRef=END`); qcFlag edits possible; qaFlag `P` | `available_at = valid_time + 1 h`, `backfilled=true`; store provider day boundary (DATA_DOCTRINE §3) |
| SMAP L3 (SPL3SMP_E v6) / L4 (SPL4SMGP v8) | **Yes** — 2015-03-31→present; the 14 May–28 Jul 2026 geolocation defect window does **not** touch Dec 2025 | S52-snow | L4 latency ~2.7 d; L3 daily | `available_at = valid_time + 3 d` (L4) / + 1 d (L3), `backfilled=true`; mountain cells flagged — lowland use only |
| NWM v3.0 operational (AnA, short/medium/long range) | **Yes, for now** — `noaa-nwm-pds` lists daily prefixes from nwm.20250101 (599 prefixes on 2026-08-22) although the registry states a four-week rollover; retrospective v3.0 ends Jan 2023 | S52-hyd | S3 `LastModified` (observed today: AnA ~44 min, short ~1 h 45, medium ~6.5 h, long ~9 h) | **Copy Dec 1–22 immediately** (T6); `available_at` = LastModified, else cycle + lag, `backfilled=true`; tag `model_version = v3.0` (v3.1 operational only from 2026-08-18) |
| USACE CWMS (CDA / A2W): HHD, MMD pool, inflow, outflow | **Yes (INFERENCE)** — HAH hourly forebay extents 1991-03-14→2026-08-22; a 2012 window returned data; `MMD.Flow-Out` JSON works | S52-res | None; catalog `last-update` ~30 min after latest value today | `available_at = valid_time + 1 h`, `backfilled=true`; `-REV` series are revised — flag revision unknown |
| USACE/utility reservoirs via USGS IV (Ross 12175000, Baker Lake 12191600, Lake Shannon 12193000, Chester Morse 12115900, SF Tolt 12147900, Lake Tapps 12101000) | Plausible (INFERENCE; Dec 2025 not queried) | S2 pattern | as USGS IV | as USGS IV |
| County data | King County HIC: 15-min historical county gauges; KC FCD report PDF (Feb 2026, text extraction garbled); Skagit County press releases (dated); Snohomish OneRain portal redirects to login (2026-08-22) | S38, S27, S52-res | Press-release dates; HIC unknown | `EventTimelineEntry` with `available_at` = publication date; ARLW1 observations depend on Snohomish County access (OPEN) |
| Declarations | OpenFEMA API (fetched 2026-08-22) gives `declarationDate` (day resolution); governor pages dated | S21, S18, S20 | Day resolution; 25-07 time 14:14 PST from press (S19) | `EventTimelineEntry`; `available_at` day-resolution flagged |

## 8. Reconstruction plan

Ordered; each task names the `DOMAIN_MODEL.md` entities it writes and an acceptance criterion (AC).

| # | Task | Entities | Acceptance criterion |
|---|---|---|---|
| T1 | Create the event: `id = event-zero-2025-12`, `start = 2025-12-03T00:00-08:00` (AR1 landfall, S6), `end = 2025-12-22T23:59-08:00` (state incident window, S23), `basins[]` = Skagit, Sauk, Baker, Nooksack, Stillaguamish, Snohomish/Skykomish/Snoqualmie, Cedar, Green, White/Puyallup/Carbon, Cowlitz, Chehalis, Skokomish, Elwha; `sources[]` = EZ + S-key | `HistoricalEvent` | Row exists; `summary` = §2 with labels preserved; every `sources[]` entry resolves |
| T2 | Ingest NWS text products Dec 1–22 from IEM AFOS for PILs ESFSEW, FFASEW, FLWSEW, FLSSEW, FFWSEW, AFDSEW, PNSSEW (and VTEC JSON); store raw; parse headers and VTEC | `RawArtifact`, `OfficialAlert` | Product count per PIL matches the IEM listing; every `OfficialAlert.issued_at` = header time in UTC; the rows for #6, #25, #47, #56, #103, #107 in §5 are reproduced byte-exact from raw text |
| T3 | Parse per-forecast-point segments of FLW/FLS into forecast runs: crest value, crest time bin, category wording, observed stage cited; chain `supersedes_run_id` per LID | `ForecastRun`, `ForecastValue` | The MVEW1 chain equals the forecast-evolution dataset below (6 runs, issuance times exact); no run without a `raw_artifact_id`; look-ahead audit (below) passes at every T |
| T4 | Seed the timeline from §5; each entry's `ref` points to the `RawArtifact`/`Observation` row that is its evidence; entries with OPEN `available_at` carry `backfilled=true` and a `text` suffix "(time unverified)" | `EventTimelineEntry` | 115 rows; every row has `source_url`; count of `backfilled=true` rows reported in the hindcast report |
| T5 | Backfill point observations Dec 1–31: USGS IV (the 27 sites of §3 plus 12150400, 12106700 and the reservoir gauges); SNOTEL daily+hourly WTEQ/PREC/TOBS/SMS for all WA sites; USACE CWMS HHD/MMD series; NWPS thresholds snapshot | `Observation` (with `revision_of`), `Threshold`, `RawArtifact` | Peak of each stored series equals §3 within 0.01 ft / 1 % flow; every row has `available_at` per §7 rule and `backfilled=true`; qualifier `A`/`P` preserved in `qualifier_raw`; Harts Pass daily values stored on the PST day boundary |
| T6 | Archive grids Dec 1–22 (priority order): NWM v3.0 AnA + short/medium range (rollover risk), MRMS Pass2 1H + RQI, HRRR, NBM v4.3, GFS, GEFS, SNODAS, Stage IV (EOL); record S3 `LastModified`; compute basin aggregates | `GridProduct`, `DerivedFeature` | Every cycle in the window indexed; `issued_at`/`available_at` populated from object stamps where present (count reported); basin 24-h QPE for Dec 9–11 reproduces the ordering of the PNS totals (#71) to rank correlation ≥ 0.8 |
| T7 | Resolve outcome ledger conflicts (§3 notes a–e) by re-fetching NWPS crest tables and USGS approved data; record each as two rows (USGS vs NWPS), never a merged value | `Observation`, note rows | Each conflict has both rows and a `note` `EventTimelineEntry`; none silently reconciled |
| T8 | Build the forecast-evolution dataset (below) for MVEW1, CONW1, SNAW1, MROW1, NRKW1, RNTW1, ARLW1, TOLW1 as a view over `ForecastRun`/`ForecastValue` vs the observed crest | view | MVEW1 view returns the six rows below; TOLW1 shows the 9,867-cfs MAJOR forecast vs 6,540 cfs observed |
| T9 | Hindcast harness runs at clock times T = {#3, #6, #9, #25, #30, #47, #56, #63, #87} of §5 (each a real issuance instant) with `as_known_at(T)`; metrics per `TESTING.md` §7 | `HindcastRun` | Report committed with the look-ahead audit output (zero violations), lead-time table per basin, and the §9 list carried forward |

Forecast-evolution dataset — Skagit nr Mount Vernon (observed crest 37.73 ft at 2025-12-12T08:15Z; error =
forecast − observed, arithmetic on FACT values from S4/S4b):

| Issued (UTC) | Issued (PST) | Product | Forecast crest | Forecast crest time | Observed stage cited | Error (ft) |
|---|---|---|---|---|---|---|
| 12-09T17:01Z | Dec 9 09:01 | FLW NEW FL.W.0042 | 36.9 ft | early Fri Dec 12 | 25.3 ft | −0.83 |
| 12-10T01:24Z | Dec 9 17:24 | FLS | 41.5 ft | early Fri | — | +3.77 |
| 12-10T09:24Z | Dec 10 01:24 | FLS | 41.5 ft | — | — | +3.77 |
| 12-10T23:14Z | Dec 10 15:14 | FLS | 42.3 ft | Fri AM | — | +4.57 |
| 12-11T01:15Z | Dec 10 17:15 | FLS | 42.1 ft | — | — | +4.37 |
| 12-11T10:04Z | Dec 11 02:04 | FLS | 39.1 ft | late Fri AM | — | +1.37 |
| 12-11T18:17Z | Dec 11 10:17 | FLS EXT | 39.1 ft | early Sat (text) | 29.5 ft at 01:15 | +1.37 |
| 12-12T01:12Z | Dec 11 17:12 | FLS EXT | 38.3 ft (press: 38.26) | late tonight | 35.8 ft at 16:15 | +0.57 |
| 12-12T08:50Z | Dec 12 00:50 | FLS EXT | 38.1 ft | early this morning | 37.7 ft at 00:15 | +0.37 |

Concrete for comparison (observed 40.99 ft): 37.6 (Dec 8 22:15 PST, −3.4) → 47.4 (Dec 9 17:24, +6.4) → 47.7 (Dec 10
01:24, +6.7) → 46.1 (Dec 10 17:15, +5.1) → 41.1 "cresting now" (Dec 11 02:04, +0.1). INFERENCE: the Skagit
over-forecast of Dec 9–10 coincides with the period before the Section 7 cut of Ross outflow to 450 cfs was reflected
in forecasts; T8/T9 must test this against the HHD/MMD-regulated Green and White, where the forecast trajectory was
different (Green nr Auburn 10,705 → 12,829 → 12,184 cfs vs 12,100 observed).

Look-ahead audit procedure (harness, `TESTING.md` §7): for each replay clock Tᵢ, (1) log `available_at` of every input
row; any `available_at > Tᵢ` fails the run; (2) assert no `Observation` with `qualifier_raw = A` or
`approval_status = Approved` is visible before event end (approval time unknown → such rows carry
`available_at = retrieved_at`); (3) assert NWPS crest-table rows, CW3E event summary (#112), USACE releases (#89, #91,
#96 carry `available_at` = 2025-12-13), OWSC analyses and FEMA DR-4906 are invisible before their publication dates;
(4) assert Stage IV and any re-issued QPE are invisible for 7 days after valid time; (5) assert forecast runs are
selected by `issued_at ≤ Tᵢ` and by `supersedes_run_id`, so that at T = #47 the MV crest is 42.3 ft and at T = #63 it
is 39.1 ft; (6) assert VTEC-derived times are never used as `issued_at`; (7) emit the share of inputs with
`backfilled=true` per product family as a headline number of the hindcast report.

## 9. Open questions (deduplicated, as actions)

1. Obtain the ARLW1 observed crest and time for Dec 11 from Snohomish County (OneRain, login) or NWPS once entered;
   until then keep the row OPEN (§3; EZ open question 1).
2. Ask NWS Seattle / NWRFC which NRKW1 record (149.6 ft 2003 vs 150.76 ft 2021) was in the operational ledger on
   Dec 11, and whether the 2021 crest was revised after the event (§3 note c).
3. Determine whether SNAW1 34.45 (USGS) vs 34.15 ft (NWPS, `R`) is a datum/sensor difference or a post-event revision;
   request the NWPS crest-stamp time-zone convention (§3 note a).
4. Re-fetch RNTW1 and ARLW1 crest tables monthly until the Dec 2025 entries appear; record the date they appear as
   the NWPS-side `available_at` (§3 note d).
5. Resolve the CRNW1 duplicate Dec 11 crest entries with NWPS (§3 note b).
6. Retrieve Upper Baker / Baker Lake, Ross Lake, Lake Shannon, Chester Morse and SF Tolt pool series for Dec 1–22 from
   USGS IV and Tolt/Masonry operations from SPU; confirm or close the "operator data web-only" risk (§6).
7. Locate the CW3E Dec 5 AR outlook (AR5 probability wording) and any CW3E archive of AR-scale forecasts; otherwise
   record Dec 5 forcing as second-hand (EZ:CW3E[5]).
8. Recover WPC QPF/ERO issuances for Dec 3–11 (risk categories, 7-day QPF) from WPC or NCEI; otherwise mark WPC as
   non-recoverable for Event Zero (§7).
9. Copy NWM v3.0 Dec 2025 outputs from `noaa-nwm-pds` before any rollover and document the bucket's actual retention
   policy with NOAA OWP (§7).
10. Pull USGS IV for Dec 1–8 for all §3 sites to quantify the AR1/AR2 response and base-flow elevation before AR3;
    quantify statewide and per-basin SWE % on Dec 1 and Dec 8 from SNOTEL/SNODAS (§4).
11. Reconcile the State EOC Level 1 activation date (Dec 9 per the Governor's letter vs 15:30 PST Dec 10 per HeraldNet)
    (§5 #48).
12. Recover the exact times for #8, #29, #33, #45, #90, #93, #102, #104, #105, #108 (Section 7 takeover, county
    actions, FEMA EM, breaches, amended proclamation) from primary releases.
13. Extract the King County FCD report and the Governor's IA/PA enclosures with a working PDF text pipeline (current
    extraction garbled): gauge-by-gauge Flood Phase tables and the Mount Vernon Dec 5–21 hydrograph figure.
14. Obtain Cowlitz at Packwood (PACW1) and Mud Mountain outflow (MMRW1) peaks and the LIDs for Sauk, Marblemount,
    Sedro-Woolley, Pilchuck, NF/SF Stillaguamish (§3).
15. Verify that Dec 2025 NWPS flood-category thresholds equalled the 2026-08-22 snapshot using "Flood stage is X feet"
    lines in the FLS products (T5).
16. Check for a later NWS service assessment, Storm Data narrative, USGS WY2026 approved peaks, and the USGS
    `time-series-revisions` content for these sites; when they appear, add revision rows rather than overwriting.

## 10. Source key

- **EZ** — `docs/research/event-zero-december-2025-western-washington-floods.json` (providers: USGS, NWPS, NWS, CW3E,
  USACE, DECL, LOCAL, ANTE; row index in brackets).
- **S2** — USGS IV, e.g. `https://waterservices.usgs.gov/nwis/iv/?format=json&sites=12200500&parameterCd=00060,00065&startDT=2025-12-08T00:00-0800&endDT=2025-12-14T00:00-0800` (EZ:USGS[0–11]); research scratch captures `usgs_iv_peaks_dec2025.json`, `usgs_iv_peaks_late_dec2025.json`.
- **S2b** — research scratch capture `usgs/<site>.json` + `peaks.py`, fetched 2026-08-22 from `https://nwis.waterservices.usgs.gov/nwis/iv/?format=json&sites=<site>&parameterCd=00060,00065&startDT=2025-12-08T00:00-0800&endDT=2025-12-22T00:00-0800` (qualifiers `A`/`P`).
- **S3** — NWPS gauge API `https://api.water.noaa.gov/nwps/v1/gauges/{LID}` (EZ:NWPS[0–15]); research scratch captures `nwps/{MVEW1,CONW1,SNAW1,CRNW1,GLBW1,ARLW1,PUYW1}.json` (2026-08-22 02:03 PDT); `docs/research/nwps-usgs-awdb-samples-2026-08-22.json` (`mvew1_gauge.flood.crests`, `.impacts`). **S3b** — RNTW1 and NRKW1 re-fetched 2026-08-22 13:17Z (scratch `nwps_RNTW1.json`, `nwps_NRKW1.json`).
- **S4** — IEM AFOS `https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?pil={ESFSEW|FFASEW|FLWSEW|FLSSEW|FFWSEW|AFDSEW|PNSSEW}&sdate=…&edate=…` (EZ:NWS[0–12]). **S4b** — same, `pil=FLSSEW&sdate=2025-12-11T12:00Z&edate=2025-12-12T12:00Z&limit=80`, fetched 2026-08-22 (scratch `flssew_dec11.txt`, 70 products).
- **S5** — `https://mesonet.agron.iastate.edu/json/vtec_events.py?wfo=SEW&year=2025` (EZ:NWS[11]).
- **S6** `https://cw3e.ucsd.edu/cw3e-ar-update-3-december-2025-outlook/` · **S7** `…/cw3e-ar-update-8-december-2025-outlook/` · **S8** `https://cw3e.ucsd.edu/cw3e-event-summary-8-12-december-2025/` · **S9** `…/cw3e-ar-update-12-december-2025-outlook/` · **S10** `…/cw3e-ar-update-15-december-2025-outlook/`.
- **S11** `https://www.dvidshub.net/news/555482/army-corps-regulates-peak-flow-mitigate-extensive-flooding-skagit-county` · **S12** `https://www.dvidshub.net/news/555484/army-corps-releases-water-howard-hanson-dam-and-mud-mountain-dam-reservoirs-prepares-predicted-rain-events` · **S13** `https://www.dvidshub.net/news/570366/usace-dams-reduced-flood-risk-during-december-2025-storms-helped-prevent-billions-potential-damages` · **S14** `https://www.kuow.org/environment/2025-12-15/army-takeover-of-skagit-dams-lowers-flood-waters` · **S15** `https://www.auburn-reporter.com/2025/12/17/army-corps-adjust-hanson-dam-flows-to-combat-green-river-flooding/` · **S16** `https://www.heraldnet.com/2025/12/10/updates-snohomish-pud-plans-to-open-spada-lake-spillway/` · **S17** `https://www.carnationwa.gov/2025-flood-event-resources/`.
- **S18** `https://governor.wa.gov/news/2025/governor-ferguson-declares-statewide-emergency-responding-major-flooding` · **S19** `https://www.cascadiadaily.com/2025/dec/10/skagit-county-asking-residents-in-flood-plain-to-get-set-for-evacuation/` · **S20** `https://governor.wa.gov/news/2025/governor-ferguson-amends-emergency-proclamation-directs-35m-support-flood-impacted-washingtonians` · **S21** OpenFEMA `https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=disasterNumber eq 3629` and `… eq 4906` (fetched 2026-08-22) · **S22** `https://www.govinfo.gov/content/pkg/FR-2026-04-16/html/2026-07430.htm` · **S23** `https://mil.wa.gov/december-2025-atmospheric-river-flooding` · **S24** `https://komonews.com/news/local/skykomish-river-nears-record-as-flooding-intensifies-across-snohomish-county-when-will-the-skykomish-river-crest-state-of-emergency` · **S25** `https://governor.wa.gov/sites/default/files/2026-03/WA_PA%20Major%20Disaster%20Declaration-December%202025%20Winter%20Storms%20with%20Enclosures.pdf` (scratch `gov_pa_request.txt`) · **S26** `https://www.ksat.com/news/national/2025/12/16/a-driver-is-found-dead-in-a-submerged-car-near-seattle-after-a-week-of-heavy-rain-and-flooding/`.
- **S27** `https://www.skagitcounty.net/Departments/Home/press/120925-3.htm` and `…/121025b.htm` · **S28** `https://www.cascadiadaily.com/2025/dec/10/skagit-river-near-mount-vernon-expected-to-reach-record-levels-thursday-night/` · **S29** `https://www.cascadiadaily.com/2025/dec/11/thursday-update-skagit-county-under-evacuation-nooksack-river-at-cedarville-crests/` · **S30** `https://www.goskagit.com/news/local_news/skagit-river-reaches-record-height-in-mount-vernon/article_ebaf24a5-8456-4865-a8ac-38011889cc0e.html` · **S31** `https://www.skagitonians.org/blog/when-the-river-kept-rising-flooding-on-the-skagit-december-2025` · **S32** `https://www.whatcomcounty.us/CivicAlerts.aspx?AID=5266` · **S33** `https://lynnwoodtimes.com/2025/12/11/flood/` · **S34** `https://www.rentonreporter.com/2025/12/15/green-river-levee-breach-impacts-small-areas-of-kent-renton-and-tukwila/` · **S35** `https://www.auburn-reporter.com/2025/12/16/pacific-residents-evacuate-amid-white-river-levee-breach/` · **S36** `https://www.rentonreporter.com/2025/12/10/moderate-flooding-expected-for-cedar-river/` · **S37** `https://mynorthwest.com/local/puyallup-river-flooding-forces-evacuations-in-orting-puyallup/4172094` · **S38** `https://kingcountyfloodcontrol.org/flood-event-report-historic-december-8-30-2025-flooding-in-king-county/` and `https://kingcountyfloodcontrol.org/wp-content/uploads/2026/02/FINAL-Dec-8-30-Flood-Event-Report.pdf` (scratch `kc_fcd_dec2025.txt`, garbled) · **S39** `https://www.valleyrecord.com/2025/12/19/flooding-sets-records-in-some-parts-of-the-snoqualmie-valley/` · **S40** `https://www.kiro7.com/news/local/see-which-rivers-are-major-flood-stage-when-well-see-some-relief/M27KZHAINZHXLKMCMTZQMN5FEY/`.
- **S41** `https://climate.uw.edu/2025/12/06/november-2025-drought-and-snowpack-update` · **S42** `https://climate.uw.edu/2026/01/12/december-2025-snowpack-and-drought-summary/` · **S43** `https://climate.uw.edu/2026/01/13/december-8-11-2025-heavy-rainfall-and-flooding-historical-context-and-a-note-on-snow-drought/` · **S44** `https://climate.uw.edu/2026/02/07/just-how-big-were-the-december-2025-floods/` · **S45** `https://www.valleyrecord.com/northwest/flood-science-how-decembers-atmospheric-river-soaked-wa/` · **S46** `https://ecology.wa.gov/blog/january-2026/did-record-rainfall-end-washington-drought` · **S47** `https://weather.com/forecast/regional/news/2025-12-07-atmospheric-river-pacific-northwest-rain-snow` · **S48** `https://usatoday.github.io/202512_washington-floods/methods.html` · **S49** `https://gpm.nasa.gov/applications/weather/news/nasa-tracks-tropical-moisture-flooding-washington` · **S50** `https://essic.umd.edu/pacific-northwest-atmospheric-rivers-catastrophic-flooding/` · **S53** `https://emeraldcityweather.com/atmospheric-river-flooding-washington-cascades-skagit-snohomish-river/`.
- **S51** — `docs/research/v1-live-verification-2026-08-22.json` (`awdb.dec2025_wteq_harts_pass`, AWDB REST `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data`; `new_usgs_api` collections list incl. `peaks`, `time-series-revisions`).
- **S52** — archive-depth evidence (`historical_depth`, `latency`, `limitations` fields): `docs/research/hydrology-observations-and-official-forecasts.json` (hyd), `precipitation-observations.json` (precip), `weather-forecast-models-and-atmospheric-rivers.json` (wx), `snow-and-soil-state.json` (snow), `reservoirs-dams-and-flood-control.json` (res).
- Whatcom County "Flooding in Whatcom County" newsletter (scratch `whatcom_newsletter.txt`) is a pre-event annual newsletter; not used as event evidence (EZ:LOCAL limitations).
