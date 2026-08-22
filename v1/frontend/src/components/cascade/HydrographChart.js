import {
    Area,
    CartesianGrid,
    ComposedChart,
    Line,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { chartTimeLabel, formatNumber } from "@/lib/format";
import { riskAccentHSL } from "@/lib/risk-style";

function CustomTooltip({ active, payload, label }) {
    if (!active || !payload || payload.length === 0) return null;
    return (
        <div className="co-glass-strong rounded-md px-2.5 py-2 text-xs" data-testid="hydrograph-tooltip">
            <div className="font-mono text-[11px] text-white/55">
                {chartTimeLabel(label)}
            </div>
            {payload.map((p) => (
                <div key={p.dataKey} className="flex items-center gap-2 mt-0.5">
                    <span
                        aria-hidden
                        className="inline-block h-1.5 w-3 rounded"
                        style={{ background: p.stroke || p.color }}
                    />
                    <span className="text-white/85 font-mono">
                        {formatNumber(p.value, 2)} {p.unit || "ft"}
                    </span>
                </div>
            ))}
        </div>
    );
}

export const HydrographChart = ({ snapshot, height = 320 }) => {
    if (!snapshot) return null;
    const { gage_height, thresholds, risk_state } = snapshot;
    const accent = `hsl(${riskAccentHSL(risk_state)})`;
    const calmAccent = `hsl(${riskAccentHSL("calm")})`;

    const data = (gage_height.series || []).map((p) => ({
        t: p.t,
        v: p.v,
    }));

    if (data.length === 0) {
        return (
            <div
                className="co-glass rounded-xl px-4 py-10 text-center text-sm text-white/55"
                data-testid="hydrograph-empty"
            >
                No recent observations available for this gauge.
            </div>
        );
    }

    const values = data.map((d) => d.v);
    let min = Math.min(...values);
    let max = Math.max(...values);
    const thrVals = [
        thresholds?.action,
        thresholds?.minor,
        thresholds?.moderate,
        thresholds?.major,
    ].filter((v) => typeof v === "number");
    if (thrVals.length) {
        // Only include thresholds that are within reasonable range of observed data
        // to avoid distorting Y axis when datums differ.
        const maxDataDelta = max + (max - min) * 4 + 4;
        const minDataDelta = min - (max - min) * 4 - 4;
        for (const t of thrVals) {
            if (t < maxDataDelta && t > minDataDelta) {
                min = Math.min(min, t);
                max = Math.max(max, t);
            }
        }
    }
    const pad = (max - min) * 0.12 || 0.5;

    const showThr = (k) => {
        const v = thresholds?.[k];
        if (typeof v !== "number") return null;
        if (v > max + pad * 2 || v < min - pad * 2) return null;
        return v;
    };

    return (
        <div data-testid="station-detail-hydrograph-chart" style={{ width: "100%", height }}>
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                    data={data}
                    margin={{ top: 12, right: 16, bottom: 12, left: 8 }}
                >
                    <defs>
                        <linearGradient id="hydro-fill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={accent} stopOpacity={0.35} />
                            <stop offset="100%" stopColor={accent} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid stroke="hsl(215 22% 22% / 0.55)" strokeDasharray="2 4" />
                    <XAxis
                        dataKey="t"
                        tickFormatter={chartTimeLabel}
                        tick={{ fontSize: 11, fill: "hsl(215 14% 62%)" }}
                        axisLine={{ stroke: "hsl(215 22% 22% / 0.6)" }}
                        tickLine={false}
                        minTickGap={32}
                    />
                    <YAxis
                        domain={[min - pad, max + pad]}
                        tick={{ fontSize: 11, fill: "hsl(215 14% 62%)" }}
                        axisLine={{ stroke: "hsl(215 22% 22% / 0.6)" }}
                        tickLine={false}
                        width={42}
                        tickFormatter={(v) => formatNumber(v, 1)}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(215 22% 35%)", strokeDasharray: "3 3" }} />

                    {showThr("action") !== null && showThr("action") !== undefined && (
                        <ReferenceLine
                            y={thresholds.action}
                            stroke="hsl(38 92% 58%)"
                            strokeDasharray="4 4"
                            label={{ value: `Action ${formatNumber(thresholds.action, 1)} ft`, position: "insideTopRight", fill: "hsl(38 92% 72%)", fontSize: 10 }}
                        />
                    )}
                    {showThr("minor") !== null && showThr("minor") !== undefined && (
                        <ReferenceLine
                            y={thresholds.minor}
                            stroke="hsl(32 96% 56%)"
                            strokeDasharray="4 4"
                            label={{ value: `Minor ${formatNumber(thresholds.minor, 1)} ft`, position: "insideTopRight", fill: "hsl(32 96% 72%)", fontSize: 10 }}
                        />
                    )}
                    {showThr("moderate") !== null && showThr("moderate") !== undefined && (
                        <ReferenceLine
                            y={thresholds.moderate}
                            stroke="hsl(6 86% 56%)"
                            strokeDasharray="4 4"
                            label={{ value: `Moderate ${formatNumber(thresholds.moderate, 1)} ft`, position: "insideTopRight", fill: "hsl(6 86% 72%)", fontSize: 10 }}
                        />
                    )}
                    {showThr("major") !== null && showThr("major") !== undefined && (
                        <ReferenceLine
                            y={thresholds.major}
                            stroke="hsl(6 86% 56%)"
                            strokeWidth={1.4}
                            label={{ value: `Major ${formatNumber(thresholds.major, 1)} ft`, position: "insideTopRight", fill: "hsl(6 86% 78%)", fontSize: 10 }}
                        />
                    )}

                    <Area
                        type="monotone"
                        dataKey="v"
                        stroke="transparent"
                        fill="url(#hydro-fill)"
                        isAnimationActive={false}
                    />
                    <Line
                        type="monotone"
                        dataKey="v"
                        stroke={accent}
                        strokeWidth={1.8}
                        dot={false}
                        activeDot={{ r: 3, fill: calmAccent, stroke: "hsl(var(--co-bg-canvas))", strokeWidth: 1.5 }}
                        isAnimationActive={false}
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
};
