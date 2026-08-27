"""``method:streamflow-doy-climatology@1.0.0`` — the platform's OWN day-of-year flow climatology.

Why the platform builds this rather than reading a published one: `DATA_DOCTRINE.md` §8 says a
percentile must name the climatology it is against, and the only USGS service that publishes a
discharge day-of-year ladder for these gauges is the legacy `nwis/stat` table, which
decommissions in Q1 2027 (the modern statistics API served ZERO discharge normals at 12200500 on
2026-08-24 — tests/fixtures/providers/usgs_stats/observation_normals_12200500_00060.json). The
published table is kept as a CROSS-CHECK under its own method id and is never averaged with this
one: disagreement is information (DATA_DOCTRINE §10).

Pure computation — no IO, no database, no clock beyond what the caller passes. Deterministic by
construction so the golden test in tests/unit/test_susceptibility.py reproduces a stored ladder
byte-for-byte.

METHOD, stated so it can be argued with:

- **Input filter.** Approved daily means only. Provisional values can be revised and would make
  the climatology change under the platform's feet; they are counted and reported, not used.
- **Day-of-year key.** ``MM-DD`` over a 366-day (leap) calendar, so 02-29 is a real key with its
  own (smaller) sample rather than being folded into 03-01.
- **Window.** ±``WINDOW_DAYS`` calendar days, wrapping at the year boundary, to stabilise the
  sample. This widens the sample ~5× and is the same convention USGS WaterWatch uses.
- **Percentile estimator.** Linear interpolation between order statistics (the R type-7 /
  numpy default rule) on the sorted sample. Written out longhand here so the result does not
  depend on a library version.
- **What it is NOT.** Not a probability, not a flood frequency, not a return period. It is the
  rank of today's flow within this gauge's own recorded flow for this time of year.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from cascade_providers_usgs.stats_parser import DailyMean, PublishedDoyStat

METHOD_ID = "method:streamflow-doy-climatology@1.0.0"
PUBLISHED_METHOD_ID = "method:usgs-published-doy-stats@1.0.0"
#: The record the seven-point ladder throws away, kept under its OWN method id so
#: `method:streamflow-doy-climatology@1.0.0` keeps producing byte-identical output and register
#: X8 (which ladder vintage?) is untouched by this. See :func:`build_record_context`.
#: Bumped from @1.0.0 when the growth reference moved OUT of this document into
#: `GROWTH_REFERENCE_METHOD_ID`. The stored shape changed, so the id changed — versioning what is
#: stored, not the code that stores it. See `growth_values_json` for why they were separated.
RECORD_CONTEXT_METHOD_ID = "method:streamflow-record-context@2.0.0"

#: The gauge's own distribution of past day-over-day changes, stored SEPARATELY from the window
#: tail so the velocity can read it without paying for the tail.
#:
#: They were one document until 2026-08-27, and that coupling had a measured consequence. The
#: record context is read only at or above `RANK_READ_EDGE` (p90) because the tail is large and
#: is wanted only where the ladder clamps — but the VELOCITY fires below p90, which is the whole
#: point of having one, so the growth rank was unavailable on exactly the days the velocity
#: earned its lead time. Measured across all six basins in `research/event-zero-ab-2026-08-27.md`
#: §7c: 100 % of the 264 h of lead the Tier 0 change bought was delivered by a statement that
#: structurally could not carry a rank.
#:
#: Splitting rather than widening the gate is what the payload says: the growth block is 247 KiB
#: of the 952 KiB context across the six seeded gauges (26 %), so reading it alone costs 74 %
#: less than reading the whole context on every request, and total storage is unchanged because
#: nothing is duplicated.
GROWTH_REFERENCE_METHOD_ID = "method:streamflow-growth-reference@1.0.0"
PERCENTILES: tuple[int, ...] = (5, 10, 25, 50, 75, 90, 95)
WINDOW_DAYS = 2
APPROVED = "Approved"
MIN_SAMPLE = 10  # below this a day's ladder is refused rather than published from a handful of years

# The sentence the USGS attaches to its own published statistics; DATA_SOURCES/method rows must
# reproduce it wherever the cross-check is shown (design §2.1).
USGS_STATISTICS_DISCLAIMER = (
    "USGS: these statistics are based on approved daily-mean data and may not match "
    "published USGS reports."
)
METHOD_PARAMETERS: dict[str, Any] = {
    "percentiles": list(PERCENTILES),
    "window_days": WINDOW_DAYS,
    "approval_filter": APPROVED,
    "min_sample": MIN_SAMPLE,
    "estimator": "linear interpolation between order statistics (R type 7)",
    "note": (
        "Day-of-year percentiles of published daily-mean discharge at one gauge. An observed "
        "integrator of soil water, groundwater and channel storage — not a soil-moisture "
        "estimate, not a snow statement, not a forecast, and never a probability."
    ),
}

# A leap year gives all 366 day-of-year keys, 02-29 included.
_LEAP = 2000
DOY_KEYS: tuple[str, ...] = tuple(
    (date(_LEAP, 1, 1) + timedelta(days=i)).strftime("%m-%d") for i in range(366)
)
_KEY_INDEX = {key: i for i, key in enumerate(DOY_KEYS)}


def doy_key(day: date) -> str:
    return f"{day.month:02d}-{day.day:02d}"


def window_keys(key: str, *, window_days: int = WINDOW_DAYS) -> tuple[str, ...]:
    """The ±window day-of-year keys around ``key``, wrapping at the year boundary."""
    if key not in _KEY_INDEX:
        raise ValueError(f"not a day-of-year key: {key!r}")
    i = _KEY_INDEX[key]
    return tuple(DOY_KEYS[(i + d) % 366] for d in range(-window_days, window_days + 1))


def percentile(sorted_values: Sequence[float], p: float) -> float:
    """The p-th percentile (0..100) of an already-sorted sample, R type 7 / numpy default."""
    if not sorted_values:
        raise ValueError("empty sample")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (len(sorted_values) - 1) * (p / 100.0)
    lo = math.floor(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return float(sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo]))


@dataclass(frozen=True)
class DoyLadder:
    """One day-of-year's percentile ladder plus how many values stand behind it."""

    key: str
    values: dict[int, float]  # {5: ..., 95: ...}
    sample_count: int


@dataclass(frozen=True)
class DoyClimatology:
    site: str
    unit: str
    method_id: str
    ladders: dict[str, DoyLadder]
    begin_year: int | None
    end_year: int | None
    used_rows: int
    skipped: dict[str, int]

    @property
    def climatology_ref(self) -> str:
        span = f"{self.begin_year}-{self.end_year}" if self.begin_year and self.end_year else "unknown"
        origin = "usgs-ogc-daily" if self.method_id == METHOD_ID else "usgs-nwis-stat"
        return f"{origin}:{self.site}:{span}"

    def to_values_json(self) -> dict[str, Any]:
        """The shape stored in ``derived_feature.values_json`` — one row carries the whole ladder."""
        return {
            "site": self.site,
            "unit": self.unit,
            "percentiles": list(PERCENTILES),
            "begin_year": self.begin_year,
            "end_year": self.end_year,
            "used_rows": self.used_rows,
            "skipped": dict(self.skipped),
            "parameters": METHOD_PARAMETERS if self.method_id == METHOD_ID else {"source": "USGS published nwis/stat table", "disclaimer": USGS_STATISTICS_DISCLAIMER},
            "ladder": {
                key: {"n": ladder.sample_count, **{f"p{p:02d}": ladder.values[p] for p in PERCENTILES if p in ladder.values}}
                for key, ladder in sorted(self.ladders.items())
            },
        }


def from_values_json(doc: dict[str, Any], *, method_id: str) -> DoyClimatology:
    """Rebuild a climatology from a stored ``derived_feature.values_json`` blob."""
    ladders: dict[str, DoyLadder] = {}
    for key, entry in (doc.get("ladder") or {}).items():
        values = {p: float(entry[f"p{p:02d}"]) for p in PERCENTILES if f"p{p:02d}" in entry}
        if values:
            ladders[key] = DoyLadder(key=key, values=values, sample_count=int(entry.get("n", 0)))
    return DoyClimatology(
        site=str(doc.get("site", "")),
        unit=str(doc.get("unit", "cfs")),
        method_id=method_id,
        ladders=ladders,
        begin_year=doc.get("begin_year"),
        end_year=doc.get("end_year"),
        used_rows=int(doc.get("used_rows", 0)),
        skipped=dict(doc.get("skipped") or {}),
    )


def build_doy_climatology(
    rows: Iterable[DailyMean],
    *,
    site: str,
    unit: str = "cfs",
    window_days: int = WINDOW_DAYS,
    min_sample: int = MIN_SAMPLE,
) -> DoyClimatology:
    """Build the day-of-year ladder from a station's published daily means (approved only)."""
    by_key: dict[str, list[float]] = {key: [] for key in DOY_KEYS}
    years: list[int] = []
    skipped = {"not_approved": 0, "no_value": 0, "unparseable": 0, "negative": 0, "other_site": 0}
    used = 0
    for row in rows:
        if row.site != site:
            skipped["other_site"] += 1
            continue
        if row.approval_status != APPROVED:
            skipped["not_approved"] += 1
            continue
        if row.raw_value is None:
            skipped["no_value"] += 1
            continue
        try:
            value = float(row.raw_value)
        except ValueError:
            skipped["unparseable"] += 1
            continue
        if not math.isfinite(value) or value < 0:
            skipped["negative"] += 1
            continue
        by_key[doy_key(row.day)].append(value)
        years.append(row.day.year)
        used += 1
    ladders: dict[str, DoyLadder] = {}
    for key in DOY_KEYS:
        sample: list[float] = []
        for neighbour in window_keys(key, window_days=window_days):
            sample.extend(by_key[neighbour])
        if len(sample) < min_sample:
            continue  # a ladder from a handful of values is refused, not published thin
        sample.sort()
        ladders[key] = DoyLadder(key=key, values={p: percentile(sample, p) for p in PERCENTILES}, sample_count=len(sample))
    return DoyClimatology(
        site=site,
        unit=unit,
        method_id=METHOD_ID,
        ladders=ladders,
        begin_year=min(years) if years else None,
        end_year=max(years) if years else None,
        used_rows=used,
        skipped=skipped,
    )


def published_climatology(stats: Iterable[PublishedDoyStat], *, site: str, unit: str = "cfs") -> DoyClimatology:
    """Wrap the USGS published nwis/stat table in the same shape, under ITS OWN method id.

    Stored separately and never fused with the Cascade-built ladder (design §2.2 step 2).
    """
    ladders: dict[str, DoyLadder] = {}
    begin: list[int] = []
    end: list[int] = []
    skipped = {"other_site": 0, "no_percentiles": 0}
    used = 0
    for stat in stats:
        if stat.site and stat.site != site:
            skipped["other_site"] += 1
            continue
        key = f"{stat.month:02d}-{stat.day:02d}"
        if key not in _KEY_INDEX or not stat.percentiles:
            skipped["no_percentiles"] += 1
            continue
        ladders[key] = DoyLadder(key=key, values=dict(stat.percentiles), sample_count=stat.count or 0)
        used += 1
        if stat.begin_year:
            begin.append(stat.begin_year)
        if stat.end_year:
            end.append(stat.end_year)
    return DoyClimatology(
        site=site, unit=unit, method_id=PUBLISHED_METHOD_ID, ladders=ladders,
        begin_year=min(begin) if begin else None, end_year=max(end) if end else None,
        used_rows=used, skipped=skipped,
    )


OUTSIDE_RANGE = "outside_climatology_range"


@dataclass(frozen=True)
class PercentileResult:
    percentile: float
    quality: tuple[str, ...]
    sample_count: int
    ladder_key: str


def percentile_of(value: float, ladder: DoyLadder) -> PercentileResult:
    """Rank ``value`` inside a stored ladder by linear interpolation between its points.

    Beyond the ends the answer is CLAMPED to the outermost stored percentile and flagged
    ``outside_climatology_range``: the ladder simply does not know where in the tail the value
    sits, and inventing 99.4 from a p95 anchor would be a fabricated number. The flag travels
    with the value so the surface can say "at or beyond the 95th percentile".
    """
    points = sorted(ladder.values.items())
    if not points:
        raise ValueError(f"empty ladder for {ladder.key}")
    if value <= points[0][1]:
        return PercentileResult(float(points[0][0]), (OUTSIDE_RANGE,) if value < points[0][1] else (), ladder.sample_count, ladder.key)
    if value >= points[-1][1]:
        return PercentileResult(float(points[-1][0]), (OUTSIDE_RANGE,) if value > points[-1][1] else (), ladder.sample_count, ladder.key)
    for (p_lo, v_lo), (p_hi, v_hi) in zip(points, points[1:], strict=False):
        if v_lo <= value <= v_hi:
            if v_hi == v_lo:
                return PercentileResult(float(p_hi), (), ladder.sample_count, ladder.key)
            frac = (value - v_lo) / (v_hi - v_lo)
            return PercentileResult(float(p_lo + frac * (p_hi - p_lo)), (), ladder.sample_count, ladder.key)
    # A non-monotone ladder (possible only in a corrupt stored blob) is refused, not guessed.
    raise ValueError(f"ladder for {ladder.key} is not monotone: {points}")


def p50_disagreement(cascade: DoyClimatology, published: DoyClimatology, key: str) -> float | None:
    """Signed fractional difference (cascade - published) / published of the two p50s, or None.

    None means "no cross-check available for this day", which is NOT the same as agreement and
    must not be reported as such.
    """
    a, b = cascade.ladders.get(key), published.ladders.get(key)
    if a is None or b is None or 50 not in a.values or 50 not in b.values or b.values[50] == 0:
        return None
    return (a.values[50] - b.values[50]) / b.values[50]


def daily_mean_valid_time(day: date, *, time_zone: str | None) -> tuple[datetime, tuple[str, ...]]:
    """The instant a station-local daily mean is complete: local midnight ENDING that day.

    A USGS daily mean is the mean over the station's local calendar day, so the value labeled
    2026-08-23 is only complete at 00:00 local on 2026-08-24 (DATA_DOCTRINE §3: store the
    provider's day boundary, never assume UTC). When the station's zone is unknown to the
    platform the UTC boundary is used and the caller is TOLD so with a quality flag, rather than
    the assumption disappearing into the number.
    """
    end_of_day = day + timedelta(days=1)
    utc_midnight = datetime(end_of_day.year, end_of_day.month, end_of_day.day, tzinfo=UTC)
    if not time_zone:
        return utc_midnight, ("day_boundary_assumed_utc",)
    try:
        zone = ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, ValueError):
        # No tz database entry (a slim container image can lack tzdata): degrade to the UTC
        # boundary and SAY so, rather than letting the assumption vanish into the number.
        return utc_midnight, ("day_boundary_assumed_utc",)
    return datetime(end_of_day.year, end_of_day.month, end_of_day.day, tzinfo=zone).astimezone(UTC), ()


# =============================================================================================
# `method:streamflow-record-context@1.0.0` — what the seven-point ladder threw away
# =============================================================================================
#
# THE DEFECT THIS ANSWERS, measured from production (`research/tier0-measured-basis-2026-08-26.md`
# §3 as corrected, and `research/high-tail-selection-2026-08-27.md`). `percentile_of` clamps at
# the ladder's top breakpoint, so 24,976 cfs and 72,440 cfs both read `p95` on the Sauk, and a
# percentile derivative between two clamped days is identically +0 through the crest.
#
# The record knows far more than the ladder stores: at the Sauk's 12-11 key the +/-2-day window
# holds 495 approved daily means over 99 water years, 25 of them strictly above p95, reaching
# 62,600 cfs. Continuing the empirical rank is therefore possible — but it is NOT sufficient,
# because Event Zero's crest exceeded the ENTIRE window sample at four of the six gauges. A rank
# is bounded by 1 exactly as a percentile is bounded by 100. Only a magnitude ratio is unbounded.
#
# So this module stores three things, and the surface (`cascade_hydrology.susceptibility`)
# assembles them into statements that are never combined:
#
#   1. the TAIL of each day-of-year window sample — every value above that key's p90, with its
#      day — so the exact rank, the previous maximum and "larger than the whole record" are
#      computable instead of censored at p95;
#   2. the per-key SUPPORT — n, distinct water years, maximum and its day, and the tail floor —
#      so every statement prints the sample it is a statement about;
#   3. the gauge's own distribution of DAY-OVER-DAY GROWTH, upper decile only, so "is that fast?"
#      is answered by a rank in this gauge's history rather than by a cutoff nobody has validated.
#
# WHAT IS DELIBERATELY NOT HERE: no new percentile breakpoints (candidate A — deferred, it fixes
# the level and measurably not the velocity, and its per-gauge support rule is unsettled), no
# distribution fit, no return period, no exceedance probability, no band edge on anything, and
# no change whatsoever to `METHOD_ID`'s output.

#: A tail statement is refused unless its exceedance set spans this many distinct water years.
#: Measured (`high-tail-selection-2026-08-27.md` §4): the window's n is days, not independent
#: events — 495 values at the Sauk are 99 water years x 5 consecutive days, and one December
#: flood contributes up to 5 of them. Jackknifing one water year out moves p99 by 0.9-19.2 %,
#: and at cedar the whole p99 exceedance set is a SINGLE water year (December 2015). Five is the
#: smallest count at which a tail point survives losing any one year. A support rule, not a
#: hydrologic threshold — and it *labels*, it never suppresses.
MIN_TAIL_YEARS = 5

#: Which ladder breakpoint bounds the stored tail. p90 and not p95: the surface needs the exact
#: rank wherever the percentile is within one breakpoint of clamping, and p90 is also the top
#: band edge, so the stored region is exactly the region where the banded surface stops
#: discriminating. Below it the ladder resolves perfectly well and no rank is published.
TAIL_FLOOR_PERCENTILE = 90

#: The windows the day-over-day growth reference is built for, in hours. These are the windows
#: `tier0-measured-basis-2026-08-26.md` §2 measured the 1-3 day lead over.
GROWTH_WINDOWS_H: tuple[int, ...] = (24, 48)

#: How much of the growth distribution is stored. The upper decile: a rank is only ever asked
#: for when something is moving, and storing 36,000 ratios per gauge to answer about the 3,600
#: that matter is not a trade worth making. Below the stored floor the answer is a BOUND with
#: its reason, never a fabricated rank.
GROWTH_TAIL_FRACTION = 0.10

#: Growth ratios are stored rounded, and the query value is rounded the same way before it is
#: ranked, so the rank is reproducible from the stored blob rather than from float noise.
GROWTH_ROUND = 4

RECORD_CONTEXT_PARAMETERS: dict[str, Any] = {
    "window_days": WINDOW_DAYS,
    "approval_filter": APPROVED,
    "min_sample": MIN_SAMPLE,
    "tail_floor_percentile": TAIL_FLOOR_PERCENTILE,
    "min_tail_years": MIN_TAIL_YEARS,
    "growth_windows_h": list(GROWTH_WINDOWS_H),
    "growth_tail_fraction": GROWTH_TAIL_FRACTION,
    "estimator": "exact counts over the approved daily-mean record; no fit, no interpolation",
    "note": (
        "The empirical record behind the day-of-year ladder, kept whole where the ladder "
        "clamps. Ranks and counts only — never a probability, a return period or an AEP."
    ),
}


def water_year(day: date) -> int:
    """USGS convention: water year N runs 1 Oct N-1 -> 30 Sep N.

    Water years and not calendar years, because a December flood belongs to the winter it
    happened in, and splitting one winter across two "years" would double-count its support.
    """
    return day.year + 1 if day.month >= 10 else day.year


@dataclass(frozen=True)
class KeySupport:
    """What stands behind one day-of-year key, printed beside anything derived from it."""

    key: str
    n: int  # values in the +/-window sample
    water_years: int  # DISTINCT water years among them — the honest denominator
    maximum: float
    maximum_day: date
    tail_floor: float  # the p90 flow; the rank is exact at or above this and refused below it
    tail_years: int  # distinct water years strictly above the tail floor


@dataclass(frozen=True)
class GrowthReference:
    """This gauge's own distribution of `Q(d) / Q(d - window)`, upper decile only.

    `n` counts every usable pair in the record, so a rank taken against `top` still names the
    full denominator: "1,514th of 35,976" is true even though only 3,598 ratios are stored.
    """

    window_h: int
    n: int
    top: tuple[float, ...]  # ascending; the largest `ceil(GROWTH_TAIL_FRACTION * n)` ratios
    span_days: int  # the pair separation in days, so the label can say what it compared

    @property
    def floor(self) -> float | None:
        return self.top[0] if self.top else None

    def rank(self, growth: float) -> tuple[int | None, str | None]:
        """(rank, reason). Exact at or above the stored floor; a refusal with its reason below it."""
        if not self.top:
            return None, "no growth reference stored for this gauge"
        g = round(growth, GROWTH_ROUND)
        if g < self.top[0]:
            pct = int(round(GROWTH_TAIL_FRACTION * 100))
            return None, (
                f"outside the largest {pct} % of this gauge's {self.n:,} {self.window_h} h "
                "changes, which is the only part of the distribution stored"
            )
        return 1 + sum(1 for t in self.top if t > g), None


@dataclass(frozen=True)
class RecordContext:
    """The empirical record behind one gauge's ladder, at the resolution the tail needs."""

    site: str
    unit: str
    window_days: int
    keys: dict[str, KeySupport]
    tail: tuple[tuple[date, float], ...]  # ascending by day
    growth: dict[int, GrowthReference]
    begin_water_year: int | None
    end_water_year: int | None
    used_rows: int

    def growth_values_json(self) -> dict[str, Any]:
        """The growth reference alone, as its own stored document (`GROWTH_REFERENCE_METHOD_ID`).

        Carries its own identity — site, unit, window, period of record, parameters — rather than
        pointing at the record context. The two are written by the same job from the same parsed
        rows and the same artifact, but they are separate STATEMENTS with different read rules and
        either may be absent, so a consumer must be able to answer "where did this come from" from
        the row in front of it.

        Nothing is duplicated: `to_values_json` no longer carries `growth`, which is why
        `RECORD_CONTEXT_METHOD_ID` went to @2.0.0.
        """
        return {
            "site": self.site,
            "unit": self.unit,
            "window_days": self.window_days,
            "begin_water_year": self.begin_water_year,
            "end_water_year": self.end_water_year,
            "used_rows": self.used_rows,
            "parameters": RECORD_CONTEXT_PARAMETERS,
            "growth": {
                str(w): {"n": g.n, "span_days": g.span_days, "top": list(g.top)}
                for w, g in sorted(self.growth.items())
            },
        }

    @property
    def reference_ref(self) -> str:
        span = f"WY{self.begin_water_year}-WY{self.end_water_year}" if self.begin_water_year else "unknown"
        return f"usgs-ogc-daily:{self.site}:{span}"

    def window_tail(self, key: str) -> list[tuple[date, float]]:
        """The stored tail values whose day falls inside ``key``'s +/-window."""
        wanted = set(window_keys(key, window_days=self.window_days))
        return [(d, v) for d, v in self.tail if doy_key(d) in wanted]

    def to_values_json(self) -> dict[str, Any]:
        return {
            "site": self.site,
            "unit": self.unit,
            "window_days": self.window_days,
            "begin_water_year": self.begin_water_year,
            "end_water_year": self.end_water_year,
            "used_rows": self.used_rows,
            "parameters": RECORD_CONTEXT_PARAMETERS,
            "keys": {
                s.key: {
                    "n": s.n,
                    "water_years": s.water_years,
                    "max": s.maximum,
                    "max_day": s.maximum_day.isoformat(),
                    "tail_floor": s.tail_floor,
                    "tail_years": s.tail_years,
                }
                for s in sorted(self.keys.values(), key=lambda s: s.key)
            },
            "tail": [[d.isoformat(), v] for d, v in self.tail],
        }


def record_context_from_values_json(doc: dict[str, Any]) -> RecordContext:
    """Rebuild a :class:`RecordContext` from a stored `derived_feature.values_json` blob."""
    keys: dict[str, KeySupport] = {}
    for key, entry in (doc.get("keys") or {}).items():
        keys[key] = KeySupport(
            key=key,
            n=int(entry["n"]),
            water_years=int(entry["water_years"]),
            maximum=float(entry["max"]),
            maximum_day=date.fromisoformat(entry["max_day"]),
            tail_floor=float(entry["tail_floor"]),
            tail_years=int(entry.get("tail_years", 0)),
        )
    growth: dict[int, GrowthReference] = {}
    for window, entry in (doc.get("growth") or {}).items():
        growth[int(window)] = GrowthReference(
            window_h=int(window),
            n=int(entry["n"]),
            top=tuple(float(v) for v in entry.get("top") or ()),
            span_days=int(entry.get("span_days", int(window) // 24)),
        )
    return RecordContext(
        site=str(doc.get("site", "")),
        unit=str(doc.get("unit", "cfs")),
        window_days=int(doc.get("window_days", WINDOW_DAYS)),
        keys=keys,
        tail=tuple((date.fromisoformat(d), float(v)) for d, v in (doc.get("tail") or [])),
        growth=growth,
        begin_water_year=doc.get("begin_water_year"),
        end_water_year=doc.get("end_water_year"),
        used_rows=int(doc.get("used_rows", 0)),
    )


def _approved_daily_means(rows: Iterable[DailyMean], *, site: str) -> list[tuple[date, float]]:
    """The same filter :func:`build_doy_climatology` applies, so both read one record.

    Approved only, one value per day (the last seen wins, matching the ladder's append order),
    finite and non-negative. If these two ever disagreed, the tail would be a statement about a
    different sample from the ladder it extends — which is exactly the kind of silent drift the
    golden test in tests/unit/test_susceptibility.py exists to catch.
    """
    by_day: dict[date, float] = {}
    for row in rows:
        if row.site != site or row.approval_status != APPROVED or row.raw_value is None:
            continue
        try:
            value = float(row.raw_value)
        except ValueError:
            continue
        if not math.isfinite(value) or value < 0:
            continue
        by_day[row.day] = value
    return sorted(by_day.items())


def build_growth_reference(
    daily: Sequence[tuple[date, float]], *, window_h: int, tail_fraction: float = GROWTH_TAIL_FRACTION
) -> GrowthReference:
    """`Q(d) / Q(d - window)` over every day-pair the record actually holds.

    Pairs are matched on the CALENDAR, not on adjacency in the list: a gap in the record must
    not silently become a 24-hour change measured over three years. A pair is used only where
    both days exist and both are strictly positive — a ratio through zero is not a rate.
    """
    span_days = max(1, window_h // 24)
    by_day = dict(daily)
    ratios: list[float] = []
    for day, value in daily:
        prior = by_day.get(day - timedelta(days=span_days))
        if prior is None or prior <= 0 or value <= 0:
            continue
        ratios.append(round(value / prior, GROWTH_ROUND))
    ratios.sort()
    keep = math.ceil(tail_fraction * len(ratios)) if ratios else 0
    return GrowthReference(window_h=window_h, n=len(ratios), top=tuple(ratios[len(ratios) - keep:]), span_days=span_days)


def build_record_context(
    rows: Iterable[DailyMean],
    *,
    site: str,
    unit: str = "cfs",
    window_days: int = WINDOW_DAYS,
    min_sample: int = MIN_SAMPLE,
    tail_floor_percentile: int = TAIL_FLOOR_PERCENTILE,
) -> RecordContext:
    """Build the record context from the same approved daily-mean record as the ladder.

    Bounded by construction. The stored tail is every day whose value exceeds the LOWEST tail
    floor among the keys whose window contains it, which guarantees the property the rank needs:
    for any key `K` and any value at or above `p90(K)`, every window value above it is stored,
    so the rank is EXACT and not an estimate. Roughly a tenth of the record survives — about
    3,100 pairs at a 100-year gauge.
    """
    daily = _approved_daily_means(rows, site=site)
    by_key: dict[str, list[tuple[date, float]]] = {key: [] for key in DOY_KEYS}
    for day, value in daily:
        by_key[doy_key(day)].append((day, value))

    supports: dict[str, KeySupport] = {}
    floors: dict[str, float] = {}
    for key in DOY_KEYS:
        sample: list[tuple[date, float]] = []
        for neighbour in window_keys(key, window_days=window_days):
            sample.extend(by_key[neighbour])
        if len(sample) < min_sample:
            continue  # no ladder here, so no rank either — the two refuse together
        values = sorted(v for _, v in sample)
        floor = percentile(values, tail_floor_percentile)
        peak_day, peak = max(sample, key=lambda p: (p[1], p[0]))
        floors[key] = floor
        supports[key] = KeySupport(
            key=key,
            n=len(sample),
            water_years=len({water_year(d) for d, _ in sample}),
            maximum=peak,
            maximum_day=peak_day,
            tail_floor=floor,
            tail_years=len({water_year(d) for d, v in sample if v > floor}),
        )

    tail: list[tuple[date, float]] = []
    for day, value in daily:
        covering = [floors[k] for k in window_keys(doy_key(day), window_days=window_days) if k in floors]
        if covering and value > min(covering):
            tail.append((day, value))

    years = [water_year(d) for d, _ in daily]
    return RecordContext(
        site=site,
        unit=unit,
        window_days=window_days,
        keys=supports,
        tail=tuple(tail),
        growth={w: build_growth_reference(daily, window_h=w) for w in GROWTH_WINDOWS_H},
        begin_water_year=min(years) if years else None,
        end_water_year=max(years) if years else None,
        used_rows=len(daily),
    )
