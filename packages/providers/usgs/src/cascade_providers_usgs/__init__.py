"""cascade_providers_usgs — USGS NWIS instantaneous values (stage 00065 ft, discharge 00060 ft3/s).

Owns the one outbound URL for this source, the strict parser, the normalization into
Observation rows (sentinels/qualifiers -> quality flags), the idempotent 15-minute job, and a
live canary. Nothing here computes features.
"""
