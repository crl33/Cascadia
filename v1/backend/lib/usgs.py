"""USGS Water Services adapter (async, httpx).

Returns normalized ParameterSeries for instantaneous values + 24h time series.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

import httpx

from .types import ParameterSeries, TimePoint

log = logging.getLogger(__name__)

USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"
USER_AGENT = "CascadeOracle/0.1 (research)"
HTTP_TIMEOUT = 12.0

PARAM_GAGE_HEIGHT = "00065"
PARAM_DISCHARGE = "00060"
DEFAULT_HISTORY_HOURS = 24
NO_DATA_SENTINEL = -999998  # USGS returns -999999 for missing


def _empty_series(code: str, label: str, unit: str, note: str) -> ParameterSeries:
    return ParameterSeries(
        code=code, label=label, unit=unit,
        latest=None, latest_at=None, series=[],
        available=False, note=note,
    )


async def fetch_usgs_iv(client: httpx.AsyncClient, site: str, hours: int = DEFAULT_HISTORY_HOURS) -> Dict[str, ParameterSeries]:
    """Fetch instantaneous values for both 00065 and 00060 over last `hours` hours."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    params = {
        "format": "json",
        "sites": site,
        "parameterCd": f"{PARAM_GAGE_HEIGHT},{PARAM_DISCHARGE}",
        "startDT": start.strftime("%Y-%m-%dT%H:%MZ"),
        "endDT": end.strftime("%Y-%m-%dT%H:%MZ"),
        "siteStatus": "all",
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    out: Dict[str, ParameterSeries] = {
        PARAM_GAGE_HEIGHT: _empty_series(PARAM_GAGE_HEIGHT, "Gage height", "ft", "No data returned"),
        PARAM_DISCHARGE: _empty_series(PARAM_DISCHARGE, "Discharge", "cfs", "No data returned"),
    }

    try:
        r = await client.get(USGS_IV_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        msg = f"USGS request failed: {e}"
        log.warning("%s site=%s", msg, site)
        for ps in out.values():
            ps.note = msg
        return out

    ts_list = (payload.get("value", {}).get("timeSeries", []) or [])
    if not ts_list:
        return out

    for ts in ts_list:
        var = ts.get("variable", {}) or {}
        codes = var.get("variableCode", []) or []
        code = codes[0].get("value") if codes else None
        if code not in out:
            continue
        unit = (var.get("unit", {}) or {}).get("unitCode") or out[code].unit
        label_raw = var.get("variableName") or out[code].label
        label = label_raw.split(",")[0].strip() if "," in label_raw else label_raw
        # Normalize common labels
        if code == PARAM_DISCHARGE:
            label = "Discharge"
            unit = "cfs" if unit in ("ft3/s", "cfs") else unit
        if code == PARAM_GAGE_HEIGHT:
            label = "Gage height"

        values_blocks = ts.get("values", []) or []
        points: list[TimePoint] = []
        latest: tuple[str, float] | None = None
        for block in values_blocks:
            for v in block.get("value", []) or []:
                raw = v.get("value")
                ttxt = v.get("dateTime")
                try:
                    fv = float(raw)
                except (TypeError, ValueError):
                    continue
                if fv <= NO_DATA_SENTINEL:
                    continue
                if not ttxt:
                    continue
                points.append(TimePoint(t=ttxt, v=fv))
                if latest is None or ttxt > latest[0]:
                    latest = (ttxt, fv)
        points.sort(key=lambda p: p.t)

        ps = out[code]
        ps.unit = unit
        ps.label = label
        ps.series = points
        if latest:
            ps.latest = latest[1]
            ps.latest_at = latest[0]
            ps.available = True
            ps.note = None
        else:
            ps.available = False
            ps.note = "Empty time series"

    return out
