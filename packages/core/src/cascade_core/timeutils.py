"""Time is three-valued and always aware (docs/DATA_DOCTRINE.md §3, §11).

Provider strings are parsed WITH their UTC offset into aware datetimes and stored as UTC.
Timestamp strings are never compared lexicographically anywhere in the codebase.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 string carrying an offset ('Z' or ±HH:MM) into an aware UTC datetime.

    Raises ValueError when the string has no offset: a naive provider timestamp is a defect,
    never an assumption.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"not a timestamp string: {value!r}")
    s = value.strip()
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"timestamp without UTC offset: {value!r}")
    return dt.astimezone(UTC)


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("naive datetime; all datetimes must be aware")
    return dt.astimezone(UTC)


def iso_z(dt: datetime) -> str:
    """UTC ISO-8601 with a trailing Z and no sub-second noise beyond what exists."""
    return to_utc(dt).isoformat().replace("+00:00", "Z")


def available_at(*, valid_time: datetime, retrieved_at: datetime, issued_at: datetime | None = None) -> datetime:
    """Knowledge time (ADR-0010): max(issued_at or valid_time, retrieved_at)."""
    anchor = issued_at if issued_at is not None else valid_time
    return max(to_utc(anchor), to_utc(retrieved_at))
