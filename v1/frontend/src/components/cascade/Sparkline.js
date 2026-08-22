import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { riskAccentHSL } from "@/lib/risk-style";

export const Sparkline = ({ series = [], state = "calm", height = 56 }) => {
    const accent = `hsl(${riskAccentHSL(state)})`;
    const data = (series || []).map((p) => ({ t: p.t, v: p.v }));
    if (data.length < 2) {
        return (
            <div
                className="flex items-center justify-center h-14 text-[11px] font-mono text-white/35"
                data-testid="sparkline-empty"
            >
                no recent series
            </div>
        );
    }
    const values = data.map((d) => d.v);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = (max - min) * 0.12 || 0.5;
    return (
        <div data-testid="sparkline" style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
                    <YAxis hide domain={[min - pad, max + pad]} />
                    <defs>
                        <linearGradient id={`spark-${state}`} x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor={accent} stopOpacity={0.35} />
                            <stop offset="100%" stopColor={accent} stopOpacity={1} />
                        </linearGradient>
                    </defs>
                    <Line
                        type="monotone"
                        dataKey="v"
                        stroke={`url(#spark-${state})`}
                        strokeWidth={1.6}
                        dot={false}
                        isAnimationActive={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
