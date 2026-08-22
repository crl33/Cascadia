import { Badge } from "@/components/ui/badge";
import {
    RISK_LABEL,
    RISK_PULSE_CLASS,
    riskBgClass,
    riskBorderClass,
    riskTextClass,
} from "@/lib/risk-style";
import { ShieldCheck, Activity, AlertTriangle, AlertOctagon, HelpCircle } from "lucide-react";

const ICON_FOR = {
    calm: ShieldCheck,
    watch: Activity,
    elevated: AlertTriangle,
    flood: AlertOctagon,
    unknown: HelpCircle,
};

export const RiskBadge = ({ state = "unknown", reason, withIcon = true }) => {
    const Icon = ICON_FOR[state] || HelpCircle;
    const pulse = RISK_PULSE_CLASS[state] || "";
    return (
        <Badge
            variant="outline"
            className={`gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium uppercase tracking-[0.14em] ${riskBgClass(
                state,
            )} ${riskBorderClass(state)} ${riskTextClass(state)} ${pulse}`}
            title={reason || RISK_LABEL[state]}
            data-testid="risk-badge"
            data-risk={state}
        >
            {withIcon && <Icon className="h-3 w-3" />}
            {RISK_LABEL[state]}
        </Badge>
    );
};
