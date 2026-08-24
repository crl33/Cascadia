"""Verify Dec 1-22 2025 operational NWM products remain retrievable from the long-term
Google Cloud and Azure NWM archives, against the AWS manifest of record.

Read-only. Produces docs/research/nwm-alternate-archives-<date>.json:
- GCS (gs://national-water-model): per-day, per-product file-count + byte sums for every
  Event Zero-relevant product incl. medium_range_mem2..7, diffed against the AWS manifest.
- Azure (https://noaanwm.blob.core.windows.net/nwm): full sums for 3 sample days + object
  spot checks.
- Retrieval tests: first-KB content equality AWS vs GCS vs Azure for sample objects.
"""
from __future__ import annotations
import datetime as dt, json, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

UA={"User-Agent":"CascadiaPapsukkal/0.1 (event-zero archive verification; read-only)"}
PRODUCTS=["analysis_assim","analysis_assim_extend","short_range","medium_range_blend"]+[f"medium_range_mem{i}" for i in range(1,8)]+["usgs_timeslices"]
DAYS=[(dt.date(2025,12,1)+dt.timedelta(days=i)).strftime("%Y%m%d") for i in range(22)]

def http(url, rng=None, attempts=4):
    h=dict(UA)
    if rng: h["Range"]=rng
    for a in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=90) as r:
                return r.read()
        except Exception:
            if a==attempts-1: raise
            time.sleep(2**a)

def gcs_sum(prefix):
    base="https://storage.googleapis.com/storage/v1/b/national-water-model/o"
    tok=None; f=b=0
    while True:
        q={"prefix":prefix,"maxResults":"1000","fields":"items(name,size),nextPageToken"}
        if tok: q["pageToken"]=tok
        j=json.loads(http(base+"?"+urllib.parse.urlencode(q)))
        for it in j.get("items",[]): f+=1; b+=int(it["size"])
        tok=j.get("nextPageToken")
        if not tok: return f,b

def azure_sum(prefix):
    f=b=0; marker=None
    while True:
        q={"restype":"container","comp":"list","prefix":prefix,"maxresults":"1000"}
        if marker: q["marker"]=marker
        root=ET.fromstring(http("https://noaanwm.blob.core.windows.net/nwm?"+urllib.parse.urlencode(q)))
        for bl in root.iter("Blob"):
            f+=1; b+=int(bl.find("Properties/Content-Length").text)
        nm=root.findtext("NextMarker")
        if not nm: return f,b
        marker=nm

def main():
    aws=json.load(open("docs/research/nwm-survival-inventory-2026-08-24.json"))
    out={"generated_at":dt.datetime.now(dt.UTC).isoformat(),
         "gcs":{"base":"https://storage.googleapis.com/national-water-model/","days":{},"mismatches":[]},
         "azure":{"base":"https://noaanwm.blob.core.windows.net/nwm/","sample_days":{},"mismatches":[]},
         "content_checks":[]}
    for day in DAYS:
        d={}
        for p in PRODUCTS:
            f,b=gcs_sum(f"nwm.{day}/{p}/")
            ref=aws["days"].get(day,{}).get(p,{})
            match=(f==ref.get("files") and b==ref.get("bytes"))
            d[p]={"files":f,"bytes":b,"matches_aws":match}
            if not match: out["gcs"]["mismatches"].append({"day":day,"product":p,"gcs":[f,b],"aws":[ref.get("files"),ref.get("bytes")]})
        out["gcs"]["days"][day]=d
        print(f"GCS {day}: {sum(v['files'] for v in d.values())} files, mismatches so far {len(out['gcs']['mismatches'])}", flush=True)
        json.dump(out, open("docs/research/nwm-alternate-archives-2026-08-24.json","w"), indent=1)
    for day in ("20251201","20251212","20251222"):
        d={}
        for p in PRODUCTS:
            f,b=azure_sum(f"nwm.{day}/{p}/")
            ref=aws["days"].get(day,{}).get(p,{})
            match=(f==ref.get("files") and b==ref.get("bytes"))
            d[p]={"files":f,"bytes":b,"matches_aws":match}
            if not match: out["azure"]["mismatches"].append({"day":day,"product":p,"azure":[f,b],"aws":[ref.get("files"),ref.get("bytes")]})
        out["azure"]["sample_days"][day]=d
        print(f"Azure {day}: {sum(v['files'] for v in d.values())} files, mismatches {len(out['azure']['mismatches'])}", flush=True)
    samples=[
        "nwm.20251212/medium_range_mem2/nwm.t00z.medium_range.channel_rt_2.f003.conus.nc",
        "nwm.20251212/medium_range_mem7/nwm.t12z.medium_range.channel_rt_7.f003.conus.nc",
        "nwm.20251210/analysis_assim/nwm.t12z.analysis_assim.channel_rt.tm00.conus.nc",
        "nwm.20251222/short_range/nwm.t23z.short_range.channel_rt.f001.conus.nc",
    ]
    for key in samples:
        a=http(f"https://noaa-nwm-pds.s3.amazonaws.com/{key}", rng="bytes=0-1023")
        g=http(f"https://storage.googleapis.com/national-water-model/{key}", rng="bytes=0-1023")
        z=http(f"https://noaanwm.blob.core.windows.net/nwm/{key}", rng="bytes=0-1023")
        out["content_checks"].append({"key":key,"gcs_equal_aws":a==g,"azure_equal_aws":a==z})
        print(f"content {key.split('/')[1]}: gcs={a==g} azure={a==z}", flush=True)
    json.dump(out, open("docs/research/nwm-alternate-archives-2026-08-24.json","w"), indent=1)
    total_mm=len(out["gcs"]["mismatches"])+len(out["azure"]["mismatches"])
    bad=[c for c in out["content_checks"] if not (c["gcs_equal_aws"] and c["azure_equal_aws"])]
    print(f"VERDICT: total_mismatches={total_mm} gcs_mismatches={len(out['gcs']['mismatches'])} azure_sample_mismatches={len(out['azure']['mismatches'])} content_failures={len(bad)}", flush=True)

if __name__=="__main__":
    main()
