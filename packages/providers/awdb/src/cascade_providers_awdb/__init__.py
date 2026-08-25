"""NRCS AWDB (SNOTEL) adapter — CONTEXT ONLY.

`HYDROLOGY.md` §7 is the reason this package exists in the shape it does: **more snow-water
equivalent is not more flood risk.** Deep snow at 5,000 ft with a cold column is a water-supply
statement; the same SWE under a warm atmospheric river with a 2,500 m snow level is a different
story entirely, and nothing in v0 can tell those apart (that needs hypsometry and snow-covered
area, neither of which is ingested). So every number this package produces is emitted as a
driver with ``direction="context_not_scored"``, contributes zero to the susceptibility index,
and is labeled as a POINT-NETWORK statistic — SNOTEL sites sit at 2,250–6,490 ft and are not a
basin mean of anything.

Soil moisture (`SMS`) is fetched by the canary and by nothing else: it has no median, uneven
depths and `no profile` quality flags, and cannot support a percentile
(docs/research/p3-surfaces-design-2026-08-24.md §2.1). Soil stays UNKNOWN with that reason.
"""
