import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Toaster, toast } from "sonner";
import { Activity } from "lucide-react";

import { AmbientBackdrop } from "@/components/cascade/AmbientBackdrop";
import { NavBar } from "@/components/cascade/NavBar";
import { HeroStatusPanel } from "@/components/cascade/HeroStatusPanel";
import { FilterBar } from "@/components/cascade/FilterBar";
import { RiverGaugeCard } from "@/components/cascade/RiverGaugeCard";
import { StationDetailDialog } from "@/components/cascade/StationDetailDialog";
import { PhaseRoadmap } from "@/components/cascade/PhaseRoadmap";
import { SystemDisclaimer } from "@/components/cascade/SystemDisclaimer";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchStations, refreshAllStations } from "@/lib/api";

const AUTO_REFRESH_MS = 5 * 60 * 1000;

function LoadingGrid() {
    return (
        <div
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5"
            data-testid="dashboard-loading"
        >
            {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="co-glass rounded-2xl p-5 space-y-4">
                    <Skeleton className="h-5 w-1/2 bg-white/10" />
                    <Skeleton className="h-9 w-32 bg-white/10" />
                    <Skeleton className="h-14 w-full bg-white/[0.06]" />
                    <Skeleton className="h-3 w-3/4 bg-white/[0.08]" />
                </div>
            ))}
        </div>
    );
}

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [openId, setOpenId] = useState(null);
    const [activeBasin, setActiveBasin] = useState(null);
    const [activeRisk, setActiveRisk] = useState(null);
    const refreshTimer = useRef(null);

    const load = useCallback(async (showSpinner = true) => {
        if (showSpinner) setLoading(true);
        try {
            const d = await fetchStations();
            setData(d);
            setError(null);
        } catch (e) {
            setError(e?.message || "Failed to load stations");
        } finally {
            setLoading(false);
        }
    }, []);

    const refreshAll = useCallback(async () => {
        setRefreshing(true);
        try {
            const d = await refreshAllStations();
            setData(d);
            const ok = d?.system?.last_attempt?.ok;
            if (ok) toast.success("Watershed snapshot refreshed.");
            else toast.warning("Refresh completed with degraded sources.");
            setError(null);
        } catch (e) {
            toast.error("Refresh failed. Showing last known snapshot.");
        } finally {
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        load(true);
    }, [load]);

    useEffect(() => {
        if (refreshTimer.current) clearInterval(refreshTimer.current);
        refreshTimer.current = setInterval(() => load(false), AUTO_REFRESH_MS);
        return () => {
            if (refreshTimer.current) clearInterval(refreshTimer.current);
        };
    }, [load]);

    const stations = data?.stations || [];
    const fetchedAt = data?.fetched_at;
    const system = data?.system || {
        cache_seconds_remaining: 0,
        notes: [],
        last_attempt: null,
    };

    const filtered = useMemo(() => {
        return stations.filter((s) => {
            if (activeBasin && s.basin_group !== activeBasin) return false;
            if (activeRisk && s.risk_state !== activeRisk) return false;
            return true;
        });
    }, [stations, activeBasin, activeRisk]);

    const openSnapshot = useMemo(
        () => stations.find((s) => s.id === openId) || null,
        [openId, stations],
    );

    const handleStationUpdated = (fresh) => {
        setData((prev) => {
            if (!prev) return prev;
            return {
                ...prev,
                stations: prev.stations.map((s) => (s.id === fresh.id ? fresh : s)),
            };
        });
    };

    return (
        <div className="relative min-h-screen text-white">
            <AmbientBackdrop />
            <NavBar
                lastUpdatedAt={fetchedAt}
                onRefresh={refreshAll}
                isRefreshing={refreshing}
            />

            <main
                className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-10 flex flex-col gap-5"
                data-testid="dashboard-main"
            >
                {/* Hero status */}
                {loading && !data ? (
                    <div className="co-glass rounded-2xl p-6" data-testid="hero-loading">
                        <Skeleton className="h-8 w-1/2 bg-white/10" />
                        <Skeleton className="h-4 w-3/4 bg-white/[0.06] mt-3" />
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
                            {Array.from({ length: 4 }).map((_, i) => (
                                <Skeleton key={i} className="h-16 w-full bg-white/[0.05]" />
                            ))}
                        </div>
                    </div>
                ) : (
                    <HeroStatusPanel
                        snapshots={stations}
                        fetchedAt={fetchedAt}
                        cacheSecondsRemaining={system.cache_seconds_remaining}
                        systemNotes={system.notes}
                        lastAttempt={system.last_attempt}
                        phaseLabel={system.phase_label}
                        precursorStatus={system.precursors}
                    />
                )}

                {/* Filter bar */}
                {!loading && data && (
                    <FilterBar
                        snapshots={stations}
                        activeBasin={activeBasin}
                        onBasinChange={setActiveBasin}
                        activeRisk={activeRisk}
                        onRiskChange={setActiveRisk}
                    />
                )}

                {/* Section header */}
                <div className="flex items-center justify-between gap-3 mt-1">
                    <div className="flex items-center gap-2">
                        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-[hsl(var(--co-cyan))]">
                            <Activity className="h-3.5 w-3.5" />
                        </span>
                        <h2 className="font-display text-lg sm:text-xl font-semibold text-white">
                            River stations
                        </h2>
                        <span className="hidden sm:inline text-[11px] uppercase tracking-[0.18em] text-white/55 ml-2">
                            Live USGS observations • {filtered.length} of {stations.length}
                        </span>
                    </div>
                    {error && (
                        <span
                            className="text-xs text-[hsl(38_92%_72%)]"
                            data-testid="dashboard-error"
                        >
                            {error}
                        </span>
                    )}
                </div>

                {/* Stations grid */}
                {loading && !data ? (
                    <LoadingGrid />
                ) : stations.length === 0 ? (
                    <div
                        className="co-glass rounded-2xl p-6 text-center text-white/65"
                        data-testid="dashboard-empty"
                    >
                        No stations available. Try the refresh button.
                    </div>
                ) : filtered.length === 0 ? (
                    <div
                        className="co-glass rounded-2xl p-6 text-center text-white/65"
                        data-testid="dashboard-filter-empty"
                    >
                        No stations match the current filters.
                    </div>
                ) : (
                    <motion.div
                        initial="hidden"
                        animate="shown"
                        variants={{
                            shown: { transition: { staggerChildren: 0.05 } },
                            hidden: {},
                        }}
                        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5"
                        data-testid="stations-grid"
                    >
                        <AnimatePresence>
                            {filtered.map((s) => (
                                <motion.div
                                    key={s.id}
                                    layout
                                    variants={{
                                        hidden: { opacity: 0, y: 8 },
                                        shown: {
                                            opacity: 1,
                                            y: 0,
                                            transition: {
                                                duration: 0.35,
                                                ease: [0.22, 1, 0.36, 1],
                                            },
                                        },
                                    }}
                                >
                                    <RiverGaugeCard
                                        snapshot={s}
                                        onOpen={() => setOpenId(s.id)}
                                    />
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </motion.div>
                )}

                {/* Phase roadmap */}
                <PhaseRoadmap variant="compact" />

                {/* Disclaimer */}
                <SystemDisclaimer />
            </main>

            <StationDetailDialog
                open={!!openId}
                onOpenChange={(o) => !o && setOpenId(null)}
                snapshot={openSnapshot}
                onUpdated={handleStationUpdated}
            />

            <Toaster
                theme="dark"
                position="top-center"
                toastOptions={{
                    className: "co-glass-strong text-white",
                }}
            />
        </div>
    );
}
