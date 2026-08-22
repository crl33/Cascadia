"""Shared offline test helpers: fixture paths and a fixed clock. No network anywhere in tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "providers"
GEO = ROOT / "tests" / "fixtures" / "geo"
CLOCK = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)  # shortly after the fixtures were captured (13:16Z)


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


def fixed_clock() -> datetime:
    return CLOCK
