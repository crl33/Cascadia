"""The `nwis/stat` -> OGC `observationNormals` cross-check migration.

Companion to `docs/research/nwis-stat-successor-2026-08-27.md`. Two jobs:

1. Pin what the successor actually is, from captured bytes — including the three ways it is NOT
   a transport swap (no period of record, literal "nan", a different record membership).
2. Refuse the comfortable reading. `nwis/stat` was retired because it decommissions, not because
   the replacement is the same numbers. A test that asserted "they match" would be asserting the
   opposite of what was measured, and would quietly bless calling this a like-for-like swap.

The legacy RDB parser is exercised here too: it is kept to read ARCHIVED artifacts, so it has to
keep working after the live path stopped using it.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import httpx
import pytest
import respx

from cascade_core.fetch import ArchivingFetcher
from cascade_core.objectstore import LocalFilesystemStore
from cascade_providers_usgs import climatology as clim
from cascade_providers_usgs import stats_client
from cascade_providers_usgs.parser import ParseError
from cascade_providers_usgs.stats_parser import parse_nwis_stat_rdb, parse_ogc_normals_json

STATS = Path(__file__).resolve().parents[1] / "fixtures/providers/usgs_stats"
SAUK = "12189500"
SKAGIT = "12200500"
LADDER_LEVELS = [5, 10, 25, 50, 75, 90, 95]


class _NullSession:
    """`fetch` only ever `add`s the RawArtifact and flushes; nothing here needs a database."""

    def add(self, _obj) -> None:
        _obj.id = 1

    async def flush(self) -> None:
        return None


def _successor(name: str = f"observation_normals_{SAUK}_00060.json"):
    return parse_ogc_normals_json((STATS / name).read_bytes())


def _legacy(site: str = SAUK):
    return parse_nwis_stat_rdb((STATS / f"stat_{site}.rdb").read_bytes())


# --- what the successor is ----------------------------------------------------------------


def test_the_successor_serves_exactly_the_ladder_cascadia_builds() -> None:
    rows = _successor()
    assert len(rows) == 366
    assert sorted({p for r in rows for p in r.percentiles}) == LADDER_LEVELS
    assert list(clim.PERCENTILES) == LADDER_LEVELS, "the ladder and the source must not drift apart"
    assert {r.site for r in rows} == {SAUK}


def test_the_successor_publishes_no_period_of_record_and_none_is_invented() -> None:
    """§8. `nwis/stat` published begin_yr/end_yr; this API publishes only a per-day sample_count.

    The ref therefore says `nN-M`. Anything that looks like a year span here would be a
    fabricated provenance claim about a source that never stated one.
    """
    rows = _successor()
    assert all(r.begin_year is None and r.end_year is None for r in rows)
    assert all(r.count for r in rows)

    built = clim.published_climatology(rows, site=SAUK)
    assert built.begin_year is None and built.end_year is None
    assert built.climatology_ref == "usgs-ogc-normals:12189500:n25-100"
    assert "19" not in built.climatology_ref and "20" not in built.climatology_ref

    legacy = clim.published_climatology(_legacy(), site=SAUK, method_id=clim.PUBLISHED_METHOD_ID_V1)
    assert legacy.climatology_ref.startswith("usgs-nwis-stat:")
    assert legacy.begin_year and legacy.end_year, "the retired source DID publish a period of record"


def test_the_literal_nan_this_api_serves_never_becomes_a_number() -> None:
    """`float("nan")` does not raise, so a try/except ValueError would let NaN through.

    Measured 2026-08-27: 735 such entries at 12100490's 17-year record, 2 at 12213100's Feb 29.
    A missing level is absent from the ladder, exactly as an empty RDB column was — never a zero
    and never a NaN.
    """
    raw = json.loads((STATS / "observation_normals_nan_days.json").read_bytes())
    served = [v for f in raw["features"] for s in f["properties"]["data"] for v in s["values"]]
    assert served, "anti-vacuity: the fixture must actually carry nan entries"
    assert any(str(x).lower() == "nan" for v in served for x in v["values"])

    rows = parse_ogc_normals_json((STATS / "observation_normals_nan_days.json").read_bytes())
    assert rows
    for row in rows:
        assert row.percentiles, "a day that lost its tail still keeps the levels it had"
        assert all(math.isfinite(v) for v in row.percentiles.values())
        assert 5 not in row.percentiles and 95 not in row.percentiles  # the nan ones
        assert {10, 25, 50, 75, 90} <= set(row.percentiles)


def test_mismatched_percentile_and_value_arrays_are_refused_not_zipped_short() -> None:
    doc = json.loads((STATS / f"observation_normals_{SAUK}_00060.json").read_bytes())
    record = next(
        v for f in doc["features"] for s in f["properties"]["data"]
        for v in s["values"] if v.get("computation") == "percentile"
    )
    record["values"] = record["values"][:-1]
    with pytest.raises(ParseError, match="percentile levels but"):
        parse_ogc_normals_json(json.dumps(doc).encode())


def test_only_daily_mean_discharge_day_of_year_percentiles_are_read() -> None:
    """The unfiltered payload carries sediment, turbidity, temperature and stage.

    Cascadia asks for `parameter_code=00060`, but the parser must not depend on the server
    honouring that — a widened response has to be ignored, not coerced into the discharge ladder.
    """
    doc = json.loads((STATS / f"observation_normals_{SAUK}_00060.json").read_bytes())
    series = doc["features"][0]["properties"]["data"][0]
    for mutation in ({"parameter_code": "00065"}, {"parent_statistic_id": "00001"}):
        poisoned = json.loads(json.dumps(doc))
        poisoned["features"][0]["properties"]["data"][0].update(mutation)
        assert parse_ogc_normals_json(json.dumps(poisoned).encode()) == (), mutation

    widened = json.loads(json.dumps(doc))
    stage = json.loads(json.dumps(series)) | {"parameter_code": "00065", "unit_of_measure": "ft"}
    widened["features"][0]["properties"]["data"].append(stage)
    assert len(parse_ogc_normals_json(json.dumps(widened).encode())) == 366

    non_doy = json.loads(json.dumps(doc))
    for v in non_doy["features"][0]["properties"]["data"][0]["values"]:
        v["time_of_year_type"] = "month"
    assert parse_ogc_normals_json(json.dumps(non_doy).encode()) == ()


# --- how it compares to the source it replaces --------------------------------------------


def test_the_successor_is_not_value_identical_to_the_table_it_replaces() -> None:
    """§7. Pinned so this is never later described as a transport swap.

    ADR-0015 kept ONE product across the two instantaneous transports because parity was measured
    exact (1754/1754 rows). Here the opposite was measured, which is why the successor carries its
    own source, product and method id.
    """
    legacy = {(r.month, r.day): r for r in _legacy()}
    new = {(r.month, r.day): r for r in _successor()}
    common = sorted(set(legacy) & set(new))
    assert len(common) == 366

    equal = [k for k in common if legacy[k].percentiles.get(50) == new[k].percentiles.get(50)]
    assert equal, "anti-vacuity: they are the same statistic, so many days DO agree exactly"
    assert len(equal) == 141, "if this moves, USGS republished one of the two — re-measure §4"

    differing_counts = [k for k in common if legacy[k].count != new[k].count]
    assert len(differing_counts) == 366, "the two are computed over different records, every day"
    assert {new[k].count - legacy[k].count for k in common} == {1, 2}


def test_the_disagreement_is_small_enough_to_stay_within_the_cross_check_threshold() -> None:
    """Not-identical is not the same as far apart: at this gauge the two agree well.

    The one gauge where they do not is 12113000, where the successor holds 6-26 more years; that
    is recorded in §4 rather than fixtured, because it needs the whole published table to see.
    """
    legacy = {(r.month, r.day): r for r in _legacy()}
    new = {(r.month, r.day): r for r in _successor()}
    rel = [
        abs(legacy[k].percentiles[50] - new[k].percentiles[50]) / legacy[k].percentiles[50]
        for k in sorted(set(legacy) & set(new))
        if legacy[k].percentiles.get(50) and new[k].percentiles.get(50)
    ]
    assert len(rel) == 366
    assert statistics.median(rel) < 0.005
    assert max(rel) < 0.06
    assert not [r for r in rel if r > 0.10], "no day crosses the confidence threshold at this gauge"


def test_a_successor_table_for_the_wrong_site_is_refused_rather_than_merged() -> None:
    rows = _successor()
    assert clim.published_climatology(rows, site=SAUK).ladders
    wrong = clim.published_climatology(rows, site=SKAGIT)
    assert wrong.ladders == {} and wrong.skipped["other_site"] == 366


def test_the_retired_source_keeps_its_own_identity_when_an_archive_is_replayed() -> None:
    """A stored ladder must name the service that actually produced its bytes."""
    legacy = clim.published_climatology(_legacy(), site=SAUK, method_id=clim.PUBLISHED_METHOD_ID_V1)
    assert legacy.method_id == "method:usgs-published-doy-stats@1.0.0"
    assert legacy.climatology_ref == "usgs-nwis-stat:12189500:1929-2026"
    assert clim.published_climatology(_successor(), site=SAUK).method_id == "method:usgs-published-doy-stats@2.0.0"
    assert clim.PUBLISHED_METHOD_ID != clim.PUBLISHED_METHOD_ID_V1


# --- the request Cascadia actually sends ---------------------------------------------------


@respx.mock
async def test_the_request_is_filtered_to_discharge_day_of_year_on_the_ogc_host(tmp_path) -> None:
    """§13. `parameter_code` is cost discipline, not tidiness.

    Unfiltered this endpoint returns every parameter the station publishes — 2.4 MB at the Sauk,
    3.6 MB at Mount Vernon, sediment and turbidity included. Filtered to discharge it is ~415 KB.
    At six gauges once a year that is the difference between ~2.5 MB and ~15 MB of archived bytes
    for the same single number the cross-check reads.
    """
    route = respx.get(stats_client.OBSERVATION_NORMALS_URL).mock(
        return_value=httpx.Response(200, content=(STATS / f"observation_normals_{SAUK}_00060.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )
    fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="CascadiaPapsukkal/0.1 (test)")
    await stats_client.fetch_published_doy_normals(fetcher, _NullSession(), site=SAUK)

    request = route.calls[0].request
    assert request.url.host == "api.waterdata.usgs.gov"
    assert request.url.params["parameter_code"] == "00060"
    assert request.url.params["normal_type"] == "DOY"
    assert request.url.params["monitoring_location_id"] == f"USGS-{SAUK}"
    assert "waterservices" not in str(request.url)


def test_the_climatology_job_cannot_reach_the_retired_service_at_all() -> None:
    """§6, the strongest form of "no silent fallback": the import does not exist.

    `jobs.py` has had this guard since the instantaneous migration
    (`test_usgs_transport_parity::test_the_live_job_cannot_reach_the_legacy_client_at_all`);
    `stats_jobs.py` did not. Found by mutation on 2026-08-27: adding a legacy import to its
    `except FetchError` handler passed the entire suite. A transport that switches itself under
    failure makes provenance and outage interpretation ambiguous — health reads green on data
    from somewhere else — which is exactly what the cross-check must never do.
    """
    from cascade_providers_usgs import stats_jobs

    source = Path(stats_jobs.__file__).read_text()
    code = [line for line in source.splitlines() if not line.strip().startswith("#")]
    offending = [line.strip() for line in code if "nwis" in line.lower() or "waterservices" in line.lower()]
    assert not offending, f"the climatology job reached for the retired service: {offending}"
    assert "fetch_published_doy_normals" in source and "parse_ogc_normals_json" in source
