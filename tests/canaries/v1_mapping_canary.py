"""Live canary: verify V1's USGS sites, NWPS LIDs and SNOTEL mappings against the real APIs.
Read-only GETs. Prints a compact JSON report. Network failures are reported, not hidden."""
import json, sys, urllib.request, urllib.parse, datetime as dt
UA = {"User-Agent": "CascadeOracle-V2-audit/0.1 (architecture verification)", "Accept": "application/json"}
def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")
report = {"run_at": dt.datetime.now(dt.timezone.utc).isoformat(), "usgs": {}, "nwps": {}, "awdb": {}, "new_usgs_api": {}, "errors": []}
stations = [("cedar-renton","12119000","RNTW1"),("snoqualmie-carnation","12149000","CRNW1"),("skagit-mt-vernon","12200500","MVEW1"),("nooksack-ferndale","12213100","NKSW1"),("green-auburn","12113000","AUBW1"),("white-auburn","12100490","WRAW1")]
# USGS site names (legacy NWIS site service, RDB)
try:
    sites = ",".join(s[1] for s in stations)
    st, body = get(f"https://waterservices.usgs.gov/nwis/site/?format=rdb&sites={sites}&siteOutput=expanded")
    for line in body.splitlines():
        if line.startswith("#") or line.startswith("agency_cd") or line.startswith("5s"): continue
        cols = line.split("\t")
        if len(cols) > 3: report["usgs"][cols[1]] = {"name": cols[2], "lat": cols[4] if len(cols)>4 else None, "lon": cols[5] if len(cols)>5 else None, "alt_datum": cols[10] if len(cols)>10 else None, "huc": cols[11] if len(cols)>11 else None}
except Exception as e: report["errors"].append(f"usgs site: {e}")
# USGS IV latest values + qualifiers
try:
    st, body = get(f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={sites}&parameterCd=00065,00060&siteStatus=all")
    j = json.loads(body)
    for ts in j.get("value",{}).get("timeSeries",[]):
        site = ts["sourceInfo"]["siteCode"][0]["value"]; code = ts["variable"]["variableCode"][0]["value"]
        vals = ts.get("values",[{}])[0].get("value",[])
        last = vals[-1] if vals else None
        quals = [q.get("qualifierCode") for q in ts.get("values",[{}])[0].get("qualifier",[])]
        report["usgs"].setdefault(site,{}).setdefault("iv",{})[code] = {"latest": last, "qualifiers_defined": quals, "noDataValue": ts["variable"].get("noDataValue")}
except Exception as e: report["errors"].append(f"usgs iv: {e}")
# New USGS Water Data API (OGC) existence
for url in ["https://api.waterdata.usgs.gov/ogcapi/v0/", "https://api.waterdata.usgs.gov/ogcapi/v0/collections"]:
    try:
        st, body = get(url)
        j = json.loads(body)
        report["new_usgs_api"][url] = {"status": st, "collections": [c.get("id") for c in j.get("collections",[])][:40] if "collections" in j else list(j.keys())[:10]}
    except Exception as e: report["new_usgs_api"][url] = f"ERR {e}"
# NWPS gauges: name, flood categories, datum, forecast availability
for sid, usgs, lid in stations:
    entry = {}
    try:
        st, body = get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}")
        j = json.loads(body)
        entry["name"] = j.get("name"); entry["usgsId"] = j.get("usgsId"); entry["rfc"] = j.get("rfc",{}).get("abbreviation") if isinstance(j.get("rfc"),dict) else j.get("rfc")
        entry["wfo"] = j.get("wfo",{}).get("abbreviation") if isinstance(j.get("wfo"),dict) else j.get("wfo")
        entry["datums"] = j.get("datums"); entry["flood_categories"] = j.get("flood",{}).get("categories"); entry["flood_keys"] = list(j.get("flood",{}).keys()) if isinstance(j.get("flood"),dict) else None
        entry["status_keys"] = list(j.get("status",{}).keys()) if isinstance(j.get("status"),dict) else None
        entry["top_keys"] = list(j.keys())
        entry["forecast_type"] = (j.get("forecast") or {}).get("type") if isinstance(j.get("forecast"),dict) else None
    except Exception as e: entry["error"] = str(e)
    try:
        st, body = get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}/stageflow")
        j = json.loads(body)
        obs = j.get("observed",{}); fc = j.get("forecast",{})
        entry["stageflow"] = {"observed_points": len(obs.get("data",[])), "observed_primary": obs.get("primaryName"), "observed_units": obs.get("primaryUnits"),
                              "forecast_points": len(fc.get("data",[])), "forecast_issued": fc.get("issuedTime"), "forecast_keys": list(fc.keys())[:12], "top_keys": list(j.keys())}
    except Exception as e: entry["stageflow_error"] = str(e)
    report["nwps"][lid] = entry
# AWDB station metadata for V1 SNOTEL triplets
try:
    trips = "911:WA:SNTL,908:WA:SNTL,515:WA:SNTL,1011:WA:SNTL,1068:WA:SNTL,1085:WA:SNTL"
    st, body = get(f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?stationTriplets={urllib.parse.quote(trips)}")
    for s in json.loads(body):
        report["awdb"][s.get("stationTriplet")] = {k: s.get(k) for k in ("name","huc","latitude","longitude","elevation","county","beginDate","endDate","dataTimeZone","networkCode")}
except Exception as e: report["errors"].append(f"awdb stations: {e}")
# AWDB reference: elements available & whether centralTendency endpoint exists
for url in ["https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/reference-data?referenceLists=elements",
            "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data?stationTriplets=515:WA:SNTL&elements=WTEQ&duration=DAILY&beginDate=2025-12-01&endDate=2025-12-15&centralTendencyType=MEDIAN&returnFlags=true"]:
    try:
        st, body = get(url); j = json.loads(body)
        if "reference-data" in url:
            els = j.get("elements",[]) if isinstance(j,dict) else []
            report["awdb"]["elements_sample"] = [e.get("code") for e in els if e.get("code") in ("WTEQ","SNWD","PREC","PRCP","TOBS","TAVG","SMS","STO","PRCPSA","WTEQX")]
        else:
            report["awdb"]["dec2025_wteq_harts_pass"] = j[0].get("data",[{}])[0].get("values",[])[:16] if j else j
    except Exception as e: report["awdb"][url[:60]] = f"ERR {e}"
print(json.dumps(report, indent=1, default=str))
