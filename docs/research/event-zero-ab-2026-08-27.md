# Event Zero A/B — what the Tier 0 correction actually bought, and what it cost

Milestone brief §13 (the old-vs-new A/B) run on the harness of brief §21
(`packages/hydrology/src/cascade_hydrology/hindcast.py`), driven by
`scripts/hindcast_event_zero.py`. Every number below is a **measured output of a replay**, not a
restatement of `tier0-measured-basis-2026-08-26.md`: 792 evaluations — six basins × two method
arms × 66 knowledge times.

Labels per `docs/research/README.md`: **FACT** = computed for this document; **INFERENCE** =
reasoned from those facts; **OPEN QUESTION** = unresolved. §12 has the reproduction.

> ## The one sentence that must travel with every figure here
>
> **This is a RETROSPECTIVE replay, not a knowledge-time replay.** It says what was
> *reconstructable at time T from evidence that existed at T*. It does **not** say what this
> platform knew or would have shown, because this platform did not exist in December 2025. The
> strict knowledge-time replay of the same window was also run and returns **UNKNOWN at all 792
> evaluations** (§2). Nothing here may be quoted as "Cascadia Papsukkal would have warned N days
> earlier".

---

## 1. Verdict

**The governing question, as the brief frames it: did the corrected method reveal material
deterioration earlier while remaining quiet when no meaningful deterioration existed?**

**Earlier: yes, on five of six basins — 24 to 72 hours. Quiet: no.** The same change that bought
those hours makes the method speak on **1.75× as many winter days** (18.0 % against 10.3 %; an
earlier draft rounded this to "roughly 1.8×") over the six gauges'
own 162,413-day records. Both halves are measured; neither is an estimate.

| | old (`@0.1.0` + `rate-of-rise@1.0.0`) | new (`@0.2.0` + `rate-of-rise@2.0.0`) |
|---|---|---|
| earliest escalation, cedar | 12-09 12:00Z | 12-08 12:00Z (**−24 h**) |
| green-duwamish | 12-09 12:00Z | 12-07 12:00Z (**−48 h**) |
| nooksack | 12-10 12:00Z | 12-07 12:00Z (**−72 h**) |
| puyallup-white | 12-08 12:00Z | 12-06 12:00Z (**−48 h**) |
| **skagit** | 12-07 12:00Z | 12-07 12:00Z (**0 h**) |
| snohomish-snoqualmie | 12-09 12:00Z | 12-06 12:00Z (**−72 h**) |
| quiet-window firings (10 pre-event days × 6 basins = 60) | **0** | **6** |
| winter days the method speaks on, 162,413-day base rate | 10.3 % | 18.0 % |

Five findings underneath that. The second and third are the ones a reader is most likely to get
wrong; the fifth is the one that should change what happens next:

1. **FACT — the lead time comes entirely from the velocity, and none of it from the level.**
   Under any rule that reads only the banded percentile the two arms are **identical on every
   basin, to the hour** (§4). That is by design — the Tier 0 change recalibrated nothing — but it
   means the phrase "the corrected surface turns red earlier" is false and must not be used.
2. **FACT — the tail representation bought no lead time at all, and was never going to.** It buys
   *discrimination while the level is censored*: on 31 clamped basin-days the percentile is
   pinned at p95 across flow ratios up to **×5.64**, and the percentile-space 24 h derivative
   reads exactly **+0.0 on 25 of those 31 days**, while the multiplicative growth still moves on
   24 of those 25 (§5). Its value is in the four days that contain the crest, not in the two days
   before it.
3. **FACT — on the Skagit, the basin of the event, the corrected method bought nothing.** Both
   arms escalate at 2025-12-07 12:00Z. The Sauk's daily mean tripled in 24 h and crossed p90 on
   the same day, so the level and the velocity fired together. INFERENCE: a fast-responding
   unregulated headwater is the case where a velocity adds least, which is the opposite of what
   an argument built only on the Skagit would suggest.
4. **FACT — the robust trend estimator changed 31 of 396 paired 6 h directions, and the net
   movement is towards STEADY** (§6). It produced one *later* escalation than the endpoint
   difference, on the Skagit, and that single case is a threshold-crossing artefact worth 2 % of
   the rate, not a systematic lag.
5. **FACT — on five of the six first escalations the growth rank was absent** (§7c), because it
   was read only at or above p90 and the velocity fires below p90. The number that answers "is
   ×1.37 fast?" without needing a cutoff was missing from exactly the hours the change exists to
   cover. **CLOSED 2026-08-27** by splitting the growth reference into its own row read at every
   percentile: first escalations carrying a rank went **1 of 6 → 6 of 6**, all rising-24 h
   evaluations **68 of 106 → 100 of 100**, and the lead times did not move — which is the check,
   not a coincidence. See §7c. The rest of this document is the run BEFORE that fix; §7c carries
   the re-run.

**Should it ship?** On this evidence, yes — but the brief is right that completeness is not a
reason, and the honest form of the recommendation is: *ship the exact rank, the seasonal
multiple, the boundary condition and the state change as separately-provenanced statements,
because they are exact and they restore discrimination the ladder had lost; do not draw a band or
a cutoff on any of them until brief §18's multi-event POD/FAR curve exists, because §7 shows the
cost of speaking is real and one flood cannot price it.* The implementation already refuses to
draw one. Keep it that way.

---

## 2. The two knowledge times, and the result of the strict one (brief §20) — FACT

The December 2025 rows in this platform were backfilled in 2026. `available_at` is therefore 2026
on all of them, and `DATA_DOCTRINE §11` / `ADR-0010` say a replay at T may read only rows with
`available_at <= T`.

The strict replay was run. **792 of 792 evaluations returned `surface_state = unknown`**, each
with the machine-readable reason naming the missing input
(`No day-of-year climatology stored for station:usgs:…`), and every trend, observed category and
official forecast came back UNKNOWN too. There were zero escalations under every rule, in both
arms.

> **RE-RUN AND VERIFIED 2026-08-27, after adversarial review found the recipe wrong.** The
> figure is correct — 792 evaluations, **0 with a computed surface** — but it was NOT reproducible
> from §12 as originally published, and nothing pinned it. The mechanism: `reference` and
> `reconstruct` both write `available_at = valid_time` (`scripts/hindcast_event_zero.py` :395,
> :631) and both ran **before** the strict run, leaving the ladder and every ranked daily mean
> visible in December 2025 — a state in which `susceptibility.assess` does **not** return UNKNOWN.
> The guard could not see it either: `projection_state` ANDs across three row families and
> observations are never projected, so `projected` was False and the KNOWLEDGE_TIME label was
> permitted.
>
> Re-run with **`unproject` first** (§12 now says so), the claim holds exactly:
> `pre_event_reference_visible_at_valid_time: 0/12`, 792/792 UNKNOWN, six distinct reasons each
> naming the gauge whose climatology is missing, and no escalation under any rule in either arm.
> It is now pinned by `tests/fixtures/hindcast/event_zero_knowledge_time.json` and
> `tests/unit/test_hindcast.py::test_the_strict_knowledge_time_replay_computed_nothing`, so the
> recipe cannot rot again without a test failing.

That is the doctrine working, not a bug, and it is the reason the harness distinguishes two modes
in its type system rather than in a footnote:

| mode | question | Event Zero answer |
|---|---|---|
| `KNOWLEDGE_TIME` | what did **this deployed system** know at T? | nothing, at every T |
| `RETROSPECTIVE` | what was **reconstructable at T from evidence that existed at T**? | §3 onward |

`scripts/hindcast_event_zero.py run` **refuses to label a run** with a mode the database it read
was not in — it measures the projection state and exits rather than produce a document whose
label its own contents contradict.

### What the retrospective projection actually does, per row family — FACT

Every rule is recorded in the run document and in `Projection.disclosure()`. Values, valid times
and issue times are **never** modified; only visibility clocks move.

| row family | rule | how optimistic |
|---|---|---|
| `observation` (USGS instantaneous) | `available_at := valid_time` | by the USGS publication latency, order 5–15 minutes |
| `derived_feature` reconstructed ranking | `available_at := valid_time` (station-local midnight ending the day) | by the daily-value publication lag (hours), **and** by approval status — see below |
| `derived_feature` climatology + record context | **not projected**; a pre-event reference is rebuilt instead (§9) | none on the clock |
| `threshold` (NWPS categories) | `effective_from := 2025-01-01` | **anachronism** — NWPS publishes no historical threshold vintage, so whether these were the categories in force is unverified. `EVENT_ZERO.md` §3 already makes this assumption; this run inherits it rather than inventing a second one |
| `forecast_run` (KSEW FLW/FLS crest statements) | `available_at := issued_at` | essentially none: `issued_at` is the AFOS transmission time of the actual product |

**OPEN QUESTION, and the largest single caveat in this document.** The December daily means used
here were fetched in 2026 and four of the six gauges now carry them as **Approved**. In December
2025 every one of them was **Provisional** and some would have carried different numbers. A
replay on approved values is reading a cleaner record than the one that existed. This cannot be
closed without a 2025 vintage of the daily record, which no archive available here holds.

### Approval status of the December 2025 daily record, measured 2026-08-26 — FACT

Directly relevant to register X8 claim D, and it is **not uniform**:

| gauge | basin | Dec-2025 days approved | last approved day in record |
|---|---|---|---|
| 12189500 Sauk | skagit | 31 / 31 | 2026-04-06 |
| 12113000 Green nr Auburn | green-duwamish | 31 / 31 | 2026-01-07 |
| 12213100 Nooksack at Ferndale | nooksack | 31 / 31 | 2026-01-12 |
| 12100490 White at R St | puyallup-white | 31 / 31 | 2026-02-08 |
| 12119000 Cedar at Renton | cedar | **4 / 31** | 2025-12-04 |
| 12149000 Snoqualmie nr Carnation | snohomish-snoqualmie | **0 / 31** | **2024-11-14** |

X8's claim D ("five of six gauges carry approved WY2026 data inside the ranking window") is
therefore **four of six for the whole month**, one partial and one gauge whose approved record
stops more than a year before the event. The Snoqualmie's shipped ladder ends **2024**.

---

## 3. The A/B, basin by basin — FACT

Retrospective mode, pre-event reference (§9), new arm. `p` is the shipped day-of-year percentile;
`Δ24` is the percentile-space 24 h change (a **diagnostic** — `@0.1.0` published no velocity at
all); `×24` is `Q(t)/Q(t−24 h)`; `rank` is the exact rank in the ±2-day window sample, whose denominator is `n + 1` because it
includes the value being ranked (§9 gives the `n`); `mult` is `Q ÷ p95(DOY)`; `cat` is the observed NWS category; `fc` is the official crest category known at
that instant.

**Each row is labelled by the daily-mean DAY and evaluated at 12:00Z of the following day**,
which is the first instant that daily mean was visible — a station-local daily mean is complete
at local midnight, 08:00Z in PST. `cat` and `fc` are therefore properties of that evaluation
instant, not of the day in the first column.

### Skagit (Sauk nr Sauk, 12189500 — unregulated, the basin of the event)

| day | Q cfs | p | band | Δ24 | ×24 | dir | rank | mult | cat | fc |
|---|---|---|---|---|---|---|---|---|---|---|
| 12-04 | 2,420 | 22.9 | low | +0.3 | 1.00 | steady | — | 0.18 | none | — |
| 12-05 | 2,740 | 30.8 | moderate | +7.9 | 1.13 | steady | — | 0.24 | none | — |
| **12-06** | 8,220 | 90.2 | **very_high** | **+59.4** | **3.00** | **rising** | 49/491 | 0.81 | none | — |
| 12-07 | 7,170 | 85.3 | high | −4.8 | 0.87 | steady | — | 0.76 | none | — |
| 12-08 | 11,100 | 95.0 | very_high ⛔ | +9.7 | 1.55 | rising | 17/491 | 1.08 | action | — |
| 12-09 | 24,900 | 95.0 | very_high ⛔ | **+0.0** | 2.24 | rising | 3/491 | 2.36 | action | major |
| 12-10 | 41,500 | 95.0 | very_high ⛔ | **+0.0** | 1.67 | rising | **1/491 ★** | 3.81 | moderate | major |
| 12-11 | 62,600 | 95.0 | very_high ⛔ | **+0.0** | 1.51 | rising | **1/491 ★** | **4.99** | major | major |
| 12-12 | 21,100 | 95.0 | very_high ⛔ | **+0.0** | 0.34 | falling | 8/491 | 1.55 | moderate | unknown |

⛔ = `outside_climatology_range`; ★ = larger than every daily mean in the ±2-day window sample.
`unknown` in the last column means an official product WAS known at that instant but its crest
lies before the knowledge time, so no forward category can be taken from it — which is the
`surfaces.forecast_crest` refusal, not a missing product.

Read the last four rows twice: **the level says the identical
thing at 11,100 cfs and at 62,600 cfs**, and the percentile derivative says the identical thing
too (`+0.0`), while `mult` runs 1.08 → 4.99, the rank runs 17th → 1st-and-beyond-the-record, and
the growth stays live at ×2.24, ×1.67, ×1.51.

### Snohomish–Snoqualmie (Snoqualmie nr Carnation, 12149000)

| day | Q cfs | p | band | Δ24 | ×24 | dir | rank | mult | cat | fc |
|---|---|---|---|---|---|---|---|---|---|---|
| 12-04 | 2,120 | 14.6 | low | −1.3 | 0.97 | steady | — | 0.13 | none | — |
| **12-05** | 2,910 | 29.3 | moderate | +14.7 | **1.37** | **rising** | — | 0.20 | none | — |
| 12-06 | 6,110 | 72.4 | moderate | +43.1 | 2.10 | rising | — | 0.43 | none | — |
| 12-07 | 6,700 | 76.8 | high | +4.4 | 1.10 | steady | — | 0.49 | none | — |
| 12-08 | 9,360 | 90.0 | very_high | +13.2 | 1.40 | rising | 49/476 | 0.69 | action | major |
| 12-09 | 31,100 | 95.0 | very_high ⛔ | +5.0 | 3.32 | rising | 4/476 | 2.25 | moderate | major |
| 12-10 | 39,300 | 95.0 | very_high ⛔ | **+0.0** | 1.26 | steady | 2/476 | 2.60 | major | major |
| 12-11 | 80,400 | 95.0 | very_high ⛔ | **+0.0** | 2.05 | rising | **1/476 ★** | 4.89 | major | unknown |
| 12-12 | 31,000 | 95.0 | very_high ⛔ | **+0.0** | 0.39 | falling | 5/476 | 1.84 | minor | unknown |

On **12-05**, three days before the band moves and just under three days before the first
official crest statement, the surface reads p29.3 — below the 30th percentile of this gauge's own
day-of-year record — and the 24 h state change reads **×1.37, rising**. That single row is this
whole change in miniature.

### The other four, first-escalation summary

| basin | first VERY_HIGH (both arms) | first RISING 24 h (new only) | earliest escalation, old → new |
|---|---|---|---|
| cedar | 12-08 | 12-07 | 12-09 12:00Z → 12-08 12:00Z |
| green-duwamish | 12-08 | 12-06 | 12-09 12:00Z → 12-07 12:00Z |
| nooksack | 12-09 | 12-06 | 12-10 12:00Z → 12-07 12:00Z |
| puyallup-white | 12-07 | 12-05 | 12-08 12:00Z → 12-06 12:00Z |
| skagit | 12-06 | 12-06 | 12-07 12:00Z → 12-07 12:00Z |
| snohomish-snoqualmie | 12-08 | 12-05 | 12-09 12:00Z → 12-06 12:00Z |

(Left columns are the daily-mean *day*; right column is the *knowledge time*, which is the first
evaluation instant that could see that day — station-local midnight is 08:00Z in PST, so the
first grid point that sees a new daily mean is 12:00Z. Evaluating at 00, 06, 12 and 18Z showed
that **the level changes only at 12:00Z**; the finer grid earns its place on the trend, not on
the level.)

### An independent, outcome-free anchor: when NWS first said it — FACT

The first KSEW FLW/FLS crest statement per forecast point, by its own AFOS transmission time:

| basin | first official crest statement | category | new arm's first escalation | difference |
|---|---|---|---|---|
| snohomish-snoqualmie | 12-09 11:14Z | major | 12-06 12:00Z | 2.97 d |
| green-duwamish | 12-09 11:16Z | minor | 12-07 12:00Z | 1.97 d |
| skagit | 12-09 17:01Z | major | 12-07 12:00Z | 2.21 d |
| puyallup-white | 12-09 20:07Z | major | 12-06 12:00Z | 3.34 d |
| cedar | 12-10 16:10Z | major | 12-08 12:00Z | 2.17 d |
| nooksack | 12-10 17:42Z | moderate | 12-07 12:00Z | 3.24 d |

**This is not a skill comparison and must never be quoted as one.** The susceptibility surface is
an antecedent-wetness statement about one gauge; an FLS is a crest forecast with a category. NWS
had been issuing Flood Watches before its first crest statement, and product cadence is not the
same thing as when a forecaster first knew. The table is here only because it is an *independent*
clock — nobody chose it after seeing the result — against which both arms can be placed.

---

## 4. The level did not move, on any basin, by any amount — FACT

Under `band_very_high` (percentile ≥ p90) and `band_high` (≥ p75), the comparison is
`no_difference` with `difference_h = 0.0` on **all six basins**, and the control-window firing
count is 0 for both arms. `tests/unit/test_hindcast.py::test_the_new_arm_never_moved_the_band`
asserts that the two arms report the identical percentile and the identical band at every one of
the paired evaluations.

That is the intended behaviour — `BAND_EDGES` is still `(25, 75, 90)`, `calibrated` is still
`False`, and brief §8 forbids recalibrating in this change — but it disposes of one framing
completely. **Whatever this change bought, it did not buy an earlier red.**

---

## 5. What the tail representation bought: discrimination, not lead time — FACT

Over the 31 clamped basin-days in the event window (new arm, 12:00Z evaluations):

| measurement | value |
|---|---|
| clamped basin-days | 31 |
| of those, percentile Δ24 h reads exactly `+0.0` | **25** |
| of those 25, the multiplicative growth is not 1 | **24** |
| clamped days on which an exact rank was published | **31 / 31** |
| clamped days at or beyond the whole window record | **13** |
| range of the seasonal multiple while clamped | **1.04× … 4.99×** |

Flow ratios spanned by a single indistinguishable `p95`:

| basin | clamped days | flow range (cfs) | ratio, all reported `p95` |
|---|---|---|---|
| skagit | 5 | 11,100 … 62,600 | **×5.64** |
| snohomish-snoqualmie | 5 | 17,500 … 80,400 | ×4.59 |
| cedar | 5 | 3,240 … 10,100 | ×3.12 |
| nooksack | 5 | 15,500 … 34,200 | ×2.21 |
| green-duwamish | 6 | 5,780 … 11,600 | ×2.01 |
| puyallup-white | 5 | 7,400 … 9,220 | ×1.25 |

`tier0-measured-basis-2026-08-26.md` §3 measured 2.9–3.7× against a single first-clamp
breakpoint and was corrected upward to 3.83–5.72× by `tail-representation-2026-08-26.md`. This
replay, ranking the **published station-local daily means** in a **pre-event** ladder, measures
**1.25–5.64×**. All three agree on the defect; they differ on the number because they differ on
which daily mean and which ladder, which is exactly what a hindcast is for.

INFERENCE: the tail statement's operational value is confined to the days on which the level is
censored — the crest and its shoulders. It is worth shipping for that and for nothing else, and
claiming a lead time for it would be false.

---

## 6. The trend: what the robust estimator changed — FACT

396 paired 6 h evaluations at the six outlet forecast points, same window, same basis, same unit,
same STEADY epsilons; only the estimator differs.

| | count |
|---|---|
| directions that agree | 365 / 396 |
| `rising` (endpoint) → `steady` (repeated median) | 14 |
| `steady` → `falling` | 7 |
| `falling` → `steady` | 6 |
| `steady` → `rising` | 4 |
| refusals, either arm | 0 (all six seeded points are measured `FLUVIAL`) |

Net movement is **towards STEADY**, which is what a 50 %-breakdown estimator on a noisy stage
record should do.

Under `trend_rising_6h` the two arms agree on the first RISING instant on five basins and differ
by one grid step on the Skagit (old 12-06 06:00Z, new 12-06 12:00Z). **That single case is a
boundary artefact, not a lag**: at 12-06 06:00Z the endpoint difference reads 0.0500 ft/h and the
repeated median 0.0489 ft/h against a STEADY epsilon of 0.0500 ft/h. The estimators differ by
2.2 % of the rate and the epsilon happens to fall between them. Six hours later both read
`rising` at 0.167 / 0.170 ft/h.

In the quiet control window the robust estimator fired **5 times against the endpoint
difference's 6** — one fewer, at green-duwamish. That is a one-count difference and no conclusion
should be hung on it.

**Coupling worth naming:** `headroom.time_to_threshold_h` is refused whenever the trend is not
rising. At first escalation the two basins whose trend was already rising got a time-to-threshold
(puyallup-white 54.1 h to action, snohomish-snoqualmie 33.4 h), and the other four got the
refusal reason. A change to the trend estimator therefore changes which basins get a
time-to-threshold, which is a second-order effect nobody had listed.

---

## 7. The cost: how often the method now speaks — FACT

This is the half of the governing question that a lead-time table hides, and it is measured two
ways.

### (a) The quiet control window: 10 pre-event days × 6 basins = 60 basin-days

Same gauges, same season, same instruments, immediately before the event.

| rule | old arm | new arm |
|---|---|---|
| `band_very_high` | 0 / 60 | 0 / 60 |
| `band_high` | 0 / 60 | 0 / 60 |
| `rising_24h` | *unanswerable* | **6 / 60** |
| `rising_48h` | *unanswerable* | 1 / 60 |
| `trend_rising_6h` | 6 / 60 | 5 / 60 |
| **earliest escalation of any kind** | **0 / 60** | **6 / 60** |

The six firings, all `rising` 24 h, all on days the band called `moderate`:

| basin | day | Q cfs | percentile | ×24 h |
|---|---|---|---|---|
| nooksack | 11-23 | 4,760 | 58.4 | 1.42 |
| snohomish-snoqualmie | 11-23 | 3,390 | 41.8 | 1.35 |
| snohomish-snoqualmie | 11-24 | 4,850 | 58.8 | 1.43 |
| green-duwamish | 11-26 | 1,060 | 34.1 | 1.42 |
| puyallup-white | 11-26 | 1,180 | 37.2 | 1.37 |
| puyallup-white | 11-28 | 1,760 | 61.5 | 1.52 |

These are **not false alarms** — nothing claimed a flood, and each of these rivers really did rise
by 35–52 % in a day. They are days on which the corrected method has something to say and the
shipped one does not. Whether that is signal or noise is a question about the renderer and the
reader, and this document cannot answer it.

### (b) The base rate over the whole record: 162,413 gauge-days — FACT

`susceptibility.state_change` and `susceptibility.band` applied to every day of all six gauges'
archived records, ranked in the same pre-event ladders.

| rule | all days | winter (Nov–Feb) |
|---|---|---|
| `band_very_high` (≥ p90) | 10.2 % | 10.3 % |
| `rising_24h` | 7.9 % | 11.4 % |
| `rising_48h` | 6.6 % | 10.3 % |
| **either (the A/B's rule)** | **15.4 %** | **18.0 %** |
| **`rising_24h` where the band is *below* p90 — the marginal cost** | **5.2 %** | **7.7 %** |

Per gauge, days per year: `band_very_high` 37.0–38.5; `rising_24h` 22.7–36.5.

Read the last two rows together. The velocity is **not noisier than the level the platform
already ships** — it fires slightly less often overall and comparably in winter. It is
**partly** independent of it, so the union speaks on 18.0 % of winter days against 10.3 %, and on
**7.7 % of winter days the velocity is the only reason the method says anything** — about **9.3
extra days per gauge-year, all of them in November–February** (the annual marginal from the same
table, 5.2 % of all days, is 19.0 days).

> **CORRECTED 2026-08-27, after adversarial review.** Two sentences here were wrong and are fixed
> above. (1) This paragraph read "about 28 extra days per gauge-year": that multiplied a
> **winter-conditional** rate (7.7 % of Nov–Feb) by a **whole year** (365.25), when winter as the
> code defines it is 120.25 days. 28 is also, coincidentally, the days-per-year of the
> *unconditional* `rising_24h` rule (0.079 × 365.25 = 28.9) — the total rate attached to a
> sentence about the increment. The correct figures are 9.3 (winter-conditional) and 19.0
> (annual marginal). (2) "substantially independent" is refuted by this table's own numbers: the
> observed overlap is 3.7 % against 1.17 % expected under independence, a **3.15× positive lift**,
> so the two rules are positively associated, not substantially independent. Both errors ran in
> the **conservative** direction — the change looked noisier than it is — so the recommendation
> does not move. A document whose thesis is honest cost accounting cannot carry a 3× error in
> the cost, which is why the correction is stated here rather than silently applied. The control window's 6/60 = 10.0 % is the same quantity measured at
a sample size of 60: consistent with the long record rather than lucky, but at n = 60 not itself
evidence of a rate.

**This is a base rate, not a false-alarm ratio.** No day here is labelled flood or not-flood, and
computing a FAR would require an event catalogue this project does not have. Brief §18 is exactly
that work.

### (c) The thing that would have answered "is that fast?" is absent where it is needed — FACT

`growth_rank` — the honest, cutoff-free answer to how unusual a change is — lives in the same
stored record context as the window tail, and `susceptibility._state_changes` reads that context
only at or above p90. The implementer flagged this as a known limitation. This replay measures
it, and the measurement is worse than the description:

| basin | first escalation, day | percentile then | ×24 h | growth rank |
|---|---|---|---|---|
| snohomish-snoqualmie | 12-05 | p29.3 | ×1.37 | **absent** |
| puyallup-white | 12-05 | p58.2 | ×1.62 | **absent** |
| green-duwamish | 12-06 | p52.4 | ×1.34 | **absent** |
| nooksack | 12-06 | p89.8 | ×2.97 | **absent** |
| cedar | 12-07 | p62.1 | ×1.93 | **absent** |
| skagit | 12-06 | p90.2 | ×3.00 | 199 of 36,007 |

> ## CLOSED 2026-08-27 — re-run after the growth reference was split out
>
> The gate was not a coincidence, it was an **identity**: `RANK_READ_EDGE` (90.0) and
> `BAND_EDGES`' top edge are the same constant applied to the same rounded number, so the rank
> was readable *if and only if* the band already read VERY_HIGH — which made `difference_h`
> identically the length of the unranked window in all six basins. **100 % of the 264 h of lead
> this change bought was delivered by a statement that structurally could not carry a rank.**
>
> The growth reference now lives in its own row (`method:streamflow-growth-reference@1.0.0`) and
> is read at every percentile. Re-running the whole A/B on the corrected surface:
>
> | | before | after |
> |---|---|---|
> | first escalations carrying a growth rank | **1 of 6** | **6 of 6** |
> | all `rising` 24 h evaluations carrying a rank | 68 of 106 | **100 of 100** |
> | lead times | 24/48/72/48/0/72 h | **unchanged** |
>
> The lead times are unchanged **by design and as a check**: the split changed what a statement
> carries, not when it fires, so any movement there would have meant a band, epsilon, window or
> score had also moved. The re-run's first escalations:
>
> | basin | first escalation | percentile then | ×24 h | growth rank |
> |---|---|---|---|---|
> | snohomish-snoqualmie | 12-06 | **p29.3** | ×1.37 | **2,651 of 34,957** |
> | puyallup-white | 12-06 | p58.2 | ×1.63 | **138 of 5,875** |
> | green-duwamish | 12-07 | p52.4 | ×1.34 | **1,595 of 32,598** |
> | nooksack | 12-07 | p89.8 | ×2.97 | **151 of 21,569** |
> | skagit | 12-07 | p90.2 | ×3.00 | 199 of 36,007 |
> | cedar | 12-08 | p62.1 | ×1.93 | **199 of 29,280** |
>
> Snohomish–Snoqualmie is the case that makes the point: at **p29.3**, nowhere near the old gate,
> a ×1.37 daily rise is the 2,651st largest day-over-day change in 34,957 days of record — the
> top 7.6 %. That is the answer to "is that fast?", and before the split the surface could not
> give it at any percentile below 90.
>
> Measured cost of the split: the growth block is 247 KiB of the 952 KiB record context, so
> reading it alone is **74 % cheaper than widening the gate**, and total storage is unchanged
> because `growth` was removed from the context rather than copied out of it.

**Five of the six first escalations carry no rank at all**, because on the day the velocity fires
the level is still below p90 — which is the entire point of having a velocity. Across the whole
run, 106 evaluations read `rising` on the 24 h window and only **68** carry a rank; the 38 that do
not are concentrated exactly in the pre-p90 window where the lead time is earned. Nooksack at
×2.97 on p89.8 misses by two tenths of a percentile point.

The absence is disclosed with its own distinct reason (`NO_GROWTH_REFERENCE_READ_REASON` — "we did
not read it because this river is quiet" — kept separate from "nobody built the context"), so
nothing is hidden. But a reader shown "×1.37, rising" with no rank has been handed the number and
denied the only context that makes it interpretable without a cutoff. **INFERENCE: this is the
highest-value follow-up in the whole change** — splitting the growth reference into its own small
feature that can be read unconditionally, which the implementer costed at a few KiB per gauge.

---

## 8. How "meaningful escalation" was fixed, and whether the comparison is legitimate

The brief is explicit: do not call a difference a lead time unless the definition was fixed
independently of the outcome. Here is exactly how it was fixed, before any result was looked at,
and it is enforced in code rather than by convention — `EscalationRule` carries
`fixed_independently_of_outcome` and `constant_provenance` with **no defaults**, and
`compare_arms` refuses the verdict `lead_time` where the first is `False`.

| rule | constant | where it came from | independent? |
|---|---|---|---|
| `band_very_high` | percentile ≥ 90 | `susceptibility.BAND_EDGES`, the USGS WaterWatch much-above-normal convention. In the surface before this change; explicitly not recalibrated by it; identical in both arms | **yes** |
| `band_high` | percentile ≥ 75 | same tuple, second edge | **yes** |
| `rising_24h` / `rising_48h` | direction ≠ steady | `trend.FLOW_STEADY_FRACTION_PER_H = 0.01`, compounded over the actual span. This is the STEADY band the *deployed* rate of rise already decided direction against; `trend.py` states it is unchanged between v1 and v2 precisely so an A/B cannot be fitted to Event Zero | **yes** |
| `trend_rising_6h` | `trend.steady_epsilon` (0.05 ft/h, 1 %/h) | unchanged between `@1.0.0` and `@2.0.0` | **yes** |
| `any_escalation` | disjunction of the first and third | both of the above | **yes** |
| `growth_rank_top_5 %` / `top_1 %` | a chosen fraction | **chosen here and validated nowhere** | **no** |

**Is the headline comparison legitimate?** Two objections and their honest answers.

1. *"You compared different rules."* No — `any_escalation` is one rule ("the method first
   publishes any escalation it has the vocabulary for") applied to both arms. Under `@0.1.0` its
   second disjunct is unanswerable and it reduces to the band. That is not a handicap the harness
   imposed; **having no velocity statement at all is the defect under test.** The harness
   distinguishes "unanswerable" from "did not fire" and reports `rising_24h` alone as
   `earlier_but_not_a_lead_time` for exactly this reason.
2. *"1 %/h is still a threshold, and you picked it."* It is a threshold, and **it was not picked
   here**: it is `FLOW_STEADY_FRACTION_PER_H`, which predates this change, decides direction for
   the estimator that was already deployed, and was deliberately left untouched. But it was never
   validated against flood response either, so the *magnitude* of the lead time is a function of
   an uncalibrated constant. What is robust is the **sign and the ordering**; what is not is
   "72 hours". A different epsilon moves every number in §1 and §3.

**The rank-fraction rules are reported and refused.** At top-5 % the new arm escalates on 12-07
(skagit) through 12-10; at top-1 % it fires on three basins and never on the other three. Both are
`earlier_but_not_a_lead_time` by construction. `high-tail-selection-2026-08-27.md` §9 is right
that a band on the growth needs brief §18, and this replay does not supply it.

---

## 9. The reference distribution, and what its vintage is worth — FACT

Two problems had one answer. A reference row's `valid_time` is the last day of the record it was
built from, so the shipped 2026-08-26 ladders are stamped 2026-08-26 and `Knowledge` correctly
refuses to hand a December-2025 replay a reference from its own future. And those same records
run *through* the event (register X8 claim D). Both are removed by re-running the **shipped
builders** — `build_doy_climatology` and `build_record_context`, unmodified — over the same
archived record truncated at **2025-10-31**. That produces exactly the row
`usgs.build_climatology` would have written on 2025-11-01: same method id, same code, fewer rows,
and no WY2026 day inside it. The run's `reference.contains_event` is therefore `False` and its
`truncated_at` is `2025-10-31`, **derived from the cutoff rather than asserted**.

The reference each basin is ranked in, at the 12-11 key:

| gauge | basin | n (±2 d window) | independent years | period | ceiling |
|---|---|---|---|---|---|
| 12189500 | skagit | 490 | 98 | 1911–2025 | moderate |
| 12149000 | snohomish-snoqualmie | 475 | 95 | 1929–**2024** | high |
| 12113000 | green-duwamish | 445 | 89 | 1936–2025 | low |
| 12119000 | cedar | 400 | 80 | 1945–2025 | moderate |
| 12213100 | nooksack | 295 | 59 | 1966–2025 | moderate |
| 12100490 | puyallup-white | **80** | **16** | 2009–2025 | low |

### What the ladder vintage is worth, measured (X8) — FACT

Same daily means, same `percentile_of`, same `band`; only the ladder differs (pre-event rebuild
vs the shipped 2026-08-26 build).

| gauge | largest percentile shift in the event window | first day at or above p90 moves? |
|---|---|---|
| **12100490 puyallup-white** | **−7.54 points** (12-08: 91.43 → 83.89) | **yes: 12-07 → 12-09, two days later** |
| 12113000 green-duwamish | −1.34 | no |
| 12213100 nooksack | −1.33 | no |
| 12189500 skagit | −0.54 | no |
| 12119000 cedar | +0.42 | no |
| 12149000 snohomish-snoqualmie | 0.00 | no (its approved record ends 2024-11-14) |

**INFERENCE, and it is a live operational finding.** At the thinnest-record gauge, letting the
event into its own reference distribution **delays the old method's escalation by two days** —
the same order as the entire Tier 0 correction. At the five long-record gauges the vintage is
worth ≤ 1.34 points and moves nothing. X8 is therefore not a uniform problem: it is a
**thin-record** problem, and White at R St (16 independent years) is where it bites. This does not
resolve X8 and is not permitted to; it prices it.

Consistent with `high-tail-selection-2026-08-27.md`, which found a leave-one-water-year-out
jackknife moving p99 by up to 19.2 %, and with the concern already recorded that
puyallup-white's ladder may be unsound above p90 independently of anything in this change.

---

## 10. Every field brief §13 asks for, and where it is

The run document carries all of these per basin, per knowledge time, per arm. Two are UNKNOWN
throughout and the reason is structural, not a defect in this run.

| field | source | status in this replay |
|---|---|---|
| basin, gauge | seed | present, 6 basins |
| flow | reconstructed daily mean | present |
| old percentile / state | `susceptibility.assess(version="0.1.0")` | present |
| new tail representation | `HydrologicState.rank` / `.multiple` | present; rank on 31/31 clamped days |
| old and new categorical state | `assemble.assess_point` → `observed_category` | present (none/action/minor/moderate/major) |
| new boundary state | `HydrologicState.boundary` | present (`separated` / `near_band_edge`) |
| old endpoint slope | `trend.rate_of_rise` (`@1.0.0`, preserved) | present, 396 evaluations |
| new robust trend | `trend.estimate_trend` (`@2.0.0`) | present, with n, span, IQR, quality |
| Δ24 / Δ48 | percentile diagnostic **and** multiplicative growth | both present, both windows |
| threshold proximity | `headroom` | present; `time_to_threshold_h` refused where the trend is not rising |
| data quality | `quality_flags` | `approved` 592, `provisional` 200, `outside_climatology_range` 228, `climatology_disagreement` 66 |
| reference-period definition | `ReferenceWindow` | present per gauge (§9) |
| **forcing** | `forcing.assess` | **UNKNOWN at all 792** — no NBM QPF exists for December 2025 in any archive this platform can reach |
| **model agreement** | `agreement.assess` | **UNKNOWN at all 792** — no NWM medium-range run survives for December 2025 (`nwm-survival-inventory-2026-08-24.md`) |
| the three clocks | `Clocks` | `as_of`, `valid_at`, `issued_at`, `available_at`, plus the event cursor and the replay process's own `system_now` — five, kept distinct |
| retrospective vs knowledge-time | `Evaluation.mode` + `Projection` | on every row; the run refuses to mislabel itself |
| provenance | `method_ids`, `raw_artifact_ids` | present, e.g. `@0.2.0`, `streamflow-tail-state@0.1.0`, `streamflow-state-change@0.1.0`, `rate-of-rise@2.0.0` with the archived CSV's artifact id |

Confidence across the run: `moderate` 394, `low` 274, `high` 124 — driven by the seeded per-gauge
ceilings and by `climatology_disagreement` dropping one level at cedar, green-duwamish,
puyallup-white and snohomish-snoqualmie.

---

## 11. What this does and does not license

**Licensed:**
- Reporting that the corrected method escalated 24–72 h earlier on five of six basins **in this
  one event**, under a rule whose constants predate the change, and always beside §7's cost.
- Reporting that the ladder vintage is worth two days of escalation at a 16-year-record gauge and
  nothing at the long-record ones.
- Using the harness for the next event: a `HindcastEvent` literal and an outcome table.

**NOT licensed by this document:**
- Any cutoff on the growth or the multiple. §7's base rate is not a POD/FAR curve, and one flood
  is one flood.
- Any weighting of velocity against level, any composite, any probability or return period.
- Recalibrating `BAND_EDGES`. §9 says the reference is worth more than the edges at one gauge;
  that is an argument for settling X8, not for moving an edge.
- Quoting any number here as what Cascadia Papsukkal would have shown. §2.
- Treating "72 hours" as a property of the method. It is a property of the method **and** an
  uncalibrated 1 %/h epsilon **and** this event.

**OPEN QUESTIONS this run raised and did not close:**
1. Provisional-vs-approved: every value here is cleaner than what existed at the time (§2). What
   the replay would say on the provisional record is unmeasured and probably unmeasurable.
2. `basin:snohomish-snoqualmie` ranks against a ladder ending **2024-11-14** in production today.
   That is a live data-freshness gap, not a hindcast artefact.
3. Whether a reader served the state change on 7.7 % more winter days is better informed or
   worse. That is a renderer question and this document cannot answer it.
4. The Skagit result (0 h) versus the other five: is a fast unregulated headwater systematically
   the case where a velocity adds least? One event cannot say.
5. §7(c): the growth rank is unavailable on five of six first escalations. Splitting the growth
   reference out of the record context would fix it; nothing here decides whether the extra
   stored feature is worth its cost.
6. `Knowledge.latest_derived_feature` asks for `valid_time <= as_of`, and a ladder's `valid_time`
   is the last day of the record it was built from. A hindcast of ANY event therefore sees no
   reference distribution unless one is rebuilt as of a day before it (§9). That is correct
   behaviour and a permanent property of every future hindcast, so the rebuild step is part of
   the harness's contract rather than an Event Zero workaround.

---

## 12. Reproduction

```bash
# a scratch database, never production; the projection step is destructive
createdb cascadia_hindcast && CASCADE_ALEMBIC_URL=... bash scripts/migrate.sh
CASCADE_DB_URL=... python -m cascade_worker seed

# one-off network ingest (the same jobs and scripts the platform already ships)
CASCADE_DB_URL=... python -c "…run_build_climatology…"          # ladders + record context
CASCADE_DB_URL=... python scripts/backfill_event_zero_usgs.py --start 2025-11-20T00:00:00Z --end 2025-12-23T00:00:00Z
CASCADE_DB_URL=... python scripts/backfill_event_zero_fls.py --start 2025-12-01T00:00Z --end 2025-12-23T00:00Z

S=scripts/hindcast_event_zero.py
python $S reference   --db-url ...           # rebuild the pre-event reference (cutoff 2025-10-31)
python $S reconstruct --db-url ...           # rank Nov-01..Dec-22 daily means as the job would
# `unproject` FIRST, and this line is load-bearing: `reference` and `reconstruct` both write
# available_at = valid_time, so without it the ladder is already visible in December 2025 and the
# "strict" run computes surfaces instead of refusing. Omitting it silently produces the OPPOSITE
# of §2's result, and `projection_state`'s three-way AND does not catch it.
python $S unproject   --db-url ...           # restore archive clocks; reference visible 0/12
python $S run   --db-url ... --mode knowledge-time --out kt.json   # §2: 792/792 UNKNOWN
python $S project     --db-url ...           # move the visibility clocks
python $S run   --db-url ... --mode retrospective  --out ab.json   # §1, §3-§6
python $S vintage     --db-url ... --out vintage.json              # §9
python $S base-rate   --db-url ... --out base.json                 # §7(b)
python $S fixture --db-url ... --run ab.json --out tests/fixtures/hindcast/event_zero_ab.json
dropdb cascadia_hindcast
```

`tests/unit/test_hindcast.py` pins the result offline: it rehydrates the run document, re-runs
`band`, `seasonal_multiple`, `independent_years`, `rank_standard_error_points`, `band_boundary`
and `state_change` on the fixture's own recorded inputs, and re-derives every escalation verdict.
No database, no network, no clock. If a method module changes what it publishes, that test names
the basin and the day.

---

## 13. Notes on the harness itself (brief §21)

`packages/hydrology/src/cascade_hydrology/hindcast.py` is a structure over seven things — event,
evaluation time, method version, reference distribution, knowledge cutoff, derived signals,
observed outcome — and deliberately nothing more. Adding an event is a literal; adding a
comparison is a `MethodArm`; adding a criterion is an `EscalationRule`.

Four properties are load-bearing, and each is enforced by something other than good intentions:

- it **calls** the shipped code (`susceptibility.assess(version=…)`, `assemble.assess_point`,
  `agreement.assess`, `forcing.assess`, `trend.rate_of_rise` / `estimate_trend`) rather than
  reimplementing any of it, so the two arms cannot drift from the versions they claim to be —
  and `tests/unit/test_hindcast.py` re-runs those same functions on the fixture's own inputs and
  fails on the basin and day where any of them changes its answer;
- it stores **compact evaluations** — what the surfaces said, never a copy of the rows they read.
  A 62 KiB record-context blob and a 36,000-row daily record stay in the database; the whole
  six-basin run is 2.7 MB of JSON and the checked-in fixture slice is 567 KB;
- it is **provider-agnostic**, enforced by the import-linter contract *cascade_hydrology is
  provider-agnostic: a method never imports an adapter* — which is why the USGS-specific
  reconstruction lives in the script and not in the package;
- it computes **no score**. No composite, no weighting between level and velocity, no
  probability — the prohibitions hold in the evaluation harness exactly as they hold in the
  surface. This one is enforced by review and by the absence of any arithmetic that could
  produce such a number; there is no test that can prove a negative.

The observed outcome is attached to the run and read by nothing that computes a signal. That is
what makes it safe to keep the outcome table in the same file as the escalation rules.
