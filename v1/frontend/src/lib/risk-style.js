// Risk-state visual mapping for Cascade Oracle (Phase 1.5 + Phase 2A).
// Used by RiverGaugeCard, HeroStatusPanel, RiskBadge, charts, FilterBar, PrecursorPanel.

export const RISK_STATES = ["calm", "watch", "elevated", "flood", "unknown"];

export const RISK_LABEL = {
    calm: "Calm",
    watch: "Watch",
    elevated: "Elevated",
    flood: "Flood",
    unknown: "Unknown",
};

export const RISK_DESCRIPTION = {
    calm: "Below all action thresholds. Conditions stable.",
    watch: "Above action stage. Increasing attention warranted.",
    elevated: "Above minor flood stage. Persistent concern.",
    flood: "At or above moderate/major flood stage.",
    unknown:
        "Risk cannot be computed safely — either no current observation, or thresholds are not yet validated for this gauge.",
};

export const RISK_HSL = {
    calm: "191 92% 55%",
    watch: "38 92% 58%",
    elevated: "32 96% 56%",
    flood: "6 86% 56%",
    unknown: "215 10% 58%",
};

export const RISK_TEXT_HSL = {
    calm: "191 92% 70%",
    watch: "38 92% 72%",
    elevated: "32 96% 72%",
    flood: "6 86% 72%",
    unknown: "215 18% 78%",
};

export const RISK_PULSE_CLASS = {
    calm: "",
    watch: "co-anim-pulse-watch",
    elevated: "co-anim-pulse-elev",
    flood: "co-anim-pulse-flood",
    unknown: "",
};

export function riskBgClass(state) {
    return {
        calm: "bg-[hsl(191_92%_55%/0.10)]",
        watch: "bg-[hsl(38_92%_58%/0.10)]",
        elevated: "bg-[hsl(32_96%_56%/0.12)]",
        flood: "bg-[hsl(6_86%_56%/0.14)]",
        unknown: "bg-white/[0.05]",
    }[state] || "bg-white/[0.05]";
}

export function riskBorderClass(state) {
    return {
        calm: "border-[hsl(191_92%_55%/0.30)]",
        watch: "border-[hsl(38_92%_58%/0.30)]",
        elevated: "border-[hsl(32_96%_56%/0.34)]",
        flood: "border-[hsl(6_86%_56%/0.36)]",
        unknown: "border-white/15",
    }[state] || "border-white/15";
}

export function riskTextClass(state) {
    return {
        calm: "text-[hsl(191_92%_72%)]",
        watch: "text-[hsl(38_92%_74%)]",
        elevated: "text-[hsl(32_96%_74%)]",
        flood: "text-[hsl(6_86%_74%)]",
        unknown: "text-white/70",
    }[state] || "text-white/70";
}

export function riskGlowStyle(state) {
    const map = {
        calm: "0 0 0 1px hsl(191 92% 55% / 0.10), 0 0 30px hsl(191 92% 55% / 0.10)",
        watch: "0 0 0 1px hsl(38 92% 58% / 0.10), 0 0 28px hsl(38 92% 58% / 0.10)",
        elevated: "0 0 0 1px hsl(32 96% 56% / 0.14), 0 0 30px hsl(32 96% 56% / 0.14)",
        flood: "0 0 0 1px hsl(6 86% 56% / 0.18), 0 0 32px hsl(6 86% 56% / 0.18)",
        unknown: "0 0 0 1px hsl(215 10% 58% / 0.06)",
    };
    return { boxShadow: map[state] || map.unknown };
}

export function riskAccentHSL(state) {
    return RISK_HSL[state] || RISK_HSL.unknown;
}

export function aggregateOverallState(snapshots = []) {
    const order = ["flood", "elevated", "watch", "calm", "unknown"];
    for (const s of order) {
        if (snapshots.some((x) => x.risk_state === s)) {
            return s;
        }
    }
    return "unknown";
}

export function countByRisk(snapshots = []) {
    const counts = { calm: 0, watch: 0, elevated: 0, flood: 0, unknown: 0 };
    for (const s of snapshots) {
        if (counts[s.risk_state] !== undefined) counts[s.risk_state] += 1;
    }
    return counts;
}

// ---------------------------------------------------------------------------
// Threshold + precursor source taxonomy (Phase 1.5 + 2A)
// ---------------------------------------------------------------------------
export const SOURCE_META = {
    official_nwps: {
        label: "Official NWS / NWPS",
        short: "NWS / NWPS",
        bg: "bg-[hsl(191_92%_55%/0.12)]",
        border: "border-[hsl(191_92%_55%/0.35)]",
        text: "text-[hsl(191_92%_72%)]",
        accent: "191 92% 55%",
        confidence: "validated",
    },
    configured_validated: {
        label: "Configured (validated)",
        short: "Configured",
        bg: "bg-[hsl(205_88%_58%/0.10)]",
        border: "border-[hsl(205_88%_58%/0.32)]",
        text: "text-[hsl(205_88%_72%)]",
        accent: "205 88% 58%",
        confidence: "validated",
    },
    configured_pending: {
        label: "Pending validation",
        short: "Pending",
        bg: "bg-[hsl(38_92%_58%/0.08)]",
        border: "border-[hsl(38_92%_58%/0.28)]",
        text: "text-[hsl(38_92%_72%)]",
        accent: "38 92% 58%",
        confidence: "unvalidated",
    },
    thresholds_unavailable: {
        label: "Thresholds unavailable",
        short: "Unavailable",
        bg: "bg-white/[0.04]",
        border: "border-white/15",
        text: "text-white/65",
        accent: "215 10% 58%",
        confidence: "none",
    },
    nrcs_snotel: {
        label: "NRCS AWDB / SNOTEL",
        short: "NRCS SNOTEL",
        bg: "bg-[hsl(191_92%_55%/0.08)]",
        border: "border-[hsl(191_92%_55%/0.30)]",
        text: "text-[hsl(191_92%_75%)]",
        accent: "191 92% 55%",
        confidence: "observational",
    },
};

export function sourceMeta(source) {
    return SOURCE_META[source] || SOURCE_META.thresholds_unavailable;
}

export function countByBasin(snapshots = []) {
    const counts = {};
    for (const s of snapshots) {
        const k = s.basin_group || "unknown";
        counts[k] = (counts[k] || 0) + 1;
    }
    return counts;
}
