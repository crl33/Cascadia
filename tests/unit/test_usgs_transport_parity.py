"""Transport parity: the OGC `continuous` path and the legacy NWIS IV path must normalize to the
SAME observations, and anything downstream must therefore be unchanged.

This is the offline, frozen half of the migration evidence. The live half is
`scripts/compare_usgs_iv_ogc.py`, which fetches both endpoints and is recorded in
`docs/research/usgs-ogc-instantaneous-parity-2026-08-27.md`; this file pins the result against
captures of the SAME gauges over the SAME window so a regression fails in CI rather than being
noticed by someone re-running a script.

The comparison is on semantic rows — station, variable, valid time, value, unit, datum, quality —
never on raw JSON. The transports serve different encodings by definition; the question is only
what lands in `observation`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from cascade_providers_usgs.normalize import to_observations
from cascade_providers_usgs.ogc_normalize import to_observation_records
from cascade_providers_usgs.ogc_parser import parse_continuous
from cascade_providers_usgs.parser import parse_iv

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/providers"
RETRIEVED = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)
#: The six gauges `usgs/valid.json` carries; `usgs_ogc/parity/*.json` covers the same window.
SITES = ("12100490", "12113000", "12119000", "12149000", "12200500", "12213100")
DATUM = "NGVD29"


def _iv_rows():
    rows = {}
    for series in parse_iv((FIXTURES / "usgs/valid.json").read_bytes()):
        for r in to_observations(series, retrieved_at=RETRIEVED, station_id=f"station:usgs:{series.site}", datum=DATUM):
            rows[(r.station_id, r.variable, r.valid_time)] = r
    return rows


def _ogc_rows():
    rows = {}
    for site in SITES:
        page = parse_continuous((FIXTURES / f"usgs_ogc/parity/{site}.json").read_bytes())
        recs, _ = to_observation_records(
            page.values, retrieved_at=RETRIEVED, station_id=f"station:usgs:{site}", datum=DATUM, backfilled=False,
        )
        for r in recs:
            rows[(r.station_id, r.variable, r.valid_time)] = r
    return rows


@pytest.fixture(scope="module")
def both():
    iv, ogc = _iv_rows(), _ogc_rows()
    assert iv, "anti-vacuity: the legacy fixture produced no rows"
    assert ogc, "anti-vacuity: the OGC fixture produced no rows"
    shared = sorted(set(iv) & set(ogc))
    assert len(shared) > 500, f"anti-vacuity: only {len(shared)} shared instants — an empty comparison cannot pass as identical"
    return iv, ogc, shared


def test_the_two_transports_agree_on_every_shared_observation(both) -> None:
    iv, ogc, shared = both
    for key in shared:
        a, b = iv[key], ogc[key]
        assert a.value == b.value, key
        assert a.unit == b.unit, key
        assert a.datum == b.datum, key
        assert set(a.quality) == set(b.quality), (key, sorted(a.quality), sorted(b.quality))


def test_the_only_difference_is_how_the_source_spells_its_own_approval(both) -> None:
    """`qualifier_raw` is verbatim source text, so it SHOULD differ — and it is the one field
    that lets a stored row say which transport produced it without joining anything."""
    iv, ogc, shared = both
    spellings = {(iv[k].qualifier_raw, ogc[k].qualifier_raw) for k in shared}
    assert spellings == {("P", "Provisional")}, spellings
    # and it is deliberately NOT part of the idempotency comparison in jobs.py, which is why
    # cutover writes no revision rows for observations the legacy path had already stored
    from cascade_providers_usgs import jobs

    source = Path(jobs.__file__).read_text()
    assert "prev.value == r.value and list(prev.quality) == list(r.quality)" in source
    assert "qualifier_raw" not in source.split("if prev is not None")[1].split("\n")[0]


def test_neither_transport_silently_loses_a_gauge_or_a_variable(both) -> None:
    iv, ogc, _ = both
    def index(rows):
        out = {}
        for (st, var, _t) in rows:
            out.setdefault(st, set()).add(var)
        return out
    assert index(iv) == index(ogc)
    for st, vars_ in index(ogc).items():
        assert vars_ == {"stage", "flow"}, (st, vars_)


def test_a_live_poll_is_not_marked_backfilled(both) -> None:
    """The flag is not cosmetic: the client renders a `backfilled` value as ARCHIVED with an age
    said as distance from today, so a live reading carrying it would show as an archived record."""
    _iv, ogc, _ = both
    assert not any("backfilled" in r.quality for r in ogc.values())
    # ...while the backfill caller, which is what the flag exists for, still sets it
    page = parse_continuous((FIXTURES / "usgs_ogc/parity/12200500.json").read_bytes())
    backfilled, _ = to_observation_records(
        page.values, retrieved_at=RETRIEVED, station_id="station:usgs:12200500", datum=DATUM,
    )
    assert backfilled and all("backfilled" in r.quality for r in backfilled)


def test_no_production_module_calls_the_decommissioning_legacy_service() -> None:
    """§13 of the migration brief, enforced rather than asserted once and forgotten.

    Every remaining `waterservices.usgs.gov` reference must be one of: the retired comparator
    (`client.py`), the host ceiling it needs, the registry row for the retired statistics source,
    or prose. A NEW production call site is a regression, and the deadline these migrations exist
    to remove would quietly come back.

    `stats_client.py` left this list on 2026-08-27 when `nwis/stat` was retired in favour of the
    OGC statistics API. It must not come back: nothing in `packages/` may request that host again.
    """
    import re

    root = Path(__file__).resolve().parents[2]
    allowed_files = {
        # the retired instantaneous comparator — see its own docstring
        "packages/providers/usgs/src/cascade_providers_usgs/client.py",
        # the host ceiling the comparator needs; no production module passes these hosts
        "packages/core/src/cascade_core/fetch.py",
        # the registry row for the RETIRED statistics source, kept so historical rows resolve
        "packages/core/src/cascade_core/registry.py",
    }
    offenders = []
    for area in ("packages", "apps", "infra"):
        for path in (root / area).rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            text = path.read_text()
            if "waterservices.usgs.gov" not in text:
                continue
            if rel in allowed_files:
                continue
            # anything else may only MENTION it, never assign or request it
            for line in text.splitlines():
                if "waterservices.usgs.gov" not in line:
                    continue
                stripped = line.strip()
                is_prose = stripped.startswith("#") or not re.search(r'["\']https://(nwis\.)?waterservices', line)
                if not is_prose:
                    offenders.append(f"{rel}: {stripped[:100]}")
    assert not offenders, "new production call sites for the decommissioning service:\n" + "\n".join(offenders)


def test_the_live_job_cannot_reach_the_legacy_client_at_all() -> None:
    """The strongest form of "no silent fallback": the import does not exist."""
    from cascade_providers_usgs import jobs

    source = Path(jobs.__file__).read_text()
    assert "from cascade_providers_usgs.client import" not in source
    assert "from cascade_providers_usgs.parser import" not in source
    assert "from cascade_providers_usgs.normalize import" not in source
    assert "ogc_client" in source and "ogc_parser" in source and "ogc_normalize" in source
