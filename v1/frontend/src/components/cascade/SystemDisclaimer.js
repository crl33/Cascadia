import { Info } from "lucide-react";

export const SystemDisclaimer = () => {
    return (
        <section
            className="co-glass rounded-2xl p-4 sm:p-5 mt-6"
            data-testid="system-disclaimer"
        >
            <div className="flex items-start gap-3">
                <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-white/60">
                    <Info className="h-3.5 w-3.5" />
                </span>
                <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] uppercase tracking-[0.20em] text-white/55">
                        Trust • Transparency • Disclaimer
                    </span>
                    <p className="text-xs sm:text-[13px] text-white/65 leading-relaxed">
                        Cascade Oracle is an{" "}
                        <span className="text-white/85">
                            experimental watershed intelligence dashboard
                        </span>
                        . It is{" "}
                        <span className="text-white/85">not</span> an official emergency
                        alert system. Observed data is sourced live from the U.S.
                        Geological Survey (USGS) Water Services. Where available, flood
                        thresholds are sourced from the National Weather Service /
                        National Water Prediction Service (NWPS); otherwise the system
                        explicitly labels the threshold source. Use NWS, local emergency
                        management, and official sources for life-safety decisions.
                    </p>
                    <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-white/55">
                        <span className="co-text-mono rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5">
                            Source: USGS Water Services
                        </span>
                        <span className="co-text-mono rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5">
                            Source: NOAA NWPS
                        </span>
                        <span className="co-text-mono rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5">
                            v0.1 • Phase 1 MVP
                        </span>
                    </div>
                </div>
            </div>
        </section>
    );
};
