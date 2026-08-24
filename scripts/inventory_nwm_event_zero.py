"""Inventory surviving NWM operational outputs for Event Zero (Dec 2025) on noaa-nwm-pds.

Read-only: anonymous S3 ListObjectsV2 over the operational bucket. Produces a manifest
(JSON) with per-day, per-product file counts, byte totals, LastModified ranges, and a
kind breakdown (channel_rt / land / reservoir / terrain_rt / forcing / other), so the
bulk-copy decision can be made on real numbers before anything is copied.

Usage: python scripts/inventory_nwm_event_zero.py [start YYYYMMDD] [end YYYYMMDD] [out.json]
Defaults: 20251201 20251222 docs/research/nwm-survival-inventory-<today>.json
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BUCKET = "https://noaa-nwm-pds.s3.amazonaws.com"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
UA = {"User-Agent": "CascadiaPapsukkal/0.1 (event-zero archive inventory; read-only)"}


def _get(params: dict[str, str], attempts: int = 5) -> ET.Element:
    url = BUCKET + "/?" + urllib.parse.urlencode(params)
    last: Exception | None = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return ET.fromstring(r.read())
        except Exception as e:  # noqa: BLE001 - retry any transport error
            last = e
            time.sleep(2**i)
    raise RuntimeError(f"listing failed after {attempts} attempts: {url}") from last


def list_common_prefixes(prefix: str) -> list[str]:
    root = _get({"list-type": "2", "prefix": prefix, "delimiter": "/", "max-keys": "1000"})
    return [e.findtext("s3:Prefix", "", NS) for e in root.findall("s3:CommonPrefixes", NS)]


def kind_of(key: str) -> str:
    name = key.rsplit("/", 1)[-1]
    for k in ("channel_rt", "land", "reservoir", "terrain_rt", "forcing"):
        if k in name:
            return k
    return "other"


def sum_prefix(prefix: str) -> dict:
    token: str | None = None
    out: dict = {"files": 0, "bytes": 0, "kinds": {}, "last_modified_min": None, "last_modified_max": None}
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            params["continuation-token"] = token
        root = _get(params)
        for c in root.findall("s3:Contents", NS):
            key = c.findtext("s3:Key", "", NS)
            size = int(c.findtext("s3:Size", "0", NS))
            lm = c.findtext("s3:LastModified", "", NS)
            out["files"] += 1
            out["bytes"] += size
            k = out["kinds"].setdefault(kind_of(key), {"files": 0, "bytes": 0})
            k["files"] += 1
            k["bytes"] += size
            if lm:
                if out["last_modified_min"] is None or lm < out["last_modified_min"]:
                    out["last_modified_min"] = lm
                if out["last_modified_max"] is None or lm > out["last_modified_max"]:
                    out["last_modified_max"] = lm
        if root.findtext("s3:IsTruncated", "false", NS) != "true":
            return out
        token = root.findtext("s3:NextContinuationToken", None, NS)


def main() -> None:
    start = sys.argv[1] if len(sys.argv) > 1 else "20251201"
    end = sys.argv[2] if len(sys.argv) > 2 else "20251222"
    today = dt.date.today().isoformat()
    out_path = sys.argv[3] if len(sys.argv) > 3 else f"docs/research/nwm-survival-inventory-{today}.json"

    d0 = dt.datetime.strptime(start, "%Y%m%d").date()
    d1 = dt.datetime.strptime(end, "%Y%m%d").date()
    days = [(d0 + dt.timedelta(days=i)).strftime("%Y%m%d") for i in range((d1 - d0).days + 1)]

    manifest: dict = {
        "bucket": "noaa-nwm-pds",
        "purpose": "Event Zero (Dec 2025) survival inventory before any bulk copy (docs/EVENT_ZERO.md S8 T6)",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window": {"start": start, "end": end},
        "days": {},
        "totals": {"files": 0, "bytes": 0, "by_product": {}},
        "days_missing_entirely": [],
    }
    for day in days:
        day_prefix = f"nwm.{day}/"
        subdirs = list_common_prefixes(day_prefix)
        if not subdirs:
            manifest["days_missing_entirely"].append(day)
            print(f"{day}: MISSING", flush=True)
            continue
        day_entry: dict = {}
        for sub in subdirs:
            product = sub[len(day_prefix) :].strip("/")
            s = sum_prefix(sub)
            day_entry[product] = s
            manifest["totals"]["files"] += s["files"]
            manifest["totals"]["bytes"] += s["bytes"]
            p = manifest["totals"]["by_product"].setdefault(product, {"files": 0, "bytes": 0, "days": 0})
            p["files"] += s["files"]
            p["bytes"] += s["bytes"]
            p["days"] += 1
        manifest["days"][day] = day_entry
        gb = sum(v["bytes"] for v in day_entry.values()) / 1e9
        print(f"{day}: {len(day_entry)} products, {sum(v['files'] for v in day_entry.values())} files, {gb:.1f} GB", flush=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)  # checkpoint after every day

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(f"TOTAL: {manifest['totals']['files']} files, {manifest['totals']['bytes']/1e12:.2f} TB -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
