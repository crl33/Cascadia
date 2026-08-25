# Sediment, geomorphic and cascading hazards; land use

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

Labels follow the repository convention: **FACT** = read on a page or PDF I fetched in this pass,
or computed here from a primary dataset I downloaded (source and query given); **INFERENCE** =
reasoned from cited facts; **ASSUMPTION** = a working simplification; **OPEN QUESTION** =
unresolved. Where a number comes from a source I could not open myself it is marked
*not independently fetched* and demoted to INFERENCE. The original computations in §5.4 and §5.5
were run on 2026-08-24 against the USGS annual-peak files and the USGS OGC Water Data API; the
exact endpoints and the analysis code are given so they can be re-run.

---

## 1. Headline

**Geomorphic processes do not make western Washington floods — they change what a given flood
does, and they do it slowly enough that the platform's *thresholds* drift while its *physics*
does not.** The operationally consequential fact in this whole domain is that the stage–discharge
relation on glacier-fed western Washington rivers is measurably nonstationary. I measured it:
regressing annual peak stage on log₁₀(peak discharge) for the upper half of the annual-peak
distribution at fifteen western Washington gauges and taking the Theil–Sen slope of the residual
against water year, the **Nooksack at Ferndale has gained +0.139 ft per decade of stage at a given
peak discharge over 1968–2024 (n = 31, p = 0.0001, residual sd 0.39 ft)** — about 0.8 ft of the
official stage scale consumed in 56 years by the riverbed rather than by water. Over the same
period, the non-glacial control gauges are flat: **Skykomish near Gold Bar +0.003 ft/decade
(p = 0.74)**, **Sauk near Sauk exactly 0.000 ft/decade over 1932–2017 (p = 0.88, residual sd
0.21 ft)**. The signal is real, it is confined to the basins with glaciated volcanic headwaters,
and it is already documented independently by USGS (Anderson & Konrad 2019; Anderson and others
2019; Czuba and others 2010).

The corollary matters more than the number. A stage threshold is a statement about *hydraulics*,
not about water, and its hydraulic meaning has a vintage. The platform's headroom computation is
correct in form (it refuses datum mismatches) and incomplete in fact: it has no concept of a
*rating epoch*, and two of the eight basins' gauges — Green near Auburn (12113000) and White near
Auburn (12100496) — return a **null `vertical_datum`** in USGS monitoring-location metadata while
others in the same set return NGVD29 and NAVD88 (FACT, queried 2026-08-24; see §5.6 for the
distinction between the site-altitude datum and the gauge datum for stage).

The acute geomorphic hazards — lahars, glacial outburst floods, landslide dams, post-fire debris
flows — are real, are well documented for these exact valleys, and are **mostly not the
platform's problem**, because in every case an authority already owns the product and the
platform's doctrine is to link rather than model. The two exceptions where the platform is
structurally blind are (a) **short-duration rainfall intensity** (I₁₅ / I₆₀), which is the
controlling variable for every debris-flow product in the region and which the forcing surface
does not carry at all, and (b) **gauge-record integrity**, where I found that the Skagit near
Mount Vernon has debris-fouled hydraulic control in **29 % of gage-height field visits** versus
3 % at Skykomish near Gold Bar (FACT, computed here from USGS field measurements).

Finally, the long-running forest-harvest-and-floods literature — the one place where a land-use
covariate could plausibly enter a flood model — says, in its own state-of-science synthesis, that
harvest effects **cannot be detected at return periods longer than about 6 years** and are
**smaller than interannual variability at basin scale** (Grant and others 2008). That conclusion
is contested on statistical grounds by Alila and others (2009), whose frequency-paired reanalysis
finds the opposite sign of trend with return period. The honest platform position is: record
forest and road state as static basin attributes, cite both sides, and keep them out of the hazard
computation.

---

## 2. Mechanisms (the physics, stated properly)

### 2.1 Where the sediment comes from: paraglacial supply from glaciated stratovolcanoes

Three of the platform's eight basins have headwaters on a glaciated stratovolcano:

| Basin | Volcanic/glacial headwater | Regulated between source and outlet? |
|---|---|---|
| Nooksack | Mount Baker (Middle Fork, North Fork via Deming/Coleman glaciers), Mount Shuksan (NF) | **no** — unregulated to Bellingham Bay |
| Skagit | Glacier Peak via the **Sauk/Suiattle/White Chuck**; Mount Baker via the **Baker River** | Sauk **unregulated**; Baker impounded by Upper/Lower Baker |
| White | Mount Rainier (Emmons/Winthrop glaciers) | Mud Mountain Dam — but it passes fine sediment (§2.10) |

The Skykomish, Snoqualmie, Stillaguamish, Green and Cedar have no stratovolcano in their
headwaters (FACT, basin geography; see §5 for what that predicts and §5.4 for the measurement
that confirms it).

Mount Baker carries **~1.8 km³ of ice, more than all other Cascade volcanoes except Rainier
combined** (FACT — USGS Mount Baker pages, corroborating the figure already in the repo's prior
pass). The relevant mechanism is *paraglacial* (Church & Ryder 1972, cited by Anderson & Konrad
2019, not independently fetched): glacier retreat exposes unconsolidated, unvegetated,
oversteepened moraine and edifice material that is then evacuated by fluvial and mass-movement
processes at rates far above the long-term denudation rate. Anderson & Konrad photograph and
describe exactly this: "deglaciated terrain down valley of the Deming Glacier on Mount Baker,
which feeds into the Middle Fork Nooksack River. Exposed slopes of unconsolidated material in the
foreground are about **250 m high with an average cross-valley slope of about 25–30°**"
(FACT — Anderson & Konrad 2019, Figure 1 caption).

Supply from a stratovolcano is roughly an **order of magnitude larger** than from a forested
catchment subject to land use (FACT — Anderson & Konrad 2019 §4.1, citing Czuba, Olsen and others
2012). Anderson & Konrad also give a spatial argument that this is the dominant term in the
Nooksack: only about **10 % of the North Fork basin above their upstream gauge has ever been
logged since 1850**, and the North/Middle Forks (draining Baker) are "broad and braided,
indicative of high coarse sediment loads," while the unglaciated South Fork "is generally
narrower and has a meandering planform" (FACT — same section).

### 2.2 How supply changes reach the lowland: bed waves and signal celerity

A change in upstream coarse-sediment supply propagates downstream as a vertical adjustment of the
channel bed. Anderson & Konrad inferred bed elevation at seven USGS gauges from **shifting
stage–discharge relations** — the same residual quantity I compute in §5.4 — and found:

- bed elevation varies over a range of **0.5–1.0 m** at each gauge;
- decadal trends run at **0.2–0.4 m per decade** (≈ 0.7–1.3 ft/decade), persisting years to decades;
- the signal originates above the uppermost North Fork gauge and **propagates downstream at
  1–4 km/yr**, with celerity scaling on channel slope as
  `celerity (km/yr) = 46.63 · S^0.51` (r² = 0.94 power law; a linear fit gives r² = 0.98)
  using the *harmonic* mean slope over 1-km subreaches;
- lag between the climate forcing and the channel response is **20 years at the upper North Fork
  gauge and ~70 years at the gauge near the mouth**; the signal takes **~50 years to travel 90 km**;
- climate explains **slightly more than 40 %** of the variance in channel elevation at the five
  arrangeable gauges;
- warm/dry periods → subsequent **aggradation**; cool/wet periods → subsequent **incision**;
- and — the paper's headline claim — there is **no apparent attenuation** of the signal over 90 km:
  "This is, to our knowledge, the first observation of a basin-scale channel bed response that has
  not involved substantial attenuation moving downstream."

(All FACT — Anderson & Konrad 2019, §§3.1–3.3, 4.3, Tables 2–3.)

The practical statement of this for an operational system: **channel change in the upper river is
a forecast of channel change in the lower river 30–50 years later.** That is a genuinely usable
decadal predictor and it is computed from data the platform can already ingest.

Two caveats the authors state themselves. First, the low amplitude (~1 m) is probably *why* the
wave translates rather than disperses; the Sacramento hydraulic-mining and Redwood Creek analogues
aggraded many metres and behaved differently. Second, glacier extent and flood intensity both
shifted with the PDO in the late 1970s, so correlation cannot separate the two mechanisms:
"assessing causal physical links through correlation of time series may be complicated given that
multiple potentially important physical processes are likely responding to the same broad climatic
forcing" (FACT — Anderson & Konrad 2019 §3.4).

### 2.3 How bed elevation becomes stage: the conveyance term

For a given discharge `Q`, uniform-flow hydraulics give

```
Q = (1/n) · A(h) · R(h)^(2/3) · S^(1/2)
```

so the stage `h` that conveys `Q` rises if the cross-sectional area `A` shrinks (aggradation,
narrowing, levee confinement), if roughness `n` rises (wood, vegetation, coarser bed), or if the
energy slope `S` falls (backwater from tide, from a downstream constriction, from delta
progradation). Every geomorphic process in this corpus enters the platform through exactly this
equation, and every one of them is a *slow* variable relative to the storm.

Two consequences the doctrine does not currently state:

1. **A stage threshold has a vintage.** NWS action/minor/moderate/major stages were set against a
   channel geometry that existed on a date. If the bed rises 0.14 ft/decade, a threshold set in
   1990 corresponds to a smaller discharge in 2026 than it did when it was set. (INFERENCE from
   the equation plus §5.4.)
2. **Flow-defined thresholds are immune to this and stage-defined thresholds are not.** NWS
   defines the Green at Auburn and White at Auburn categories in **flow** because those reaches are
   regulated (repo `HYDROLOGY.md` §2). The White near Auburn is also the reach with the largest
   measured aggradation in the region (§3), so the flow basis happens to be doubly correct there.
   (INFERENCE.)

Delta progradation is a distinct, quantifiable term. For the Nooksack, Anderson and others (2019)
compute that the observed **0.11 mi/decade of delta extension from 1887 to 1998**, at bed slopes of
0.0002 / 0.0002 / 0.00063, implies aggradation of **0.11, 0.13 and 0.37 ft/decade** at Ferndale,
Brennan and Marine Drive respectively *from delta growth alone* (FACT — SIR 2019-5008). Note that
this is the same order as the total drift I measure at Ferndale (§5.4): most of the Ferndale signal
may be base-level, not supply.

### 2.4 Lahars

A lahar is a rapidly flowing mixture of rock debris and water from a volcano; by the Washington
Geological Survey's own convention (FACT — Mickelson & Allen 2022, Appendix A) the sediment
concentration by volume separates **flood (<5 %) → hyperconcentrated flow (~5–60 %) → debris flow
(>50 %)**. The taxonomy matters because most reported "debris flows" in the media are actually
hyperconcentrated flows.

Documented for the platform's valleys:

- **Glacier Peak → Sauk/Skagit/Stillaguamish.** About **13,000 years ago** eruption-generated
  lahars ran down the White Chuck, Suiattle and Sauk, then down both the North Fork Stillaguamish
  and the Skagit to the sea, depositing **more than 2 m (7 ft) of sediment at Arlington, more than
  95 km (60 mi) downstream**. Within the last 2,000 years, lahars have run the entire length of the
  White Chuck and part way down the Suiattle. Darrington, Rockport, Concrete, Sedro-Woolley,
  Burlington, Mount Vernon and La Conner all sit in valleys inundated in the geologically recent
  past. (FACT — USGS Glacier Peak lahar hazards page, fetched.) The USGS page gives **no volume
  estimates and no numerical recurrence intervals** — frequency is stated qualitatively.
- **Mount Baker → Nooksack / Baker–Skagit.** Small lahars occur frequently and typically without
  an eruption, travelling a few km; moderate ones **10–14 km**; large ones **>15 km**. About
  **6,700 years ago** large lahars flowed at least **12 km down Sulphur Creek and the Middle Fork
  Nooksack** and were **at least 100 m (325 ft) deep** in the Middle Fork. Non-eruptive triggers
  are named explicitly: regional earthquakes, slope failure of hydrothermally altered rock,
  increased subsurface heat, and **sudden release of glacial water (glacial outbursts)**.
  (FACT — USGS Mount Baker lahars page, fetched.)
- **Mount Rainier → White River.** The Osceola Mudflow, ~5,600 yr BP, filled White River valleys
  to depths of **more than 100 m**, ran **more than 120 km**, and covered **more than 200 km²** of
  the Puget Lowland (INFERENCE — this figure appears consistently across USGS and secondary
  sources but I could not fetch the USGS Professional Paper itself; treat as
  *not independently fetched*).

The mechanism that connects lahars to the platform's *flood* problem is not the lahar itself but
the decade-scale sediment pulse afterwards. USGS states for Mount Baker that while initial
deposition takes minutes to hours, "long-lasting down-valley transport of sediment occurs over a
period of decades and affects fish habitat, flood risk, gravel mining, and drinking water"
(FACT — quoted in the repo's prior pass from the USGS Mount Baker page).

### 2.5 Glacial outburst floods (jökulhlaups) and moraine failures

A jökulhlaup is a sudden discharge of water stored within, under or at the margin of a glacier.
On Mount Rainier these have been "the most destructive natural events" of the twentieth century;
between 1930 and 1980 floods were reported from five glaciers, mostly Nisqually, Kautz and South
Tahoma; **one or more may occur in any given year**, and since 1985 **more than 30 debris flows
have run down Tahoma Creek** (INFERENCE — consistent USGS/academic sources, but the Annals of
Glaciology and Journal of Glaciology papers are paywalled and *not independently fetched*).
Triggers are unusually hot or rainy weather in summer/early autumn, i.e. **rapid meltwater or
rainwater input to the glacier bed** — not a winter AR.

The directly relevant Washington event for the platform's basins is **31 May 2013 on the Middle
Fork Nooksack**: a landslide in a Little Ice Age moraine at the Deming Glacier generated a debris
flow of an estimated **100,000 m³** that swept the upper Middle Fork, deposited boulders up to
~3 m across on a terrace ~4.5 m above water level, and affected turbidity along the entire river.
The event was recorded by a **PNSN seismometer on Mount Baker**, and the discharge pulse reached
the **Nugent's Corner streamgauge ~25 miles downstream a couple of hours later**
(INFERENCE — the PNSN blog and Mount Baker Volcano Research Center accounts are consistent and
were surfaced in search; I did not fetch the seismic waveform record itself).

This is the single most instructive case in the domain for platform design: a **non-meteorological
event produced a stage and turbidity anomaly at a USGS gauge**, in a basin the platform covers,
with a two-hour travel time, detected first by a seismic network the platform does not read.

### 2.6 Debris flows: two initiation mechanisms, and why the difference is everything

There are two distinct paths to a debris flow, and the Pacific Northwest is dominated by the one
that is *not* the one the operational models were built for:

| Path | Trigger physics | Controlling rainfall variable | Where it dominates |
|---|---|---|---|
| **Shallow landslide → debris flow** | soil saturation, pore-pressure rise, loss of root cohesion | *cumulative* rainfall over days, plus antecedent wetness | Pacific Northwest (both burned and unburned) |
| **Runoff-initiated** | rainfall rate exceeds infiltration capacity → rilling, sheetwash, channel scour, bulking | *short-duration intensity*, I₁₅ ≤ 30 min | southern California, Rockies, Interior Northwest |

Wall, Roering & Rengers (2020) state the regional baseline flatly: "runoff-initiated debris flows
are not common in the Pacific Northwest; **only one instance of a runoff-initiated debris flow has
been documented in the Eastern Cascades in Washington State**" prior to their study, and "shallow
landslides initiated via soil saturation and root strength decline are the predominant geomorphic
response to fire that is typical in the Pacific Northwest" (FACT — Wall and others 2020,
Introduction). Their case study (Black Crater, Oregon Cascades, one year after the 24,000-acre
Milli fire) is the first documented runoff-initiated post-fire debris flow in the Oregon Cascades:
**peak 15-min rainfall rate 25.4 mm h⁻¹**, against a measured post-fire soil infiltration rate with
a **geometric mean of ~24 mm h⁻¹** — i.e. the flow occurred precisely when rainfall rate crossed
infiltration capacity. Initiation was by dispersed rilling on **>30° slopes**, and the flow
travelled **>1.5 km** (FACT — Wall and others 2020, Abstract).

The general empirical form for rainfall thresholds is the Caine (1980) power law

```
I = α · D^β          I = mean rainfall intensity (mm/h), D = duration (h)
```

with α and β fitted regionally; Guzzetti and others (2008) compiled **2,626 events globally** and
found that the minimum triggering intensity decreases with duration approximately linearly in
log–log space over **10 min to 35 days** (INFERENCE — Guzzetti and others 2008 abstract via search;
the Landslides paper is paywalled and *not independently fetched*).

For **Seattle-area shallow landslides** — the closest thing the region has to a calibrated,
operational threshold — Chleborad, Baum & Godt (2006) fit a *cumulative* rather than
intensity–duration threshold:

```
P3 = 3.5 − 0.67 · P15          (inches)
```

where `P3` is 3-day (72 h) rainfall and `P15` the preceding 15 days (360 h); exceedance requires
**3.5 to 5.2 inches of total precipitation over the 18-day window**, and the threshold captured
**more than 90 % of historical multi-landslide days from 1978 to 2003** (INFERENCE — the equation
and statistics are quoted consistently in secondary literature; USGS OFR 2006-1064 returned 403 on
fetch and is *not independently fetched*). The form is the important part: **for maritime
western Washington the calibrated predictor is multi-day accumulation with antecedent memory, not
short-duration intensity** — the exact opposite of the post-fire runoff case.

### 2.7 Post-wildfire hydrologic change

Fire reduces infiltration capacity (hydrophobicity, loss of duff and litter, ash sealing),
eliminates canopy interception, and reduces root cohesion. The USGS emergency assessment product
that Washington DNR uses models a design storm with **peak rainfall intensity of approximately
one quarter inch in 15 minutes** (≈ 25.4 mm h⁻¹) and produces basin-level and channel-segment-level
combined hazard classes (Low / Moderate / High) from modelled probability and volume (FACT —
Mickelson & Allen 2022, WGS WALERT report). The underlying model is Staley and others (2017), a
logistic regression on peak 15-minute rainfall accumulation interacted with (i) the fraction of
upslope area burned at moderate/high severity on slopes ≥23°, (ii) basin-average dNBR/1000, and
(iii) soil KF-factor (INFERENCE — model form from the USGS pfdf documentation surfaced in search;
the code page returned 403 and the *Geomorphology* paper is paywalled, so *not independently
fetched*).

Two Washington-specific caveats are stated in the WALERT report itself and are load-bearing:

> "These models were not developed with data that [account for] the effect of rain-on-snow in a
> recently burned area. Debris flows and flash floods may occur during rain-on-snow events and not
> meet the predicted rainfall threshold." **All four fires in that report are within mapped
> rain-on-snow zones.** (FACT — Mickelson & Allen 2022.)

And DNR's own program page: current models "may be less accurate for Washington's geology and
climate" than for the regions they were built in (FACT — WA DNR post-wildfire debris flow page,
fetched).

Elevated hazard persists **2–5 years** after a fire; DNR's public guidance says "up to five years"
and USGS says "generally 2–5 years" (FACT — DNR page and USGS post-fire landing page, fetched).

The quantitative western-Cascades test is Selander and others (2025), who built burned (2020–22)
and unburned (1995–2022) debris-flow inventories around five 2020 Oregon fires: after the
wildfires, **annual rates of runoff-generated debris flows increased by 22 % and shallow
landslide-initiated debris flows decreased by 17 %**, yet **shallow landsliding remained the
dominant initiation mechanism in both burned and unburned environments**, and the southern-
California-calibrated USGS likelihood model showed degraded performance in western Oregon
(FACT — USGS publication page for Selander and others 2025, *ESPL*, doi:10.1002/ESP.70045, fetched;
the journal article itself is paywalled).

### 2.8 Landslide dams and their outburst

The reference case is in one of the platform's basins. On **22 March 2014 the State Route 530
(Oso) landslide** mobilised **8 million m³** of unconsolidated Pleistocene material and fully
impounded the North Fork Stillaguamish. Documented behaviour (all FACT — Anderson, Keith, Magirl,
Wallick, Mastin & Foreman 2017, USGS SIR 2017-5055, fetched):

- impoundment **8 m high**; the lake covered **1.5 km²** and extended **3 km** upstream (the
  commonly quoted **3.3 × 10⁶ m³** lake volume is *not* stated in SIR 2017-5055 — do not cite it
  to this report);
- **overtopped within 25 hours**, then steadily incised a new channel;
- by May 2014 (2 months) a **20–40 m wide, deeply inset channel** existed through the deposit;
  mean water-surface elevation through the deposit **fell 7 m** in that period and was **~1 m above
  the pre-landslide profile by July 2014**;
- the 2014–15 flood season, which included a ~2-year flood, widened the channel tens of metres and
  lowered the profile a further **0.5 m**;
- over 18 months the deposit delivered **820 thousand metric tons** of sediment, **77 % silt/clay,
  19 % sand, 4 % >2 mm**;
- at 5 km downstream, landslide sediment made up **20–40 % of bedload and 65–85 % of suspended
  load**; at 70 km downstream, **~600 of 1,440 thousand metric tons (30 %)** of the suspended load
  was landslide-derived;
- **~70 % of the eroded landslide sediment transited the entire basin into Puget Sound within weeks
  of entrainment**;
- downstream channel response was "modest and short-lived": a **~1 m aggradation wedge over the
  0.5 km** reach at and just below the western edge of the deposit and a **0.3 m pulse at 5 km**, both peaking within about a month.

The design lesson for the platform is precise and non-obvious: the **hydraulic** hazard of a
valley-blocking landslide in a maritime river of this size resolved in **hours to weeks**, not
years, and the **downstream flood-conveyance** consequence was small. What was large was the
*sediment* signal and the *local* hazard. A platform that only watches discharge would have seen a
25-hour anomaly and then nothing.

### 2.9 Large wood, log jams and the gauge record

Channel-spanning jams create backwater, force avulsion at fan apices, and change the hydraulic
control at gauging stations. The WGS WALERT report notes for Buck Creek that "the log jam at the
apex of the fan also increases the likelihood of channel avulsion, which could cause inundation on
a large part of the fan" (FACT — Mickelson & Allen 2022). The Skagit historical-peak literature
notes that "levee failures and log jams" complicate gauge measurements and estimates of the
disputed historic peaks (FACT, carried forward from the repo's prior pass). Modelling and flume
work reports upstream water-level rises of **up to 2 m** from jams and reach-scale effects on flood
peak height of **±4 %** for 1–5 km of engineered-log-jam restoration (INFERENCE — figures from
review summaries surfaced in search; primary papers *not independently fetched*).

The platform-relevant observation is not the hydraulics; it is that **USGS already records the
condition of the hydraulic control at every field visit**, and that record is queryable. See §5.5.

### 2.10 Forest harvest, roads and road drainage

**The state-of-science position (Grant, Lewis, Swanson, Cissel & McDonnell 2008, PNW-GTR-760 — all
FACT, fetched):**

- The largest reported increases are for the *smallest* storms: up to **90 % over control** for
  events with recurrence interval much less than 1 year; the increase decays roughly exponentially
  with event magnitude.
- The minimum detectable change in peak flow from streamflow measurements alone is about **10 %**.
- "The field and analytical methods represented by these studies … do not provide evidence that
  forest harvest increases peak flows for storms with recurrence intervals **longer than 6 years**."
- Range of reported increases: **0–40 %** in the rain and transient-snow zones, **0–50 %** in the
  snow zone, with zero/no-significant-change reported anywhere from 25 % to 100 % harvested.
- **Rain zone**: the *maximum* response line crosses the 10 % detection limit at ~**29 % harvested**
  (first detectable reported value at 40 %); the *mean* response line at ~**45 %**.
- **Transient snow zone**: the maximum no-roads response line crosses the detection limit at
  ~**15 % harvested**, mean at **19 %**.
- **Roads**: modelling for Washington watersheds suggests "an approximate **doubling** of the
  percentage change in peak flows attributed to harvest alone when road construction is included"
  (Bowling & Lettenmaier 2001, as cited).
- **Seasonality**: increases are greatest for **fall storms**, mechanistically because reduced
  post-harvest evapotranspiration leaves soils wetter going into the first storms.
- **Basin scale**: "No hydrologic mechanism exists by which peak flow increases, when measured as
  a percentage change, can combine to yield a higher percentage increase in peak flows in a larger
  basin," and for the few large-basin studies the increase is "**less than the inter-annual
  variability in streamflows** … the inter-annual variance swamps the land use signal."
- **Channel response**: "to date no field studies explicitly link peak flow increases with changes
  in channel morphology."

**Road drainage as a runoff-generating surface (Wemple, Jones & Grant 1996 — FACT, fetched).**
In Lookout Creek (62 km²) and Blue River (119 km²), western Cascades, with 1.9 km km⁻² road density
and 3.1 % of basin area in road surface: **more than 57 % of surveyed road length drained to the
stream network**, either via ditches to streams (34 % of the 62 km surveyed) or via culverts with
gullies incised below their outlets (24 %). Of 436 culverts examined, 35 % were ditch-relief
culverts draining to streams and 23 % had incised gullies. Gully incision is significantly more
likely below culverts on **>40 % slopes** with longer-than-average contributing ditch length. Net
effect: estimated drainage density rises from **3.0 → 4.1 km km⁻²** (Lookout) and **2.9 → 4.0**
(Blue River), i.e. **+21 to +50 %** depending on assumptions.

This is the mechanism the repo's prior pass correctly identified: in a landscape where
infiltration-excess runoff is otherwise absent, roads are a Hortonian surface *and* a
flow-routing shortcut.

**The statistical controversy (Alila, Kuraś, Schnorbus & Hudson 2009 — FACT, fetched).** Alila and
others argue that chronological pairing of peak flows (matching treatment and control events by
storm) answers the wrong question, because it estimates a change in magnitude conditional on an
input while floods are defined by *frequency*. Under frequency pairing at Fool Creek their
reanalysis finds "a 3-year event to become a 2-year, a 6-year to become a 3-year, a 13-year to
become a 6-year, a 19-year to become a 9-year, and a 30-year to become a 14-year event," i.e. **all
peak flows roughly doubled in expected frequency regardless of magnitude**, which "translates into
an **increasing** change in return period with increasing magnitude" — the reverse of the
conventional reading. At H.J. Andrews, WS1 (100 % clearcut, **no roads**) showed a **34 % upward
shift in mean** with a 4 % reduction in variance, and WS3 (25 % patch cut **with roads**) a **27 %
upward shift in mean with a 34 % increase in variance**; together these "roughly doubled the
expected frequency of 3- to 5-year and 5- to 40-year events, respectively."

Alila and others also state honestly the four uncertainties that could produce spurious tail
separation: plotting-position uncertainty for the largest observation, short post-treatment record,
regression extrapolation beyond the calibration range, and loss of variance from using a
calibration equation to generate the "expected" series.

**Where the debate stands.** The dispute is live and unresolved: Lewis, Reid & Grant commented on
Alila and others (2009) and were answered; Bathurst and Birkinshaw each commented on Green & Alila
(2014); Bathurst, Fahey, Iroumé & Jones (2020, *Hydrological Processes* 34:3295–3310) attempt a
field-evidence reconciliation, reporting that forested catchments show lower peak magnitudes at a
given frequency for small-to-moderate floods with **the curves converging for the largest floods**;
Alila's group continued into nonstationary stochastic paired-watershed methods through 2023, and
most recently **Kaluarachchi & Alila (2026, *Ambio* 55:1478–1492, doi:10.1007/s13280-026-02346-6)**
argue that the conventional chronological/deterministic approach — the one PNW-GTR-760 rests on —
poses "a non-relevant research question" and is therefore "scientifically indefensible", concluding
that forests mitigate floods of all sizes. That is a partisan contribution from one side, not a
resolution, but it is 2026 and it postdates everything else cited here
(INFERENCE — I could fetch the Alila 2009 PDF but the comments, replies and the 2020 HYP paper
returned 403; the titles, journals and years above are from search results and are
*not independently fetched*).

### 2.11 Urbanization and impervious area

Booth & Jackson (1997) found that lowland streams in western Washington show "the onset of readily
observable aquatic-system degradation at a remarkably consistent level of development, typically
about **ten percent effective impervious area**," with channel stability thresholds at the same
level (INFERENCE — widely and consistently quoted; the JAWRA paper is paywalled and *not
independently fetched*). The USGS Puget Sound trend study (Konrad & Booth 2002, WRIR 02-4040,
fetched) found trends in (1) the fraction of the year that annual mean discharge is exceeded
(TQmean) and (2) annual maximum discharge "evident in streams with the highest levels of urban
development but not in streams with the lowest," while annual mean discharge and 7-day low flow
showed **no consistent trends**, and all trends were **sensitive to the period of record** (FACT).

For this platform's basins the relevance is bounded: the mountainous headwaters that generate the
floods are essentially unurbanized. Urban land cover is material only in the **lower Green /
Duwamish** and **Cedar (Renton)** reaches, and there its documented signature is flashiness and
channel instability at the small-stream scale, not a change in the main-stem flood peak
(INFERENCE).

---

## 3. Quantitative anchors

| Quantity | Value | Context | Source |
|---|---|---|---|
| Sediment delivered to Puget Sound by rivers | **6.5 million tons/yr** (9.1 Mt/yr incl. shoreline erosion) | all Puget Sound tributaries, 13,000 mi² | USGS FS 2011-3083 (fetched) |
| Skagit annual sediment load | **2,800,000 tons/yr**; mean annual SSL **2.5 Tg/yr** at Mount Vernon | 3,200 mi²; 75 yr of record 1941–2015 | FS 2011-3083; Curran and others 2016 (both fetched) |
| Skagit share of Puget Sound fluvial sediment | **~40 %** | — | Curran and others 2016 |
| Skagit SSL seasonality | **74 %** delivered Oct–Mar | winter storm season | Curran and others 2016 |
| Skagit bedload fraction | **1–3 %** of total load | winter storm flows, medium-coarse sand | Curran and others 2016 |
| Skagit sediment-rating nonstationarity | **SSC–Q regression slope increased 66 %** between 1974–76 and 2006–09 | implies change in supply, hydraulics and/or hydrology | Curran and others 2016 |
| Skagit single-event dominance | WY2007 load 4.5 Tg, of which **1.8 Tg (40 %) from one flood** | daily automated sampling | Curran and others 2016 |
| Nooksack annual load | **0.78–1.17 Mt/yr, mean 0.97 Mt/yr** (WY2012–17); **93 % suspended, 7 % bedload** | Ferndale | USGS SIR 2019-5008 (fetched) |
| Nooksack suspended yield | **1,150 tons/mi²/yr** (Ferndale); **1,650 tons/mi²/yr** on the older 1.4 Mt/yr estimate — **highest per-area of 14 Puget Sound rivers** | — | SIR 2019-5008; Czuba and others 2011 |
| Nooksack bedload composition | **55 % sand, 45 % gravel**; bedload/total **7.8 %** | 2 Elwha-sampler measurements at Ferndale | SIR 2019-5008 |
| Nooksack channel storage change | active channel aggraded **1–2 ft** locally at Ferndale and Everson, 2005/06→2013/15; **2.3 ± 1.7 M yd³** net incision upstream of Nugent's Corner | repeat topo/bathy | SIR 2019-5008 |
| Nooksack bed-elevation trends at gauges | **~1 ft per decade**, total range 1–3 ft; propagation **0.5–2.5 mi/yr** | 7 gauges | SIR 2019-5008 |
| Nooksack stage trend without discharge trend | **+0.4 ft/decade** (Mar) and **+0.5 ft/decade** (Nov) in the 90th percentile of daily stage; **+0.3 ft/decade** in *median* daily stage (Nov) at Ferndale, 1992–2017, with **no trend in mean monthly discharge** | attributed to bed elevation | SIR 2019-5008 |
| Nooksack delta-progradation aggradation | **0.11 / 0.13 / 0.37 ft/decade** at Ferndale / Brennan / Marine Drive | from 0.11 mi/decade delta extension, 1887–1998 | SIR 2019-5008 |
| Bed-wave celerity | **1–4 km/yr**; `celerity = 46.63·S^0.51` (r²=0.94) | 5 Nooksack gauges over 90 km | Anderson & Konrad 2019 |
| Climate→channel lag | **20 yr** (upper NF) to **~70 yr** (mouth); ~50 yr to travel 90 km | — | Anderson & Konrad 2019 |
| Climate variance explained | **>40 %** of bed-elevation variance (JGR); **35–50 %** (SIR) | — | Anderson & Konrad 2019; SIR 2019-5008 |
| Mount Rainier river aggradation | **local maxima**, not river totals, 1984–2009: Puyallup up to **7.5 ft** just below the Orting gauge (basin-average at the gauges was **+1.1 / +0.9 / −0.3 ft**); White **2–6.5 ft** confined to RM 4–7.2 (**3.5 ft** at the near-Auburn gauge); Carbon "little or variable change" (~2 ft over 0.3 mi) | avg cross-section elevation change | USGS SIR 2010-5240 (fetched) |
| Peak aggradation rates | Nisqually near National **5.0 in/yr** (1998–2008) — *SIR Table 7 footnote: a similar magnitude of incision was measured 1989–1998, so this is not a secular trend*; **White near Auburn 1.8 in/yr** (1988–2009) | 12 gauges analysed | SIR 2010-5240, Table 7 |
| Non-glacial control gauges | Greenwater **0.1 in/yr** (sd 0.13 ft); South Prairie Creek **−0.1 in/yr** (sd 0.25 ft) | vs White nr Auburn sd 1.42 ft | SIR 2010-5240, Table 7 |
| White River conveyance loss | **20–50 %** decrease since 1984 (R Street Bridge → Lake Tapps return, 1-D model); separately, a **~25 %** drop at the White nr Auburn gauge **over the two months Nov 2008 → 8 Jan 2009** (overtopping discharge 19,600 → 14,700 ft³/s) — an event figure, *not* a cumulative one. The cumulative figure at that gauge is that stage for 9,000–12,000 ft³/s rose **~5.6 ft since 1987** | SIR 2010-5240 |
| Mount Baker ice volume | **~1.8 km³** — more than all Cascade volcanoes except Rainier combined | — | USGS / prior repo pass |
| Glacier Peak lahar reach | **>2 m** of deposit at Arlington, **>95 km** downstream | ~13,000 yr BP | USGS Glacier Peak page (fetched) |
| Mount Baker lahar depth | **≥100 m** deep in the Middle Fork Nooksack; ran **≥12 km** | ~6,700 yr BP | USGS Mount Baker page (fetched) |
| 2013 Deming Glacier debris flow | **~100,000 m³**; detected at Nugent's Corner **~2 h** later, 25 mi downstream | Middle Fork Nooksack, 31 May 2013 | PNSN / MBVRC (not independently fetched) |
| Oso landslide | **8 × 10⁶ m³** mobilised; **8 m** impoundment, lake **1.5 km²** extending **3 km** upstream; **overtopped in 25 h** | NF Stillaguamish, 22 Mar 2014 | USGS SIR 2017-5055 (fetched) |
| Oso sediment delivery | **820 kt** over 18 months (77 % silt/clay); **~70 %** transited the basin within weeks | — | SIR 2017-5055 |
| Oso downstream aggradation | **~1 m** wedge over 0.5 km; **0.3 m** pulse at 5 km; both peaked within ~1 month | "modest and short-lived" | SIR 2017-5055 |
| USGS post-fire design storm | **~0.25 in in 15 min ≈ 25.4 mm h⁻¹**; explicitly excludes rain-on-snow | as used for Bolt Creek | WGS WALERT 2022 (fetched) |
| Bolt Creek Fire burn severity | 12,070 ac at assessment (fire still active; ~11,500 ac classified): **51 % unburned/low, 32 % moderate, 16 % high** soil burn severity | King/Snohomish Cos., Sep 2022 | WGS WALERT 2022 |
| Post-fire hazard duration | **2–5 years** ("up to five years", DNR) | — | USGS / WA DNR pages (fetched) |
| Post-fire mechanism shift, W. Cascades | runoff-generated debris flows **+22 %/yr**, shallow-landslide-initiated **−17 %**; shallow landsliding still dominant in both | 5 Oregon 2020 fires, 1995–2022 | Selander and others 2025 (abstract fetched) |
| Post-fire runoff DF threshold, W. Cascades | peak **I₁₅ = 25.4 mm h⁻¹** vs infiltration geometric mean **~24 mm h⁻¹**; slopes >30°; runout >1.5 km | Milli fire, Black Crater, OR | Wall and others 2020 (fetched) |
| Intensity beats total (AR vs thunderstorm) | AR: **258.6 mm** total, peak **I₁₅ 16.8 mm h⁻¹** → streamflow only, ~2,000 m³ deposit. Thunderstorm: **33.4 mm** total, peak **I₁₅ 39.2 mm h⁻¹** → debris flow, **≥10,000 m³** | Dixie Fire, N. California | Thomas and others 2023 (fetched) |
| Seattle landslide cumulative threshold | **P3 = 3.5 − 0.67·P15** (inches); 3.5–5.2 in over 18 d; >90 % of multi-slide days captured | Seattle area, 1933–2003 | Chleborad and others 2006 (not independently fetched) |
| Harvest peak-flow detection limit | **10 %**; no evidence of effect beyond **6-year** return period | rain + transient snow zones | PNW-GTR-760 (fetched) |
| Harvest threshold for detectable change | **~29 %** harvested (rain zone, max line); **~15 %** (TSZ, no roads) | — | PNW-GTR-760 |
| Road effect | modelled **~doubling** of harvest-attributed peak-flow change when roads included | WA watersheds | Bowling & Lettenmaier 2001 via GTR-760 |
| Road–stream connectivity | **>57 %** of road length drains to streams; drainage density **+21–50 %** (3.0→4.1 km km⁻²) | 62 and 119 km² basins, W. Cascades OR | Wemple and others 1996 (fetched) |
| Frequency-paired harvest effect | 30-yr event → 14-yr; **+34 % mean shift** at HJA WS1 (100 % clearcut, no roads) | contested method | Alila and others 2009 (fetched) |
| Impervious-area degradation threshold | **~10 %** effective impervious area | W. Washington lowland streams | Booth & Jackson 1997 (not independently fetched) |
| Dec 2025 AR landslide response | **750 landslides** catalogued (154 clearinghouse forms); 73 identified by 19 Dec; **13 debris flows**; 8 WGS site visits near **Concrete**, 1 east of **Darrington** | Whatcom, Skagit, Snohomish Cos. | WA Geological Survey posts (fetched via curl) |
| WA landslide/fan inventory coverage | **>50,000** mapped hazards in 8 counties (60 % of state population); **27,000 alluvial fans mapped — east of the Cascades** | west-side fan mapping incomplete | WGS post (fetched) |
| **[original] Conveyance drift, Nooksack at Ferndale** | **+0.139 ft/decade** (1968–2024, n=31, p=0.0001, resid. sd 0.39 ft) | stage residual at fixed peak Q | §5.4, USGS peak file |
| **[original] Conveyance drift, Sauk near Sauk** | **+0.000 ft/decade** (1932–2017, n=44, p=0.88, resid. sd 0.21 ft) | 86-year stable rating, then a −0.8 ft step at 2018 | §5.4 |
| **[original] Skagit at Mount Vernon rating variance** | residual sd **0.25 ft (1948–2005) → 1.38 ft (2006–2024)** | 5.5× in *standard deviation* (≈30× in variance); WY2007–08 at −2.1 ft, WY2022 at +1.9 ft | §5.4 |
| **[original] Green near Auburn** | **−0.133 ft/decade (1948–2005, p=0.0002)** then **+0.298 ft/decade (1990–2025, p=0.0002)** | incision after Howard Hanson, later reversal | §5.4 |
| **[original] Debris-fouled gauge control** | Skagit nr Mount Vernon **29 %** of gage-height visits debris-affected; Skykomish nr Gold Bar **3 %**; Sauk **5 %** | USGS `control_condition` | §5.5 |

---

## 4. What is settled, what is emerging, what is contested

**Settled (established).**

1. Glaciated stratovolcano headwaters supply an order of magnitude more coarse sediment than
   forested catchments of comparable size, and the Nooksack has the highest per-area sediment yield
   of the major Puget Sound rivers.
2. Coarse-sediment supply changes propagate downstream as vertical bed adjustments, at celerities
   of km/yr scaling with channel slope, over decades.
3. Aggradation reduces flood conveyance, and this has already been measured as a **20–50 %**
   conveyance loss since 1984 on the lower White River between R Street Bridge and the Lake Tapps
   return. (Caveat: SIR 2010-5240 notes that significant gravel removal occurred in that same reach
   just before the 1984 baseline survey and "this reach seems to have filled in with sediment", so
   part of the measured 1984–2009 aggradation is recovery from mining rather than new supply.)
4. Shallow landsliding, not runoff generation, is the dominant debris-flow initiation mechanism in
   the Pacific Northwest, burned or unburned.
5. Post-fire debris-flow hazard is elevated for 2–5 years and is controlled by short-duration
   rainfall intensity in the settings where runoff initiation dominates.
6. Roads extend the drainage network substantially (+21–50 % drainage density in the studied
   basins) and are a Hortonian runoff surface in a landscape that otherwise has none.
7. Forest-harvest peak-flow effects are largest for the smallest storms and diminish with harvest
   intensity and event magnitude. (The *magnitude* claim is settled; see contested for the tail.)
8. Landslide dams on rivers of this size in this climate resolve hydraulically in hours to weeks.

**Emerging.**

1. That climate-driven sediment signals translate **without attenuation** at basin scale —
   Anderson & Konrad (2019) state this is the first such observation, and it depends on the low
   (~1 m) amplitude of the Nooksack signal.
2. That the western Cascades are shifting toward more runoff-generated post-fire debris flows —
   Selander and others (2025) measure a +22 % rate change but find the mechanism is still not
   dominant, and Wall and others (2020) document only the second such event in the region.
3. That the southern-California-calibrated USGS post-fire model needs regional recalibration for
   the maritime Northwest — asserted by both USGS (Selander and others 2025) and WA DNR.
4. That decadal channel change should be treated as a *predictable* rather than a random
   background — the 30–50-year lead time from headwater to lowland gauges is a testable forecast.

**Contested.**

1. **The statistics of forest harvest and floods.** Grant and others (2008) conclude no detectable
   effect beyond ~6-year return periods; Alila and others (2009) argue the chronological-pairing
   method used to reach that conclusion cannot detect a frequency change in principle, and their
   frequency-paired reanalysis finds effects that *grow* with return period. Comments from Lewis,
   Reid & Grant; from Bathurst; and from Birkinshaw dispute Alila's methodology in turn; Bathurst
   and others (2020) attempt reconciliation and report convergence of the curves at the largest
   floods. Grant and others (2008) state that the basin-scale effect is smaller
   than interannual variability; **Alila's camp does not concede this**, because it regards the
   magnitude-at-fixed-input comparison that produces it as the wrong frame (see Kaluarachchi &
   Alila 2026). The platform's reason for keeping land use out of the hazard computation is
   therefore *unresolved method*, not agreement between the camps.
2. **Whether glacier extent or flood intensity is the physical link** between climate and sediment
   supply in the Nooksack. Anderson & Konrad show both correlate with channel change since 1930 but
   *diverge* before 1930, when climate was cool/wet while Mount Baker glaciers continued to
   retreat — and the channel tracked climate, not glaciers.
3. **The upper tail of the Skagit peak record** (240,000 cfs in 1921, derived from a single 1923
   indirect measurement, later recalculated as ~6.2 % lower but not officially revised, ±15 % error
   bands) — carried forward from the repo's prior pass; it is contested precisely because it sets
   floodplain regulation.
4. **Whether dredging restores Nooksack conveyance.** A 1995 channel-capacity study is widely cited
   as requiring 2.7 million yd³ of excavation for a 5-year flood and 11.4 million yd³ for a 100-year
   flood; Washington Department of Ecology's Scott McKinney: "You can dig it out at a given
   location, but it will fill back in, that's what the river is going to do." (INFERENCE — the
   1995 KCM study is *not independently fetched*; the quotation is from the Encyclopedia of Puget
   Sound article, fetched.)
5. **Whether the aggradation signal at Ferndale is supply-driven or base-level-driven.** SIR
   2019-5008's own delta-progradation calculation (0.11 ft/decade at Ferndale) is the same order as
   the total observed drift, and the report explicitly flags a mismatch: the downstream-translating
   North Fork signal "would account for recently observed aggradation at Everson and Ferndale but
   not the observed incision in unconfined reaches upstream of Nugent's Corner."

---

## 5. Western Washington specificity

### 5.1 What transfers

- **Paraglacial sediment supply** — Mount Baker, Glacier Peak and Mount Rainier are the same class
  of source as the Alpine and Coast Mountain systems in the literature, and the Alder Lake
  (Rainier) and Cheakamus Lake (BC) records corroborate the Nooksack chronology (Anderson & Konrad
  2019 §4.2).
- **Bed-wave translation and slope-scaled celerity** — the Redwood Creek (northern California)
  analogue behaves the same way qualitatively.
- **Landslide-dam mechanics** — overtopping-and-incision is generic; the Oso timescale is a
  function of river power, which is high here.
- **The Caine power-law form** for rainfall thresholds — the form transfers; the coefficients do
  not.

### 5.2 What does not transfer

- **Post-fire runoff-generated debris flows.** This is the single most important negative transfer
  in the domain. Thomas and others (2023) is the cleanest demonstration: an atmospheric-river storm
  delivering **258.6 mm** of rain with a peak I₁₅ of only **16.8 mm h⁻¹** produced streamflow and a
  ~2,000 m³ sand deposit; a thunderstorm delivering **33.4 mm** — an order of magnitude less water —
  with a peak I₁₅ of **39.2 mm h⁻¹** produced debris flows depositing **≥10,000 m³**. Western
  Washington's flood-season storms are the first kind. Wall and others (2020) note the candidate
  physical reasons the maritime Northwest resists runoff initiation: well-developed duff and litter,
  structured soils with very high infiltration capacity, and discontinuous fire-induced
  hydrophobicity. **INFERENCE for the platform: post-fire debris-flow hazard in the platform's
  basins is a warm-season, convective-cell hazard and a rain-on-snow hazard — not an AR hazard —
  and it therefore does not coincide with the flood season the platform is built around.** But it
  is not zero: the WALERT report emphasises that all four 2022 fires lie in mapped rain-on-snow
  zones and that the USGS model does not represent rain-on-snow at all.
- **California/Rockies post-fire thresholds** and the USGS likelihood model's coefficients —
  explicitly flagged as degraded in western Oregon by USGS itself.
- **Alila's frequency-paired results from snow-dominated interior catchments** (Fool Creek,
  Colorado; Camp Creek, BC) — the runoff-generation regime is different; Grant and others (2008)
  decline to extend their own snow-zone figure into management guidance for the same reason.

### 5.3 The December 2025 event was also a landslide event

The repo's `EVENT_ZERO.md` treats December 2025 as a flood. The Washington Geological Survey
treats the same period as a landslide event: **750 landslides** catalogued in the December 2025
Atmospheric River Landslides Clearinghouse (154 field survey forms, field teams in **Whatcom,
Skagit and Snohomish counties** in February 2026), **13 debris flows** identified by 19 December
including flows that damaged and forced evacuation of Stehekin, **eight WGS site visits near
Concrete** and one east of **Darrington** during the event, and a debris flow that blocked
eastbound I-90 near North Bend on **10 December** (FACT — WGS blog posts, fetched via curl
2026-08-24, *except* the **750 landslides** and **154 clearinghouse forms**, which appear on the
DNR *Washington Geologic Hazards Clearinghouse* page's weekly updates, **not** in either blog post;
that page also records 279 landslides as of 12 Feb 2026 and field work in **King** and **Clallam**
counties as well as Whatcom/Skagit/Snohomish, so the response was statewide, not basin-focused).

**A date discrepancy to reconcile.** The WGS post says "These storms began December 11, delivering
**7.5 inches of rain at SeaTac** and even more in the Cascade foothills," with a break on
December 13–14, high winds December 16–17, and a further AR on December 18 focused on southwest
Washington. The repo's `HYDROLOGY.md` §12 describes the AR sequence as **Dec 3–5, Dec 7, Dec 8–11**
with the Mount Vernon crest at **2025-12-12 08:15Z**. These are not obviously compatible; a debris
flow on I-90 on **December 10** also predates the WGS "began December 11" framing.
**OPEN QUESTION — reconcile the WGS event chronology against the CW3E/NWS chronology already in
`EVENT_ZERO.md` before either is treated as authoritative.**

### 5.4 Original computation: conveyance drift at fifteen western Washington gauges

**Method.** For each gauge I downloaded the USGS annual peak-flow file
(`https://nwis.waterdata.usgs.gov/nwis/peak?site_no={site}&agency_cd=USGS&format=rdb`, retrieved
2026-08-24), kept water years with both `peak_va` (cfs) and `gage_ht` (ft), restricted to the
**upper half of the peak-discharge distribution** at that gauge (so the result speaks to
flood-stage hydraulics, not low-flow control), fitted `gage_ht = a + b·log₁₀(peak_va)` by least
squares, and took the **Theil–Sen** slope of the residual against water year with a Mann–Kendall
significance test. Year-to-year residual jumps greater than 1.5 ft were treated as **datum or
site changes** and the record split; the reported window is the longest homogeneous segment (or an
explicitly named sub-window). This is the same measurement principle Anderson & Konrad (2019) and
Czuba and others (2010) use, applied to the annual-peak file rather than to the full field-
measurement record.

| Gauge (USGS id) | Window | n | ft / decade | p | resid. sd (ft) |
|---|---|---:|---:|---:|---:|
| NF Nooksack bl Cascade Ck nr Glacier (12205000) | 1938–2024 | 44 | +0.016 | 0.77 | 0.77 |
| Nooksack at Deming (12210500) | 1932–1991 | 28 | **+0.114** | 0.040 | 0.47 |
| **Nooksack at Ferndale (12213100)** | 1968–2024 | 31 | **+0.139** | **0.0001** | 0.39 |
| Sauk near Sauk (12189500) | 1932–2017 | 44 | **+0.000** | 0.88 | **0.21** |
| Skagit near Concrete (12194000) | 1962–2024 | 29 | +0.096 | 0.20 | 0.71 |
| Skagit near Mount Vernon (12200500) | 1948–2005 | 30 | −0.029 | 0.25 | **0.25** |
| Skagit near Mount Vernon (12200500) | 2006–2024 | 11 | *+2.531* | 0.0006 | **1.38** |
| Skykomish near Gold Bar (12134500) | 1932–2024 | 48 | **+0.003** | 0.74 | **0.18** |
| Snohomish near Monroe (12150800) | 1965–2024 | 32 | −0.034 | 0.26 | 0.25 |
| NF Stillaguamish nr Arlington (12167000) | 1932–2022 | 48 | +0.040 | 0.30 | 0.50 |
| Snoqualmie near Carnation (12149000) | 1945–2023 | 43 | +0.094 | 0.015 | 0.52 |
| Green near Auburn (12113000) | 1948–2005 | 28 | **−0.133** | 0.0002 | 0.29 |
| Green near Auburn (12113000) | 1990–2025 (excl. WY2022) | 13 | **+0.298** | 0.0002 | 0.35 |
| Greenwater at Greenwater (12097500) | 1932–2023 | 41 | +0.078 | 0.019 | 0.58 |
| Dungeness near Sequim (12048000) | 1924–2022 | 48 | +0.075 | 0.002 | 0.32 |

> **ADVERSARIAL RE-RUN, 2026-08-24 (independent replication of this table).** The method above was
> re-executed from scratch against freshly downloaded peak files. **Sauk (−0.001, p = 0.93,
> sd 0.21), Skykomish (+0.001, p = 0.88, sd 0.18), Snohomish near Monroe (−0.035, p = 0.30) and the
> Skagit at Mount Vernon post-2005 block (+2.51, sd 1.38, n = 11) all reproduce.** The
> **Nooksack at Ferndale row does not.** A genuine Theil–Sen slope with a Mann–Kendall p over
> WY1968–2024, upper half of the peak distribution, gives **+0.065 ft/decade, p = 0.028, n = 30** —
> less than half the tabulated slope and two orders of magnitude weaker in significance. The
> tabulated **+0.139 / p = 0.0001 is reproduced almost exactly by an ordinary least-squares slope
> of the residual with an OLS t-test (+0.133, p = 0.00017)**, i.e. the reported estimator is not the
> estimator the method text names. No variant of the stated method (any top-*k* subset from 24 to
> 41 peaks) yields a slope above +0.105. Ferndale is precisely the gauge where OLS and Theil–Sen
> diverge most, which is the signature of a leverage-driven fit.
>
> **Use +0.065 ft/decade (p = 0.028) as the Ferndale anchor until this is re-derived**, and treat
> the Deming (+0.114, p = 0.040) and Green-near-Auburn 1948–2005 (−0.133, p = 0.0002) rows as
> likewise unverified — the re-run gives +0.155 (p = 0.0005) and −0.093 (p = 0.008) for those two.
> This matters downstream: at +0.065 ft/decade the Ferndale drift is **smaller than** SIR 2019-5008's
> delta-progradation term (0.11 ft/decade), which strengthens rather than weakens the base-level
> reading in Open Question 4.

**Readings (INFERENCE from the table, corroborated by the cited literature; see the re-run box
above before quoting reading 1).**

1. **The Nooksack is aggrading at flood stage and the signal is unambiguous.** +0.139 ft/decade at
   Ferndale over 56 years, p = 0.0001, against a residual sd of only 0.39 ft. *(Not reproduced — see
   the re-run box: the robust estimate is +0.065 ft/decade, p = 0.028.)* Independent
   corroboration: SIR 2019-5008 measured +0.3 to +0.5 ft/decade in the 90th percentile of *daily*
   stage at Ferndale with no discharge trend. My flood-peak figure is smaller than their
   high-daily-stage figure, which is the expected ordering — the bed matters proportionally less at
   higher stage.
2. **Non-glacial basins are flat.** Skykomish near Gold Bar is the cleanest gauge in the region
   (residual sd 0.18 ft over 92 years) and shows +0.003 ft/decade. Snohomish near Monroe and
   NF Stillaguamish show nothing significant. This is the control the argument needed.
3. **The Sauk is a remarkable natural benchmark.** Exactly 0.000 ft/decade over 1932–2017 across 44
   flood peaks with residual sd 0.21 ft — an 86-year stationary stage–discharge relation on an
   unregulated river draining an active volcano — followed by a **step of about −0.8 ft that
   appears in WY2018 and persists through WY2024** (residuals −0.81, −0.86, −0.56, −0.89, −0.84).
   That is a step, not a trend; it is either a channel change or a rating revision. **OPEN
   QUESTION** — resolve against the USGS station analysis. Until it is resolved, *any* comparison
   of a post-2017 Sauk stage to a pre-2018 Sauk stage is suspect. The repo uses the Sauk as its
   basin-state gauge for the Skagit (`Basin.susceptibility_gauge_id = station:usgs:12189500`), which
   makes this a live concern — though the susceptibility surface uses *flow* percentile, not stage,
   and is therefore insulated.
4. **Skagit at Mount Vernon: the rating did not drift, it destabilised.** The residual sd was
   **0.25 ft across 1948–2005** (30 flood peaks — extraordinary stability), then **1.38 ft across
   2006–2024**: WY2007 and WY2008 sit at **−2.1 ft** and WY2018 and WY2022 at **+1.4 and +1.9 ft**.
   The apparent +2.53 ft/decade for 2006–2024 is mostly recovery from the WY2007–08 excursion and
   should not be quoted as a trend. What *should* be quoted is the **5.5-fold increase in the
   *standard deviation* of the stage–discharge residual after 2005** (≈30× in variance). Note also
   that the post-2005 residual sequence is close to monotone in time (−2.0, −2.0, −1.2, −0.8, −0.3,
   +0.3, +1.1, +1.5, +0.6, +2.0, +0.7 ft), which is a *ramp* as much as it is scatter, and which the
   Mann–Kendall test flags at p = 0.0006. Independent re-run 2026-08-24 confirms the excursion is
   an interpolation, not an extrapolation (the 1948–2005 fit spans 69,400–152,000 ft³/s, bracketing
   every post-2005 peak), so it is not an artefact of the rating's functional form. This localises and confirms the "2006 outlier"
   the repo's prior pass flagged (it is water years 2007 *and* 2008), and it means the platform's
   stage headroom at Mount Vernon has an effective uncertainty of order ±1.4 ft that no datum check
   will catch.
5. **Green near Auburn shows the reservoir signature.** Significant **incision** (−0.133 ft/decade)
   across 1948–2005, consistent with Howard A. Hanson Dam (completed 1961–62) trapping bed material
   and starving the downstream reach, then a significant **reversal to +0.298 ft/decade since 1990**.
   (WY2022's residual of +4.1 ft is excluded as an evident artefact and is itself an **OPEN
   QUESTION**.) This is the one place in the dataset where regulation and geomorphology visibly
   interact, and it argues that `regulation_class` and sediment regime are not independent
   attributes.

**Caveats, stated plainly.**

- `peak_va` at most of these sites is itself **derived from `gage_ht` through the USGS rating**.
  So what I measure is the *rating shift history*, not an independent survey of the bed. That is
  exactly the quantity Anderson & Konrad and Czuba and others use — USGS attributes rating shifts
  to channel change — but the interpretation "the bed moved" is one step of inference away from the
  measurement, and on a tidally influenced reach like Mount Vernon "the backwater changed" is an
  equally good reading.
- The peak file does not flag gauge datum changes. My 1.5 ft step detector found them at
  **Nooksack at Ferndale (a ~7 ft step between 1964 and 1968)**, **Snoqualmie at Carnation (a ~43 ft
  step at 1940)** and **Cedar at Renton (steps at ~1951 and ~1976, no segment long enough to
  analyse)**. Any long-record stage analysis that does not do this will produce nonsense; the
  unsegmented Cedar at Renton record yields a spurious +0.9 ft/decade.
- Regulated reaches (Skagit at Concrete/Mount Vernon, Green, White) have peaks whose magnitude is
  an operations outcome; the *stage-for-a-given-Q* residual is still a valid hydraulic quantity, but
  the sampling of Q is not natural.

### 5.5 Original computation: how often is the gauge's hydraulic control fouled?

The USGS OGC Water Data API exposes a `field-measurements` collection carrying, per field visit,
`control_condition` and `measurement_rated`. I queried all gage-height (parameter 00065) field
measurements for nine western Washington gauges
(`https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items?monitoring_location_id=USGS-{id}&parameter_code=00065&limit=10000`,
retrieved 2026-08-24) and tabulated the control condition (FACT — computed here):

| Gauge | visits | Clear | Debris (light+mod+heavy) | Vegetation | Poor-rated measurements |
|---|---:|---:|---:|---:|---:|
| Skagit nr Mount Vernon | 1,020 | 42 % | **29 %** (21+7+1) | 0 % | 25 |
| Nooksack at Ferndale | 1,245 | 50 % | **12 %** (9+3) | <1 % | 27 |
| Green nr Auburn | 800 | 64 % | 8 % | 2 % | 9 |
| Cedar at Renton | 1,301 | 52 % | 8 % | <1 % | 0 |
| White nr Auburn | 553 | 68 % | 7 % | 0 % | 4 |
| Sauk at Sauk | 942 | 61 % | 5 % | <1 % | 23 |
| Snoqualmie nr Carnation | 937 | 72 % | 5 % | <1 % | 13 |
| NF Stillaguamish nr Arlington | 900 | 59 % | 3 % | 2 % | 20 |
| Skykomish nr Gold Bar | 728 | 74 % | **3 %** | <1 % | 10 |

**Reading (INFERENCE).** The spread is a factor of ten. Two cautions before this is read as a
sediment-supply ranking. (a) The denominators are not comparable: 34 % of the Ferndale visits and
12 % of the Mount Vernon visits carry a null `control_condition`, plus 16 % "Unspecifed" at Mount
Vernon. Restricting to visits where the field crew actually recorded a condition gives Skagit 41 %,
Ferndale 20 %, Sauk 7.5 %, Skykomish 3.9 % — the factor of ten survives, the absolute percentages do
not. (b) It does **not** order with sediment supply: the Nooksack has the *highest* per-area
sediment yield of the 14 major Puget Sound rivers (§3) yet Ferndale ranks well below Mount Vernon.
Channel gradient, proximity to the depositional delta reach, wood supply and per-office field
practice are all live alternatives. Treat this as a **data-quality** attribute — which is all the
platform needs it for — not as a supply proxy. The Skagit near Mount Vernon — the platform's most important forecast
point, and the reach whose historical peaks the literature says are disputed partly because of
"levee failures and log jams" — has a debris-affected hydraulic control at nearly **three in ten**
field visits. This is a per-gauge, provenance-carrying, already-published data-quality attribute
that the platform can ingest today and that speaks directly to how much a stage reading from that
gauge should be trusted.

### 5.6 Datum metadata is incomplete for exactly the gauges that matter

Querying `monitoring-locations` for the same set (FACT, 2026-08-24):

| Gauge | drainage area (mi²) | `vertical_datum` |
|---|---:|---|
| Skagit nr Mount Vernon (12200500) | 3,093 | NAVD88 |
| Nooksack at Ferndale (12213100) | 786 | NAVD88 |
| **Sauk near Sauk (12189500)** | 714 | **NGVD29** |
| **Nooksack at Deming (12210500)** | 584 | **NGVD29** |
| **Green near Auburn (12113000)** | 399 | **null** |
| **White near Auburn (12100496)** | 475 | **null** |
| Skykomish nr Gold Bar, Snohomish nr Monroe, NF Stilly nr Arlington, Snoqualmie nr Carnation, Greenwater, Dungeness, NF Nooksack nr Glacier, Skagit nr Concrete | — | NAVD88 |

**Two caveats on reading this table.** The `vertical_datum` field in the `monitoring-locations`
collection is the datum of the *site altitude*, not the gauge datum against which stage is
reported; USGS publishes the gauge datum in the station description, which this collection does not
expose. So a null here is a metadata gap in the collection, not proof that no gauge datum exists.
What the table does establish is (a) that **two vertical datums are in active use across the
platform's gauges** — NGVD29 and NAVD88 differ by roughly 3–4 ft in western Washington — and (b)
that the platform cannot get a complete datum picture from this one endpoint and must resolve the
gauge datum from NWPS threshold metadata or the USGS station description as well.

Note the coincidence worth checking: **the two gauges with a null datum here are the two whose NWS
thresholds are flow-defined** (Green and White at Auburn). The existing `compatibility_problem()`
refuses a stage comparison when either datum is null, which is the right behaviour and means the
platform reports UNKNOWN rather than a wrong number — but the UI should say *why* it is unknown,
not merely go blank. **OPEN QUESTION**: is the null a coincidence of the metadata, or does it
reflect that these sites' stage scales are not tied to a published vertical datum at all?

---

## 6. What this means for Cascadia Papsukkal

### 6.1 Doctrine

1. **Add a fourth time to the three-valued clock, for slow variables: the *hydraulic epoch*.**
   `DATA_DOCTRINE.md` §3 has `valid_time`, `issued_at`, `retrieved_at`. Stage observations and
   stage thresholds additionally belong to a channel state that has a date. Two stage values from
   different epochs are not comparable even when their datums match. Concretely: the Sauk step at
   WY2018, the Ferndale step between 1964 and 1968, the Carnation step at 1940.
2. **State that ratings are nonstationary.** `HYDROLOGY.md` §9 correctly says USGS "shifts and
   revises" ratings and correctly forbids the platform converting stage↔flow. It does not say that
   the *threshold* inherits this. Add: *an official stage threshold is a statement about the channel
   as it was when the threshold was set; on aggrading reaches its discharge equivalent drifts.*
3. **Add a basin attribute for sediment regime, beside `regulation_class`.** Proposed values:
   `volcanic_glaciated` (Nooksack, White; Skagit via the Sauk), `glaciated_non_volcanic`,
   `non_glacial`. It is CONFIGURED, it never enters a hazard computation, and it is the honest
   answer to "why does this gauge's stage record drift and that one's does not."
4. **Extend the "will not claim" list (§13) to geomorphic hazard.** The platform will not model or
   forecast lahars, glacial outburst floods, landslide-dam outbursts, or post-fire debris flows.
   It displays the responsible agency's product verbatim (USGS volcano alert level and post-fire
   hazard assessments; WA DNR WALERT reports and the post-wildfire debris-flow dashboard; NWS
   flash-flood products) and links to it.
5. **A geomorphic anomaly is a data-quality event, not a hydrologic one.** A sudden stage change
   that is inconsistent with the discharge trend is a candidate log jam, avulsion, breach, debris
   flow or rating break. It must be surfaced as an anomaly with `quality=suspect` and a reason —
   never smoothed, never read as basin behaviour, and never used in `rate_of_rise`.
6. **Staleness needs a slow-variable class.** `DATA_DOCTRINE.md` §5 derives staleness from
   `expected_cadence`. A 2019 channel survey or a 2015 bed-elevation trend is not stale; it is the
   current best estimate of a decadal quantity. Give geomorphic products a cadence class where the
   correct display is "as surveyed 2015" rather than an age-in-years staleness mark.

### 6.2 Methods

1. **`conveyance_drift` — a DERIVED / EXPERIMENTAL feature per gauge.** Exactly the §5.4 method:
   fit `gage_ht ~ a + b·log₁₀(Q)` on USGS field measurements or annual peaks, restricted to the
   upper half of the discharge distribution; report the Theil–Sen slope of the residual in
   ft/decade with a Mann–Kendall p-value and the residual sd. Emit **step detection** as a
   first-class output (`rating_epoch_breaks`), because the steps are what invalidate comparisons.
   Method version it; it is EXPERIMENTAL until hindcast-evaluated. This is genuinely cheap — the
   whole computation in §5.4 is ~60 lines and one HTTP call per gauge.
2. **`rating_epoch` on every stage series and threshold**, derived from the step detector plus any
   USGS-published datum change. `compatibility_problem()` gains a fourth check: refuse a
   *historical* stage comparison across epochs. (Leave the current-value-vs-threshold path alone;
   it is already correct.)
3. **`gauge_control_quality` — a DERIVED per-gauge attribute** from USGS `control_condition` and
   `measurement_rated`: the fraction of field visits with debris/vegetation-affected control and
   the distribution of measurement ratings. Render it as a labelled category (not a decimal —
   `DATA_DOCTRINE.md` §9), e.g. "hydraulic control debris-affected in 29 % of USGS field visits."
4. **Add short-duration precipitation to the forcing surface.** `HYDROLOGY.md` §4 lists QPF windows
   of 6/12/24/48/72/120 h. Every debris-flow and shallow-landslide product in this region is keyed
   to either **I₁₅ / I₆₀** or **multi-day accumulation with antecedent memory**. The platform
   already ingests MRMS hourly QPE and could compute both. Suggested features: `qpe_i60_max_6h`,
   `qpe_p3_in`, `qpe_p15_in`, and the Seattle-form cumulative-threshold margin
   `P3 − (3.5 − 0.67·P15)` **labelled EXPERIMENTAL and scoped to the Seattle/Puget Lowland region
   the threshold was fitted for** — never extrapolated to a mountain basin.
5. **Do NOT build a harvest/road/impervious term into any hazard computation.** Record
   `forest_disturbance_pct`, `road_density_km_km2` and `effective_impervious_pct` as CONFIGURED
   basin attributes with the GTR-760 detection-limit caveat attached, and cite both sides of the
   Alila controversy in the method note. Both camps agree the basin-scale effect is smaller than
   interannual variability.
6. **A landslide-dam / conveyance-failure watcher.** Two signatures worth detecting from data the
   platform already has: (a) a **sustained stage rise at an upstream gauge with a simultaneous
   discharge collapse at the next gauge downstream** (impoundment); (b) a **step change in stage on
   a falling or steady discharge** (avulsion, jam, breach). Both emit an anomaly `Assessment`, not
   a hazard.

### 6.3 Data sources to add to `docs/DATA_SOURCES.md`

| Source | What it gives | Access verified 2026-08-24 |
|---|---|---|
| USGS OGC API `field-measurements` | gage height + discharge pairs, `control_condition`, `measurement_rated`, `approval_status`, `vertical_datum` | `https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items?monitoring_location_id=USGS-12213100&parameter_code=00065` — **works** |
| USGS OGC API `channel-measurements` | channel width/area/velocity, `channel_stability`, `channel_material` | works; sparsely populated for older visits |
| USGS OGC API `peaks` | annual peak stage + discharge with qualification codes | works (legacy RDB `nwis.waterdata.usgs.gov/nwis/peak` also works; `waterdata.usgs.gov/nwis/measurements` now 301s) |
| USGS OGC API `monitoring-locations` | drainage area, altitude, **`vertical_datum`** | works — and is how §5.6 found the two null datums |
| WA DNR Post-Wildfire Debris Flow Dashboard | burned areas assessed since 2017, telemetered weather stations, reported debris-flow events | ArcGIS dashboard; **no documented public API found** — OPEN QUESTION |
| WA DNR Geologic Information Portal / Open Data | landslide inventories (>50,000 mapped hazards, 8 counties), alluvial fans, **Rain-on-Snow (FP) zone layer** | Rain-on-Snow feature service resolves: `https://gis.dnr.wa.gov/site2/rest/services/Public_Forest_Practices/WADNR_PUBLIC_FP_Watershed/FeatureServer/6` |
| WA DNR Geologic Hazards Clearinghouse | event-scoped landslide inventories (e.g. the 750 December-2025 slides) | web pages + Survey123; machine access unknown |
| USGS Post-Fire Debris-Flow Hazard Assessments | per-fire basin and segment hazard classes, design-storm thresholds | published per fire; served through a USGS dashboard |
| USGS Volcano Hazards / PNSN | volcano alert level, seismic detection of lahars and outburst floods | alert level is a small, stable, OFFICIAL-badgeable field |
| USGS SIR sediment reports (2010-5240, 2016-5106, 2019-5008, 2017-5055) | one-off but authoritative aggradation and conveyance numbers | CONFIGURED reference values with citation and vintage |

Badging: everything from USGS/DNR/NWS above is **OBSERVED** or **OFFICIAL_FORECAST** as
appropriate for its own product; anything the platform computes from them (conveyance drift, control
quality, threshold margins) is **DERIVED** and, until hindcast, **EXPERIMENTAL**.

### 6.4 Contracts

- `Basin`: add `sediment_regime` (CONFIGURED enum) and `volcano_headwater` (nullable string:
  `mount_baker` | `glacier_peak` | `mount_rainier`). Both display-only.
- `Threshold`: add `hydraulic_epoch` (nullable) alongside `datum`, and surface
  `effective_from` in the UI as the threshold's vintage.
- `Observation` for stage: add `rating_epoch` (nullable) and allow `quality=suspect` with a
  geomorphic reason code (`control_fouled`, `rating_break`, `impoundment_suspected`).
- New `DerivedFeature` kinds: `conveyance_drift_ft_per_decade`, `rating_epoch_breaks`,
  `gauge_control_quality`, `qpe_i60_max`, `qpe_p3_p15_margin`.
- `BasinVisualizationState` / `SceneSummary`: a `geomorphic_context` block carrying the sediment
  regime, the conveyance-drift label, the gauge-control-quality label, and any active official
  post-fire or volcano product — all clearly badged, none entering a category or hazard field.
- Contracts version note: this is additive and belongs in a 1.2.0 minor bump, not a breaking change.

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

1. **`HYDROLOGY.md` §9, "Vertical datums."** The doctrine treats a datum check as sufficient for
   stage comparison. It is necessary but not sufficient: the Sauk's stage–discharge relation stepped
   ~0.8 ft in WY2018 with no datum change, and the Skagit at Mount Vernon's residual variance rose
   5.5× (in standard deviation) after 2005. **Qualification, not contradiction** — add the rating epoch.
2. **`HYDROLOGY.md` §9, "Hydraulic headroom."** "stage headroom: `threshold_stage − current_stage`
   (simple, datum-checked)" is described as the simple case. On the Nooksack at Ferndale the bed has
   consumed ~0.8 ft of that headroom since 1968; on the White near Auburn USGS measured a **~25 %
   conveyance loss at the gauge**. Stage headroom on an aggrading reach is not simple; it needs an
   uncertainty statement.
3. **`HYDROLOGY.md` §2, basin descriptions.** The Skagit entry says Mount Baker/Glacier Peak nothing
   — sediment regime is absent from the domain model entirely, while `regulation_class` is a
   first-class attribute. Given that three of eight basins have stratovolcano headwaters and that
   this is the single best predictor of which gauges drift, that is an asymmetry worth fixing.
4. **`HYDROLOGY.md` §4, forcing features.** The forcing surface has no sub-6-hour precipitation
   quantity. Every regional debris-flow product is keyed to 15- or 60-minute intensity. This is a
   genuine structural gap, and it is also the reason the platform currently cannot reason about the
   one geomorphic hazard that *is* rainfall-triggered.
5. **`DATA_DOCTRINE.md` §5, staleness.** The formula `stale = now − valid_time > cadence + grace`
   is right for observations and wrong for decadal geomorphic quantities. The doctrine already has
   the ARCHIVED concept for backfilled values; slow variables need a third treatment.
6. **`DATA_DOCTRINE.md` §7, thresholds.** Thresholds are versioned rows keyed to their retrieval,
   which is correct for *when NWS said it*. Nothing records *what channel it was said about*.
7. **The prior solo pass, §6.3.** It attributes Skagit aggradation to Mount Baker sediment. More
   precisely: Mount Baker's contribution to the Skagit arrives via the **Baker River, which is
   impounded by Upper and Lower Baker dams (combined catchment ~770 km²)**, so the Skagit's
   *unregulated* volcanic coarse-sediment source is **Glacier Peak via the Sauk** (1,900 km², 23 % of
   the basin). Mount Baker's unimpeded sediment goes to the **Nooksack**. This matters because it
   predicts — correctly, per §5.4 — that the Nooksack drifts and the Skagit at Concrete does not
   significantly.
8. **The prior solo pass, §6.6.** "Overland flow in these basins occurs essentially only on roads
   and compacted ground, making road density a direct runoff-generation term" is right as physics
   and misleading as an operational inference. GTR-760's synthesis is that the resulting peak-flow
   effect is **undetectable beyond ~6-year return periods** and **smaller than interannual
   variability at basin scale**. Road density is a real term in the water balance and not a usable
   per-event predictor for the events the platform cares about. Alila's group disputes the
   statistical basis of that conclusion; the platform should cite both and use neither.
9. **`EVENT_ZERO.md`.** December 2025 was also a large landslide event — 750 slides catalogued —
   and the subject of a WGS Geologic Hazards Clearinghouse activation. (Do **not** call it "the
   largest WGS has run a clearinghouse for": the Clearinghouse Plan was only published in
   February 2024, so there is almost no comparison set.), with field response concentrated in the platform's own basins
   (Concrete, Darrington). And the WGS chronology ("storms began December 11", 7.5 in at SeaTac)
   does not obviously match the repo's Dec 3–5 / 7 / 8–11 AR sequence. Both the addition and the
   discrepancy belong in the Event Zero evidence set.

---

## 8. Open questions

1. **Is the Sauk's WY2018 −0.8 ft step a channel change or a rating revision?** Resolve against the
   USGS station analysis for 12189500. It bounds the validity of every historical Sauk stage
   comparison, and the Sauk is the repo's chosen basin-state gauge for the Skagit.
2. **What happened at Skagit near Mount Vernon in WY2007–2008** (residuals −2.1 ft) **and in
   WY2018/2022** (+1.4/+1.9 ft)? Candidate mechanisms: upstream spill or Nookachamps Creek off-
   channel storage engagement (raised by the prior pass), levee overtopping, tidal coincidence, a
   rating-method revision, and — for the *positive* post-2013 residuals specifically — the
   **Downtown Mount Vernon flood-protection floodwall, completed 2018**, which confines flow through
   the gauged reach and would raise stage at a given discharge (INFERENCE; the residual ramp begins
   before 2018, so the floodwall cannot be the whole explanation). The USGS station analysis and Skagit County records would settle it.
3. **Why is Green near Auburn's WY2022 residual +4.1 ft?** Datum change, gauge relocation, or a
   real event?
4. **What fraction of the Nooksack at Ferndale drift is delta progradation versus upstream supply?**
   SIR 2019-5008 computes 0.11 ft/decade from progradation alone against my measured 0.139
   ft/decade total — suspiciously close. If progradation dominates, the drift is a base-level
   process that will continue regardless of Mount Baker.
5. **Does the Anderson & Konrad 30–50-year lead time actually forecast?** The claim is testable
   now: the upper North Fork record since ~1990 should predict Ferndale's bed elevation in
   2020–2040. My NF-near-Glacier result (+0.016 ft/decade, p = 0.77 over 1938–2024) is a whole-
   record average and does not test it; the sub-window structure would.
6. **Is there a machine-readable feed for the WA DNR post-wildfire debris-flow dashboard and the
   Geologic Hazards Clearinghouse landslide inventory?** If yes, both are cheap, authoritative,
   basin-joinable layers. If no, that is a data-sourcing dead end worth documenting.
7. **Are the December 2025 chronologies reconcilable?** (WGS "began December 11" and 7.5 in at
   SeaTac vs the repo's Dec 3–5 / 7 / 8–11 AR sequence and the 12 December crest.)
8. **What is the correct rain-on-snow post-fire threshold for western Washington?** WA DNR states
   the USGS model does not represent it and that all four 2022 fires lie in mapped ROS zones. There
   is, as far as this sweep found, **no published ROS-aware post-fire debris-flow threshold for the
   maritime Northwest.** That is a genuine hole in the operational science, not just in the
   platform.
9. **Does the platform want a `lahar_valley` flag at all?** The USGS pages give no numerical
   recurrence intervals for Baker or Glacier Peak lahars; the honest attribute may be "this valley
   is mapped in a USGS lahar hazard zone" with a link, and nothing more.
10. **How much of the disputed 1921 Skagit peak (240,000 cfs, ±15 %) is a conveyance artefact?**
    The channel of 1921 is not the channel of 2026, and the drift measured here is one-directional.
11. **Bedload is 1–3 % of the Skagit's load but 7–8 % of the Nooksack's** (Curran and others 2016;
    SIR 2019-5008). Is that a real basin difference (volcanic supply, slope) or a measurement-method
    difference? It matters because bedload, not suspended load, is what changes conveyance.

---

## 9. Sources

Fetched and read in this pass:

- [Anderson, S.W., & Konrad, C.P. (2019). *Downstream-propagating channel responses to decadal-scale climate variability in a glaciated river basin.* JGR Earth Surface 124, 902–919. doi:10.1029/2018JF004734](https://www.whatcomcounty.us/DocumentCenter/View/40868/Anderson_et_al-2019-Journal_of_Geophysical_Research__Earth_Surface) (Whatcom County copy; the AGU page is paywalled/403)
- [Anderson, S.W., Konrad, C.P., Grossman, E.E., & Curran, C.A. (2019). *Sediment storage and transport in the Nooksack River basin, northwestern Washington, 2006–15.* USGS SIR 2019-5008](https://pubs.usgs.gov/sir/2019/5008/sir20195008.pdf)
- [Anderson, S.W., Keith, M.K., Magirl, C.S., Wallick, J.R., Mastin, M.C., & Foreman, J.R. (2017). *Geomorphic response of the North Fork Stillaguamish River to the State Route 530 landslide near Oso, Washington.* USGS SIR 2017-5055](https://pubs.usgs.gov/sir/2017/5055/sir20175055.pdf)
- [Czuba, J.A., Czuba, C.R., Magirl, C.S., & Voss, F.D. (2010). *Channel-conveyance capacity, channel change, and sediment transport in the lower Puyallup, White, and Carbon Rivers, western Washington.* USGS SIR 2010-5240](https://pubs.usgs.gov/sir/2010/5240/pdf/sir20105240.pdf)
- [Czuba, J.A., and others (2011). *Sediment load from major rivers into Puget Sound and its adjacent waters.* USGS Fact Sheet 2011-3083](https://pubs.usgs.gov/fs/2011/3083/pdf/fs20113083.pdf)
- [Curran, C.A., Grossman, E.E., Mastin, M.C., & Huffman, R.L. (2016). *Sediment load and distribution in the lower Skagit River, Skagit County, Washington.* USGS SIR 2016-5106](https://pubs.usgs.gov/sir/2016/5106/sir20165106.pdf)
- [Grant, G.E., Lewis, S.L., Swanson, F.J., Cissel, J.H., & McDonnell, J.J. (2008). *Effects of forest practices on peak flows and consequent channel response: a state-of-science report for western Oregon and Washington.* USDA PNW-GTR-760](https://www.fs.usda.gov/pnw/pubs/pnw_gtr760.pdf)
- [Alila, Y., Kuraś, P.K., Schnorbus, M., & Hudson, R. (2009). *Forests and floods: A new paradigm sheds light on age-old controversies.* WRR 45, W08416](https://andrewsforest.oregonstate.edu/pubs/pdf/pub5256.pdf)
- [Wemple, B.C., Jones, J.A., & Grant, G.E. (1996). *Channel network extension by logging roads in two basins, western Cascades, Oregon.* JAWRA 32(6)](https://andrewsforest.oregonstate.edu/sites/default/files/lter/pubs/pdf/pub2314.pdf)
- [Wall, S.A., Roering, J.J., & Rengers, F.K. (2020). *Runoff-initiated post-fire debris flow, Western Cascades, Oregon.* Landslides. doi:10.1007/s10346-020-01376-9](https://wpg.forestry.oregonstate.edu/sites/default/files/seminars/Wall%20et%20al.%20-%202020%20-%20Runoff-initiated%20post-fire%20debris%20flow%20Western%20Cas.pdf)
- [Thomas, M.A., and others (2023). *The rainfall intensity–duration control of debris flows after wildfire.* GRL 50, e2023GL103645](https://cawaterlibrary.net/wp-content/uploads/2023/07/Geophysical-Research-Letters-2023-Thomas-The-Rainfall-IntensityE28090Duration-Control-of-Debris-Flows-After-Wildfire.pdf)
- [Mickelson, K., & Allen, M. (2022). *WALERT report: Bolt Creek, Suiattle River, Boulder Lake, and Lake Toketie Fires.* Washington Geological Survey](https://dnr.wa.gov/sites/default/files/2025-03/ger_hazards_landslide_walert_report_bolt_creek_suiattle_boulder_toketie_2022.pdf)
- [Konrad, C.P., & Booth, D.B. (2002). *Hydrologic trends associated with urban development for selected streams in the Puget Sound basin, western Washington.* USGS WRIR 02-4040](https://pubs.usgs.gov/wri/wri024040/pdf/WRIR02-4040.pdf)
- [USGS — Lahar hazards at Glacier Peak](https://www.usgs.gov/volcanoes/glacier-peak/science/lahar-hazards-glacier-peak)
- [USGS — Lahars and debris flows at Mount Baker](https://www.usgs.gov/volcanoes/mount-baker/lahars-and-debris-flows-mount-baker)
- [WA DNR — Wildfire-associated debris flows (program, dashboard, WALERT)](https://dnr.wa.gov/washington-geological-survey/geologic-hazards-and-environment/wildfire-associated-debris-flows)
- [Washington State Geology News — December 2025 atmospheric rivers landslide response (19 Dec 2025)](https://washingtonstategeology.wordpress.com/2025/12/19/december-2025-atmospheric-rivers-landslide-response-by-the-washington-geological-survey/)
- [Washington State Geology News — Clearinghouse activated for the December 2025 atmospheric river landslides (5 Feb 2026)](https://washingtonstategeology.wordpress.com/2026/02/05/clearinghouse-activated-for-the-december-2025-atmospheric-river-landslides/)
- [USGS — Assessment of western Oregon debris-flow hazards in burned and unburned environments (Selander, Calhoun, Burns, Kean & Rengers, 2025, ESPL, doi:10.1002/ESP.70045)](https://www.usgs.gov/publications/assessment-western-oregon-debris-flow-hazards-burned-and-unburned-environments) — publication page fetched; journal article paywalled
- [Encyclopedia of Puget Sound — Rethinking flood control for the Nooksack River](https://www.eopugetsound.org/magazine/nooksack-river)

Primary data queried directly (2026-08-24):

- USGS annual peak-flow files, `https://nwis.waterdata.usgs.gov/nwis/peak?site_no={site}&agency_cd=USGS&format=rdb` — 17 western Washington gauges (§5.4)
- USGS OGC Water Data API, `field-measurements`, `channel-measurements`, `monitoring-locations` collections, `https://api.waterdata.usgs.gov/ogcapi/v0/` (§5.5, §5.6)
- WA DNR ArcGIS open data search and `https://gis.dnr.wa.gov/site2/rest/services` (Rain-on-Snow feature service, §6.3)

Cited but **not independently fetched** (paywalled, 403, or only reachable in summary):

- Chleborad, A.F., Baum, R.L., & Godt, J.W. (2006). *Rainfall thresholds for forecasting landslides in the Seattle, Washington, area — exceedance and probability.* USGS OFR 2006-1064 (403 on fetch)
- Guzzetti, F., Peruccacci, S., Rossi, M., & Stark, C.P. (2008). *The rainfall intensity–duration control of shallow landslides and debris flows: an update.* Landslides 5, 3–17
- Booth, D.B., & Jackson, C.R. (1997). *Urbanization of aquatic systems: degradation thresholds, stormwater detention, and the limits of mitigation.* JAWRA 33(5), 1077–1090
- Staley, D.M., Negri, J.A., Kean, J.W., Laber, J.L., Tillery, A.C., & Youberg, A.M. (2017). *Prediction of spatially explicit rainfall intensity–duration thresholds for post-fire debris-flow generation in the western United States.* Geomorphology 278, 149–162
- Bathurst, J.C., Fahey, B., Iroumé, A., & Jones, J. (2020). *Forests and floods: using field evidence to reconcile analysis methods.* Hydrological Processes 34, 3295–3310 (403)
- Lewis, J., Reid, L.M., & Grant, G.E. (2010), and Bathurst (2014) and Birkinshaw (2014) comments on Alila/Green — titles and journals from search results only
- Jones, J.A., & Perkins, R.M. (2010). *Extreme flood sensitivity to snow and forest harvest, western Cascades, Oregon.* WRR 46 (403)
- Church, M., & Ryder, J.M. (1972) paraglacial concept; Czuba, Olsen and others (2012) Alder Lake sediment yields; Madej & Ozaki (1996) Redwood Creek — all via Anderson & Konrad (2019)
- Abbe, T.B., & Montgomery, D.R. (1996, 2003) large woody debris jams — abstracts only
- USGS Professional Paper on the Osceola Mudflow; Walder & Driedger on Mount Rainier outburst floods — secondary sources only
- KCM Inc. (1995) Nooksack channel capacity study (2.7 / 11.4 million yd³ figures)
- Kerr Wood Leidal (2008) Nooksack gravel-removal history — via SIR 2019-5008, which *was* fetched
