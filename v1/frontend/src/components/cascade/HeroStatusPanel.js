import { motion } from "framer-motion";
import {
    ShieldCheck,
    AlertTriangle,
    Activity,
    Waves,
    AlertOctagon,
    Snowflake,
} from "lucide-react";
import {
    aggregateOverallState,
    countByRisk,
    riskAccentHSL,
} from "@/lib/risk-style";
import { timeAgo } from "@/lib/format";

function headlineFor(state, counts) {
    if (state === "flood") {
        const n = counts.flood;
        return {
            title: `${n} ${n === 1 ? "basin" : "basins"} at flood risk`,
            sub: "High-attention conditions detected. Cross-reference with NWS for life-safety decisions.",
        };
    }
    if (state === "elevated") {
        return {
            title: `${counts.elevated} ${counts.elevated === 1 ? "basin" : "basins"} elevated`,
            sub: "Above minor flood stage. Watch trends carefully.",
        };
    }
    if (state === "watch") {
        return {
            title: `${counts.watch} ${counts.watch === 1 ? "basin" : "basins"} on watch`,
            sub: "Above action stage at one or more gauges. Monitoring closely.",
        };
    }
    if (state === "calm") {
        return {
            title: "All watersheds calm",
            sub: "No gauges above action stage. Observed and modeled signals stable.",
        };
    }
    return {
        title: "Awaiting basin signal",
        sub: "Gathering observations. Some thresholds may not yet be validated.",
    };
}

function Kpi({ label, value, accent, testid }) {
    return (
        <div
            className="flex flex-col gap-1 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5"
            data-testid={testid}
        >
            <span className="text-[10px] uppercase tracking-[0.18em] text-white/55">
                {label}
            </span>
            <span
                className="font-mono text-2xl text-white"
                style={{
                    color: accent ? `hsl(${accent})` : undefined,
                }}
            >
                {value}
            </span>
        </div>
    );
}

function PrecursorPill({ precursorStatus }) {
    if (!precursorStatus) return null;
    const active = !!precursorStatus.snowpack_active;
    const ok = !!precursorStatus.snowpack_last_attempt_ok;
    const total = precursorStatus.snowpack_basins_total || 0;
    const withData = precursorStatus.snowpack_basins_with_data || 0;
    const accent = active ? "191 92% 55%" : "215 10% 58%";
    const label = active
        ? `Snowpack • ${withData}/${total} basins`
        : "Snowpack precursor offline";
    return (
        <span
            className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 border text-[11px]"
            style={{
                background: `hsl(${accent} / 0.10)`,
                borderColor: `hsl(${accent} / 0.35)`,
                color: `hsl(${accent})`,
            }}
            data-testid="hero-precursor-pill"
            data-snowpack-active={active ? "true" : "false"}
            title={
                ok
                    ? "NRCS AWDB / SNOTEL last refresh succeeded"
                    : "NRCS AWDB / SNOTEL last refresh did not fully succeed"
            }
        >
            <Snowflake className="h-3 w-3" />
            {label}
        </span>
    );
}

export const HeroStatusPanel = ({
    snapshots = [],
    fetchedAt,
    cacheSecondsRemaining = 0,
    systemNotes = [],
    lastAttempt,
    phaseLabel,
    precursorStatus,
}) => {
    const overall = aggregateOverallState(snapshots);
    const counts = countByRisk(snapshots);
    const head = headlineFor(overall, counts);
    const accent = riskAccentHSL(overall);
    const Icon =
        overall === "flood"
            ? AlertOctagon
            : overall === "elevated"
            ? AlertTriangle
            : overall === "watch"
            ? Activity
            : overall === "calm"
            ? ShieldCheck
            : Waves;

    const lastAttemptOk = lastAttempt?.ok;
    const lastAttemptAt = lastAttempt?.attempted_at;

    return (
        <section
            className="co-glass relative overflow-hidden rounded-2xl"
            data-testid="hero-status-panel"
        >
            <div
                className="relative px-4 sm:px-5 py-3 border-b border-white/10"
                style={{
                    background: `linear-gradient(135deg, hsl(${accent} / 0.18), hsl(${accent} / 0.05) 55%, hsl(var(--co-bg-canvas) / 0))`,
                }}
            >
                <motion.div
                    aria-hidden
                    className="absolute inset-0"
                    initial={{ opacity: 0.6 }}
                    animate={{ opacity: [0.55, 0.85, 0.55] }}
                    transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
                    style={{
                        background: `linear-gradient(120deg, transparent, hsl(${accent} / 0.06), transparent)`,
                    }}
                />
                <div className="relative flex items-center justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2.5">
                        <span
                            className="flex h-7 w-7 items-center justify-center rounded-md border border-white/15 bg-white/[0.05]"
                            style={{ color: `hsl(${accent})` }}
                        >
                            <Icon className="h-4 w-4" />
                        </span>
                        <div>
                            <span className="text-[10px] uppercase tracking-[0.20em] text-white/55">
                                System Status
                            </span>
                            {phaseLabel && (
                                <span
                                    className="hidden sm:inline ml-2 text-[10px] uppercase tracking-[0.18em] text-white/55"
                                    data-testid="hero-phase-label"
                                >
                                    • {phaseLabel}
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                        <PrecursorPill precursorStatus={precursorStatus} />
                        <span className="font-mono text-[11px] text-white/55">
                            Auto-refresh • 5 min
                        </span>
                    </div>
                </div>
            </div>

            <div className="px-4 sm:px-5 py-4 sm:py-5 flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
                <div className="max-w-2xl">
                    <h1
                        className="font-display text-2xl sm:text-3xl lg:text-[34px] font-semibold tracking-tight text-white"
                        data-testid="hero-status-headline"
                    >
                        {head.title}
                    </h1>
                    <p className="mt-2 text-sm sm:text-[15px] text-white/65 leading-relaxed">
                        {head.sub}
                    </p>
                    <div
                        className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-white/55"
                        data-testid="hero-status-updated"
                    >
                        <span className="font-mono">Updated {timeAgo(fetchedAt)}</span>
                        <span className="font-mono">
                            Next refresh ≈ {Math.max(0, Math.round(cacheSecondsRemaining / 60))} min
                        </span>
                        {lastAttemptAt && (
                            <span
                                className={`font-mono inline-flex items-center gap-1.5 ${
                                    lastAttemptOk
                                        ? "text-[hsl(var(--co-cyan))]"
                                        : "text-[hsl(var(--co-flood-red))]"
                                }`}
                                data-testid="hero-status-last-attempt"
                            >
                                <span
                                    className={`inline-block h-1.5 w-1.5 rounded-full ${
                                        lastAttemptOk
                                            ? "bg-[hsl(var(--co-cyan))]"
                                            : "bg-[hsl(var(--co-flood-red))]"
                                    }`}
                                />
                                {lastAttemptOk ? "refresh OK" : "refresh degraded"}
                                {" • "}
                                {timeAgo(lastAttemptAt)}
                            </span>
                        )}
                        {systemNotes.length > 0 && (
                            <span
                                className="text-[hsl(var(--co-amber-watch))]"
                                data-testid="hero-status-note"
                            >
                                {systemNotes[0]}
                            </span>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 min-w-[260px] sm:min-w-[420px]">
                    <Kpi
                        label="Stations"
                        value={snapshots.length}
                        testid="hero-status-kpi-total"
                    />
                    <Kpi
                        label="Calm"
                        value={counts.calm}
                        accent={"191 92% 55%"}
                        testid="hero-status-kpi-calm"
                    />
                    <Kpi
                        label="Watch"
                        value={counts.watch + counts.elevated}
                        accent={"38 92% 58%"}
                        testid="hero-status-kpi-watch"
                    />
                    <Kpi
                        label="Flood"
                        value={counts.flood}
                        accent={"6 86% 56%"}
                        testid="hero-status-kpi-flood"
                    />
                </div>
            </div>
        </section>
    );
};
