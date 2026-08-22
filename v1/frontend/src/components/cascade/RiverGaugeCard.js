import { motion } from "framer-motion";
import { ChevronRight, Clock, MapPin } from "lucide-react";

import { Card } from "@/components/ui/card";
import { RiskBadge } from "@/components/cascade/RiskBadge";
import { SourceBadge } from "@/components/cascade/SourceBadge";
import { Sparkline } from "@/components/cascade/Sparkline";
import { formatNumber, formatFlow, timeAgo } from "@/lib/format";
import { riskGlowStyle, riskAccentHSL } from "@/lib/risk-style";

function Trend({ series }) {
    if (!series || series.length < 2) return null;
    const a = series[0].v;
    const b = series[series.length - 1].v;
    const delta = b - a;
    const sign = delta > 0.005 ? "↑" : delta < -0.005 ? "↓" : "→";
    const color =
        delta > 0.005
            ? "text-[hsl(38_92%_72%)]"
            : delta < -0.005
                ? "text-[hsl(191_92%_72%)]"
                : "text-white/55";
    return (
        <span className={`font-mono text-xs ${color}`}>
            {sign} {formatNumber(Math.abs(delta), 2)} ft / 24h
        </span>
    );
}

export const RiverGaugeCard = ({ snapshot, onOpen }) => {
    if (!snapshot) return null;
    const {
        name,
        river,
        basin,
        gage_height,
        discharge,
        risk_state,
        risk_reason,
        thresholds,
        is_stale,
        usgs_site,
    } = snapshot;

    const accent = riskAccentHSL(risk_state);

    return (
        <motion.button
            type="button"
            onClick={onOpen}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.995 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            className="group relative text-left w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--co-focus)/0.6)] rounded-2xl"
            data-testid="station-card-open-detail"
            aria-label={`Open detail for ${name}`}
        >
            <Card
                className="co-glass relative overflow-hidden rounded-2xl border-white/10 bg-transparent text-white"
                style={riskGlowStyle(risk_state)}
                data-testid="station-card"
                data-station-id={snapshot.id}
                data-basin-group={snapshot.basin_group || ""}
            >
                <span
                    aria-hidden
                    className="absolute inset-x-0 top-0 h-px"
                    style={{
                        background: `linear-gradient(90deg, transparent, hsl(${accent} / 0.55), transparent)`,
                    }}
                />

                <div className="p-4 sm:p-5 flex flex-col gap-4">
                    <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.20em] text-white/55">
                                <MapPin className="h-3 w-3" />
                                <span>{basin}</span>
                            </div>
                            <h3
                                className="font-display text-[15px] sm:text-base font-semibold text-white truncate mt-0.5"
                                data-testid="station-card-name"
                            >
                                {name}
                            </h3>
                            <div className="text-[11px] text-white/55 font-mono mt-0.5">
                                USGS {usgs_site} • {river}
                            </div>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                            <RiskBadge state={risk_state} reason={risk_reason} />
                            {is_stale && (
                                <span
                                    className="co-text-mono text-[10px] uppercase tracking-[0.16em] text-[hsl(38_92%_72%)] flex items-center gap-1"
                                    data-testid="station-stale-indicator"
                                >
                                    <Clock className="h-3 w-3" />
                                    Stale
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="flex items-end justify-between gap-4">
                        <div>
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/55">
                                Gage height
                            </div>
                            <div className="flex items-baseline gap-1.5 mt-0.5">
                                <span
                                    className="font-mono text-3xl sm:text-[34px] tracking-tight text-white"
                                    data-testid="station-card-gage-height"
                                >
                                    {formatNumber(gage_height.latest, 2)}
                                </span>
                                <span className="text-xs text-white/55">
                                    {gage_height.unit || "ft"}
                                </span>
                            </div>
                            <Trend series={gage_height.series} />
                        </div>
                        <div className="text-right">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/55">
                                Discharge
                            </div>
                            <div className="flex items-baseline justify-end gap-1.5 mt-0.5">
                                <span
                                    className="font-mono text-xl sm:text-2xl tracking-tight text-white/85"
                                    data-testid="station-card-discharge"
                                >
                                    {formatFlow(discharge.latest)}
                                </span>
                                <span className="text-[11px] text-white/55">
                                    {discharge.unit || "cfs"}
                                </span>
                            </div>
                            <span className="font-mono text-[11px] text-white/45">
                                {discharge.latest_at
                                    ? `obs ${timeAgo(discharge.latest_at)}`
                                    : "—"}
                            </span>
                        </div>
                    </div>

                    <div className="-mx-1">
                        <Sparkline
                            series={gage_height.series}
                            state={risk_state}
                            height={56}
                        />
                    </div>

                    <div className="flex items-center justify-between gap-2 pt-1 border-t border-white/[0.06]">
                        <div className="flex items-center gap-2 min-w-0">
                            <SourceBadge
                                source={thresholds.source}
                                title={thresholds.source_label}
                                short
                            />
                            <span
                                className="co-text-mono text-[11px] text-white/55 truncate"
                                data-testid="station-card-last-updated"
                            >
                                Updated {timeAgo(gage_height.latest_at)}
                            </span>
                        </div>
                        <span className="inline-flex items-center gap-1 text-[11px] text-white/55 group-hover:text-white/85 transition-colors">
                            Detail <ChevronRight className="h-3.5 w-3.5" />
                        </span>
                    </div>
                </div>
            </Card>
        </motion.button>
    );
};
