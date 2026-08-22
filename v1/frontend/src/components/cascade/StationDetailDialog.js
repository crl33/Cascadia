import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
    RefreshCw,
    MapPin,
    Database,
    Activity,
    Info,
    Layers,
    HelpCircle,
} from "lucide-react";
import { toast } from "sonner";

import { RiskBadge } from "@/components/cascade/RiskBadge";
import { SourceBadge } from "@/components/cascade/SourceBadge";
import { HydrographChart } from "@/components/cascade/HydrographChart";
import { PrecursorPanel } from "@/components/cascade/PrecursorPanel";
import {
    formatNumber,
    formatFlow,
    timeAgo,
    formatLocalDateTime,
} from "@/lib/format";
import { refreshStation } from "@/lib/api";
import {
    sourceMeta,
    RISK_DESCRIPTION,
    RISK_LABEL,
    riskAccentHSL,
} from "@/lib/risk-style";

function StatLine({ label, value, mono = true }) {
    return (
        <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-white/[0.06] last:border-0">
            <span className="text-[11px] uppercase tracking-[0.16em] text-white/55">
                {label}
            </span>
            <span
                className={`text-sm ${mono ? "font-mono" : ""} text-white/90 text-right`}
            >
                {value}
            </span>
        </div>
    );
}

function SectionHeader({ icon: Icon, title, source, accent }) {
    return (
        <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
                <span
                    className="flex h-6 w-6 items-center justify-center rounded-md border border-white/10 bg-white/[0.04]"
                    style={accent ? { color: `hsl(${accent})` } : undefined}
                >
                    <Icon className="h-3 w-3" />
                </span>
                <span className="text-[11px] uppercase tracking-[0.18em] text-white/65">
                    {title}
                </span>
            </div>
            {source && (
                <SourceBadge source={source.source} title={source.label} short />
            )}
        </div>
    );
}

export const StationDetailDialog = ({ open, onOpenChange, snapshot, onUpdated }) => {
    const [isRefreshing, setIsRefreshing] = useState(false);
    if (!snapshot) return null;

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            const fresh = await refreshStation(snapshot.id);
            onUpdated?.(fresh);
            toast.success(`Refreshed: ${snapshot.name}`);
        } catch (e) {
            toast.error("Refresh failed. Will retry on next cycle.");
        } finally {
            setIsRefreshing(false);
        }
    };

    const t = snapshot.thresholds || {};
    const tMeta = sourceMeta(t.source);
    const obsAccent = "191 92% 55%";
    const stateAccent = riskAccentHSL(snapshot.risk_state);
    const precursors = snapshot.precursors || null;

    const thrLine = (k, label) =>
        typeof t[k] === "number"
            ? `${formatNumber(t[k], 2)} ft • ${label}`
            : `— • ${label}`;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent
                className="co-glass-strong w-[96vw] max-w-3xl border-white/10 bg-[hsl(var(--co-bg-canvas))] text-white p-0 overflow-hidden"
                data-testid="station-detail-dialog"
            >
                {/* Header */}
                <DialogHeader className="px-5 sm:px-6 py-4 border-b border-white/10 bg-white/[0.03]">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.20em] text-white/55">
                        <MapPin className="h-3 w-3" />
                        <span>{snapshot.basin}</span>
                        <span className="text-white/30">•</span>
                        <span>{snapshot.river}</span>
                    </div>
                    <DialogTitle className="font-display text-xl sm:text-2xl text-white tracking-tight">
                        {snapshot.name}
                    </DialogTitle>
                    <DialogDescription className="text-xs text-white/55 font-mono">
                        USGS {snapshot.usgs_site}
                        {snapshot.nwps_lid ? ` • NWPS ${snapshot.nwps_lid}` : ""}
                        {snapshot.lat && snapshot.lon
                            ? ` • ${snapshot.lat.toFixed(3)}, ${snapshot.lon.toFixed(3)}`
                            : ""}
                    </DialogDescription>
                    <div className="flex flex-wrap items-center gap-2 pt-2">
                        <RiskBadge
                            state={snapshot.risk_state}
                            reason={snapshot.risk_reason}
                        />
                        <SourceBadge source={t.source} title={t.source_label} />
                        {precursors?.available && (
                            <SourceBadge
                                source="nrcs_snotel"
                                title="Snowpack precursor active"
                                short
                            />
                        )}
                    </div>
                </DialogHeader>

                {/* Body */}
                <div
                    className="px-4 sm:px-6 py-5 space-y-5 max-h-[70vh] overflow-y-auto"
                    data-testid="station-detail-body"
                >
                    {/* Why this status? */}
                    <section
                        className="co-glass rounded-xl p-4"
                        data-testid="station-why-status"
                    >
                        <SectionHeader
                            icon={HelpCircle}
                            title="Why this status?"
                            accent={stateAccent}
                        />
                        <div className="flex flex-col gap-2.5">
                            <div className="flex items-baseline gap-2">
                                <span className="text-[11px] uppercase tracking-[0.16em] text-white/55">
                                    State
                                </span>
                                <span
                                    className="text-sm font-medium"
                                    style={{ color: `hsl(${stateAccent})` }}
                                >
                                    {RISK_LABEL[snapshot.risk_state]}
                                </span>
                            </div>
                            <p
                                className="text-[13px] text-white/85 leading-relaxed"
                                data-testid="station-risk-reason"
                            >
                                {snapshot.risk_reason}
                            </p>
                            <p className="text-[12px] text-white/55 leading-relaxed">
                                {RISK_DESCRIPTION[snapshot.risk_state]}
                            </p>
                            {!t.validated && (
                                <div className="mt-1 flex items-start gap-2 rounded-lg border border-[hsl(38_92%_58%/0.25)] bg-[hsl(38_92%_58%/0.06)] px-2.5 py-2 text-[12px] text-[hsl(38_92%_82%)]">
                                    <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                                    <span>
                                        Risk computation requires validated thresholds.
                                        Current threshold source:{" "}
                                        <span className="font-medium">{tMeta.label}</span>.
                                    </span>
                                </div>
                            )}
                            {precursors?.available && (
                                <div className="mt-1 flex items-start gap-2 rounded-lg border border-[hsl(191_92%_55%/0.20)] bg-[hsl(191_92%_55%/0.05)] px-2.5 py-2 text-[12px] text-white/70">
                                    <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                                    <span>
                                        Precursor signals (snowpack) are{" "}
                                        <span className="text-white/90">context only</span>{" "}
                                        and do not affect river risk state.
                                    </span>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* KPI strip */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-3">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/55">
                                Gage height
                            </div>
                            <div className="font-mono text-2xl text-white mt-0.5">
                                {formatNumber(snapshot.gage_height.latest, 2)}
                                <span className="ml-1 text-xs text-white/55">
                                    {snapshot.gage_height.unit || "ft"}
                                </span>
                            </div>
                            <div className="text-[11px] font-mono text-white/45 mt-0.5">
                                {timeAgo(snapshot.gage_height.latest_at)}
                            </div>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-3">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/55">
                                Discharge
                            </div>
                            <div className="font-mono text-2xl text-white mt-0.5">
                                {formatFlow(snapshot.discharge.latest)}
                                <span className="ml-1 text-xs text-white/55">
                                    {snapshot.discharge.unit || "cfs"}
                                </span>
                            </div>
                            <div className="text-[11px] font-mono text-white/45 mt-0.5">
                                {timeAgo(snapshot.discharge.latest_at)}
                            </div>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-3 col-span-2 sm:col-span-1">
                            <div className="text-[10px] uppercase tracking-[0.18em] text-white/55">
                                Stale?
                            </div>
                            <div className="text-sm text-white/85 mt-0.5">
                                {snapshot.is_stale ? (
                                    <span className="text-[hsl(38_92%_72%)]">
                                        Yes — last observation older than 90 min
                                    </span>
                                ) : (
                                    <span className="text-[hsl(191_92%_72%)]">No — fresh</span>
                                )}
                            </div>
                            <div className="text-[11px] font-mono text-white/45 mt-0.5">
                                fetched {timeAgo(snapshot.fetched_at)}
                            </div>
                        </div>
                    </div>

                    {/* Observed data */}
                    <section
                        className="co-glass rounded-xl p-4"
                        data-testid="station-section-observed"
                    >
                        <SectionHeader
                            icon={Activity}
                            title="Observed data"
                            source={{ source: "official_nwps", label: "USGS Water Services" }}
                            accent={obsAccent}
                        />
                        <p className="text-[12px] text-white/55 leading-relaxed mb-2">
                            Live instantaneous values from USGS. Updated every 15–60 min depending on station.
                        </p>
                        <HydrographChart snapshot={snapshot} height={300} />
                    </section>

                    {/* Precursor (Phase 2A) */}
                    <section data-testid="station-section-precursors">
                        <PrecursorPanel precursors={precursors} />
                    </section>

                    {/* Thresholds */}
                    <section
                        className="co-glass rounded-xl p-4"
                        data-testid="station-section-thresholds"
                    >
                        <SectionHeader
                            icon={Database}
                            title="Flood thresholds"
                            source={{ source: t.source, label: t.source_label }}
                            accent={tMeta.accent}
                        />
                        <p className="text-[12px] text-white/55 leading-relaxed mb-2">
                            {t.source === "official_nwps" &&
                                "Authoritative thresholds from NOAA / National Weather Service."}
                            {t.source === "configured_validated" &&
                                "Locally configured thresholds verified against an authoritative source."}
                            {t.source === "configured_pending" &&
                                "Locally configured values pending validation. NOT used in risk computation."}
                            {t.source === "thresholds_unavailable" &&
                                "No validated thresholds available for this gauge. Risk reported as unknown."}
                        </p>
                        <StatLine label="Action" value={thrLine("action", "first warning")} />
                        <StatLine label="Minor" value={thrLine("minor", "minor flood")} />
                        <StatLine label="Moderate" value={thrLine("moderate", "moderate flood")} />
                        <StatLine label="Major" value={thrLine("major", "major flood")} />
                        {t.notes && (
                            <p className="mt-2 text-[12px] text-white/55 leading-relaxed">
                                <Info className="inline h-3 w-3 mr-1 -mt-0.5" />
                                {t.notes}
                            </p>
                        )}
                    </section>

                    {/* Provenance + station notes */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <section
                            className="co-glass rounded-xl p-4"
                            data-testid="station-section-provenance"
                        >
                            <SectionHeader icon={Layers} title="Data provenance" />
                            <StatLine label="USGS site" value={snapshot.usgs_site} />
                            <StatLine label="NWPS LID" value={snapshot.nwps_lid || "—"} />
                            <StatLine
                                label="Last observed"
                                value={formatLocalDateTime(snapshot.gage_height.latest_at)}
                            />
                            <StatLine
                                label="Snapshot taken"
                                value={formatLocalDateTime(snapshot.fetched_at)}
                            />
                            <StatLine
                                label="Active"
                                value={snapshot.active ? "Yes" : "No"}
                            />
                            {snapshot.errors && snapshot.errors.length > 0 && (
                                <div
                                    className="mt-2 text-[11px] text-[hsl(38_92%_72%)] space-y-0.5"
                                    data-testid="station-errors"
                                >
                                    {snapshot.errors.map((e, i) => (
                                        <div key={i} className="font-mono">
                                            ! {e}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>
                        <section
                            className="co-glass rounded-xl p-4"
                            data-testid="station-section-notes"
                        >
                            <SectionHeader icon={Info} title="Station notes" />
                            {snapshot.notes ? (
                                <p className="text-[13px] text-white/75 leading-relaxed">
                                    {snapshot.notes}
                                </p>
                            ) : (
                                <p className="text-[12px] text-white/45 italic">
                                    No operational notes recorded.
                                </p>
                            )}
                        </section>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-4 sm:px-6 py-3 border-t border-white/10 bg-white/[0.02] flex items-center justify-between gap-2">
                    <span className="text-[11px] text-white/45 font-mono truncate">
                        Observed + snowpack precursor • Forecast layer not yet active
                    </span>
                    <Button
                        size="sm"
                        variant="outline"
                        className="border-white/15 bg-white/[0.04] text-white hover:bg-white/[0.08]"
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                        data-testid="station-detail-refresh"
                    >
                        <RefreshCw
                            className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`}
                        />
                        <span className="ml-1.5">Refresh</span>
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
};
