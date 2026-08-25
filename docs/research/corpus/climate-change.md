# Climate change: forcing intensification and PNW hydrologic response

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

*Labels follow the repository convention: **FACT** = read on a page I fetched, or computed by me from a
primary dataset I fetched (URL and command given); **INFERENCE** = reasoned from cited facts, not itself
read anywhere; **ASSUMPTION** = a working simplification; **OPEN QUESTION** = unresolved. Where a paywall
or a bot wall blocked me, the claim is marked "not independently fetched" and demoted to INFERENCE.
Consensus is marked **established / emerging / contested** per claim. Nothing in the repository was
modified except this file.*

---

## 1. Headline

**Warming has already moved the two quantities Cascadia Papsukkal ranks values against — the forcing
distribution and the climatological reference distribution — and it moves them by amounts comparable to
the platform's own decision bands, so the load-bearing change is not "add a climate factor to the hazard"
but "make every percentile, threshold and normal carry a *vintage* and refuse to compare across
vintages."** The physics is a floor, not a ceiling: atmospheric moisture rises ~7 % K⁻¹ by
Clausius–Clapeyron, western Washington's flood response amplifies that (basin peak flow is projected
+11 % at the 1.5 °C global warming level and +24 % at 4 °C, against +20 % in the 2-year storm and +22 %
in the 25-year storm), and the amplification runs through *hypsometry* — a rising snow level converts
basin area from snow-storing to rain-exposed, which is a step change in contributing area, not a linear
scaling. Meanwhile the reference distribution the platform ranks against is itself non-stationary and
strongly modulated by the PDO: on the unregulated Sauk, the *same* observed August flow ranks at the 50th
percentile against the full period of record, the 68th against 2006–2025, and the 26th against 1946–1965
(computed here from USGS daily values). That 42-percentile spread is larger than the width of two of the
platform's four susceptibility bands.

---

## 2. Mechanisms (the physics, stated properly)

### 2.1 Clausius–Clapeyron is the thermodynamic floor, and it applies to *moisture*, not to *rain*

The Clausius–Clapeyron relation gives the temperature dependence of saturation vapour pressure over
liquid water:

```
d(ln e_s)/dT = L_v / (R_v T²)
```

with `L_v ≈ 2.5 × 10⁶ J kg⁻¹` and `R_v = 461.5 J kg⁻¹ K⁻¹`. At `T ≈ 288 K` this evaluates to
**≈ 6.5–7 % K⁻¹**, and under the (well-supported) assumption of roughly constant relative humidity over
the ocean, column water vapour scales at the same rate (FACT, textbook thermodynamics; the 7 % K⁻¹ figure
is restated in the Yakima County BAS compilation as `dq/dT ≈ 0.07 q` — [Yakima County BAS addendum,
17 Dec 2025](https://www.yakimacounty.us/DocumentCenter/View/43010/Clausius_Clapeyron_Atmospheric_Rivers_BAS_Research_DRAFT-12172025-ksw), fetched). **Established.**

Precipitation is not vapour. Precipitation intensity `P` at a point scales approximately as

```
P ≈ w · q · (precipitation efficiency)
```

— vertical mass flux times specific humidity times efficiency. Only the `q` term is CC-constrained. The
`w` term is *dynamic* and is the dominant source of projection uncertainty (INFERENCE from the
thermodynamic/dynamic decomposition in [Payne et al. 2020, *Nat Rev Earth Environ*](https://doi.org/10.1038/s43017-020-0030-5), abstract fetched via
[EESM](https://eesm.science.energy.gov/publications/responses-and-impacts-atmospheric-rivers-climate-change);
the full review is paywalled and was **not independently fetched**). **Established as a framing.**

### 2.2 Super-CC scaling is largely a rain-type mixing artefact, not convective invigoration

Observed hourly precipitation extremes frequently scale at **~2× CC (≈14 % K⁻¹)** against dew-point
temperature. The competing explanations were (1) genuine thermodynamic invigoration of convection and
(2) a statistical shift of the sample from weak stratiform to intense convective rain as it warms.
Using 514 German stations at 10-minute resolution (2005–2020) paired with EUCLID lightning data,
[Dallan et al. 2025, *Nature Geoscience*](https://pmc.ncbi.nlm.nih.gov/articles/PMC12074990/) (fetched)
show that **stratiform and convective extremes each scale at approximately the CC rate in isolation**,
while the convective fraction increases at **β ≈ 41 % °C⁻¹**, and the mixing of the two alone reproduces
the apparent near-2-CC scaling. Explanation (1) is refuted for that dataset. **Emerging → established.**

**Transferability to western Washington: poor for the mechanism, useful for the caution.** Western
Washington's extreme-flood-producing precipitation is *not* convective. The repository's own prior pass
already establishes that the largest western-Cascades floods ran at hourly intensities of only
**2.7 ± 0.9 mm h⁻¹** — long, moderate, stratiform, orographically forced
(`docs/research/flood-genesis-mechanisms-2026-08-24.md` §2.4). The operational consequence is the
*opposite* of the headline: because our extremes are stratiform, **super-CC hourly scaling from convective
regions should not be imported into a western Washington design storm**, and the honest local prior is
CC-to-modestly-above-CC for storm-total intensity, with the amplification coming from *duration and area*,
not from rain rate. (INFERENCE. **Contested** — see §4.)

### 2.3 Thermodynamic vs dynamic decomposition of atmospheric-river change

ARs are the forcing agent for essentially all extreme western Washington floods (repo doctrine
`HYDROLOGY.md` §2, verified in the prior pass). Their response to warming decomposes as:

```
IVT  =  (1/g) ∫ q · |V| dp        →     δIVT/IVT  ≈  δq/q  +  δ|V|/|V|
                                              (thermo, ~CC)   (dynamic, uncertain sign)
```

The thermodynamic term is robust and positive. The dynamic term — jet position, storm-track latitude,
blocking frequency — is not. This is why AR *moisture* projections are far more confident than AR
*frequency* or *landfall latitude* projections (INFERENCE from Payne et al. 2020 framing;
**established** as a framing).

Observationally, the decomposition is already visible.
[Henny & Kim 2025, *J. Climate* 38(6)](https://cawaterlibrary.net/wp-content/uploads/2025/04/clim-JCLI-D-24-0234.1-1.pdf)
(abstract page fetched) find, across ARTMIP Tier-2 detection tools applied to ERA5, MERRA-2 and JRA-55
over 1980–2019/2023:

- total AR **area +6 % to +9 %**;
- AR **IWV +1.5 % to +2.5 %**;
- AR **IVT < +1 %**;
- 850-hPa wind speed and vertically integrated moisture-flux convergence both **decreased**;
- restricted to the most intense AR grid points: **IVT +3–4 %, IWV +4–6 %, VIMFC +6–10 %**;
- for individual ARs, **maximum IVT and IWV increased at ~3–6× and ~1.5–2× the rate of AR-mean values**.

Verbatim caution from the same abstract: *"further research is required to determine the extent to which
these trends are affected by reanalysis observational assimilation changes."* **FACT for the numbers;
emerging for the attribution.**

The structural reading: **ARs are moistening and spreading, the wind is not strengthening, and the extremes
are moving faster than the means.** For a platform that badges *AR scale* (an IVT-magnitude-and-duration
rating), this says the AR-scale distribution shifts less than the precipitation distribution does, and that
the mean of the AR population is the wrong statistic to watch (INFERENCE).

### 2.4 Orographic transfer amplifies the thermodynamic signal in the mountains

The upslope model — `P ∝ (terrain-parallel wind) × (column moisture)` — makes windward precipitation
first-order proportional to the *product* of the two IVT terms rather than to IVT itself
(`flood-genesis-mechanisms-2026-08-24.md` §2.2, which cites 58–88 % and 74 % of rain-rate variance
explained). If wind is roughly unchanged and moisture rises at CC, windward precipitation rises at
roughly CC, but the *saturated* portion of the profile deepens, so condensation over the barrier can
exceed the column-integrated moisture increase (INFERENCE; **contested** in magnitude).

The Washington-specific projections are consistent with a mountain amplification: the state's own
assessment finds *"The greatest increases are over the northeast Olympics, northwest Cascades, Okanogan
mountains, and the east Cascade foothills"* for 25-year-storm magnitude
([WA Dept. of Ecology Pub. 25-14-064, Aug 2025](https://apps.ecology.wa.gov/publications/documents/2514064.pdf),
PDF fetched, p. 60). **FACT.**

### 2.5 Snow-level rise is a hypsometric step function, not a smooth scaling

This is the mechanism that makes PNW flood response *non-linear* in temperature and is the single most
platform-relevant piece of physics in this domain.

```
rain-exposed area  A_rain(t)  =  ∫_0^{z_snow(t)} a(z) dz          (a(z) = basin hypsometry)
effective runoff-contributing area ≈ A_rain + (melting fraction of A_snow)
```

Because `a(z)` in Cascade basins is strongly peaked in the mid-elevations, `dA_rain/dz_snow` is *large*
exactly in the 1,000–4,000 ft transient band. A given warming raises `z_snow` by roughly
`ΔT / Γ` with an environmental lapse rate `Γ ≈ 4.5–6.5 °C km⁻¹` — i.e. **~150–220 m per °C** — and the
Skagit report's own hypsometric framing of this is *"warmer climate causes higher freezing levels and
increased effective basin areas … which, coupled with increasing cool-season precipitation, dramatically
increases flood risk even for the relatively small temperature increases projected for the 2020s"*
([Lee & Hamlet 2011, Skagit River Basin Climate Science Report](https://www.skagitcounty.net/EnvisionSkagit/Documents/ClimateChange/Complete.pdf),
PDF fetched, ch. 5). **FACT for the quote; established for the mechanism.**

A corroborating elevation number: for the Cascades a **1 °C warming moves the snowline from ~600 m to
~750 m** with a ~12 % loss of mean April 1 SWE (search-summary attribution to Casola et al.; the primary
paper was **not independently fetched** — INFERENCE, treat the 150 m °C⁻¹ as order-of-magnitude only).

### 2.6 Rain-on-snow migrates upward; the increase is rain, not melt

[Musselman et al. 2018, *Nature Climate Change* 8, 808–812](https://bpb-us-w2.wpmucdn.com/sites.coecis.cornell.edu/dist/f/423/files/2021/09/musselman18natcc.pdf)
(PDF fetched and text-extracted) simulate ROS with flood-generating potential over western North America
with WRF at **4 km**, historical 2000–2013 vs a pseudo-global-warming RCP8.5 end-of-century forcing
(19-model mean deltas). ROS is defined as **rainfall ≥ 10 mm d⁻¹ on SWE ≥ 10 mm where snowmelt is ≥ 20 %
of rain + melt**. Verbatim results:

- *"In the warmer climate, we show that ROS becomes less frequent at lower elevations due to snowpack
  declines, particularly in warmer areas (for example, the Pacific maritime region). By contrast, at
  higher elevations where seasonal snowcover persists, ROS becomes more frequent due to a shift from
  snowfall to rain."*
- *"the water available for runoff increases for 55 % of western North American river basins, with
  corresponding increases in flood risk of 20–200 %"*.
- *"In 58 of the 106 major river basins (55 %) … average event runoff increased by > 20 %. In 20 of the
  basins, or ~17 % of western North America, ROS runoff increased by > 100 %."*
- **For the Cascades specifically**: *"basin event runoff volumes increase by 20 % to > 100 % for the
  Cascade Mountains, the northern Sierra Nevada, interior British Columbia and the Canadian Rockies, and
  by > 200 % for central and southern Sierra Nevada basins and the Colorado River headwaters."*
- The driver is rain: *"the change … is largely explained by increases in rainfall during ROS events …
  rather than increases in snowmelt intensity."*
- Historical snowmelt contribution to total ROS runoff is **lowest in the maritime regions (30 %–45 %)**
  and highest in the Rockies (45 % to > 65 %).
- *"increases in total ROS runoff volume are associated with increases in the spatial extent of ROS
  events, which are explained by an upward expansion of ROS to include higher elevations."*
- Little ROS frequency change above **2,500 m a.s.l.**

**FACT. Established.** The mechanism is exactly §2.5: the ROS *band* translates upslope, so a fixed
elevation band is the wrong coordinate and the fraction-of-basin coordinate is the right one.

Two caveats that matter here. (a) *"the results shown in Fig. 4 do not include rainfall on snow-free
ground"* — so the Musselman ROS decline at low elevations is **not** a decline in flood risk there; it is
a change of category from ROS to plain rain-on-saturated-ground, with rain intensity separately rising.
(b) The maritime 30–45 % melt contribution means that in western Washington the ROS *melt* term was never
the dominant term to begin with — consistent with `HYDROLOGY.md` §7 and with Marks et al.'s 60–90 %
turbulent-flux share of the *melt energy* (a share of a minority term).

### 2.7 Flood change ≠ precipitation change: four competing terms

Precipitation extremes rising does not imply flood extremes rising by the same amount, or at all. The
literature identifies four terms with different signs:

1. **Antecedent moisture.** Only **36 %** of extreme precipitation events in the CONUS produce an extreme
   discharge; conditioned on a wet catchment this rises to **62 %**, and on a dry catchment falls to
   **13 %** ([Sharma, Wasko & Lettenmaier 2018, *WRR* 54, 8545–8551](https://doi.org/10.1029/2018WR023749);
   **not independently fetched** — search summary only, INFERENCE). Warming that dries soils in the
   shoulder seasons therefore *offsets* rainfall intensification. **Established** as a mechanism.
2. **Snowmelt loss.** Declining snowmelt removes a flood-generating mechanism in snow-dominant basins,
   which is why some basins can see flood risk fall from warming alone (Hamlet et al. 2007, as cited in
   the Skagit report — FACT for the citation chain).
3. **Contributing-area gain** (§2.5) — the term that dominates in transient basins.
4. **Storm duration and simultaneity** — western Washington's extremes are duration-driven, so a change
   in AR *duration* or in AR-family sequencing changes flood peaks more than a change in rain rate does
   (INFERENCE from `flood-genesis-mechanisms-2026-08-24.md` §2.4, §2.6).

The regional resolution of these four terms is the key quantitative result of
[Chegwidden et al. 2020, *ERL* 15, 094048](https://iopscience.iop.org/article/10.1088/1748-9326/ab986f)
(HTML fetched): 21 northwestern-US headwater basins, 10 GCMs × 4 hydrologic models (3 VIC variants +
PRMS) × RCP4.5/8.5, 1950–2099. Verbatim:

- *"precipitation-driven AMFs show the largest increases in flow magnitude, ranging between 29 % and
  36 %"*;
- *"ROS-driven AMFs show the smallest changes in magnitude (between −9 and +10 %)"*;
- snowmelt-driven AMFs: *"in the transition and montane regions we see average increases of 12 % in
  magnitude, in temperate regions, AMFs increase by 33 %"*;
- mechanism shift, temperate basins: *"AMFs in temperate basins were mostly precipitation driven, with
  about 25 % caused either by snowmelt or rain-on-snow"* historically; *"By the 2080s under RCP 8.5,
  ROS-driven AMFs nearly disappear and snowmelt-driven AMFs account for only about 5 %"*;
- mechanism shift, transition basins: *"precipitation is responsible for only 13 % of AMFs but by the end
  of the 21st century it is responsible for 50 % of AMFs"*;
- elasticity: *"flood magnitude scaling between 1 % and 2 % increases for every 1 % increase in annual
  precipitation"*.

**FACT. Established.** Two operational readings: **(i) flood elasticity to precipitation is > 1 in these
basins**, so the flood signal is amplified relative to the precipitation signal; **(ii) rain-on-snow is a
shrinking share of the annual-maximum population in western Washington**, not a growing one — the growth
in ROS *severity* found by Musselman coexists with a decline in ROS *prevalence among annual maxima*.

### 2.8 Snow drought has two mechanisms with opposite flood signs

Harpold et al.'s dry/warm split is already in the repository's prior pass. What climate change does to it
is the new content: warming converts *dry* snow drought (a precipitation deficit, lowers the whole
hydrograph) into *warm* snow drought (normal precipitation delivered as rain, which is a **flood-relevant**
state). WY2026 is the local proof case: Oct–Feb precipitation **104 % of normal**, statewide snowpack
**~50 % of normal**, and the same water year contained the December 2025 record floods *and* an April 2026
statewide drought declaration (FACT — WA Ecology, cited in `flood-genesis-mechanisms-2026-08-24.md` §4.6).

Attribution now exists for that water year:
[Marshall, Cowherd, Rahimi & Ye 2026, *PNAS*](https://www.pnas.org/doi/10.1073/pnas.2612961123) find the
2026 western-US snow drought was **≈ 4.4× more likely** in the current climate than pre-industrial
(**95 % CI 2.6–9.4×**), and **≈ 14×** in the Upper Colorado; the reported physical cause is that
*"unusually warm temperatures caused much of the precipitation to fall as rain rather than snow and
accelerated snowmelt"*, with ≈ **40 km³** of "missing" snow attributed to climate change across the
western US. The PNAS paper itself is bot-walled; these numbers come from the search result and the
[Colorado School of Mines release](https://www.minesnewsroom.com/news/climate-change-made-years-snow-drought-western-us-four-times-more-likely-new-colorado-school)
(fetched). **FACT for the release; the primary paper was not independently fetched. No separate Pacific
Northwest / Cascades attribution factor is published in the release — treat the 4.4× as western-US-wide.**
See also the companion commentary, Swain 2026, *PNAS*, "Strong human fingerprint on low snowpack amid
increasing volatility" (**not independently fetched**).

### 2.9 The reference distribution is itself non-stationary — and decadal variability is as large as the trend

This is the mechanism with the sharpest consequences for this codebase, and I measured it directly rather
than citing it.

**Method.** USGS daily mean discharge, Sauk River near Sauk (12189500, unregulated, WY1929–2026, 35,663
daily values), fetched from `https://waterservices.usgs.gov/nwis/dv/`. Day-of-year ladders were rebuilt
with the platform's own convention — ±2-day window, R-type-7 linear interpolation between order statistics
(`method:streamflow-doy-climatology@1.0.0`, `packages/providers/usgs/src/cascade_providers_usgs/climatology.py`)
— over three different reference windows. **FACT, computed 2026-08-24.**

| Day | median, POR 1929–2026 | median, 2006–2025 | change | p90, POR | p90, 2006–2025 | change |
|---|---|---|---|---|---|---|
| Oct 15 | 1,930 cfs | 1,750 | −9.3 % | 4,774 | 6,932 | **+45.2 %** |
| Nov 15 | 3,670 | 4,580 | +24.8 % | 10,300 | 17,730 | **+72.1 %** |
| Dec 15 | 3,520 | 3,270 | −7.1 % | 9,506 | 8,600 | −9.5 % |
| Jan 15 | 3,415 | 4,025 | +17.9 % | 8,503 | 9,724 | +14.4 % |
| Feb 15 | 2,895 | 2,790 | −3.6 % | 6,224 | 5,963 | −4.2 % |
| Jul 15 | 5,115 | 4,315 | −15.6 % | 9,673 | 7,879 | −18.5 % |
| Aug 15 | 2,330 | 1,900 | −18.5 % | 3,975 | 3,702 | −6.9 % |
| Sep 15 | 1,640 | 1,210 | **−26.2 %** | 3,036 | 2,072 | **−31.8 %** |

**The same observed flow, ranked in three ladders:**

| Day | flow (= POR median) | rank vs POR 1929–2026 | rank vs 2006–2025 | rank vs 1946–1965 |
|---|---|---|---|---|
| Oct 15 | 1,930 cfs | p49.5 | p53.0 | p28.0 |
| Dec 15 | 3,520 cfs | p49.7 | p55.0 | p43.0 |
| **Aug 15** | **2,330 cfs** | **p50.0** | **p68.0** | **p26.0** |

A **42-percentile-point** spread on the same number, from nothing but the choice of reference window. The
susceptibility surface's band edges are `[25, 75, 90]`
(`packages/hydrology/src/cascade_hydrology/susceptibility.py`), so this spread crosses two band
boundaries. (FACT, computed. Caveat: the 20-year ladders have n≈100 per day-of-year key against n≈485 for
the POR ladder, so part of the low-flow-season spread is sampling noise, not trend — but the *direction*
is consistent across the whole warm season, which noise would not be.)

**Trend vs. decadal mode.** Mann–Kendall on annual instantaneous peaks (USGS peak-flow files, fetched):

| Gauge | period | n | τ | p | Sen slope |
|---|---|---|---|---|---|
| Sauk nr Sauk 12189500 (**unregulated**) | WY1929–2025 | 97 | **+0.198** | **0.004** | +168 cfs yr⁻¹ |
| Sauk nr Sauk 12189500 | WY1976–2025 | 50 | +0.007 | **0.953** | +14 cfs yr⁻¹ |
| Skagit nr Mount Vernon 12200500 (**regulated**) | WY1941–2025 | 85 | +0.048 | 0.516 | +59 cfs yr⁻¹ |

Split-sample means: Sauk +32.5 % (WY≤1968 vs WY>1968); Mount Vernon +4.3 % (WY≤1983 vs WY>1983). Fraction
of annual peaks falling in Oct–Feb: Sauk 78 % → 84 %; Mount Vernon 81 % → 83 %.

Conditioning the same peaks on the ERSSTv5 PDO index (NDJFM mean, fetched from
`https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/index/ersst.v5.pdo.dat`):

| Gauge | cool PDO (≤ −0.5) mean / p90 | warm PDO (≥ +0.5) mean / p90 | cool:warm ratio (mean / p90) |
|---|---|---|---|
| Sauk 12189500 | 39,727 / 65,300 cfs (n=41) | 34,392 / 52,620 (n=27) | 1.16× / **1.24×** |
| Skagit Mount Vernon | 76,951 / 127,600 (n=39) | 70,890 / 94,470 (n=20) | 1.09× / **1.35×** |

**FACT, computed 2026-08-24.** Three readings, all operationally load-bearing:

1. **Regulation masks the climate signal.** The unregulated Sauk carries a significant century-scale
   positive trend; the regulated Skagit outlet does not. A trend fitted at Mount Vernon measures dam
   policy, not climate. (This vindicates the platform's existing choice — `p3_surfaces.json` already reads
   the Sauk for Skagit susceptibility.)
2. **The trend is period-dependent.** Significant from 1929, absent from 1976. Anyone fitting a trend to
   a 30–50 year record here will get an answer dominated by PDO phase.
3. **Decadal variability is the same order as the anthropogenic signal.** A 24–35 % cool-vs-warm PDO
   difference in the p90 annual peak sits alongside a projected **+24 %** in Washington peak flows at the
   4 °C GWL. **Therefore a single "climate-adjusted threshold" is not defensible; carrying the baseline's
   vintage and phase is.**

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| Clausius–Clapeyron moisture scaling | **~7 % K⁻¹** | saturation vapour pressure at ~288 K; constant-RH assumption | thermodynamics; restated in Yakima County BAS (fetched) |
| Apparent super-CC scaling of hourly extremes | **~2 × CC (~14 % K⁻¹)** | Germany, 10-min data 2005–2020; **explained by stratiform→convective mixing, not invigoration**; convective fraction β ≈ 41 % °C⁻¹ | [Dallan et al. 2025 *Nat Geosci*](https://pmc.ncbi.nlm.nih.gov/articles/PMC12074990/) (fetched) |
| Observed AR area change, 1980–2023 | **+6 % to +9 %** | ARTMIP T2 ARDTs on ERA5/MERRA-2/JRA-55 | [Henny & Kim 2025 *J Clim* 38(6)](https://cawaterlibrary.net/wp-content/uploads/2025/04/clim-JCLI-D-24-0234.1-1.pdf) (fetched) |
| Observed AR IWV / IVT change, 1980–2023 | **+1.5–2.5 % / < +1 %** | 850-hPa wind and VIMFC *decreased* | same |
| Intense-AR subset, 1980–2023 | **IVT +3–4 %, IWV +4–6 %, VIMFC +6–10 %** | fixed-frequency most-intense grid points | same |
| Extreme-vs-mean AR intensification ratio | **max IVT ~3–6×, max IWV ~1.5–2× the AR-mean rate** | per individual AR | same |
| Projected global AR frequency (RCP8.5) | **~+50 %** AR conditions; IVT strength **~+25 %**; ARs **~25 % longer, ~25 % wider**; **~10 % fewer** discrete ARs | 21 CMIP5 models, 1979–2002 vs 2073–2096 | [Espinoza et al. 2018 *GRL*](https://cw3e.ucsd.edu/cw3e-publication-notice-global-analysis-of-climate-change-projection-effects-on-atmospheric-rivers/) (CW3E notice fetched) |
| ARTMIP Tier 2 AR-day trend | **+1–10 AR days yr⁻¹ per century** on western coastlines; ~+20 AR days yr⁻¹ century⁻¹ (~+30 %) in midlatitude storm tracks; AR global area 5 % → ~7 % | CMIP5 RCP8.5 + CMIP6 SSP5-8.5 | [O'Brien et al. 2022 *JGR-A*](https://pmc.ncbi.nlm.nih.gov/articles/PMC9285484/) (fetched) |
| Dominant uncertainty in AR projections | **detector (ARDT) choice > model choice**, at all latitudes on both Pacific and Atlantic coasts | | same |
| ROS runoff change, **Cascade Mountains** | **+20 % to > +100 %** in top-10 event basin runoff volume | WRF 4 km, PGW RCP8.5, 2000–2013 vs end-century | [Musselman et al. 2018 *Nat Clim Chg*](https://bpb-us-w2.wpmucdn.com/sites.coecis.cornell.edu/dist/f/423/files/2021/09/musselman18natcc.pdf) (fetched) |
| ROS flood-risk enhancement, western N. America | **+20–200 %**, for **55 %** of basins | 58/106 basins > +20 %; 20 basins (~17 % of area) > +100 % | same |
| Snowmelt share of ROS runoff, **maritime** | **30–45 %** (the *lowest* of any region; Rockies 45 % to > 65 %) | historical | same |
| ROS elevation response | less frequent at low elevation (snow loss), **more** at middle elevations; little change above **2,500 m** | | same |
| Washington **peak flow** (annual max daily runoff) projection | **+10 % (1.5 °C), +14 % (2 °C), +17 % (3 °C), +24 % (4 °C)** state average; **western WA +11 / +15 / +17 / +24 %** | RMJOC-II: 10 GCMs × 2 downscalings × 4 hydrologic models = 80 projections; 5th–95th shown | [WA Ecology Pub. 25-14-064](https://apps.ecology.wa.gov/publications/documents/2514064.pdf) (fetched, Table C-13) |
| Washington **2-year storm** (heavy precip) | **+3 % / +5 % / +13 % / +20 %** at 1.5/2/3/4 °C GWL; historical 1.8 in | WRF-UW dynamical downscaling | same, Table C-6 |
| Washington **25-year storm** (extreme precip) | **+2 % / +7 % / +13 % / +22 %**; historical 3.0 in | all models agree on sign only at 4 °C | same, Table C-7 |
| Washington **April 1 SWE** | **−21 % / −33 % / −50 % / −67 %** at 1.5/2/3/4 °C | historical 6.7 in | same, Table C-9 |
| Washington **snowpack-drought likelihood** (< 75 % of 1995–2014 April 1 SWE) | **0.2 → 0.25 / 0.5 / 0.85 / 0.95** | *"Nearly every year expected to fit the definition of snowpack drought under the 4.0 °C GWL."* | same, Table C-10 |
| Current global warming level | **2025 = 1.47 °C** above 1850–1900 (ERA5); **2023–2025 mean = 1.52 °C** (ERA5) / 1.50 °C (JRA-3Q) — first 3-yr mean above 1.5 °C | anchors which GWL column is "today" | [Copernicus GCH 2025](https://climate.copernicus.eu/sites/default/files/custom-uploads/GCH-2025/GCH2025-full-report.pdf) (fetched) |
| Snohomish + Stillaguamish **peak flow** projection | **+10 % to +40 %** by the 2080s; per-gauge averages over 2/5/10/25/50/100-yr events cluster **+21 % to +40 %** | DHSVM on 12 WRF-downscaled RCP8.5 projections, 2070–2099 vs 1981–2010 | [CIG for Snohomish County, 2021](https://cig.uw.edu/wp-content/uploads/sites/2/2021/09/Snohomish-WRF-DHSVM-Final-Report-2021-08-31-FINAL.pdf) (fetched, Table 15) |
| — Snoqualmie R. nr Snoqualmie | **+27 % (1 h) / +25 % (1 d)**, 25th–75th +10 to +42 % | 2080s | same |
| — Skykomish R. nr Gold Bar | **+22 % / +27 %** | 2080s | same |
| — Snohomish R. nr Monroe | **+24 % / +24 %**, 25th–75th +16 to +36 % | 2080s | same |
| — Stillaguamish at Stanwood | **+29 % / +24 %** | 2080s | same |
| CIG reliability caveat | *"we recommend against using"* the 1.01-yr and 500-yr projections; the 2/5/10-yr are most reliable; **no clear relationship with return interval** | | same |
| Skagit at **Mount Vernon**, natural 100-yr flood | **~ +30 % by the 2040s** (10-scenario mean) | VIC + Hybrid Delta, AR4/A1B — **vintage 2011** | [Lee & Hamlet 2011](https://www.skagitcounty.net/EnvisionSkagit/Documents/ClimateChange/Complete.pdf) (fetched) |
| Skagit at Mount Vernon, **regulated** 100-yr flood | **+20 % by 2040s, +24 % by 2080s**; proposed extra flood storage buys back only **3 % / 7 %** | single scenario, current SCL/USACE operating rules | same |
| Skagit at **Ross Dam** 100-yr flood | ~unchanged in the 2020s; **+49 % by the 2080s (A1B)** after the basin flips snow-dominant → transient | the "later in the headwaters" signal | same |
| Skagit basin low flow (7Q10) by 2080s | **75 %** of historical at Ross Dam, **60 %** at Mount Vernon; ~50 % on the Sauk and Baker | glaciers excluded, so pessimistic bias missing | same |
| PNW flood-mechanism shift | precip-driven AMF **+29 to +36 %**; snowmelt-driven **+12 %** (transition/montane), **+33 %** (temperate); **ROS-driven −9 to +10 %** | 21 headwaters, 10 GCM × 4 hydro models, RCP4.5/8.5 | [Chegwidden et al. 2020 *ERL*](https://iopscience.iop.org/article/10.1088/1748-9326/ab986f) (fetched) |
| PNW flood **elasticity** to precipitation | **1 %–2 % flood increase per 1 % annual precipitation increase** | i.e. elasticity > 1 | same |
| Mechanism prevalence, transition basins | precipitation-driven AMFs **13 % → 50 %** of annual maxima by 2100 | RCP8.5 | same |
| Mechanism prevalence, temperate basins | ROS-driven AMFs **nearly disappear**; snowmelt-driven → **~5 %** by the 2080s | RCP8.5 | same |
| Extreme-precip → extreme-flood conversion | **36 %** overall; **62 %** wet antecedent; **13 %** dry antecedent (CONUS) | the "why aren't floods" paradox | Sharma et al. 2018 — **not independently fetched** |
| Nov 2021 BC AR event attribution | AR of that magnitude ≈ **1-in-10-yr**, made **≥ 60 % more likely**; 2-day precipitation ≈ **1-in-50 to 1-in-100 yr**, **+50 %** likelihood; extreme streamflow **2–4×** more likely | closest analogue event to Nooksack/Skagit flooding | [Gillett et al. 2022, *Weather & Climate Extremes*](https://gwf-uwaterloo.github.io/gwf-publications/G22-30002/) (abstract fetched) |
| WY2026 western-US snow drought attribution | **≈ 4.4× more likely** (95 % CI **2.6–9.4×**); Upper Colorado **≈ 14×**; ~**40 km³** missing snow | no separate PNW factor published | Marshall et al. 2026 *PNAS* — release fetched, paper **not independently fetched** |
| Western snowpack decline since 1915 | **−15 % to −30 %**; **> 90 %** of long-record sites declining, **33 %** significantly; largest in spring, in Pacific states, in mild-winter climates | | Mote et al. 2018 *npj Clim Atmos Sci* — **not independently fetched** |
| **Local SNOTEL April 1 SWE trend, 1990–2026** | Stevens Pass (3,940 ft) τ = −0.087, **p = 0.46**; Paradise (5,150 ft) τ = −0.021, **p = 0.87**; Wells Creek (4,040 ft) τ = −0.043, **p = 0.75** | **no detectable trend at these sites over 35 y** — the regional decline is a longer-record, lower-elevation signal | computed 2026-08-24 from NRCS AWDB REST |
| **Sauk annual-peak trend** | WY1929–2025 τ = +0.198, **p = 0.004**; WY1976–2025 τ = +0.007, **p = 0.95** | period-dependent | computed 2026-08-24, USGS peak file |
| **PDO conditioning of annual peaks** | cool-PDO p90 is **1.24×** (Sauk) / **1.35×** (Mount Vernon) the warm-PDO p90 | decadal mode ≈ end-of-century trend in magnitude | computed 2026-08-24, USGS + ERSSTv5 PDO |
| **Percentile-ladder vintage sensitivity (Sauk)** | same Aug 15 flow = **p50** (POR) / **p68** (2006–25) / **p26** (1946–65) | crosses two of the platform's four susceptibility bands | computed 2026-08-24 |
| NOAA **Atlas 15** timeline | CONUS preliminary estimates **September 2026**; published **2027**; rest of country 2027. Vol. 1 = present-day, trend-aware, **replaces Atlas 14**; Vol. 2 = future projections via adjustment factors from downscaled climate models | Montana pilot Sept 2024, public review complete | [water.noaa.gov/about/atlas15](https://water.noaa.gov/about/atlas15) (fetched) |
| Dec 8–11 2025 event, historical rank | **7th** largest 1-day and **5th** largest 4-day western-WA precipitation volume since 1981; Nov 2006 still largest; statewide snowpack **66 % of normal** on 14 Jan 2026; snow levels 6,000–9,000 ft | *"too early to say how much of an impact climate change had on this event"* | [UW/WA State Climate Office, 13 Jan 2026](https://climate.uw.edu/2026/01/13/december-8-11-2025-heavy-rainfall-and-flooding-historical-context-and-a-note-on-snow-drought/) (fetched) |
| ENSO/PDO modulation of Skagit April 1 SWE | warm-phase April 1 SWE **42 %** (ENSO) and **58 %** (PDO) below cool-phase; **86 %** below when both warm vs both cool; Oct–Mar T difference 1.4–1.7 °F, **2.8 °F** in phase | shows the "normal" is conditional | [Lee & Hamlet 2011](https://www.skagitcounty.net/EnvisionSkagit/Documents/ClimateChange/Complete.pdf) (fetched) |

---

## 4. What is settled, what is emerging, what is contested

### Settled (established)

- **Atmospheric moisture rises at ~CC**, and AR moisture content has measurably risen since 1980
  (+1.5–2.5 % IWV). The thermodynamic term in AR intensification is not in dispute.
- **Warming shifts precipitation phase from snow to rain in the transient zone**, reducing April 1 SWE and
  raising winter runoff. Every PNW hydrologic projection since Hamlet & Lettenmaier agrees, and
  Washington's own assessment puts state-average April 1 SWE at −50 % at the 3 °C GWL.
- **Basins migrate snow-dominant → transient → rain-dominant**, and *the transient basins move first and
  most* because they sit nearest the freezing line. Present snow-dominant rivers (Sauk, upper Skagit) come
  to resemble present transient rivers; present transient rivers come to resemble present rain-dominant
  ones (CIG/TNC Puget Sound floodplains synthesis; Tohver & Hamlet 2014; Lee & Hamlet 2011).
- **Winter/cool-season streamflow rises, spring/summer falls**, with the hydrograph's peak month shifting
  toward December.
- **ROS shifts upward in elevation**, becoming rarer low and more frequent mid, with intensity increases
  driven by rain rather than melt.
- **Flood magnitude and precipitation magnitude are different questions**, mediated by antecedent
  moisture, snow, and contributing area.
- **Extreme-event attribution of AR-driven flooding is technically feasible and has been done in this
  exact climate** (Gillett et al. 2022, southwestern BC — geographically adjacent to the Nooksack).

### Emerging

- **Extremes of the AR population are intensifying faster than the AR mean** (max IVT at 3–6× the mean
  rate). If it holds, the AR *scale* rating loses information at the top end, because AR-5 is defined by a
  fixed IVT threshold whose exceedance frequency is drifting.
- **Attribution of snow drought**, now quantified for a specific western-US water year (4.4×, CI 2.6–9.4).
  No Cascades-specific factor is published yet.
- **Non-stationary precipitation-frequency standards as a routine operational input** (NOAA Atlas 15,
  CONUS preliminary Sept 2026, published 2027). This will be the first time the design-storm layer under
  Washington floodplain practice is officially non-stationary.
- **Storyline attribution as a decision-support tool.** The spectrally nudged storyline method
  ([NHESS 21, 171–186, 2021](https://nhess.copernicus.org/articles/21/171/2021/), fetched) attributes the
  *thermodynamic* component of a specific event at daily and local resolution, explicitly declining to
  assess whether climate change altered the likelihood of the dynamical setup: *"The effect of climate
  change on the occurrence likelihood of those dynamical conditions is not assessed."*

### Contested

- **Whether landfalling AR frequency over the Pacific Northwest is increasing at all.** The global and
  hemispheric picture is one of increase, but at least one 2025 analysis identifies an *"AR increasing
  hole"* over the PNW — little or no increase, possibly a decrease, attributed to anticyclonic blocking
  near the west coast — coexisting with large significant increases over the eastern US (Pan et al. 2025,
  *npj Clim Atmos Sci*; **not independently fetched**, nature.com is auth-walled; the finding is also
  summarised in the Yakima County BAS document I fetched). Against this,
  [Scholz et al. 2025, *AGU Advances*](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025AV001888)
  report a *"widespread increase in atmospheric river frequency and impacts over the 20th century"*
  (**not independently fetched**, 403). **These are not reconciled. The platform must not assert a local
  AR-frequency trend in either direction.**
- **The magnitude of AR-frequency projections at all**, because ARTMIP Tier 2 finds *detector choice*
  dominates *model choice* as the uncertainty source. A "+50 % AR frequency" number is an artefact of a
  detection algorithm as much as of a climate.
- **Whether super-CC scaling is physically real anywhere.** Dallan et al. 2025 argue the observed super-CC
  is statistical; others maintain convective invigoration. Either way, importing super-CC into a
  stratiform, orographic, duration-driven regime is unjustified.
- **Whether rain-on-snow flood risk in western Washington goes up or down.** Musselman says ROS event
  runoff rises 20 % to > 100 % in the Cascades; Chegwidden says ROS-driven annual maxima change by only
  −9 to +10 % and *decline in prevalence* to near-zero in temperate basins by the 2080s. **Both can be
  true** — Musselman conditions on ROS occurring and integrates upward-migrating extent, Chegwidden asks
  which mechanism produces the annual maximum — but the naive reading "ROS floods get worse here" is not
  supported without saying which question is being asked. (INFERENCE.)
- **Whether observed snowpack decline is detectable at Cascade SNOTEL sites over the satellite era.** I
  find **no significant trend** in April 1 SWE at Stevens Pass, Paradise or Wells Creek over 1990–2026
  (p = 0.46/0.87/0.75), against a strong regional decline in the 1915-onward record. Short records at high
  elevations do not resolve the signal. This is a caution about what the platform may say from its own
  SNOTEL feeds, not a refutation of Mote et al.
- **Whether individual-event attribution is operationally defensible.** See §6.7.

---

## 5. Western Washington specificity (what transfers, what does not)

**Transfers well.**
- The Musselman ROS result *is* partly a maritime result and explicitly names the Cascades (+20 % to
  > 100 % basin event runoff) and the Pacific maritime region (largest low-elevation ROS frequency
  decline). Its 30–45 % maritime snowmelt share is directly usable as a local prior.
- Chegwidden covers northwestern-US headwaters including the Cascades; its "temperate" class is the
  western-Washington lowland/foothill class.
- The Washington Ecology GWL tables and the CIG Snohomish DHSVM study are *of* this region.

**Transfers with caution.**
- **California AR results.** California ARs are more often the sole flood mechanism and hit a
  Mediterranean antecedent state; western Washington enters flood season with soils already near
  field capacity and with AR *families* rather than single events. California statistics on
  AR-scale-to-flood conversion (only 17 % of AR4–5 producing a flood) are informative about the
  *insufficiency of IVT*, not about our conversion rate.
- **Rockies and Sierra ROS.** Their snowmelt share of ROS runoff is 45 % to > 65 % versus our 30–45 %, and
  their snowpacks are cold and continental. Sierra "> 200 %" ROS increases are not our number; the
  Cascades number is 20 % to > 100 %.
- **European super-CC / convective results.** Different precipitation type entirely (§2.2).

**Does not transfer.**
- Design-storm intensification numbers derived from convective regimes (US Southeast, Midwest, continental
  Europe). Our extremes are 2.7 ± 0.9 mm h⁻¹, multi-day, orographic.
- Snow-drought attribution factors computed over the whole western US, or dominated by the Upper Colorado
  (14×), applied to the Cascades.

**Purely local structure the literature will not give you.**
1. **Regulation.** The Skagit, Green, White and Cedar outlets are policy-mediated. The measured
   consequence (§2.9) is that the anthropogenic peak-flow trend is detectable on the unregulated Sauk and
   *not* at the regulated Mount Vernon outlet. Any climate statement about a regulated reach is a
   statement about the joint system of climate *and* operating rule — and the operating rule is itself
   under revision, which is a second, faster non-stationarity.
2. **The Skagit's stage–discharge relation is itself non-stationary** — the repository's prior pass
   documents ~29 % less flow for the same 37.00 ft stage between 1906 and 2021, and a record 37.73 ft on
   ~12 % less flow than the 1990 record. So even a perfectly climate-adjusted *discharge* projection maps
   to a moving *stage* threshold. Sediment aggradation, channel change and levee works compound with
   climate here; they are not the same signal and must not be blended.
3. **Tidal/compound coastal.** Mount Vernon and Ferndale are tidally influenced; sea-level rise adds a
   downstream boundary-condition trend to a river-stage threshold. Washington Ecology's synthesis uses
   Sweet et al. (2022) exceedance probabilities for 0.3/0.5/1.0 m by 2081–2100 (FACT, Ecology p. 49) — a
   separate non-stationarity acting on the same displayed number.
4. **Where we are in the decadal cycle right now matters more than the trend for the coming season.** The
   ERSSTv5 PDO index for July 2026 is **−2.03** and has been negative essentially continuously since 2020
   (FACT — fetched; consistent with `flood-genesis-mechanisms-2026-08-24.md` §5). Cool PDO is the higher
   flood-risk phase here (p90 annual peak 1.24–1.35× the warm-phase value). The platform is entering
   WY2027 in the *high* half of the decadal modulation, alongside a projected very strong El Niño that
   points the other way.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 Every climatology, threshold and normal gets a **vintage**, and cross-vintage comparison is refused

This is the P0. `method:streamflow-doy-climatology@1.0.0` already records
`climatology_ref="usgs-ogc-daily:<site>:<begin>-<end>"` — good. What is missing is that the *reader* is
never told the ladder mixes climate regimes, and nothing enforces that two percentiles built from
different windows are not compared. Given the measured 42-percentile spread (§2.9), a percentile without
its window is a number without a unit.

Concretely: add `climatology_period_start` / `climatology_period_end` / `climatology_n_years` as
*required* fields on any percentile-bearing `DerivedFeature`; render them beside the percentile; make
`as_known_at` replays reproduce the ladder that existed at knowledge time (a ladder rebuilt annually is a
*revision*, per `DATA_DOCTRINE.md` §8, not an update); and add a contract test that a percentile computed
against ladder A can never be differenced against one from ladder B.

### 6.2 Publish the ladder's sensitivity, do not "correct" for it

Do **not** apply a climate-trend adjustment to the percentile ladder. The measured decadal modulation is
as large as the century trend, the trend is period-dependent (p=0.004 from 1929, p=0.95 from 1976), and
any adjustment would be an uncalibrated method the doctrine forbids. Instead **publish the sensitivity**:
alongside the primary percentile, compute the same value against a second, explicitly named ladder (e.g.
most-recent-30-years) and expose the *difference* as a `climatology_vintage_sensitivity` driver. That is a
disagreement signal, and `DATA_DOCTRINE.md` §10 already says disagreement is information.

### 6.3 The ROS-exposed fraction is the right primitive; the fixed 1,000–4,000 ft band is the wrong one

`HYDROLOGY.md` §2 labels the transient zone 1,000–4,000 ft an ASSUMPTION and §7 already promotes the two
derived fractions. Musselman's central result — that ROS migrates *upslope* and that the runoff increase
comes from *extent* expansion — closes this: a fixed band is guaranteed to be wrong in a warming climate,
whereas `rain-exposed basin fraction` and `rain-on-snow exposed fraction` are correct by construction
because they recompute from the forecast snow level and today's snow-covered area every cycle. **Delete
the fixed band from the doctrine; keep it only as a display annotation with a vintage.**

### 6.4 Add "SWE below the forecast snow level" as a first-class feature, and keep percent-of-normal as context only

Musselman's definition (rain ≥ 10 mm d⁻¹ on SWE ≥ 10 mm with melt ≥ 20 % of total) is a usable, citable,
*published* threshold set for a derived ROS-potential indicator, and it is far better than a percent-of-
normal SWE number whose denominator is a moving 1991–2020 normal. The susceptibility module already
carries SWE with `direction="context_not_scored"` — correct, and this domain reinforces it: with
snowpack-drought likelihood going 0.2 → 0.85 at the 3 °C GWL, "percent of normal SWE" will spend most
future winters flagging a state that is *normal for the new climate* and says nothing about hazard.

### 6.5 Do not compute return periods; now there are four reasons, not three

The prior pass gave three: mixed populations, a non-stationary rating, disputed historic peaks. This
domain adds the fourth and it is decisive: **the underlying precipitation-frequency standard is being
replaced by a non-stationary one**. NOAA Atlas 15 Vol. 1 (trend-aware present day, replacing Atlas 14) has
CONUS preliminary estimates in **September 2026** and publication in **2027**; Vol. 2 adds future-projected
estimates. Any "100-year" number the platform stores between now and then has a known expiry date. Store
Atlas-14-derived values, if at all, as `CONFIGURED` with a `standard_version` field, and plan the Atlas 15
ingest now.

### 6.6 Model agreement (Surface IV) should include a *climate-vintage* axis

`HYDROLOGY.md` §6 computes agreement between NWPS, NWM and ensemble spread. Add a fourth, slower axis:
agreement between the *reference distributions* — the platform's own ladder, the USGS published day-of-year
statistics (already carried as a cross-check under `method:usgs-published-doy-stats@1.0.0`), and the NWS
threshold vintage. Where these disagree, that is not noise; it is the non-stationarity signal, and it is
exactly the kind of thing an operator should see rather than have averaged away.

### 6.7 Attribution: say nothing about the event in front of you

Rapid attribution of a *specific* AR flood is scientifically defensible (Gillett et al. 2022 did it for
southwestern BC: ≥ 60 % more likely for the AR, 2–4× for the streamflow) but it is **not operationally
defensible for this platform**, for three independent reasons:

1. It arrives weeks to months after the event, so it can never be part of a live surface.
2. Probabilistic attribution requires a calibrated model chain; `DATA_DOCTRINE.md` §9 forbids the platform
   from printing a probability without one.
3. Storyline attribution, which *is* conditional and physically transparent, explicitly declines to say
   anything about the likelihood of the dynamical setup — so a storyline statement is not the sentence a
   reader would take it for.

**Recommended doctrine sentence:** *Cascadia Papsukkal does not attribute individual events to climate
change. It links to published attribution studies, badged OFFICIAL or EXTERNAL with issuer and date, and
it states the climatological vintage of every threshold and percentile it displays so that a reader can
see the baseline moving without the platform claiming to have measured why.*

### 6.8 The Sauk is the climate sensor; say so

The measurement in §2.9 turns an existing configuration choice into a documented method: reading basin
wetness for the Skagit from the unregulated Sauk rather than from Mount Vernon is not only a
regulation-hygiene choice (as `p3_surfaces.json` says), it is the only place in that basin where a climate
trend is detectable at all. Record that in the note.

### 6.9 New data sources this domain justifies

| Source | What it gives | Priority |
|---|---|---|
| **NOAA Atlas 15 Vol. 1/2** (CONUS preliminary Sept 2026) | non-stationary precipitation-frequency standard; replaces Atlas 14 | P1, ingest planned now |
| **NCEI ERSSTv5 PDO index** (`.../ersst.v5.pdo.dat`) + CPC ONI | decadal/interannual phase as *context* on every climatology | P1, trivially cheap, plain text |
| **RMJOC-II hydrologic projections** (80 members for the Columbia basin + WA/OR coastal) | the dataset behind Washington's official peak-flow/SWE indicator tables | P2, reference only — never a live surface |
| **WRF-UW dynamically downscaled WA projections** | the precipitation-indicator basis for Ecology's GWL tables | P2, reference only |
| **CIG Snohomish/Stillaguamish DHSVM per-gauge tables** | per-gauge % change in peak flow, directly attachable to forecast points as documented context | P2 |
| **USGS peak-flow files** (already fetched for 8 basins) | trend and PDO conditioning per gauge, recomputed annually | P1, one file per gauge |

All of these are **reference/context** classes. None may enter a hazard computation: they are projections,
so under `DATA_DOCTRINE.md` §2 they are `MODELED` at best and, when used for a Cascade-derived statement,
`EXPERIMENTAL`.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

| # | Repo statement | Verdict | Why |
|---|---|---|---|
| 1 | `HYDROLOGY.md` §2: *"transient snow zone … roughly 1,000 and 4,000 ft"* (labelled ASSUMPTION) | **Qualified — and now demonstrably time-varying** | The band translates upward with warming (Musselman: ROS declines low, rises mid, little change > 2,500 m). A fixed band is not merely imprecise, it decays. Keep the derived fractions; retire the band from doctrine. |
| 2 | `HYDROLOGY.md` §8: *"Percentiles require climatology; the platform builds its own from stored history"* | **Materially incomplete** | Silent on *which* history. Measured: the same Sauk flow ranks p26/p50/p68 depending on the window. A percentile without a stated period is not a defensible number under §1's "every value carries its provenance". |
| 3 | `DATA_DOCTRINE.md` §7: *"Official thresholds … re-fetched on a schedule and versioned"* | **Correct instinct, insufficient scope** | Versioning catches NWS *changing* a threshold. It does not capture that the threshold's *underlying standard* (Atlas 14 → Atlas 15) is being replaced, nor that the stage-defined thresholds sit on a shifting rating and a rising tide. Add `standard_version` and a `datum_and_baseline_vintage` block. |
| 4 | `HYDROLOGY.md` §5: hazard *"Ordered by authority"*, with official categories first | **Unchanged and correct** | Nothing in this domain justifies the platform adjusting an official category for climate. The opposite: it justifies displaying the category's vintage. |
| 5 | `HYDROLOGY.md` §7: *"SWE is storage, not hazard … More SWE can buffer a storm … or amplify it"* | **Confirmed and sharpened** | Maritime ROS snowmelt share is only 30–45 %, the lowest of any western region (Musselman Fig. 3f), so the amplification term is structurally small here — and Chegwidden finds ROS-driven annual maxima nearly disappear in temperate PNW basins by the 2080s. The doctrine's refusal to score SWE is right *and* becoming more right. |
| 6 | `HYDROLOGY.md` §12: knowledge-time replay | **Extended** | Replay currently guarantees you see the *values* known at T. It does not yet guarantee you see the *climatology* known at T. A ladder rebuilt annually silently back-dates a better baseline into a 2025 replay — a look-ahead bias of exactly the kind §11 exists to prevent. This is a bug class, not a feature request. |
| 7 | `HYDROLOGY.md` §2: *"Extreme Western Washington floods are forcing-driven"* | **Confirmed, with a caveat this domain adds** | True, and the forcing is intensifying thermodynamically. But Chegwidden's elasticity of 1–2 % flood per 1 % precipitation means the *basin* amplifies the forcing change — the forcing/state split is a decomposition, not an independence claim. |
| 8 | `docs/research/flood-genesis-mechanisms-2026-08-24.md` §6.7 (nonstationary forcing) | **Confirmed and dated** | Atlas 15's CONUS timeline is now concrete: preliminary Sept 2026, published 2027. |
| 9 | Implicit anywhere the platform shows "percent of normal" SWE or precipitation | **Contradicted** | With snowpack-drought likelihood projected 0.2 → 0.85 at 3 °C, a 1991–2020 or 1995–2014 normal will label most future winters "drought". The denominator must carry its period, and the statistic should be demoted to context. |
| 10 | `p3_surfaces.json` note: Sauk chosen *"not from the Mount Vernon outlet"* on regulation grounds | **Confirmed, with a second reason** | Regulation also erases the climate trend: Sauk p = 0.004 (WY1929–2025), Mount Vernon p = 0.52. |

---

## 8. Open questions

1. **Is landfalling AR frequency over western Washington increasing, flat, or decreasing?** The literature
   is split (Pan et al. 2025's PNW "AR increasing hole" vs Scholz et al. 2025's widespread 20th-century
   increase), neither was independently fetched, and ARTMIP shows detector choice dominates. Resolvable
   only by running two or three ARDTs on ERA5 over a Washington landfall window — a bounded piece of work.
2. **What is the Cascades-specific snow-drought attribution factor?** The 4.4× is western-US-wide and the
   14× is Upper Colorado. Maritime packs are more temperature-sensitive, so the local factor is plausibly
   *higher* — but that is an INFERENCE, not a number.
3. **What is the correct baseline window for a day-of-year flow ladder on a regulated reach?** The
   climate argument says "recent"; the sampling argument says "long"; the regulation argument says "since
   the current operating rule took effect". These three give different answers and there is no principled
   reconciliation in the literature I found.
4. **How much of the Sauk's 1929-onward peak-flow trend is climate and how much is PDO sampling?** The
   record begins in a warm-PDO phase and the 1976-onward window shows nothing. A pre-whitened or
   PDO-conditioned trend test is needed before any statement is made.
5. **Do Musselman's Cascade ROS increases survive at basin scale with a real hydrologic model?** His result
   is water-available-for-runoff from an atmospheric model, not routed streamflow; Chegwidden's routed
   result shows ROS-driven annual maxima barely changing. The reconciliation has not been published for
   these basins.
6. **How much does sea-level rise move the Mount Vernon and Ferndale stage thresholds, and on what
   timescale, relative to channel-change effects?** Both are non-stationarities on the same displayed
   number; nothing I found separates them for the Skagit delta.
7. **Does the AR-scale rating degrade as a hazard signal as the IVT distribution shifts?** If max IVT
   rises 3–6× faster than mean IVT (Henny & Kim), the AR-5 exceedance frequency drifts and the scale's
   categories are themselves a stationary artefact. No study I found tests this.
8. **What is the right operational treatment of storyline attribution?** It is physically transparent and
   conditional, which fits this platform's epistemics better than probabilistic attribution — but it
   explicitly does not constrain the likelihood of the dynamical setup, and no guidance exists on
   communicating that distinction to a non-specialist reader.
9. **Are the Cascade SNOTEL non-trends (p ≈ 0.5–0.9 over 1990–2026) a power problem or a real elevation
   effect?** A field-significance test across all WA SNOTEL sites, stratified by elevation, would settle
   it, and the platform already ingests AWDB.

---

## 9. Sources

**Independently fetched (primary or agency):**

- [Musselman, K.N. et al. (2018), *Projected increases and shifts in rain-on-snow flood risk over western North America*, Nature Climate Change 8, 808–812](https://bpb-us-w2.wpmucdn.com/sites.coecis.cornell.edu/dist/f/423/files/2021/09/musselman18natcc.pdf) — full text extracted.
- [O'Brien, T.A. et al. (2022), *Increases in Future AR Count and Size: Overview of the ARTMIP Tier 2 CMIP5/6 Experiment*, JGR-Atmospheres 127, e2021JD036013](https://pmc.ncbi.nlm.nih.gov/articles/PMC9285484/)
- [Henny, L. & Kim, K.-M. (2025), *The Changing Nature of Atmospheric Rivers*, J. Climate 38(6)](https://cawaterlibrary.net/wp-content/uploads/2025/04/clim-JCLI-D-24-0234.1-1.pdf) — abstract page.
- [Dallan, E. et al. (2025), *Super-Clausius–Clapeyron scaling of extreme precipitation explained by shift from stratiform to convective rain type*, Nature Geoscience 18, 382–…](https://pmc.ncbi.nlm.nih.gov/articles/PMC12074990/)
- [Chegwidden, O.S. et al. (2020), *Climate change alters flood magnitudes and mechanisms in climatically-diverse headwaters across the northwestern United States*, ERL 15, 094048](https://iopscience.iop.org/article/10.1088/1748-9326/ab986f)
- [Washington State Dept. of Ecology (Aug 2025), *2025 Summary Report on the Science of Human Caused Climate Change and Impacts in Washington State*, Pub. 25-14-064](https://apps.ecology.wa.gov/publications/documents/2514064.pdf) — Tables C-6, C-7, C-9, C-10, C-13 and methods.
- [UW Climate Impacts Group for Snohomish County (Sept 2021), *Climate Change & Flooding in Snohomish County: New Dynamically-Downscaled Hydrologic Model Projections*](https://cig.uw.edu/wp-content/uploads/sites/2/2021/09/Snohomish-WRF-DHSVM-Final-Report-2021-08-31-FINAL.pdf) — Table 15 and exec. summary.
- [Lee, S.-Y. & Hamlet, A.F. (2011), *Skagit River Basin Climate Science Report*, UW CEE / CIG for Skagit County](https://www.skagitcounty.net/EnvisionSkagit/Documents/ClimateChange/Complete.pdf) — vintage AR4/A1B; flood, low-flow and ENSO/PDO sections.
- [Tohver, I. & Hamlet, A.F. (2014), *Impacts of 21st century climate change on hydrologic extremes in the Pacific Northwest region of North America*](https://digital.lib.washington.edu/server/api/core/bitstreams/9417b526-78bc-4d3e-a049-ad7fb357e87b/content) — qualitative basin-class results.
- [NOAA Atlas 15 informational page](https://water.noaa.gov/about/atlas15) — timeline, Vol. 1/Vol. 2 scope.
- [Copernicus/C3S, *Global Climate Highlights 2025*](https://climate.copernicus.eu/sites/default/files/custom-uploads/GCH-2025/GCH2025-full-report.pdf) — 1.47 °C (2025), 1.52 °C (2023–2025 mean).
- [WA State Climate Office / UW (13 Jan 2026), *December 8–11, 2025 Heavy Rainfall and Flooding: Historical Context and a Note on Snow Drought*](https://climate.uw.edu/2026/01/13/december-8-11-2025-heavy-rainfall-and-flooding-historical-context-and-a-note-on-snow-drought/)
- [WA State Climate Office / UW (13 Jan 2025), *Rain on Snow*](https://climate.uw.edu/2025/01/13/rain-on-snow/)
- [Gillett, N.P. et al. (2022), *Human Influence on the 2021 British Columbia Floods*, Weather and Climate Extremes 36, 100441](https://gwf-uwaterloo.github.io/gwf-publications/G22-30002/) — abstract.
- [Espinoza, V. et al. (2018), *Global Analysis of Climate Change Projection Effects on Atmospheric Rivers*, GRL 45, 4299–4308](https://cw3e.ucsd.edu/cw3e-publication-notice-global-analysis-of-climate-change-projection-effects-on-atmospheric-rivers/) — CW3E publication notice.
- [Payne, A.E. et al. (2020), *Responses and impacts of atmospheric rivers to climate change*, Nature Reviews Earth & Environment 1, 143–157](https://eesm.science.energy.gov/publications/responses-and-impacts-atmospheric-rivers-climate-change) — **abstract only**; full review paywalled.
- [NHESS 21, 171–186 (2021), *A methodology for attributing the role of climate change in extreme events: a global spectrally nudged storyline*](https://nhess.copernicus.org/articles/21/171/2021/)
- [Colorado School of Mines newsroom (21 Jul 2026), release for Marshall et al. 2026 PNAS](https://www.minesnewsroom.com/news/climate-change-made-years-snow-drought-western-us-four-times-more-likely-new-colorado-school)
- [Yakima County (17 Dec 2025), *Clausius-Clapeyron Relationship and Atmospheric Rivers: Climate Change Impacts on Yakima Basin*, BAS Update research compilation](https://www.yakimacounty.us/DocumentCenter/View/43010/Clausius_Clapeyron_Atmospheric_Rivers_BAS_Research_DRAFT-12172025-ksw) — **secondary compilation**; used only where its primary citations were independently checked.

**Primary datasets fetched and computed by me, 2026-08-24:**

- USGS NWIS daily values, Sauk River near Sauk 12189500, 1929-01-01 → 2026-08-23 (`https://waterservices.usgs.gov/nwis/dv/?format=rdb&sites=12189500&parameterCd=00060&statCd=00003`) — 35,663 daily means; day-of-year ladders.
- USGS annual peak-flow files, 12189500 (WY1912–2025, n=98) and Skagit River near Mount Vernon 12200500 (WY1941–2025, n=85) (`https://nwis.waterdata.usgs.gov/nwis/peak?...&format=rdb`) — Mann–Kendall, Sen slope, split-sample, seasonality.
- NOAA NCEI ERSSTv5 PDO index (`https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/index/ersst.v5.pdo.dat`) — NDJFM phase conditioning; July 2026 value −2.03.
- NRCS AWDB REST daily WTEQ, Stevens Pass (791:WA:SNTL, 3,940 ft), Paradise (679:WA:SNTL, 5,150 ft), Wells Creek (909:WA:SNTL, 4,040 ft) — April 1 and peak SWE trends 1990–2026.

**Cited but NOT independently fetched (auth-walled, bot-walled, or search-summary only) — all claims from these are labelled INFERENCE above:**

- Sharma, A., Wasko, C. & Lettenmaier, D.P. (2018), *If Precipitation Extremes Are Increasing, Why Aren't Floods?*, WRR 54, 8545–8551, doi:10.1029/2018WR023749.
- Ivancic, T.J. & Shaw, S.B. (2015), on extreme-precipitation-to-extreme-discharge conversion and soil moisture.
- Wasko, C. & Nathan, R. (2019), *Influence of changes in rainfall and soil moisture on trends in flooding*, J. Hydrol.
- Mote, P.W. et al. (2018), *Dramatic declines in snowpack in the western US*, npj Clim Atmos Sci 1, 2.
- Marshall, A.M., Cowherd, M., Rahimi, S. & Ye, Y. (2026), *The 2026 western US snow drought was about four times more likely due to climate change*, PNAS, doi:10.1073/pnas.2612961123 (numbers taken from the Mines release).
- Swain, D.L. (2026), *Strong human fingerprint on low snowpack amid increasing volatility*, PNAS, doi:10.1073/pnas.2620765123.
- Marshall, A.M. et al. (2019), *Projected changes in interannual variability of peak snowpack amount and timing in the Western United States*, GRL 46, 8882–8892 — reported 6.6 % → 42.2 % frequency of consecutive snow-drought years.
- Pan, M. et al. (2025), *Contrasting historical trends of atmospheric rivers in the Northern Hemisphere*, npj Clim Atmos Sci — the PNW "AR increasing hole".
- Scholz, S. et al. (2025), *Widespread Increase in Atmospheric River Frequency and Impacts Over the 20th Century*, AGU Advances, doi:10.1029/2025AV001888.
- Higgins, T. et al. (2025), *Changes to Atmospheric River Related Extremes Over the United States West Coast Under Anthropogenic Warming*, GRL 52, e2024GL112237 — the ~10× extreme-AR-frequency claim, **unverified**.
- Shields, C.A. & Kiehl, J.T. (2016), *Atmospheric river landfall-latitude changes in future climate simulations*, GRL 43.
- Warner, M.D., Mass, C.F. & Salathé, E.P. (2015), *Changes in winter atmospheric rivers along the North American West Coast in CMIP5 climate models*, J. Hydrometeorol. 16, 118–128.
- Salathé, E.P. et al. (2014), *Estimates of twenty-first-century flood risk in the Pacific Northwest based on regional-scale climate model simulations*, J. Hydrometeorol.
- Shepherd, T.G. et al. (2018), *Storylines: an alternative approach to representing uncertainty in physical aspects of climate change*, Climatic Change 151, 555–571.
- Fifth National Climate Assessment (2023), Ch. 27 Northwest — DNS failure at fetch time; its Washington findings are represented here via the Ecology 2025 synthesis, which cites it.
