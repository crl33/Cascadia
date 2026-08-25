# Snow hydrology, rain-on-snow, and snow drought

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

Domain lead pass deepening `docs/research/flood-genesis-mechanisms-2026-08-24.md` §4. Every claim
below is labelled FACT (a source was fetched and read, URL given), INFERENCE (reasoned from cited
facts, arithmetic shown), ASSUMPTION, or OPEN QUESTION. Two datasets were fetched directly from
NRCS AWDB for this entry and the arithmetic is reproduced so it can be re-run.

---

## 1. Headline

**In the maritime Cascades the snowpack is a small, leaky, energy-limited buffer, not a reservoir of
flood water: for the archetypal western-Washington rain-on-snow flood, snowmelt supplies on the
order of 19–35 % of the water reaching the ground and rain supplies the rest, the pack's combined
cold-content and liquid-water buffer is worth roughly 30–45 mm against a 200–400 mm atmospheric
river, and the flood-relevant quantity is therefore not "percent of normal SWE" but *how much snow
sits below the storm's mountainside snow line, how much energy is available to ripen it, and how
synchronised its outflow is with the rain*.** Every one of those four quantities is unobserved by
the network Cascadia Papsukkal currently ingests, and the one number the platform can get today —
SNOTEL percent-of-median — is measured almost entirely *above* the elevation band where the floods
are made.

The quantitative proof of the last sentence, computed for this entry from NRCS AWDB on 2026-08-24:
on **2025-12-11**, the day before the record Skagit crest at Mount Vernon, the twenty western-
Washington Cascade SNOTEL sites below 4,500 ft held **14 % of median SWE** and ten of them read
exactly **0.0 in**, while the all-station composite read 44 % because three crest/leeward North
Cascades sites were at 128–174 % of median. A basin-mean "percent of normal" would have concealed
the entire hydrologic story of Event Zero.

---

## 2. Mechanisms — the physics, stated properly

### 2.1 The snowpack energy balance

The complete surface energy balance of a snow cover, in W m⁻² positive toward the pack, is

```
ΔQ = (S↓ − S↑) + (L↓ − L↑) + H + λE + G + M − ΔU/Δt
```

| Term | Name | Physics |
|---|---|---|
| `S↓ − S↑` | net shortwave | governed by incoming solar and albedo (0.9 fresh → 0.4–0.6 aged/wet/dirty snow) |
| `L↓ − L↑` | net longwave | `L↑ = εσT_s⁴` is pinned near 316 W m⁻² for a melting surface (ε≈0.98, T_s=273.15 K); `L↓` from a saturated overcast column at 5 °C is ~340–360 W m⁻², so net longwave becomes a **positive** melt term under warm cloud |
| `H` | sensible heat | `H = ρ_a c_p C_H U (T_a − T_s)`; scales with wind speed and air-minus-surface temperature |
| `λE` | latent heat | `λE = ρ_a λ_v C_E U (q_a − q_s)`; **condensation onto a 0 °C pack releases λ_v ≈ 2.50 MJ kg⁻¹ against λ_f = 0.334 MJ kg⁻¹, so 1 kg of condensate melts ≈ 7.5 kg of ice** |
| `G` | ground heat | small but non-zero, and non-trivially large at some PNW sites (below) |
| `M` | advected heat from rain | `M = ρ_w c_w P (T_r − 0 °C)`; `c_w = 4.18 kJ kg⁻¹ K⁻¹` |
| `ΔU/Δt` | internal energy change | cold content payment, refreeze, warming toward isothermal |

**Advected rain heat, worked (INFERENCE, arithmetic shown).** 50 mm of rain at 6 °C onto a 0 °C
pack carries `0.050 m × 1000 kg m⁻³ × 4.18 kJ kg⁻¹ K⁻¹ × 6 K = 1.25 MJ m⁻²`, which melts
`1.25 / 0.334 = 3.8 kg m⁻² = 3.8 mm SWE`. That is **7.5 % of the rain depth** — the standard
"rain heat is minor" result, and it is why the term is minor *in mass* even where it is a large
fraction of the *energy* budget of a pack that is already isothermal.

### 2.2 Cold content and the ripening sequence

Cold content is the energy deficit that must be paid before any melt occurs (FACT — Jennings,
Kittel & Molotch 2018, *The Cryosphere*):

```
CC = c_i · ρ_s · d_s · (T_s − T_m),     c_i = 2.1 × 10⁻³ MJ kg⁻¹ °C⁻¹,  T_m = 0 °C
```

with `ρ_s d_s` = SWE in kg m⁻². Ripening then proceeds in three gated stages, and **outflow begins
only after all three are complete** (FACT — Frontiers ROS review, Brandt et al. 2022):

1. **Warming** — pay `CC` until the pack is isothermal at 0 °C.
2. **Ripening** — melt grain boundaries; meltwater is retained in pore space against gravity up to
   the **liquid water holding capacity**.
3. **Output** — only now does further input produce outflow at the base.

**How big is the buffer in a maritime pack? (INFERENCE, arithmetic shown.)**
Take SWE = 400 mm (400 kg m⁻²), depth-weighted pack temperature −1 °C — typical for a Cascade
pack in a warm December.

- `CC = 2.1e-3 × 400 × 1 = 0.84 MJ m⁻²`, equivalent to `0.84 / 0.334 = 2.5 mm` of melt forgone.
- Under a sustained ROS melt-energy flux of ~150 W m⁻², that deficit is paid in
  `0.84e6 / 150 ≈ 5,600 s ≈ 1.6 hours`.
- Liquid water holding: **[CORRECTED 2026-08-24 by adversarial review — the original arithmetic
  applied a *volumetric* LWC percentage as if it were a fraction of SWE by mass, and understated the
  liquid term by roughly a factor of three.]** Brandt et al. 2022 report LWC of 0.9 % / 3.7 % / 6.8 %
  (stratified / isothermal / rain-conditioned). Checking the primary source: Juras et al. 2017
  (HESS 21:4973–4987, Table 2) measured LWC with a Denoth meter in **volume percent**, and report both
  `Total LWC (%)` and `Total LWC (mm)` — e.g. 3.7 % over a 29.7 cm pack = 11.0 mm. Two consequences:
  (a) Brandt's "0.9 %" for the stratified mid-winter pack is a mis-transcription of Juras's **0.9 mm**;
  the volumetric value is **0.2 %**. (b) Volumetric percentages cannot be multiplied by SWE. Expressed
  as a fraction of SWE, Juras's three ripe packs held **6.8–9.4 % of SWE** before sprinkling and
  **10.9–15 % of SWE** after, so for a 400 mm SWE maritime pack the liquid term is
  **~27–37 mm held, ~44–60 mm at saturation**, not 12 mm. (FACT — Juras et al. 2017 Table 2, fetched.)
- **Combined buffer ≈ 30–45 mm of water** (cold content ~2.5 mm + liquid ~27–37 mm; up to ~60 mm at
  full saturation). A 72-hour AR over a western-WA basin delivers 200–400 mm. The pack absorbs
  **roughly 8–20 % of the storm**, then conducts the rest. The qualitative conclusion is unchanged —
  the pack is a small, leaky buffer, not a reservoir — but the **15 mm / 4–7 % figures originally
  stated here must not be encoded**; they are wrong by ~3×.

A cold, deep pack is genuinely different: SWE = 800 mm at −5 °C gives `CC = 8.4 MJ m⁻²` ≡ 25 mm of
melt forgone ≡ ~16 h at 150 W m⁻². The *sign flip* the doctrine asserts is real; the *magnitude* of
the buffering side is hours to a day, not a storm.

Jennings et al. 2018 measured the melt-onset delay attributable to cold content at **3.4 h (alpine)
and 3.9 h (subalpine)** in Colorado (FACT) — the same order as the arithmetic above, in a
*continental* climate where cold content is larger. Peak cold content in the Colorado subalpine ran
**−2.2 to −1.7 MJ m⁻²**, and alpine peak cold content was **2.6× subalpine** while alpine peak SWE
was only 2.1× subalpine — i.e. cold content per unit SWE is lower where the pack is warmer. The
authors note explicitly that a unit of Sierra/Cascade snowfall "should contribute less snowpack cold
content" than the same unit in the Rockies (FACT), but **present no maritime data** — the maritime
cold-content climatology is an OPEN QUESTION.

### 2.3 Preferential flow — why outflow can precede ripening

Water does not move through snow as clean matrix (Darcian) flow. Dye-tracer work shows
**preferential flow paths occupying only 3–8 % of a cross-sectional area** can convey large volumes,
effectively insulating the rest of the pack (FACT via Brandt et al. 2022, citing McGurk & Marsh
1995). Consequences the platform must respect:

- A pack can pass rain to the ground **before** its bulk cold content is satisfied. "Ripe or not"
  is not a binary gate on outflow.
- **Highly-stratified mid-winter packs (LWC 0.9 %) generated a *faster* outflow response** than
  three isothermal packs (mean LWC 3.7 %) in rainfall-simulation experiments (FACT, ibid.,
  citing Juras et al. 2017) — the opposite of the naive expectation.
- SWE can stay flat or **increase** across a ROS event because of liquid retention and intermittent
  snowfall (FACT, ibid.). **A SNOTEL pillow that does not drop during a ROS event is not evidence
  that the pack did not deliver water.**

### 2.4 Rain-on-snow melt energy partitioning — the genuinely contested core

This is the most contested quantity in the domain, and the repo currently asserts one side of it as
FACT. The literature, in order:

| Study | Setting | Result |
|---|---|---|
| Marks et al. 1998 | Feb 1996 PNW flood, Oregon Cascades, open sites | **60–90 % of melt energy from sensible + latent (condensation-dominated)** |
| Berris & Harr 1987 | H.J. Andrews, 900 m, clearcut vs forest | clearcut **40 % greater melt** during common ROS melt periods; **21 % greater outflow** in the largest event |
| Mazurkiewicz, Callery & McDonnell 2008 | H.J. Andrews, 3 sites 1,018–1,294 m, **8 years, SNOBAL** | **Net radiation was the largest melt contributor during ROS: 55 % (UPLMET), 35 % (VANMET), 33 % (CENMET)**; turbulent max 42 % (VANMET); advected rain **10–15 %**; ground heat 8–24 % |
| Jennings & Jones 2015 | H.J. Andrews, 26 storms 1992–2012 | advected rain heat **29–44 % of the energy budget in persistent-melt events**; wind at 5 m was **0.2 ± 0.1 m s⁻¹** on peak days |
| Li et al. 2019 | CONUS, process model | **net radiation (longwave-dominated) is the leading energy source, 68 %**, for ROS melt in the mountainous western US |
| Trubilowicz & Moore 2017 | British Columbia, 286 ROS events / 10 yr | advected heat **< 10 %** of energy consumed for melt |

**The reconciliation (INFERENCE, and it is the operationally correct statement).** The two camps are
measuring different points of the distribution and different exposures:

- **Extreme, wind-exposed, warm-advection ROS** (Feb 1996 in the open) → turbulent fluxes dominate,
  60–90 %. Marks et al. themselves attribute the forest/open difference to **lower wind speeds
  beneath canopy reducing turbulent exchange** (FACT).
- **The ROS event population, and anywhere sheltered from the prevailing storm wind** → net
  radiation, dominated by **longwave from a warm saturated overcast**, dominates. Mazurkiewicz
  states that UPLMET "was protected from the prevailing wind direction during storm events, which
  resulted in lower turbulent-exchange rates" (FACT).
- Mazurkiewicz's own conclusion is that the results **"question the general perception of turbulent
  energy exchange dominance of ROS and seasonal melt in the PNW"** (FACT).

**Therefore: wind speed and dewpoint at pack elevation are the *discriminating* variables, not
because turbulence always dominates, but because turbulence is what makes an ordinary ROS event an
extreme one.** That is a sharper and more useful statement than "ROS melt is turbulent-flux driven".

### 2.5 Phase interference — why most ROS events are not floods

Jennings & Jones 2015 examined 26 ten-day storms at H.J. Andrews (Lookout Creek, 64 km²), 1992–2012.
All 26 largest events were ROS events with initial SWE > 0 and **> 60 % of precipitation falling as
rain** (FACT). Their mechanism, stated precisely (the prior repo pass §4.4 states the sense correctly but omits the π/2 value for large floods and the three-way moderate/large/extreme split):

- **Moderate floods:** precipitation pulses are counteracted by snowpack-outflow pulses **displaced
  by π radians → destructive interference → damped Q waveform** (FACT).
- **Large floods:** pulses are **almost in phase, displaced by π/2 radians → constructive
  interference → higher-amplitude Q**, but only intermittently through the storm (FACT).
- **Extreme floods:** P and net snowpack outflow are almost in phase **at multiple timescales (2–64 h)
  for several days coinciding with the peak** (FACT), with lysimeter outflow correlated across
  stations spanning 900–1,300 m and **42 % of basin area**.

Only **7 of 26** storms had continuous net snowpack outflow; only **2 of those 7** produced extreme
floods (FACT). The snowpack is normally a low-pass filter; in the rare extreme it stops filtering.

### 2.6 Rate limits on snowpack outflow (the numbers that bound the melt term)

From the same lysimeter record (FACT):

- For **> 81 %** of the 10-day storm hours, hourly *net* snowpack outflow was between −1 and
  +1 mm h⁻¹.
- For **> 97 %** of the hours on the day before and the day of peak discharge, **net** outflow was
  **< 3 mm h⁻¹** and **total** outflow **< 10 mm h⁻¹**; total **never exceeded 14 mm h⁻¹**.
- Cumulative snowpack outflow over 10 days was **< 300 mm**.
- Peak-day hourly precipitation intensity was **2.7 ± 0.9 mm h⁻¹**; air and dewpoint temperature
  **4.1 ± 2.7 °C and 3.4 ± 2.7 °C**.

**These are hard physical ceilings on how much a snowpack can add per hour, and they are small.**
Any product implying tens of mm per hour of snowmelt in a maritime ROS event is wrong.

### 2.7 Canopy — interception, and the clearcut-amplification question

**Interception, maritime, quantified** (FACT — Storck, Lettenmaier & Bolton 2002, Umpqua NF Oregon,
1,200 m, 3 years):

- **~60 % of snowfall intercepted** by a mature canopy, linear in snowfall up to 50 mm SWE per
  storm; maximum interception **≥ 40 mm SWE** (30 mm observed on cut trees).
- Of intercepted snow, **~72 % is removed as meltwater drip and ~28 % as mass release**
  (in melt-conducive conditions ~70 / 30).
- Sublimation **< 1 mm d⁻¹ average, ~100 mm per winter season** — against ~2 m of regional winter
  precipitation, i.e. **~5 %**. Sublimation is *not* an important maritime term.
- Under-canopy accumulation ran **~50 %** of the shelterwood; in the El Niño winter of 1997–98,
  max under-canopy SWE was **< 50 mm** against **~250 mm** in the shelterwood.
- The one significant ROS event in three years (29 Dec 1996 – 2 Jan 1997) cost the shelterwood
  **86.9 mm SWE** and the beneath-canopy lysimeter **60.4 mm** — the open site lost **44 % more**.

**Has clearcut amplification held up? Partly, and at a scale that does not reach the basin.**
(FACT, with the resolution being an INFERENCE across three studies.)

- Harr 1986: in a 96-ha clearcut in the transient snow zone, peaks of ~3–8-year return period were
  higher than pre-logging prediction.
- Berris & Harr 1987: clearcut water equivalents **2–3× forested**; **40 % greater melt**;
  **21 % greater outflow** in the largest event.
- **Jones & Perkins 2010** (>1,000 peak events, 1953–2006, three paired-watershed experiments plus
  six large basins, western Cascades): ROS events delivered **75 % more water to soils than rain
  events**; **> 10-year ROS peaks were almost twice rain peaks in large basins but only slightly
  higher in small basins**; post-logging increases in **> 1-year** peaks were only **10–20 % in
  small basins**, and *"small basin peaks do not account for the magnitudes of large basin
  rain-on-snow peak discharges"* (FACT).
- Brandt et al. 2022 summarise the canopy literature as **inconclusive**: some studies find glades
  produce more outflow, "others observed little difference" (FACT).

**Operational reading:** the plot-scale clearcut effect is real, well-measured, and worth ~20–40 % on
melt at a *point*; it does not scale to the 500–3,000 mi² basins Cascadia Papsukkal forecasts, and
should never be a basin-level term.

**Fire is the live version of this question and it is larger.** Ebel & Gleason 2026 (western Oregon
Cascades, Breitenbush) report that in burned forest, ROS events produced **14.3 mm d⁻¹ of meltwater
vs 6.2 mm d⁻¹ unburned (p < 0.001)**; a single 2023 ROS event cost a high-elevation burned site
**151 mm SWE vs 39 mm unburned (+287 %)**; midwinter melt fraction by peak SWE was **54 % burned vs
27 % unburned**; **13 additional melt days**. Mid-elevations were most vulnerable. (FACT.)

### 2.8 Snow level, freezing level, and the mountainside snow line

Three distinct elevations, routinely conflated:

1. **Freezing level `Z_0C`** — height of the 0 °C isotherm in the free air.
2. **Atmospheric snow level** — height at which falling hydrometeors finish melting in a column;
   the NBM `SNOWLVL` field is *the altitude where wet-bulb temperature first crosses above 0.5 °C*
   (FACT, `DATA_SOURCES.md` W2).
3. **Mountainside snow line `Z_S`** — where the rain/snow boundary actually intersects the terrain
   on a windward slope. **This is the one the hypsometry intersection needs, and it is the lowest
   of the three.**

Quantities (FACT — Minder, Durran & Roe 2011, *J. Atmos. Sci.* 68, 2107–2127, and sources therein):

| Quantity | Value |
|---|---|
| Radar bright band below `Z_0C`, northern California | **230–237 m mean, range 122–427 m** (White et al. 2010) |
| `Z_BB` over windward slopes vs upwind | **~200 m lower on average**; storm range **1 km lower to 200 m higher** (Kingsmill et al. 2008) |
| `Z_BB` drop, coastal profiler → Sierra base profiler | **73 m** (Lundquist et al. 2008) |
| Melting distance `Δ_melt`, weak precipitation | **~60 m** |
| `Δ_melt` at 3.5 mm h⁻¹ frozen precipitation rate | **148 m (WRF), 144 m (column model)** |
| `Δ_melt`, intense precipitation | **beyond 300 m** |
| Minder control simulation total | `d_0C = 142 m`, `d_S = 221 m`, **`d = 267 m`** |
| Component attributable to `Δ_melt` variation | **125 m** |
| Component attributable to latent cooling from melting | **61 m** |
| `Z_0C` descent over windward slopes, N. Sierra stratiform | **at least 400 m** (Marwitz 1987) |
| Same deepening/drop observed over the **Oregon Cascades** | several hundred metres (Medina et al. 2005) |

**Three consequences that matter here (INFERENCE from the above):**

- The total offset from *upwind free-air freezing level* to *mountainside snow line* is
  **roughly 250–450 m (800–1,500 ft) in ordinary storms**, which brackets the repo's 1,000 ft
  ASSUMPTION well — but the *storm-to-storm range is a full kilometre*.
- **The offset grows with precipitation intensity** (`Δ_melt` 60 m → >300 m), i.e. it is largest
  exactly during the heaviest AR hours. A fixed offset is biased high on snow level precisely when
  the answer matters most.
- Minder et al. find **`d` increases with temperature**, a negative feedback that "could act to
  buffer mountain hydroclimates against the impacts of climate warming" (FACT) — an important
  contrarian result against naive "snow level rises 150 m per °C" reasoning.

**Direct Washington number:** Minder (2010b) modelled that the **~200 m rise in mean snow line per
1 °C of warming reduces annual snowpack accumulation in the western Cascade Mountains of Washington
by about 15–18 %** (FACT, cited in Minder et al. 2011). And White et al. (2002) modelled that a
**~610 m (2,000 ft) snow-line rise during a storm would triple runoff** for three northern
California mountain basins (FACT, ibid.) — the clearest statement of why this variable is the
single highest-leverage forecast quantity in a maritime flood.

### 2.9 Precipitation-phase partitioning

FACT — Jennings et al. 2018, *Nature Communications* 9:1148, n = 17.8 million observations, 29 years,
Northern Hemisphere:

- Mean 50 % rain–snow **air-temperature threshold = 1.0 °C**; 95 % of stations span **−0.4 to 2.4 °C**.
- **Maritime climates have the coolest thresholds.** Western US: **0.6–1.5 °C near the Pacific Coast,
  Cascades and Sierra Nevada**, rising to ~3.8 °C in the Intermountain West and Rockies.
- Humidity dominates the variation: **each 10 % increase in relative humidity lowers the 50 %
  threshold by 0.8 °C**; threshold by RH bin runs **0.7 °C (90–100 % RH) to 4.5 °C (40–50 % RH)**.
  Pressure is second order: −0.3 °C per 10 kPa.
- The mixed-phase band (10 %–90 % thresholds) is **2.6–4.6 °C wide**, wider in dry air.
- **Method skill:** bivariate (T + RH) logistic regression minimum success rate **68.7 %** vs
  **60.7 %** temperature-only — and 35.3 % higher minimum success rate by RH bin. Wet-bulb methods
  had the **lowest standard deviation in success rate (5.0 % vs 15.0 % for T-only)**.
- Wet-bulb and dew-point thresholds are **colder** than air-temperature thresholds under unsaturated
  conditions.

**Operational reading:** a wet-bulb-based product (which NBM `SNOWLVL` is) is the right family. A
fixed air-temperature threshold is the wrong family. And in the maritime Cascades the correct air
temperature threshold is **near 1 °C, not 0 °C** — a fixed 0 °C rule systematically over-predicts
snow. Empirical support from the same forest: Mazurkiewicz et al. tuned dew-point thresholds of
**0.5 °C at 1,273–1,294 m and 1.0 °C at 1,018 m** to reproduce observed accumulation (FACT) — the
threshold is *lower at higher elevation*, consistent with the humidity control.

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| Specific heat of ice `c_i` | 2.1 × 10⁻³ MJ kg⁻¹ °C⁻¹ | cold-content equation | Jennings et al. 2018 TC |
| Latent heat of fusion `λ_f` | 0.334 MJ kg⁻¹ | melt | standard |
| Latent heat of vaporisation `λ_v` | ~2.50 MJ kg⁻¹ | condensation melts ~7.5× its mass | standard |
| Cold content, maritime pack 400 mm SWE at −1 °C | **0.84 MJ m⁻² ≡ 2.5 mm melt ≡ ~1.6 h at 150 W m⁻²** (the 150 W m⁻² melt flux is an unsourced ASSUMPTION representing an extreme ROS event; at the ~30–50 W m⁻² implied by Jennings & Jones's peak-day net outflow the payment is 5–8 h) | INFERENCE, arithmetic §2.2 | this entry |
| Liquid water content, real packs | **0.2 % / 3.7 % / 6.8 % by volume** (stratified / isothermal / rain-conditioned) ≡ **6.8–9.4 % of SWE** held, **10.9–15 % of SWE** at saturation | measured, Denoth meter; Brandt's "0.9 %" is a mis-transcription of Juras's 0.9 **mm** | Juras et al. 2017 Table 2 (fetched); Singh et al. 1997 (**Austria**, not maritime PNW) via Brandt et al. 2022 |
| Preferential-flow path area fraction | **3–8 %** of cross-section | conveys large volumes | McGurk & Marsh 1995 via Brandt 2022 |
| Melt energy from turbulent fluxes, Feb 1996 PNW extreme | **60–90 %** | open sites, high wind | Marks et al. 1998 |
| Melt energy from net radiation during ROS, 8-yr HJA | **55 % / 35 % / 33 %** (3 sites) | wind-sheltered forest | Mazurkiewicz et al. 2008 |
| Net radiation share of ROS melt, mountainous western US | **68 %** (longwave-dominated) | CONUS model | Li et al. 2019 |
| Advected rain heat share of ROS energy | **<10 % (BC, 286 events)** … **10–15 % (HJA)** … **29–44 % (persistent-melt HJA)** | contested by regime | Trubilowicz & Moore 2017; Mazurkiewicz 2008; Jennings & Jones 2015 |
| Share of annual snowmelt occurring on non-ROS days, HJA 1996–2003 | **80–90 %** | ROS is 22 % of melt-producing days | Mazurkiewicz et al. 2008 |
| Total snowpack outflow, peak day, maritime | **<10 mm h⁻¹, never > 14 mm h⁻¹** | hard ceiling | Jennings & Jones 2015 |
| Net snowpack outflow, >97 % of peak-day hours | **< 3 mm h⁻¹** | hard ceiling | Jennings & Jones 2015 |
| Cumulative snowpack outflow, 10-day storm | **< 300 mm** | maritime | Jennings & Jones 2015 |
| Rain fraction of precipitation in the 26 largest HJA storms | **> 60 %** in every one | maritime ROS is rain-dominated | Jennings & Jones 2015 |
| Snowmelt share of TWI, 1996 PNW flood (`C_snow`) | **18.6 %** basin average — but the same paper notes this is *below* the **21–57 % measured at SNOTEL stations** for the same event (ref. 28 therein), the gap being because the domain is the whole **Willamette** basin, much of which is low and snow-free | km-scale land-surface model | Hao et al. 2025 |
| Snowmelt share of ROS runoff, maritime regions | **30–45 %** (Rockies 45 – >65 %) | WRF 4 km, 2000–2013 | Musselman et al. 2018 |
| Extreme (upper 0.1 %) runoff events with a ROS contribution | **70 %** in ROS-affected regions | but ROS runoff is **<10 %** of total extreme flood runoff | Li et al. 2019 |
| ROS "flood potential" definition | rain ≥ **10 mm d⁻¹**, SWE ≥ **10 mm**, melt ≥ **20 %** of (rain+melt) | the de facto standard | Musselman et al. 2018 |
| ROS water-available-for-runoff change, Cascade Mountains, RCP8.5 PGW | **+20 % to >100 %** | 55 % of 106 basins gain >20 % | Musselman et al. 2018 |
| Change in ROS timing under warming | top-10 events up to **3 months earlier** | spring → winter | Musselman et al. 2018 |
| 1996 PNW flood runoff under +5 K | **167.2 → 240.5 mm (+44 %)**; **+59 % per K above 1,500 m**; largest increase **~226 mm at 1,850 m** | storyline simulation | Hao et al. 2025 |
| Rain–snow 50 % air-temperature threshold, Cascades/Pacific coast | **0.6–1.5 °C** (NH mean 1.0 °C) | 17.8 M observations | Jennings et al. 2018 NC |
| Threshold sensitivity to humidity | **−0.8 °C per +10 % RH** | 0.7 °C at 90–100 % RH to 4.5 °C at 40–50 % | Jennings et al. 2018 NC |
| Bright band below free-air 0 °C isotherm | **230–237 m mean, 122–427 m range** | northern California | White et al. 2010 via Minder 2011 |
| Melting distance `Δ_melt` vs precipitation rate | **60 m (weak) → 148 m (3.5 mm h⁻¹) → >300 m (intense)** | column + WRF | Minder et al. 2011 |
| Total simulated snow-line depression `d` | **267 m** (`d_0C` 142, `d_S` 221) | idealised windward ridge | Minder et al. 2011 |
| Snowpack loss per 1 °C, western Cascades of **Washington** | **15–18 %** annual accumulation, via ~200 m snow-line rise | modelled | Minder 2010b via Minder 2011 |
| Runoff response to a 610 m in-storm snow-line rise | **tripled** | 3 northern California basins | White et al. 2002 via Minder 2011 |
| Canopy snow interception, maritime | **~60 %** of snowfall; capacity **≥ 40 mm SWE** | Umpqua NF, 1,200 m | Storck et al. 2002 |
| Fate of intercepted snow | **~72 % meltwater drip / ~28 % mass release** | maritime | Storck et al. 2002 |
| Canopy sublimation, maritime | **~1 mm d⁻¹, ~100 mm season (~5 % of winter P)** | not an important term here | Storck et al. 2002 |
| ROS SWE loss, open vs beneath canopy | **86.9 mm vs 60.4 mm (open +44 %)** | the only significant ROS in 3 yr | Storck et al. 2002 |
| Clearcut vs forest ROS melt, HJA 900 m | **+40 % melt**; **+21 % outflow** largest event; SWE **2–3×** | plot scale | Berris & Harr 1987 |
| Forest-harvest effect on **>1-year** peaks | **+10–20 %, small basins only**; does not explain large-basin ROS peaks | 1,000+ peaks, 1953–2006 | Jones & Perkins 2010 |
| ROS vs rain water delivery to soils | ROS delivers **75 % more**; >10-yr ROS peaks **~2× rain peaks in large basins** | western Cascades | Jones & Perkins 2010 |
| Burned vs unburned ROS meltwater | **14.3 vs 6.2 mm d⁻¹**; single event **151 vs 39 mm SWE (+287 %)** | W. Oregon Cascades | Ebel & Gleason 2026 |
| Snow drought thresholds (operational) | dry: SWE ≤ P30 **and** accumulated P below median; warm: SWE ≤ P30 **and** accumulated P above median | daily, percentile-based | Hatchett et al. 2022 |
| PNW warm snow drought WY2015 | P **70–120 % of normal**, 1 Apr SWE **~50 %**, winter T **+3.0 °C** | the reference case | Harpold et al. 2017 |
| "At-risk" snow, PNW, 0 °C threshold | **~9,200 km², ~6.5 km³ of water** | vulnerable to rain conversion | Nolin & Daly 2006 |
| **Western WA SNOTEL, active** | **31 sites**, median **3,900 ft**, only **3 below 3,000 ft**, **1 below 2,000 ft** | fetched from AWDB 2026-08-24 | this entry |
| **Western WA SNOTEL SWE, 2025-12-11** | **14 % of median below 4,500 ft** (10 of 20 sites at 0.0 in); composite 44 % | Event Zero eve | this entry |
| **Western WA SNOTEL SWE, 2026-04-01** | composite **55 % of median** with accumulated precipitation **105–138 % of median at every station** | textbook warm snow drought | this entry |

### 3.1 The two datasets fetched for this entry

**A. Western Washington SNOTEL elevation distribution** (NRCS AWDB
`/stations?stationTriplets=*:WA:SNTL&activeOnly=true`, retrieved 2026-08-24). 78 active WA sites;
31 in Puget Sound HUC8s 17110004–17110015. Elevation distribution of all 78: 1 % below 2,000 ft,
6 % 2,000–3,000, 36 % 3,000–4,000, 31 % 4,000–5,000, 26 % above 5,000. Western WA subset: min
1,680 ft (Hozomeen Camp, far upper Skagit at the Canadian border), median **3,900 ft**, max 6,490 ft.

**The transient snow zone in which maritime ROS floods are generated is roughly 1,000–4,000 ft. The
median western-Washington SNOTEL sits at the top of that band and only one site sits inside its
lower half.** (FACT — dataset arithmetic reproduced above.) Three basins are effectively
single-station: Skykomish (Stevens Pass only), Sauk (Decline Creek, record begins 2018-11) and
Stillaguamish (Deer Pass, record begins 2020-12 — **too short for a climatology**). Snoqualmie has
three sites (Skookum Creek, Alpine Meadows, Olallie Meadows) but all lie within 3,320–4,010 ft.
AWDB returns **no median at all** for Decline Creek or Deer Pass, so any percentile- or
percent-of-median product is uncomputable for the Sauk and the Stillaguamish today.

**B. WY2026 SWE and accumulated precipitation vs median, western WA** (AWDB `/data`,
`elements=WTEQ,PREC&duration=DAILY&centralTendencyType=MEDIAN`, retrieved 2026-08-24):

| Date | Composite SWE (Σvalue/Σmedian) | Below 4,500 ft | Accumulated precipitation |
|---|---|---|---|
| **2025-12-11** (Event Zero) | 44 % of median (n=28) | **14 % of median (n=20)** | 113–194 % of median (n=27) |
| **2026-04-01** | 55 % of median (n=26) | — | **105–138 % of median at every station** |

Individual western-WA sites on 2025-12-11: Alpine Meadows (3,500 ft) **0.0 in vs 10.2 median**;
Skookum Creek (3,320 ft) **0.0 vs 6.1**; Rex River (3,810 ft) **0.0 vs 5.9**; Olallie Meadows
(4,010 ft) **0.0 vs 12.6**; Stevens Pass (3,940 ft) **1.5 vs 9.6 (16 %)**. Against that, crest and
leeward North Cascades sites read **Harts Pass 174 %, Brown Top 134 %, Rainy Pass 128 %, Swamp Creek
131 %**. On 2026-04-01, Elbow Lake (3,050 ft, Nooksack) held **8.0 in vs a 40.0 in median — 20 %**
while its accumulated precipitation was **113 % of median**.

This is Harpold's warm snow drought reproduced station by station, and it independently confirms the
Event Zero framing in `HYDROLOGY.md` §12: the December 2025 floods were **rain on bare ground up to
at least 4,000 ft in the maritime Cascades**, not rain on snow.

---

## 4. What is settled, what is emerging, what is contested

### Settled (established)

1. Cold content must be paid, then holding capacity filled, before matrix outflow; the equation and
   `c_i` are standard.
2. Condensation onto a melting pack releases ~7.5× the energy needed to melt the same mass; latent
   heat is the largest single turbulent term when the air is warm, moist and windy.
3. Rain's own heat is a minor **mass** contributor (~7.5 % of rain depth at ΔT = 6 K).
4. Maritime ROS floods are **rain-dominated**: >60 % of storm precipitation as rain in every one of
   the 26 largest H.J. Andrews events; snowmelt 18.6–45 % of total water input by three independent
   methods.
5. Snowpack outflow rates are bounded at roughly 10–14 mm h⁻¹ in maritime packs.
6. Precipitation-phase thresholds vary systematically with humidity; maritime thresholds are near
   1 °C, and humidity-aware methods beat temperature-only methods.
7. The mountainside snow line sits hundreds of metres below the free-air freezing level, and the
   offset grows with precipitation intensity.
8. Canopy interception in maritime forest is ~60 % of snowfall, released mostly as drip; sublimation
   is a minor maritime term.
9. Warm vs dry snow drought are distinct states with opposite flood implications, and there is now
   an operational percentile definition.

### Emerging

1. **Phase interference / pressure-wave transmission** as the discriminator between an ordinary ROS
   event and an extreme one (Jennings & Jones 2015). No operational product represents it. It is the
   most promising unexploited signal in the domain.
2. **Preferential flow** as a first-order control on outflow timing, including the counter-intuitive
   result that stratified packs respond faster than isothermal ones.
3. **Burned forest as a ROS amplifier** — the effect measured by Ebel & Gleason 2026 (2.3× ROS melt)
   is larger than the classic clearcut effect and is spatially trackable from public fire perimeters.
4. **Elevation-band divergence under warming**: low elevations shift ROS → pure rain; mid and high
   elevations gain ROS. The transition band is moving up through exactly the Cascade elevations that
   generate western-WA floods.
5. **Divergent, non-monotonic responses of specific historic events to warming** (Hao et al. 2025):
   2017CA-Feb runoff peaks at +3 K then declines, while 1996PacN increases monotonically. Event
   identity matters more than regional averages.

### Contested

1. **Turbulent flux vs net radiation as the dominant ROS melt energy source.** Marks et al. 1998
   (60–90 % turbulent) vs Mazurkiewicz et al. 2008 (radiation largest, 33–55 %, and explicitly
   *"question the general perception of turbulent energy exchange dominance"*) vs Li et al. 2019
   (net radiation 68 % CONUS). **Unresolved. Depends on exposure, wind, and where in the event
   distribution you look.** The repo currently asserts one side as FACT.
2. **Advected rain heat's share.** <10 % (Trubilowicz & Moore, BC) vs 10–15 % (Mazurkiewicz) vs
   **29–44 % in persistent-melt events** (Jennings & Jones). The high value is exactly for the
   events that produce floods.
3. **Whether canopy removal materially raises basin-scale ROS peaks.** Plot scale: yes, 20–40 %.
   Basin scale: Jones & Perkins 2010 find small-basin effects of 10–20 % on >1-year peaks that "do
   not account for" large-basin ROS peaks; Brandt et al. 2022 call the canopy literature
   inconclusive. **Treat basin-scale clearcut amplification as unproven.**
4. **Whether ROS flood risk in the maritime PNW rises or falls.** Musselman et al. 2018 project
   +20 % to >100 % ROS runoff for the Cascade Mountains; Maina & Kumar 2025 project western-US ROS
   impacts becoming "twice lower" through snowpack loss and rainfall intensification; Hao et al. 2025
   find the 1996 PNW event's runoff rising 44 % at +5 K. **These are not the same question**: ROS
   *frequency* falls at low elevation, ROS *event runoff* rises where snow persists, and total flood
   risk may rise from rain alone regardless. Any statement that omits the elevation band is
   meaningless.
5. **Whether the "transient snow zone" is a useful concept at all.** Jennings & Jones: *"the
   transient snow zone implies a static area, when in fact the area undergoing melt is highly
   dynamic during storm events."* (FACT.)

---

## 5. Western Washington specificity — what transfers and what does not

**Transfers directly.** H.J. Andrews (western Oregon Cascades, 430–1,300 m, marine west coast,
>80 % of precipitation Nov–Apr) is the closest long-record analogue to the Snoqualmie, Skykomish and
Stillaguamish headwaters that exists. Berris & Harr 1987, Marks et al. 1998, Mazurkiewicz et al.
2008, Jennings & Jones 2015 and Jones & Perkins 2010 are all from this one forest, and their
conclusions should be treated as **regionally applicable, with the caveat that they all come from
one 64 km² basin**. Storck et al. 2002 (Umpqua NF, 1,200 m) is the same climate. Nolin & Daly 2006
and Minder (2010b) are PNW/Washington-specific by construction.

**Transfers with caution.** Musselman et al. 2018, Li et al. 2019, Hao et al. 2025 and Maina & Kumar
2025 are continental or global; their maritime results are the relevant ones and they are all
consistent in direction (maritime = lowest snowmelt fraction of ROS runoff, greatest sensitivity of
snow-line to warming).

**Does not transfer.** Jennings, Kittel & Molotch 2018 cold content is Colorado — continental, cold,
deep, radiation-driven spring melt. Its *equation* transfers; its *magnitudes* do not, and the
authors say so. Sierra Nevada work (Oroville 2017, ASO intercomparisons) has a different snowpack
depth regime and a different reservoir-operations context. Rockies ROS snowmelt fractions (45–>65 %)
are roughly double the maritime value and must never be used as a Cascade prior.

**Washington's own specifics that the Oregon literature does not capture.**

- **The Cascade crest is a hydroclimatic divide inside single basins.** The 2025-12-11 data show
  Skagit basin sites reading 0–9 % of median (Beaver Pass, Marten Ridge) on the maritime side while
  Harts Pass read 174 % on the crest. `DATA_SOURCES.md` S1 already flags Harts Pass as an
  east-crest proxy; the December data confirm this is not a technicality but a factor-of-twenty
  difference in the same HUC8.
- **Regulation interacts with snow state.** Ross/Diablo/Gorge and Baker sit above much of the Skagit
  snow; the Sauk does not. A snow signal on the Sauk is hydrologically live; the same signal above
  Ross is an operator's problem.
- **Recent fire in the flood-generating band.** Western WA has burned repeatedly in the transient
  snow zone (Bolt Creek 2022 in the Skykomish is the obvious example). Ebel & Gleason 2026 makes
  post-fire ROS a **measurable, mappable** basin state that Oregon-era doctrine did not consider.
- **The monitoring network is worse here than the literature assumes.** Three western-WA basins have
  a single SNOTEL, two of those records begin in 2018 and 2020, and the median site sits at the top
  of the ROS band.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 Doctrine

1. **Rewrite `HYDROLOGY.md` §7's ROS bullet.** It currently asserts as FACT that ROS melt comes
   "mostly from turbulent sensible and latent heat fluxes". The honest statement is: *melt energy
   partitioning in maritime ROS is contested; net radiation (longwave-dominated) leads in the event
   population and in wind-sheltered forest (33–68 %), while turbulent fluxes dominate (60–90 %) in
   wind-exposed extremes; advected rain heat ranges 10–44 % and is largest in the persistent-melt
   events that produce floods.* Keep the operational conclusion — **temperature, humidity and wind
   at pack elevation are forcing inputs** — but derive it from "turbulence discriminates the
   extremes", not from "turbulence dominates".
2. **Add a magnitude statement to the "SWE is storage, not hazard" bullet.** The buffering side is
   worth **~30–45 mm of water for a typical maritime pack (≈2.5 mm of cold content plus ~27–37 mm of liquid
   storage) against a 200–400 mm AR**. Without a magnitude, "the pack can buffer the storm" reads as
   a much stronger claim than the physics supports.
3. **Add an explicit snowmelt-fraction prior.** In maritime western Washington, snowmelt supplies
   **~19–45 %** of the water reaching the ground in a ROS flood; rain supplies the rest. State it,
   with the three sources and their spread, so no downstream feature can imply otherwise.
4. **Add hard rate ceilings.** Snowpack outflow **< 3 mm h⁻¹ net, < 10 mm h⁻¹ total, never above
   14 mm h⁻¹** — a range-validation rule on any derived melt quantity, exactly as
   `DATA_DOCTRINE.md` §7 handles other physical bounds.
5. **Demote the 1,000–4,000 ft transient snow zone from `HYDROLOGY.md` §2 to prose**, per Jennings &
   Jones. The derived dynamic fractions are the correct formulation. (Already recommended by the
   prior pass; the SNOTEL elevation dataset in §3.1 now gives it a second, independent reason: the
   band is not observed.)
6. **Add a three-level vocabulary to the glossary**: freezing level / atmospheric snow level /
   **mountainside snow line**, with the statement that they differ by hundreds of metres and that
   only the third one may be intersected with hypsometry.
7. **A SNOTEL pillow that does not fall during a ROS event is not evidence of no outflow.** Add this
   to §7; it is a real interpretation trap given liquid retention and intermittent snowfall.

### 6.2 Methods to build

| Method | What it computes | Why it is now justified |
|---|---|---|
| `method:snow-drought-state@1.0.0` | daily {none, dry, warm, warm-and-dry} per basin from (SWE percentile ≤ 30) × (accumulated-precipitation percentile vs median), with the US Drought Monitor D-scale sub-bands | Hatchett et al. 2022 gives an exact, published, percentile-based definition using **precisely the two AWDB elements the platform already ingests (WTEQ, PREC)**. This is buildable **today** and it is the single highest-value new derived feature in this domain. |
| `method:snow-line-offset@2.0.0` | replaces the constant 1,000 ft with a precipitation-intensity-dependent depression of the mountainside snow line below the NBM wet-bulb `SNOWLVL`, parameterised as `Δ_melt(pcp)` from Minder et al. 2011 (60 m weak → ~150 m at 3.5 mm h⁻¹ → >300 m intense) plus a mesoscale term | The NBM `SNOWLVL` field is a **column wet-bulb level, not a mountainside snow line**. On a windward Cascade slope the terrain intersection is O(100–250 m) lower, and the gap widens during the heaviest AR hours. Using `SNOWLVL` unadjusted biases rain-exposed fraction **low exactly when it matters**. |
| `method:swe-below-snow-line@1.0.0` | SWE at elevations below the forecast mountainside snow line, per basin — not percent of median | §2.8, §4.5 of the prior pass, and the 2025-12-11 dataset. Requires hypsometry (gap 6). |
| `method:pack-buffer-capacity@1.0.0` | `CC(SWE, T_pack) / λ_f + LWC_capacity × SWE`, in mm of water, per elevation band, with an explicit statement of how many hours of the forecast rain rate it absorbs | Turns "SWE is storage, not hazard" into a number a user can act on. SNODAS provides pack average temperature (parameter 1038, K) and SWE (1034); the equation is standard. |
| `method:snotel-elevation-coverage@1.0.0` | per basin: n sites, elevation span, **fraction of basin hypsometry within ±X ft of an observing site**, and an explicit "the ROS-generating band is unobserved" flag | The network gap is a first-class provenance fact, not a footnote. `DATA_DOCTRINE.md` §4 already says "no mapping configured" is a surfaced configuration state; this is its snow analogue. |

### 6.3 Data sources to add or re-scope

- **AWDB `TOBS`/`TAVG` and `SNWD`** (S1, already available, currently unused in v0). `SNWD` with
  `WTEQ` gives bulk density; `TOBS` is the only in-situ air temperature at pack elevation in these
  basins. Both are needed for any pack-state statement.
- **A wind and dewpoint source at pack elevation.** Neither exists in the ingest today. HRRR/NBM
  10 m wind and 2 m dewpoint interpolated to band elevations is the only realistic path; label it
  MODELED. This is the discriminating variable for extreme ROS (§2.4) and its absence is why the
  forcing surface cannot represent ROS at all today (`DATA_SOURCES.md` already concedes this).
- **Fire perimeters (MTBS / NIFC) intersected with the transient snow band.** New, cheap, public,
  and now backed by a 2.3× ROS-melt result (Ebel & Gleason 2026). A `burned_fraction_in_snow_band`
  basin attribute is a static-ish derived feature with real signal.
- **Snow-covered area (MODIS/VIIRS)** remains the missing half of the rain-on-snow-exposed fraction.
  Note the maritime caveat: optical SCA under the Cascade cloud deck during an AR is exactly when it
  is unavailable. Any ROS-exposed fraction must carry a "SCA age" and go UNKNOWN when the last clear
  view predates the storm.
- **SNODAS pack temperature (1038)** is already documented (S2) but not ingested; it is the only
  gridded cold-content input available. Carry its documented failure mode (unbounded SWE growth at
  Baker/Glacier Peak/Rainier cells) as a quality flag, not a correction.

### 6.4 Contracts

- `Driver.direction` needs a value distinct from `context_not_scored` for **snow-drought state**,
  which *is* a legitimate scored input once calibrated — but scored in the direction the physics
  says: **warm snow drought raises susceptibility, dry snow drought lowers it**, and *low SWE alone
  says nothing*. Encoding that requires a two-dimensional driver, not a scalar.
- Any melt or outflow quantity needs a `physical_ceiling` annotation (§6.1 item 4) so
  range-validation is declared with the variable rather than living in a parser.
- The snow-level driver's `label` should name **which of the three elevations** it is. Today the
  label says "basin mean of the NBM pointwise 50th-percentile snow level" — accurate about the
  product, silent about the fact that this is not the terrain intersection.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

| # | Repo claim | Status after this pass |
|---|---|---|
| 1 | `HYDROLOGY.md` §7: "Rain-on-snow runoff enhancement comes **mostly** from turbulent sensible and latent heat fluxes … (FACT — e.g. Marks et al. 1998)" | **CONTRADICTED as a general FACT.** True for wind-exposed extremes; false for the event population and for wind-sheltered forest, where net radiation leads (Mazurkiewicz et al. 2008: 33–55 %; Li et al. 2019: 68 % CONUS). Marks 1998 is a single-event result. Downgrade to a regime-dependent statement. |
| 2 | `HYDROLOGY.md` §7: "the heat content of the rain itself is a minor term (FACT)" | **QUALIFIED.** Minor in mass (~7.5 % of rain depth at ΔT = 6 K) and minor in energy in most events (<10–15 %), but **29–44 % of the energy budget in the persistent-melt events that produce extreme floods** (Jennings & Jones 2015). "Minor" is wrong for exactly the cases the platform exists to detect. |
| 3 | `HYDROLOGY.md` §7: "Working assumption: snow level ≈ freezing level − ~1,000 ft" | **SUPPORTED IN CENTRAL VALUE, WRONG IN FORM.** 250–450 m (800–1,500 ft) is the right central range, but the offset is **precipitation-intensity dependent** (60 m → >300 m for the melting-distance term alone) and the storm-to-storm range spans a full kilometre. A constant is biased during heavy AR hours. Also: the platform's primary input (NBM `SNOWLVL`) is a **wet-bulb column level**, to which the *mesoscale/terrain* depression (`d_S` ≈ 221 m in Minder's control) still has to be applied — an offset the repo does not currently apply to `SNOWLVL` at all. |
| 4 | `HYDROLOGY.md` §2: transient snow zone ≈ 1,000–4,000 ft (ASSUMPTION) | **CRITICISED IN THE LITERATURE AND UNOBSERVED IN THE NETWORK.** Jennings & Jones call the concept inadequate; the AWDB fetch shows only 1 of 31 western-WA sites lies below 2,000 ft and only 3 below 3,000 ft. Keep the dynamic derived fractions; delete the band as a parameter. |
| 5 | `susceptibility.py`: SWE driver carries `direction="context_not_scored"` because "more SWE is not more risk" | **CORRECT BUT INCOMPLETE.** The doctrine is right that SWE is unsigned. But **snow *drought state* is signed** — warm snow drought is a flood-relevant state (Harpold et al. 2017; confirmed by the WY2026 data in §3.1). The platform currently has no way to express "low SWE with above-normal precipitation is a *positive* susceptibility contribution", so it emits nothing where the science supports something. |
| 6 | `susceptibility.py`: `basin_swe_percent_of_median` is the SWE context driver | **QUALIFIED AS THE WRONG STATISTIC.** Three independent reasons (§4.5 of the prior pass) plus a new fourth: measured on 2025-12-11, the western-WA composite read 44 % while the flood-relevant sub-4,500 ft band read **14 %**. The statistic the platform prints would have understated the anomaly by a factor of three on the eve of the record crest. It is not merely uninformative — it is *misleading in the direction of calm*, which `DATA_DOCTRINE.md` §12 forbids. |
| 7 | `HYDROLOGY.md` §12: "near record-low statewide snowpack — so the response was rain on saturated soils, not snowmelt (FACT)" | **CONFIRMED AND SHARPENED WITH PRIMARY DATA.** Below 4,500 ft in the maritime Cascades, SWE on 2025-12-11 was **14 % of median with 10 of 20 sites at exactly zero**. The statement can be upgraded from "near record-low statewide" to a basin-band measurement. |
| 8 | `DATA_SOURCES.md` W8: offset default 1,000 ft, range 500–1,500 ft, sourced from local-media secondary citations, "an authoritative weather.gov/sew citation is an OPEN QUESTION" | **CLOSED, with peer-reviewed sources.** Minder et al. 2011 (and White et al. 2010, Kingsmill et al. 2008, Lundquist et al. 2008 therein) give the offset, its components, its precipitation dependence and its variance. Replace the KIRO 7 / MyNorthwest / OpenSnow citations with these. |
| 9 | `HYDROLOGY.md` §7: "Point observations (SNOTEL) are ground truth for their elevation and aspect" | **SUPPORTED, AND THE CONSEQUENCE IS MORE SEVERE THAN STATED.** With a median site elevation of 3,900 ft and one site below 2,000 ft, the network is ground truth for an elevation band **above** the one that makes the floods. The platform should say so explicitly rather than treating the gap as a coverage detail. |
| 10 | `packages/hydrology/forcing.py`: the snow-level driver is `direction=DIRECTION_CONTEXT`, "context only; not scored" | **CORRECT for a bare elevation, and it should stay that way.** But note that once hypsometry exists, *rain-exposed fraction* derived from it **is** a scored quantity with an unambiguous sign, and the "never scored" rule must not be inherited by the derived fraction. |

---

## 8. Open questions

1. **Maritime cold-content climatology.** No fetched study reports peak cold content for a Cascade
   or Olympic pack. Jennings et al. 2018 is Colorado and explicitly declines to generalise. Without
   it, `method:pack-buffer-capacity` has to lean on SNODAS pack temperature, which is modelled.
2. **Does the phase-interference signal (Jennings & Jones 2015) exist at the scale of a 500–3,000 mi²
   Washington basin, or is it a 64 km² phenomenon?** It was measured at Lookout Creek with three
   lysimeters covering 42 % of basin area. Nothing comparable exists in Washington. If it scales, it
   is the highest-value unexploited flood signal in the region; if it does not, it is a curiosity.
3. **What is the actual offset between the NBM wet-bulb `SNOWLVL` and the observed Cascade
   mountainside snow line?** Minder gives the physics for an idealised ridge. Nobody has verified it
   against NBM output over the Washington Cascades. This is a hindcastable question: NBM `SNOWLVL`
   percentiles vs SNOTEL sites transitioning from accumulation to ablation during ARs.
4. **Is there a usable maritime SWE remote-sensing product during an AR?** Optical SCA fails under
   cloud, passive microwave fails in wet/deep snow, SAR-based SWE retrieval is immature in wet snow,
   and airborne lidar (ASO) is neither continuous nor cheap. **Not independently fetched for this
   entry** (the search budget was exhausted before the remote-sensing sweep) — flagged as the
   largest unexamined sub-topic in this domain.
5. **How much of each western-Washington basin lies in the 1,000–4,000 ft band?** Unanswerable in
   this repo today: `NEXT_STEPS.md` gap 6 records that basin geometry is HUC8 unions with no
   hypsometry. Until 3DEP hypsometry exists, every rain-exposed and ROS-exposed statement is
   blocked. **This is the single largest structural blocker in the snow domain.**
6. **Do the Oregon canopy results hold in Washington's wetter, higher-relief Nooksack and Skagit?**
   All the maritime canopy/ROS numbers come from two Oregon sites at 900–1,200 m.
7. **Post-fire ROS in Washington specifically.** Ebel & Gleason 2026 is Oregon, n = 4 post-fire
   years, and its own streamflow signal was weak (0.05 percentage points). The plot-scale melt result
   is strong; the basin-scale consequence is unproven.
8. **Whether the NWRFC's operational snow model (SNOW-17 family) shares these biases**, and whether
   its ROS behaviour can be characterised well enough that model-agreement (Surface IV) can name a
   *snow-specific* divergence rather than a generic one. Not investigated here.

---

## 9. Sources

Independently fetched and read:

- [Musselman, K. N., Lehner, F., Ikeda, K., Clark, M. P., Prein, A. F., Liu, C., Barlage, M., & Rasmussen, R. (2018). Projected increases and shifts in rain-on-snow flood risk over western North America. *Nature Climate Change*, 8, 808–812.](https://bpb-us-w2.wpmucdn.com/sites.coecis.cornell.edu/dist/f/423/files/2021/09/musselman18natcc.pdf) — full text extracted.
- [Jennings, K. S., Winchell, T. S., Livneh, B., & Molotch, N. P. (2018). Spatial variation of the rain–snow temperature threshold across the Northern Hemisphere. *Nature Communications*, 9, 1148.](https://pmc.ncbi.nlm.nih.gov/articles/PMC5861046/)
- [Jennings, K., & Jones, J. A. (2015). Precipitation-snowmelt timing and snowmelt augmentation of large peak flow events, western Cascades, Oregon. *Water Resources Research*, 51, 7649–7661.](https://andrewsforest.oregonstate.edu/pubs/pdf/pub4911.pdf) — full text extracted.
- [Mazurkiewicz, A. B., Callery, D. G., & McDonnell, J. J. (2008). Assessing the controls of the snow energy balance and water available for runoff in a rain-on-snow environment. *Journal of Hydrology*, 354, 1–14.](https://www.fs.usda.gov/pnw/pubs/journals/pnw_2008_mazurkiewica001.pdf) — full text extracted.
- [Minder, J. R., Durran, D. R., & Roe, G. H. (2011). Mesoscale controls on the mountainside snow line. *Journal of the Atmospheric Sciences*, 68, 2107–2127.](https://www.atmos.washington.edu/~durrand/pdfs/AMS/2011_Minder_etal_JAS.pdf) — full text extracted.
- [Storck, P., Lettenmaier, D. P., & Bolton, S. M. (2002). Measurement of snow interception and canopy effects on snow accumulation and melt in a mountainous maritime climate, Oregon, United States. *Water Resources Research*, 38(11), 1223.](http://dusk.geo.orst.edu/prosem/PDFs/dselkowitz_snowint.pdf) — full text extracted.
- [Brandt, W. T., Haleakala, K., Hatchett, B. J., & Pan, M. (2022). A review of the hydrologic response mechanisms during mountain rain-on-snow. *Frontiers in Earth Science*, 10, 791760.](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2022.791760/full) — full text extracted.
- [Jennings, K. S., Kittel, T. G. F., & Molotch, N. P. (2018). Observations and simulations of the seasonal evolution of snowpack cold content and its relation to snowmelt and the snowpack energy budget. *The Cryosphere*, 12, 1595–1614.](https://tc.copernicus.org/articles/12/1595/2018/)
- [Hatchett, B. J., Rhoades, A. M., & McEvoy, D. J. (2022). Monitoring the daily evolution and extent of snow drought. *Natural Hazards and Earth System Sciences*, 22, 869–890.](https://nhess.copernicus.org/articles/22/869/2022/)
- [Harpold, A. A., Dettinger, M., & Rajagopal, S. (2017). Defining snow drought and why it matters. *Eos*, 98.](https://eos.org/opinions/defining-snow-drought-and-why-it-matters)
- [Maina, F. Z., & Kumar, S. V. (2025). Global patterns of rain-on-snow and its impacts on runoff from past to future projections. *Nature Communications*, 16.](https://www.nature.com/articles/s41467-025-59855-3)
- [Hao, D., Bisht, G., Xu, D., Kumar, M., & Leung, L. R. (2025). Divergent responses of historic rain-on-snow flood extremes to a warmer climate. *Communications Earth & Environment*, 6.](https://www.nature.com/articles/s43247-025-02354-6)
- [Ebel, S. C., & Gleason, K. E. (2026). Forest fires increase vulnerability to midwinter rain-on-snow snowmelt in the western Oregon Cascades. *Environmental Research Communications*, 8(3), 031011.](https://iopscience.iop.org/article/10.1088/2515-7620/ae550d)
- [NSIDC (2026). SNODAS Data Products at NSIDC, G02158.](https://nsidc.org/data/g02158)
- **NRCS AWDB REST API**, `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations` and `/data`, retrieved 2026-08-24 — the two datasets and all arithmetic in §3.1.

Read via a fetched secondary source or search result, **not independently fetched** — treat the
numbers as INFERENCE-grade and re-verify before they enter a method:

- Marks, D., Kimball, J., Tingey, D., & Link, T. (1998). The sensitivity of snowmelt processes to climate conditions and forest cover during rain-on-snow: a case study of the 1996 Pacific Northwest flood. *Hydrological Processes*, 12, 1569–1587. — **not independently fetched**; the 60–90 % turbulent-flux figure is reported consistently by Brandt et al. 2022 and Mazurkiewicz et al. 2008, both of which were fetched.
- Marks, D., Link, T., Winstral, A., & Garen, D. (2001). Simulating snowmelt processes during rain-on-snow over a semi-arid mountain basin. *Annals of Glaciology*, 32, 195–202. — **not independently fetched**; note that this paper is a **semi-arid** basin, so the prior repo pass's attribution of the "60–90 %" PNW figure to Marks et al. 2001 rather than Marks et al. 1998 should be corrected.
- [Berris, S. N., & Harr, R. D. (1987). Comparative snow accumulation and melt during rainfall in forested and clear-cut plots in the western Cascades of Oregon. *Water Resources Research*, 23(1), 135–142.](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/WR023i001p00135) — **paywalled**; the 2–3× SWE, +40 % melt and +21 % outflow figures come from the Andrews Forest publication record and the Frontiers review.
- [Harr, R. D. (1986). Effects of clearcutting on rain-on-snow runoff in western Oregon: a new look at old studies. *Water Resources Research*, 22(7), 1095–1100.](https://andrewsforest.oregonstate.edu/publications/681) — **not independently fetched**.
- [Jones, J. A., & Perkins, R. M. (2010). Extreme flood sensitivity to snow and forest harvest, western Cascades, Oregon, United States. *Water Resources Research*, 46, W12512, doi:10.1029/2009WR008632.](https://research.fs.usda.gov/treesearch/39625) — **abstract only**; the 75 %, ~2×, and 10–20 % figures are from the USFS abstract.
- [Li, D., Lettenmaier, D. P., Margulis, S. A., & Andreadis, K. (2019). The role of rain-on-snow in flooding over the conterminous United States. *Water Resources Research*, 55, 8492–8513.](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2019WR024950) — **Cloudflare-blocked**; the 68 % net-radiation figure is quoted verbatim by Brandt et al. 2022 (fetched); the "70 % of extreme events / <10 % of extreme flood runoff" and "rainfall dominant on the west-facing slopes of the Cascades" findings come from the publisher abstract via search.
- [Roberts-Pierel, J., Raleigh, M. S., & Kennedy, R. E. (2024). Tracking the evolution of snow drought in the U.S. Pacific Northwest at variable scales. *Water Resources Research*, 60.](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023WR034588) — **Cloudflare-blocked**; only the abstract's methodological framing (point → HUC6 aggregation, in situ + gridded + optical remote sensing) was obtained. **Its PNW-specific snow-drought-type frequencies remain unread and should be the first target of a follow-up pass.**
- [Nolin, A. W., & Daly, C. (2006). Mapping "at-risk" snow in the Pacific Northwest. *Journal of Hydrometeorology*, 7, 1164–1171.](https://journals.ametsoc.org/view/journals/hydr/7/5/jhm543_1.xml) — **not independently fetched**; the 9,200 km² / 6.5 km³ figures are from the publisher abstract.
- [Lundquist, J. D., Neiman, P. J., Martner, B., White, A. B., Gottas, D. J., & Ralph, F. M. (2008). Rain versus snow in the Sierra Nevada, California: comparing Doppler profiling radar and surface observations of melting level. *Journal of Hydrometeorology*, 9, 194–211.](https://journals.ametsoc.org/view/journals/hydr/9/2/2007jhm853_1.pdf) — **HTTP 403**; the 73 m figure is quoted in Minder et al. 2011 (fetched).
- Trubilowicz, J. W., & Moore, R. D. (2017), British Columbia, 286 ROS events, advected heat <10 % — **not independently fetched**; quoted by Brandt et al. 2022.
- White, A. B., et al. (2002, 2010); Kingsmill, D. E., et al. (2008); Marwitz, J. (1983, 1987); Medina, S., et al. (2005); Minder, J. R. (2010b); McGurk, B. J., & Marsh, P. (1995); Juras, R., et al. (2017) — all **quoted from within Minder et al. 2011 or Brandt et al. 2022**, both fetched.

**Search budget note.** This pass consumed the session's WebSearch allowance before the remote-sensing
of SCA/SWE sub-topic could be swept. Sections 2–8 therefore under-cover satellite and airborne snow
observation, and Open Question 4 records that gap explicitly rather than filling it with unverified
recollection.
