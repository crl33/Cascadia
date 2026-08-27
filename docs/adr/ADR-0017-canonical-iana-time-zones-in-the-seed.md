# ADR-0017 — Seed canonical IANA time zone names, and refuse anything the runtime cannot resolve

- **Status.** Accepted, 2026-08-27.
- **Deciders.** Platform.
- **Supersedes nothing.** It repairs a configuration defect against ADR-0010 (knowledge time) and
  DATA_DOCTRINE §3 (a daily value is stored on the provider's day boundary, never midnight UTC).

## Context

A USGS daily mean is the mean over the station's **local** calendar day, so the value labelled
2026-08-23 is complete at 00:00 local on 2026-08-24 — 07:00Z in PDT, 08:00Z in PST.
`climatology.daily_mean_valid_time` computes that instant from `station.time_zone`, and when the
zone will not resolve it degrades to the UTC boundary and says so with the quality flag
`day_boundary_assumed_utc`. The function does exactly what it promises.

**FACT (verified 2026-08-27).** Stations were seeded `time_zone="PST8PDT"` — a legacy POSIX alias
for Pacific time. The deployment image (`python:3.14-slim`, `infra/Dockerfile`) ships Debian's
`tzdata` **without `tzdata-legacy`**: 486 resolvable keys over 436 distinct zone files — the
POSIX aliases (`PST8PDT`, `EST5EDT`, `MST7MDT`) and most `backward` links are gone. It is not
alias-free: 50 of those keys are aliases in 34 groups (`America/Nipigon`, `Etc/Greenwich`, …).
The ones this platform would reach for are precisely the ones dropped.

```
docker run --rm python:3.14-slim python -c "from zoneinfo import ZoneInfo; ZoneInfo('PST8PDT')"
ZoneInfoNotFoundError: 'No time zone found with key PST8PDT'
```

`America/Los_Angeles` resolves in that image; `PST8PDT`, `US/Pacific` and `EST5EDT` do not. A
developer laptop resolves all of them (598 keys). So does CI — not asserted here but
demonstrated: `test_every_seeded_gauge_has_a_time_zone_so_the_day_boundary_is_never_assumed`
asserts the seeded zone resolves with no flag, and it passed on every green run while
`PST8PDT` was the seeded value.

**FACT.** The consequence in production: every `streamflow_doy_percentile` row written *inside the
container* was stamped at UTC midnight and flagged `day_boundary_assumed_utc`. The correct local
stamp sits 7 h away (8 h in PST), and `susceptibility.STATE_CHANGE_TOLERANCE_H` is 6 h — chosen so
±6 h absorbs the DST step "without admitting a different day". So `state_change` refused every
pairing: every basin's 24 h entry in `/viz/basins` carried `growth: null` — and therefore no
`rank` — with a refusal reason where a rate belonged, and the whole Tier 0 velocity surface was
dead. Cron runs on 2026-08-25 02:06, 2026-08-26 00:11 and 2026-08-27
00:10 were all UTC-assumed; the one correctly stamped batch, 2026-08-27 09:26, was a manual
off-cron run from a laptop. That split is what made the defect look intermittent.

**FACT.** The pre-existing test asserting the seed's zones resolve
(`test_every_seeded_gauge_has_a_time_zone_so_the_day_boundary_is_never_assumed`) passed throughout.
It asked whether the **test runtime's** tz database resolved the key, and both a laptop and CI carry
the aliases the image drops. A runtime-dependent assertion cannot detect a runtime-dependent defect.

## Decision

**Seed canonical IANA `Area/Location` names, and let the seed refuse everything else.**
`cascade_core.seed.SEEDABLE_TIME_ZONES` names the zones the seed may write —
`America/Los_Angeles` today — and `_validate_time_zones` raises on any other key, and again on any
allowed key this runtime cannot actually resolve. The seed runs in the same image the jobs do, so
an unresolvable key now fails once and loudly at seed time instead of degrading quietly in every
derived row.

The check has two halves and both are load-bearing: membership is **runtime-independent**, so a
legacy alias is refused even on a host that resolves it; resolution is **runtime-dependent**, so an
allowed key missing from this particular image is refused too.

## Alternatives considered

- **Install `tzdata-legacy` (or the `tzdata` PyPI package) in the image.** Rejected: it treats the
  symptom. `PST8PDT` is a compatibility alias; the canonical name is what the rest of the codebase
  should carry, and a bigger tz database would let the next alias in silently. It also leaves the
  runtime-dependent hole open — a future zone absent from *whatever* database is installed would
  degrade exactly the same way.
- **Make `daily_mean_valid_time` raise instead of degrading.** Rejected: an unknown zone is a
  legitimate state for a station the platform has not configured, and the flag is the honest answer
  there. The defect was not the fallback; it was reaching the fallback from a *configured* value.
- **Assert canonicality in CI by parsing `tzdata.zi`/`zone.tab`.** Rejected: it makes the gate
  depend on files the CI host may or may not ship, and a gate that skips when its input is missing
  is the same failure mode as the one being fixed. An explicit allowlist fails closed.
- **Rewrite the flagged historical rows.** Rejected — see below.

## The historical rows are left exactly as they are

The UTC-assumed rows stay. They are honestly flagged, DATA_DOCTRINE forbids rewriting history
casually, and — decisively — they are **inert against the regime that replaces them**: a UTC-assumed
row sits 7 h (PDT) or 8 h (PST) from a correctly stamped endpoint, past the 6 h tolerance, so
`state_change` can never mix one with a correct row.

Be exact about the limit of that claim, because the looser version is false. Two UTC-assumed rows
are exactly 24 h apart and DO pair with each other when the endpoint is itself UTC-assumed —
`state_change` returns a growth from them. What retires them is that no such endpoint is produced
any more: once the seed carries a resolvable zone, every new row is local-stamped, and a
local-stamped endpoint cannot reach back across the 7 h step. They go stale rather than being
neutralised, and the assertion that they are unreachable is pinned by
`test_a_utc_assumed_row_can_never_pair_with_a_correctly_stamped_one`, which tests both directions.
Nothing is backfilled to manufacture a growth rank. The 24 h `growth` becomes non-null on its own once two correctly stamped daily rows exist
— one cron interval after the first correct row, not before.

## Consequences

- A seed carrying an unresolvable zone now **fails the seed run** rather than producing three days of
  quietly degraded rows. That is the intended trade.
- `station.time_zone` changes value for all seven seeded stations. It is CONFIGURED metadata, not an
  observation: no stored value row is altered by re-seeding.
- Re-running `usgs.fetch_daily_percentile` after the re-seed writes a **new** row for the same day at
  the local stamp. The UTC-stamped row for that day remains. Both are real, differently stamped, and
  differently flagged — append-only, as ADR-0010 requires.
- Widening `SEEDABLE_TIME_ZONES` requires verifying the new key against the deployment image; the
  command is in the comment block above the constant.
- What would make us revisit: a base image change, or a station outside Pacific time.

## Evidence

- [research/nwis-stat-successor-2026-08-27.md](../research/nwis-stat-successor-2026-08-27.md)
  — production `derived_feature` timestamps and flags, and the first diagnosis.
- `docker run --rm python:3.14-slim python -c "…"`, re-run 2026-08-27: 486 available zones;
  `America/Los_Angeles` and `UTC` resolve, `PST8PDT`, `US/Pacific`, `EST5EDT` raise.
- Tests: `test_a_legacy_time_zone_alias_is_refused_at_seed_time`,
  `test_every_seedable_time_zone_resolves_and_is_not_a_legacy_alias` (tests/unit/test_p3_foundation.py);
  `test_every_seeded_gauge_has_a_time_zone_so_the_day_boundary_is_never_assumed` (tests/unit/test_susceptibility.py).

## Production outcome (2026-08-27)

The seed fix changes what a future seed writes; it does not correct rows already in a database,
and re-seeding is a manual act. Migration `0004` carries the correction on the path the
deployment already runs. Landed `5d00299`, all five CI jobs green (445 offline / 15 pg).

`alembic upgrade head` against production, from `0003`:

```
Running upgrade 0003 -> 0004, Correct the one seeded station time zone …
0004: station.time_zone 'PST8PDT' -> 'America/Los_Angeles' on 7 row(s)
```

Full row snapshots either side: all 7 stations corrected, **zero non-`time_zone` differences**,
same station set. No other table touched, no schema change, no derived row rewritten.

**The production image resolves the zone — proved by the job, not by a laptop.** The next
`usgs.fetch_daily_percentile` run, deferred to the production worker and executed in the
container, wrote 6 rows stamped `2026-08-27T07:00:00Z` — local midnight ending 2026-08-26 in PDT,
derived from `America/Los_Angeles` rather than assumed — with `quality: ['provisional']` and **no
`day_boundary_assumed_utc`**. An image that could not resolve the key would have produced
`00:00Z` and the flag; that is what it had produced on every prior container run.

**`state_change` recovered immediately, without waiting a day.** Production already held one
correctly stamped batch at `2026-08-26T07:00Z` from an off-cron manual run; the new row at
`2026-08-27T07:00Z` is exactly 24 h later, so the pair was available at once. All six basins now
publish a non-null 24 h `growth` with `span_h: 24.0`.

The pair is both-local, and that was verified rather than inferred — the values alone cannot
distinguish the two stampings, because a UTC-assumed row and its local twin carry the *same*
daily mean. Re-running `state_change` over the real production rows shows only LOCAL rows fall
inside `STATE_CHANGE_TOLERANCE_H` of either endpoint:

```
end anchor 2026-08-27T07:00:00+00:00
  within 6.0h of the to   anchor: [('2026-08-27T07:00:00+00:00', 'LOCAL')]
  within 6.0h of the from anchor: [('2026-08-26T07:00:00+00:00', 'LOCAL')]
  -> growth 0.9831932773109243   (the surface reports 0.9832)
```

This is §"The historical rows are left exactly as they are" holding in production: the 24
UTC-assumed rows are all still present, still flagged, and simply unreachable from a
local-stamped endpoint 7 h away. Nothing was deleted, superseded or backfilled, and
`STATE_CHANGE_TOLERANCE_H` is untouched at 6 h.

Two nulls that are correct and are not defects. The 48 h window still refuses —
`no daily mean within 6 h of 2026-08-25T07:00:00+00:00` — because only a UTC-assumed row exists
for that date; it closes on its own. And the 24 h growth `rank` is null with the reason *outside
the largest 10 % of this gauge's N changes over this window, which is the only part stored*: the
flows are steady, so the change is below the stored p90 tail. The rank is populated where the
reference supports it, and here it honestly does not.
