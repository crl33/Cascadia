"""Measure the candidate trend estimators against real Event Zero hydrographs.

Produces the evidence behind `docs/research/trend-estimator-selection-2026-08-27.md`.
`packages/hydrology/src/cascade_hydrology/trend.py` holds the estimators — as
`trend_candidates.py` when this script was written, folded into `trend.py` when
`method:rate-of-rise@2.0.0` shipped. This script only measures them, so the two cannot drift
apart, and it measures the SHIPPED code rather than a copy of it.

Run:  CASCADE_DB_URL=<direct url> python scripts/measure_trend_estimators.py [--cache PATH]

Four questions, each answered on the 15-minute observations already in the database for
2025-12-01 .. 2025-12-22 at the seven seeded gauges:

  A. JITTER      how much does the reported rate move between consecutive 15-minute updates?
  B. ROBUSTNESS  how far does an injected telemetry fault move the answer?
  C. TIMING      when does each estimator first report a SUSTAINED rise, and how often does it
                 report one that the hydrograph does not justify?
  D. TIDE        does any estimator remove an injected semidiurnal signal?

No estimator is tuned here and no threshold is fitted. B and D inject faults into real data;
A and C use the record exactly as observed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages/hydrology/src"))

from cascade_hydrology.trend import (  # noqa: E402
    endpoint_slope,
    ols_slope,
    repeated_median_slope,
    steady_epsilon,
    theil_sen_slope,
)

ESTIMATORS = {
    "endpoint": endpoint_slope,       # the shipped estimator, the thing being replaced
    "ols": ols_slope,
    "theil_sen": theil_sen_slope,
    "repeated_median": repeated_median_slope,
}

STATIONS = [
    "station:usgs:12100490", "station:usgs:12113000", "station:usgs:12119000",
    "station:usgs:12149000", "station:usgs:12189500", "station:usgs:12200500",
    "station:usgs:12213100",
]
START = datetime(2025, 12, 1, tzinfo=timezone.utc)
END = datetime(2025, 12, 23, tzinfo=timezone.utc)
WINDOW_H = 6.0
CADENCE_MIN = 15
MIN_SAMPLES = 3
#: A rise has to hold this long before it counts as a detection in C. Two hours = 8 updates at
#: the 15-minute cadence. Chosen to exclude single-update blips, NOT fitted to the outcome.
SUSTAIN_H = 2.0


async def fetch(url: str) -> dict:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url.replace("postgresql://", "postgresql+psycopg://"))
    out: dict[str, dict[str, list]] = {}
    async with engine.connect() as conn:
        for station in STATIONS:
            out[station] = {}
            for basis in ("stage", "flow"):
                rows = (await conn.execute(sa.text(
                    "SELECT valid_time, value FROM observation "
                    "WHERE station_id=:s AND variable=:v AND valid_time>=:a AND valid_time<:b "
                    "ORDER BY valid_time"
                ), {"s": station, "v": basis, "a": START, "b": END})).all()
                out[station][basis] = [[r[0].isoformat(), float(r[1])] for r in rows if r[1] is not None]
    await engine.dispose()
    return out


def windows(series: list[tuple[datetime, float]]):
    """Every trailing 6 h window that meets the shipped admissibility rules, in order."""
    span = timedelta(hours=WINDOW_H)
    for i in range(len(series)):
        end_t = series[i][0]
        lo = end_t - span
        j = i
        while j > 0 and series[j - 1][0] >= lo:
            j -= 1
        pts = series[j:i + 1]
        if len(pts) < MIN_SAMPLES:
            continue
        gaps = [(b[0] - a[0]).total_seconds() / 3600 for a, b in zip(pts, pts[1:])]
        if max(gaps) > 2.0 or (pts[-1][0] - pts[0][0]).total_seconds() / 3600 < 0.5 * WINDOW_H:
            continue
        t0 = pts[0][0]
        xs = [(t - t0).total_seconds() / 3600 for t, _ in pts]
        ys = [v for _, v in pts]
        yield end_t, xs, ys


def direction(slope: float, basis: str, last: float) -> str:
    eps = steady_epsilon(basis, last)
    return "steady" if abs(slope) <= eps else ("rising" if slope > 0 else "falling")


def run_a_jitter(data, basis):
    """Median |Δslope| between consecutive updates, and the count of direction changes."""
    res = {n: {"steps": [], "flips": 0, "n": 0} for n in ESTIMATORS}
    for station, series in data.items():
        prev = {}
        for end_t, xs, ys in windows(series[basis]):
            for name, fn in ESTIMATORS.items():
                s = fn(xs, ys)
                d = direction(s, basis, ys[-1])
                r = res[name]
                r["n"] += 1
                ps, pd = prev.get(name, (None, None))
                if ps is not None:
                    # normalised by the window's own scale so gauges are comparable
                    scale = max(abs(ys[-1]), 1e-9)
                    r["steps"].append(abs(s - ps) / scale)
                    if d != pd and "steady" not in (d, pd):
                        r["flips"] += 1
                prev[name] = (s, d)
    return {
        n: {
            "median_relative_step": statistics.median(v["steps"]) if v["steps"] else None,
            "p95_relative_step": (sorted(v["steps"])[int(0.95 * (len(v["steps"]) - 1))] if v["steps"] else None),
            "hard_direction_flips": v["flips"],
            "windows": v["n"],
        }
        for n, v in res.items()
    }


def _corrupt(ys, mode):
    y = list(ys)
    n = len(y)
    if mode == "spike":            # one bad reading, the classic isolated outlier
        y[n // 2] = y[n // 2] * 1.5 + 1.0
    elif mode == "held_run":       # frozen datalogger: the last 25 % repeat one value
        k = max(2, n // 4)
        y[n - k:] = [y[n - k]] * k
    elif mode == "held_run_long":  # a longer freeze, 40 % of the window
        k = max(2, int(0.4 * n))
        y[n - k:] = [y[n - k]] * k
    elif mode == "two_spikes":     # two bad readings, still under the Theil-Sen breakdown point
        y[n // 3] = y[n // 3] * 1.4 + 1.0
        y[2 * n // 3] = y[2 * n // 3] * 0.6
    elif mode == "spike_last":     # a bad FINAL reading — the endpoint estimator's worst case
        y[-1] = y[-1] * 1.5 + 1.0
    elif mode == "spike_first":    # a bad FIRST reading — the other endpoint
        y[0] = y[0] * 1.5 + 1.0
    return y


def run_b_robustness(data, basis):
    """|corrupted - clean| / |clean| per estimator per fault, over every admissible window."""
    modes = ("spike", "spike_first", "spike_last", "two_spikes", "held_run", "held_run_long")
    acc = {n: {m: [] for m in modes} for n in ESTIMATORS}
    # Relative error is unstable when the clean slope is near zero, which is most of a 22-day
    # record. `eps_err` is the same displacement measured in STEADY epsilons: an error below 1.0
    # cannot change the reported direction, so it says whether the fault matters operationally.
    eps_err = {n: {m: [] for m in modes} for n in ESTIMATORS}
    sign_flips = {n: {m: 0 for m in modes} for n in ESTIMATORS}
    dir_changes = {n: {m: 0 for m in modes} for n in ESTIMATORS}
    for _station, series in data.items():
        for _end_t, xs, ys in windows(series[basis]):
            clean = {n: fn(xs, ys) for n, fn in ESTIMATORS.items()}
            eps = steady_epsilon(basis, ys[-1])
            for m in modes:
                yc = _corrupt(ys, m)
                for n, fn in ESTIMATORS.items():
                    got = fn(xs, yc)
                    base = abs(clean[n])
                    if base > 1e-9:
                        acc[n][m].append(abs(got - clean[n]) / base)
                    eps_err[n][m].append(abs(got - clean[n]) / eps)
                    if clean[n] * got < 0:
                        sign_flips[n][m] += 1
                    # the direction is decided against the CLEAN last value in both cases, so a
                    # change here is the fault changing what the surface would say, not a
                    # side effect of the epsilon moving
                    if direction(got, basis, ys[-1]) != direction(clean[n], basis, ys[-1]):
                        dir_changes[n][m] += 1
    def q(vals, p):
        return sorted(vals)[int(p * (len(vals) - 1))] if vals else None
    return {
        n: {
            m: {
                "median_relative_error": statistics.median(acc[n][m]) if acc[n][m] else None,
                "p90_relative_error": q(acc[n][m], 0.90),
                "median_error_in_steady_eps": statistics.median(eps_err[n][m]) if eps_err[n][m] else None,
                "p90_error_in_steady_eps": q(eps_err[n][m], 0.90),
                "sign_reversals": sign_flips[n][m],
                "reported_direction_changed": dir_changes[n][m],
                "windows": len(eps_err[n][m]),
            }
            for m in modes
        }
        for n in ESTIMATORS
    }


def run_c_timing(data, basis):
    """First SUSTAINED rise per station, and sustained rises during the quiescent period.

    `peak_time` is the observed maximum: a fact about the record, not a label anyone assigned.
    A detection is credited only if it precedes that peak. `quiescent` is 12-14 .. 12-22, after
    every gauge has crested; a sustained rise there is counted but NOT called a false positive —
    real secondary rises happened, and this script cannot tell them apart. It reports the count.
    """
    need = int(SUSTAIN_H * 60 / CADENCE_MIN)
    out = {}
    for station, raw in data.items():
        series = raw[basis]
        peak_t = max(series, key=lambda p: p[1])[0]
        rows = list(windows(series))
        per = {}
        for name, fn in ESTIMATORS.items():
            dirs = [(t, direction(fn(xs, ys), basis, ys[-1])) for t, xs, ys in rows]
            first, run = None, 0
            quiescent = 0
            for t, d in dirs:
                run = run + 1 if d == "rising" else 0
                if run == need:
                    if t < peak_t and first is None:
                        first = t - timedelta(hours=SUSTAIN_H)
                    if t >= datetime(2025, 12, 14, tzinfo=timezone.utc):
                        quiescent += 1
            per[name] = {
                "first_sustained_rise": first.isoformat() if first else None,
                "hours_before_peak": round((peak_t - first).total_seconds() / 3600, 2) if first else None,
                "sustained_rise_onsets_after_12_14": quiescent,
            }
        out[station] = {"peak_at": peak_t.isoformat(), "peak_value": max(v for _, v in series), "estimators": per}
    return out


def run_d_tide(data, amplitude_ft=1.0, period_h=12.42):
    """Inject a pure M2 tide onto a real fluvial stage record; report the false rate produced.

    If a robust estimator removed a tide, the reported rate would fall toward the clean value.
    The measurement exists to test that claim, not to assume it.
    """
    station = "station:usgs:12200500"  # Skagit at Mount Vernon: the seeded point nearest tidewater
    series = data[station]["stage"]
    out = {n: [] for n in ESTIMATORS}
    clean_out = {n: [] for n in ESTIMATORS}
    for end_t, xs, ys in windows(series):
        phase = (end_t - START).total_seconds() / 3600
        yt = [y + amplitude_ft * math.sin(2 * math.pi * (phase - (xs[-1] - x)) / period_h) for x, y in zip(xs, ys)]
        for n, fn in ESTIMATORS.items():
            out[n].append(abs(fn(xs, yt)))
            clean_out[n].append(abs(fn(xs, ys)))
    return {
        "station": station, "amplitude_ft": amplitude_ft, "period_h": period_h,
        "steady_epsilon_ft_per_h": steady_epsilon("stage", 0.0),
        "estimators": {
            n: {
                "median_abs_rate_with_tide": round(statistics.median(out[n]), 4),
                "median_abs_rate_clean": round(statistics.median(clean_out[n]), 4),
                "median_inflation": round(statistics.median(out[n]) - statistics.median(clean_out[n]), 4),
            }
            for n in ESTIMATORS
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/trend_estimator_data.json")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cache = Path(args.cache)
    if cache.exists():
        raw = json.loads(cache.read_text())
    else:
        url = os.environ.get("CASCADE_DB_URL")
        if not url:
            print("CASCADE_DB_URL is required when the cache is absent", file=sys.stderr)
            return 2
        raw = asyncio.run(fetch(url))
        cache.write_text(json.dumps(raw))
    # The observation column is timestamp-without-time-zone, so the cache round trip returns
    # naive values. Everything downstream compares against UTC instants; attach it once, here,
    # rather than letting a naive/aware mix surface as a TypeError deep in an estimator loop.
    def _utc(t: str) -> datetime:
        d = datetime.fromisoformat(t)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

    data = {
        s: {b: [(_utc(t), v) for t, v in pts] for b, pts in bases.items()}
        for s, bases in raw.items()
    }

    report = {
        "generated_from": "production Neon observations 2025-12-01 .. 2025-12-22, 15-minute cadence",
        "stations": STATIONS, "window_h": WINDOW_H, "sustain_h": SUSTAIN_H,
        "A_jitter": {b: run_a_jitter(data, b) for b in ("stage", "flow")},
        "B_robustness": {b: run_b_robustness(data, b) for b in ("stage", "flow")},
        "C_timing": {b: run_c_timing(data, b) for b in ("stage", "flow")},
        "D_tide": run_d_tide(data),
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
