import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";

export const PHASES = [
    {
        n: 1,
        title: "Beautiful Real-Data MVP",
        status: "current",
        summary:
            "Cinematic command-center dashboard with live USGS gauge data and NWPS flood stages for 6 Washington rivers. Risk states, source labeling, auto-refresh.",
        bullets: [
            "USGS instantaneous values (00065, 00060)",
            "NOAA NWPS flood thresholds (where mappable)",
            "Risk state engine (calm → watch → elevated → flood → unknown)",
            "Trust UI: source badges, last-updated, stale warnings",
        ],
    },
    {
        n: 2,
        title: "Precursor Intelligence Layer",
        status: "future",
        summary:
            "Snowpack, rainfall accumulation, and soil saturation begin informing a basin-tension score upstream of the gauges.",
        bullets: [
            "NRCS SNOTEL / AWDB snow water equivalent",
            "Precipitation accumulation",
            "Soil moisture proxy",
            "Basin-level precursor score",
        ],
    },
    {
        n: 3,
        title: "Forecasting Engine v1",
        status: "future",
        summary:
            "Simple forecast bands with rate-of-rise and threshold-crossing estimates. Always labeled experimental.",
        bullets: [
            "Rate-of-rise forecasting",
            "Threshold-crossing ETA",
            "12 / 24 / 72-hour outlook",
            "Backtesting against historical events",
        ],
    },
    {
        n: 4,
        title: "Forecasting Engine v2",
        status: "future",
        summary:
            "Time-series foundation models (e.g., TimesFM) and ensemble logic compare official forecasts, modeled forecasts, and historical analogs.",
        bullets: [
            "TimesFM (or comparable) integration",
            "Multivariate inputs",
            "Ensemble + confidence scoring",
            "Historical analog matching",
        ],
    },
    {
        n: 5,
        title: "Cinematic Event Mode",
        status: "future",
        summary:
            "3D terrain, glowing river paths, alert theater mode, radar / webcam overlays, and animated fly-throughs.",
        bullets: [
            "3D watershed map (Cesium / Mapbox / Three.js)",
            "Theater mode • ambient audio narration (TTS)",
            "Radar + webcam overlays",
            "Animated fly-throughs of risk basins",
        ],
    },
];

export const PhaseRoadmap = ({ variant = "compact" }) => {
    if (variant === "compact") {
        return (
            <section
                className="co-glass rounded-2xl p-4 sm:p-5"
                data-testid="phase-roadmap"
            >
                <div className="flex items-center justify-between gap-3 mb-3">
                    <div className="flex flex-col">
                        <span className="text-[10px] uppercase tracking-[0.20em] text-white/55">
                            Cascade Oracle • Phased Architecture
                        </span>
                        <span className="font-display text-base sm:text-lg font-semibold text-white/90">
                            Currently in <span className="text-[hsl(var(--co-cyan))]">Phase 1</span>
                        </span>
                    </div>
                    <a
                        href="/roadmap"
                        className="inline-flex items-center gap-1 text-xs sm:text-sm text-white/70 hover:text-white"
                        data-testid="phase-roadmap-view-all"
                    >
                        Full vision <ChevronRight className="h-3.5 w-3.5" />
                    </a>
                </div>
                <div
                    className="grid grid-cols-2 md:grid-cols-5 gap-2.5"
                    data-testid="phase-roadmap-rail"
                >
                    {PHASES.map((p) => {
                        const isCurrent = p.status === "current";
                        return (
                            <motion.div
                                key={p.n}
                                whileHover={{ y: -2 }}
                                transition={{ duration: 0.18 }}
                                className={`relative rounded-xl border px-3 py-2.5 ${
                                    isCurrent
                                        ? "border-[hsl(191_92%_55%/0.45)] bg-[hsl(191_92%_55%/0.08)]"
                                        : "border-white/10 bg-white/[0.03]"
                                }`}
                                data-testid={isCurrent ? "phase-roadmap-current" : `phase-roadmap-${p.n}`}
                            >
                                <div className="flex items-center gap-2">
                                    <span
                                        className={`font-mono text-[11px] ${
                                            isCurrent ? "text-[hsl(var(--co-cyan))]" : "text-white/55"
                                        }`}
                                    >
                                        Phase {p.n}
                                    </span>
                                    {isCurrent && (
                                        <span className="co-anim-shimmer text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--co-cyan))]">
                                            Active
                                        </span>
                                    )}
                                </div>
                                <div
                                    className={`mt-1 text-[12.5px] sm:text-sm font-medium leading-tight ${
                                        isCurrent ? "text-white" : "text-white/75"
                                    }`}
                                >
                                    {p.title}
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </section>
        );
    }

    // Full page
    return (
        <section
            className="grid grid-cols-1 lg:grid-cols-12 gap-6"
            data-testid="phase-roadmap-full"
        >
            <div className="lg:col-span-4">
                <div className="co-glass rounded-2xl p-5 sticky top-20">
                    <span className="text-[10px] uppercase tracking-[0.22em] text-white/55">
                        Phased Architecture
                    </span>
                    <h2 className="font-display text-2xl sm:text-3xl font-semibold mt-1 text-white">
                        From observatory to foresight engine.
                    </h2>
                    <p className="mt-3 text-sm text-white/65 leading-relaxed">
                        Cascade Oracle deliberately stages capability. Each phase only
                        proceeds once the previous layer is stable, transparent, and
                        traceable. Beauty must sit on top of credible data — never
                        replace it.
                    </p>
                    <p className="mt-3 text-sm text-white/55 leading-relaxed">
                        Today, Phase 1 is live. Future phases below are deliberately not
                        active and are described, not simulated.
                    </p>
                </div>
            </div>
            <div className="lg:col-span-8 flex flex-col gap-4">
                {PHASES.map((p) => {
                    const isCurrent = p.status === "current";
                    return (
                        <div
                            key={p.n}
                            className={`relative rounded-2xl border p-5 ${
                                isCurrent
                                    ? "border-[hsl(191_92%_55%/0.40)] bg-[hsl(191_92%_55%/0.05)]"
                                    : "border-white/10 bg-white/[0.035]"
                            }`}
                            data-testid={`phase-card-${p.n}`}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span
                                        className={`font-mono text-xs ${
                                            isCurrent
                                                ? "text-[hsl(var(--co-cyan))]"
                                                : "text-white/55"
                                        }`}
                                    >
                                        Phase {p.n}
                                    </span>
                                    {isCurrent ? (
                                        <span className="text-[10px] uppercase tracking-[0.20em] rounded-full px-2 py-0.5 border border-[hsl(191_92%_55%/0.45)] text-[hsl(var(--co-cyan))] bg-[hsl(191_92%_55%/0.10)]">
                                            Currently Active
                                        </span>
                                    ) : (
                                        <span className="text-[10px] uppercase tracking-[0.20em] rounded-full px-2 py-0.5 border border-white/10 text-white/55">
                                            Future Phase
                                        </span>
                                    )}
                                </div>
                            </div>
                            <h3 className="font-display text-lg sm:text-xl font-semibold text-white mt-2">
                                {p.title}
                            </h3>
                            <p className="mt-2 text-sm text-white/70 leading-relaxed">
                                {p.summary}
                            </p>
                            <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
                                {p.bullets.map((b) => (
                                    <li
                                        key={b}
                                        className="text-[13px] text-white/65 flex items-start gap-2"
                                    >
                                        <span
                                            className={`mt-1.5 inline-block h-1 w-1 rounded-full ${
                                                isCurrent
                                                    ? "bg-[hsl(var(--co-cyan))]"
                                                    : "bg-white/35"
                                            }`}
                                        />
                                        {b}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    );
                })}
            </div>
        </section>
    );
};
