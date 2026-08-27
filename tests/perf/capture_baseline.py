"""Capture the semantic + query baseline for `/viz/basins` and `/basins/{id}/state`.

    python -m tests.perf.capture_baseline                 # SQLite scratch DB, writes baseline/
    python -m tests.perf.capture_baseline --db "$URL"     # a migrated scratch PostgreSQL
    python -m tests.perf.capture_baseline --check         # re-measure, diff, write nothing

`--check` is the one to run after an optimisation: it ingests the same fixtures, calls the same
endpoints at the same knowledge time, and prints the query count beside a byte-for-byte diff of
the normalised bodies. A clean run is "N queries, body identical".

Everything written under `baseline/` is committed. It is evidence, not cache: the point of the
optimisation is that these files do not change.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

import httpx

from cascade_api.main import create_app
from cascade_core.db import make_engine
from cascade_core.settings import Settings

from tests.perf import normalize
from tests.perf.harness import AS_OF, BASELINE_DIR, SKAGIT, ingest, iso, settings_for
from tests.perf.instrument import QueryRecorder, attributed, table_of

#: The two endpoints the baseline covers, as (file stem, path, query parameters).
ENDPOINTS: tuple[tuple[str, str, dict[str, str]], ...] = (
    ("viz_basins", "/viz/basins", {"as_of": iso(AS_OF)}),
    ("basin_skagit_state", f"/basins/{SKAGIT}/state", {"as_of": iso(AS_OF)}),
)


async def measure(settings: Settings, path: str, params: dict[str, str]) -> tuple[dict, QueryRecorder]:
    """Call one endpoint against an ingested database, recording every statement it issues."""
    engine = make_engine(settings.db_url)
    recorder = QueryRecorder().attach(engine)
    try:
        app = create_app(settings, engine=engine)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://perf") as client:
            with attributed():
                recorder.clear()
                response = await client.get(path, params=params)
        if response.status_code != 200:
            raise SystemExit(f"{path} returned {response.status_code}: {response.text}")
        return response.json(), recorder
    finally:
        recorder.detach()
        await engine.dispose()


def query_report(recorder: QueryRecorder) -> dict:
    """The whole query picture for one request, in the shape the inventory is written from.

    Statement TEXTS are stored once in ``statement_texts`` and referenced by index everywhere
    else. There are only twelve of them behind 120 executions — writing each out 103 times would
    quadruple the file and bury the one number that matters in repetition of the other.
    """
    texts: dict[str, int] = {}

    def ref(statement: str) -> int:
        return texts.setdefault(statement, len(texts))

    distinct = [
        {
            "occurrences": count,
            "table": table_of(rep.statement),
            "reader": rep.reader,
            "call_sites": list(sites),
            "statement_ref": ref(rep.statement),
            "parameters": rep.parameters,
            # Three frames, not the whole chain: enough to reach the ORIGINATING module, which is
            # the fact `call_sites` alone loses. Every `latest_derived_feature` read is issued
            # from knowledge.py:220; only the frame beneath it says whether that was
            # susceptibility's percentile, its SWE context or its precipitation context.
            "stack": list(rep.stack[:3]),
        }
        for rep, count, sites in recorder.by_identity()
    ]
    return {
        "total_queries": recorder.total,
        "distinct_queries": recorder.distinct,
        "exact_repeats": recorder.exact_repeats,
        "distinct_statement_texts": len(texts),
        "sql_wall_ms": round(recorder.total_ms(), 2),
        "by_table": dict(recorder.by_table().most_common()),
        "by_call_site": dict(recorder.by_call_site().most_common()),
        "statement_texts": [text for text, _ in sorted(texts.items(), key=lambda kv: kv[1])],
        "distinct_statements": distinct,
        "in_order": [
            {
                "n": i + 1,
                "reader": r.reader,
                "call_site": r.call_site,
                "table": table_of(r.statement),
                "statement_ref": ref(r.statement),
                "parameters": r.parameters,
                "duration_ms": round(r.duration_ms, 3),
            }
            for i, r in enumerate(recorder.records)
        ],
    }


async def run(settings: Settings, *, check: bool, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    summary: dict[str, dict] = {}

    for stem, path, params in ENDPOINTS:
        body, recorder = await measure(settings, path, params)
        canonical = normalize.canonical_json(body)
        report = query_report(recorder)
        summary[stem] = {
            "path": path,
            "params": params,
            "total_queries": report["total_queries"],
            "distinct_queries": report["distinct_queries"],
            "exact_repeats": report["exact_repeats"],
            "sql_wall_ms": report["sql_wall_ms"],
        }
        body_path = out_dir / f"{stem}.json"
        queries_path = out_dir / f"{stem}.queries.json"

        print(
            f"{path:34s} {report['total_queries']:4d} queries "
            f"({report['distinct_queries']} distinct, {report['exact_repeats']} exact repeats), "
            f"{report['sql_wall_ms']:.1f} ms in SQL"
        )

        if check:
            if not body_path.exists():
                print(f"  no baseline at {body_path}; run without --check first")
                failures += 1
                continue
            baseline_body = json.loads(body_path.read_text())
            differences = normalize.diff(baseline_body, body)
            if differences:
                failures += 1
                print(f"  SEMANTIC DIFF against the baseline ({len(differences)}):")
                for line in differences[:40]:
                    print(f"    {line}")
                if len(differences) > 40:
                    print(f"    ... and {len(differences) - 40} more")
            else:
                byte_identical = canonical == normalize.canonical_json(baseline_body)
                print(f"  body identical to the baseline (byte-for-byte normalised: {byte_identical})")
        else:
            body_path.write_text(json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            (out_dir / f"{stem}.read_time_fields.json").write_text(
                json.dumps(normalize.read_time_values(body), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            )
            queries_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if not check:
        (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=None, help="an already-migrated scratch database URL (default: a temporary SQLite file)")
    parser.add_argument("--check", action="store_true", help="compare against the stored baseline instead of writing it")
    parser.add_argument("--out", default=str(BASELINE_DIR), help="where the baseline lives")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="cascade-perf-") as tmp:
        settings = ingest(settings_for(Path(tmp), db_url=args.db))
        return asyncio.run(run(settings, check=args.check, out_dir=Path(args.out)))


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
