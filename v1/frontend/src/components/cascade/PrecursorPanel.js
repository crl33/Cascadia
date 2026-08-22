import { Snowflake, TrendingDown, TrendingUp, Minus, Mountain, Info } from "lucide-react";
import { motion } from "framer-motion";
import { SourceBadge } from "@/components/cascade/SourceBadge";
import { formatNumber, timeAgo } from "@/lib/format";

function confidenceBucket(c) {
    if (typeof c !== "number") return { label: "Unknown", color: "215 10% 58%", note: "" };
    if (c >= 0.75) return { label: "High", color: "191 92% 55%", note: "Mapping confirmed; data fresh." };
    if (c >= 0.55) return { label: "Medium", color: "205 88% 58%", note: "Representative signal; verify trend with adjacent stations." };
    if (c >= 0.30) return { label: "Low", color: "38 92% 58%", note: "Stale data or weak basin mapping." };
    return { label: "None", color: "215 10% 58%", note: "No usable signal." };
}

function parseTrend(notes) {
    if (!notes) return { label: null, kind: "hold" };
    if (/melting/i.test(notes)) return { label: "Melting", kind: "down" };
    if (/rising/i.test(notes)) return { label: "Rising", kind: "up" };
    if (/holding/i.test(notes)) return { label: "Holding", kind: "hold" };
    return { label: null, kind: "hold" };
}

function TrendBadge({ kind, label }) {
    if (!label) return null;
    const Icon = kind === "up" ? TrendingUp : kind === "down" ? TrendingDown : Minus;
    const color =
        kind === "down" ? "hsl(191 92% 72%)" : kind === "up" ? "hsl(38 92% 72%)" : "hsl(215 18% 78%)";
    return (
        <span
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-white/10 bg-white/[0.04] text-[11px]"
            style={{ color }}
        >
            <Icon className="h-3 w-3" />
            {label}
        </span>
    );
}

/**
 * PrecursorPanel
 *
 * Displays SNOTEL-derived snowpack precursor for a basin, when available.
 * Trust rules:
 *   - Always shows the SNOTEL source badge.
 *   - Always shows mapping confidence + the mapping_note disclosure.
 *   - When the signal is stale or unavailable, the panel renders an explicit
 *     unavailable state instead of hiding.
 *   - The precursor MUST be visually distinct from the river-risk surface.
 */
export const PrecursorPanel = ({ precursors, compact = false }) => {
    if (!precursors) {
        return null;
    }
    const swe = precursors.snow_water_equivalent || null;
    const available = !!precursors.available && !!swe && swe.value !== null && swe.value !== undefined;
    const conf = confidenceBucket(swe?.confidence);
    const trend = parseTrend(swe?.notes);
    const accent = "191 92% 55%"; // glacier cyan for snowpack

    return (
        <section
            className="relative rounded-xl border border-white/10 bg-white/[0.025] p-4 overflow-hidden"
            data-testid="precursor-panel"
            data-precursor-available={available ? "true" : "false"}
        >
            {/* Subtle snowpack glow header beam */}
            <span
                aria-hidden
                className="absolute inset-x-0 top-0 h-px"
                style={{
                    background: `linear-gradient(90deg, transparent, hsl(${accent} / 0.55), transparent)`,
                }}
            />
            {available && (
                <motion.span
                    aria-hidden
                    initial={{ opacity: 0.18 }}
                    animate={{ opacity: [0.10, 0.22, 0.10] }}
                    transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                    className="pointer-events-none absolute -top-12 -right-10 h-32 w-44 rounded-full blur-3xl"
                    style={{
                        background: `radial-gradient(closest-side, hsl(${accent} / 0.18), transparent 70%)`,
                    }}
                />
            )}

            <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                    <span
                        className="flex h-6 w-6 items-center justify-center rounded-md border border-white/10 bg-white/[0.04]"
                        style={{ color: `hsl(${accent})` }}
                    >
                        <Snowflake className="h-3 w-3" />
                    </span>
                    <span className="text-[11px] uppercase tracking-[0.18em] text-white/65">
                        Snowpack precursor
                    </span>
                    <span className="hidden sm:inline text-[10px] uppercase tracking-[0.18em] text-white/40">
                        • Phase 2A
                    </span>
                </div>
                <SourceBadge source="nrcs_snotel" title="NRCS AWDB / SNOTEL" short />
            </div>

            {!available ? (
                <p
                    className="text-[12px] text-white/55 leading-relaxed"
                    data-testid="precursor-unavailable-message"
                >
                    {(swe && swe.notes) ||
                        precursors.note ||
                        "No SNOTEL signal currently available for this basin."}
                </p>
            ) : (
                <div className="flex flex-col gap-3">
                    <div className="flex items-end justify-between gap-3">
                        <div>
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/55">
                                Snow water equivalent
                            </div>
                            <div className="flex items-baseline gap-1.5 mt-0.5">
                                <span
                                    className="font-mono text-3xl tracking-tight text-white"
                                    data-testid="precursor-swe-value"
                                >
                                    {formatNumber(swe.value, 1)}
                                </span>
                                <span className="text-xs text-white/55">
                                    {swe.unit || "in"}
                                </span>
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                                <TrendBadge kind={trend.kind} label={trend.label} />
                                {swe.timestamp && (
                                    <span className="font-mono text-[11px] text-white/45">
                                        Observed {timeAgo(swe.timestamp)}
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="flex items-center justify-end gap-1.5 text-[10px] uppercase tracking-[0.16em] text-white/55">
                                <Mountain className="h-3 w-3" />
                                <span>Source station</span>
                            </div>
                            <div
                                className="font-display text-sm text-white/90 mt-0.5"
                                data-testid="precursor-station-name"
                            >
                                {swe.station_name || "—"}
                            </div>
                            {swe.station_elevation_ft !== null && swe.station_elevation_ft !== undefined && (
                                <div className="font-mono text-[11px] text-white/55">
                                    {Math.round(swe.station_elevation_ft).toLocaleString()} ft
                                    {swe.station_id ? ` • ${swe.station_id}` : ""}
                                </div>
                            )}
                        </div>
                    </div>

                    {!compact && (
                        <p
                            className="text-[12.5px] text-white/75 leading-relaxed"
                            data-testid="precursor-interpretation"
                        >
                            {swe.notes}
                        </p>
                    )}

                    <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-white/[0.06]">
                        <span
                            className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 border text-[11px]"
                            style={{
                                background: `hsl(${conf.color} / 0.10)`,
                                borderColor: `hsl(${conf.color} / 0.30)`,
                                color: `hsl(${conf.color})`,
                            }}
                            data-testid="precursor-confidence"
                            data-confidence={conf.label.toLowerCase()}
                        >
                            Confidence • {conf.label}
                        </span>
                        {swe.mapping_confidence && (
                            <span
                                className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 border border-white/10 bg-white/[0.03] text-[11px] text-white/65"
                                title={swe.mapping_note || ""}
                            >
                                Mapping • {swe.mapping_confidence}
                            </span>
                        )}
                    </div>

                    {swe.mapping_note && !compact && (
                        <p className="text-[11.5px] text-white/55 leading-relaxed flex items-start gap-1.5">
                            <Info className="h-3 w-3 mt-0.5 shrink-0" />
                            <span>{swe.mapping_note}</span>
                        </p>
                    )}

                    <p className="text-[11px] text-white/45 italic">
                        Representative snowpack signal only — not a flood forecast.
                        Phase 2B (precipitation), 2C (soil moisture), 2D (basin tension) pending.
                    </p>
                </div>
            )}
        </section>
    );
};
