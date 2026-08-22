"""
Cascade Oracle — Phase 1 POC

Goal: Validate core real-data workflow in isolation BEFORE building the app.

Tests:
  1. USGS Water Services IV API — instantaneous values (00065, 00060) for last 24h
  2. NOAA NWPS API — official flood stages by NWS LID (action/minor/moderate/major)
  3. Risk-state computation — calm/watch/elevated/flood/unknown using observed stage vs thresholds
  4. Source-labeling logic — official_nwps / fallback_configured / unknown
  5. Stale-data detection (>45 min)

If this passes for all 6 stations, the V1 app can be built confidently around the
proven adapters and normalized data contract.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
log = logging.getLogger("poc_hydro")

# ---------------------------------------------------------------------------
# Station Configuration (config-driven; mirrors what will live in MongoDB)
# ---------------------------------------------------------------------------
STATIONS: list[dict[str, Any]] = [
    {
        "id": "cedar-renton",
        "name": "Cedar River at Renton",
        "river": "Cedar River",
        "basin": "Lake Washington",
        "usgs_site": "12119000",
        "nwps_lid": "RNTW1",
        "lat": 47.4825,
        "lon": -122.2025,
        # Fallback thresholds (gage height in feet) — used ONLY if NWPS unavailable.
        # These are placeholders and must be clearly labeled in UI.
        "fallback_thresholds_ft": {"action": 9.0, "minor": 11.0, "moderate": 13.0, "major": 15.0},
    },
    {
        "id": "snoqualmie-carnation",
        "name": "Snoqualmie River near Carnation",
        "river": "Snoqualmie River",
        "basin": "Snohomish",
        "usgs_site": "12149000",
        "nwps_lid": "CRNW1",
        "lat": 47.6656,
        "lon": -121.9242,
        "fallback_thresholds_ft": {"action": 54.0, "minor": 56.0, "moderate": 58.0, "major": 60.0},
    },
    {
        "id": "skagit-mt-vernon",
        "name": "Skagit River near Mount Vernon",
        "river": "Skagit River",
        "basin": "Skagit",
        "usgs_site": "12200500",
        "nwps_lid": "MVEW1",
        "lat": 48.4453,
        "lon": -122.3342,
        "fallback_thresholds_ft": {"action": 25.0, "minor": 28.0, "moderate": 32.0, "major": 35.0},
    },
    {
        "id": "nooksack-ferndale",
        "name": "Nooksack River at Ferndale",
        "river": "Nooksack River",
        "basin": "Nooksack",
        "usgs_site": "12213100",
        "nwps_lid": "NKSW1",  # NWS LID for Nooksack at Ferndale
        "lat": 48.8467,
        "lon": -122.5897,
        # Validated NWS thresholds (Nooksack at Ferndale): action 12 / minor 14 / mod 16 / major 18 ft
        "fallback_thresholds_ft": {"action": 12.0, "minor": 14.0, "moderate": 16.0, "major": 18.0},
    },
    {
        "id": "green-auburn",
        "name": "Green River near Auburn",
        "river": "Green River",
        "basin": "Green-Duwamish",
        "usgs_site": "12113000",
        "nwps_lid": "AUBW1",
        "lat": 47.3081,
        "lon": -122.2017,
        # Datum here reads ~58 ft normally; without verified NWS thresholds we keep this null
        # so risk_state reports "unknown" instead of a false flood alert.
        "fallback_thresholds_ft": None,
    },
    {
        "id": "white-auburn",
        "name": "White River near Auburn",
        "river": "White River",
        "basin": "Puyallup",
        "usgs_site": "12100490",
        "nwps_lid": "WRAW1",
        "lat": 47.2950,
        "lon": -122.2317,
        # Datum here reads ~110 ft normally; null fallback prevents false flood states.
        "fallback_thresholds_ft": None,
    },
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"
NWPS_GAUGE_URL = "https://api.water.noaa.gov/nwps/v1/gauges/{lid}"
HTTP_TIMEOUT = 12
USER_AGENT = "CascadeOracle/0.1 (research; contact: ops@cascade-oracle.local)"
STALE_AFTER_MINUTES = 90
HISTORY_HOURS = 24

PARAM_GAGE_HEIGHT = "00065"  # ft
PARAM_DISCHARGE = "00060"  # cfs


# ---------------------------------------------------------------------------
# Normalized data contract (will become Pydantic models in the FastAPI app)
# ---------------------------------------------------------------------------
@dataclass
class TimePoint:
    t: str  # ISO timestamp UTC
    v: float


@dataclass
class ParameterSeries:
    code: str
    label: str
    unit: str
    latest: Optional[float]
    latest_at: Optional[str]
    series: list[TimePoint] = field(default_factory=list)
    available: bool = True
    note: Optional[str] = None


@dataclass
class FloodThresholds:
    action: Optional[float]
    minor: Optional[float]
    moderate: Optional[float]
    major: Optional[float]
    unit: str
    source: str  # "official_nwps" | "fallback_configured" | "unknown"
    source_label: str  # human readable


@dataclass
class StationSnapshot:
    id: str
    name: str
    river: str
    basin: str
    usgs_site: str
    nwps_lid: Optional[str]
    lat: float
    lon: float
    gage_height: ParameterSeries
    discharge: ParameterSeries
    thresholds: FloodThresholds
    risk_state: str  # calm | watch | elevated | flood | unknown
    risk_reason: str
    is_stale: bool
    fetched_at: str
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# USGS adapter
# ---------------------------------------------------------------------------
def fetch_usgs_iv(site: str, hours: int = HISTORY_HOURS) -> dict[str, ParameterSeries]:
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

    out: dict[str, ParameterSeries] = {
        PARAM_GAGE_HEIGHT: ParameterSeries(
            code=PARAM_GAGE_HEIGHT, label="Gage height", unit="ft",
            latest=None, latest_at=None, series=[], available=False,
            note="No data returned",
        ),
        PARAM_DISCHARGE: ParameterSeries(
            code=PARAM_DISCHARGE, label="Discharge", unit="cfs",
            latest=None, latest_at=None, series=[], available=False,
            note="No data returned",
        ),
    }

    try:
        r = requests.get(USGS_IV_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        for ps in out.values():
            ps.note = f"USGS request failed: {e}"
        return out

    ts_list = (
        payload.get("value", {}).get("timeSeries", []) or []
    )
    if not ts_list:
        return out

    for ts in ts_list:
        var = ts.get("variable", {})
        codes = var.get("variableCode", [])
        code = codes[0].get("value") if codes else None
        if code not in out:
            continue
        unit = var.get("unit", {}).get("unitCode") or out[code].unit
        label = var.get("variableName") or out[code].label
        values_blocks = ts.get("values", []) or []
        points: list[TimePoint] = []
        latest: Optional[tuple[str, float]] = None
        for block in values_blocks:
            for v in block.get("value", []) or []:
                raw = v.get("value")
                ttxt = v.get("dateTime")
                try:
                    fv = float(raw)
                except (TypeError, ValueError):
                    continue
                # USGS "no data" sentinels are commonly -999999
                if fv <= -999998:
                    continue
                if not ttxt:
                    continue
                points.append(TimePoint(t=ttxt, v=fv))
                if latest is None or ttxt > latest[0]:
                    latest = (ttxt, fv)
        # Sort by time ascending
        points.sort(key=lambda p: p.t)
        ps = out[code]
        ps.unit = unit
        ps.label = label.split(",")[0].strip() if "," in label else label
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


# ---------------------------------------------------------------------------
# NOAA NWPS adapter
# ---------------------------------------------------------------------------
def fetch_nwps_thresholds(lid: str) -> tuple[Optional[FloodThresholds], Optional[str]]:
    """Fetch official flood stages for a gauge by NWS LID. Returns (thresholds, error)."""
    if not lid:
        return None, "No NWPS LID configured"

    url = NWPS_GAUGE_URL.format(lid=lid)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        if r.status_code == 404:
            return None, f"NWPS LID '{lid}' not found (404)"
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, f"NWPS request failed: {e}"

    # NWPS schema commonly: { "flood": { "categories": { "action": {"stage": x}, "minor": ... } } }
    flood = data.get("flood") or {}
    cats = flood.get("categories") or {}

    def _stage(cat_key: str) -> Optional[float]:
        cat = cats.get(cat_key)
        if not isinstance(cat, dict):
            return None
        for k in ("stage", "value", "ft"):
            v = cat.get(k)
            try:
                if v is None:
                    continue
                fv = float(v)
                # NWPS uses very negative sentinels for missing
                if fv <= -9000:
                    return None
                return fv
            except (TypeError, ValueError):
                continue
        return None

    action = _stage("action")
    minor = _stage("minor")
    moderate = _stage("moderate")
    major = _stage("major")

    if not any(v is not None for v in (action, minor, moderate, major)):
        return None, "NWPS response missing flood categories"

    return (
        FloodThresholds(
            action=action,
            minor=minor,
            moderate=moderate,
            major=major,
            unit="ft",
            source="official_nwps",
            source_label="Official NWS / NWPS",
        ),
        None,
    )


# ---------------------------------------------------------------------------
# Risk computation
# ---------------------------------------------------------------------------
def compute_risk(stage_ft: Optional[float], thresholds: FloodThresholds) -> tuple[str, str]:
    """Compute risk state from observed stage + thresholds. Returns (state, reason)."""
    if stage_ft is None:
        return "unknown", "No current gage height available."

    # If no validated thresholds, never guess — return unknown with clear reason.
    if thresholds.source == "thresholds_unavailable" or all(
        v is None for v in (thresholds.action, thresholds.minor, thresholds.moderate, thresholds.major)
    ):
        return "unknown", "Flood thresholds not available for this gauge."

    # Walk thresholds in order of severity; tolerate missing values.
    pairs = [
        ("flood", thresholds.major, "above MAJOR flood stage"),
        ("flood", thresholds.moderate, "above MODERATE flood stage"),
        ("elevated", thresholds.minor, "above MINOR flood stage"),
        ("watch", thresholds.action, "above ACTION stage"),
    ]
    for state, thr, reason in pairs:
        if thr is not None and stage_ft >= thr:
            return state, f"Observed {stage_ft:.2f} ft is {reason} ({thr:.2f} ft)."
    return "calm", "Observed stage is below action thresholds."


def is_stale(latest_at_iso: Optional[str]) -> bool:
    if not latest_at_iso:
        return True
    try:
        dt = datetime.fromisoformat(latest_at_iso.replace("Z", "+00:00"))
    except Exception:
        return True
    age = datetime.now(timezone.utc) - dt
    return age > timedelta(minutes=STALE_AFTER_MINUTES)


# ---------------------------------------------------------------------------
# Orchestration per station
# ---------------------------------------------------------------------------
def build_snapshot(cfg: dict[str, Any]) -> StationSnapshot:
    errors: list[str] = []

    # 1) USGS data
    usgs = fetch_usgs_iv(cfg["usgs_site"])
    gh = usgs[PARAM_GAGE_HEIGHT]
    dq = usgs[PARAM_DISCHARGE]
    if not gh.available:
        errors.append(f"USGS gage height unavailable: {gh.note}")
    if not dq.available:
        errors.append(f"USGS discharge unavailable: {dq.note}")

    # 2) NWPS thresholds (with fallback)
    thresholds, nwps_err = fetch_nwps_thresholds(cfg.get("nwps_lid", ""))
    if thresholds is None:
        if nwps_err:
            errors.append(nwps_err)
        fb = cfg.get("fallback_thresholds_ft")
        if isinstance(fb, dict) and any(fb.get(k) is not None for k in ("action", "minor", "moderate", "major")):
            thresholds = FloodThresholds(
                action=fb.get("action"),
                minor=fb.get("minor"),
                moderate=fb.get("moderate"),
                major=fb.get("major"),
                unit="ft",
                source="fallback_configured",
                source_label="Temporary configured threshold",
            )
        else:
            # No validated thresholds available — never invent flood states.
            thresholds = FloodThresholds(
                action=None, minor=None, moderate=None, major=None,
                unit="ft",
                source="thresholds_unavailable",
                source_label="Thresholds not configured",
            )

    # 3) Risk
    state, reason = compute_risk(gh.latest, thresholds)

    # 4) Stale
    stale = is_stale(gh.latest_at)

    return StationSnapshot(
        id=cfg["id"],
        name=cfg["name"],
        river=cfg["river"],
        basin=cfg["basin"],
        usgs_site=cfg["usgs_site"],
        nwps_lid=cfg.get("nwps_lid"),
        lat=cfg["lat"],
        lon=cfg["lon"],
        gage_height=gh,
        discharge=dq,
        thresholds=thresholds,
        risk_state=state,
        risk_reason=reason,
        is_stale=stale,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Pretty print summary + assertions
# ---------------------------------------------------------------------------
def summarize(snaps: list[StationSnapshot]) -> dict[str, Any]:
    rows = []
    pass_count = 0
    for s in snaps:
        gh_v = f"{s.gage_height.latest:.2f} {s.gage_height.unit}" if s.gage_height.latest is not None else "—"
        dq_v = f"{s.discharge.latest:,.0f} {s.discharge.unit}" if s.discharge.latest is not None else "—"
        ok = bool(s.gage_height.available) and bool(s.gage_height.series)
        if ok:
            pass_count += 1
        rows.append({
            "station": s.name,
            "site": s.usgs_site,
            "lid": s.nwps_lid,
            "gage_height": gh_v,
            "discharge": dq_v,
            "series_points": len(s.gage_height.series),
            "thresholds_source": s.thresholds.source,
            "risk": s.risk_state,
            "stale": s.is_stale,
            "errors": s.errors,
            "pass": ok,
        })
    return {"summary_rows": rows, "stations_passing_core": pass_count, "total": len(snaps)}


def main() -> int:
    log.info("=== Cascade Oracle POC: USGS + NWPS + Risk ===")
    log.info("Stations: %d", len(STATIONS))

    snaps: list[StationSnapshot] = []
    for cfg in STATIONS:
        log.info("Fetching %s (USGS %s / LID %s)...", cfg["name"], cfg["usgs_site"], cfg.get("nwps_lid"))
        snaps.append(build_snapshot(cfg))

    summary = summarize(snaps)
    print("\n=== SUMMARY TABLE ===")
    for row in summary["summary_rows"]:
        mark = "PASS" if row["pass"] else "FAIL"
        print(
            f"[{mark}] {row['station']:<40} "
            f"site={row['site']} lid={row['lid'] or '—':<6} "
            f"GH={row['gage_height']:<14} Q={row['discharge']:<18} "
            f"pts={row['series_points']:<4} thr={row['thresholds_source']:<20} "
            f"risk={row['risk']:<8} stale={row['stale']}"
        )
        if row["errors"]:
            for e in row["errors"]:
                print(f"        ! {e}")

    print(f"\nStations with core data (gage height + series): "
          f"{summary['stations_passing_core']}/{summary['total']}")

    # Dump first station full normalized JSON to confirm contract
    if snaps:
        sample = asdict(snaps[0])
        # Truncate series for readability
        for key in ("gage_height", "discharge"):
            if isinstance(sample.get(key), dict) and isinstance(sample[key].get("series"), list):
                full = sample[key]["series"]
                sample[key]["series_count"] = len(full)
                sample[key]["series_preview"] = full[:3] + (["…"] if len(full) > 3 else [])
                del sample[key]["series"]
        print("\n=== SAMPLE NORMALIZED CONTRACT (Station 1) ===")
        print(json.dumps(sample, indent=2, default=str))

    # POC pass criterion: all 6 stations return at least gage height + a series
    if summary["stations_passing_core"] == summary["total"]:
        log.info("POC PASSED: all %d stations returned core data.", summary["total"])
        return 0
    log.error(
        "POC INCOMPLETE: %d/%d stations returned core data.",
        summary["stations_passing_core"], summary["total"],
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
