"""AFOS FLW/FLS parser fixture tests + the Event Zero T3 golden MVEW1 chain (blocking).

GOLDEN below is the byte record of the 12 archived KSEW MVEW1 crest issuances,
2025-12-09T17:01Z .. 2025-12-12T08:50Z (fixtures are byte-exact IEM AFOS copies; see
tests/fixtures/providers/nws_afos/manifest.yaml). The 2026-08-22 draft of
docs/EVENT_ZERO.md §8 listed 9 issuances and disagreed with the bytes in three places —
each verified against the raw product text; §8 was corrected to this byte record on
2026-08-24 (adversarial verification pass). The original discrepancies, for the record:

- §8 "12-10T09:24Z / 41.5": no KSEW FLW/FLS was transmitted at 09:24Z (IEM listing,
  Dec 10); the 41.5 ft re-issuance is the 08:54Z FLS (MND "1254 AM PST Wed Dec 10").
- §8 "12-11T01:15Z / 42.1": the 42.1 ft statement is the 02:21Z FLS (MND "621 PM PST
  Wed Dec 10"); 5:15 PM PST = 01:15Z is that segment's observed-stage citation time.
- §8 "12-11T10:04Z / 39.1": the 10:04Z FLS forecasts "a crest of 39.7 feet".
- §8 omits the 41.5 ft re-issuances of 12-10T16:47Z and 12-10T19:01Z and the 41.3 ft
  issuance of 12-11T06:47Z.

The six §8 rows the bytes confirm (17:01Z/36.9, 01:24Z/41.5, 23:14Z/42.3, 18:17Z/39.1,
01:12Z/38.3, 08:50Z/38.1) appear below unchanged.
"""

from datetime import UTC, datetime

import pytest

from cascade_providers_nwps.afos import AfosParseError, parse_afos

# (fixture file, wmo ddHHMM, pil, crest ft, H-VTEC crest time)
GOLDEN = (
    ("202512091701-KSEW-WGUS46-FLWSEW.txt", "091701", "FLWSEW", 36.9, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
    ("202512100124-KSEW-WGUS86-FLSSEW.txt", "100124", "FLSSEW", 41.5, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
    ("202512100854-KSEW-WGUS86-FLSSEW.txt", "100854", "FLSSEW", 41.5, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
    ("202512101647-KSEW-WGUS86-FLSSEW.txt", "101647", "FLSSEW", 41.5, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
    ("202512101901-KSEW-WGUS86-FLSSEW.txt", "101901", "FLSSEW", 41.5, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
    ("202512102314-KSEW-WGUS86-FLSSEW.txt", "102314", "FLSSEW", 42.3, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
    ("202512110221-KSEW-WGUS86-FLSSEW.txt", "110221", "FLSSEW", 42.1, datetime(2025, 12, 12, 18, 0, tzinfo=UTC)),
    ("202512110647-KSEW-WGUS86-FLSSEW.txt", "110647", "FLSSEW", 41.3, datetime(2025, 12, 12, 18, 0, tzinfo=UTC)),
    ("202512111004-KSEW-WGUS86-FLSSEW.txt", "111004", "FLSSEW", 39.7, datetime(2025, 12, 12, 18, 0, tzinfo=UTC)),
    ("202512111817-KSEW-WGUS86-FLSSEW.txt", "111817", "FLSSEW", 39.1, datetime(2025, 12, 12, 18, 0, tzinfo=UTC)),
    ("202512120112-KSEW-WGUS86-FLSSEW.txt", "120112", "FLSSEW", 38.3, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
    ("202512120850-KSEW-WGUS86-FLSSEW.txt", "120850", "FLSSEW", 38.1, datetime(2025, 12, 12, 12, 0, tzinfo=UTC)),
)


def _segment(product, lid):
    return next(s for s in product.segments if s.lid == lid)


@pytest.mark.parametrize(("fname", "ddhhmm", "pil", "crest", "crest_time"), GOLDEN, ids=[g[0][:12] for g in GOLDEN])
def test_golden_mvew1_chain(fixtures, fname, ddhhmm, pil, crest, crest_time) -> None:
    """BLOCKING: every MVEW1 issuance reproduces the archived crest value and time bin."""
    (product,) = parse_afos((fixtures / f"nws_afos/{fname}").read_bytes())
    assert (product.office, product.wmo_ddhhmm, product.pil) == ("KSEW", ddhhmm, pil)
    issued = datetime.strptime(f"2025{ddhhmm}", "%Y%d%H%M").replace(month=12, tzinfo=UTC)
    assert product.wmo_matches(issued)
    seg = _segment(product, "MVEW1")
    assert seg.crest is not None and seg.crest.unit == "ft"
    assert seg.crest.value == pytest.approx(crest)
    assert seg.hvtec is not None and seg.hvtec.crest == crest_time


def test_flw_header_segments_and_vtec(fixtures) -> None:
    (p,) = parse_afos((fixtures / "nws_afos/202512091701-KSEW-WGUS46-FLWSEW.txt").read_bytes())
    assert p.ttaaii == "WGUS46" and p.bbb is None
    assert p.mnd_time_raw == "901 AM PST Tue Dec 9 2025"
    assert [s.lid for s in p.segments] == ["MVEW1", "ARLW1"]
    mv = _segment(p, "MVEW1")
    (pv,) = mv.pvtec
    assert (pv.action, pv.office, pv.phenomenon, pv.significance, pv.etn) == ("NEW", "KSEW", "FL", "W", 42)
    assert pv.begin == datetime(2025, 12, 10, 1, 47, tzinfo=UTC) and pv.end is None  # 000000T0000Z
    assert (mv.hvtec.severity, mv.hvtec.cause, mv.hvtec.record) == ("3", "ER", "NO")
    assert [m.value for m in mv.crest_mentions] == [28.4, 26.1, 36.9]  # crest = MAX
    assert mv.flood_stage.value == 28.0 and mv.observed.value == 25.3  # log-only context
    arl = _segment(p, "ARLW1")
    assert arl.crest.value == 18.8 and arl.hvtec.crest == datetime(2025, 12, 11, 12, 0, tzinfo=UTC)


def test_flood_history_never_counts_as_crest(fixtures) -> None:
    (p,) = parse_afos((fixtures / "nws_afos/202512100124-KSEW-WGUS86-FLSSEW.txt").read_bytes())
    con = _segment(p, "CONW1")
    # "to a crest of 47.4 feet" is the forecast; the 45.7 ft Flood History line is not.
    assert [m.value for m in con.crest_mentions] == [47.4]
    assert "45.7" not in (con.forecast_text or "")
    mv = _segment(p, "MVEW1")
    assert [m.value for m in mv.crest_mentions] == [27.7, 26.7, 41.5]


def test_flow_defined_crest_in_cfs(fixtures) -> None:
    (p,) = parse_afos((fixtures / "nws_afos/202512091736-KSEW-WGUS46-FLWSEW.txt").read_bytes())
    aub = _segment(p, "AUBW1")
    assert aub.crest is not None and (aub.crest.value, aub.crest.unit) == (12828.6, "cfs")
    assert aub.hvtec.crest == datetime(2025, 12, 10, 0, 0, tzinfo=UTC)


def test_missing_hvtec_crest_time_is_none(fixtures) -> None:
    (p,) = parse_afos((fixtures / "nws_afos/202512160055-KSEW-WGUS86-FLSSEW.txt").read_bytes())
    rnt = _segment(p, "RNTW1")
    assert rnt.crest is not None and rnt.crest.value == 14.3
    assert rnt.hvtec.crest is None  # 000000T0000Z -> no crest time -> loader refuses the run


def test_forecast_bullet_without_crest_phrase_is_unknown(fixtures) -> None:
    (p,) = parse_afos((fixtures / "nws_afos/202512111817-KSEW-WGUS86-FLSSEW.txt").read_bytes())
    iss = _segment(p, "ISSW1")
    # "cresting now at around 2470 cfs" matches no to/of crest phrase: UNKNOWN, not 2470.
    assert iss.forecast_text is not None and iss.crest_mentions == () and iss.crest is None


def test_soh_concatenation_yields_multiple_products(fixtures) -> None:
    a = (fixtures / "nws_afos/202512091701-KSEW-WGUS46-FLWSEW.txt").read_bytes()
    b = (fixtures / "nws_afos/202512100124-KSEW-WGUS86-FLSSEW.txt").read_bytes()
    products = parse_afos(b"\x01" + a + b"\x03\x01" + b + b"\x03")
    assert [p.wmo_ddhhmm for p in products] == ["091701", "100124"]


def test_negative_fixtures(fixtures) -> None:
    (p,) = parse_afos((fixtures / "nws_afos/truncated.txt").read_bytes())
    assert p.segments == ()  # nothing parseable -> nothing fabricated
    with pytest.raises(AfosParseError, match="no WMO heading"):
        parse_afos((fixtures / "nws_afos/malformed_no_wmo.txt").read_bytes())
    with pytest.raises(AfosParseError, match="empty"):
        parse_afos(b"")
