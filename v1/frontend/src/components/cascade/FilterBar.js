import { useEffect, useState } from "react";
import axios from "axios";
import { Filter, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { API_BASE } from "@/lib/api";
import {
    RISK_STATES,
    RISK_LABEL,
    riskAccentHSL,
} from "@/lib/risk-style";

function Chip({ active, count, accent, children, onClick, testid }) {
    return (
        <button
            type="button"
            onClick={onClick}
            data-testid={testid}
            data-active={active ? "true" : "false"}
            className={`shrink-0 inline-flex items-center gap-1.5 rounded-full px-3 h-8 text-xs sm:text-[13px] border transition-colors ${
                active
                    ? "text-white"
                    : "text-white/70 hover:text-white border-white/10 bg-white/[0.03] hover:bg-white/[0.07]"
            }`}
            style={
                active
                    ? {
                          background: `hsl(${accent} / 0.14)`,
                          borderColor: `hsl(${accent} / 0.45)`,
                          boxShadow: `0 0 0 1px hsl(${accent} / 0.18) inset`,
                      }
                    : undefined
            }
        >
            <span className="truncate">{children}</span>
            {typeof count === "number" && (
                <span
                    className={`co-text-mono text-[10px] rounded-full px-1.5 ${
                        active ? "" : "bg-white/[0.06]"
                    }`}
                    style={
                        active
                            ? { background: `hsl(${accent} / 0.20)` }
                            : undefined
                    }
                >
                    {count}
                </span>
            )}
        </button>
    );
}

export const FilterBar = ({
    snapshots = [],
    activeBasin,
    onBasinChange,
    activeRisk,
    onRiskChange,
}) => {
    const [basins, setBasins] = useState([]);
    useEffect(() => {
        let cancelled = false;
        axios
            .get(`${API_BASE}/system/basins`)
            .then((r) => !cancelled && setBasins(r.data?.basins || []))
            .catch(() => {});
        return () => {
            cancelled = true;
        };
    }, []);

    const basinCounts = {};
    const riskCounts = { calm: 0, watch: 0, elevated: 0, flood: 0, unknown: 0 };
    for (const s of snapshots) {
        basinCounts[s.basin_group] = (basinCounts[s.basin_group] || 0) + 1;
        if (riskCounts[s.risk_state] !== undefined) riskCounts[s.risk_state] += 1;
    }

    const filtersActive = !!activeBasin || !!activeRisk;

    return (
        <section
            className="co-glass rounded-2xl px-3 sm:px-4 py-3 flex flex-col gap-3"
            data-testid="filter-bar"
        >
            <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-white/65">
                        <Filter className="h-3 w-3" />
                    </span>
                    <span className="text-[10px] uppercase tracking-[0.20em] text-white/55">
                        Filter
                    </span>
                </div>
                <AnimatePresence>
                    {filtersActive && (
                        <motion.div
                            initial={{ opacity: 0, y: -2 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -2 }}
                        >
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                    onBasinChange?.(null);
                                    onRiskChange?.(null);
                                }}
                                className="h-7 text-[11px] text-white/65 hover:text-white"
                                data-testid="filter-clear"
                            >
                                <X className="h-3 w-3" />
                                <span className="ml-1">Clear</span>
                            </Button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Basin row */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin" data-testid="filter-basins">
                <Chip
                    active={!activeBasin}
                    onClick={() => onBasinChange?.(null)}
                    accent="191 92% 55%"
                    count={snapshots.length}
                    testid="filter-basin-all"
                >
                    All basins
                </Chip>
                {basins.map((b) => (
                    <Chip
                        key={b.key}
                        active={activeBasin === b.key}
                        onClick={() =>
                            onBasinChange?.(activeBasin === b.key ? null : b.key)
                        }
                        accent="191 92% 55%"
                        count={basinCounts[b.key] || 0}
                        testid={`filter-basin-${b.key}`}
                    >
                        {b.label}
                    </Chip>
                ))}
            </div>

            {/* Risk row */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 -mx-1 px-1" data-testid="filter-risks">
                <Chip
                    active={!activeRisk}
                    onClick={() => onRiskChange?.(null)}
                    accent="215 10% 58%"
                    count={snapshots.length}
                    testid="filter-risk-all"
                >
                    All states
                </Chip>
                {RISK_STATES.map((s) => (
                    <Chip
                        key={s}
                        active={activeRisk === s}
                        onClick={() => onRiskChange?.(activeRisk === s ? null : s)}
                        accent={riskAccentHSL(s)}
                        count={riskCounts[s] || 0}
                        testid={`filter-risk-${s}`}
                    >
                        {RISK_LABEL[s]}
                    </Chip>
                ))}
            </div>
        </section>
    );
};
