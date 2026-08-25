"""SNOTEL point values -> basin CONTEXT numbers. Pure computation; no IO, no clock.

Two numbers, both unscored (`HYDROLOGY.md` §7 — more SWE is not more risk):

- ``basin_swe_percent_of_median`` — the unweighted mean of ``value / median × 100`` across the
  basin's mapped SNOTEL sites. A **point-network** statistic: 2–7 pillows at 2,250–6,490 ft are
  not a basin mean, and the label says so with ``n`` and the elevations.
- ``snotel_precip_14d_percent_of_median`` — AWDB ``PREC`` is water-year ACCUMULATED
  precipitation, so the 14-day amount is the DIFFERENCE ``PREC(D) − PREC(D−14)`` and its
  reference is the same difference of the medians. A negative difference means the water year
  rolled over inside the window; that site is dropped with a reason, never clamped to zero.

The hard rule everywhere below: **a percent-of-median with a zero or missing denominator is
UNKNOWN, not zero and not 100.** In late August every mapped WTEQ median is 0.0 (verified live
2026-08-24, tests/fixtures/providers/awdb/data_wteq_prec_puget.json), so the honest answer for
the SWE driver right now is "no value, and here is why" — which is exactly what this returns.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from cascade_providers_awdb.parser import AwdbSeries, AwdbStation

SWE_FEATURE = "basin_swe_percent_of_median"
PRECIP_FEATURE = "snotel_precip_14d_percent_of_median"
SWE_METHOD_ID = "method:snotel-basin-swe-context@1.0.0"
PRECIP_METHOD_ID = "method:snotel-precip-14d-context@1.0.0"
# HYDROLOGY §7: the ONLY direction these drivers may ever carry. A change here is a doctrine
# change, and tests/unit/test_susceptibility.py fails on it.
CONTEXT_DIRECTION = "context_not_scored"
PRECIP_WINDOW_DAYS = 14
SUSPECT_QC_FLAGS = frozenset({"S", "N"})  # suspect; no profile


@dataclass(frozen=True)
class SiteContribution:
    triplet: str
    name: str
    elevation_ft: float | None
    value: float
    median: float
    percent_of_median: float


@dataclass(frozen=True)
class ContextResult:
    """One basin-scale context number, or a specific reason there is not one."""

    feature: str
    method_id: str
    value: float | None
    unit: str
    day: date | None
    sites: tuple[SiteContribution, ...]
    excluded: dict[str, int]
    reason: str | None
    mapped_site_count: int

    @property
    def direction(self) -> str:
        return CONTEXT_DIRECTION

    def to_values_json(self) -> dict:
        return {
            "n_sites_used": len(self.sites),
            "n_sites_mapped": self.mapped_site_count,
            "day": None if self.day is None else self.day.isoformat(),
            "excluded": dict(self.excluded),
            "statistic": "unweighted mean of per-site percent of median (point network, not a basin mean)",
            "sites": [
                {"triplet": s.triplet, "name": s.name, "elevation_ft": s.elevation_ft,
                 "value": s.value, "median": s.median, "percent_of_median": round(s.percent_of_median, 1)}
                for s in self.sites
            ],
        }

    def label(self, *, element: str) -> str:
        if self.value is None:
            return f"SNOTEL {element}: no usable value ({self.reason})"
        elevations = [int(s.elevation_ft) for s in self.sites if s.elevation_ft is not None]
        span = f"{min(elevations)}–{max(elevations)} ft" if elevations else "elevations unknown"
        return (
            f"SNOTEL {element} percent of median, unweighted mean of {len(self.sites)} point "
            f"site(s) at {span} (NRCS AWDB). A point-network statistic, not a basin mean; "
            "shown as context and never scored as risk."
        )


def daily_value_valid_time(day: date, *, utc_offset_hours: float | None) -> tuple[datetime, tuple[str, ...]]:
    """When a ``periodRef=END`` DAILY value dated ``day`` was actually read.

    AWDB DAILY values are the 00:00 station-local reading, and with ``periodRef=END`` the value
    dated D is the reading taken at 00:00 local on D+1 (DATA_SOURCES S1, "the periodRef
    pitfall"). SNOTEL runs on standard time year-round (``dataTimeZone`` −8 for Washington, no
    DST), so the offset comes from the station record rather than a timezone database. When the
    station does not carry one the UTC boundary is used and the caller is told with a flag.
    """
    end_of_day = day + timedelta(days=1)
    midnight = datetime(end_of_day.year, end_of_day.month, end_of_day.day, tzinfo=UTC)
    if utc_offset_hours is None:
        return midnight, ("day_boundary_assumed_utc",)
    return midnight - timedelta(hours=utc_offset_hours), ()


def map_stations_to_basins(
    stations: Iterable[AwdbStation],
    basin_huc8: Mapping[str, Sequence[str]],
) -> dict[str, tuple[AwdbStation, ...]]:
    """Assign each station to a basin by its OWN HUC8 prefix against the seeded basin HUC8 list.

    No hardcoded site list: NRCS says which HUC a pillow sits in and the seed says which HUC8s a
    basin is made of. A station whose HUC matches no seeded basin is simply unmapped.

    Known caveat kept visible rather than patched: site 515 (Harts Pass) is filed under Upper
    Skagit 17110005 but its ``associatedHucs`` are all Methow/Pasayten and it sits on the crest
    (DATA_SOURCES S1). It therefore maps to the Skagit here; the per-site list in
    ``values_json`` is what makes that inspectable.
    """
    lookup: dict[str, str] = {}
    for basin_id, hucs in basin_huc8.items():
        for huc in hucs:
            lookup[str(huc)[:8]] = basin_id
    out: dict[str, list[AwdbStation]] = {basin_id: [] for basin_id in basin_huc8}
    for station in stations:
        basin_id = lookup.get(station.huc8 or "")
        if basin_id is not None:
            out[basin_id].append(station)
    return {basin_id: tuple(sorted(sites, key=lambda s: s.triplet)) for basin_id, sites in out.items()}


def _series_for(series: Iterable[AwdbSeries], *, triplet: str, element: str) -> AwdbSeries | None:
    for s in series:
        if s.triplet == triplet and s.element_code == element and s.height_depth is None:
            return s
    return None


def _value_on(series: AwdbSeries, day: date):
    for v in series.values:
        if v.day == day:
            return v
    return None


def latest_common_day(series: Iterable[AwdbSeries], *, element: str) -> date | None:
    """The most recent day for which ANY mapped site reports the element (with a value)."""
    days = [v.day for s in series if s.element_code == element for v in s.values if v.value is not None]
    return max(days) if days else None


def swe_percent_of_median(
    series: Iterable[AwdbSeries],
    sites: Sequence[AwdbStation],
    *,
    day: date | None,
) -> ContextResult:
    series = tuple(series)
    excluded = {"no_series": 0, "no_value_on_day": 0, "median_absent": 0, "median_zero": 0, "suspect_flag": 0}
    contributions: list[SiteContribution] = []
    if day is None:
        return ContextResult(SWE_FEATURE, SWE_METHOD_ID, None, "pct", None, (), excluded,
                             "No SNOTEL snow-water-equivalent value was reported for any mapped site in the requested window",
                             len(sites))
    for station in sites:
        s = _series_for(series, triplet=station.triplet, element="WTEQ")
        if s is None:
            excluded["no_series"] += 1
            continue
        v = _value_on(s, day)
        if v is None or v.value is None:
            excluded["no_value_on_day"] += 1
            continue
        if v.qc_flag in SUSPECT_QC_FLAGS:
            excluded["suspect_flag"] += 1
            continue
        if v.median is None:
            excluded["median_absent"] += 1
            continue
        if v.median <= 0:
            excluded["median_zero"] += 1
            continue
        contributions.append(
            SiteContribution(station.triplet, station.name, station.elevation_ft, v.value, v.median, 100.0 * v.value / v.median)
        )
    if not contributions:
        reason = (
            f"No mapped SNOTEL site has a non-zero median snow-water equivalent for {day.isoformat()} "
            f"({excluded['median_zero']} site(s) report a median of 0.0, {excluded['median_absent']} report none), "
            "so percent of median is undefined"
        )
        return ContextResult(SWE_FEATURE, SWE_METHOD_ID, None, "pct", day, (), excluded, reason, len(sites))
    mean = sum(c.percent_of_median for c in contributions) / len(contributions)
    return ContextResult(SWE_FEATURE, SWE_METHOD_ID, round(mean, 1), "pct", day, tuple(contributions), excluded, None, len(sites))


def precip_14d_percent_of_median(
    series: Iterable[AwdbSeries],
    sites: Sequence[AwdbStation],
    *,
    day: date | None,
    window_days: int = PRECIP_WINDOW_DAYS,
) -> ContextResult:
    series = tuple(series)
    excluded = {"no_series": 0, "no_value_on_day": 0, "no_value_at_window_start": 0,
                "median_absent": 0, "median_increment_zero": 0, "water_year_rollover": 0, "suspect_flag": 0}
    contributions: list[SiteContribution] = []
    if day is None:
        return ContextResult(PRECIP_FEATURE, PRECIP_METHOD_ID, None, "pct", None, (), excluded,
                             "No SNOTEL precipitation value was reported for any mapped site in the requested window",
                             len(sites))
    start = day - timedelta(days=window_days)
    for station in sites:
        s = _series_for(series, triplet=station.triplet, element="PREC")
        if s is None:
            excluded["no_series"] += 1
            continue
        now, then = _value_on(s, day), _value_on(s, start)
        if now is None or now.value is None:
            excluded["no_value_on_day"] += 1
            continue
        if then is None or then.value is None:
            excluded["no_value_at_window_start"] += 1
            continue
        if now.qc_flag in SUSPECT_QC_FLAGS or then.qc_flag in SUSPECT_QC_FLAGS:
            excluded["suspect_flag"] += 1
            continue
        if now.median is None or then.median is None:
            excluded["median_absent"] += 1
            continue
        amount = now.value - then.value
        reference = now.median - then.median
        if amount < 0 or reference < 0:
            # PREC is a water-year accumulation; a decrease means the year reset inside the
            # window, so the difference is not a 14-day amount at all.
            excluded["water_year_rollover"] += 1
            continue
        if reference <= 0:
            excluded["median_increment_zero"] += 1
            continue
        contributions.append(
            SiteContribution(station.triplet, station.name, station.elevation_ft, amount, reference, 100.0 * amount / reference)
        )
    if not contributions:
        reason = (
            f"No mapped SNOTEL site has a usable {window_days}-day accumulated-precipitation increment "
            f"ending {day.isoformat()} (the median increment is zero or the water year rolled over inside the window)"
        )
        return ContextResult(PRECIP_FEATURE, PRECIP_METHOD_ID, None, "pct", day, (), excluded, reason, len(sites))
    mean = sum(c.percent_of_median for c in contributions) / len(contributions)
    return ContextResult(PRECIP_FEATURE, PRECIP_METHOD_ID, round(mean, 1), "pct", day, tuple(contributions), excluded, None, len(sites))
