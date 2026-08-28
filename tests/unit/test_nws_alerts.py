"""NWS CAP alerts: routing by derived UGC mapping, append-only supersession, honest replay.

The captured fixture is genuinely useful as a NEGATIVE case: the two live alerts on capture day
were east-side (Air Quality, WAC007/WAC017/WAC037/WAC047), so they must be STORED — they are
knowledge — while routing to zero seed basins. Flood alerts for the seed basins are synthesized
from the same shape with west-side UGC codes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from sqlalchemy import select

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher
from cascade_core.knowledge import as_known_at
from cascade_core.models import OfficialAlertRecord
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_hydrology.assemble import basin_envelope
from cascade_providers_nwps import alerts_jobs
from cascade_providers_nwps.alerts import (
    ALERTS_URL,
    load_ugc_mapping,
    parse_active_alerts,
)
from cascade_providers_nwps.reaches_parser import ParseError
from tests.conftest import FIXTURES, GEO

NWS = FIXTURES / "nws_api"
ACTIVE = (NWS / "alerts_active_wa.json").read_bytes()
NOW = datetime(2026, 8, 28, 5, 0, tzinfo=UTC)


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/alerts.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def _fetcher(tmp_path) -> ArchivingFetcher:
    return ArchivingFetcher(
        store=LocalFilesystemStore(tmp_path), user_agent="test", clock=lambda: NOW
    )


def _flood_alert(
    alert_id: str,
    *,
    ugc: list[str],
    sent: str = "2026-08-28T04:00:00+00:00",
    ends: str | None = "2026-08-29T04:00:00+00:00",
    references: list | None = None,
    status: str = "Actual",
    message_type: str = "Alert",
) -> dict:
    return {
        "properties": {
            "id": alert_id,
            "event": "Flood Warning",
            "status": status,
            "messageType": message_type,
            "severity": "Severe",
            "certainty": "Likely",
            "urgency": "Expected",
            "headline": "Flood Warning issued for the Skagit River",
            "senderName": "NWS Seattle WA",
            "sent": sent,
            "onset": sent,
            "expires": ends,
            "ends": ends,
            "geocode": {"UGC": ugc},
            "references": [{"identifier": r} for r in (references or [])],
        }
    }


def _payload(*alerts: dict) -> bytes:
    return json.dumps({"features": list(alerts)}).encode()


# --- the mapping --------------------------------------------------------------------------


def test_the_derived_mapping_routes_by_real_geography() -> None:
    mapping = load_ugc_mapping(GEO / "basin_ugc.json")
    assert mapping.method_id == "method:basin-ugc-mapping@1.0.0"
    # Skagit County covers the Skagit and clips the Nooksack; Eastside is the Cedar/Lake WA basin
    assert mapping.basins_for(("WAC057",)) == ("basin:nooksack", "basin:skagit")
    assert mapping.basins_for(("WAZ314",)) == ("basin:cedar",)
    # east-side counties route nowhere — the negative case the live fixture exercises
    assert mapping.basins_for(("WAC007", "WAC017", "WAC037", "WAC047")) == ()
    # multiple codes union
    assert "basin:puyallup-white" in mapping.basins_for(("WAC053", "WAZ314"))


def test_a_missing_or_malformed_mapping_refuses_rather_than_routing_nothing(
    tmp_path,
) -> None:
    with pytest.raises(ParseError, match="no UGC mapping"):
        load_ugc_mapping(tmp_path / "absent.json")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"zones": {}}))
    with pytest.raises(ParseError, match="no method_id or no zones"):
        load_ugc_mapping(bad)


# --- the parser ---------------------------------------------------------------------------


def test_the_real_payload_parses_with_aware_utc_instants() -> None:
    alerts = parse_active_alerts(ACTIVE)
    assert len(alerts) == 2
    for a in alerts:
        assert a.sent.tzinfo is not None and a.sent.utcoffset().total_seconds() == 0
        assert a.status == "Actual"
        assert a.ugc  # every CAP alert locates itself
    # '-07:00' offsets normalised, not stripped: 11:52 PDT is 18:52Z
    pendleton = next(a for a in alerts if "Pendleton" in (a.sender_name or ""))
    assert pendleton.sent == datetime(2026, 8, 27, 18, 52, tzinfo=UTC)


def test_a_naive_timestamp_is_refused() -> None:
    doc = json.loads(ACTIVE)
    doc["features"][0]["properties"]["sent"] = "2026-08-27T11:52:00"
    with pytest.raises(ParseError, match="carries no offset"):
        parse_active_alerts(json.dumps(doc).encode())


# --- the job ------------------------------------------------------------------------------


@respx.mock
async def test_east_side_alerts_are_stored_but_route_to_no_basin(
    sessions, tmp_path
) -> None:
    respx.get(ALERTS_URL).mock(
        return_value=httpx.Response(
            200, content=ACTIVE, headers={"content-type": "application/geo+json"}
        )
    )
    async with sessions() as s:
        written = await alerts_jobs.run_fetch_alerts(s, _fetcher(tmp_path), geo_dir=GEO)
        await s.commit()
        rows = list((await s.execute(select(OfficialAlertRecord))).scalars())
    assert written == 2 and len(rows) == 2
    for row in rows:
        assert (
            row.basin_ids == []
        )  # knowledge, stored; spatially irrelevant to the seed basins
        assert row.mapping_method_id == "method:basin-ugc-mapping@1.0.0"
        assert row.available_at is not None


@respx.mock
async def test_the_poll_is_idempotent_by_cap_id(sessions, tmp_path) -> None:
    respx.get(ALERTS_URL).mock(
        return_value=httpx.Response(
            200, content=ACTIVE, headers={"content-type": "application/geo+json"}
        )
    )
    async with sessions() as s:
        first = await alerts_jobs.run_fetch_alerts(s, _fetcher(tmp_path), geo_dir=GEO)
        await s.commit()
    async with sessions() as s:
        second = await alerts_jobs.run_fetch_alerts(s, _fetcher(tmp_path), geo_dir=GEO)
        await s.commit()
    assert first == 2 and second == 0


@respx.mock
async def test_a_flood_warning_reaches_its_basins_envelope_with_provenance(
    sessions, tmp_path
) -> None:
    """End to end: poll -> route -> knowledge -> envelope, with the ref resolving."""
    respx.get(ALERTS_URL).mock(
        return_value=httpx.Response(
            200,
            content=_payload(
                _flood_alert("urn:oid:2.49.0.1.840.0.test.001.1", ugc=["WAC057"])
            ),
            headers={"content-type": "application/geo+json"},
        )
    )
    async with sessions() as s:
        await alerts_jobs.run_fetch_alerts(s, _fetcher(tmp_path), geo_dir=GEO)
        await s.commit()
    async with sessions() as s:
        k = as_known_at(s, NOW)
        env = await basin_envelope(k, await k.basins(), generated_at=NOW)
    by_id = {i.id: i for i in env.items}
    skagit = by_id["basin:skagit"].official_alerts
    assert len(skagit) == 1
    alert = skagit[0]
    assert alert.event == "Flood Warning"
    assert alert.issuer == "NWS Seattle WA"
    assert alert.prov in env.provenance_refs, "every displayed alert traces"
    ref = env.provenance_refs[alert.prov]
    assert ref.source_kind.value == "OFFICIAL_FORECAST"
    assert "WAC057" in ref.label and "method:basin-ugc-mapping" in ref.label
    # WAC057 clips the Nooksack too; and the Cedar had no alert
    assert len(by_id["basin:nooksack"].official_alerts) == 1
    assert by_id["basin:cedar"].official_alerts == ()


@respx.mock
async def test_supersession_and_expiry_govern_what_is_active_at_a_knowledge_time(
    sessions, tmp_path
) -> None:
    """Append-only: the Update is a NEW row referencing the old; replay resolves the chain."""
    original = _flood_alert(
        "urn:test.a.1", ugc=["WAC057"], sent="2026-08-28T02:00:00+00:00"
    )
    update = _flood_alert(
        "urn:test.a.2",
        ugc=["WAC057"],
        sent="2026-08-28T04:30:00+00:00",
        references=["urn:test.a.1"],
        message_type="Update",
    )
    respx.get(ALERTS_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                content=_payload(original),
                headers={"content-type": "application/geo+json"},
            ),
            httpx.Response(
                200,
                content=_payload(original, update),
                headers={"content-type": "application/geo+json"},
            ),
        ]
    )
    async with sessions() as s:
        fetcher = _fetcher(tmp_path)
        await alerts_jobs.run_fetch_alerts(s, fetcher, geo_dir=GEO)
        await alerts_jobs.run_fetch_alerts(s, fetcher, geo_dir=GEO)
        await s.commit()
        # now: only the update is active — the original is superseded, not deleted
        active_now = await as_known_at(s, NOW).active_alerts()
        assert [a.id for a in active_now] == ["urn:test.a.2"]
        rows = list((await s.execute(select(OfficialAlertRecord))).scalars())
        assert len(rows) == 2, "supersession never deletes: both rows replay"
        # past the end time, nothing is active
        later = as_known_at(s, NOW + timedelta(days=2))
        assert await later.active_alerts() == []


@respx.mock
async def test_test_and_exercise_alerts_never_reach_a_surface(
    sessions, tmp_path
) -> None:
    test_alert = _flood_alert("urn:test.x.1", ugc=["WAC057"], status="Test")
    respx.get(ALERTS_URL).mock(
        return_value=httpx.Response(
            200,
            content=_payload(test_alert),
            headers={"content-type": "application/geo+json"},
        )
    )
    async with sessions() as s:
        written = await alerts_jobs.run_fetch_alerts(s, _fetcher(tmp_path), geo_dir=GEO)
        await s.commit()
        assert written == 1, "stored — the poll happened and the record is knowledge"
        assert await as_known_at(s, NOW).active_alerts() == [], (
            "but never active, never displayed"
        )


@respx.mock
async def test_an_alert_is_invisible_to_replays_before_cascadia_knew_it(
    sessions, tmp_path
) -> None:
    """The look-ahead rule, on alerts: sent-time is NOT knowledge-time.

    An alert SENT at 04:00 that this platform first fetched at 05:00 must be absent from a
    replay of 04:30 — at 04:30 Cascadia did not know it. `available_at` carries the poll
    instant, and the reader filters on it, never on `sent`.
    """
    respx.get(ALERTS_URL).mock(
        return_value=httpx.Response(
            200,
            content=_payload(
                _flood_alert(
                    "urn:test.k.1", ugc=["WAC057"], sent="2026-08-28T04:00:00+00:00"
                )
            ),
            headers={"content-type": "application/geo+json"},
        )
    )
    async with sessions() as s:
        await alerts_jobs.run_fetch_alerts(
            s, _fetcher(tmp_path), geo_dir=GEO
        )  # fetched at NOW = 05:00
        await s.commit()
        replay = as_known_at(s, datetime(2026, 8, 28, 4, 30, tzinfo=UTC))
        assert await replay.active_alerts() == [], (
            "sent 04:00, known 05:00 — invisible at 04:30"
        )
        assert len(await as_known_at(s, NOW).active_alerts()) == 1


@respx.mock
async def test_an_alert_that_never_says_when_it_ends_is_bounded_not_eternal(sessions, tmp_path) -> None:
    """CAP permits a message with neither ends nor expires; 'active forever' is a duration the
    issuer never claimed, so the reader bounds it at MAX_UNBOUNDED_ALERT_AGE from sent."""
    from cascade_core.knowledge import MAX_UNBOUNDED_ALERT_AGE

    endless = _flood_alert("urn:test.e.1", ugc=["WAC057"], sent="2026-08-28T00:00:00+00:00", ends=None)
    endless["properties"]["expires"] = None
    respx.get(ALERTS_URL).mock(return_value=httpx.Response(
        200, content=_payload(endless), headers={"content-type": "application/geo+json"}))
    async with sessions() as s:
        await alerts_jobs.run_fetch_alerts(s, _fetcher(tmp_path), geo_dir=GEO)
        await s.commit()
        soon = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)
        assert len(await as_known_at(s, soon).active_alerts()) == 1
        past_cap = datetime(2026, 8, 28, 0, 0, tzinfo=UTC) + MAX_UNBOUNDED_ALERT_AGE + timedelta(hours=1)
        assert await as_known_at(s, past_cap).active_alerts() == []


@respx.mock
async def test_supersession_outlives_a_short_lived_cancel(sessions, tmp_path) -> None:
    """The time-sliced candidate read must not resurrect a cancelled alert: the Cancel's own
    end can be long past while its target's natural end is not, and the reference must still
    suppress the target (the regression the SQL prefilter would have introduced)."""
    original = _flood_alert("urn:test.c.1", ugc=["WAC057"], sent="2026-08-28T00:00:00+00:00",
                            ends="2026-08-30T00:00:00+00:00")
    cancel = _flood_alert("urn:test.c.2", ugc=["WAC057"], sent="2026-08-28T02:00:00+00:00",
                          ends="2026-08-28T02:30:00+00:00", references=["urn:test.c.1"],
                          message_type="Update")
    respx.get(ALERTS_URL).mock(return_value=httpx.Response(
        200, content=_payload(original, cancel), headers={"content-type": "application/geo+json"}))
    async with sessions() as s:
        await alerts_jobs.run_fetch_alerts(s, _fetcher(tmp_path), geo_dir=GEO)
        await s.commit()
        # hours after the Cancel itself ended, days before the original would have:
        later = datetime(2026, 8, 28, 20, 0, tzinfo=UTC)
        assert await as_known_at(s, later).active_alerts() == [], (
            "the cancelled alert must stay dead even when the Cancel left the time slice"
        )
