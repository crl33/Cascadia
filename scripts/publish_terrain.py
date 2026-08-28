"""Publish a built quantized-mesh pyramid to R2 and put a public domain in front of it.

ADR-0021 §2: the terrain lives in its own DEDICATED bucket (never the raw archive — that one
must stay private), uploaded with the headers quantized-mesh serving requires (`ctb-tile -C`
gzips every .terrain, so Content-Encoding must say so or Cesium reads compressed bytes as
mesh), fronted by R2's managed public domain. Everything here is public-domain USGS 3DEP
derivative — publishing tiles, not data anyone owns.

Credentials come only from the environment (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`,
`R2_S3_ENDPOINT`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` — the deployment env
files); nothing is echoed and nothing lands in the repo.

Usage: .venv/bin/python scripts/publish_terrain.py <tiles-dir> [--bucket cascadia-terrain] [--prefix terrain/v1]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import urllib.request
from pathlib import Path

CF_API = "https://api.cloudflare.com/client/v4"


def cf(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{CF_API}{path}",
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def ensure_bucket(account: str, bucket: str) -> None:
    out = cf("POST", f"/accounts/{account}/r2/buckets", {"name": bucket})
    if out.get("success"):
        print(f"bucket {bucket}: created")
        return
    errors = {e.get("code") for e in out.get("errors", ())}
    if 10004 in errors:  # already exists
        print(f"bucket {bucket}: exists")
        return
    raise RuntimeError(f"bucket create failed: {out.get('errors')}")


def ensure_public_domain(account: str, bucket: str) -> str:
    out = cf("PUT", f"/accounts/{account}/r2/buckets/{bucket}/domains/managed", {"enabled": True})
    if not out.get("success"):
        raise RuntimeError(f"managed domain enable failed: {out.get('errors')}")
    domain = out["result"]["domain"]
    print(f"public domain: https://{domain}")
    return domain


def upload(tiles: Path, bucket: str, prefix: str) -> int:
    import obstore
    from obstore.store import S3Store

    store = S3Store(
        bucket=bucket,
        endpoint=os.environ["R2_S3_ENDPOINT"],
        region="auto",
        virtual_hosted_style_request=False,
    )
    files = sorted(p for p in tiles.rglob("*") if p.is_file())

    def put(path: Path) -> str:
        key = f"{prefix}/{path.relative_to(tiles).as_posix()}"
        attributes = {"Cache-Control": "public, max-age=31536000, immutable"}
        if path.suffix == ".terrain":
            attributes["Content-Type"] = "application/vnd.quantized-mesh"
            attributes["Content-Encoding"] = "gzip"  # ctb -C gzipped every tile
        elif path.name == "layer.json":
            attributes["Content-Type"] = "application/json"
        obstore.put(store, key, path.read_bytes(), attributes=attributes, use_multipart=False)
        return key

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for _key in pool.map(put, files):
            done += 1
            if done % 500 == 0:
                print(f"  {done}/{len(files)} uploaded")
    print(f"uploaded {done} objects to {bucket}/{prefix}")
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tiles", type=Path)
    parser.add_argument("--bucket", default="cascadia-terrain")
    parser.add_argument("--prefix", default="terrain/v1")
    args = parser.parse_args()
    if not (args.tiles / "layer.json").is_file():
        print(f"{args.tiles} has no layer.json — not a finished pyramid", file=sys.stderr)
        return 2
    account = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    ensure_bucket(account, args.bucket)
    upload(args.tiles, args.bucket, args.prefix)
    domain = ensure_public_domain(account, args.bucket)
    print(f"terrain root: https://{domain}/{args.prefix}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
