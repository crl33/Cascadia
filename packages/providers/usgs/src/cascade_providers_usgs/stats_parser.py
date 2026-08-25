"""Strict parsers for the three day-of-year statistics payloads susceptibility v0 reads.

1. ``parse_daily_csv``  — USGS OGC API ``daily`` in CSV. One request returns a station's ENTIRE
   daily-mean record (31,373 rows / 903 KB for the Skagit), which is what lets the platform
   build its own climatology instead of depending on a service that decommissions in Q1 2027
   (p3-surfaces-design §2.1). **The rows are NOT time-ordered** — verified live 2026-08-24, the
   first three rows were 2014, 2019, 2016 — so nothing here may assume order.
2. ``parse_latest_daily_json`` — OGC ``latest-daily`` GeoJSON: the previous complete daily mean
   per site, with its ``approval_status``.
3. ``parse_nwis_stat_rdb`` — the LEGACY ``nwis/stat`` day-of-year table. This is the
   CROSS-CHECK and never a dependency (design §2.2 step 2).

Values stay strings until the number/flag decision, exactly like parser.py and ogc_parser.py.
A daily mean is labeled by a DATE, not an instant: the parsers keep ``datetime.date`` and refuse
to invent a time of day. Turning that date into a knowledge-time instant needs the station's
day boundary and happens in climatology.daily_mean_valid_time (DATA_DOCTRINE §3).
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import date

from cascade_providers_usgs.parser import ParseError

DISCHARGE_CODE = "00060"
DAILY_MEAN_STATISTIC = "00003"
# nwis/stat spells its percentile columns pNN_va; these are the seven the ladder carries.
RDB_PERCENTILE_COLUMNS = {"p05_va": 5, "p10_va": 10, "p25_va": 25, "p50_va": 50, "p75_va": 75, "p90_va": 90, "p95_va": 95}


@dataclass(frozen=True)
class DailyMean:
    """One published daily-mean discharge value, labeled by its (station-local) calendar date."""

    site: str  # bare site number
    day: date
    raw_value: str | None  # None when the API serves null / an empty cell
    approval_status: str | None  # verbatim: "Approved" | "Provisional" | ...
    unit: str | None  # verbatim provider spelling when present ("ft^3/s"); None in the CSV form


@dataclass(frozen=True)
class PublishedDoyStat:
    """One (month, day) row of the USGS published daily-statistics table."""

    site: str
    month: int
    day: int
    begin_year: int | None
    end_year: int | None
    count: int | None
    percentiles: dict[int, float]  # {5: 7410.0, 10: 8650.0, ...}; only columns that carried a number


def _req(obj: dict, key: str, ctx: str):
    if not isinstance(obj, dict) or key not in obj:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def _day(raw: str, ctx: str) -> date:
    try:
        return date.fromisoformat(raw.strip())
    except (AttributeError, ValueError) as e:
        raise ParseError(f"{ctx}: not an ISO date: {raw!r}") from e


def parse_daily_csv(content: bytes, *, site: str) -> tuple[DailyMean, ...]:
    """Parse the OGC ``daily`` CSV export. Returns rows sorted by date (the payload is not).

    ``site`` is the site the request was made for: with ``properties=time,value,approval_status``
    the CSV does not name its own station. When a ``monitoring_location_id`` column IS present
    it is cross-checked against ``site`` and a mismatch is a ParseError, never a silent merge.
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ParseError(f"not UTF-8 CSV: {e}") from e
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ParseError("empty CSV: no header row")
    for column in ("time", "value", "approval_status"):
        if column not in reader.fieldnames:
            raise ParseError(f"missing required column {column!r}; got {reader.fieldnames}")
    out: list[DailyMean] = []
    for i, row in enumerate(reader):
        ctx = f"row {i + 2}"
        loc = (row.get("monitoring_location_id") or "").strip()
        if loc and loc.removeprefix("USGS-") != site:
            raise ParseError(f"{ctx}: row is for {loc!r}, not the requested site {site!r}")
        statistic = (row.get("statistic_id") or "").strip()
        if statistic and statistic != DAILY_MEAN_STATISTIC:
            continue  # a different daily statistic (max/min) is a different product
        raw = row.get("value")
        approval = (row.get("approval_status") or "").strip() or None
        unit = (row.get("unit_of_measure") or "").strip() or None
        out.append(
            DailyMean(
                site=site,
                day=_day(row["time"], ctx),
                raw_value=None if raw is None or raw.strip() == "" else raw.strip(),
                approval_status=approval,
                unit=unit,
            )
        )
    out.sort(key=lambda r: r.day)
    return tuple(out)


def parse_latest_daily_json(content: bytes) -> tuple[DailyMean, ...]:
    """Parse the OGC ``latest-daily`` FeatureCollection (one feature per site/parameter)."""
    try:
        doc = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    features = _req(doc, "features", "document")
    if not isinstance(features, list):
        raise ParseError("features is not a list")
    out: list[DailyMean] = []
    for i, feature in enumerate(features):
        ctx = f"features[{i}]"
        props = _req(feature, "properties", ctx)
        if str(_req(props, "parameter_code", ctx)) != DISCHARGE_CODE:
            continue
        if str(props.get("statistic_id", DAILY_MEAN_STATISTIC)) != DAILY_MEAN_STATISTIC:
            continue  # daily max/min are a different product, never a stand-in for the mean
        raw = _req(props, "value", ctx)  # key must exist; null is a legal value
        approval = _req(props, "approval_status", ctx)
        out.append(
            DailyMean(
                site=str(_req(props, "monitoring_location_id", ctx)).removeprefix("USGS-"),
                day=_day(str(_req(props, "time", ctx)), ctx),
                raw_value=None if raw is None else str(raw),
                approval_status=None if approval is None else str(approval),
                unit=None if props.get("unit_of_measure") is None else str(props["unit_of_measure"]),
            )
        )
    out.sort(key=lambda r: (r.site, r.day))
    return tuple(out)


def parse_nwis_stat_rdb(content: bytes) -> tuple[PublishedDoyStat, ...]:
    """Parse the legacy ``nwis/stat`` RDB day-of-year table (tab-separated, '#' comments).

    RDB layout: comment lines, one header line, one column-format line ('5s', '3n', ...), then
    data. Only the seven percentile columns the ladder uses are read; a column that carries no
    number is simply absent from ``percentiles`` rather than becoming a zero.
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ParseError(f"not UTF-8 RDB: {e}") from e
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    if len(lines) < 3:
        raise ParseError("RDB has no header, format line and data")
    header = lines[0].split("\t")
    for column in ("site_no", "month_nu", "day_nu", "p50_va"):
        if column not in header:
            raise ParseError(f"missing required RDB column {column!r}")
    out: list[PublishedDoyStat] = []
    for i, line in enumerate(lines[2:]):  # lines[1] is the RDB column-format line
        ctx = f"data row {i + 1}"
        row = dict(zip(header, line.split("\t"), strict=False))
        try:
            month, day = int(row["month_nu"]), int(row["day_nu"])
        except (KeyError, ValueError) as e:
            raise ParseError(f"{ctx}: month_nu/day_nu not integers: {line!r}") from e
        if not (1 <= month <= 12 and 1 <= day <= 31):
            raise ParseError(f"{ctx}: month {month} day {day} is not a calendar day")
        percentiles: dict[int, float] = {}
        for column, p in RDB_PERCENTILE_COLUMNS.items():
            raw = (row.get(column) or "").strip()
            if raw:
                try:
                    percentiles[p] = float(raw)
                except ValueError:
                    continue  # a non-numeric statistic cell is absent, never zero
        out.append(
            PublishedDoyStat(
                site=row.get("site_no", "").strip(),
                month=month,
                day=day,
                begin_year=_int_or_none(row.get("begin_yr")),
                end_year=_int_or_none(row.get("end_yr")),
                count=_int_or_none(row.get("count_nu")),
                percentiles=percentiles,
            )
        )
    return tuple(out)


def _int_or_none(raw: str | None) -> int | None:
    try:
        return int((raw or "").strip())
    except ValueError:
        return None
