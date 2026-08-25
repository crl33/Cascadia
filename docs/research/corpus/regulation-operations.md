# Reservoir regulation, flood control, and operations

*Corpus entry, 2026-08-24. Part of the Cascadia Papsukkal flood-science corpus.*

*Labels: **FACT** = read on a fetched page or computed by me from a fetched primary dataset (URL or
query given); **INFERENCE** = reasoned from cited facts, not itself read anywhere; **ASSUMPTION** =
a working simplification; **OPEN QUESTION** = unresolved. Every API result in §6 was fetched live on
2026-08-24; every reservoir number in §3 marked "computed" was derived by me from the USACE A2W
time-series API and is reproducible from the query given.*

---

## 1. Headline

**A flood-control reservoir does not reduce flood risk by a fixed amount; it converts a fraction of
the basin's water into a decision, and the size of that fraction is bounded by drainage-area control,
allocated storage, and forecast lead time — all three of which are publishable numbers that the
platform does not currently carry.** On the Skagit, Ross and Upper Baker control **39 %** of the
drainage area at Mount Vernon and hold **194,000 acre-feet** of allocated flood storage; the peak
reduction they deliver rises from **0 % at the 2-year event to ~18 % at the 25-year event and falls
back to ~11 % at the 500-year event**. And the buffer that actually mattered in December 2025 was not
the allocated pool at all: Ross entered the storm **7.6 ft below** its required rule curve and absorbed
**110,900 acre-feet** — 92 % of a full flood pool's worth — while occupying only **25 %** of its
*designated* flood pool. Any gauge that reports "percent of flood pool used" against the rule curve
alone would have shown a quarter-full reservoir during the most consequential regulation event in the
basin's modern record.

---

## 2. Mechanisms

### 2.1 The reservoir is a storage integrator with an operator-chosen release

The governing statement is trivial and the difficulty is entirely in the last term:

```
dS/dt = Q_in(t) − Q_out(t)                                  (reservoir continuity)
S(t)  = f_elev→stor( h(t) )                                 (site capacity table, revisable)
Q_out(t) = g( h(t), gate settings, WCM rules, operator intent, Corps direction )
```

`Q_in` is not measured; at every project in scope it is **computed** by inverting continuity from
observed pool change and released outflow, which is why computed inflow can go negative
(FACT — `ROS.Flow-In.Inst.1Hour.0.SCL-RAW` returned **−5,273.8 cfs** and **−677.0 cfs** within
2025-12-01…2025-12-20; `HAH.Flow-In…COMPUTED-REV` likewise goes negative). A negative inflow is not a
sentinel; it is the noise floor of a differenced storage signal, and it must be carried as
`quality=estimated` with the differencing method named, not clipped to zero.

The downstream consequence is a routing problem, not a reservoir problem:

```
Q_control(t + τ) = Q_out(t) + Q_local_uncontrolled(t..t+τ)
```

where `τ` is the travel time to the *control point* — the gauge the water control manual names as the
regulation target. **The uncontrolled term is the one that floods people.**

### 2.2 The rule curve is a seasonal allocation of one volume between two purposes

A rule curve (a "water control diagram" in 33 CFR 208.11 language) is a time-varying upper bound on
pool elevation: the operator must keep the pool at or below it so that a prescribed volume stays empty.
It is a *risk allocation*, not a physical property. Three real examples, all fetched:

**Ross Dam (SCL, Skagit) — Table 15 of the 2013 USACE hydrology documentation** (FACT):

| Date | Ross Lake elevation (SCL datum) | Active flood storage required |
|---|---|---|
| Oct 1 | 1,602.50 ft | 0 ac-ft |
| Oct 15 | 1,600.80 ft | 20,000 ac-ft |
| Nov 1 | 1,598.84 ft | 43,000 ac-ft |
| Nov 15 | 1,597.37 ft | 60,000 ac-ft |
| Dec 1 – Mar 15 | 1,592.11 ft | 120,000 ac-ft |

**Upper Baker (PSE, Baker) — Table 10, per the 2008 FERC licence** (FACT):

| Date | Upper Baker elevation (NAVD88) | Active flood storage required |
|---|---|---|
| Oct 1 | 727.77 ft | 0 ac-ft |
| Oct 15 – Nov 1 | 724.53 ft | 16,000 ac-ft |
| Nov 15 – Mar 1 | 711.70 ft | 74,000 ac-ft |
| Apr 1 | 727.77 ft | 0 ac-ft |

**Howard A. Hanson (USACE, Green)** holds the winter pool "at or near elevation 1,075 ft to provide a
minimum of roughly **103,000 acre-feet** of storage for the regulation of floods", refills to a summer
conservation elevation of **1,167 ft** under AWSP Phase I, and reserves a *variable* minimum space
through spring per Chart 7-2; refill "may begin as early as 15 February" (FACT — HHD Water Control
Manual §7.03).

Two structural consequences follow (INFERENCE, but both are demonstrated in §3):

1. **Storage is not available when the season says it is.** The Skagit study is explicit: "The full
   amount of flood control storage is not required at Upper Baker until November 15 and at Ross until
   December 1. Large floods have, however, occurred early in the flood control season" — October 2003
   and November 2006 named (FACT). Weighting regulated hydrographs by the historical frequency of
   annual maxima within each two-week window **raised regulated peak quantiles at Concrete by about
   5 % for 50-year events and larger** (FACT).
2. **Refill is a competing risk.** Every reservoir with a conservation purpose (Ross, Upper Baker,
   Howard Hanson, Chester Morse, Tolt) buys flood safety in autumn by accepting refill risk in spring.
   Under a declining maritime snowpack that trade gets worse from both ends — this is the stated
   motivation for the Howard Hanson FIRO effort (FACT — CW3E names "increasing risk of failure to
   refill due to changing hydrology").

### 2.3 Control fraction is the hard ceiling

Define the **control fraction** `φ = A_controlled / A_at_control_point`. No operating rule can move
water that never passes a gate. The three western-Washington projects publish theirs:

- **Howard Hanson:** "The project regulates only **55 %** of the total drainage area above the station
  near Auburn. Therefore, it is not possible to provide total control of all floods in the basin"
  (FACT — HHD WCM §7.03a).
- **Mud Mountain:** "Because MMD controls only **42 %** of the total drainage area at Puyallup, not
  all potential floods can be held below the non-damaging discharge **even if there is no discharge
  from the dam**" (FACT — MMD WCM §7.04c).
- **Skagit:** "Ross and Upper Baker reservoir watersheds are **39 %** of the total Skagit River drainage
  area at Mount Vernon (the remaining 61 % of the total area is uncontrolled), and their combined
  annual runoff is **32 %** of the average annual runoff … Uncontrolled runoff is **68 %**" (FACT —
  2013 hydrology documentation §2.4.9.1). Above Concrete the split is 1,214 mi² controlled /
  1,523 mi² uncontrolled (FACT).

The Skagit's uncontrolled area is dominated by one river: the **Sauk, 732 mi², over 25 % of the area
above Concrete and "just over 50 % of the uncontrolled drainage area"** — and it contributed 45 %,
46 %, 64 % and 59 % of the Concrete peak in the 1990, 1995, 2003 and 2006 floods, with a modelled 52 %
at the 100-year event (FACT — Table 12).

The saturation statement that follows is quantitative and blunt: flood control at Ross and Upper Baker
"is sufficient to control floods in the lower valley … with exceedance frequencies of **four to five
percent (20–25 year event)**", and above roughly the 25-year event "flood runoff from the Skagit's
uncontrolled watersheds … is sufficient to produce major flooding in the valley **regardless of the
flood control regulation**". Even holding inflow to minimum outflow through a 50-year event, the
uncontrolled contribution alone "is still large enough to deliver **175,000 cfs** to the Mount Vernon
area, which exceeds the current levee capacity" (FACT).

### 2.4 Objective flow, control point, travel time — the forecast-lead constraint

The regulation rule is always of the form *hold the control point below an objective flow set below
the true channel capacity, using a forecast of local inflow over one travel time*:

| Project | Control point | Channel capacity | Objective (rising) | Travel time |
|---|---|---|---|---|
| Howard Hanson | Green R nr Auburn (USGS 12113000) | 12,000 cfs | **10,000 cfs** | ~8 h at high water |
| Mud Mountain | Puyallup R at Puyallup (USGS 12101500) | 50,000 cfs | **45,000 cfs** | ~6 h at high water |
| Ross / Upper Baker | Skagit R nr Concrete (USGS 12194000) | 90,000 cfs "major damage" | trigger, not target | 8 h (Ross), 2–3 h (U. Baker) |

(FACT — HHD WCM §7.02 Table 7-1 and §6.02a; MMD WCM §6.02a and §7.04c; Skagit 2013 doc §4.4.2.4.2.)

The gap between capacity and objective is explicitly a forecast-error margin: Auburn is "regulated to
10,000 cfs **to provide a margin of safety against errors in forecasted local inflow and weather**",
raised to 12,000 cfs only "on a flood recession … when conditions assure an accurate local inflow
forecast" (FACT). Puyallup's 45,000 cfs target exists "to provide a factor of safety against errors in
forecasting" against a 50,000 cfs capacity (FACT). **A 17 % release headroom at Howard Hanson and a
10 % headroom at Mud Mountain are, literally, the monetised value of forecast uncertainty.** That is
the same quantity FIRO tries to buy back (§2.9).

The Skagit trigger is a *forecast of natural flow*, not an observation: "eight hours before the
Northwest River Forecast Center forecasts the natural (unregulated) flow at Concrete to be
**90,000 cfs**, flow out of both Ross and Upper Baker will be set to their respective minimums"
(FACT). Seattle City Light's public fact sheet states the same threshold in the regulated frame:
"When river flows at Concrete are expected to top 90,000 cubic feet per second, the Corps temporarily
takes control of Ross Dam" (FACT — SCL Skagit Settlement fact sheet, March 2026). Interpolating the
2013 unregulated frequency curve at Concrete (2-yr 77,300 cfs, 5-yr 120,500 cfs, log-linear) puts the
90,000 cfs trigger at a **~2.7-year unregulated event** (INFERENCE, my computation). Howard Hanson's
manual makes the analogous statement directly: "Flood events that require flood control regulation are
expected to have a **50 % chance of occurrence each year**" (FACT). *Section 7 takeover is a common
event, not an emergency.*

### 2.5 Why regulation reverses at the extreme: the discharge regulation schedule

Both Corps manuals carry an override that inverts the reservoir's behaviour once filling threatens the
structure. Howard Hanson: "During rare high runoff floods, continued regulation according to the normal
flood control procedures could result in a premature filling of the reservoir requiring discharges
**exceeding the peak that would have occurred under pre-project conditions**. The Discharge Regulation
Schedule (DRS), expressing discharge in terms of reservoir inflow … will be used to determine the
minimum release rate for large floods" (FACT). Mud Mountain's spillway design flood routes a peak
inflow of **252,000 cfs to an outflow of 245,000 cfs** — the project passes **97 %** of the design
flood (FACT — MMD WCM §8.02a(2)). Howard Hanson's PMF routing yields a maximum spillway outflow of
**108,000 cfs** at surcharge elevation 1,223.9 ft (FACT).

This is the mechanism behind the shape of the regulated frequency curve in §2.8 and behind the single
most important safety statement the platform can make about a dam: **at sufficiently extreme forcing a
flood-control reservoir stops attenuating and begins transmitting.** It is also why "the dam will
hold" and "the dam will protect us" are different claims, and the platform is already forbidden from
making either (`HYDROLOGY.md` §13).

### 2.6 Evacuation is the second-flood constraint

Emptying the pool is as rule-bound as filling it. 33 CFR 208.11 requires that water in flood-control
space "shall be evacuated **as rapidly as can be safely accomplished without causing downstream flows
to exceed the controlling rates**" (FACT). On the Skagit, "when the flow at Concrete recedes to
90,000 cfs, evacuation of Ross can commence", and evacuating Upper Baker must not "push Concrete back
above its peak or cause a secondary peak" (FACT). In November 1995 the RCC *delayed* Upper Baker
evacuation until nearly a day after the Concrete crest because field engineers reported levees holding
but at risk from duration — costing Mount Vernon "0.5 feet above major damage stage for an extra half
day" while lowering the initial height (FACT). Mud Mountain may raise releases from 12,000 to
17,600 cfs "if forecasts indicate that expedited evacuation is required to provide for control of an
expected subsequent flood" (FACT).

**Therefore a reservoir's remaining buffer during a multi-pulse atmospheric-river sequence is a
function of the *next* storm's forecast, not only of the current one** (INFERENCE). December 2025 was
"six atmospheric river pulses over nearly two weeks" (FACT — USACE, via DVIDS 2026-07).

### 2.7 Section 7: what the authority actually is

Section 7 of the Flood Control Act of 1944, codified at **33 U.S.C. § 709**, requires the Secretary of
the Army to prescribe regulations for the use of storage allocated to flood control or navigation at
*any* reservoir built wholly or partly with federal funds for those purposes, and requires the project
to be operated accordingly. The implementing regulation is **33 CFR § 208.11** (FACT — uscode.house.gov;
law.cornell.edu). Key clauses, verbatim from the fetched text of 208.11:

- The Corps *prescribes*; **the project owner executes** the water control plan day to day.
- The owner must provide instrumentation to record and transmit hydrometeorological and reservoir data
  "on a **real-time basis**", report "on a **timely basis**", and keep the storage space "available for
  flood control … in accordance with the water control agreement".
- **"During any emergency that affects flood control and/or navigation, the Corps of Engineers may
  temporarily prescribe regulation of flood control or navigation storage space on a day-to-day
  (real-time) basis without request of the project owner."**
- **Deviation** from the approved plan requires advance approval from the Chief of Engineers, except
  for dam-safety emergencies, which must be reported "by the fastest means of communication available"
  and confirmed in writing the same day.

Three platform-relevant consequences (INFERENCE):

1. Section 7 status is a **binary, time-stamped state of a reservoir** — "Corps-directed" vs
   "owner-directed" — with a named legal basis. It is knowable and it changes the meaning of every
   release. On the Skagit it flipped on **2025-12-08**, and again at **08:30 on 2025-12-15** when
   natural flows were forecast to exceed 90,000 cfs at Concrete within eight hours (FACT — USACE
   Seattle District release of 2025-12-13 and follow-ups, as recorded in
   `docs/research/event-zero-december-2025-western-washington-floods.json`).
2. There is **no public feed for Section 7 status**. It appears in press releases and in the
   `-RAW`/`-COMPUTED` provenance tags of the CWMS series, not as a field (OPEN QUESTION).
3. A **deviation** is the legal instrument by which FIRO is trialled before a manual is rewritten
   (§2.9). Deviations are approved, dated documents — again not in any feed found.

Section 7 reservoirs in scope for western Washington: **Ross (Seattle City Light), Upper Baker (Puget
Sound Energy), Wynoochee (Tacoma Public Utilities)** (FACT — USACE December 2025 summary).

### 2.8 Regulation breaks flood-frequency analysis, and the break is structured

Bulletin 17C's procedures "do not cover watersheds where flood flows are appreciably altered by
reservoir regulation, watershed changes, or hydrologic nonstationarities" (FACT — Bulletin 17C, via
the fetched search summary of the USGS TM 4-B5 text; the PDF itself was not fetched). The Skagit study
states the practical consequence flatly: **"regulated peak flow data do not fit any statistical
distribution such as the Log Pearson type III (used to fit unregulated peak flow data)"** (FACT).

The regulated curve is therefore built piecewise — observed regulated peaks for frequent events,
simulated reservoir routing of synthetic unregulated hydrographs for rare ones — and it carries
**visible discontinuities at the regulation trigger points**: "The regulated frequency curve for peak
annual flow at Concrete shows discontinuities or slope changes at regulated flows of about **62,000
and 90,000 cfs**. … The regulated curve **does not merge back into the unregulated frequency curve** at
high exceedance frequencies" (FACT).

Two things the platform must take from this (INFERENCE):

- Any "percentile of record" or "return period" computed at a **regulated** gauge is a statement about
  an operating policy, not about the basin — and it silently changes whenever the policy or the
  reservoir's pre-storm state changes. This is exactly why every modern Skagit peak carries USGS
  qualification code 6, *discharge affected by regulation or diversion* (FACT — noted in
  `flood-genesis-mechanisms-2026-08-24.md` §6.5).
- The *shape* of the regulation effect is knowable and non-monotonic (§3). It is legitimate to display
  it; it is not legitimate to fit it.

### 2.9 FIRO: buying storage with forecast skill

Forecast-Informed Reservoir Operations replaces (or augments) a fixed guide curve with a release rule
conditioned on a streamflow forecast. The best-documented implementation, **Ensemble Forecast
Operations (EFO)**, models reservoir operations *for each ensemble member individually*, computes the
probability of reaching a critical threshold, and releases only enough to hold that risk below a
declared tolerance (FACT — Delaney, Mendoza, Whitin & Hartman 2020, *WRR* 10.1029/2019WR026604; the
Wiley full text returned 403, so the quantitative summary below is from the CW3E publication notice and
the FVA, both fetched).

Results at Lake Mendocino (111,000 ac-ft, Russian River, CA):

| Alternative | Description | Increase in median 10 May storage |
|---|---|---|
| Existing operation | 1986 WCM guide curve + 2003 flood-control diagram | 0 % (baseline) |
| **EFO** | no traditional guide curve; 15-day ensemble drives releases | **27 %** |
| Hybrid EFO | baseline + variable buffer pool; used in WY2019/WY2020 deviations | 15 % |
| **Modified Hybrid EFO** | Hybrid + "corner-cutting" from 15 Feb to aid refill — **preferred** | **20 %** |
| Five-day deterministic | alternative guide curves ±11,000/10,000 ac-ft, 5-day deterministic | 18 % |

(FACT — Lake Mendocino FIRO Final Viability Assessment, Table E.1, fetched PDF.) Real operations under
two USACE **major deviations** produced a **19 % (>11,000 ac-ft) storage increase by end of winter in
WY2020 — the third driest year in a 127-year record** (FACT). The economic assessment put total
estimated annual benefits at **$9.4 M** for Modified Hybrid EFO ($9.9 M for EFO), positive in every
category except hydropower. A flood-risk study "found **no significant difference** between the baseline
and the FIRO alternatives when measuring damages to structures and contents"; on populations at risk,
all FIRO alternatives *reduced* risk upstream of Hacienda Bridge (FACT). Delaney et al. 2020 report a
**33 % increase in median 10 May storage** over a 26-year (1985–2010) hindcast with a **61-member,
15-day** ensemble and "no marked changes in flood frequency for locations downstream" (FACT — CW3E
publication notice).

**Prado Dam** (Santa Ana, CA) is the operational counter-example that is already permanent-ish:
**344,359 acre-feet conserved across WY2016–WY2026**, conservation pool raised from **505 ft to 508 ft**
by multi-year deviation, FIRO operational since **February 2025**, formal WCM update targeted for 2030
(FACT — cw3e.ucsd.edu/firo_prado).

**Pacific Northwest status (FACT — cw3e.ucsd.edu/firo_hhd and /firo_willamette, fetched 2026-08-24):**

- **Howard A. Hanson Dam** — Preliminary Viability Assessment *in progress*. Steering Committee
  convened September 2023; Work Plan completed August 2024; **PVA publication targeted December 2026**.
  Co-chairs CW3E (Ralph), USACE ERDC (Talbot), Tacoma Water (Vaughan); members include NWRFC, NMFS,
  King County, and the Muckleshoot Indian Tribe. Three stated objectives: winter flood risk reduction,
  municipal supply for ~700,000 people, and summer/fall flow augmentation for listed Chinook and
  steelhead. Stated framing numbers: **~$21.5 billion in flood damages prevented since 1962**, and
  **atmospheric rivers account for over 93 % of Washington's flood damage costs**.
- **Willamette Valley** — 13 USACE dams, ~11,500 mi², work plan approval "anticipated mid-late 2026",
  first Steering Committee meeting September 2025. No results.
- **No FIRO effort exists for the Skagit, Baker, White, Cedar or Snoqualmie** as of 2026-08-24 (FACT —
  the CW3E FIRO index lists only Howard A. Hanson, Prado, Russian River, Seven Oaks, Willamette,
  Yuba & Feather).

**The transferability limit, stated by the FVA itself.** The FVA opens with "the analysis, results, and
conclusions of the FVA are **only applicable to Lake Mendocino**" (FACT). More usefully, it names the
precise reason a Russian River result cannot be lifted to the Cascades: "Since the elevation of the
Russian River watershed is **normally well below the snowline**, especially during warm AR events,
**temperature forecasts are not a significant source of streamflow forecast error or uncertainty**"
(FACT). Western Washington's flood-generating basins sit *astride* the transient snow zone, so
freezing-level error is a first-order inflow-forecast error there and is not in the Mendocino error
budget at all (INFERENCE — see §5).

Forecast-skill anchors from the FVA (CNRFC, cool season, Lake Mendocino watershed, FACT):

| Lead | 1 d | 2 d | 3 d | 4 d | 5 d |
|---|---|---|---|---|---|
| 24-h QPF R² | 0.83 | 0.76 | 0.65 | 0.54 | 0.39 |

24-h inflow R² falls from **0.9 at one day to just above 0.5 at five days**; forecasts of *no*
significant rainfall had a **hit rate of 0.97**; five-day inflow errors above 10,000 ac-ft were rare
over 1985–2010 (FACT). The asymmetry matters: skill at forecasting *dry* is what lets an operator keep
encroached water, and skill at forecasting *wet* is what lets an operator pre-release.

### 2.10 The downstream channel is not stationary either

Mud Mountain's manual records that "due to **aggradation in the White River channel** and encroachment
in the flood plain, the White River can no longer carry the planned maximum discharge from Mud Mountain
Dam of 17,600 cfs without some damage occurring" (FACT). NWS's own official flood categories on the
Mud Mountain **outflow** gauge MMRW1 are flow-defined at **action 4,500 / minor 9,000 / moderate
12,000 / major 14,000 cfs** (FACT — `api.water.noaa.gov/nwps/v1/gauges/MMRW1`, fetched 2026-08-24).
**The dam's authorised maximum release (17,600 cfs) exceeds the major-flood threshold on its own
outflow gauge by 26 %** (INFERENCE from the two fetched facts). A reservoir's release schedule and the
downstream rating are drifting apart.

Sedimentation moves the capacity table too. HHD's manual records a loss of **1,384 ac-ft** of storage
since the 1961 original survey (**1,913 ac-ft** in the conservation pool) (FACT). §3 shows the live
storage series now sitting **3 % (HHD) and 7 % (MMD)** below the manuals' published capacity tables at
the same elevation — direction consistent with sedimentation, magnitude not attributed (OPEN QUESTION).

This is the same class of finding as the Mount Vernon stage-discharge drift already recorded in
`flood-genesis-mechanisms-2026-08-24.md` §7.1 (1906: 180,000 cfs → 37.00 ft; 2021: 127,000 cfs →
36.99 ft; 2025: 133,000 cfs → 37.73 ft). The 2013 documentation preserves the *old* Mount Vernon
rating used by the Ross and Upper Baker water control manuals — 25.0 ft = 53,200 cfs, 32.7 ft =
100,300 cfs "major damage", 36.60 ft = 141,500 cfs, 38.1 ft = 160,000 cfs (FACT — Table 27). Those
pairs are ~10 % higher in flow-for-stage than the 2025 observation. **The dams are still being operated
against a stage-discharge relation that the river has left behind** (INFERENCE).

---

## 3. Quantitative anchors

### 3.1 Project physical and allocation constants

| Quantity | Value | Context | Source |
|---|---|---|---|
| Ross active flood-control storage | **120,000 ac-ft** (120,051 ac-ft "total active flood-control storage") | Dec 1 – Mar 15; established 1953; an original 1950 plan required 200,000 ac-ft and was reduced | Skagit 2013 §2.4.9, §3.7 (FACT) |
| Ross active storage, full pool → lowest sluice (1,265 ft) | 1,434,796 ac-ft | flood pool is **8.4 %** of active storage | Skagit 2013 §3.7 (FACT) |
| Ross normal full pool / spillway crest / spillway capacity | 1,602.5 ft (SCL datum) / 1,582 ft / 90,000 cfs at full pool, 121,000 cfs at surcharge 1,608 ft | | Skagit 2013 §3.7 (FACT) |
| Ross "ideal" maximum release / project discharge limit | 25,000 cfs / 26,000–28,000 cfs | limit that delayed 1995 evacuation by ~2 days | Skagit 2013 §4.4.2.4.1, §2.4.9.5 (FACT) |
| Upper Baker flood storage | **74,000 ac-ft** (16,000 from 1956 licence + 58,000 authorised 1977 under §209 PL 87-874) | Nov 15 – Mar 1 | Skagit 2013 §3.2 (FACT) |
| Upper Baker active storage / full pool / spillway | 180,128 ac-ft / 727.77 ft NAVD88 / 48,000 cfs at full pool, 60,000 cfs at max design | minimum outflow 5,000 cfs during flood ops | Skagit 2013 §3.2 (FACT) |
| Lower Baker authorised flood storage | **none**; cannot draw down while Upper Baker is storing | active storage 116,770 ac-ft; outlet 40,000–41,000 cfs | Skagit 2013 §3.2 (FACT) |
| Howard Hanson winter flood storage | **~103,000 ac-ft** at pool 1,075 ft; top of flood 1,206 ft = 104,266 ac-ft | AWSP Phase I summer pool 1,167 ft (+20,000 ac-ft Tacoma SSWR, +5,000 ac-ft §1135) | HHD WCM §7.03; A2W levels (FACT) |
| Howard Hanson SPF | peak **65,000 cfs**, 5-day volume **190,000 ac-ft** | 5-day SPF volume is **1.84×** the flood pool | HHD WCM §8.02b (FACT) |
| Howard Hanson PMF routing | max spillway outflow 108,000 cfs at surcharge 1,223.9 ft | | HHD WCM §8.02a (FACT) |
| Mud Mountain flood storage / spillway crest | **106,000 ac-ft** below crest el. 1,215 ft | reservoir is **empty** except during regulation (live min storage 3 ac-ft) | MMD WCM §8.02c; A2W (FACT) |
| Mud Mountain 1986 spillway design flood | inflow **252,000 cfs** → outflow **245,000 cfs** | project passes **97 %** of the SDF | MMD WCM §8.02a (FACT) |
| Mud Mountain authorised maximum release | **17,600 cfs**; 23-ft tunnel alone can pass 21,500 cfs | vs NWS major-flood category 14,000 cfs on MMRW1 | MMD WCM §7.02a; NWPS (FACT) |

### 3.2 Control fraction and effectiveness limits

| Quantity | Value | Source |
|---|---|---|
| Ross + Upper Baker share of drainage area at Mount Vernon | **39 %** (61 % uncontrolled); above Concrete 1,214 / 1,523 mi² | Skagit 2013 §2.4.9.1, §3.1 (FACT) |
| Ross + Upper Baker share of mean annual runoff at Mount Vernon | **32 %** (68 % uncontrolled) | Skagit 2013 §2.4.9.1 (FACT) |
| Sauk drainage area / share of uncontrolled area | 732 mi² / "just over 50 %" | Skagit 2013 §3.3 (FACT) |
| Sauk contribution to Concrete peak, 1990 / 1995 / 2003 / 2006 / 100-yr | 45 % / 46 % / 64 % / 59 % / 52 % | Skagit 2013 Table 12 (FACT) |
| Exceedance the Skagit system can hold below lower-valley damage | **4–5 % (20–25 yr)** | Skagit 2013 §2.4.9.1 (FACT) |
| Uncontrolled contribution at the 50-yr event, delivered to Mount Vernon | **175,000 cfs**, "exceeds the current levee capacity" | Skagit 2013 §2.4.9.1 (FACT) |
| Howard Hanson control fraction above Auburn | **55 %** | HHD WCM §7.03a (FACT) |
| Mud Mountain control fraction at Puyallup | **42 %** | MMD WCM §7.04c (FACT) |
| Lower-valley levee hydraulic capacities, Skagit | ~**80,000 – 150,000 cfs** across 16 diking districts, 45,000 acres | Skagit 2013 §7.0 (FACT) |

### 3.3 The regulation effect on the frequency curve — Skagit River near Concrete

From Table 22 of the 2013 documentation (weighted regulated hydrographs, "infinite levee" routing);
the reduction column is my arithmetic (INFERENCE):

| Recurrence | Unregulated Concrete (cfs) | Regulated Concrete (cfs) | Peak reduction | Regulated Mount Vernon (cfs) |
|---|---|---|---|---|
| 2-yr | 77,300 | 77,300 | **0.0 %** | 76,900 |
| 5-yr | 120,500 | 101,100 | 16.1 % | 92,900 |
| 10-yr | 153,300 | 127,700 | 16.7 % | 119,000 |
| 25-yr | 201,200 | 165,300 | **17.8 %** (max) | 149,800 |
| 50-yr | 229,300 | 189,100 | 17.5 % | 167,600 |
| 75-yr | 255,500 | 211,400 | 17.3 % | 192,300 |
| 100-yr | 272,400 | 225,900 | 17.1 % | 206,500 |
| 250-yr | 325,400 | 279,700 | 14.0 % | 244,700 |
| 500-yr | 363,600 | 324,400 | **10.8 %** | 282,600 |

**The effectiveness curve is a hump.** Zero at the 2-year event (regulation is never triggered),
maximum near the 25-year event, and decaying thereafter as the fixed 194,000 ac-ft is overwhelmed and
the gate schedules force releases. At Mount Vernon the 100-year reduction is only **12.6 %**
(236,400 → 206,500 cfs) because 61 % of the contributing area enters below the dams (INFERENCE).

Successive study vintages disagree materially on the same quantiles — 100-yr unregulated Concrete was
297,100 (2004 GI), 278,000 (2008 FIS), 272,400 (2011 GI), 272,400 (2013 GI); 100-yr regulated was
235,400 / 209,490 / 214,200 / 225,900 (FACT — Table 26). **The regulated 100-year flow at Concrete has
moved by 26,000 cfs (12 %) across four official studies in nine years, with no change to the dams.**

### 3.4 Historical regulation performance

| Event | What regulation did | Source |
|---|---|---|
| Nov 1990 (first flood) | 194,000 ac-ft stored (112,000 Ross + 82,000 Upper Baker); outflows held to 5,000 cfs; Ross peak inflow 46,000 cfs, U. Baker 33,000 cfs | Skagit 2013 §2.4.9.4 (FACT) |
| Nov 1990 (second flood) | 153,900 ac-ft stored (100,000 + 53,900); **Fir Island levee failed twice**, artificially depressing the Mount Vernon crest | Skagit 2013 §2.4.9.4 (FACT) |
| Nov 1995 | Ross filled to 1,602.38 ft using **118,623 of 120,051 ac-ft (98.8 %)**, within **0.12 ft** of full flood pool; U. Baker used 63,800 of 74,000 ac-ft; Ross outflow ≤13,500 cfs; **stage reduction ~5 ft at Concrete, ~2 ft at Mount Vernon** | Skagit 2013 §2.4.9.5 (FACT) |
| Oct 2003 | Record Concrete crest 42.21 ft *despite* regulation; Mount Vernon 36.2 ft, a foot below 1990/1995 | Skagit 2013 §2.4.9.6 (FACT) |
| Dec 1977 (HHD flood of record, peak) | inflow 36,200 cfs → release 10,000 cfs; Auburn peak **9,920 cfs vs natural 35,000 cfs** (72 % reduction) | HHD WCM §8.02c (FACT) |
| Feb 1996 / Jan 2009 (HHD) | pool 1,183.2 ft / 1,188.8 ft; damages prevented **$3.1 B / $4.1 B** (2010 dollars) | HHD WCM §8.02c (FACT) |
| MMD, cumulative through FY1999 | damages prevented **$308,152,000**, of which **$146.1 M** in February 1996 alone | MMD WCM §4 (FACT) |

### 3.5 December 2025 — agency figures and my own computations from the primary series

USACE Seattle District preliminary analysis (published ~2026-07, FACT — DVIDS 570366):

| Project | Result |
|---|---|
| Howard A. Hanson | record pool **1,189.3 ft**, **77,700 ac-ft** (~75 % of flood storage); peak flow reduced ~**58 %**; stage reduced **>5 ft**; **$7.8 B** damages prevented |
| Mud Mountain | ~**70 %** of storage used; Puyallup ~**2 ft** lower; **$215 M** prevented; ~400,000 people in the lower valley |
| Section 7 (Ross, Upper Baker, Wynoochee) | additional **$746 M** prevented |
| Total | **$8.7 B** |

**My computations** (A2W `/cda/reporting/providers/nws/timeseries`, window 2025-12-01T00Z →
2025-12-20T00Z, fetched 2026-08-24; every figure below is reproducible from that query):

| Quantity | Value | Status |
|---|---|---|
| Ross pool, 2025-11-01 → pre-storm minimum (Dec 9 00Z) → peak (Dec 12 12Z) | 1,571.71 ft → 1,584.53 ft → **1,594.53 ft** | FACT (computed) |
| Ross storage over the same points | 715,900 → 851,183 → **962,083 ac-ft** | FACT (computed) |
| **Ross volume absorbed during the event** | **110,900 ac-ft** (= 92 % of the 120,000 ac-ft allocated pool) | FACT (computed) |
| Ross position relative to its Dec 1 rule curve (1,592.11 ft) on Dec 9 | **7.6 ft below** it | INFERENCE (computed vs Table 15) |
| Ross space below top of flood at Dec 9 | ≈ **201,000 ac-ft** ≈ **1.67×** the required 120,000 | INFERENCE (linear extrapolation of the fetched elev–storage pair 1,601.78 ft = 1,043,715 ac-ft at 11,260 ac-ft/ft) |
| **Fraction of Ross's *designated* flood pool occupied at peak** | **≈ 25 %** | INFERENCE (computed) |
| Ross peak inflow / minimum outflow | **50,099 cfs** (Dec 11 09Z) / **389 cfs** — 99.2 % of peak inflow withheld | FACT (computed); matches USACE's public "held back ~99 %" |
| Upper Baker pool / storage, minimum → peak (Dec 12 01Z) | 698.41 → **712.59 ft**; 90,161 → **143,355 ac-ft** | FACT (computed) |
| **Upper Baker volume absorbed** | **53,194 ac-ft** (= 72 % of its 74,000 ac-ft pool) | FACT (computed) |
| **Fraction of Upper Baker's designated pool occupied at peak** (top of conservation 711.56 ft = 139,002 ac-ft) | **≈ 5.9 %** | INFERENCE (computed) |
| Upper Baker peak inflow / minimum outflow | 28,910 cfs / 37 cfs | FACT (computed) |
| Howard Hanson storage at the record pool 1,189.30 ft, live series | **75,171.5 ac-ft** (**72.6 %** of the 103,561 ac-ft pool) — vs USACE's published 77,700 ac-ft / 75 % | FACT (computed) |
| Mud Mountain peak pool / storage (Dec 13 04Z) | **1,185.22 ft** / **74,642.6 ac-ft** = **70.4 %** of 106,000 ac-ft | FACT (computed) |
| **Minimum "hours to top of flood pool at current net inflow", Howard Hanson** | **≈ 33 h**, at 2025-12-12T00Z (net inflow 13,377 cfs, 36,476 ac-ft remaining) | INFERENCE (computed; 1 cfs·h = 0.0826446 ac-ft) |
| Green nr Auburn observed peak | **12,100 cfs** — i.e. essentially the 12,000 cfs authorised control flow | FACT (`event-zero…json`, USGS 12113000) |

**The two Ross percentages are the headline.** Measured against the rule curve, Ross was a quarter
full. Measured against the water it actually removed from the Skagit, it absorbed almost a full design
flood pool. Both are true; only the second describes what happened.

### 3.6 FIRO anchors

| Quantity | Value | Source |
|---|---|---|
| Lake Mendocino WY2020 storage gain under major deviation | **+19 %, >11,000 ac-ft**, in the 3rd driest year of 127 | FVA Fig. E.2 (FACT) |
| Median 10 May storage gain, modelled | EFO **27 %**, Modified Hybrid EFO **20 %**, 5-day deterministic **18 %**, Hybrid EFO **15 %** | FVA Table E.1 (FACT) |
| Delaney et al. 2020 hindcast (1985–2010, 61 members, 15 d) | **+33 %** median 10 May storage, no marked downstream flood-frequency change | CW3E notice (FACT) |
| Estimated annual benefit | **$9.4 M** (Modified Hybrid EFO); **$9.9 M** (EFO); hydropower negative | FVA (FACT) |
| Prado Dam conserved, WY2016–WY2026 | **344,359 ac-ft**; pool 505 → 508 ft; operational since Feb 2025 | cw3e.ucsd.edu/firo_prado (FACT) |
| Howard Hanson FIRO PVA target | **December 2026** | cw3e.ucsd.edu/firo_hhd (FACT) |
| HHD damages prevented since 1962 (CW3E framing) | **~$21.5 B**; ARs = **>93 %** of WA flood damage cost | cw3e.ucsd.edu/firo_hhd (FACT) |

---

## 4. What is settled, what is emerging, what is contested

**Settled (established).**

- Control fraction bounds effectiveness, and the bound is published per project (55 % HHD, 42 % MMD,
  39 % Skagit). No operating change alters it.
- Regulated peak-flow records are not fittable by standard flood-frequency distributions, and
  Bulletin 17C excludes them by scope.
- The seasonal rule curve is a legal instrument under 33 CFR 208.11 with a defined deviation process,
  and the Corps may take real-time control of a Section 7 project without owner request.
- Reservoirs reduce frequent-to-moderate peaks strongly and rare peaks much less; at the design flood
  they approach pass-through by rule (discharge/gate regulation schedules).
- FIRO increases carryover storage without a measurable increase in modelled structural flood damage at
  Lake Mendocino, and has been implemented under multi-year deviations at Prado.

**Emerging.**

- FIRO in snow-influenced, maritime PNW basins. Howard Hanson's PVA is not published (target
  December 2026); Willamette's work plan is not approved. **There is no published FIRO viability result
  for any Washington reservoir as of 2026-08-24** (FACT).
- Machine-learning probabilistic inflow forecasts inside USACE operations. The NWDP catalog now carries
  eleven **HydroForecast** quantile series (Q01…Q99) plus observation-blended variants for HAH and MMD
  (FACT — CWMS catalog, fetched 2026-08-24). Their read paths returned no values (§6.3), so their
  operational role is unknown (OPEN QUESTION).
- Rule-curve revision under a changing snowpack. The Skagit settlement's move of the full-storage date
  from **December 1 to November 1** and the increase of Ross's requirement from **120,000 to
  165,000 ac-ft** is the first substantive PNW rule-curve change in decades (FACT for the numbers as
  reported by Salish Current 2026-03-12; **not confirmed on a Seattle City Light or USACE page** —
  the March 2026 SCL fact sheet confirms only the 90,000 cfs Corps-control trigger). Treat the volume
  as OPEN QUESTION until a primary document is fetched.

**Contested.**

- **Damages-prevented figures.** Mud Mountain's own water control manual puts *cumulative* damages
  prevented through FY1999 at **$308 M**, of which $146.1 M was February 1996. USACE's December 2025
  release puts **$215 M** for that single event, and **$7.8 B** for Howard Hanson. Howard Hanson's
  manual gives $3.1 B (1996) and $4.1 B (2009) in 2010 dollars. These are HEC-FDA-class estimates whose
  magnitude is dominated by assumed inventory, price level and levee-failure assumptions, and they are
  not comparable across vintages (INFERENCE). They are advocacy-adjacent numbers and the platform
  should never render one as a fact about a river.
- **What the December 2025 dams actually saved on the Skagit.** USACE's preliminary estimate was
  **4–5 ft** of stage reduction at Mount Vernon; Skagitonians asserted **7–8 ft** and a ~45 ft
  no-dam crest (FACT that both claims were made; the second is unverified — recorded in
  `event-zero…json`). SCL's own fact sheet credits "careful planning and coordinated water storage
  management … **and with some help from a forecast that did not fully materialize**" (FACT). The
  attribution between operations and forecast bust is genuinely unresolved.
- **The 1815/1856 Skagit floods** (510,000 / 340,000 cfs) are excluded from the frequency analysis by
  USGS reclassification to "estimates" and by concern that decadal woody-debris jams may have created
  dam-break-like high-water marks (FACT). This is the upper anchor of the regulated curve and it is
  contested for regulatory reasons.
- **Elevation–storage capacity tables.** Live storage series sit **3.3 % (HHD)** and **7.2 % (MMD)**
  below the manuals' tables at the same elevation, and HHD's storage series is **non-monotonic in
  elevation** at the December 2025 peak (§6.4). Whether this is sedimentation, a revised survey, or a
  computation lag is unresolved (OPEN QUESTION).

---

## 5. Western Washington specificity — what transfers and what does not

**Transfers from California FIRO:**

- The *method*: risk-based ensemble operation with a declared risk tolerance; deviation-then-manual
  as the legal pathway; the observation that release headroom below channel capacity is a priced
  forecast-uncertainty margin.
- The *finding* that forecast skill at 1–5 day lead is already adequate for meaningful operational
  flexibility in AR-dominated basins.
- The *governance* finding: a research–operations steering committee with the RFC, the operator, the
  regulator, tribes and downstream interests at the same table is what made deviations approvable.

**Does not transfer, or transfers with a large penalty:**

1. **Freezing level is a first-order error term here and is absent from Mendocino's error budget.**
   The FVA states the Russian River sits below the snowline so temperature forecasts are not a
   significant error source (FACT). The Green, Skagit, Sauk, Snoqualmie and White basins span the
   transient snow zone; the December 2025 event had snow levels of 6,000–9,000 ft (FACT —
   `HYDROLOGY.md` §12). An inflow-forecast error budget for Howard Hanson must include snow-level
   error explicitly, and Mendocino's R² table is an **upper bound**, not an estimate, for PNW skill
   (INFERENCE).
2. **Mendocino is one reservoir on one river. The Skagit is two operators, three agencies and one
   Corps control point.** Ross (SCL) and Upper Baker (PSE) are regulated jointly by the Seattle
   District RCC against a *shared* Concrete trigger, with sequencing constraints between them ("care is
   needed when evacuating Upper Baker to ensure that the increased outflow from Ross does not push
   Concrete back above its peak") and a hard constraint that Lower Baker may not draw down while Upper
   Baker is storing (FACT). Single-reservoir FIRO results say nothing about the coupled problem.
3. **The dominant flood contributor is unregulated.** The Sauk supplies half the uncontrolled area and
   up to 64 % of the observed Concrete peak (FACT). No amount of forecast skill at Ross changes that;
   FIRO's benefit on the Skagit would be concentrated in *water supply/power/ecology*, not in flood
   reduction (INFERENCE).
4. **Mud Mountain is a dry, single-purpose reservoir** (live minimum storage 3 ac-ft). It has no
   conservation pool to trade, so classical FIRO — buy carryover storage with forecast skill — has
   nothing to buy. Its FIRO-analogue benefit would be *earlier, larger pre-release* and *evacuation
   sequencing between AR pulses* (INFERENCE).
5. **Duration, not intensity, is the western-Washington extreme.** With hourly intensities in the
   largest western-Cascades floods around 2.7 ± 0.9 mm h⁻¹ (FACT — recorded in
   `flood-genesis-mechanisms-2026-08-24.md` §2.4) and December 2025 delivering six AR pulses over two
   weeks, the binding reservoir constraint is *volume across a sequence*, not peak attenuation of one
   hydrograph. Mendocino's metrics (median 10 May storage) do not measure this.
6. **The regulated frequency curve's shape is basin-specific.** The Skagit's hump (0 % → 18 % → 11 %)
   is a product of a 90,000 cfs trigger, 194,000 ac-ft, and a 61 % uncontrolled area. Howard Hanson,
   with 55 % control and a 12,000 cfs control flow, delivered **58 %** peak reduction in December 2025.
   These are not interchangeable numbers and must be per-project attributes.

---

## 6. What this means for Cascadia Papsukkal

### 6.1 The doctrine change: three buffers, never one

`HYDROLOGY.md` §10 defines flood-buffer capacity as "available flood-control storage (rule-curve
maximum − current storage)". §3.5 shows that single definition producing 25 % for Ross in the event
where Ross removed 110,900 ac-ft from the Skagit. **A `Reservoir` must expose three volumes with three
different meanings, each with its own provenance:**

```
required_buffer_ac_ft   = S(rule_curve_elev_today) − S(pool_now)      # may be NEGATIVE (encroached)
available_buffer_ac_ft  = S(top_of_flood_elev)     − S(pool_now)      # what physically remains
allocated_pool_ac_ft    = S(top_of_flood_elev)     − S(rule_curve_elev_today)   # the policy volume
```

- `required_buffer` negative ⇒ the pool is **into the flood pool** — the state operators call
  encroachment. Render it as a signed quantity, never clipped.
- `available_buffer` is the only one that answers "how much more can it hold".
- **`pool_below_curve = max(0, S(rule) − S(pool))` is a first-class signal in its own right**: it is
  buffer the operator is not obliged to have and may spend on power or supply at any moment. In
  December 2025 it was ~81,000 ac-ft at Ross and ~49,000 ac-ft at Upper Baker (INFERENCE, computed).
  It must be labelled *discretionary*, and it must never be added to `required_buffer` without saying
  which part is which.

Companion rate quantity, directly analogous to the platform's existing time-to-threshold:

```
hours_to_top_of_flood = available_buffer_ac_ft / (0.0826446 × max(0, Q_in − Q_out))
```

computed over a named window, UNKNOWN when net inflow ≤ 0, and always carrying "assumes present
release continues" — because it does not (§2.6). Worked example in §3.5: Howard Hanson bottomed at
≈33 h on 2025-12-12T00Z.

### 6.2 The rule curve is observable — poll it and keep it

The A2W location endpoint returns each project's operating levels, and **"Bottom of Flood Control" /
"Bottom of Flood" is typed `REGULAR` (time-varying) while the others are `CONSTANT`** (FACT, fetched
2026-08-24). On 2026-08-24 it read **1,603 ft for Ross** and **727.70 ft for Upper Baker** — both
essentially at full pool, exactly as Tables 15 and 10 require on 1 October (0 ac-ft of flood storage).
**The REGULAR level *is* the rule curve, published as a current value.**

There is no endpoint that returns it as a series: `/cda/reporting/providers/nws/timeseries?name=ROS.Elev-Forebay.Inst.0.Bottom of Flood Control`
returns an empty body, CWMS `/levels?office=NWDP&level-id-mask=ROS.*` returns `total: 0`, and
`/levels/{level-id}` returns HTTP 500 (FACT, all three fetched). **Therefore: poll
`/providers/nws/locations/{slug}` daily and persist the REGULAR levels as rows with `retrieved_at`.**
That reconstructs the rule curve with correct knowledge time and is the only way a hindcast will ever
know what the curve said on 2025-12-08. `DATA_SOURCES.md` R2 already anticipates
`flood_control_rule_curve` rows; this finding says *which* levels are the curve and that the history
must be built by us, starting now.

Constant levels worth seeding (FACT, fetched): HAH top of flood 1,206 ft / 104,266 ac-ft, bottom of
flood pool 103,561 ac-ft, top of dam 1,228 ft; MMD top of flood 1,215 ft / 106,000 ac-ft (spillway
crest storage listed inconsistently as 102,041 ac-ft), bottom 895 ft; Ross top of flood/normal
1,602.5 ft, top of conservation 1,592.1 ft, spillway crest 1,582 ft, top of dam 1,615 ft; Upper Baker
top of flood 727.77 ft / 212,995 ac-ft, top of conservation 711.56 ft / 139,002 ac-ft (difference
**73,993 ac-ft** — an exact independent confirmation of the licence's 74,000 ac-ft); Lower Baker
"top of flood" = top of normal 442.35 ft, i.e. **no flood pool**.

### 6.3 Official reservoir inflow forecasts exist — use them; the pool forecasts do not read

`HYDROLOGY.md` §10 says "Forecast inflow comes from official sources where published; otherwise the
reservoir's future state is UNKNOWN." **It is published.** NWPS serves reservoir-inflow forecasts as
ordinary gauge objects (FACT, fetched 2026-08-24):

- `GET https://api.water.noaa.gov/nwps/v1/gauges/RODW1/stageflow` → `forecast.issuedTime`
  **2026-08-24T15:10:00Z**, **30 six-hourly points to 2026-09-01T00:00Z**, units **kcfs**, pedts
  `QIIFZ` (inflow, forecast). Same shape for `UBDW1`, `HHDW1`, `MORW1`, `TLRW1`; `MMRW1` is
  **outflow** (`QRIRZ`/`QRIFZ`).
- `MMRW1` carries **official flow-defined categories: action 4,500 / minor 9,000 / moderate 12,000 /
  major 14,000 cfs**, with historic crests 15,200 cfs (1986-11-24), 14,800 (1977-12-02), 14,100
  (1990-01-09). The other reservoir LIDs return `-9999` for all categories — correctly, because a pool
  is not a flood-category location.

This is an **OFFICIAL_FORECAST** source (NWRFC) and it is the missing input for a reservoir-state
horizon. But it must be badged with the constraint that makes it honest: **the RFC forecast already
contains an assumed operating plan.** Howard Hanson's manual: "NWRFC incorporates **the planned
regulation** into the forecast of reservoir elevation and discharge at Auburn" (FACT). So the official
downstream forecast at a regulated point is a *conditional* forecast — conditional on an operating
intention that is not published. Every regulated forecast point in the platform should render that
sentence.

Series that are catalogued but return **no values** on any public path tested (CWMS CDA unversioned,
`MAX_AGGREGATE`, `SINGLE_VERSION`; A2W; NWD Dataquery `ecsv`) — FACT, all attempted 2026-08-24:
`HAH.Elev-Forebay.Ave.1Hour.1Hour.CENWS-COMPUTED-FCST`, `HAH.Elev-Forebay.Ave.6Hours.6Hours.RFC-FCST`,
`MMD.Elev-Forebay…FCST`, `ROS.Flow-In.Ave.6Hours.6Hours.RFC-FCST`,
`ROS.Flow-Loc.Ave.1Hour.1Hour.BLEND-SCL-OBS-CENWS-FCST`, and all
`HAH|MMD.Flow.Inst.1Hour.0.HYDROFORECAST-Q*-FCST`. Their catalog extents run to **2026-09-03T12:00Z**,
so the data exist server-side. **A published forecast pool trajectory is exactly the operator-intent
signal the platform needs; it is advertised and not readable.** Worth an email to the Seattle District
RCC; until then, UNKNOWN with reason "USACE forecast series catalogued but not served".

### 6.4 Do not compute buffer from the storage series

At Howard Hanson's December 2025 peak the reported elevation rose 1,188.98 → **1,189.30 ft** while the
reported storage **fell** 75,257.08 → 75,171.52 ac-ft (FACT, fetched hourly pairs). A single-valued
capacity curve cannot do that: the storage series is not a function of the published elevation series.
Separately, at 1,189.3 ft the manual's Table 2-1 gives **77,706 ac-ft** against the live series'
**75,171 ac-ft** (3.3 % apart) — and USACE's own press release used **77,700**, i.e. the table. Mud
Mountain is worse: at 1,185.22 ft the live series says **74,642.6** against Table 2-1's **80,409**
(7.2 % apart).

**Rule for the platform:** store pool **elevation** as the primary observable, carry the project's
elevation–storage table as a versioned CONFIGURED artifact with its survey date, derive storage as
DERIVED with lineage, and store the provider's storage series *beside* it as an independent OBSERVED
series. When they disagree by more than a declared tolerance, that is a `model_agreement`-class
assessment about the reservoir, not an error to hide. Never mix the two in one arithmetic expression —
the "% of flood pool used" number the public sees depends on which one you picked, and USACE itself
picked differently for HHD and MMD in the same press release.

### 6.5 Datum discipline is worse here than anywhere else in the platform

Every A2W series in scope returns `"vertical_datum": "NGVD29"` — including Upper Baker, whose
licence, manual and A2W level constants all use figures (727.77 ft, 711.56 ft) that the 2013 USACE
document states in **NAVD88** (FACT for both). Ross's Table 15 elevations are in "SCL Datum", footnoted
as **1.79 ft above NGVD29**, yet the A2W "Top of Flood" constant for Ross is 1,602.5 ft — numerically
the SCL-datum value (FACT). USGS reports Ross (12175000) and Diablo/Gorge pool as parameter 00065
"gage height" in project datum, Baker Lake (12191600) as 62615 NAVD88, and Howard Hanson (12105800) as
62614 NGVD29 (FACT — already in `DATA_SOURCES.md` R5). **The `vertical_datum` field in the A2W
response appears to be a service-wide default and must not be trusted.** Treat reservoir pool datum as
CONFIGURED per project, sourced from the water control manual or the licence, never from the feed; and
refuse elevation comparisons across unrecorded datums exactly as `HYDROLOGY.md` §9 already requires for
river stage.

### 6.6 Contract additions

A `Reservoir` entity (none exists today; `packages/contracts/.../visualization.py` has only
`Regulation{class, regulated_by}` and the seed carries `reservoir:*` ids as opaque strings):

| Field | Kind | Notes |
|---|---|---|
| `pool_elevation` + `datum` | OBSERVED | primary observable; datum CONFIGURED per project |
| `storage_derived` | DERIVED | from elevation × versioned capacity table (`table_survey_date`) |
| `storage_reported` | OBSERVED | provider series, kept separately |
| `inflow_computed`, `outflow` | OBSERVED, `method=continuity_difference` | inflow may be negative |
| `rule_curve_elevation_today` | CONFIGURED-from-feed | A2W REGULAR level, `retrieved_at` mandatory |
| `top_of_flood_elevation`, `top_of_dam` | CONFIGURED | manual/licence |
| `required_buffer`, `available_buffer`, `pool_below_curve` | DERIVED | §6.1; signed |
| `hours_to_top_of_flood` | DERIVED, EXPERIMENTAL | §6.1 |
| `control_fraction` at the named control point | CONFIGURED | 0.55 HHD, 0.42 MMD, 0.39 Skagit@MtVernon |
| `control_point_lid`, `objective_flow`, `channel_capacity`, `travel_time_h` | CONFIGURED | §2.4 table |
| `section7_status` | CONFIGURED / UNKNOWN | no feed; `UNKNOWN` with reason by default |
| `operating_authority` | CONFIGURED | `owner` \| `usace_section7` \| `usace_owned` |
| `forecast_inflow` | OFFICIAL_FORECAST | NWPS `/gauges/{lid}/stageflow`, `issuedTime` |

And on `Regulation`, a `control_fraction` plus an `uncontrolled_dominant_gauge` (Skagit → Sauk at Sauk,
USGS 12189500 — which `susceptibility.py` already reads for a different and correct reason).

### 6.7 Copy rules this domain forces

- Never render a reservoir as "protecting" a place. The Corps' own manuals say total control is
  impossible at 42–55 % control fraction, and the Skagit study says major flooding occurs above the
  25-year event "regardless of the flood control regulation".
- Never present a return period or flow percentile at a regulated gauge without the regulation flag and
  a pointer to §2.8. `susceptibility.py` already refuses this for the Skagit by reading the Sauk; the
  same refusal has to reach `headroom.py` and any percentile displayed at Concrete, Auburn or Puyallup.
- Never display "damages prevented".
- When the pool is above the rule curve, say **"encroached into the flood pool by N ft"**, which is the
  operators' own word, not "N % full".

---

## 7. What this domain contradicts or qualifies in the current repo doctrine

1. **`HYDROLOGY.md` §10 — flood-buffer capacity.** "Flood-buffer capacity = available flood-control
   storage (rule-curve maximum − current storage)" is **one of three necessary quantities** and is the
   least informative of the three during a real event. December 2025 at Ross: 25 % by this formula,
   110,900 ac-ft actually absorbed. Requires §6.1's three-buffer definition.

2. **`HYDROLOGY.md` §10 — "The platform never infers dam operations; it reports them."** Correct as a
   prohibition, but incomplete: the *official downstream forecast at a regulated point already embeds
   an inferred operating plan* made by NWRFC in coordination with the Corps (FACT, HHD WCM §6.02b).
   The platform must therefore label the official forecast at MVEW1, Auburn and Puyallup as
   **conditional on an assumed regulation plan**, or it will present an operator decision as a river
   prediction.

3. **`HYDROLOGY.md` §10 — "otherwise the reservoir's future state is UNKNOWN."** Too pessimistic.
   Official NWRFC inflow forecasts are served for RODW1, UBDW1, HHDW1, MORW1, TLRW1 and outflow for
   MMRW1 (FACT, §6.3). Reservoir future state should be UNKNOWN only in the *release* dimension.

4. **`HYDROLOGY.md` §2 — the regulation bullet.** Materially right, three corrections/additions:
   (a) Ross and Upper Baker control **39 %** of the area at Mount Vernon, and this number belongs in
   the doctrine because it caps everything downstream; (b) **Lower Baker has no authorised flood
   storage** and is constrained only against drawing down while Upper Baker stores — the current text
   groups "Upper and Lower Baker" as controlling the Baker; (c) the Cedar bullet should say Chester
   Morse's flood reduction is *incidental* with **no published rule curve or flood release schedule
   found** (OPEN QUESTION carried forward from `reservoirs-dams-and-flood-control.json`).

5. **`HYDROLOGY.md` §9 — hydraulic headroom.** On a regulated reach, `threshold_flow − current_flow`
   is not headroom in the basin sense; it is headroom under a *current release decision that can
   change on the next forecast cycle*. Time-to-threshold on a regulated reach must either carry the
   reservoir's `hours_to_top_of_flood` beside it or be suppressed. `packages/hydrology/headroom.py`
   (37 lines) has no regulation awareness.

6. **`DATA_DOCTRINE.md` §2 — source kinds.** A rule-curve value fetched from A2W is not cleanly
   CONFIGURED (it is not hand-entered) nor OBSERVED (it is a policy, not a measurement). It is a
   *retrieved configuration*: recommend `source_kind=CONFIGURED` with `configured_from_source_id` and
   `retrieved_at` required, so the closed taxonomy holds while provenance survives. Note that
   `DATA_DOCTRINE.md` §2 forbids CONFIGURED values in hazard computation — and a rule curve genuinely
   should not enter a hazard number, only a *state* display. That is a happy accident worth making
   explicit.

7. **`DATA_SOURCES.md` R1/R2.** Three corrections from live fetches on 2026-08-24: (a) the CWMS `/levels`
   endpoint returns `total: 0` for `office=NWDP` and `/levels/{id}` returns HTTP 500 — the levels are
   reachable **only** through A2W `/locations/{slug}`; (b) several `-FCST` series (including forecast
   forebay elevation and eleven HydroForecast quantiles) are catalogued with future extents but return
   **zero values** on CDA, A2W and Dataquery; (c) `vertical_datum` in A2W responses reads `NGVD29`
   uniformly and disagrees with the projects' own documents (Upper Baker NAVD88, Ross SCL datum) — do
   not trust the field.

8. **`flood-genesis-mechanisms-2026-08-24.md` finding 6 (moving Mount Vernon rating).** Reinforced and
   extended: the *dams'* water control manuals encode an even older rating (Table 27: 32.7 ft =
   100,300 cfs "major damage"), so both the forecast target and the operating target are drifting.

9. **`EVENT_ZERO.md` / `HYDROLOGY.md` §12.** "Ross Dam held back ~99 % of inflow" is confirmed at the
   instantaneous peak by primary data (50,099 cfs in, 389 cfs out) and should be stated that way rather
   than as an event-integrated figure — event-integrated, Ross passed roughly 20 % of the inflow volume
   over 2025-12-08…12-20 (INFERENCE, order-of-magnitude from the fetched series).

---

## 8. Open questions

1. **What did the rule curves actually say on 2025-12-08?** Without a stored history of the A2W REGULAR
   levels, the hindcast cannot state required buffer at knowledge time. Start persisting today.
2. **Is there any public feed for Section 7 status, deviation grants, or the Corps' Reservoir Control
   Center directives?** None found. If not, Section 7 state must be a curated, dated CONFIGURED series
   with a citation per transition.
3. **Why do the `-FCST` series return no values, and can read access be arranged?** A published
   forecast pool trajectory would let the platform show *planned* operations without inferring them.
4. **Which elevation–storage table is current for HHD and MMD?** The manuals date from 2011 and 2004;
   live series sit 3 % and 7 % below them. Is there a post-2011 survey, and is the discrepancy
   sedimentation, a lag, or a different reference?
5. **What is the actual Skagit settlement flood-storage requirement?** 165,000 ac-ft with a 1 November
   full-storage date is reported by Salish Current and echoed by Cascadia Daily News; neither SCL's own
   fact sheet nor a FERC filing has been fetched confirming the volume. Also unresolved: how the
   "different management regimes depending on the reservoir's level" work, and whether the 90,000 cfs
   Concrete trigger changes.
6. **What are the Skagit water control manuals' current contents?** Only the 2013 study's excerpts were
   fetched. The Ross and Upper Baker WCMs themselves (which contain the Special Gate Regulation
   Schedule) were not located as public PDFs, unlike HHD (wc/2664) and MMD (wc/2666).
7. **Does Ross's public elevation series use SCL datum or NGVD29?** The 1.79 ft footnote and the A2W
   label are mutually inconsistent, and 1.79 ft is ~20,000 ac-ft of apparent buffer.
8. **Is Wynoochee (Tacoma Public Utilities, NID WA00302) worth ingesting?** It is a named Section 7
   project in the December 2025 damages figure but drains to Grays Harbor, outside the eight seed
   basins.
9. **Chester Morse / Masonry (SPU) and South Fork Tolt (SPU/SCL): is there any published flood
   operating rule?** Carried forward unresolved. Tolt's morning-glory spillway is uncontrolled, which
   means its "flood buffer" is not an operator decision at all.
10. **What is the honest denominator for "percent of flood pool used"?** USACE used the manual table for
    HHD and the live series for MMD in the same press release. The platform must pick one, publish the
    choice, and show the other as a cross-check.
11. **Would FIRO help the Skagit at all?** With 61 % of the area uncontrolled and the Sauk dominant, the
    flood-side benefit may be near zero while the water-supply/ecology benefit is real. No study found.

---

## 9. Sources

**Primary agency documents (fetched and text-extracted locally):**

- [USACE Seattle District, *Hydrology Technical Documentation, Skagit River Basin, WA — Flood Risk Management Study*, Final Report, August 2013](https://www.skagitcounty.net/PublicWorksSalmonRestoration/Documents/Skagit%20River%20Hydrology%20Technical%20Doc_Final_August2013.pdf) — 67 pp; Tables 9, 10, 12, 15, 16, 22, 26, 27 and §§2.4.9, 3.1–3.7, 4.1–4.4, 7.0 used.
- [USACE Seattle District, *Howard A. Hanson Dam Water Control Manual* (redacted), September 2011](https://water.usace.army.mil/cda/documents/wc/2664/Complete_HHD_Rdct.pdf) — 189 pp; §§6.02, 7.02–7.03, 8.02, Table 2-1 used.
- [USACE Seattle District, *Mud Mountain Dam Water Control Manual* (redacted), September 2004](https://water.usace.army.mil/cda/documents/wc/2666/Complete_MMD_Rdct.pdf) — 194 pp; §§4, 6.01–6.02, 7.01–7.05, 8.02, Table 2-1 used.
- [Seattle City Light, *Skagit Project FERC Relicensing Settlement — Managing Flood Risks for Skagit Communities*, March 2026](https://www.seattle.gov/documents/Departments/CityLight/CurrentProjects/SkagitSettlement_FactSheet-FloodMgmt.pdf) — 1 p.
- [33 CFR § 208.11 (Cornell LII)](https://www.law.cornell.edu/cfr/text/33/208.11) — deviation, emergency and owner-obligation clauses quoted. (eCFR itself returned a 302 to an unblock page.)
- [33 U.S.C. § 709 (uscode.house.gov)](https://uscode.house.gov/view.xhtml?req=(title:33+section:709+edition:prelim)) — read via search summary; **statutory text not independently fetched.**

**FIRO:**

- [Lake Mendocino FIRO Steering Committee, *Final Viability Assessment*, 2021 (CW3E)](https://cw3e.ucsd.edu/FIRO_docs/LakeMendocino_FIRO_FVA.pdf) — 141 pp, text-extracted; Table E.1, Fig. E.2, §§1.x, 2.1–2.2 used. Also at [eScholarship](https://escholarship.org/uc/item/3b63q04n).
- [CW3E, FIRO programme index](https://cw3e.ucsd.edu/firo/) · [Howard A. Hanson Dam FIRO](https://cw3e.ucsd.edu/firo_hhd/) · [Prado Dam FIRO](https://cw3e.ucsd.edu/firo_prado/) · [Willamette Valley FIRO](https://cw3e.ucsd.edu/firo_willamette/) — all fetched 2026-08-24.
- [CW3E publication notice for Delaney, Mendoza, Whitin & Hartman (2020), *WRR* 10.1029/2019WR026604](https://cw3e.ucsd.edu/cw3e-publication-notice-forecast-informed-reservoir-operations-using-ensemble-streamflow-predictions-for-a-multi-purpose-reservoir-in-northern-california/) — **the Wiley full text returned HTTP 403; the +33 %, 61-member, 15-day and 1985–2010 figures are from this notice, not from the paper.**
- USBR, *Lake Mendocino: Economic Benefits of Alternative Reservoir Operations* — **PDF fetched but not text-extractable; not used.**

**December 2025 event:**

- [USACE, "USACE dams reduced flood risk during December 2025 storms…" (DVIDS 570366, printable)](https://www.dvidshub.net/news/printable/570366) — all damages-prevented and storage-percentage figures. (The army.mil mirror returned HTTP 403.)
- `docs/research/event-zero-december-2025-western-washington-floods.json` — Section 7 takeover times, Ross peak pool, gauge peaks, levee failures (in-repo, previously verified).

**Live API verification, all fetched 2026-08-24 (see §6.2–6.5 for exact queries):**

- USACE A2W: `https://water.usace.army.mil/cda/reporting/providers/nws/locations/{ros|ubk|hah|mmd|sha|dia}` and `/providers/nws/timeseries?name=…&begin=…&end=…`
- USACE CWMS CDA: `https://cwms-data.usace.army.mil/cwms-data/catalog/TIMESERIES?office=NWDP&like=…&include-extents=true`, `/timeseries`, `/levels`
- NOAA NWPS: `https://api.water.noaa.gov/nwps/v1/gauges/{RODW1|UBDW1|HHDW1|MMRW1|MORW1|TLRW1}` and `/stageflow`
- NWD Dataquery (legacy): `https://www.nwd-wc.usace.army.mil/dd/common/web_service/webexec/ecsv?id=…` (TLS chain fails strict verification; `curl -k` required)

**Secondary / press (used only where labelled, and flagged as unconfirmed against a primary source):**

- [Salish Current, "Skagit County urged to approve FERC licensing agreement — with conditions", 2026-03-12](https://salish-current.org/2026/03/12/skagit-county-urged-to-approve-ferc-licensing-agreement-with-conditions/) — Ross flood storage 120,000 → **165,000 ac-ft**, drawdown start moved to November.
- [Cascadia Daily News, "Skagit County, tribes approve of Seattle City Light 'compromise' — with caveats", 2026-03-11](https://www.cascadiadaily.com/2026/mar/11/skagit-county-tribes-approve-of-seattle-city-light-compromise-with-caveats/) — confirms the **December 1 → November 1** date change; does not give volumes.

**Not independently fetched (claims relying on them are labelled INFERENCE or flagged):**

- Bulletin 17C (USGS TM 4-B5) — the scope-exclusion sentence for regulated watersheds is quoted from a search-result summary, not from the fetched PDF.
- USACE EM 1110-2-1415 / 1110-2-1417 — referenced, not fetched.
- Di Baldassarre et al., "reservoir effect" / levee effect literature — **not fetched; the session's web-search budget was exhausted before this thread could be pursued.** No claim in this corpus rests on it.
- Ross and Upper Baker Water Control Manuals (including the Special Gate Regulation Schedule) — not located as public documents; all rules quoted are as paraphrased in the 2013 USACE study.
