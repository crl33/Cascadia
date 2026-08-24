"""Integration-test config. Registers the `pg` marker: tests that need a live PostgreSQL,
gated on CASCADE_TEST_PG_URL (skipped everywhere else; the default suite stays offline)."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "pg: requires PostgreSQL via CASCADE_TEST_PG_URL (skipped when unset)")
