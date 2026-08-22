"""cascade_providers_nwps — NOAA National Water Prediction Service v1.

Owns gauge metadata (datums, topology, reach id, official flood categories in stage OR flow),
official NWRFC forecasts from /stageflow (kcfs -> cfs explicitly), the idempotent jobs for both,
and a live canary. Observed series are parsed (for tests and canaries) but not stored: USGS is
the observation source of record in the spike.
"""
