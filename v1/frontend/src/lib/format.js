// Number + time formatting helpers for Cascade Oracle.

export function formatNumber(n, fractionDigits = 2) {
    if (n === null || n === undefined || Number.isNaN(n)) return "—";
    if (Math.abs(n) >= 10000) {
        return new Intl.NumberFormat("en-US", {
            maximumFractionDigits: 0,
        }).format(n);
    }
    return new Intl.NumberFormat("en-US", {
        maximumFractionDigits: fractionDigits,
        minimumFractionDigits: fractionDigits,
    }).format(n);
}

export function formatFlow(n) {
    if (n === null || n === undefined || Number.isNaN(n)) return "—";
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n);
}

// Returns relative time, e.g., "3 min ago", "just now", "2 h ago"
export function timeAgo(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    const diffMs = Date.now() - d.getTime();
    const sec = Math.max(1, Math.floor(diffMs / 1000));
    if (sec < 30) return "just now";
    if (sec < 60) return `${sec}s ago`;
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min} min ago`;
    const h = Math.floor(min / 60);
    if (h < 24) return `${h} h ago`;
    const days = Math.floor(h / 24);
    return `${days} d ago`;
}

export function formatClockUTC(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short",
    });
}

export function formatLocalDateTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export function chartTimeLabel(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });
}
