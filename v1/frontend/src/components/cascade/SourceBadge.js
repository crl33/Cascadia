import { Badge } from "@/components/ui/badge";
import {
    BadgeCheck,
    ShieldCheck,
    Hourglass,
    MinusCircle,
    Snowflake,
} from "lucide-react";
import { sourceMeta } from "@/lib/risk-style";

const ICONS = {
    official_nwps: BadgeCheck,
    configured_validated: ShieldCheck,
    configured_pending: Hourglass,
    thresholds_unavailable: MinusCircle,
    nrcs_snotel: Snowflake,
};

export const SourceBadge = ({
    source = "thresholds_unavailable",
    title,
    short = false,
}) => {
    const m = sourceMeta(source);
    const Icon = ICONS[source] || MinusCircle;
    return (
        <Badge
            variant="outline"
            className={`gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium tracking-[0.04em] ${m.bg} ${m.border} ${m.text}`}
            title={title || m.label}
            data-testid="source-badge"
            data-source={source}
        >
            <Icon className="h-3 w-3" />
            {short ? m.short : m.label}
        </Badge>
    );
};
