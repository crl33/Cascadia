"""Archive the Event Zero NWS text-product record (T2) from the IEM AFOS archive into R2.

Fetches every product issuance for the seven KSEW PILs (ESFSEW FFASEW FLWSEW FLSSEW
FFWSEW AFDSEW PNSSEW) over 2025-12-01T00:00Z..2025-12-23T00:00Z (end exclusive) from the
Iowa Environmental Mesonet, plus the VTEC watch/warning event listing for WFO SEW
(docs/EVENT_ZERO.md section 8 row T2; sources S4/S5), and copies the raw bytes into the
cascadia-event-zero R2 bucket:

    afos/{PIL}/{YYYYMMDDHHMM}-{n}.txt      one object per product issuance (n: same-minute seq)
    afos/_vtec/vtec_events_SEW_2025.json   raw VTEC year listing (window counts go in manifest)
    _manifest/afos/{PIL}.json              issued_at / bytes / source_url / sha256 per object
    _manifest/afos/_vtec.json

Listing comes from /api/1/nws/afos/list.json, one call per UTC day per PIL -- the list API
is day-granular, which is its pagination. Raw text comes from /api/1/nwstext/{product_id}
(with ?nolimit=1 when the listing reports >1 product stored at the same id, so every byte
is captured). Gentle by design: sequential requests, a short pause after each, User-Agent
CascadiaPapsukkal/0.1. Idempotent: objects already in R2 are skipped and their existing
manifest entries preserved; source bytes are immutable at IEM.

Credentials: upload mode reads ONLY environment variables -- R2_S3_ENDPOINT plus the
standard AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY that obstore's S3Store picks up from
the environment. This script never reads any credential file. --dry-run needs no
credentials and writes nothing: it fetches everything and prints per-PIL product counts
and byte totals.

Usage: python scripts/archive_afos_event_zero.py [--dry-run]
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, time, urllib.parse, urllib.request

API = "https://mesonet.agron.iastate.edu"
PILS = ("ESFSEW", "FFASEW", "FLWSEW", "FLSSEW", "FFWSEW", "AFDSEW", "PNSSEW")
UTC = dt.timezone.utc
WINDOW_START = dt.datetime(2025, 12, 1, tzinfo=UTC)
WINDOW_END = dt.datetime(2025, 12, 23, tzinfo=UTC)  # exclusive
VTEC_URL = f"{API}/json/vtec_events.py?wfo=SEW&year=2025"
VTEC_KEY = "afos/_vtec/vtec_events_SEW_2025.json"
BUCKET = "cascadia-event-zero"
UA = {"User-Agent": "CascadiaPapsukkal/0.1 (event-zero AFOS archive)"}
PAUSE_S = 0.3


def fetch(url: str, timeout: int = 120) -> bytes:
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            data = urllib.request.urlopen(req, timeout=timeout).read()
            time.sleep(PAUSE_S)  # be gentle: sequential + pause
            return data
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def parse_z(ts: str) -> dt.datetime:
    return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def list_products(pil: str) -> list[dict]:
    """One row per product issuance for pil inside the window, deduped by product_id,
    ordered by issuance, with R2 keys afos/{pil}/{YYYYMMDDHHMM}-{n}.txt assigned."""
    rows: list[dict] = []
    seen: set[str] = set()
    day = WINDOW_START.date()
    while day < WINDOW_END.date():
        q = urllib.parse.urlencode({"pil": pil, "date": day.isoformat()})
        payload = json.loads(fetch(f"{API}/api/1/nws/afos/list.json?{q}"))
        for row in payload.get("data") or []:
            pid = row["product_id"]
            if pid in seen or not (WINDOW_START <= parse_z(row["entered"]) < WINDOW_END):
                continue
            seen.add(pid)
            src = row["text_link"]
            if int(row.get("count") or 1) > 1:
                src += "?nolimit=1"  # capture every product stored at this id
            rows.append({"product_id": pid, "issued_at": row["entered"], "source_url": src})
        day += dt.timedelta(days=1)
    rows.sort(key=lambda r: (r["issued_at"], r["product_id"]))
    per_minute: dict[str, int] = {}
    for r in rows:
        ts = r["issued_at"][:16].replace("-", "").replace(":", "").replace("T", "")
        n = per_minute.get(ts, 0)
        per_minute[ts] = n + 1
        r["key"] = f"afos/{pil}/{ts}-{n}.txt"
    return rows


def vtec_window_count(payload: dict) -> int:
    n = 0
    for ev in payload.get("events") or []:
        try:
            issued = parse_z(ev.get("product_issue") or ev.get("issue") or "")
        except ValueError:
            continue
        if WINDOW_START <= issued < WINDOW_END:
            n += 1
    return n


# --- upload mode (obstore imported lazily so --dry-run has no R2/credential surface) ---

def open_store():
    from obstore.store import S3Store
    return S3Store(bucket=BUCKET, endpoint=os.environ["R2_S3_ENDPOINT"], region="auto")


def exists(store, key: str) -> bool:
    import obstore
    try:
        obstore.head(store, key)
        return True
    except Exception:
        return False


def load_manifest(store, key: str) -> dict:
    import obstore
    try:
        return json.loads(bytes(obstore.get(store, key).bytes()))
    except Exception:
        return {}


def put_json(store, key: str, obj: dict) -> None:
    import obstore
    obstore.put(store, key, json.dumps(obj, sort_keys=True, indent=1).encode(), mode="overwrite")


def archive_pil(store, pil: str) -> int:
    import obstore
    rows = list_products(pil)
    mkey = f"_manifest/afos/{pil}.json"
    manifest = load_manifest(store, mkey)
    new = skipped = nbytes = 0
    for r in rows:
        if r["key"] in manifest and exists(store, r["key"]):
            skipped += 1
            continue
        data = fetch(r["source_url"])
        obstore.put(store, r["key"], data, mode="overwrite")  # source bytes immutable at IEM
        manifest[r["key"]] = {
            "pil": pil, "product_id": r["product_id"], "issued_at": r["issued_at"],
            "bytes": len(data), "source_url": r["source_url"],
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        new += 1
        nbytes += len(data)
    put_json(store, mkey, manifest)
    print(f"{pil}: {len(rows)} products, {new} uploaded ({nbytes} bytes), {skipped} already archived", flush=True)
    return len(rows)


def archive_vtec(store) -> None:
    import obstore
    data = fetch(VTEC_URL)
    payload = json.loads(data)
    total = len(payload.get("events") or [])
    in_window = vtec_window_count(payload)
    mkey = "_manifest/afos/_vtec.json"
    manifest = load_manifest(store, mkey)
    if VTEC_KEY in manifest and exists(store, VTEC_KEY):
        print(f"_vtec: already archived ({manifest[VTEC_KEY]['bytes']} bytes); "
              f"listing now reports {total} events, {in_window} in window", flush=True)
        return
    obstore.put(store, VTEC_KEY, data, mode="overwrite")
    manifest[VTEC_KEY] = {
        "wfo": "SEW", "year": 2025,
        "fetched_at": dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bytes": len(data), "source_url": VTEC_URL,
        "sha256": hashlib.sha256(data).hexdigest(),
        "events_total": total, "events_in_window": in_window,
        "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
    }
    put_json(store, mkey, manifest)
    print(f"_vtec: uploaded {len(data)} bytes, {total} events ({in_window} in window)", flush=True)


def dry_run() -> None:
    grand_n = grand_b = 0
    for pil in PILS:
        rows = list_products(pil)
        pil_b = sum(len(fetch(r["source_url"])) for r in rows)
        print(f"{pil}: {len(rows)} products, {pil_b} bytes", flush=True)
        grand_n += len(rows)
        grand_b += pil_b
    data = fetch(VTEC_URL)
    payload = json.loads(data)
    print(f"_vtec: {len(payload.get('events') or [])} events "
          f"({vtec_window_count(payload)} in window), {len(data)} bytes", flush=True)
    print(f"DRY RUN TOTAL: {grand_n} products, {grand_b} bytes ({grand_b / 1e6:.2f} MB) "
          f"+ VTEC {len(data)} bytes; nothing written", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="fetch and count only; no R2 access, nothing written")
    args = ap.parse_args()
    if args.dry_run:
        dry_run()
        return
    store = open_store()
    total = sum(archive_pil(store, pil) for pil in PILS)
    archive_vtec(store)
    print(f"DONE: {total} products across {len(PILS)} PILs + VTEC listing", flush=True)


if __name__ == "__main__":
    main()
