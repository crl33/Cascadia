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
