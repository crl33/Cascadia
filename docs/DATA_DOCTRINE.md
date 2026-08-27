# DATA DOCTRINE — provenance, uncertainty, missing data, and claims

These rules bind every value the platform stores, computes or displays. They are enforced by
types in `packages/contracts`, by database constraints, and by tests — not by convention.

## 1. Every value carries its provenance

A value is never a bare number. The minimum record (see `DOMAIN_MODEL.md` for the schema):

| Field | Meaning |
|---|---|
| `source_id` | which `DataSource` produced it (e.g. `usgs-nwis-iv`, `nwps-v1`, `nwm-v3-medium-range-m01`) |
| `source_kind` | OBSERVED · OFFICIAL_FORECAST · MODELED · DERIVED · EXPERIMENTAL · CONFIGURED · UNKNOWN |
| `variable` | canonical variable id (`stage`, `discharge`, `swe`, `qpf_24h`, …) from the variable registry |
| `value`, `unit` | the number and its unit (§6) |
| `valid_time` | when the value is true (observation instant, or forecast valid time) |
| `issued_at` | forecast/model run issuance (null for observations) |
| `retrieved_at` | when Cascadia Papsukkal fetched it |
| `available_at` | knowledge time: the earliest instant the platform *could* have had it = `max(issued_at or valid_time, retrieved_at)` for hindcasts — see §11 |
| `quality` | flags (provisional/approved/estimated/ice/equipment/suspect/sentinel/out-of-range) |
| `raw_artifact_id` | pointer to the archived raw payload the value was parsed from |
| `lineage` | for DERIVED: the feature definition version and the input value ids |

Display consequence: every rendered number can answer *where from, what kind, when valid,
when produced, when fetched, how stale, what transformed it, from which inputs*.

## 2. Source kinds are a closed, ordered taxonomy

| Kind | Definition | May be labeled "official"? |
|---|---|---|
| OBSERVED | a measurement by an instrument or sensor network (USGS, SNOTEL, MRMS radar QPE is "observed-derived" and is tagged OBSERVED with `method=radar_qpe`) | no — labeled *observed* |
| OFFICIAL_FORECAST | a forecast issued by an authority with public responsibility (NWS/NWRFC river forecasts, NWS QPF, NWS alerts) | **yes** |
| MODELED | output of an authoritative model not designated as the official forecast (NWM, SNODAS, SMAP L4, NBM, HRRR, GFS) | no — labeled with the model name |
| DERIVED | computed by Cascadia Papsukkal from the above with a published, versioned method | no |
| EXPERIMENTAL | DERIVED outputs whose method has not passed hindcast evaluation | no — always badged EXPERIMENTAL |
| CONFIGURED | hand-entered operational metadata (thresholds, mappings) | never; never used in hazard computation |
| UNKNOWN | absent, failed, or unclassifiable | n/a |

Never silently substitute one kind for another. A fallback changes `source_kind` and is
visible in the API response.

## 3. Time is three-valued

`valid_time`, `issued_at`, and `retrieved_at` are distinct and never collapsed. For
forecasts the UI shows "valid 12:00 PST, issued 06:30 PST by NWRFC, fetched 06:41".
Observations carry the provider's timestamp with its offset converted to UTC, plus the
provider's local time zone as metadata. Daily values (SNOTEL, USGS daily means) are stored with
the provider's day boundary, not midnight UTC (V1 got this wrong). The zone metadata is what
computes that boundary, so it is stored as a canonical IANA name and the seed refuses any key the
running image cannot resolve — a key that will not resolve silently returns the whole platform to
the UTC boundary V1 assumed ([ADR-0017](adr/ADR-0017-canonical-iana-time-zones-in-the-seed.md)).

## 4. Missing data is a value, not an absence

- A product that should exist and does not yields a row with `quality=missing` and a reason,
  so gaps are visible in history and in freshness metrics.
- Provider sentinels (`−999999`, `−9999`, `−9000`, empty strings) are parsed into
  `quality=sentinel` using the provider's declared `noDataValue`, never a hard-coded
  comparison.
- "No mapping configured" (e.g. a basin without a SNOTEL station) is a configuration state
  surfaced in metadata, distinct from "station failed".

## 5. Staleness is derived from cadence, per product

Each `SourceProduct` declares `expected_cadence` and `grace`. `stale = now − valid_time >
expected_cadence + grace`; `degraded = now − retrieved_at > expected_cadence × k` (ingestion
falling behind). Both are computed at read time from stored timestamps; nothing stores a
"stale" boolean. Defaults (overridable per product, recorded in `DATA_SOURCES.md`):

| Product class | Cadence | Grace |
|---|---|---|
| USGS IV stage/flow | 15 min (some 60 min) | 75 min |
| NWPS forecast | ~6–12 h during events, daily otherwise | 18 h |
| SNOTEL hourly / daily | 1 h / 1 d | 3 h / 36 h |
| SNODAS | daily | 30 h |
| MRMS QPE | 1 h accumulations | 2 h |
| HRRR / NBM / GFS | hourly / hourly / 6-hourly cycles | one cycle |
| Reservoir operator data | varies (15 min – daily) | 2× cadence |

Stale values are displayed with their age and a STALE mark; they are never hidden and never
shown as current.

The clock matters at the point of display. `age = read clock − valid_time`, so a deliberately
archived value (a backfilled December 2025 observation, a forecast run reconstructed from stored
text) computes as `stale` with an age of months — true of *today*, and meaningless as a fault. The
presentation rule is VISUAL_TRUTH_DOCTRINE §5.6: such values are marked ARCHIVED and their age is
stated as "N before today", never as staleness and never as an age at a replayed instant.

## 6. Units

- Storage: values are stored in the **provider's native unit** with `unit` recorded
  (preserves fidelity and auditability), and every variable has a **canonical unit** in the
  registry (SI for science: m, m³ s⁻¹, mm, kg m⁻², K). Conversion uses `pint` with
  registry-pinned definitions; converted values are DERIVED with lineage to the source value.
- Display: stage in ft and discharge in cfs (or kcfs) where NWS defines thresholds in those
  units, because official thresholds must be shown in their own units; SWE in inches beside
  mm; precipitation in inches beside mm. The UI shows the unit every time.
- Never mix kcfs and cfs without conversion (NWPS uses kcfs for flow-defined points).

## 7. Validation and thresholds

- Official thresholds come from NWPS per forecast point, in the unit NWS defines them
  (stage or flow), with datum and `retrieved_at`. They are re-fetched on a schedule and
  versioned; a change creates a new threshold row, never an update.
- CONFIGURED thresholds exist only for display with a "configured" badge and are excluded
  from any category or hazard computation by type (the hazard function does not accept them).
- Range validation per variable (e.g. stage ≥ datum-plausible, flow ≥ 0, SWE ≥ 0) sets
  `quality=out_of_range` rather than dropping the value.
- Schema drift: parsers are strict about the fields they use and tolerant of extras; a
  missing required field fails the parse, archives the payload, and raises an alert.

## 8. Revisions and supersession

- Observations: USGS revises provisional data to approved; later fetches of the same
  `(source, site, variable, valid_time)` that differ create a **revision** row linked to the
  prior one. The "current best" is a view; history retains both. Hindcasts read the revision
  that existed at knowledge time.
- Forecasts: a new run supersedes an older run for the same valid times; both are stored.
  "Forecast evolution" is a query over runs.
- Derived features: recomputation under a new method version creates new rows tagged with
  `method_version`; old rows are kept for comparison.

## 9. Uncertainty and confidence

- Distributions are stored as distributions: ensemble members as members, percentiles as
  percentiles, with the member/percentile id. Averages are computed at read time and labeled.
- "Confidence" is reserved for calibrated quantities. Mapping quality, data completeness and
  model agreement are **labeled categories**, not decimals (V1 invented 0.85/0.65/0.45).
- Probabilities are displayed only when they are (a) issued by an authority, (b) empirical
  fractions of a named ensemble ("11 of 21 GEFS-driven members exceed minor"), or (c) a
  Cascade method that has passed hindcast evaluation with its reliability diagram published.
  Otherwise the output is an *index* or *indicator* and says so.

## 10. Model disagreement is information

When two or more authoritative sources forecast the same quantity, the platform stores each,
computes agreement metrics (crest magnitude, timing, category), and exposes them as a
first-class `Assessment` of kind `model_agreement`. Disagreement is explained, never averaged
into a single line.

## 11. Knowledge time and look-ahead bias

For any replay at clock time T, a query may only return rows with `available_at ≤ T` and
must select observation revisions as they existed at T. Products that are republished with
later improvements (reanalyses, approved data, re-gridded QPE) are stored with the publication
time of each version so that a hindcast cannot accidentally use a better version than existed
at T. This is enforced by a single query helper (`as_known_at(T)`) that every replay path
uses; direct table access in replay code is a review failure.

## 12. Claims and safety language

- Cascadia Papsukkal is **not** an official alert authority. Official warnings, watches and
  evacuation instructions are displayed verbatim with issuer and time, badged OFFICIAL, and
  linked to the issuer.
- Cascade-derived intelligence is badged DERIVED or EXPERIMENTAL, with a one-line method
  pointer, everywhere it appears — panels, maps, API responses, exports.
- Copy never uses "will flood", "safe", or "protected". It uses "official forecast crest",
  "exceeds", "remains below", "experimental index", "model disagreement".
- UNKNOWN is rendered as UNKNOWN with its reason. It is never rendered as calm, green, or zero.

## 13. Retention and lifecycle

| Data | Retention | Where |
|---|---|---|
| Raw provider payloads (JSON/CSV) | indefinite, compressed | object storage, content-addressed |
| Raw gridded products (GRIB2/NetCDF/COG) | full for event windows and a rolling window (e.g. 90 d) for all cycles; basin aggregates indefinite | object storage, lifecycle rules |
| Normalized observations, forecasts, thresholds | indefinite | PostgreSQL (partitioned) |
| Derived features and assessments | indefinite with `method_version` | PostgreSQL |
| Visualization derivatives (tiles, simplified geometry) | regenerable; cached | object storage / CDN |

Nothing in PostgreSQL is ever deleted by application code; corrections are rows.

## 14. Enforcement

- Types: `packages/contracts` makes `source_kind`, timestamps and `unit` required on every
  value model; there is no constructor for a bare number.
- Database: NOT NULL + CHECK constraints on kinds, units and timestamps; append-only tables
  for observations and forecasts (no UPDATE/DELETE grants to application roles).
- Tests: property tests that a fallback cannot carry `OFFICIAL_FORECAST`; that
  `as_known_at(T)` excludes later rows; that staleness is computed, not stored.
- Review: a PR that displays a value without a badge, or computes hazard from CONFIGURED
  input, fails review by checklist (`.claude/skills/vibesec/references/cascadia-papsukkal-addendum.md` §7).
