# Method specification — what the platform computes, in what order, from what

*2026-08-24. Synthesis of the twelve `docs/research/corpus/` domain entries into an implementable
build. Companion to `docs/research/p3-surfaces-design-2026-08-24.md`, which specifies what already
ships.*

**Binding constraint applied throughout.** The test of relevance is a **6–120 h flood prediction for
a named western-Washington basin**. Every method below carries a *6–120 h payoff* line saying how it
changes that prediction. Anything that could not answer that line is in §6 (not worth building) or is
marked NON-OPERATIONAL CONTEXT.

**Three categories held apart, per the constraint.** MEASUREMENT (instrument records — admissible and
preferred), PHYSICS (Clausius–Clapeyron and the like — admissible as a constraint, never as a transfer
coefficient), PROJECTION (GCM/RCM futures — **not admissible operationally**; see §7 for what was
quarantined and why the platform's own `DATA_DOCTRINE.md` §11/§9/§2 already excluded it).

---

## 0. The shape of the answer

Twelve domains produced roughly ninety P0/P1 platform implications. Deduplicated they collapse to
**eighteen distinct demands** (§1), which resolve into **thirty-one methods in six dependency tiers**
(§2–§4). Three things dominate:

1. **The platform's existing surfaces claim precision they cannot support, and the fix is free.** A
   day-of-year percentile has a sampling SD of ±5.5–6.2 points at a 30-year ladder against band edges
   15 points apart (climate-change §2.4); it saturates at p95 across a 2.5× flow range during the
   defining event of the record (climate-change §2.5); and its entire Event Zero signal lived in a
   derivative the surface does not compute (antecedent-conditions §3.1(f)). Tier 0 fixes all of this
   with no new provider.
2. **Basin hypsometry is the single largest structural blocker.** Snow, orography, atmospheric-river
   orientation and elevation-band anything all terminate on it. It is a one-time compute with
   essentially zero steady-state cost.
3. **The highest-value new science is terrain-projected IVT with duration and orientation** — the only
   atmospheric quantities with published variance-explained numbers against *runoff* (74 % / 61 %,
   Ralph et al. 2013; r² = 0.85 over the Olympics, Tierney & Durran 2024) and the only western-
   Washington-specific flood discriminator in the literature (Neiman et al. 2011, Green 245°–275°,
   separation at >95 %). None of it exists in `forcing.py`, which bands on one scalar.

---

## 1. The deduplicated implication set

Where two or more domains independently demanded the same thing, that is recorded — independent
arrival is the strongest evidence a demand is real.

| # | Demand | Domains that raised it independently | Resolves to |
|---|---|---|---|
| D1 | Basin hypsometry / elevation–area curve | snow (§6, "single largest structural blocker"), orographic (§6 P0), atmospheric-rivers (M4/M7), climate-change (§7 item 12) | M2.1 |
| D2 | A percentile must carry period, sampling interval, homogeneity epoch, and must not clamp at p95 | climate-change (§6.1–6.4), antecedent (§6.3 P0.2), flood-statistics (§6.4), cascading-hazards (§6.1) | M0.1 |
| D3 | Rate of change and hydrograph limb, not level alone | antecedent (§6.3 P0.1 — *Event Zero's whole signal*), runoff-generation (§6.2 `storage_limb`), routing (§6.2 conveyance anomaly), forecasting (D3 consistency) | M0.2, M0.3 |
| D4 | Terrain-projected (upslope) IVT, per basin, integrated over the event | atmospheric-rivers (M2, P0), orographic (§6 P0) | M3.2 |
| D5 | Duration of AR conditions, and duration-above-rate rather than a window total | atmospheric-rivers (M3, M9), runoff-generation (§6.2), snow (phase interference) | M3.3, M4.3 |
| D6 | Per-basin optimal onshore wind-direction window | atmospheric-rivers (M4), orographic (§6 P0) | M3.4 |
| D7 | Blocking flag M = Nh/U as a qualifier on QPF confidence, never a multiplier | orographic (§6 P0) | M3.5 |
| D8 | Rating epoch, rating id/shift, measurement quality, control condition on every rated value | routing (§6.2), cascading-hazards (§6.2), climate-change (§6.7), flood-statistics (§6.4) | M1.3, M1.4 |
| D9 | Conveyance / stage–discharge drift as a first-class derived feature | routing (§5.2), cascading-hazards (§5.4), climate-change (§6.8) | M1.3 |
| D10 | Reservoir entity with **three** buffers, not one | regulation (§6.1), routing (§6.2), compound-coastal (§6.4) | M5.1 |
| D11 | Tidal class per forecast point, measured; de-tide before trend | compound-coastal (§6.1, §7.2 — a live bug), routing (§5.5 — refutes tide at Mount Vernon) | M1.5 |
| D12 | Basin QPE with an RQI gate and a per-cell engine label | orographic (§6 P0/P1), runoff-generation (§6.3 "highest-value new ingest"), cascading-hazards (§6.2 item 4), antecedent (§6.3 P1.6) | M4.3 |
| D13 | Couple antecedent state to forcing, and **hindcast before shipping any promote/demote rule** | antecedent (§6.3 P1.7), runoff-generation (§5.4 second computation), atmospheric-rivers (§4 emerging 2), flood-statistics (§8.1) | M6.2 |
| D14 | Buy the official probability (HEFS) before building one | forecasting (§6.2 M2, P0) | M4.1 |
| D15 | Snow-drought state, snow line as three distinct elevations, SWE below the snow line | snow (§6.2, all five methods) | M1.2, M2.3, M2.4 |
| D16 | Catchment storage sensitivity g(Q) as the physically motivated replacement for WaterWatch band edges | runoff-generation (§6.2) | M1.1 |
| D17 | Refuse recurrence intervals; publish rank-in-record instead | flood-statistics (§6.1, §6.3) | M0.5 + doctrine |
| D18 | An evaluation harness designed around rarity, with `UNVERIFIABLE` as a legitimate verdict | forecasting (§6.1 D1, §6.2 M5–M6) | M6.1 |

### 1.1 Where domains disagree, and the recommendation

| Disagreement | Position A | Position B | Recommendation |
|---|---|---|---|
| **How much antecedent state matters here** | runoff-generation §5.4: pre-event flow explains r² = 0.001–0.057 of peak magnitude at four unregulated gauges; antecedent §3.1(d): Spearman(pct at −7 d, cool-season peak) ≈ 0 | antecedent §3, quoting Webb et al. 2025 with storm-total precipitation controlled: Washington's group shows **2×** amplification above the ASM threshold — "low, not zero" | **Both are right and they measure different things.** Build the state estimate (M0.1/M0.2), never render LOW as reassurance (24–25 % of annual maxima at unregulated gauges were preceded by a below-25th-percentile state at −7 d), and settle the magnitude with the *conditional* hindcast M6.2. Do not ship a Webb-style promote/demote rule before M6.2 returns — the paper contains zero PNW catchments and names snow-influenced basins as its low-improvement group. |
| **Reference-period length for the ladder** | climate-change §2.3: full record wins at every tested length; "prefer the longest homogeneous record" | climate-change's own adversarial caveat: a recent-30 ladder beat the full record at **10 of 10** gauges on the 2016–2025 holdout and lost on 2006–2015 (PDO phase) | **Use the longest homogeneous record as the primary ladder** (homogeneity, not recency, is the binding constraint — a regulation split moves the ranking 9.9–11.1 percentile points, more than any climate term), and publish the WMO-aligned recent-30 ladder as a `climatology_vintage_sensitivity` **disagreement driver**, never as a correction (climate-change §6.6). |
| **Tide at Mount Vernon** | compound-coastal §3.1: Q–skew-surge dependence is real (ρ = +0.31, p ≪ 0.001) and P(p90 surge \| Q ≥ p95) is 2.5× independence | routing §5.5 + compound §3.4: measured tidal transmission at MVEW1 is **0.010 ft/ft**, the 30-winter backwater regression is null, and the USACE model puts the tidal limit ~7 river miles below the gauge | **Not in conflict once `tidal_class` is measured per point.** The *dependence* is a co-occurrence fact about the delta; the *transmission* is a hydraulic fact about the gauge. Build M1.5, badge MVEW1/NKSW1 `MARGINAL`, badge SNAW1 `TIDAL` (0.831 ft/ft, r = 0.94) and fix the live `trend.py`/`headroom.py` bug there. Do **not** wire a tide/surge term into the Mount Vernon or Ferndale forecast points. |
| **ROS melt energy partition** | snow §2.4: Marks et al. 1998 — 60–90 % turbulent in the wind-exposed 1996 extreme | snow §2.4: Mazurkiewicz et al. 2008 (8 yr, HJA) — net radiation leads at 33–55 %; Li et al. 2019 — 68 % CONUS | **Encode neither partition.** Encode the operational consequence both sides support: **wind speed and dewpoint at pack elevation discriminate an ordinary ROS event from an extreme one.** Until those inputs exist the ROS surface is UNKNOWN with that reason, and the snow-melt term carries the hard ceilings (<3 mm h⁻¹ net, <10 mm h⁻¹ total, never >14 mm h⁻¹, Jennings & Jones 2015) as range validation. |
| **Mixed-population flood frequency in WA** | flood-statistics §4: Barth et al. 2017 — the western-US AM series is a mixture whose tail is AR-dominated; pooling dilutes the tail | flood-statistics §4: USGS SIR 2016-5118 p. 23 — "no streamgages had substantially diverging distributions that required a mixed-population analysis" | **Moot for this platform: do not compute a frequency curve at all** (§6 item 1). The dispute is about a fitting choice inside a method Bulletin 17C already excludes for regulated basins, and USGS peak code 9 appears 3 times in ~900 western-WA peaks, so no objective separator exists. Publish rank-in-record (M0.5). |
| **Forest harvest and peak flows** | cascading-hazards §2.10: Grant et al. 2008 — no detectable effect beyond ~6-year return periods; basin-scale effect < interannual variability | cascading-hazards §2.10: Alila et al. 2009 and successors — chronological pairing cannot detect a frequency change in principle; frequency-paired effects *grow* with return period | **Keep it out of the hazard computation entirely**, and record the reason honestly as *unresolved method*, not as agreement between the camps. `forest_disturbance_pct` / `road_density_km_km2` / `effective_impervious_pct` are CONFIGURED basin attributes with both citations attached. |
| **Crest lag on the lower Skagit** | routing §5.1: measured crest-to-crest lag lengthens with magnitude (r = +0.65, n = 12) | routing §3: USACE 2013 §2.4.6.4 documents hydraulic travel time *shortening* with discharge (15–20 h → 10–15 h) | **Store the empirical lag distribution (median 16.9 h, sd 3.5 h), label it a storage-and-inflow statistic rather than a wave celerity, and do not assert the magnitude trend** until a crest-*centroid* timing method has been tried (the largest-lag event's argmax is tie-broken across 5.5 h). |
| **Nooksack conveyance drift magnitude** | cascading-hazards §5.4 table: +0.139 ft/decade at Ferndale, p = 0.0001 | cascading-hazards' own adversarial re-run: the stated Theil–Sen estimator gives **+0.065 ft/decade, p = 0.028** — the tabulated figure is an OLS fit | **Use +0.065 ft/decade** as the seeded anchor. This matters: at +0.065 the drift is *smaller* than the delta-progradation term (0.11 ft/decade, SIR 2019-5008), which strengthens the base-level reading over the supply reading. |

---

## 2. Dependency-ordered roadmap

```
TIER 0  corrections to what already ships — no new provider, no new cost
  M0.1 streamflow-doy-climatology@2.0.0 ──┬─> M0.2 susceptibility-index@0.2.0
  M0.3 rate-of-rise@2.0.0 ────────────────┘        │
  M0.4 model-agreement@0.3.0                       │
  M0.5 rank-in-record@1.0.0                        │
                                                   │
TIER 1  cheap DERIVED features, ≤1 new HTTP call per gauge per month
  M1.1 catchment-sensitivity@1.0.0 ────────────────┤ (supplies physical band edges)
  M1.2 snow-drought-state@1.0.0 ───────────────────┤ (AWDB already ingested)
  M1.3 rating-epoch@1.0.0 + conveyance-drift@1.0.0 ─┼─> bounds M0.1's ladder
  M1.4 gauge-control-quality@1.0.0                 │
  M1.5 tidal-transmission@1.0.0 ───────────────────┴─> fixes M0.3 at SNAW1

TIER 2  geometry foundation — everything elevation-dependent blocks here
  M2.1 basin-hypsometry@1.0.0 ──┬─> M2.2 basin-barrier-geometry@1.0.0 ──> M3.2, M3.4, M3.5
                                ├─> M2.3 mountainside-snow-line@1.0.0 ──> M2.4
                                └─> M2.4 rain-exposed-fraction@1.0.0 / ros-exposed-fraction@1.0.0
                                        (also needs M1.2 and SCA)

TIER 3  forcing v1 — the highest-leverage new science
  M3.1 basin-ivt@1.0.0 ──┬─> M3.2 upslope-ivt@1.0.0 ──┐
                         ├─> M3.3 ar-duration@1.0.0 ──┤
                         ├─> M3.4 orientation-favourability@1.0.0 ─┼─> M3.8 forcing-assessment@1.0.0
                         ├─> M3.5 blocking-index@1.0.0 ────────────┤
                         └─> M3.6 ar-scale@0.1.0 ──> M3.7 ar-sequence@0.1.0

TIER 4  official probability and basin QPE
  M4.1 hefs-ingest + hefs-exceedance@1.0.0     (independent; can run any time after Tier 0)
  M4.2 mefp-forcing-ensemble@1.0.0             (needs M4.1's location mapping)
  M4.3 basin-qpe@1.0.0 ──> qpe-intensity@1.0.0 ──> landslide-threshold-margin@0.1.0
  M4.4 antecedent-index@0.1.0                  (needs M4.3 or the AORC climatology)

TIER 5  reservoir and coastal state
  M5.1 reservoir-buffer@1.0.0 ──> hours-to-top-of-flood@0.1.0
  M5.2 skew-surge@1.0.0 ──> coastal sub-state at TIDAL points only (needs M1.5)

TIER 6  evaluation — the machinery that graduates everything above
  M6.1 hindcast-harness@1.0.0 ──> M6.2 conditional-antecedent-skill@1.0.0
                              └─> graduation gate for every EXPERIMENTAL method
```

**Why this order.** Tier 0 removes false precision from surfaces that are already on screen — the
highest-value-per-hour work in the whole plan and the only work that reduces the platform's exposure
rather than increasing it. Tier 1 is cheap, physically motivated, and supplies the band edges Tier 0
needs to stop being an uncalibrated convention. Tier 2 unblocks four domains at once. Tier 3 is where
the science lives. Tier 4 buys the authoritative probability and the one genuinely expensive ingest.
Tier 5 is state display. Tier 6 is how anything graduates.

---

## 3. Method specifications

Every method below states: **id and version · inputs (source, product, variable, cadence, latency) ·
computation · output contract shape · UNKNOWN conditions and reasons · confidence ceiling and why ·
graduation condition · exit test · 6–120 h payoff.**

Conventions inherited from the codebase and not restated per method: outputs are `DerivedFeature`
rows keyed by `(method_id, feature, scope_id, window, valid_time, issued_at)`; recomputation is a new
row, never an update; `available_at` is the knowledge-time filter; `source_kind` is resolved from
`cascade_core.registry`, never spelled beside the value; UNKNOWN carries a reason naming the missing
input.

---

### TIER 0 — Corrections to what already ships

#### M0.1 `method:streamflow-doy-climatology@2.0.0`

Supersedes `@1.0.0`. Four changes, each measured rather than argued.

**Inputs.** `src:usgs-wdfn-ogc` / `product:usgs-ogc-daily` — daily mean discharge (00060, statistic
00003), approved values only, full period of record, cadence 86 400 s, latency ~1 day. Plus, new:
`method:rating-epoch@1.0.0` output (M1.3) for the homogeneity boundary, and the seed's
regulation-epoch block (new CONFIGURED data, §4 table row R1).

**Computation.**
1. **Bound the record at the most recent homogeneity break.** A break is a gauge datum epoch change, a
   documented rating-revision epoch, a station relocation, or a change of upstream operating rule.
   *It is never the passage of time.* Justification: splitting the Green at 1962 and the Skagit at
   1959 moves the ranking by a mean of 9.9–11.1 percentile points and flips 29–32 % of days
   (climate-change §3) — larger than any climate term measured anywhere in the corpus. The
   Snoqualmie-at-Carnation stage series carries a **41.26 ft** datum step between WY1939 and WY1940
   and that gauge is in the platform's own seed.
2. **Extend the ladder into the tail.** `PERCENTILES = (5, 10, 25, 50, 75, 90, 95, 98, 99, 99.5)`,
   each emitted only where the ±2-day window sample supports it (a 90-year window holds ~450 values,
   so p99 is the 4th-largest — publishable *with its rank stated*), refused below
   `min_sample_for_tail`. Measured need: the surface read p95/VERY_HIGH at 24 900 / 41 500 / 62 600 /
   21 100 cfs on the Sauk over 9–12 December 2025 — a 2.5× flow range with **zero** discrimination.
3. **Publish the flow multiple beside every clamped percentile**: `value ÷ ladder_p95`, DERIVED, no
   distributional assumption. Observed flows reach **5.0×** the p95 value since 2016.
4. **Publish the sampling interval.** At ladder-build time, resample `L` random years 400× and emit
   the SD of the estimated percentile. Measured: **±12.1 (L=10), ±7.7 (20), ±6.2 (30), ±4.0 (50)**
   percentile points at the Sauk on 15 November.
5. **Version the ladder as a knowledge-timed artefact.** A ladder rebuilt annually with one more year
   of data is the same `method_version` with different inputs; a December-2025 replay that reads
   today's ladder is a real look-ahead bias of 4–8 percentile points. `as_known_at(T)` must select the
   ladder row whose `available_at ≤ T`. **This is a bug class, not a feature request.** Rebuild on a
   published WMO-aligned decadal boundary so the vintage is a citable object.

**Output contract.** New required fields on any percentile-bearing `DerivedFeature` and on the
`SurfaceState.value` it feeds: `climatology_period_start`, `climatology_period_end`,
`climatology_n_years`, `climatology_n_effective`, `percentile_sampling_sd`,
`homogeneity_epoch_reason`, `regulation_status`, and (when clamped) `flow_multiple_of_p95` with
`outside_climatology_range`. Rendered as *"p78 ± 6 (34-year ladder, 1992–2025, post-regulation
epoch)"*, never a bare p78.

**UNKNOWN conditions.** No approved daily record (`no_daily_record`); fewer than `min_sample` values
in the ±2-day window after epoch truncation (`homogeneous_record_too_short: N years since the WY1962
impoundment break`); the epoch block is unseeded for this gauge
(`homogeneity_epochs_not_configured`) — the last is a *refusal to build*, not a silent full-record
ladder.

**Confidence ceiling: MODERATE.** The ladder is an empirical rank against a named record — legitimate
— but band assignment on top of it inherits ±5.5–6.2 points of sampling error against edges 15 points
apart. It cannot be HIGH until M0.2's edge refusal exists and M1.1 supplies physically motivated
edges.

**Graduation.** Already DERIVED, not EXPERIMENTAL; it is an empirical rank, not a model. What is
EXPERIMENTAL is the *banding* built on it (M0.2).

**Exit test.** (a) A replay at `as_of = 2025-12-05` uses a ladder whose `available_at ≤ 2025-12-05`
and the test fails if it reads a later one. (b) The Sauk on 2025-12-11 renders a discriminating value
(p99+ or a flow multiple), not a flat p95. (c) A gauge with an unseeded epoch block renders UNKNOWN
with that reason, not a full-record ladder.

**6–120 h payoff.** Directly: on the Sauk (Skagit susceptibility gauge) and the Skykomish, the
surface currently cannot distinguish a 24 900 cfs day from a 62 600 cfs day during a live AR sequence.
After M0.1 it can, which is the difference between "elevated" and "the third-largest flow in 99 years"
inside the forecast window.

---

#### M0.2 `method:susceptibility-index@0.2.0`

Supersedes `@0.1.0`. The measured failure this fixes: replaying Event Zero with a 2025-excluded
climatology, the surface read **LOW in four of six basins on 3–4 December and MODERATE in all six on
5 December** — the day NWS Seattle issued its first Flood Watch, 6.5 days before the record Mount
Vernon crest. It first read VERY_HIGH on 8–10 December, when the rivers were already in flood
(antecedent §3.1(f)). Across the full record, **45–75 % of VERY_HIGH readings occur on days when flow
is already more than 25 % above its value three days earlier.** The surface as built is predominantly
a concurrent high-flow detector.

**Inputs.** M0.1 output; the same USGS daily series at lags −1, −2, −3 d; `product:awdb-snotel-daily`
(WTEQ, PREC) as today; M1.2 snow-drought state; M1.1 `g(Q)` when available.

**Computation — four changes.**
1. **A signed derivative driver.** `streamflow_doy_percentile_delta_48h` and `_delta_24h`, banded
   separately, plus an `in_event` boolean from `Q(t) / Q(t−3) > 1.25`. *The Event Zero signal was
   entirely here*: the Sauk moved **+64 percentile points in 48 hours** (24.8 → 88.7, Dec 4 → Dec 6).
   A VERY_HIGH concurrent with a rising hydrograph must be visually distinct from an antecedent one —
   they mean opposite things operationally.
2. **Band refusal near an edge.** `band()` becomes a function from `(percentile, sampling_sd)` to a
   level **or** to UNKNOWN with reason `within_sampling_error_of_band_edge` when
   `|percentile − edge| < k·sd`, `k = 1` as a stated starting parameter.
3. **Physically motivated edges where M1.1 exists.** Band by `g(Q)/g(Q_seasonal_median)` — the storage
   sensitivity gain — rather than by the USGS WaterWatch 25/75/90 drought convention. `g(Q)` is
   monotone in `Q` so the banding stays reproducible, but the edges then mean something
   (runoff-generation §6.2). Retain the percentile as the *display* statistic.
4. **Snow drought as a scored, two-dimensional driver.** Today `basin_swe_percent_of_median` carries
   `direction="context_not_scored"`, which is correct for a bare SWE number and wrong for the *state*:
   **warm snow drought raises susceptibility, dry snow drought lowers it, and low SWE alone says
   nothing** (snow §6.4). This requires a two-dimensional driver, not a scalar with a sign. Until
   `Driver` can carry that, emit M1.2's state as an unscored labelled driver and say so.

**Output contract.** `Driver` gains the ability to carry a signed delta and an angular/2-D quantity
(the same contract change M3.4 needs). `SurfaceState.reason` gains
`within_sampling_error_of_band_edge`. `METHOD_PARAMETERS` publishes the measured per-band conditional
probabilities from antecedent §3.1(c) — P(top-1 % future flow | VERY_HIGH) = **2.1–5.1 %** against a
**1.0 %** base rate, P(top-1 % | LOW) = **0.0–0.8 %** — so the band ships its own skill number and
cannot be misread as a probability.

**UNKNOWN conditions.** Inherited from M0.1, plus: `MAX_DAILY_MEAN_AGE` tightened below 48 h in the
cool season (the Sauk moved 64 percentile points in 48 h — a 48 h tolerance is too loose for the
regime); `no_delta_available` when fewer than two ladder-comparable days exist.

**Confidence ceiling: MODERATE**, and LOW at regulated gauges. Regulation does not make the percentile
noisier — the regulated gauges have the *highest* statistical persistence (Cedar ρ = 0.705, lowest
mid-event share 45 %) — it makes the signal an operating decision rather than a basin state, and the
seed's existing ceilings encode the right answer for a reason the docstring states wrongly.

**Graduation to DERIVED.** Requires M6.2: score four antecedent formulations (DOY percentile, its 48 h
delta, NWM/AORC soil percentile, 90-day SSPI) against cool-season peaks **conditioned on basin
QPE/QPF**, so the test is "does antecedent state add skill *given* the forcing" and not "does high
flow follow high flow". **A null result for western Washington is a genuine finding and belongs in
`HYDROLOGY.md`, not in a drawer.**

**Exit test.** Replaying 2025-12-04 → 2025-12-06 produces a *rising* susceptibility driver with a
banded magnitude, and the rendered state on 2025-12-05 is distinguishable from the rendered state on a
climatologically-similar quiet day at the same percentile.

**6–120 h payoff.** On 5 December 2025, at the moment of the official Flood Watch and 6.5 days before
the crest, this method turns a MODERATE-everywhere reading into "Sauk and Snoqualmie rising fastest in
the record for this date". That is the entire operational value of a susceptibility surface.

---

#### M0.3 `method:rate-of-rise@2.0.0`

**The defect.** `trend.rate_of_rise` computes `(pts[-1] − pts[0]) / span_h` — exactly the two
endpoints — while `HYDROLOGY.md` §9 says "trend never comes from the two endpoints of a response
window" (flood-statistics §7 item 10). Separately, at **SNAW1 (Snohomish at Snohomish)** the stage
oscillates ~11 ft on a 12-hour tidal cycle at low flow with a measured transmission of **0.831 ft/ft,
r = 0.94**; a 1/3/6-hour rate there is dominated by the tide, not the flood. **`trend.py` and
`headroom.py` produce nonsense at SNAW1 today** (compound-coastal §7.2) — a live bug, not a future
concern.

**Inputs.** Stored observations at the point; M1.5 `tidal_class` and transmission coefficient;
NOAA CO-OPS predicted water level at the mapped reference station for de-tiding.

**Computation.** Replace the endpoint difference with a Theil–Sen slope over the window (robust to the
single-point spikes a fouled control produces). At `tidal_class ∈ {TIDAL, TIDALLY_MODULATED}`, either
de-tide the series against the reference station's *predicted* high/low before fitting, or refuse the
trend with reason `tidal_signal_dominates_window`. Emit `limb ∈ {rising, falling, steady, unknown}`
as a first-class field consumed by M0.2 and by the routing anomaly detector. Use M1.1's recession time
constant `τ(Q)` — 17.5–28.1 h in the unregulated basins, 42 h at Mount Vernon, 116 h on the Cedar,
264 h on the Green — as the *denominator scale* for the window rather than a hand-chosen 6 h.
Response time is not a basin-size property; it is dominated by regulation, and any time-to-threshold
logic that treats regulated and unregulated reaches on the same time scale is wrong by an order of
magnitude.

**Output contract.** `Trend` gains `method` (`theil_sen`), `detided` (bool), `reference_tide_station`,
and `window_basis` (`fixed_h` | `tau_scaled`).

**UNKNOWN conditions.** As today, plus `tidal_signal_dominates_window` and
`no_tide_prediction_for_reference_station`.

**Confidence ceiling: HIGH** at `FLUVIAL` points (this is arithmetic on observations), **UNKNOWN** at
`TIDAL` points until de-tiding is verified.

**Exit test.** A synthetic series carrying an 11 ft M2 oscillation on a flat mean returns
`direction=steady` or UNKNOWN with the tidal reason — never `rising`. A regression fixture from SNAW1,
15–30 September 2025, asserts the same against real data.

**6–120 h payoff.** Snohomish at Snohomish is one of Event Zero's record gauges (34.45 ft). Every
headroom and time-to-threshold number the platform prints there today is contaminated by an 11 ft
diurnal signal. This is the difference between a usable and a fabricated number at a delta forecast
point during a 6–24 h decision.

---

#### M0.4 `method:model-agreement@0.3.0`

**The defect.** NWS SCN 26-64 made **NWM v3.1 operational on 2026-08-18, 12Z**, with: *"Assimilation
of USGS streamflow observations available at the forecast execution time into the corresponding
beginning hours of the NWM short-, medium-, and long-range forecasts. The initial forecast period
overlapping with available observations will thus track observed values."* `agreement.py` opens its
comparison window at `as_of − 6 h` (`LOOKBACK_H = 6.0`). Inside the assimilation tail, "agreement" is
not agreement between two forecasts — it is agreement between a forecast and a gauge, and it reads
artificially high.

**Computation.** (1) **Measure the tail before assuming it.** Compare `channel_rt` f001…f012 against
USGS IV at the six seed reaches over one week; the tail is anchored on the NWM *cycle* time, not on
`as_of`, so a cycle several hours old may already have its tail behind the window's opening edge —
the exposure is real but "guaranteed contamination" is not established. (2) Start the comparison
window after the measured tail and record the measurement as a versioned method parameter with the
same stated-assumption discipline `AgreementBands` already uses. (3) **`MODEL_LABEL` becomes a stored
per-row value, not a module constant** — any data ingested before 2026-08-18 is v3.0 under a v3.1
label, and a hindcast crossing that boundary silently mixes two models. (4) Add a **distinct-value
count** to every reported member fraction: `3 of 6` and `22 of 45` are not the same evidence, and the
existing `QUALITY_DEGENERATE_ENSEMBLE` flag generalises. Live measurement: HEFS at MVEW1 has **zero
spread at lead 0** (all 45 members exactly 6725.89 cfs) — the same failure at a different point in the
hydrograph. *A low measured spread in a dry month is not evidence of confidence and must never render
as one.*

**Output contract.** `AgreementState` gains `model_version`, `assimilation_tail_h`, and
`distinct_member_values`. Until the tail is measured, the honest output at short lead is a **caveat on
the agreement level, not a higher level**.

**Confidence ceiling: MODERATE** while the bands remain the uncalibrated 0.25/0.60 and 6 h/18 h first
cut.

**Exit test.** A fixture cycle whose leading hours equal the stored USGS IV series produces a caveat
clause naming the assimilation tail, and the comparison window's opening edge is strictly after it.

**6–120 h payoff.** Agreement is the platform's only meta-signal at the two regulated points where the
upper flood categories will never acquire a verifiable sample (AUBW1 major: 0 events in 62 years post-
dam). If it reads high because the model is quoting the gauge back, the meta-signal is worthless in the
0–18 h window where it matters most.

---

#### M0.5 `method:rank-in-record@1.0.0`

The honest object that replaces the recurrence interval the platform must never compute.

**Inputs.** `api.water.noaa.gov/nwps/v1/gauges/{lid}` → `flood.crests.historic` (MVEW1 returns **93**
historic crests, each with a preliminary/observed/revised flag); USGS annual peak file
(`nwis.waterdata.usgs.gov/nwis/peak?site_no=…&format=rdb`) with `peak_cd` and `gage_ht_cd` verbatim.
Cadence: monthly. Latency: **annual peaks lag the event by up to two years** — as of 2026-08-24 the
Mount Vernon peak file ends at WY2025 and the December 2025 record crest **is not in it**.

**Computation.** *"This crest is the Nth highest **stage** in M years of record at this gauge (WY a–b),
and the Kth highest **discharge**."* Separate statements for stage and flow, because at Mount Vernon
they differ: record stage 37.73 ft on ~133 000 cfs versus 152 000 cfs in 1990 at a lower stage. Plus
the nearest observed analogue by peak discharge, with its crest stage. Ingest `peak_cd` verbatim —
6 (regulation), 2 (estimate), 7 (historic), 5 (affected to unknown degree), 9 (snowmelt/ice-jam),
C (urbanised), R (revised), Bd/Bm (date uncertain to day/month) — these map directly onto the existing
`quality` vocabulary and are pure provenance gold.

**Output contract.** A `historic_crest` block carrying `rank`, `record_begin_year`, `record_end_year`,
`basis` (stage|flow), `datum`, `rating_epoch`, `preliminary`, `source_id`, `peak_codes`. **No field
anywhere may carry a recurrence interval, return period or AEP.** Cross-source disagreement is
reported, not reconciled: NWPS gives the 2021-11-16 Mount Vernon crest as 37.32 ft / 122 596 cfs while
the USGS peak file gives 36.99 ft / 127 000 cfs for the same event.

**UNKNOWN conditions.** `rank_crosses_rating_epoch` — a historical stage rank that spans a rating epoch
boundary is refused (the Sauk carries a −0.8 ft step at WY2018; Ferndale a ~7 ft step 1964–1968;
Carnation a ~43 ft step at 1940).

**Confidence ceiling: HIGH.** A rank is an observation against a named record with no distributional
assumption — one of the few things in this document that can be.

**Doctrine change this forces.** `HYDROLOGY.md` §13 must gain: *the platform will not claim a
recurrence interval, return period or annual exceedance probability for any reach.* The prior research
pass asserted "the platform already declines to compute return periods"; a grep of `HYDROLOGY.md` and
`DATA_DOCTRINE.md` for "return period", "recurrence", "AEP", "100-year" and "Bulletin" returns
**zero matches**. It does not decline in writing. Copy rules must prohibit the strings "100-year",
"N-year flood", "return period" and "recurrence interval" outside a quoted, attributed official
product.

**Exit test.** A crest whose stage rank and flow rank differ renders both, with a sentence that does
not imply they are the same statement. `-9999` and `-0.999` NWPS sentinels parse to `quality=sentinel`
and never render as a stage — **a `-0.999 ft` crest on screen is a visible falsehood.**

**6–120 h payoff.** During a live event this is the sentence an operator can act on — "third-highest
in 99 years" — computed from data already ingested, replacing an unbuildable and forbidden one.

---

### TIER 1 — Cheap derived features

#### M1.1 `method:catchment-sensitivity@1.0.0`

Kirchner (2009) storage sensitivity, computed from data already ingested. This is the physically
motivated replacement for the WaterWatch band-edge convention.

**Inputs.** `src:usgs-wdfn-ogc` / instantaneous or hourly discharge (00060), 5+ water years, plus
drainage area from the USGS site service. **No new provider.** Cadence: refit annually. Latency: n/a
(reference data).

**Computation.** Convert to basin depth (mm h⁻¹). Select recession points as hours in Nov–Mar where
`dQ/dt < 0` continuously for the preceding 6 h. Fit `ln(−dQ/dt) = c₁ + c₂ ln Q + c₃ (ln Q)²`
(Kirchner Eq. 9). Publish:
- `catchment_sensitivity_g` — `g(Q) = dQ/dS`;
- `storage_sensitivity_gain` — `g(Q)/g(Q_seasonal_median)`;
- `dynamic_storage_mm` — `∫ dQ/g(Q)` between chosen flows (Eq. 20);
- `recession_time_constant_h` — `τ = 1/g(Q)` (Eq. 21).

**Measured reference values** (runoff-generation §5.4, unregulated gauges): `b` = 1.85–2.05,
gain `g(1.0)/g(0.1)` = **7.6–11.1×**, wet-season dynamic store **71–104 mm** — one to two days of AR
precipitation — and `τ(1 mm h⁻¹)` = 17.5–28.1 h.

**Refuse on regulated reaches, by type.** Green below Howard Hanson fits `b−1 ≈ −0.06`: `g(Q)` is
*flat*, i.e. the recession plot measures the operator, not the hillslope, and its implied 790 mm of
"storage" is reservoir operation. Return UNKNOWN with a reason naming the regulation, exactly as
`susceptibility` already caps confidence by regulation class. Usefully, `b−1` orders the basins
exactly as `regulation_class` does (unregulated 0.85–1.05 > Skagit 0.67–0.77 > Cedar 0.17–0.26 >
Green −0.06), so the platform can **measure regulation class from the hydrograph as a consistency
check on its seed data**.

**Publish the fit quality — and publish the right one.** The corpus's own adversarial re-check found
the headline r² = 0.985–0.996 was computed on ~20 *binned means*; refitting the same points unbinned
gives **r² = 0.74–0.80**. The unbinned statistic is what ships, or the method overstates certainty by
hiding ~25 % unexplained variance. Also record `b`'s sensitivity to the recession filter (Sauk: 2.04
at 2 h, 1.92 at 6 h, 1.85 at 12 h, 1.71 at 24 h) as a stored parameter, since it is not insensitive.

**Kirchner's own stated failure mode binds here and must be recorded.** §15.6: the methods "must break
down for catchments that are too large… one can speculate that in significantly larger catchments (say,
1000 km²)… the methods presented here would not work." Six of the seven Cascadia gauges are at or
beyond that scale (NF Stillaguamish 679 km²; Skagit at Mount Vernon 8 011 km²). Channel-network routing
lag is an unexcluded alternative explanation for a flattened `g(Q)` at Mount Vernon. Carry it as a
`method_caveat`, not a footnote.

**Output contract.** Four new `DerivedFeature` ids as above plus `storage_limb`
(rising/falling/unknown, from M0.3) and a `fit` block: `r2_unbinned`, `n_points`, `filter_h`,
`flow_range_mm_h`, `extrapolation_beyond_fit` (bool).

**Confidence ceiling: MODERATE.** The method is peer-reviewed with a stated failure mode and a
per-basin fit statistic — **the first derived quantity in the platform that can carry a numeric quality
measure without violating `DATA_DOCTRINE.md` §9.** The ceiling is MODERATE and not HIGH because
Kirchner's recession plots reached ~1–1.5 mm h⁻¹ and the December 2025 Skagit event exceeded the
fitted range; extrapolation to flood flows is untested.

**Graduation.** `g(Q)` and `τ` are DERIVED *provided the unbinned fit statistic ships with the value*.
The **banding built on top of them stays EXPERIMENTAL** until M6.1 hindcasts `g(Q)`-predicted peaks
against Event Zero.

**Exit test.** An independent implementation reproduces `b` for the four unregulated gauges on the same
window **within the filter-length sensitivity band**, and returns UNKNOWN-with-reason at Green near
Auburn. (Note: the corpus's own re-implementation returned b = 1.69–1.92 against a stated 1.85–2.05, so
the exit test is a band, not a point.)

**6–120 h payoff.** Two things inside the window. (a) `τ(Q)` is the published time scale that makes
time-to-threshold honest — 17.5 h on the Sauk versus 264 h on the Green is an order-of-magnitude
difference the platform currently ignores. (b) The gain `g(Q)/g(Q_median)` says how much discharge the
*next* millimetre of the forecast AR will produce, which is exactly the quantity a 24–72 h QPF needs to
be converted into an expectation about the river.

---

#### M1.2 `method:snow-drought-state@1.0.0`

Buildable **today** from elements already ingested. The single highest-value new derived feature in the
snow domain.

**Inputs.** `src:nrcs-awdb` / `product:awdb-snotel-daily` — WTEQ and PREC with per-value median,
daily, latency ~1 day. **Already in the ingest.** Plus `method:snotel-elevation-coverage@1.0.0`
(below) for the honesty flag.

**Computation.** Hatchett et al. (2022) daily percentile definition: state ∈ {none, dry, warm,
warm_and_dry} from (SWE percentile ≤ 30) × (accumulated-precipitation percentile vs median), with the
US Drought Monitor D-scale sub-bands. Computed **per elevation band once M2.1 exists**, and until then
computed twice — once over all mapped stations and once over stations below 4 500 ft — with both
reported.

**Why the elevation split is not optional.** On 2025-12-11, the day before the record Skagit crest, the
twenty western-Washington Cascade SNOTEL sites below 4 500 ft held **14 % of median SWE** with ten
reading exactly 0.0 in, while the all-station composite read **44 %** because three crest/leeward
North Cascades sites were at 128–174 %. The statistic the platform prints today would have understated
the anomaly by a factor of three on the eve of the record crest. That is not merely uninformative — it
is *misleading in the direction of calm*, which `DATA_DOCTRINE.md` §12 forbids.

**Companion: `method:snotel-elevation-coverage@1.0.0`.** Per basin: n sites, elevation span, fraction
of basin hypsometry within ±X ft of an observing site, and an explicit **"the ROS-generating band is
unobserved"** flag. Measured: 31 active western-WA SNOTEL sites, median **3 900 ft**, only 3 below
3 000 ft and **1 below 2 000 ft**, against a transient snow zone of roughly 1 000–4 000 ft. Three
basins are effectively single-station (Skykomish = Stevens Pass only; Sauk = Decline Creek, record
begins 2018-11; Stillaguamish = Deer Pass, begins 2020-12 — too short for a climatology). **AWDB
returns no median at all for Decline Creek or Deer Pass, so any percent-of-median product is
uncomputable for the Sauk and the Stillaguamish today.** The network gap is a first-class provenance
fact, not a footnote.

**Output contract.** `snow_drought_state` (closed vocabulary) + `snow_drought_subband` +
`swe_percentile_below_4500ft` + `accumulated_precip_percentile` + `observing_coverage_flag`.
`Driver.direction` needs a value distinct from `context_not_scored`: warm snow drought *raises*
susceptibility, dry snow drought *lowers* it, and low SWE alone says nothing — a two-dimensional
driver, not a scalar (D15/M0.2 item 4).

**UNKNOWN conditions.** `no_median_published_for_station` (Sauk, Stillaguamish today);
`fewer_than_min_stations_in_band`; `record_too_short_for_climatology` (Deer Pass, 2020–).

**Confidence ceiling: LOW** until calibrated, and **capped at LOW permanently for the Sauk and
Stillaguamish** while AWDB publishes no median there.

**Graduation.** EXPERIMENTAL until M6.1 shows the state adds skill conditional on forcing. Hatchett's
definition is published and percentile-based, so the *computation* is DERIVED; the *susceptibility
contribution* is the experimental part.

**Exit test.** Replaying 2025-12-11 returns `warm_and_dry` for the sub-4 500 ft band with 14 % of
median, and the all-station composite (44 %) is present but not the headline. Replaying 2026-04-01
returns warm snow drought at a composite 55 % of median with accumulated precipitation 105–138 % of
median at every station — Harpold's textbook case, reproduced station by station.

**6–120 h payoff.** Warm snow drought is the state in which an AR's rain falls on bare ground up to
4 000 ft instead of onto a buffering pack, which is exactly what happened in December 2025. Knowing it
*before* the AR lands changes how a 72 h QPF should be read for the Skagit, Skykomish and Nooksack.

---

#### M1.3 `method:rating-epoch@1.0.0` + `method:conveyance-drift@1.0.0`

Two methods, one fetch. Four domains demanded this independently (D8, D9).

**Inputs.**
- USGS OGC `field-measurements`:
  `https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items?monitoring_location_id=USGS-{site}&parameter_code=00065`
  — measured discharge, mean gage height, measurement rating (Good/Fair/Poor), `control_condition`,
  `approval_status`, per field visit. 430 paired measurements 1959–2026 at 12200500. Monthly.
- USGS expanded rating tables: `https://nwis.waterdata.usgs.gov/nwisweb/get_ratings?site_no={site}&file_type=exsa`
  — rating ID, type, breakpoints, offsets, current and previous shift with begin/end times, **the
  analyst's remark**, and the full stage→discharge table. Monthly.
- USGS OGC `peaks` — annual peaks with qualification codes.

**Computation — `rating-epoch@1.0.0`.** Detect epoch boundaries: (a) any published rating id change;
(b) a documented datum change; (c) a residual step > 1.5 ft in the annual-peak `gage_ht ~ a + b·log₁₀(Q)`
fit. Known boundaries the detector must find: **Sauk −0.8 ft at WY2018** (persisting through WY2024 —
a step, not a trend, and unresolved as channel change vs rating revision); **Ferndale ~7 ft between
1964 and 1968**; **Carnation ~43 ft at 1940**; **Cedar at Renton at ~1951 and ~1976**. An unsegmented
Cedar record yields a spurious +0.9 ft/decade.

**Computation — `conveyance-drift@1.0.0`.** Restrict to the upper half of the peak-discharge
distribution (so the result speaks to flood-stage hydraulics), fit `gage_ht = a + b·log₁₀(peak_va)`,
take the **Theil–Sen** slope of the residual against water year with a Mann–Kendall test, and report
`ft_per_decade`, `p`, `residual_sd`, `n`, `window`. **Report the Theil–Sen slope, not OLS** — the
corpus's own re-run found the tabulated Ferndale figure was an OLS fit and the robust estimate is less
than half of it.

**Seeded anchors** (with the corrected values): Nooksack at Ferndale **+0.065 ft/decade, p = 0.028**;
Sauk near Sauk **0.000 ft/decade over 1932–2017, residual sd 0.21 ft**; Skykomish near Gold Bar
**+0.003, p = 0.74, sd 0.18 ft over 92 years** (the cleanest gauge in the region — the control the
argument needed); Green near Auburn **−0.093 ft/decade 1948–2005** (Howard Hanson trapping bed
material) reversing since 1990. **Skagit near Mount Vernon did not drift — it destabilised**: residual
sd **0.25 ft across 1948–2005** → **1.38 ft across 2006–2024** (≈30× in variance), with WY2007–08 at
−2.1 ft and WY2022 at +1.9 ft. That is an effective ±1.4 ft of stage uncertainty at the platform's
most important forecast point **that no datum check will catch**, against NWS category spacing of
2 ft.

**Separately measured and complementary** (routing §5.2): rating-independent measured pairs above
90 000 cfs give **−8 % to −11 % of conveyance at flood stage** since the late 1980s–2000s
(≈0.1–0.3 % yr⁻¹), corroborated by USGS's own rating-24.0 remark (*"Older high QMs were not used for
the rating based on presumed control changes"*), by 20 of 25 cross-sections aggrading +1.5 ft average
bed 1975→1999, and by a **66 %** increase in the suspended-sediment rating slope at that gauge. This
**corrects the repository's standing "~29 %" figure**, which was a two-point comparison against a 1906
indirect estimate (peak date `1906-11-00`, day unknown) and a 1990 crest **depressed by the Fir Island
levee failure**.

**Output contract.** `rating_id`, `rating_shift`, `rating_valid_from`, `rating_epoch` on every rated
observation; `measurement_quality` (Good/Fair/Poor → 5 %/8 %/>8 % uncertainty) and `control_condition`
on every ingested field measurement; `conveyance_drift_ft_per_decade` + `p` + `residual_sd` +
`estimator` as a per-gauge `DerivedFeature`. `compatibility_problem()` gains a fourth check: refuse a
*historical* stage comparison across epochs. (Leave the current-value-vs-threshold path alone; it is
already correct.)

**Confidence ceiling: LOW** on the drift slope (n = 2–4 modern high-flow measurements at Mount Vernon,
measurement quality *Fair* = 8 % which is the same size as the effect), **HIGH** on the epoch detector
(a published rating id change is a fact).

**Exit test.** The detector finds all four known steps above. `conveyance_drift` at Skykomish returns
a slope statistically indistinguishable from zero and at Ferndale a positive slope in the 0.05–0.11
ft/decade band. A stage percentile spanning the Carnation 1940 datum step is refused.

**6–120 h payoff.** Indirect but decisive: it is the reason a stage threshold at Mount Vernon has a
**discharge vintage**, and it bounds the honest uncertainty on stage headroom there at ±1.4 ft during
a live event. It also supplies the homogeneity boundaries M0.1's ladder cannot be built without.

---

#### M1.4 `method:gauge-control-quality@1.0.0`

Same fetch as M1.3, separate meaning.

**Computation.** From `control_condition` and `measurement_rated` across all field visits: the fraction
debris- or vegetation-affected, and the distribution of measurement ratings. Restricting to visits where
a condition was actually recorded (34 % of Ferndale and 12 % of Mount Vernon visits carry a null, plus
16 % "Unspecifed" at Mount Vernon): **Skagit near Mount Vernon 41 %, Ferndale 20 %, Sauk 7.5 %,
Skykomish near Gold Bar 3.9 %.** A factor of ten across the platform's own gauges.

Read it as a **data-quality attribute, which is all the platform needs it for** — not as a sediment-
supply proxy. It does not order with supply (the Nooksack has the highest per-area sediment yield of
the 14 major Puget Sound rivers yet Ferndale ranks well below Mount Vernon); gradient, proximity to the
depositional reach, wood supply and per-office field practice are all live alternatives.

**Output contract.** Rendered as a **labelled category, never a decimal** (`DATA_DOCTRINE.md` §9):
*"hydraulic control debris-affected in 41 % of USGS field visits where a condition was recorded."*

**Confidence ceiling: MODERATE.** Denominators are not comparable across gauges.

**Exit test.** Mount Vernon renders a debris-affected category and Skykomish does not, from the same
code path.

**6–120 h payoff.** It is the honest caveat on the stage reading at the platform's most important
forecast point during the hours when a jam is most likely to be present — the Skagit's disputed
historic peaks are disputed partly because of "levee failures and log jams", and 20 ft of debris across
90 % of the channel was observed at the RR bridge 2 river miles above the gauge in November 1995.

---

#### M1.5 `method:tidal-transmission@1.0.0`

Measurement, not judgement. Resolves D11 and fixes the live M0.3 bug.

**Inputs.** USGS OGC `continuous` stage (00065), hourly, low-flow window; NOAA CO-OPS
`hourly_height` at the nearest reference station
(`https://api.tidesandcurrents.noaa.gov/api/prod/datagetter`), free, no auth, 1-year max per request.

**Computation.** 25-hour high-pass (centred moving-mean removal) applied to both series over a low-flow
window; sweep lag −6…+18 h; slope = OLS of tidal-band stage on tidal-band sea level at the best
lag. Re-derive annually.

**Measured** (compound-coastal §3.4): **Snohomish at Snohomish (SNAW1) 0.831 ft/ft, r = 0.936**,
tidal-band sd **3.03 ft**, raw stage swinging **4.89 → 17.16 ft** against an NWS flood stage of 25 ft.
Nooksack at Ferndale **0.019 ft/ft, r = 0.33**. Skagit at Mount Vernon **0.010 ft/ft, r = 0.23** —
0.024 ft/ft during the December 2025 flood itself.

**Output contract.** `ForecastPoint` gains `tidal_class ∈ {TIDAL (≥0.5), TIDALLY_MODULATED (0.05–0.5),
MARGINAL (0.01–0.05), FLUVIAL (<0.01), UNKNOWN}` and `tidal_transmission_ft_per_ft` (a nullable
`DerivedFeature` reference with its measurement window recorded). From the measurement: SNAW1 =
`TIDAL`, NKSW1 = `MARGINAL`, MVEW1 = `MARGINAL`.

**Doctrine this corrects.** `HYDROLOGY.md` §2 flags Ferndale as tidally influenced (true but
quantitatively negligible) and **says nothing about Snohomish, which is the one that actually is** —
even though §12 cites SNAW1 as one of Event Zero's record gauges. Its record stage is a compound
quantity. Conversely, the prior pass's claim that a river-only stage forecast is "structurally
incomplete" at Mount Vernon and Ferndale is **half right**: it over-generalised the Skagit Climate
Science Consortium's "below Mt. Vernon to Puget Sound" — *below* the gauge, not at it.

**Confidence ceiling: HIGH.** It is a regression on two observed series with a stated window.

**Exit test.** SNAW1 classifies `TIDAL` and M0.3 refuses or de-tides there; MVEW1 classifies `MARGINAL`
and no tide term enters its forecast, headroom or hazard path.

**6–120 h payoff.** Immediate: it makes trend, headroom and time-to-threshold *correct* at a delta
forecast point where they are currently nonsense, and it prevents the opposite error of wiring an
irrelevant tide term into the Skagit.

---

### TIER 2 — Geometry foundation

#### M2.1 `method:basin-hypsometry@1.0.0`

**The single largest structural blocker in the corpus.** `NEXT_STEPS.md` gap 6 records that basin
geometry is HUC8 unions with no hypsometry; until it exists, every rain-exposed, ROS-exposed,
SWE-below-snow-line, cross-barrier-bearing and elevation-band statement is blocked.

**Inputs.** USGS 3DEP (public domain, 10 m or 1/3 arc-second) over the eight basin polygons, one time.
Fallback: Copernicus GLO-30 (free, attribution required). Existing basin polygons at two display LODs
are already seeded.

**Computation.** Per basin (and per sub-basin where the seed defines one): the elevation–area curve
sampled at a stated interval (100 m bands to 3 000 m is sufficient for every downstream use), stored as
a few hundred floats. Also: basin barrier height `h` (for M3.5), mean and median elevation, and the
fraction of area in the 1 000–4 000 ft band **recorded as a display annotation with a vintage, not as a
parameter** — Jennings & Jones's criticism stands ("the transient snow zone implies a static area, when
in fact the area undergoing melt is highly dynamic during storm events") and so does the second,
independent reason that the band is unobserved by the SNOTEL network (M1.2).

**Output contract.** A `BasinHypsometry` CONFIGURED-from-DEM artefact with `dem_source`,
`dem_resolution_m`, `dem_vintage`, `band_interval_m`, `area_km2_by_band`, `computed_at`. It is
reference data: re-derive only on a DEM or polygon change.

**Cost.** One-time download (tens of GB if 10 m 3DEP over eight basins; use the USGS 3DEP dynamic
service or GLO-30 to avoid it), **~0 bytes/day steady state**, a few hundred KB stored.

**Confidence ceiling: HIGH** for the curve itself; the *downstream* uses inherit their own ceilings.

**Exit test.** The Sauk returns ~60 % of area above 1 km with two-thirds between ~0.7 and 1.8 km, and
the Green two-thirds between 0.7 and 1.3 km with three-quarters below 1.2 km — the independently
published figures in Neiman et al. (2011) Table 1. **This is a real external check, not a self-test.**

**6–120 h payoff.** None on its own. It unblocks M2.3/M2.4 (rain-exposed fraction — the highest-leverage
snow quantity in a maritime flood) and M3.2/M3.5 (upslope IVT and blocking), all of which pay off
directly inside the window.

---

#### M2.2 `method:basin-barrier-geometry@1.0.0`

**Inputs.** M2.1; the basin polygon; the DEM.

**Computation.** Per basin: (a) a **cross-barrier unit bearing** — the mean terrain-gradient direction
weighted by area over the windward slopes, plus a fitted alternative from history (below); (b) an
effective **barrier height `h`** for the Froude/blocking calculation; (c) the terrain-gradient field
for the IVT projection.

**Seed the bearings from the literature and fit the rest.** Neiman et al. (2011) give defensible
starting windows for two of the platform's basins from ten flood cases each — **Green 245°–275°**
(the most restrictive window studied) and **Sauk south-westerly only** (rain-shadowed by the Olympics
*and* Vancouver Island for every onshore direction except SW). A one-sided *t* test separates the
Green–Queets low-level wind directions from the Sauk–Satsop ones at **>95 % confidence**.
**Nooksack, Skykomish, Snoqualmie, Stillaguamish, White and Cedar have no published window** —
derive them by fitting the bearing that maximises correlation with basin response over history, which
is exactly what Tierney & Durran did per sounding site (they fitted **224°** at Quillayute and **251°**
at Taholah for the *same* massif, and attributed the difference to terrain-induced flow deflection).

**Read the orientation result correctly.** Orientation under-determines which basin floods: within each
same-orientation pair, Neiman et al.'s top-10 lists share only three dates, and cross-pair overlap is
*not* smaller. The paper draws the opposite of a separation conclusion — it is evidence that the other
four terms (strength, stationarity, melting level, antecedent soil moisture) also matter. Do not cite
the pair statistic as evidence the pairs are hydrologically distinct.

**Output contract.** `Basin` gains `cross_barrier_bearing_deg` (with `source`: `neiman_2011` |
`fitted_from_history` | `dem_derived`), `bearing_window_deg` (a *periodic interval*, not a scalar),
`barrier_height_m`, and a `provenance` block. **CONFIGURED with provenance**, never OBSERVED.

**Contract change this forces.** `Driver` and `BandTable` currently assume a **scalar with monotone
bands**. Orientation favourability is **periodic and peaks in an interval**. The contract needs an
angular quantity type and an interval band table (also needed by M3.4).

**Confidence ceiling: MODERATE** for the two literature-seeded basins, **LOW** for the six fitted ones
until M6.1 evaluates them.

**Exit test.** The Green's fitted window brackets 245°–275°; the Sauk's brackets the SW quadrant.
Fitting on a held-out half of the record reproduces the window on the other half.

**6–120 h payoff.** It is the input that lets a 24–72 h wind-direction forecast say *which* basin the
AR will load. The Green's peak flows vary by **an order of magnitude between years** because of the
narrowness of its window, and its flood composites have the **weakest** vapour fluxes and **coldest**
θₑ of the four basins studied — i.e. flooding on the Green is more sensitive to flow orientation than
to the magnitude of the incoming vapour flux.

---

#### M2.3 `method:mountainside-snow-line@1.0.0`

Replaces the constant 1 000 ft offset. Three elevations must never again be conflated: **freezing
level** `Z_0C` (free-air 0 °C isotherm) · **atmospheric snow level** (NBM `SNOWLVL` — the altitude
where *wet-bulb* temperature first crosses above 0.5 °C) · **mountainside snow line** `Z_S` (where the
rain/snow boundary intersects the terrain on a windward slope). **Only the third may be intersected
with hypsometry, and it is the lowest of the three.**

**Inputs.** `src:nbm-v5` / `product:nbm-v5-core` — `SNOWLVL` percentiles, already ingested, 6-hourly,
observed at cycle + 42–44 m. Plus the basin QPF rate from `product:nbm-v5-qmd` for the intensity
dependence, and M2.1.

**Computation.** `Z_S = SNOWLVL − Δ_melt(P) − d_mesoscale`, with `Δ_melt` parameterised from Minder,
Durran & Roe (2011): **60 m** in weak precipitation → **~150 m** at 3.5 mm h⁻¹ → **>300 m** in intense
precipitation; and `d_mesoscale ≈ 221 m` in Minder's control simulation (`d_0C` 142 m, `d_S` 221 m,
total `d` 267 m).

**Why a constant is wrong in form even though it is right in central value.** The total offset from
upwind free-air freezing level to mountainside snow line is roughly **250–450 m (800–1 500 ft)** in
ordinary storms — which brackets the repository's 1 000 ft assumption well — but the storm-to-storm
range is a **full kilometre**, and the offset **grows with precipitation intensity**, i.e. it is
largest exactly during the heaviest AR hours. A fixed offset is biased high on snow level precisely
when the answer matters most. Separately, the repository currently applies **no** mesoscale/terrain
depression to `SNOWLVL` at all, and `SNOWLVL` is a *column wet-bulb level*, not a terrain intersection.

**Cite it properly.** `DATA_SOURCES.md` W8 currently rests on KIRO 7 / MyNorthwest / OpenSnow secondary
citations and records that "an authoritative weather.gov/sew citation is an OPEN QUESTION". Two better
sources exist and are **two separate quantities, not one corroborated number**: (a) Neiman et al.
(2011) subtract **300 m** from NARR 0 °C heights on a **200–400 m** observational basis (Stewart et al.
1984; White et al. 2002) — peer-reviewed, and a *free-air melting-level* offset; (b) an NWS WFO Seattle
Western Region Technical Attachment documents a 3 500 ft freezing level with a ~2 500 ft ambient snow
level — **not peer-reviewed, and from a single mid-May post-frontal convergence-zone case with CAPE
300–500 J kg⁻¹**, a different regime from the cool-season warm-sector ARs the platform cares about.
Minder, Durran & Roe say the *mountainside* depression is a **further** "hundreds of metres" beyond
(a). Replace the media citations; do not merge the two numbers.

**Also record the contrarian result.** Minder et al. find `d` **increases with temperature**, a
negative feedback that "could act to buffer mountain hydroclimates against the impacts of climate
warming" — an important check against naive "snow level rises 150 m per °C" reasoning, and it depends
on the microphysics scheme, so it is stated conditionally.

**Output contract.** `basin_mountainside_snow_line_m` with `offset_components` (`{delta_melt_m,
mesoscale_m, source_product_level}`) and `offset_is_intensity_dependent: true`. The existing snow-level
driver's `label` must name **which of the three elevations it is** — today it says "basin mean of the
NBM pointwise 50th-percentile snow level", accurate about the product and silent about the fact that
this is not a terrain intersection.

**UNKNOWN conditions.** No NBM core cycle; no basin QPF rate for the intensity term
(`intensity_dependent_offset_uncomputable`).

**Confidence ceiling: LOW.** The offset parameterisation is transferred from an idealised windward
ridge and **nobody has verified it against NBM output over the Washington Cascades**.

**Graduation.** EXPERIMENTAL until hindcast: NBM `SNOWLVL` percentiles versus SNOTEL sites
transitioning from accumulation to ablation during ARs. That is a bounded, buildable experiment against
data already ingested.

**Exit test.** The offset increases monotonically with the basin QPF rate; the December 2025 replay
produces a mountainside snow line consistent with the observed 0.0-in SWE at Alpine Meadows (3 500 ft),
Skookum Creek (3 320 ft), Rex River (3 810 ft) and Olallie Meadows (4 010 ft).

**6–120 h payoff.** White et al. (2002) modelled that a **~610 m (2 000 ft) in-storm snow-line rise
triples runoff** for three northern California mountain basins. Snow line is the single
highest-leverage forecast quantity in a maritime flood, and the platform currently displays a column
wet-bulb level with no terrain correction and calls it context.

---

#### M2.4 `method:rain-exposed-fraction@1.0.0` / `method:ros-exposed-fraction@1.0.0`

**Inputs.** M2.1 (hypsometry) × M2.3 (mountainside snow line) → rain-exposed fraction. Plus snow-covered
area and SWE-by-band → ROS-exposed fraction.

**Computation.** `rain_exposed_fraction` = fraction of basin hypsometry below `Z_S`.
`ros_exposed_fraction` = fraction below `Z_S` **that carries snow**, which needs SCA or SWE by band.
`method:swe-below-snow-line@1.0.0` reports SWE at elevations below `Z_S` — **not** percent of median,
which is the wrong statistic for the reason M1.2 documents.

**The SCA problem, stated honestly.** Optical SCA (MODIS/VIIRS) under the Cascade cloud deck during an
AR is exactly when it is unavailable. Any ROS-exposed fraction must carry an **SCA age** and go UNKNOWN
when the last clear view predates the storm. Passive microwave fails in wet/deep snow; SAR SWE
retrieval is immature in wet snow; airborne lidar is neither continuous nor cheap. This is the largest
unexamined sub-topic in the snow domain (its own §8 open question 4).

**Companion: `method:pack-buffer-capacity@1.0.0`.** `CC(SWE, T_pack)/λ_f + LWC_capacity × SWE`, in mm
of water per elevation band, with an explicit statement of how many hours of the forecast rain rate it
absorbs. Requires SNODAS pack temperature (parameter 1038) and SWE (1034) — documented but not
ingested, and carrying a known failure mode (unbounded SWE growth at Baker/Glacier Peak/Rainier cells)
that must travel as a **quality flag, not a correction**.

**The magnitudes this method must not overstate.** A 400 mm SWE maritime pack at −1 °C holds
`CC = 0.84 MJ m⁻² ≡ 2.5 mm` of melt forgone plus **~27–37 mm** of liquid (~44–60 mm at saturation) —
a **combined buffer of ~30–45 mm against a 200–400 mm AR**, i.e. the pack absorbs roughly **8–20 % of
the storm** and conducts the rest. *(The corpus's own correction: an earlier draft's 15 mm / 4–7 %
figures were wrong by ~3× because a volumetric LWC percentage was applied as a mass fraction of SWE.
The corrected numbers are what ships.)* Snowmelt supplies **~19–45 %** of the water reaching the ground
in a maritime ROS flood; rain supplies the rest.

**Hard rate ceilings as range validation** (Jennings & Jones 2015, lysimeters at H.J. Andrews): net
snowpack outflow **< 3 mm h⁻¹** in >97 % of peak-day hours, total **< 10 mm h⁻¹**, **never above
14 mm h⁻¹**, cumulative **< 300 mm** over a 10-day storm. Any derived melt quantity outside these is
`quality=out_of_range`, handled exactly as `DATA_DOCTRINE.md` §7 handles other physical bounds. Add a
`physical_ceiling` annotation to the variable so the rule is declared with the quantity rather than
living in a parser.

**One interpretation trap to encode as doctrine.** **A SNOTEL pillow that does not fall during a ROS
event is not evidence that the pack did not deliver water** — liquid retention and intermittent
snowfall can hold SWE flat or *increase* it across a ROS event, and preferential flow paths occupying
only 3–8 % of the cross-section can convey large volumes before bulk cold content is satisfied.

**Confidence ceiling: LOW**, and UNKNOWN whenever SCA age predates the storm.

**Exit test.** `rain_exposed_fraction` on 2025-12-11 for the Skagit is near 1.0 given a snow line above
4 000 ft, and `ros_exposed_fraction` returns UNKNOWN with an SCA-age reason rather than 0.

**6–120 h payoff.** This is the quantity that converts a basin QPF into "how much of this basin is
receiving rain rather than snow over the next 72 h", which is the first-order determinant of the flood
in a maritime AR. Once hypsometry exists, *rain-exposed fraction is a scored quantity with an
unambiguous sign* — the "never scored" rule that correctly applies to a bare snow-level elevation must
not be inherited by the derived fraction.

---

### TIER 3 — Forcing v1

`forcing.py` today bands on **one number**: the basin-area-weighted mean of the NBM pointwise p50 QPF
over 0–72 h, edges at 25/75/150 mm. It contains **no orientation, no duration, no melting level and no
sequence information** — none of the four non-magnitude terms in the only published five-term
description of what makes a western-Washington AR flood. Worse, the edges are probably too high: the
top-10 annual peak daily flows on the Sauk and Green occurred with **2-day Cascade precipitation totals
of 85–150 mm**, so the events that produced these basins' largest recorded flows of the past 30 years
land in the platform's **HIGH** band and only just touch VERY_HIGH; and `score_cap = 200 mm` makes the
top band saturate exactly where the discriminating information lives.

#### M3.1 `method:basin-ivt@1.0.0`

**Inputs.** GFS 0.25° `pgrb2b` pressure-level SPFH, UGRD, VGRD, 1000 → 200 hPa. `pgrb2a` does **not**
carry SPFH (already established in the repo's 2026-08-22 research). Via NOMADS
`filter_gfs_0p25.pl` with a lat/lon subset, or AWS `noaa-gfs-bdp-pds`. 4 cycles/day, ~3.5 h latency.
Alternative to verify: ERA5 / ECMWF open-data `viwve`/`viwvn` vertical integrals (an unverified OPEN
QUESTION in the AR entry; if present, the cheapest hindcast IVT for Event Zero replay).

**Computation.** `IVT = (1/g) ∫ q·V_h dp` from 1000 to 200 hPa (MERRA convention: every 25 hPa to
700, every 50 above). Emit `ivt_magnitude` and `ivt_direction` at (a) the basin's **coastal Eulerian
reference point** and (b) the basin mean. **Where the reference point should be is unresolved and it
changes every category the platform would compute** — the natural candidate is the coastal landfall
point upstream of the basin's optimal wind window, not the basin centroid. Record the choice as a
CONFIGURED parameter with that caveat.

**Why IVT and not IWV.** Less elevation-dependent; more directly related to precipitation; better NWP
skill; and it carries wind, which is half of the orographic forcing. The choice is not cosmetic: under
IVT ≥ 250 the AR-frequency maximum sits on the **Oregon–Washington coast**, under IWV ≥ 20 mm it sits
on the **Northern California coast** and declines northward. Any statement that Washington is the AR
maximum of the West Coast is conditional on a transport threshold.

**Cost.** 3 vars × ~13 levels × ~13 forecast steps (0–72 h at 6 h) over a 40–52 N / 115–140 W subset
≈ **15–25 MB/day** raw. With a 90-day R2 lifecycle that is ~2 GB steady state. Roughly doubles the
current 13.2 MB/day ingest and stays inside the free tier.

**Confidence ceiling: MODERATE.** IVT is well-forecast relative to precipitation, but the value is
model output and inherits GFS error.

**Exit test.** Recomputed IVT for a known Event Zero hour matches an independent ERA5/MERRA value
within 10 % (Ralph et al. 2017 measured <10 % agreement between IVT- and IWV-edge definitions of the
same storm's total transport, which sets the tolerance scale).

**6–120 h payoff.** It is the input to M3.2–M3.6, none of which exist without it.

---

#### M3.2 `method:upslope-ivt@1.0.0` — **the single highest-leverage new build**

**Inputs.** M3.1 (IVT vector at ~1 km MSL / the low-level-jet altitude, not the surface and not
700 hPa) × M2.2 (per-basin cross-barrier bearing).

**Computation.** `IVT⊥ = |IVT| · cos(θ_flow − θ_barrier)`, emitted **instantaneously and
time-integrated over the event**. Both matter and they are different features:
`upslope_ivt_kg_m_s` and `upslope_ivt_integrated`.

**The evidence, which is the strongest in the corpus.** Storm-total **upslope** IVT explains **74 % of
the variance in storm-total rainfall and 61 % of the variance in storm-total runoff volume** across 91
events (Ralph et al. 2013 — and note this is variance in *runoff*, not in precipitation). Over the
Olympics during OLYMPEX warm sectors, IVT⊥ against hourly rainfall gives **r² = 0.87 / 0.82 / 0.85**
with a best-fit slope of **0.014 mm h⁻¹ per (kg m⁻¹ s⁻¹)** — so +200 kg m⁻¹ s⁻¹ buys +2.8 mm h⁻¹
(Tierney & Durran 2024, western Washington, which is unusual good fortune given how Californian the AR
literature is).

**Read the skill number honestly.** The repository's prior pass reports "58–88 % (Neiman 2002)" as the
transfer function's skill; that is the **per-case** range across seven selected case studies. The
**season-long** figures at the same three couplets are **31 %, 48 % and 41 %**, rising to 56 % in
low-level-jet conditions. And Tierney & Durran's r² = 0.85 is for **warm-sector, unblocked** events —
the best case. The honest headline is r² ≈ 0.85 in the warm sector, with the blocking flag (M3.5)
travelling beside it.

**Never downscale QPF with a static orographic ratio.** Any scheme of the form "basin QPF × elevation
ratio" or "NBM cell × PRISM ratio" is the Mountain Mapper failure mode reimplemented. Smith & Barstad
(2004) state that raw upslope models over terrain rising and falling at scales **≤20 km can
overestimate total precipitation by a factor of 5 or greater**, and Smith et al. (2003) found upslope
estimates *exceeding the incoming moisture flux* in the Italian Alps — an outright violation of water
conservation. If sub-basin distribution is ever needed, the defensible options are to use the model's
own field at its native resolution and say so, or to implement S&B04 properly as a named, versioned
EXPERIMENTAL method with its five parameters recorded — never a ratio.

**Output contract.** Two `DerivedFeature` ids plus the `bearing_source` and `bearing_window` from M2.2
in the provenance.

**Confidence ceiling: MODERATE** for the two literature-seeded basins, **LOW** for the fitted six.

**Graduation.** EXPERIMENTAL until M6.1 verifies the Ralph 2013 duration→runoff scalings and the
IVT⊥→response relation in Cascade basins. Likely *higher* than the Californian numbers, not lower —
western Washington orography is steeper and wetter — but that is an inference, not a result.

**Exit test.** For the Green, IVT⊥ computed on the 245°–275° window separates the top-10 annual peak
days from magnitude-matched non-flood AR days better than unprojected `|IVT|` does. **That is a real,
falsifiable test on the platform's own record.**

**6–120 h payoff.** Direct and large. At a 24–72 h lead, two ARs with identical basin 72-h QPF and
different orientation have documented flood responses differing by nearly an order of magnitude. This
is the feature that tells the Green apart from the Snoqualmie in the same storm.

---

#### M3.3 `method:ar-duration@1.0.0`

**Computation.** Hours of **continuous** IVT ≥ 250 kg m⁻¹ s⁻¹ at the basin's Eulerian reference point,
in forecast and in analysis. Continuity is definitional: a sequence of ARs separated by sub-threshold
gaps is **not one event** and cannot be scored as one.

**Why it is co-equal with intensity, not a modifier.** ARs with **double** the composite mean duration
produced nearly **6× greater peak streamflow and more than 7× the storm-total runoff volume** (Ralph
et al. 2013). Mean duration at a coastal point is ~20 h; along the coast it peaks at **23–24 h on the
Oregon coast** and falls to **~19 h at the north-west tip of Washington**; about 50 % of coastal AR
events last more than 12 h.

**Also emit `duration_above_rate`** — hours of basin QPF above a moderate rate, and **the basin
fraction simultaneously above it**. This is the operational form of the corpus's most important scaling
statement: at basin scale the controlling variable is not *how much* rain fell but **how much of the
basin crossed threshold at the same time**. Hillslope thresholds are individually small (18–60 mm;
30 mm at the closest analogue site) and are crossed everywhere in a long maritime frontal storm; what
distinguishes an extreme is **simultaneity**. Peak-day hourly intensity in the largest western-Cascades
floods is **2.7 ± 0.9 mm h⁻¹** — long and moderate, not short and intense — and infiltration capacity
exceeds any plausible rain rate by ~20×, so intensity cannot generate Hortonian runoff outside roads
and impervious surfaces. The existing NBM grid-mask machinery can compute the simultaneity fraction
directly.

**This is also the honest way to settle a live contest.** Warner, Mass & Salathé (2012) find most
regional flooding events are associated with precipitation periods of **24 h or less** and that 2-day
totals capture nearly all major events; Jennings & Jones (2015) find the largest western-Cascades
floods are duration-driven. These are not necessarily inconsistent (different basins, response times
and metrics) but they support opposite design choices, and they are **unresolved for this platform's
specific basins**. `duration_above_rate` measures the thing both sides argue about.

**Confidence ceiling: MODERATE.**

**Exit test.** Event Zero's three ARs over 3–11 December 2025 are reported as **three durations, not
one 96 h event**.

**6–120 h payoff.** Duration is forecastable at 24–72 h and is worth ~6× on peak streamflow. It is the
single largest piece of information the current forcing band throws away.

---

#### M3.4 `method:orientation-favourability@1.0.0`

**Computation.** Angular distance between the forecast low-level wind direction (≈900–950 hPa, or 1 km
MSL — the low-level jet sits at **0.8–1.0 km MSL** in the western-Washington flood composite, with
maximum water-vapour flux just below 1 km) and the basin's CONFIGURED optimal window (M2.2). Emitted as
a **periodic** quantity that peaks in an interval, not a monotone scalar.

**Confidence ceiling: MODERATE** (Green, Sauk) / **LOW** (fitted six).

**Exit test.** The favourability is maximal inside 245°–275° for the Green and falls off on both sides;
the December 2025 replay reproduces the observed cross-basin ordering.

**6–120 h payoff.** The only western-Washington-specific, statistically significant flood discriminator
in the literature, available at 24–72 h lead from any wind forecast.

---

#### M3.5 `method:blocking-index@1.0.0`

**A flag that qualifies confidence, never a multiplier that corrects a number.**

**Computation.** `M = N·h/U` from the model sounding upstream of each basin — `h` = barrier height
(M2.2), `U` = cross-barrier wind, `N` from the model temperature profile.

**Bands from measurement, not textbook** (Purnell & Kirshbaum 2018, 18 OLYMPEX frontal periods):
warm-frontal mean **M = 1.1** (range 0.8–1.5), warm-sector **0.7** (0.5–0.9), post-frontal **2.5**
(1.2–3.9). So: **M ≲ 0.8 unblocked / high enhancement; M ≈ 1 transitional; M ≳ 2 blocked, enhancement
collapses and precipitation shifts upstream.** Under `DATA_DOCTRINE.md` §9 this is a **labelled
category, never a decimal confidence**.

**Two things it must not do.** (a) **Do not infer M from frontal sector** — the per-event spread
forbids it: two of six post-frontal periods had M ≤ 1.5 and one warm-frontal period reached 1.5. M must
be computed. (b) Note that latent heating during ascent reduces effective stratification, so flows that
would be blocked in dry air often surmount the barrier when condensation occurs; the "effective M" is
lower than an upstream dry calculation implies.

**Confidence ceiling: LOW.** It qualifies other numbers; it is not itself a hazard quantity.

**Exit test.** Warm-sector cases return M < 1 and post-frontal cases return M > 2 for the Olympics on
the OLYMPEX dates, from the same code path.

**6–120 h payoff.** It tells the operator when the QPF's own error structure changes sign — the
literature's cross-barrier bias is **signed and regime-dependent** (light/moderate events over-predicted
on upper windward slopes, heavy events under-predicted in lowlands and Cascade gaps; and modern
convection-permitting models show bias ratio rising windward→leeward). "Carries its own uncertainty"
becomes "carries its own *signed, regime-dependent* uncertainty, and here is the regime label".

---

#### M3.6 `method:ar-scale@0.1.0` and M3.7 `method:ar-sequence@0.1.0`

**AR presence and AR category are DERIVED quantities, not observations.** ARTMIP applied 20+ published
detection algorithms to one dataset and one period precisely to quantify method uncertainty: frequency,
duration and seasonality span a wide range across methods, and a Bayesian detector ensemble found that
**even the sign of the correlation between global AR count and ENSO depends on which plausible
parameter set is used**. Therefore the `method_version` **must encode the detector's parameters** —
variable, threshold, grid, geometry test, temporal continuity rule, promotion rule — and *two products
disagreeing about whether an AR is present is information, never a data fault.*

**M3.6 computation.** Ralph et al. (2019) scale from M3.1 (max 3-h IVT) and M3.3 (duration), computed
by Cascadia Papsukkal, badged DERIVED/EXPERIMENTAL. Record the mechanics that are usually lost: the
scale is **Eulerian at a point** with **no geometry requirement** (it is not an ARDT in the ARTMIP
sense); CW3E computes it on a **0.5° grid** the authors describe as somewhat arbitrary; duration ≥48 h
promotes **one** category and Cat 5 is the cap; and **promotion is common** — at Bodega Bay the mean
maximum 3-h IVT for Cats 3–5 came out *slightly below* the nominal threshold for those categories, so
**"AR 4" is not a statement that IVT reached 1000**. Carry the authors' own four stated limits, including
that the scale "will only be as reliable as the forecast model being used" — in their own GFS example
verification came in **~1 category stronger than forecast** over much of the West.

**A category can never be rendered as a basin hazard level.** The scale is explicitly not
location-linked, and the Russian River statistics are the demonstration: Cat 5 produced major flooding
in **3 of 10** cases, Cat 4 in **6 of 22**, Cat 3 in **2 of 78**. Three of the non-flooding Cat 5 events
struck early season or in drought with dry soils. **No AR-category-to-flood verification exists for
Washington at all** — building it from the platform's own history is a bounded, high-value hindcast and
would be a genuine contribution (M6.1).

**Never ingest a category from imagery.** CW3E's AR-scale products are image-only and research-use-only
(re-confirmed 2026-08-24: the `/arscale/` page exposes no data endpoint). A category read off a picture
has no `valid_time`, no `issued_at`, no model identity and no unit, and cannot satisfy
`DATA_DOCTRINE.md` §1. `HYDROLOGY.md` §4's forcing table currently lists "CW3E products" as a source
column; that must be struck.

**M3.7 computation.** AR family identification with an explicit `aggregation_period_d` parameter
(default 5 d per Fish et al. 2019) and an inter-event `recovery_gap_h`. **The window is regional, not
constant** — the time window within which clustering exceeds random chance varies by location.
Density matters more than count: over Oregon and Washington, AR precipitation intensity in dense
clusters is **120–140 %** of sparse, and **over the Cascade Range the extra runoff from dense clusters
is 150–300 % more than from sparse clusters** — the strongest region-specific evidence in the corpus
that temporal compounding matters *here*. Dense clusters peak in **November**.

**This is a correctness fix to Event Zero's description.** `HYDROLOGY.md` §12 reads "a CW3E AR-4
(coastal WA) / AR-3 (Cascade foothills) event with ~96 h of AR conditions". Under the scale's own
definition an AR event is one *continuous* period of AR conditions at a point; **three ARs across
3–11 December 2025 are an AR family**, and 96 h is the family span, not an event duration. Restate as a
family with per-AR categories and the inter-event gaps recorded.

**Confidence ceiling: LOW** for both.

**Exit test.** Changing the detector threshold changes `method_version` and produces a different, both-
recorded answer; Event Zero decomposes into three events with named gaps.

**6–120 h payoff.** M3.7 is the operationally live one: a reservoir's remaining buffer during a
multi-pulse sequence is a function of the **next** storm's forecast, not only the current one (USACE's
Seattle strategy of storing the peak and releasing as fast as prudent "to make room for a possible
subsequent rain event" is an explicit operational acknowledgement of AR families). M3.6 is mainly a
communication object and should be treated as one.

---

#### M3.8 `method:forcing-assessment@1.0.0`

Supersedes `@0.1.0`. The surface stops being a single banded scalar and becomes a multi-driver state:
QPF magnitude (kept, rebanded), **upslope IVT integrated**, **AR duration**, **duration-above-rate and
simultaneity fraction**, **orientation favourability**, **rain-exposed fraction**, **blocking index (as
a confidence qualifier)**, and a `mechanism` context driver (`ar_upslope` | `post_frontal_convective` |
`convergence_zone`) that is **displayed and never scored**.

**The PSCZ path is why the mechanism driver exists.** The Puget Sound Convergence Zone deposits
precipitation on the Snohomish/Skykomish/Snoqualmie headwaters through a mechanism that is neither
upslope nor IVT-driven, in the post-frontal sector where blocking has already broken the upslope
relation. **No IVT-based reasoning will see it.** At minimum: do not let a low IVT/QPF-derived forcing
level render as reassurance during post-frontal north-westerly flow.

**Rebanding.** Test the 25/75/150 mm edges against the two external anchors the corpus supplies — the
85–150 mm 2-day Cascade totals that accompanied the top-10 annual peak daily flows on the Sauk and
Green, and the NWRFC region's top-0.1 % daily precipitation of **73.7 mm/24 h** on a 32-km grid. Both
carry caveats (NARR composites and 32-km Stage IV are smoothed; the NWRFC region includes the dry
interior; a 72-h NBM pointwise-p50 basin mean is not a 2-day observed total) but the direction is
consistent and this is a cheap, high-value hindcast check.

**Confidence ceiling: MODERATE**, capped by the pointwise-percentile caveat that already applies.

**Exit test.** Two synthetic storms with identical basin 72-h QPF and different orientation produce
different forcing states, with the difference attributable to a named driver.

---

### TIER 4 — Official probability and basin QPE

#### M4.1 HEFS ingest + `method:hefs-exceedance@1.0.0`

**Buy the official probability before building one.** HEFS is live and machine-readable at **all six**
Cascadia seed LIDs.

**Inputs.** `https://api.water.noaa.gov/hefs/v1/{headers,ensembles,hydrograph-quantiles,locations}/`.
Measured live 2026-08-24: **45 members** indexed **1981–2025**; `parameter_id = QINE` (instantaneous
flow, CFS) **only — no stage parameter is served**; 6-hourly, 121 steps = **30 days**; **one cycle per
day at 12:00Z**; issuance latency **3 h 07 m – 6 h 14 m** across all ten retained cycles; **archive
depth ~10 cycles**. The service self-labels **EXPERIMENTAL** in its OpenAPI title.

**Provenance mapping.** `source_kind = MODELED`, **not** OFFICIAL_FORECAST — HEFS omits the forecaster
modifications (MODs) that constitute the NWS's operational data assimilation, and the endpoint
self-labels experimental. `issued_at = forecast_datetime`; `available_at = creation_datetime`;
`retrieved_at` = fetch time. *This is a rare case where the provider hands us all three cleanly — use
it as the reference implementation of three-valued time.*

**Store members, not quantiles**, and derive quantiles at read time. **Archive aggressively**: the API
keeps ~10 cycles, so without an ingest the forecast-evolution record for HEFS is lost after ten days.

**Do not call the member index an analogue.** The member index *is* a historical year, and the platform
may print it as an identifier — "12 of 45 members exceed…" — but MEFP conditions the forcing ensemble
on the *current single-valued forecast*; the historical year supplies the rank ordering (Schaake
shuffle) and the space–time covariance structure, **not the weather**. Member 1997 is "the trace that
inherits 1997's rank position", not "what 1997's weather would do to today's basin". Do not attribute
a historical year's meteorology to a member.

**Where the exceedance fraction can and cannot be computed.** At **AUBW1 and WRAW1** the official
categories are **flow-defined** (14 000/12 000/9 000/6 000 cfs and 12 000/10 000/7 500/5 500 cfs), so
`k of 45 members exceed 9 000 cfs` is defensible. At **MVEW1, CRNW1, RNTW1, NKSW1** the categories are
stage-defined and HEFS serves flow only, so ADR-0011 forbids the conversion.
`SurfaceReason.no_model_probability(why)` already exists; the reason string should now name the
specific blocker: *"official categories at this point are defined in stage; HEFS produces flow (QINE)
only; ADR-0011 forbids converting."* **This is the single most consequential local fact in the
forecasting domain** and it blocks HEFS and NWM identically.

**Report the distinct-value count with every fraction.** Measured: **all 45 members are exactly equal
at lead 0** at MVEW1, AUBW1 and WRAW1 — the served ensemble carries **zero initial-condition
uncertainty**, so its short-lead spread is forcing spread only and will be under-dispersed wherever
hydrologic uncertainty dominates. *A low measured spread in a dry month is not evidence of confidence.*

**Confidence ceiling: MODERATE.** It is an authoritative-model ensemble but not the official forecast,
and it is served from an experimental endpoint.

**Exit test.** A stored cycle at AUBW1 produces a member fraction with a distinct-value count; a stored
cycle at MVEW1 produces `no_model_probability` with the stage/flow reason, not a converted number.

**6–120 h payoff.** It is an authoritative 6-hourly probability distribution out to 30 days at every
seed point, at **~1.3 MB/day**. Nothing else in this document has that ratio.

**Cost:** 45 members × 121 steps × 6 LIDs × 1 cycle/day ≈ **1.3 MB/day**. Negligible.

---

#### M4.2 `method:mefp-forcing-ensemble@1.0.0` — the sleeper finding

The same HEFS API serves **MEFP basin-average precipitation, temperature and SWE ensembles**
(`parameter_id ∈ {MAP, MAT, SWE}` at numeric `location_id`s). The forcing surface currently derives
basin-average QPF itself from NBM; **NWRFC already publishes a bias-corrected, Schaake-shuffled,
45-member basin-average precipitation ensemble on the same zones its own hydrology model uses.** That
is a strictly better forcing input than anything the platform can derive, with the provenance chain
intact.

**Blocker:** the `/locations/` endpoint enumerates numeric ids; **mapping them to Skagit / Snoqualmie /
Green zones is an open question** and is the first task of this method.

**Confidence ceiling: MODERATE.** Same reasoning as M4.1.

**6–120 h payoff.** Replaces a pointwise-percentile basin mean (whose own docstring concedes it is not
the percentile of basin-mean QPF) with a genuine 45-member basin-average precipitation ensemble.

---

#### M4.3 `method:basin-qpe@1.0.0` → `method:qpe-intensity@1.0.0`

**The one genuinely costly ingest, and four domains asked for it.**

**Inputs.** MRMS MultiSensor QPE (Pass 2) hourly, **plus RQI and GaugeInflIndex with every QPE**, via
NODD (`noaa-mrms-pds`). Hourly, ~1 h latency.

**Computation — gate, do not merely annotate.** `DATA_SOURCES.md` P1 already says to ingest RQI with
every QPE; make it **binding**: a basin-mean MRMS value computed over cells whose RQI is below a stated
threshold is `quality=out_of_range` **with a reason, not a number**. The published construction
(`RQI = RQI_blk × RQI_hgt`, with `RQI_blk = 0` above 50 % blockage and 1 at ≤10 %, linear between)
means an RQI-weighted basin mean is computable and auditable.

**Record which engine produced each cell.** Where MRMS falls back to **Mountain Mapper**, the value is
*PRISM climatology rescaled by an inverse-distance-weighted (b = 2, D = 200 km) ratio to low-elevation
gauges*. Its stated failure modes: large errors when the real-time gradient differs from the PRISM
climatology; far-reaching interpolation where the gauge network is sparse; and it is applied **only to
stratiform rain**, i.e. **not applied at all in the frozen-precipitation season over the upper
basins** — which leaves a third fill path to identify, and which is precisely the blocked,
warm-frontal and convergence-zone cases. A Mountain-Mapper cell is a *climatological downscaling of a
distant gauge*, and the platform's one rule ("what transformed it") requires saying so. This is a
`source_kind`/lineage question, not a footnote.

**The honest bound on what any QPE can deliver here.** Radar covers only **¼ to ⅓** of the coastal
western US land surface adequately for QPE and reads **<50 %** of gauge values where the rain is
heaviest; the **Snoqualmie** is named among six flood-prone basins whose coverage is "either extremely
poor or nonexistent". Gauges undercatch **5–15 % in the lowlands, 15–20 % in Cascade gaps (~1 000 m),
and 25–40 % above 1 500 m** in exactly this region. Spread among gridded precipitation datasets is
±20 % in annual means and **greatest in maritime ranges**. **UNKNOWN and a signed, regime-dependent
error bar are the honest outputs; a bare basin-mean millimetre value is not.**

**Companion: a catch-efficiency field on every precipitation observation.** Either apply the
Kochendorfer et al. (2018) correction `CE = a·exp(−b·U) + (1−a)` (capped at `U_thresh = 7.2 m s⁻¹` for
unshielded gauges) as a DERIVED value with lineage to the raw reading, or carry an `undercatch_class`.
Silently comparing an uncorrected SNOTEL `PREC` at 1 400 m against an NBM basin mean is a 25–40 % error
**with a known sign**.

**`method:qpe-intensity@1.0.0`.** From the same hourly field: `qpe_i60_max_6h`, `qpe_p3_in` (72 h),
`qpe_p15_in` (360 h), `duration_above_rate`, and the basin fraction simultaneously above a rate. Then
`method:landslide-threshold-margin@0.1.0` = `P3 − (3.5 − 0.67·P15)` (inches, Chleborad et al. 2006),
**labelled EXPERIMENTAL and scoped to the Seattle/Puget Lowland region the threshold was fitted for —
never extrapolated to a mountain basin.**

**Why the intensity features are the right ones for this region, and the negative transfer that proves
it.** For maritime western Washington the calibrated shallow-landslide predictor is **multi-day
accumulation with antecedent memory**, not short-duration intensity: shallow landsliding, not runoff
generation, is the dominant debris-flow initiation mechanism here, burned or unburned. The cleanest
demonstration is Thomas et al. (2023): an AR delivering **258.6 mm** of rain with a peak I₁₅ of only
**16.8 mm h⁻¹** produced streamflow and a ~2 000 m³ sand deposit, while a thunderstorm delivering
**33.4 mm** — an order of magnitude less water — with a peak I₁₅ of **39.2 mm h⁻¹** produced debris
flows depositing **≥10 000 m³**. So: **post-fire debris-flow hazard in these basins is a warm-season
convective and a rain-on-snow hazard, not an AR hazard**, and it does not coincide with the flood
season the platform is built around. It is not zero — the WGS WALERT report emphasises that all four
2022 fires lie in mapped rain-on-snow zones and that the USGS model does not represent rain-on-snow at
all.

**Basin-mean is the right aggregation; per-cell display is not.** The ridge-crest signal is
**50–300 %** at ~10 km scale, at or below the *effective* resolution of the NBM 2.5 km grid. Rendering
a cell value on a map as "precipitation here" asserts placement skill the product does not have.

**Cost — the honest number.** MRMS is published per-CONUS-product; there is no NOMADS-style subsetter
equivalent to `filter_blend.pl`. MultiSensor Pass2 CONUS hourly grib2.gz is roughly 1–3 MB compressed;
RQI similar. Downloading both hourly is **~50–100 MB/day**, which at a 90-day lifecycle is **4.5–9 GB**
— alone near the R2 free-tier limit of 10 GB. **Recommendation: decode on ingest, store the basin means
and the RQI-weighted coverage permanently, and keep the raw CONUS payload for 14 days only** (~0.7–1.4
GB steady state). That preserves the platform's raw-archive doctrine for the recent window while
staying inside the free tier. Flag this as the one build that needs an explicit cost decision.

**Confidence ceiling: LOW** in the Cascade headwaters (RQI-gated, frequently refused), **MODERATE** in
the lowlands.

**Exit test.** A Cascade-headwater basin mean during a beam-blocked hour returns
`quality=out_of_range` with the RQI reason rather than a number; a Mountain-Mapper cell is labelled as
one in the lineage.

**6–120 h payoff.** Two. (a) It closes the QPF verification loop — the platform can finally ask "did
the forcing arrive?" inside the event, which is the single most useful update between the 72 h and the
12 h forecast. (b) `duration_above_rate` and the simultaneity fraction are computed on *observations*,
which is what turns the corpus's central scaling insight into an operational signal.

---

#### M4.4 `method:antecedent-index@0.1.0`

**Two candidates, and the recommendation is the cheaper one.**

**(a) 90-day SSPI from AORC.** `noaa-nws-aorc-v1-1-1km` carries per-year Zarr from **1979** at 1 km
(verified on S3). Fit a Gamma reference to rolling 90-day totals **ending during the cool season** and
map the current total to a standard normal deviate (Webb et al. 2026 methods). **One-time climatology
build; store only the fitted Gamma parameters per basin per day-of-year — kilobytes.** The operational
value then comes from the platform's own accumulating basin QPE (M4.3) or from a lighter AORC read.

**(b) NWM soil-saturation percentile.** Verified 2026-08-24: `ldasout.zarr` on
`noaa-nwm-retrospective-3-0-pds` carries `SOIL_M`, "volumetric soil moisture", m³ m⁻³, shape
[128 568, 3 840, 4, 4 608] — 128 568 three-hourly steps from **1979-02-01T03:00**, 1 km LCC, 4 soil
layers. A 44-year, 1-km, per-day-of-year climatology is buildable now with no new provider agreement.
**But** the *operational* current value needs NWM AnA land output, which is the single largest byte
cost anywhere in this corpus, and the domain's own open question 4 asks whether SOIL_M will simply
track the flow percentile (both being pinned near saturation from November). Known hazards: the
retrospective is v3.0 while the operational stream is v3.1, there is an archive gap 2023-02 → 2025-01,
and the layer thicknesses are an ASSUMPTION — the Zarr metadata carries **no depth coordinate**. Noah-MP's
2 m column may also be the wrong control volume for basins whose active store is a deep permeable
colluvial mantle over bedrock.

**Recommendation: build (a) first, and defer (b) until M6.2 says whether it adds anything.**

**Report disagreement; never average.** If both exist, report the signed difference between the NWM
soil percentile and the streamflow percentile as a driver. That disagreement is the platform's honest
expression of storage–discharge **hysteresis**: on the rising limb a flow percentile *understates*
storage and on the recession limb it *overstates* it, so a basin can be near its connectivity threshold
while its river is still low — precisely the state in which a susceptibility surface would earn its
keep. Do **not** average the flow percentile with a soil percentile into a single "wetness" number.

**Ship it as a displayed feature first, not as a forcing modifier.** Do **not** ship the Webb 2026
promote/demote rule (AR rank ±1 at SSPI ≷ ±0.5) until M6.2 hindcasts it here: the paper contains
**97 California + 45 central Chile catchments and zero PNW**, its six low-improvement catchments are
the cooler ones, and it says snow-dominated regions "may require… tools that explicitly account for
snow processes".

**Consider a transparent fallback with no model dependency.** A single-production-store SMA index
(AORC precipitation minus a reference PET) sits at the **top** of the estimator ranking in the one
study that ranks all four (R² = 0.90 vs API 0.82 vs antecedent-discharge 0.67 vs the textbook SCS
5-day rule 0.19), and a calibrated bucket topped 18 global soil-moisture products (median R = 0.78).

**Confidence ceiling: LOW.**

**Exit test.** A December 2025 replay produces an SSPI value whose Gamma reference was fitted on
cool-season-ending windows **excluding** the replay year.

**6–120 h payoff.** Conditional on M6.2 returning a positive result. If it returns a null for western
Washington, that is a publishable finding and the correct action is to say so and not ship the modifier.

---

### TIER 5 — Reservoir and coastal state

#### M5.1 `method:reservoir-buffer@1.0.0` → `method:hours-to-top-of-flood@0.1.0`

**The measured failure this fixes.** `HYDROLOGY.md` §10 defines flood-buffer capacity as "available
flood-control storage (rule-curve maximum − current storage)". In December 2025 that single definition
would have shown Ross at **~22 % of its designated flood pool** — a quarter full — during the event in
which Ross removed **110 900 acre-feet** from the Skagit, i.e. **92 % of a full design flood pool**.
Both numbers are true; only the second describes what happened. The buffer that mattered was that Ross
entered the storm **7.6 ft below** its required rule curve.

**Three volumes, three meanings, three provenances.**
```
required_buffer_ac_ft  = S(rule_curve_elev_today) − S(pool_now)    # MAY BE NEGATIVE (encroached)
available_buffer_ac_ft = S(top_of_flood_elev)     − S(pool_now)    # what physically remains
allocated_pool_ac_ft   = S(top_of_flood_elev)     − S(rule_curve_elev_today)   # the policy volume
pool_below_curve       = max(0, S(rule) − S(pool))                 # DISCRETIONARY buffer
```
`required_buffer` negative means the pool is **encroached into the flood pool** — render it signed,
never clipped, and use the operators' own word. `pool_below_curve` is a first-class signal: buffer the
operator is not obliged to have and may spend on power or supply at any moment (~81 000 ac-ft at Ross
and ~49 000 at Upper Baker in December 2025). It must be labelled *discretionary* and never added to
`required_buffer` without saying which part is which.

**The rule curve is machine-readable — read it, do not reconstruct it.** CWMS `/levels` (the **list**
path; `/levels/{id}` returns HTTP 500) with `office=NWDP&level-id-mask=ROS.*` returns
`ROS.Elev-Forebay.Inst.0.Bottom of Flood Control` carrying the **entire seasonal rule curve** as a
structured `seasonal-values` array. A2W's `REGULAR` level is the same function evaluated today and
rounded to whole feet — the lossy view. **Two live curves disagree with the published manuals and the
live one wins**: Upper Baker's CWMS curve steps to 711.60 ft on **2 October** and holds to ~3 March
(Table 10 phases down only by 15 November), and Howard Hanson's live winter curve reads **1 060 ft**,
not the manual's 1 075 ft. Seed from CWMS, snapshot daily for change detection, and treat any change as
an event — the seasonal array carries **no version history**.

**Do not compute buffer from the provider's storage series.** At Howard Hanson's December 2025 peak the
reported elevation rose 1 188.98 → 1 189.30 ft while the reported storage **fell** 75 257 → 75 172
ac-ft. A single-valued capacity curve cannot do that. Store **pool elevation** as the primary
observable, carry the project's elevation–storage table as a **versioned CONFIGURED artefact with its
survey date**, derive storage as DERIVED with lineage, and keep the provider's storage series *beside*
it as an independent OBSERVED series. When they disagree beyond a declared tolerance that is a
`model_agreement`-class assessment about the reservoir, not an error to hide. (Live series sit **3.3 %**
below the HHD table and **7.2 %** below the MMD table at the same elevation; USACE's own press release
used the table for HHD and the series for MMD, in the same document.)

**Datum discipline is worse here than anywhere else in the platform.** Every A2W series returns
`"vertical_datum": "NGVD29"` — including Upper Baker, whose licence and manual use **NAVD88**, and Ross,
whose Table 15 elevations are in **SCL datum** (footnoted as 1.79 ft above NGVD29 — worth ~20 000 ac-ft
of apparent buffer). **The A2W `vertical_datum` field is a service-wide default and must not be
trusted.** Treat reservoir pool datum as CONFIGURED per project from the manual or licence, never from
the feed.

**`hours_to_top_of_flood`** = `available_buffer / (0.0826446 × max(0, Q_in − Q_out))`, over a named
window, UNKNOWN when net inflow ≤ 0, always carrying *"assumes present release continues"* — **because
it does not**: evacuation is rule-bound (33 CFR 208.11 requires water be evacuated "as rapidly as can
be safely accomplished without causing downstream flows to exceed the controlling rates"), and a
reservoir's remaining buffer during a multi-pulse AR sequence is a function of the **next** storm's
forecast. Worked reference: Howard Hanson bottomed at **≈33 h** at 2025-12-12T00Z.

**Control fraction is the hard ceiling and belongs in the contract.** Howard Hanson regulates **55 %**
of the area above Auburn; Mud Mountain **42 %** at Puyallup; Ross + Upper Baker **39 %** of the area at
Mount Vernon (32 % of mean annual runoff). The Skagit's uncontrolled area is dominated by the **Sauk**
(732 mi², just over 50 % of the uncontrolled area), which contributed 45 / 46 / 64 / 59 % of the
Concrete peak in the 1990, 1995, 2003 and 2006 floods. Above roughly the 25-year event, uncontrolled
runoff "is sufficient to produce major flooding in the valley **regardless of the flood control
regulation**". The regulation effectiveness curve is a **hump**: 0 % at the 2-year event, maximum
**17.8 %** at the 25-year, decaying to **10.8 %** at the 500-year.

**Reservoir inflow forecasts exist — but do not hard-code that they do.** NWPS serves them as ordinary
gauge objects: `RODW1`, `MORW1`, `TLRW1` returned live 30-point 6-hourly `QIIFZ` forecasts on
2026-08-24, and `MMRW1` returns outflow. **`UBDW1` and `HHDW1` returned empty `data` arrays with
three-week-old `issuedTime`s** — and *an empty `data` array with a live-looking metadata block is
exactly the shape that silently renders as "no flood risk"*. The ingest must distinguish *forecast
absent* from *forecast of low flow*, and treat `issuedTime` age as a first-class staleness signal.

**And label what the official downstream forecast already contains.** NWRFC "incorporates the planned
regulation into the forecast of reservoir elevation and discharge at Auburn" — so the official forecast
at a regulated point is a **conditional forecast, conditional on an operating intention that is not
published**. Every regulated forecast point should render that sentence. This qualifies §10's "the
platform never infers dam operations; it reports them": correct as a prohibition, incomplete as a
description.

**Section 7 status has no public feed.** It is a binary, time-stamped, legally-defined state
("Corps-directed" vs "owner-directed") that changes the meaning of every release; on the Skagit it
flipped on 2025-12-08 and again at 08:30 on 2025-12-15. It appears in press releases and in
`-RAW`/`-COMPUTED` provenance tags, not as a field. Carry it as a curated, dated CONFIGURED series
with a citation per transition, defaulting to `UNKNOWN` with a reason.

**Confidence ceiling: MODERATE** for the buffers (they are arithmetic on an observed elevation and a
versioned table), **LOW** for `hours_to_top_of_flood` (it assumes a release that will change).

**Exit test.** A December 2025 replay reports all three Ross volumes with the discretionary part named,
and a synthetic encroached pool renders "encroached into the flood pool by N ft" rather than a
percentage.

**6–120 h payoff.** `hours_to_top_of_flood` is a 12–72 h quantity by construction, and the three-buffer
split is what makes it interpretable. Copy rules this forces: never render a reservoir as "protecting"
a place; never display "damages prevented".

---

#### M5.2 `method:skew-surge@1.0.0` + a coastal sub-state at TIDAL points only

**Computation.** **Skew surge, not non-tidal residual, and computed per tidal cycle**: match each
predicted high water to the maximum observed water level within ±3 h and store the matched pair so the
match is auditable. *The calendar-day shortcut is wrong by up to 2 ft in spring* — Seattle's diurnal
inequality puts the higher-high near local midnight in late spring and a day boundary splits the pair,
producing spurious +3.5 to +4.6 ft "surges".

**Measured context to seed.** Seattle 1996–2025, 21 166 matched cycles: mean **+0.116 ft**, p90 +0.668,
p99 +1.375, max **+2.576 ft**; winter p99 **+1.609 ft**; **zero cycles above 3.0 ft in 30 years**.
ρ(predicted HW, skew surge) = −0.094 — near-independent, which licenses the multiply-the-marginals
form, with the small negative tendency logged (Santamaria-Aguilar & Vafeidis contest independence for
mixed semidiurnal regimes, which is Puget Sound's).

**Never sum tide + surge + river.** In the Duwamish the nonlinear interaction terms are **first-order,
not corrections**: tide–surge interaction is +10 % of total water level downstream and is what lifts a
king tide from *no flooding* to *major flooding*, while surge–river and tide–river interactions are
**negative**, reaching −17 % / −40 % (SRI) and −10 % (TRI) upstream, together reducing upstream water
levels by **up to 50 %** relative to a linear sum. Anyone who adds arithmetically will over-predict
upstream and under-predict downstream. If a combined water level is ever displayed it must come from a
hydrodynamic model (SSCOFS, PS-CoSMoS) or be labelled an upper bound that ignores nonlinear damping.

**Record what Event Zero did *not* sample.** All three record crests occurred at **4.8–6.6 ft below
MHHW** with **no skew surge anywhere in the AR sequence exceeding +1.17 ft**. Without that fact
recorded, any skill score computed on Event Zero silently assumes a benign coastal boundary and will
mislead the first time an AR crest lands on a king tide. Add a coastal block to every historical crest
in the hindcast set: concurrent observed water level, predicted high water, and skew surge at the
reference tide station.

**Recommendation on architecture.** Coastal water level is a **modifier of hazard at `TIDAL` points**,
not a fourth basin surface — it is a boundary condition, not a basin property, and only a minority of
forecast points feel it.

**Contract additions.** `Station.station_kind ∈ {river_gauge, tide_gauge, tide_prediction_only,
ofs_virtual}`; `tidal_datum_epoch` required when any tidal datum is present; `navd88_tie: null` with a
reason rather than a computed guess (**NAVD88 is not published at Port Townsend, Cherry Point, Friday
Harbor, Bremerton or La Conner** — converting a tidal datum to NAVD88 there requires VDatum, not
arithmetic). `Threshold.datum_family ∈ {gauge_datum, tidal_datum, geodetic_datum}` + `reference_datum`,
with construction **refused** when the family is unknown — this is what makes NWPS's EBSW1 "2.1 ft"
safe to store.

**Two provider guards to encode.** (a) NWPS carries two Puget Sound tide gauges (`EBSW1`, `BMTW1`) with
SHEF PE `HC`, which the NWS SHEF manual defines as **"Height, ceiling"** — a cloud-base variable — while
`HM` is "Height of tide, MLLW"; their values are **MHHW-relative with no datum recorded**, and the
`/stageflow` response labels the series "Ceiling Height" in ft with a secondary "Flow" in kcfs.
Recommended: **exclude both LIDs and use CO-OPS directly** (`EBSW1` returns no data at all). (b) CO-OPS
`sealvltrends.json` reports `"seasonalUnits": "inches"` while the values are **feet**; encode a unit
override with that note as its provenance. CO-OPS also returns errors as `{"error":{...}}` with **HTTP
200** — parse the body, do not trust the status code.

**Sea level is a *local* measurement, never a regional constant.** Cherry Point (nearest the Nooksack
delta) trends **−0.06 mm yr⁻¹, 95 % CI [−0.64, +0.52]** — statistically indistinguishable from zero —
while Seattle 115 km away rises at **+2.09 mm yr⁻¹** with a tight interval. That 2.15 mm yr⁻¹ spread
across one inland sea is vertical land motion, and it forbids a single regional constant. Neah Bay's
relative sea level is **falling** (−1.70 mm yr⁻¹). Where the CI includes zero, say so rather than
applying a small positive number for tidiness.

**Confidence ceiling: MODERATE** for skew surge (arithmetic on two published series), **UNKNOWN** for
anything combined.

**Exit test.** The December 2022 Seattle event reproduces 15.12 ft MLLW and a +2.22 ft skew surge, which
independently matches Spicer et al.'s published 3.90 m NAVD88 and 0.7 m surge to 0.02 ft and 0.02 m.
*This is a genuine external cross-validation of the whole chain.*

**6–120 h payoff.** Only at SNAW1 and the delta reaches. Elsewhere its payoff is **negative work
avoided**: it is the measurement that says do *not* build a river-plus-tide joint model at Mount
Vernon, which would be solving the wrong problem.

---

### TIER 6 — Evaluation

#### M6.1 `method:hindcast-harness@1.0.0`

**The central evaluation problem is rarity.** Measured base rates at the six seed points: minor
flooding occurs on **0.16 %–0.77 %** of days. At the two regulated points the upper categories are
nearly or entirely empty: **AUBW1 moderate has 2 instantaneous exceedances since 1990** (12 400 cfs in
1996, 12 200 in 2006) and **AUBW1 major and WRAW1 major are genuinely empty over the post-dam record**.
Any conventional skill score computed on that sample is dominated by the base rate and will read
"excellent" for a forecast that says *no flood, forever*.

**Base rates must be computed from instantaneous values, not daily means.** NWS categories are defined
on instantaneous stage/flow; computing exceedance from daily means silently redefines the event, which
the platform's own "official thresholds, in the unit NWS defines them" rule forbids. Measured: the
December 2025 MVEW1 crest was **37.73 ft instantaneous versus a 35.06 ft daily mean** — a 2.67 ft
shortfall on the one day that matters most.

**Required design.**
- **Verification unit = event, not timestep.** Timestep-pooled scores at a 0.36 % base rate measure the
  dry season.
- **`UNVERIFIABLE` is a legitimate verdict**, alongside UNKNOWN: `UNVERIFIABLE (n_events = 0 in 62
  post-dam years)`, never "skill = 1.0" and never a blank.
- **Every skill number carries its reference, stratum and event count**:
  `{metric, value, reference, n_pairs, n_events, base_rate, stratum, lead_time, method_version,
  evaluated_at}`. A CRPSS without a named reference is meaningless — climatology and persistence give
  different answers, and **climatology inherits persistence skill at day 1**, so the day-1 score is
  systematically depressed. Report persistence as a second reference at short lead.
- **Report SEDI alongside POD/FAR**, never POD/FAR alone — threat score, ETS and hit rate *degenerate*
  as the base rate → 0. This is a proved property, not a modelling opinion.
- **Report CRPS**, which reduces to MAE for a deterministic forecast — the one score that puts the
  official single-valued forecast, HEFS and any Cascade ensemble on the same axis.
- **Report the bias-corrected Brier decomposition** (Ferro & Fricker 2012) with `n` and `K` stated. The
  bias scales as K/n: at MVEW1's minor threshold `UNC ≈ 0.00356`, so with K = 10 and n = 500 the
  reliability inflation is ~2 % of the entire uncertainty term before any real miscalibration; at
  n = 100 it is 10 %. **A reliability diagram drawn from a few winters of western Washington data is
  measuring its own sampling noise.**
- **Do not rest a reliability claim on a rank histogram alone** — spread–error and rank-based
  diagnostics can pass while an ensemble is demonstrably miscalibrated (Dirkson & Buehner 2025;
  contested and very recent, so state it as a live dispute).
- **Compute relative economic value V(α) across α ∈ [0.001, 0.1] and publish the curve, not a point.**
  V peaks where the cost/loss ratio equals the base rate, and `s̄ = 0.0016–0.0077` here — so the only
  users for whom this signal has value are those whose **cost of acting is under ~1 % of their loss**:
  cheap precautionary actions, not expensive irreversible ones. *That is an argument for building the
  product around lead time on cheap actions, and against ever implying it supports expensive
  decisions.*
- **Bootstrap intervals on every score.** At these base rates the interval will usually contain zero,
  and that is the finding.
- **Stratify by regime × rising/falling limb × observed magnitude band.** Aggregate statistics hide the
  tail: NWS's own analysis showed a point with RMSE 0.8 ft and ME −0.1 ft **under-forecasting the
  largest events**, with POD falling and FAR rising as observed stage rises. Rain-on-snow will be the
  last regime to acquire a verifiable sample and should be flagged as such from the start.
- **Handle the no-forecast problem.** Many points are flood-only: a flood that was not anticipated
  produces *no forecast–observation pair at all* and silently vanishes from the sample. It is a **miss,
  not an absence**. The existing `quality=missing` row discipline is the mechanism; it must apply to
  *forecasts that were never issued*.
- **Measure timing by threshold-crossing time** (Morris 1988), not peak-time difference on a hydrograph
  that may have no crest — a lesson `agreement.py` already learned the hard way.
- **Verify consistency separately from accuracy.** Forecast jumpiness and forecast error are only
  weakly correlated. Event Zero is the platform's best available consistency benchmark: the Mount Vernon
  official crest evolved **36.9 → 41.5 → 42.3 → 39.1 → 38.26 ft** against an observed **37.73 ft** — a
  textbook flip-flop with a **+4.57 ft peak over-forecast**. That number should be in the doctrine,
  because it sets the scale of what "the official forecast can be wrong by" in this region and is the
  honest counterweight to badging it OFFICIAL.

**Pin versions, not just timestamps.** `as_known_at(T)` is necessary and not sufficient. Three
look-ahead channels escape it: **product-version improvement** (AORC v1.0→v1.1, MRMS re-gridding),
**model-version change** (NWM v3.0→v3.1 on 2026-08-18 — any archive the platform holds already
straddles it), and **archive survivorship** (HEFS keeps ~10 cycles; what was purged is *invisible*, not
`quality=missing`). Every forecast row must carry its producing model/product version, and a hindcast
spanning a boundary must refuse or declare the split.

**Where "what would have happened" is unobservable** — regulated reaches — pseudo-observation
verification against a reference simulation is the only way to separate *model error* from *operator
decision*, and it must be badged as such and never conflated with verification against gauges.

**Exit test.** The harness returns `UNVERIFIABLE (n_events = 2)` at AUBW1 moderate and refuses to emit
a skill number there; it returns a V(α) curve rather than a scalar; and a hindcast configured to span
2026-08-18 refuses with a model-version reason.

**6–120 h payoff.** Indirect: it is the only mechanism by which anything in this document stops being
EXPERIMENTAL. `TESTING.md` §7's promotion rule (EXPERIMENTAL → DERIVED only with a committed, reviewed
evaluation report linked from the `Method` row) is exactly right and should be extended: the report must
contain the reliability diagram *and its n*, the REV curve, the stratum table with event counts, and an
explicit list of strata marked UNVERIFIABLE. **A method may not be promoted on aggregate skill alone.**

---

#### M6.2 `method:conditional-antecedent-skill@1.0.0` — the decisive experiment

Four domains converge on one question and none of them can answer it alone: **does antecedent state add
skill in western Washington *conditional on the forcing*?**

**Design.** Score four antecedent formulations — DOY flow percentile, its 48 h delta, the NWM/AORC soil
percentile, and the 90-day SSPI — against cool-season peaks in the six configured basins, **conditioned
on basin QPE/QPF**, so the test is "does antecedent state add skill given the forcing" rather than "does
high flow follow high flow". Every flow-only computation in the corpus is uncontrolled for
precipitation and therefore bounds the effect loosely rather than measuring it.

**Companion experiments this unlocks, in priority order.**
1. **AR category → flood verification for Washington.** None exists in the literature; the only
   category-to-flood mapping anywhere is the Russian River. Building the Washington equivalent from AR
   category at a coastal reference point versus NWS category exceedance at Mount Vernon, Concrete, Gold
   Bar, Carnation, Snohomish and Ferndale is bounded, high-value, and **a genuine contribution**.
2. **The basin-scale connectivity threshold in mm of basin QPE.** The hillslope literature says
   18–60 mm; **nobody has published a basin-scale value for the Sauk, Snoqualmie or Nooksack.**
   Estimable from M4.3 plus the stored hydrographs.
3. **Do the Ralph 2013 duration→runoff scalings (≈6× peak, >7× volume for 2× duration) hold in Cascade
   basins?** Testable once M3.1–M3.3 exist.
4. **Does `g(Q)` extrapolate to flood flows?** Kirchner's recession plots reached ~1–1.5 mm h⁻¹; the
   corpus fits reach 1.5–3.0; December 2025 exceeded both. Testing `g(Q)`-predicted peaks against Event
   Zero is the obvious hindcast.
5. **What is the actual offset between NBM wet-bulb `SNOWLVL` and the observed Cascade mountainside
   snow line?** Hindcastable: NBM `SNOWLVL` percentiles versus SNOTEL sites transitioning from
   accumulation to ablation during ARs.
6. **How many independent flood events per season do the eight basins collectively produce?** This is
   the real sample size for anything the platform wants to verify, nothing has quantified it, and it is
   computable from the USGS record. **It should be computed before any evaluation plan is written.**

**A null result is a result.** Six catchments in Webb et al. (2026) with "cooler mean annual
temperatures" showed little or no improvement from an antecedent index. A null for western Washington is
a publishable finding and should be sought, not avoided.

---

## 4. New data sources

All are US-federal public domain unless noted. "Cost" is recurring infrastructure cost, which the owner
constraint says must be zero unless required for functionality actively being built.

| ID | Source / endpoint | Gives | Cadence · latency | Bytes/day | Licence · cost | Needed by |
|---|---|---|---|---|---|---|
| **G1** | GFS 0.25° `pgrb2b` pressure levels (SPFH/UGRD/VGRD) — NOMADS `filter_gfs_0p25.pl` or `noaa-gfs-bdp-pds` | IVT magnitude and direction | 4 cycles/day · ~3.5 h | **15–25 MB** raw (~2 GB at 90-day lifecycle) | public domain · $0 | M3.1–M3.6 |
| **G1a** | ECMWF open data `viwve`/`viwvn`, or ERA5 vertical integrals | cheapest hindcast IVT | — | — | **unverified — OPEN QUESTION** | M6.1 replay |
| **H1** | NWS HEFS API `https://api.water.noaa.gov/hefs/v1/` | 45-member flow ensemble at all six seed LIDs; MEFP MAP/MAT/SWE basin ensembles | 1 cycle/day 12Z · 3–6 h | **~1.3 MB** | public domain · $0 · **self-labelled EXPERIMENTAL** | M4.1, M4.2 |
| **P2** | MRMS MultiSensor QPE Pass 2 + **RQI** + GaugeInflIndex — NODD `noaa-mrms-pds` | basin QPE, I₆₀, duration-above-rate, simultaneity, QPF verification | hourly · ~1 h | **50–100 MB** CONUS (**recommend 14-day raw retention** → ~0.7–1.4 GB) | public domain · **$0 only with the retention rule** | M4.3, M4.4 |
| **P3** | AORC v1.1 1 km Zarr — `noaa-nws-aorc-v1-1-1km` | 1979– forcing archive for the SSPI Gamma reference | one-time | ~0 steady state | public domain · $0 | M4.4 |
| **S3** | NWM v3.0 retrospective `ldasout.zarr` — `noaa-nwm-retrospective-3-0-pds` | 44-year 1-km SOIL_M climatology | one-time | ~0 steady state | public domain · $0 | M4.4(b) — **deferred** |
| **E1** | USGS 3DEP (or Copernicus GLO-30 fallback) | basin hypsometry, barrier bearing and height | one-time | ~0 steady state | 3DEP public domain; GLO-30 free **with attribution** · $0 | M2.1, M2.2 |
| **R3** | USGS OGC `field-measurements` `?monitoring_location_id=USGS-{id}&parameter_code=00065` | gage-height/discharge pairs, measurement rating, `control_condition` | monthly | <1 MB | public domain · $0 | M1.3, M1.4 |
| **R4** | USGS expanded ratings `get_ratings?…&file_type=exsa` | rating id, shifts with begin/end, **the analyst's remark**, full table | monthly | <1 MB | public domain · $0 | M1.3 |
| **R5** | USGS OGC `peaks` + `monitoring-locations` | annual peaks with qualification codes; drainage area; `vertical_datum` | monthly | <1 MB | public domain · $0 | M0.5, M1.3 |
| **N1** | NWPS `flood.crests.historic` (already ingested endpoint) | 93 historic crests with preliminary/observed/revised flags | 6-hourly | included | public domain · $0 | M0.5 |
| **C1** | NOAA CO-OPS datagetter + mdapi + `sealvltrends` | water level, predictions, high/low, datums, flood levels, RSL trends | 6-min · ~10 min | **~1 MB** | public domain · $0 · **note the unit-label bug and HTTP-200 errors** | M1.5, M5.2 |
| **C2** | NOAA SSCOFS via CO-OPS `product=ofs_water_level` | modelled water level at **Sneeoosh Point, Swinomish, Everett, Tulare Beach, Bellingham** — where no real gauge exists | 6-min nowcast + ~94 h forecast | ~2 MB | public domain · $0 · **MODELED, never OFFICIAL** | M5.2 |
| **U1** | USACE CWMS CDA `/levels` (list path) + A2W timeseries, office `NWDP` | seasonal rule curves as `seasonal-values`; pool elevation, storage, computed inflow, outflow | hourly · ~1 h | **~1 MB** | public domain · $0 · `/levels/{id}` returns 500; `vertical_datum` field untrustworthy | M5.1 |
| **U2** | NWPS `/gauges/{RODW1,UBDW1,HHDW1,MORW1,TLRW1,MMRW1}/stageflow` | official reservoir inflow/outflow forecasts | daily | <1 MB | public domain · $0 · **UBDW1/HHDW1 currently serve empty arrays** | M5.1 |
| **S2** | SNODAS pack temperature (1038) + SWE (1034), NSIDC G02158 | cold content for pack-buffer capacity | daily | ~5 MB | public domain · $0 · carry the unbounded-SWE failure at Baker/Glacier Peak/Rainier as a **flag, not a correction** | M2.4 |
| **F1** | MTBS / NIFC fire perimeters | `burned_fraction_in_snow_band` (post-fire ROS melt 2.3× unburned) | annual | ~0 | public domain · $0 | M2.4 context |
| **A1** | ARTMIP Tier 1 catalogues (NCAR CDG, doi 10.5065/D6R78D1M) | the honest way to quantify **detector** uncertainty on historical events | one-time | ~0 | research use · $0 | M3.6, M6.1 |
| **X1** | CW3E AR-scale / NOAA PSL AR portal | — | — | — | **image only, research-use-only. DO NOT INGEST.** | — |

**Total new recurring ingest: ~20–30 MB/day** with the MRMS retention rule, against the current
~13.2 MB/day. Steady-state R2 stays inside the 10 GB free tier. **No new service and no new recurring
charge**, provided MRMS raw retention is capped at 14 days. That cap is the one explicit cost decision
in this plan.

**One CONFIGURED seed block the platform does not have and cannot build ladders without (R1):**
`homogeneity_epochs` per station — `(start, end, reason, source)` covering gauge datum epochs,
documented rating-revision epochs, station relocations, and **upstream operating-rule epochs** (Howard
Hanson 1961–62, Mud Mountain, Ross/Diablo/Gorge, Baker 1959, Chester Morse). Bounded work: ten gauges,
USGS station manuscripts and operator records. Until it exists, the platform is building ladders across
breaks it has not looked for.

---

## 5. Doctrine and contract changes this specification requires

**`HYDROLOGY.md`**
- §1: state determines the **gain** that converts forcing to discharge — measured at **7.6–11.1×**
  across the wet-season flow range — and most of what leaves was already there. "Reacts" understates a
  factor of ten. Add the regional qualification that the state term has small variance during the flood
  season here, with the Webb 2025 classification and the Cayuse Pass measurement.
- §2: add the three-elevation vocabulary (freezing level / atmospheric snow level / **mountainside snow
  line**); add `runoff_regime` (`mountain_subsurface` | `lowland_till` | `outwash` | `urban_impervious`)
  as a sibling of `regulation_class`; add `sediment_regime` (`volcanic_glaciated` |
  `glaciated_non_volcanic` | `non_glacial`); record the 39 % Skagit control fraction and that **Lower
  Baker has no authorised flood storage**; record that low-elevation tributaries below the flood-control
  dams can contribute **more than 50 %** of total flow.
- §5/§9: **a stage threshold has a discharge vintage.** Record the Mount Vernon numbers that justify the
  stage↔flow refusal (residual sd 0.68 ft, a 3.14 ft inversion, against 2 ft category spacing) and add
  the **rating epoch** as a fourth time alongside valid/issued/retrieved for slow variables.
- §7: rewrite the ROS bullet as regime-dependent (§1.1); add the **~30–45 mm** pack-buffer magnitude;
  add the **~19–45 %** snowmelt-fraction prior; add the hard outflow ceilings; add "a SNOTEL pillow that
  does not fall during ROS is not evidence of no outflow".
- §10: replace one flood-buffer definition with **three**; label the official forecast at regulated
  points as **conditional on an assumed operating plan**.
- §13 additions: no recurrence interval / return period / AEP for any reach; no AR category sourced from
  imagery; no modelling or forecasting of lahars, glacial outburst floods, landslide-dam outbursts or
  post-fire debris flows (display the responsible agency's product and link); no claim that a river
  stage forecast is complete at a tidally influenced point when the source model does not carry the
  coastal boundary condition.
- Add a **coastal section**: the TWL decomposition as the governing equation at tidally influenced
  points, and the per-point transmission coefficients.

**`DATA_DOCTRINE.md`**
- §2: name **HEFS explicitly on the MODELED row**; add that AR presence/category are DERIVED with
  detector parameters in `method_version`; add `configured_from_source_id` + required `retrieved_at` for
  a retrieved configuration (a rule curve is neither hand-entered nor measured).
- §5: add a **slow-variable staleness class** — a 2019 channel survey is not stale, it is the current
  best estimate of a decadal quantity, and the correct display is "as surveyed 2019".
- §6: add a **vertical-datum family** taxonomy naming tidal datums explicitly, with epoch, and marking
  the Puget Sound stations with no published NAVD88 tie as requiring VDatum.
- §9: distinguish **forecast probabilities** (authority-issued, time-stamped, verifiable) from
  **frequency estimates** (authority-issued, vintage-stamped, not verifiable at any operational lead) —
  §9(a) is currently too permissive and would admit a 1 % AEP quantile with a factor-1.66 CI as if it
  were an issued forecast probability. Add the **degeneracy clause**: a member fraction must be reported
  with the number of *distinct* member values.
- §11: require a pinned `product_version` / `model_version` on every row and treat a
  purged-before-archived cycle as a **recorded gap**, not an absence.
- §12: prohibit "100-year", "N-year flood", "return period" and "recurrence interval" in generated copy.

**`packages/contracts`**
- `DerivedFeature` / `SurfaceState.value`: the five climatology fields (M0.1) and `physical_ceiling`.
- `Driver`: must carry an **angular** quantity and a **duration**, and a **signed delta**; `BandTable`
  needs an interval (periodic) variant — the current shape assumes a monotone scalar.
- `Basin`: `runoff_regime`, `sediment_regime`, `cross_barrier_bearing_deg`, `bearing_window_deg`,
  `barrier_height_m`, `hypsometry_ref`.
- `ForecastPoint`: `tidal_class`, `tidal_transmission_ft_per_ft`, `rating_epoch`.
- `Regulation`: `control_fraction`, `uncontrolled_dominant_gauge` (Skagit → Sauk, USGS 12189500 — which
  `susceptibility.py` already reads for a different and correct reason).
- New `Reservoir` entity (none exists; the seed carries `reservoir:*` ids as opaque strings) with the
  fields in M5.1.
- `Station.station_kind`; `Threshold.datum_family` + `reference_datum`.
- `BasinVisualizationState` / `SceneSummary`: a **coastal sub-state** at TIDAL points, or UNKNOWN with a
  reason — rendering a delta scene with a flat blue sea and no tide state is a visual-truth violation of
  the same family as moving the snow line. **Sea level in Puget Sound moves 11 ft twice a day; a frozen
  shoreline is a fabricated certainty.** No field anywhere may carry a recurrence interval.
- Every AR category needs three extra provenance fields: the **reference point** (lat/lon), the **grid
  resolution**, and the **model run**. Without those, "AR 4" is not a value under §1.

---

## 6. What the corpus says is NOT worth building

| # | Not built | Reason, from the corpus |
|---|---|---|
| 1 | **A Cascade-computed flood frequency analysis, return period or AEP** | Bulletin 17C excludes regulated basins **by scope** (101/107 Concrete peaks and 85/86 Mount Vernon peaks carry USGS code 6); provides no evaluated mixed-population method and says so in its own text; the platform has no calibrated basis to deviate. Published 1 % AEP CIs in western WA span a factor of **~1.66**. **52 % of gauges have already recorded a peak above their own published 1 % AEP against a binomial expectation of 49 %** — the "100-year flood keeps happening" is arithmetic, not signal. Publish rank-in-record instead (M0.5). |
| 2 | **SMAP L4 as a susceptibility input** | Its own accuracy requirement **explicitly excludes snow, frozen ground and mountainous topography** — the Cascades in winter are outside the product's claimed validity envelope. Latency ~2.66 d against a state that moves 64 percentile points in 48 h. SMAP L4 ranked **4th of 6** DA products in the largest independent evaluation. The cost/benefit is poor and the failure mode is silent. |
| 3 | **SNOTEL soil moisture** | Permanently closed with evidence: **four of eight basins have zero SMS stations**; the Sauk — the gauge the Skagit surface reads — has none; MF Nooksack returned 51/123 days *all reading 0.0 %* and **nothing at all before 2025-12-12**, i.e. through the entire lead-up to the record Nooksack flood; Meadows Pass returned 0/123. |
| 4 | **A basin-scale forest-harvest / clearcut amplification term** | The plot-scale effect is real (+20–40 % on melt at a point) and **does not scale** to 500–3 000 mi² basins. Grant et al.: no detectable effect beyond ~6-year return periods; basin-scale effect smaller than interannual variability. And the statistical method is genuinely disputed (Alila et al.), so the honest reason is *unresolved method*. Record as CONFIGURED attributes; keep out of the hazard computation. |
| 5 | **Static orographic downscaling of QPF** ("basin QPF × elevation ratio", "NBM cell × PRISM ratio") | The Mountain Mapper failure mode reimplemented. S&B04's factor-of-5 warning applies to the DEM-based version, and upslope estimates have been measured *exceeding the incoming moisture flux*. |
| 6 | **Any "pre-event water fraction" or old/new-water claim** | The literature's spread is 0–100 %, it moves with wetness, intensity and land cover, and it is not measurable operationally here. |
| 7 | **Tide/surge as a term at Mount Vernon or Ferndale** | M2 amplitude **0.009 ft** at the Mount Vernon gauge; the USACE model and the 2013 hydrology document put the tidal limit **~7 river miles downstream**; a 30-winter daily backwater regression is null. Building a river-plus-tide joint model there would be solving the wrong problem. Wire it at SNAW1 only. |
| 8 | **Averaging any two sources into a consensus value** | Doctrine, and reinforced independently by five domains. Disagreement is the information. |
| 9 | **Ingesting CW3E AR-scale or NOAA PSL AR imagery** | Image-only, research-use-only, no data endpoint (re-confirmed 2026-08-24). A category read off a picture has no valid_time, issued_at, model identity or unit. |
| 10 | **A trend adjustment to the climatology ladder** | It would be an uncalibrated method, and the adjustment would be chasing a term **smaller than the noise at six of ten gauges**. Publish the vintage sensitivity as a disagreement driver instead. |
| 11 | **A snowpack trend from the platform's own SNOTEL feed** | No field-significant April-1 SWE trend across 28 western/crest WA sites 1979–2026 (field p = 0.156, correlation-aware null permits **7 of 28** "significant" sites by chance); and the network's temperature channel carries a documented **+1.7 °C Tmin sensor step** that propagates into PRISM and DAYMET. |
| 12 | **Lahar / GLOF / landslide-dam / post-fire debris-flow modelling** | An authority already owns each product (USGS volcano alert levels and post-fire assessments, WA DNR WALERT and the debris-flow dashboard, NWS flash-flood products). Display verbatim and link. Also: the USGS post-fire model is southern-California-calibrated, **degrades in western Oregon by USGS's own assessment**, and does not represent rain-on-snow at all. |
| 13 | **Anything derived from century-scale projections** | Fenced. See §7. |
| 14 | **"Damages prevented" figures** | HEC-FDA-class estimates dominated by assumed inventory, price level and levee-failure assumptions, not comparable across vintages, and advocacy-adjacent. MMD's own manual gives $308 M cumulative through FY1999 against a USACE release of $215 M for a single 2025 event. |
| 15 | **NWM AnA land soil moisture as an operational ingest** | Deferred, not refused. It is the single largest byte cost in the corpus, and the domain's own open question asks whether SOIL_M will simply track the flow percentile. Build the AORC SSPI first (M4.4a) and let M6.2 decide. |
| 16 | **Any stage↔flow conversion, ever** | ADR-0011, now with the numbers: rating 24.0 is **extrapolated above 125 000 cfs**; conveyance changed ~9–11 % in three decades; the residual scatter is 0.68 ft against 2 ft categories. |
| 17 | **An ensemble mean as a comparison value** | The repo already takes the lower-median *member*. Averaging members produces a hydrograph no member forecast. (Noted honestly: ensemble means are demonstrably *more consistent* than control runs, so the choice is defensible rather than uncontested.) |
| 18 | **A single regional or statewide sea-level rate** | Measured refutation: **the sign flips within the domain** (Neah Bay −1.70, Cherry Point −0.06, Seattle +2.09 mm yr⁻¹). Use the nearest gauge's measured trend with its CI, and say "no detectable trend" where the CI includes zero. |
| 19 | **A `mechanism` driver that is scored** | The PSCZ/AR/post-frontal label is displayed context, never a score — it has no calibrated relationship to outcome. |

---

## 7. Projections quarantined, and the two files affected

**The exclusion is the platform's own epistemics applied consistently, not a new editorial rule.** A
century-scale projection cannot carry an `available_at` knowledge time (`DATA_DOCTRINE.md` §11) so it
cannot participate in `as_known_at(T)`; it cannot be verified at 6–120 h lead so it cannot pass §9's
calibration requirement; and §2 puts a GCM→RCM→hydrologic-model chain at MODELED at best, which may not
enter a threshold, a percentile or a hazard computation.

**Files quarantined.**
1. **`docs/research/corpus/climate-change.md`** — already fenced by its own author into Appendix P, and
   the file was rebuilt around measurement for exactly this reason. **No further action needed; this is
   the model the other files should follow.**
2. **`docs/research/corpus/snow-hydrology.md` §3 and §4** — the rows sourced from Musselman et al.
   (2018) PGW under **RCP8.5** (+20 % to >100 % ROS water-available-for-runoff over the Cascades; top-10
   ROS events up to 3 months earlier), Hao et al. (2025) +5 K storyline (+44 % runoff for the 1996 PNW
   flood), and Maina & Kumar (2025). **Quarantine as NON-OPERATIONAL CONTEXT.** They cannot enter
   `snow-drought-state`, `pack-buffer-capacity` or any exposed fraction.
3. **`docs/research/corpus/atmospheric-rivers.md` §3 and §4** — Warner, Mass & Salathé (2015) CMIP5
   **RCP8.5** end-of-century rows (+11–18 % west-coast winter mean precipitation, +15–39 % on
   extreme-IVT days, up to **+290 %** in days above the historical 99th-percentile IVT) and Gershunov et
   al. (2019) LOCA "Real-5" rows; also Zhou, Wehner & Collins's projected cluster-density increase.
   **Quarantine.** The *measured* cluster results (120–140 % OR/WA intensity, **150–300 %** Cascade
   runoff) are admissible and are what M3.7 uses.
4. **`docs/research/corpus/compound-coastal.md` §3.6** — Miller et al. (2018) **RCP8.5** SLR rows
   (2.0 ft central 2100, 4.8 ft at 1 % exceedance, 8.3 ft at 0.1 %), Hamman et al. (2016) 2080s Skagit
   inundation rows, and Spicer et al.'s "+0.61 m SLR (AR6 **SSP5-8.5**, 2100) doubles the flooded area"
   row. **Quarantine as planning context.** What is admissible and operational is the *measured* CO-OPS
   relative-sea-level trend per station with its CI (§2.7 of climate-change; M5.2).
5. **`docs/research/corpus/regulation-operations.md`** — carries no projections of its own; CW3E's FIRO
   framing numbers are historical.

**Hausfather & Peters (2020, *Nature*) flag required on all of the above.** RCP8.5 and SSP5-8.5 are
routinely described as "business as usual"; Hausfather & Peters show they are **implausible as
baselines**, tracking a high-end coal-intensive pathway rather than a central expectation. Every
quarantined row must carry that flag **and the lower-scenario result alongside**, wherever the source
reports one. Where a source reports **only** the high scenario — Musselman et al. (2018) PGW,
Gershunov et al. (2019), Spicer et al.'s single SSP5-8.5 case — that absence is itself the caveat and
must be stated: *the cited number is a high-end-scenario result with no lower-scenario companion in the
source.*

**What is admissible from the same neighbourhood, and is elevated rather than fenced.**
- **MEASUREMENT.** Observed AR **IVT change 1980–2023 is <+1 %** (AR-mean; +3–4 % for the most intense
  subset), with 850-hPa wind and vertically-integrated moisture-flux convergence both **decreasing** —
  and the authors' own caution that reanalysis assimilation changes may affect the trends. Observed
  centre-of-timing shifts of **−2.3 to −4.6 days per decade** at the five snow-influenced gauges and
  **not** at the rain-dominated lowland gauges — the physically expected pattern, and evidence the
  signal is not an artefact. Observed local RSL per station with CIs.
- **PHYSICS.** Clausius–Clapeyron at **~7 % K⁻¹** for saturation vapour pressure is a constraint on
  **moisture and only on moisture**. Precipitation is `P ≈ w·q·ε` and only `q` is CC-constrained; `w` is
  dynamic. Observations depart in **both** directions — apparent super-CC hourly scaling is explained as
  a stratiform→convective **rain-type mixing artefact** in the one dataset that decomposed it, and does
  not transfer to a stratiform orographic regime anyway. **Importing a "7 % per degree" or "14 % per
  degree" factor into a western Washington design storm or threshold is unsupported in both
  directions.**
- **OBSERVING-NETWORK ARTEFACTS masquerading as trends** — elevated to first-class, because these
  directly corrupt a predictor: the **41.26 ft** datum step at Snoqualmie near Carnation (a platform
  susceptibility gauge) between WY1939 and WY1940; the **+1.7 °C Tmin / −0.5 °C Tmax** SNOTEL sensor
  step propagating into PRISM and DAYMET; **44 % of 748 SNOTEL stations** reporting at least one year
  with max SWE *greater than* accumulated precipitation (physically impossible); gauge undercatch of
  **25–40 % above 1 500 m**; and the **NWM v3.0 → v3.1 model-version boundary on 2026-08-18**, which is
  a system non-stationarity every hindcast must respect.

---

## 8. What to build first

If only three things are built, build these.

1. **Tier 0 in full (M0.1–M0.5).** It removes false precision from surfaces already on screen, it costs
   nothing, and it fixes the specific failure that would have shown MODERATE-everywhere on the day of
   Event Zero's Flood Watch. **This is the only work in the plan that reduces the platform's exposure
   rather than increasing it.**
2. **M2.1 basin hypsometry, then M3.1 + M3.2 upslope IVT.** Hypsometry is a one-time compute that
   unblocks four domains. Upslope IVT is the only atmospheric quantity with published
   variance-explained numbers against *runoff*, and it is the feature that tells the Green apart from
   the Snoqualmie in the same storm.
3. **M4.1 HEFS ingest.** 45 authoritative members, six seed points, 30-day horizon, **~1.3 MB/day**,
   and an archive that disappears in ten days if nobody stores it. Nothing else in this document has
   that ratio of value to cost.

The fourth, if there is room: **M1.1 catchment sensitivity** — no new data, a peer-reviewed method with
a stated failure mode, and the first derived quantity in the platform that can carry a numeric quality
measure without violating the confidence doctrine.
