"""Copy a set of noaa-nwm-pds prefixes into the cascadia-event-zero R2 bucket, resumably.

Free-tier-conscious: run only for prefixes the budget allows (usgs_timeslices now; larger
tiers only after explicit owner approval - see research/nwm-survival-inventory-2026-08-24.md).
Skips objects that already exist (content is immutable at source), writes a per-prefix
manifest under _manifest/ capturing size/LastModified/ETag so available_at survives the copy.

Usage: python scripts/pump_event_zero_prefix.py <subdir> <startYYYYMMDD> <endYYYYMMDD> [workers]
Example: python scripts/pump_event_zero_prefix.py usgs_timeslices 20251201 20251222 6
"""
from __future__ import annotations
import datetime as dt, json, os, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from obstore.store import S3Store
import obstore

SRC = "https://noaa-nwm-pds.s3.amazonaws.com"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
UA = {"User-Agent": "CascadiaPapsukkal/0.1 (event-zero archive pump)"}

def list_keys(prefix: str):
    token = None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token: q["continuation-token"] = token
        req = urllib.request.Request(SRC + "/?" + urllib.parse.urlencode(q), headers=UA)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=60).read())
        for c in root.findall("s3:Contents", NS):
            yield (c.findtext("s3:Key", "", NS), int(c.findtext("s3:Size", "0", NS)),
                   c.findtext("s3:LastModified", "", NS), c.findtext("s3:ETag", "", NS).strip('"'))
        if root.findtext("s3:IsTruncated", "false", NS) != "true": return
        token = root.findtext("s3:NextContinuationToken", None, NS)

def copy_one(store, row):
    key, size, lm, etag = row
    try:
        obstore.head(store, key); return 0  # already archived
    except Exception: pass
    for attempt in range(5):
        try:
            req = urllib.request.Request(f"{SRC}/{urllib.parse.quote(key)}", headers=UA)
            data = urllib.request.urlopen(req, timeout=300).read()
            if len(data) != size: raise IOError(f"size mismatch {len(data)}!={size}")
            obstore.put(store, key, data, mode="overwrite")  # same-source bytes; overwrite==idempotent
            return len(data)
        except Exception as e:
            if attempt == 4: print(f"FAILED {key}: {e}", flush=True); return -1
            time.sleep(2 ** attempt)

def main():
    sub, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    store = S3Store(bucket="cascadia-event-zero", endpoint=os.environ["R2_S3_ENDPOINT"], region="auto")
    d0, d1 = (dt.datetime.strptime(x, "%Y%m%d").date() for x in (start, end))
    days = [(d0 + dt.timedelta(days=i)).strftime("%Y%m%d") for i in range((d1 - d0).days + 1)]
    total_b = total_f = failed = 0
    for day in days:
        prefix = f"nwm.{day}/{sub}/"
        rows = list(list_keys(prefix))
        manifest = {k: {"size": s, "last_modified": lm, "etag": e} for k, s, lm, e in rows}
        obstore.put(store, f"_manifest/{sub}/{day}.json", json.dumps(manifest).encode(), mode="overwrite")
        with ThreadPoolExecutor(workers) as ex:
            for r in ex.map(lambda row: copy_one(store, row), rows):
                if r == -1: failed += 1
                elif r > 0: total_b += r; total_f += 1
        print(f"{day}: {len(rows)} listed, cumulative copied {total_f} files {total_b/1e9:.2f} GB, failed {failed}", flush=True)
    print(f"DONE {sub}: {total_f} new files, {total_b/1e9:.2f} GB, {failed} failures", flush=True)

if __name__ == "__main__":
    main()
