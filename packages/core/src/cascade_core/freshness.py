"""Freshness is computed at read time from SourceProduct cadence/grace (docs/DATA_DOCTRINE.md §5).

stale    : now - valid_time  > expected_cadence + grace
degraded : now - retrieved_at > expected_cadence * DEGRADED_MULTIPLIER  (ingestion fell behind)
missing  : no value at all
Nothing stores a freshness boolean; callers pass the stored timestamps and the clock.
"""

from __future__ import annotations

from datetime import datetime

from cascade_contracts import Freshness, FreshnessState

DEGRADED_MULTIPLIER = 4


def compute_freshness(
    *,
    expected_cadence_seconds: int | None,
    grace_seconds: int | None,
    valid_time: datetime | None,
    retrieved_at: datetime | None,
    now: datetime,
) -> Freshness:
    if valid_time is None and retrieved_at is None:
        return Freshness(state=FreshnessState.MISSING, expected_cadence_seconds=expected_cadence_seconds)
    anchor = valid_time if valid_time is not None else retrieved_at
    assert anchor is not None
    age = max(0, int((now - anchor).total_seconds()))
    if expected_cadence_seconds is None or grace_seconds is None:
        return Freshness(state=FreshnessState.UNKNOWN, age_seconds=age)
    if retrieved_at is not None and (now - retrieved_at).total_seconds() > expected_cadence_seconds * DEGRADED_MULTIPLIER:
        state = FreshnessState.DEGRADED
    elif age > expected_cadence_seconds + grace_seconds:
        state = FreshnessState.STALE
    else:
        state = FreshnessState.CURRENT
    return Freshness(state=state, age_seconds=age, expected_cadence_seconds=expected_cadence_seconds)
