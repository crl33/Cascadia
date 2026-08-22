"""Risk-state computation + stale detection.

Doctrine (Phase 1.5):
  - Compute non-unknown risk ONLY when thresholds.validated is True.
  - When thresholds source is 'configured_pending' or 'thresholds_unavailable',
    risk = 'unknown' with a clear reason. We never guess.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from .types import FloodThresholds

STALE_AFTER_MINUTES = 90  # USGS publishing cadence varies (15-60 min typical)


def compute_risk(
    stage_ft: Optional[float],
    thresholds: FloodThresholds,
) -> Tuple[str, str]:
    """Returns (state, reason).

    Only runs comparison when thresholds.validated is True.
    """
    if stage_ft is None:
        return "unknown", "No current gage height available."

    if not thresholds.validated:
        if thresholds.source == "configured_pending":
            return (
                "unknown",
                "Configured thresholds for this gauge have not yet been validated; "
                "risk cannot be computed safely.",
            )
        return (
            "unknown",
            "Flood thresholds are not available for this gauge.",
        )

    if all(
        v is None
        for v in (
            thresholds.action,
            thresholds.minor,
            thresholds.moderate,
            thresholds.major,
        )
    ):
        return "unknown", "Validated thresholds are missing values for all categories."

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


def is_stale(latest_at_iso: Optional[str], minutes: int = STALE_AFTER_MINUTES) -> bool:
    if not latest_at_iso:
        return True
    try:
        dt = datetime.fromisoformat(latest_at_iso.replace("Z", "+00:00"))
    except Exception:
        return True
    age = datetime.now(timezone.utc) - dt
    return age > timedelta(minutes=minutes)
