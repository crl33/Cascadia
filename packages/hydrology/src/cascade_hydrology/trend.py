"""Rate of rise over a window from stored observations (method:rate-of-rise@1.0.0).

rate = (last - first) / hours between them, using only non-sentinel values inside the window.
UNKNOWN when fewer than two values, when any gap between consecutive values exceeds
`max_gap_h`, or when the covered span is under `min_span_fraction` of the window. Direction:
|rate| <= steady epsilon => STEADY (stage: 0.05 ft/h; flow: 1 %/h of the latest value)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

RISING = "rising"
FALLING = "falling"
STEADY = "steady"
UNKNOWN = "unknown"

STAGE_STEADY_EPS_FT_PER_H = 0.05
FLOW_STEADY_FRACTION_PER_H = 0.01


@dataclass(frozen=True)
class TrendResult:
    window_h: int
    rate: float | None  # unit per hour
    unit: str | None  # e.g. ft/h, cfs/h
    direction: str
    reason: str | None


def steady_epsilon(basis: str, last_value: float) -> float:
    if basis == "stage":
        return STAGE_STEADY_EPS_FT_PER_H
    return max(1.0, abs(last_value) * FLOW_STEADY_FRACTION_PER_H)


def rate_of_rise(
    points: list[tuple[datetime, float]],
    *,
    basis: str,
    unit: str,
    end: datetime,
    window_h: int = 6,
    max_gap_h: float = 2.0,
    min_span_fraction: float = 0.5,
) -> TrendResult:
    start = end - timedelta(hours=window_h)
    pts = sorted((t, v) for t, v in points if start <= t <= end)
    if len(pts) < 2:
        return TrendResult(window_h, None, None, UNKNOWN, f"fewer than 2 observations in the last {window_h} h")
    gaps = [(b[0] - a[0]).total_seconds() / 3600 for a, b in zip(pts, pts[1:], strict=False)]
    if max(gaps) > max_gap_h:
        return TrendResult(window_h, None, None, UNKNOWN, f"gap of {max(gaps):.2f} h between observations exceeds {max_gap_h:g} h tolerance")
    span_h = (pts[-1][0] - pts[0][0]).total_seconds() / 3600
    if span_h < min_span_fraction * window_h:
        return TrendResult(window_h, None, None, UNKNOWN, f"observations span only {span_h:.2f} h of the {window_h} h window")
    rate = (pts[-1][1] - pts[0][1]) / span_h
    eps = steady_epsilon(basis, pts[-1][1])
    direction = STEADY if abs(rate) <= eps else (RISING if rate > 0 else FALLING)
    return TrendResult(window_h, rate, f"{unit}/h", direction, None)
