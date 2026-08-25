# docs/research/corpus — the flood-science corpus

One job: hold the *domain science* behind `HYDROLOGY.md` and `DATA_DOCTRINE.md` at a depth no
doctrine file should carry. Twelve domains, one file each, written 2026-08-24 as domain-lead passes
deepening `../flood-genesis-mechanisms-2026-08-24.md`. Each file has the same nine sections:
headline, mechanisms, quantitative anchors, settled/emerging/contested, western-Washington
specificity, what it means for the platform, what it contradicts in current repo doctrine, open
questions, sources.

**The test of relevance is a 6–120 hour flood forecast for a named western Washington basin.**
Everything in these files is here because it changes that forecast, or changes a number the forecast
is compared against. Three things are held apart and must never blur:

| | Admissible? |
|---|---|
| **MEASUREMENT** — observed trends in instrument records | yes, and preferred |
| **PHYSICS** — e.g. Clausius–Clapeyron ~7 % K⁻¹ | yes, as a constraint; precipitation and flood response are not required to follow it |
| **PROJECTION** — GCM/RCM-driven futures | **no.** Fenced context only |

The projection exclusion is the repository's existing epistemics applied consistently, not a new
editorial rule: a century-scale projection carries no knowledge time (`DATA_DOCTRINE.md` §11) so it
cannot participate in `as_known_at(T)`, and it cannot be verified at operational lead time (§9).
`climate-change.md` is the model for how to handle it — all projection material sits behind a fence
in its Appendix P, with scenario, ensemble and compounded uncertainty attached to every number and
the Hausfather & Peters (2020) critique applied to every RCP8.5 result. **Three files still need that
treatment applied** — see *Projection quarantine* below.

**Facts decay.** Re-verify before relying on anything older than a quarter. In this corpus that
applies with unusual force in three places: agency endpoints move (USGS legacy IV is decommissioned,
`waterdata.usgs.gov/nwis/measurements` now redirects), operational models version (NWM went 3.0 → 3.1
on 2026-08-18, mid-corpus), and standards are mid-replacement (NOAA Atlas 15 Vol. 1 preliminary
September 2026 replaces Washington's 1973 Atlas 2). A number in these files is a reading taken on a
date, not a property of a river.

| File | What it holds | Independently verified? | The one finding to carry |
|---|---|---|---|
| `runoff-generation.md` | Hillslope runoff generation, the old-water paradox, fill-and-spill thresholds, Kirchner storage–discharge, transit times, hillslope→basin scaling; original `g(Q)` fits for 7 Cascadia gauges | yes — 17 papers fetched per claim; an adversarial re-implementation found the stated exit test **not reproducible** (b = 1.69–1.92, not 1.85–2.05), the r² inflated by binning (0.74–0.80 unbinned), and one anchor row unattributable | The wet-season dynamic store is only **71–104 mm** — one to two days of AR rain — so antecedent state is a measured **7.6–11.1× gain** on the marginal millimetre, and *not* a predictor of peak magnitude (r² = 0.001–0.057 across the top-25 peaks at four unregulated gauges) |
| `snow-hydrology.md` | Snowpack energy balance, cold content, preferential flow, ROS melt partitioning, phase interference, canopy, snow line vs freezing level, snow drought | partial — one arithmetic error found and corrected in place (the liquid-water buffer was understated ~3×); the satellite SWE/SCA sub-topic was never swept (search budget exhausted) and is flagged as the largest unexamined gap | The pack is a **small, leaky buffer, not a reservoir**: ~30–45 mm of combined cold-content and liquid storage against a 200–400 mm AR, with outflow hard-capped below 10 mm h⁻¹ and never above 14. On 2025-12-11 the sub-4,500 ft SNOTEL sites read **14 % of median SWE** while the all-station composite read 44 % |
| `atmospheric-rivers.md` | IVT vs IWV, ARTMIP detector uncertainty, vertical and horizontal structure, the Ralph 2019 scale and its stated limits, duration, mesoscale frontal waves, families and cluster density, landfall latitude | **not re-checked** — no adversarial pass ran on this file. Several load-bearing numbers (Ralph et al. 2017 width and TIVT, Konrad & Dettinger 2017, Corringham et al. 2019) are abstract-only and labelled as such | The AR is the **necessary cause and a poor sufficient one**. What separates a flood AR from an ordinary one is a five-term conjunction — orientation, strength, stationarity, melting level, antecedent wetness — of which magnitude is one, and `forcing.py` carries none of the other four |
| `orographic-precipitation.md` | The upslope model, IVT⊥, Smith & Barstad linear theory, Froude blocking, seeder–feeder, spillover and drying ratios, the Puget Sound Convergence Zone, QPE and QPF error structure | not re-checked externally — but the file performs its own citation forensics, correcting three mis-citations *inside its fetched sources* (Rotunno & Houze 2007 mis-ordered and mis-dated by Minder & Roe; Hobbs 1973 vs 1975; Marwitz 1981 vs 1987) and re-reads Neiman et al. 2002 to correct a figure in a repo research file | Orographic precipitation is a **transfer function, not an amplifier**, and its operative scalar is IVT projected onto *each basin's own* terrain gradient. Over the Olympics in unblocked warm sectors that relation is r² = 0.85, slope 0.014 mm h⁻¹ per kg m⁻¹ s⁻¹ — a genuinely local, genuinely quantitative result |
| `antecedent-conditions.md` | Storage deficit as the state variable, streamflow as a storage proxy, API/SPI/SSPI/SMA proxy ranking, maritime winter pinning, the extremeness threshold, how NWRFC and NWM represent state | yes — an adversarial pass re-fetched Webb et al. 2025 in full and **reversed the entry's central claim** from "no effect in Washington" to "2× — Washington's own end of the published 2–4.5× range, precipitation-controlled" | Replaying Event Zero, `susceptibility@0.1.0` would have read **LOW in four of six basins on 3–4 December and MODERATE in all six on 5 December** — the day of the first Flood Watch. The signal was never in the level; it was in the derivative (the Sauk moved 64 percentile points in 48 h) |
| `routing-hydraulics.md` | Saint-Venant wave hierarchy, Kleitz–Seddon celerity, attenuation, looped ratings, USGS shift practice, backwater and conveyance loss; measured routing and rating drift on the lower Skagit | yes — adversarial pass, six corrections in place: two mis-dated USACE passages, a "robustness check" that was algebraically vacuous, an internally inconsistent celerity, and an unstable harmonic fit | The Mount Vernon conveyance drift is **real and about a third of what the repo asserts**: −9 to −11 % at flood stage since the late 1980s, not −29 %, driven by bed aggradation in a levee-confined sand-bed reach — **not** by the tide, which is refuted at the gauge (M2 ≈ 0.004–0.009 ft; tidal limit ~7 river miles downstream) |
| `compound-coastal.md` | Compound-event typology, total-water-level decomposition and its nonlinear terms, skew surge vs non-tidal residual, Puget Sound surge sources, vertical land motion, co-seismic subsidence, the CO-OPS/NWPS station inventory | **strongest in the corpus** — §3.1–3.5 independently re-run and reproduce to 3 dp; every literature citation checked against Crossref/DataCite and **all exist exactly as described, no fabrication**; six numeric errors found and corrected, one finding (a "stale" gauge) fully refuted as an array-ordering mistake | The dependence is real here (ρ = +0.30 to +0.39 with Seattle skew surge at −1 day) **and Event Zero sampled the benign corner**: all three record crests landed 4.8–6.6 ft *below* MHHW. The compound tail is unrealised and therefore invisible in the platform's calibration set |
| `flood-statistics.md` | Bulletin 17C, LP3/EMA/MGBT/regional skew, mixed populations, the regulated exclusion, non-stationarity detection vs modelling, the Atlas 14 → 15 transition | yes — an independent re-parse reproduces the substance (95 % CI factor ~1.6–2.0 at 1 % AEP; observed exceedance ≈ binomial expectation) but **not** the gauge count (76 vs 69) or the quoted 1.66; both are flagged unconfirmed in place | **Refuse the return-period object.** 17C excludes regulated watersheds by scope, has no evaluated mixed-population method by its own admission, and NWPS publishes no recurrence field at any seed point. Rank-in-record is the honest substitute — and 52 % of western WA gauges already exceed their own 1 % AEP against a binomial expectation of 49 % |
| `regulation-operations.md` | Rule curves as risk allocation, control fraction, objective flow and travel time, the discharge regulation schedule, evacuation, Section 7 authority, FIRO; December 2025 recomputed from primary series | yes — an adversarial pass **reversed a headline data-availability finding** (CWMS `/levels` serves the full seasonal rule curve; the file had said `total: 0`), corrected an author list, and revised the Ross pool fraction | A reservoir converts a **bounded fraction** of the basin into a decision — 39 % of the area at Mount Vernon, 55 % at Auburn, 42 % at Puyallup — and effectiveness is a **hump**: 0 % at the 2-year event, 17.8 % at the 25-year, 10.8 % at the 500-year. Buffer must be three signed volumes, never one |
| `climate-change.md` | Measured non-stationarity that corrupts the platform's own reference distributions: percentile sampling error, the variance–bias curve, the p95 clamp, seasonal-shape drift, local relative sea level, Clausius–Clapeyron discipline. Projections fenced in Appendix P | yes — the adversarial pass found §2.3's central evidence **circular by construction**, re-tested it out-of-sample (the rule survives, the stated evidence does not), cut a §2.6 inference by an order of magnitude, and flagged the table's header row as regulation rather than climate | The dominant corruption of the day-of-year ladder is **not climate drift, it is estimation variance**: 12.8–17.4 % of daily observations change susceptibility band from ladder *length* alone, with the trend removed by construction. A regulation-epoch split moves more (29–32 %) than either |
| `forecasting-verification.md` | The NWRFC chain and why the official forecast is not reproducible, ESP → MEFP → HEFS, NWM v3.1, Brier/CRPS/reliability/ROC/SEDI/relative economic value, forecast evolution and jumpiness, hindcast design | yes — a review pass found the base-rate method **wrong in kind** (daily means cannot verify an instantaneously-defined threshold) and corrected six further claims, including two study-version and two transferability errors | **Buy the official probability before building one**: HEFS is live and machine-readable at all six seed LIDs, 45 members, 30 days. But at four of six points the NWS category is in *stage* and HEFS serves *flow* only, so the exceedance probability is not computable and ADR-0011 forbids bridging it |
| `cascading-hazards.md` | Paraglacial sediment supply, bed waves and celerity, conveyance, lahars, jökulhlaups, debris-flow initiation, post-fire hydrology, landslide dams, large wood, forest harvest and roads, urbanisation | **partial — the headline number does not reproduce.** The Ferndale conveyance drift is **+0.065 ft/decade (p = 0.028)** under the estimator the method text names, not the tabulated +0.139 / p = 0.0001, which is an OLS fit mislabelled as Theil–Sen. Two further rows likewise unverified | Geomorphic processes do not make these floods; they change **what a given flood does**, and slowly enough that the platform's *thresholds* drift while its *physics* does not. A stage threshold is a statement about a channel that had a date |

## Cross-domain synthesis

What only becomes visible when the twelve are read together — six convergent findings, eleven
contradictions needing adjudication, the forcing-to-stage causal chain assembled end to end with its
weakest links named, and the factors ranked by how much they actually move flood outcome — is in
[`CROSS-DOMAIN-FINDINGS.md`](CROSS-DOMAIN-FINDINGS.md).

## How to read a claim

Labels follow `DATA_DOCTRINE.md`: **FACT** = read on a page or dataset the author fetched in that
pass (URL given), or computed there from a fetched primary dataset; **INFERENCE** = reasoned from
cited facts; **ASSUMPTION** = a working simplification; **OPEN QUESTION** = unresolved. A number a
source could not be opened for is marked *not independently fetched* and demoted to INFERENCE. Every
file's §9 splits its sources into fetched-and-read versus cited-but-blocked, and names the paywall or
403 that blocked it.

Nine of the twelve files carry original computations against live USGS, NOAA CO-OPS, NRCS AWDB, USACE
or NWPS endpoints, with the query reproduced so it can be re-run. Those are the corpus's most durable
content and its most fragile: they are FACT-grade in that the data were fetched, and INFERENCE-grade
in everything the author did to them afterwards. Two of them did not survive re-execution
(`cascading-hazards.md` §5.4, `runoff-generation.md` §5.4) and say so in place.

## Projection quarantine

Applied consistently, the exclusion above means a projection may not sit unmarked in the same table
as a measurement. `climate-change.md` complies fully. Three files do not, and their projection
material should be fenced before any of it is quoted:

- **`atmospheric-rivers.md`** — the last three rows of the §3 anchor table (Warner, Mass & Salathé
  2015's "+290 % days above the historical 99th-percentile IVT"; Gershunov et al. 2019) are CMIP5
  RCP8.5 results sitting beside measured IVT return periods with no scenario flag and no Hausfather &
  Peters caveat. §4 contested items 3–4 and open question 10 are projection disputes.
- **`snow-hydrology.md`** — three §3 anchor rows are RCP8.5 pseudo-global-warming or storyline
  results (Musselman et al. 2018's "+20 % to >100 %" Cascade ROS runoff; Hao et al. 2025's "+44 % at
  +5 K"; the "3 months earlier" timing shift), and §4 contested item 4 is entirely a projection
  argument. The scenario is named for Musselman but is not flagged as single-scenario.
- **`compound-coastal.md`** — §3.6 carries RCP8.5 sea-level-rise projections (Miller et al. 2018;
  Hamman et al. 2016's Skagit 2080s figures; Spicer's +0.61 m case) unmarked in the anchor table. The
  file's own §6.3 already applies the correct fence in prose — *"treat as CONFIGURED context, never as
  an input to a hazard computation"* — so this is a table-marking gap, not a doctrinal one.

`orographic-precipitation.md` §4 carries two model-derived non-stationarity results (Kirshbaum &
Smith 2008; Minder et al. 2011) but labels both as model results in place; no action needed.
`flood-statistics.md` describes NOAA Atlas 15 Volume 2's projection method and explicitly recommends
against ingesting it. The remaining six files contain no projection material.

## Human check

Before a claim from this corpus enters `HYDROLOGY.md`, `DATA_SOURCES.md` or a method docstring: open
the file's §7 (*what this contradicts in current repo doctrine*) to see whether the claim is already
recorded as a correction; check §9 to see whether the source was fetched or blocked; and if the claim
is an original computation, re-run it. Two of nine did not reproduce. Record the date in the ADR or
the method note.
