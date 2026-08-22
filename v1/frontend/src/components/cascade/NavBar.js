import { Link, useLocation } from "react-router-dom";
import { Activity, Compass, RefreshCw } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

import { timeAgo } from "@/lib/format";

export const NavBar = ({
    lastUpdatedAt,
    onRefresh,
    isRefreshing = false,
}) => {
    const location = useLocation();
    const isRoadmap = location.pathname === "/roadmap";

    return (
        <div
            className="sticky top-0 z-40 border-b border-white/10 bg-[hsl(var(--co-bg-canvas)/0.72)] backdrop-blur-xl"
            data-testid="nav-bar"
        >
            <div className="mx-auto max-w-7xl h-14 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-3">
                <Link to="/" className="flex items-center gap-2.5 group" data-testid="nav-brand">
                    <span className="relative flex h-8 w-8 items-center justify-center rounded-md border border-white/15 bg-white/[0.05]">
                        <Activity className="h-4 w-4 text-[hsl(var(--co-cyan))]" />
                        <motion.span
                            aria-hidden
                            className="absolute inset-0 rounded-md"
                            initial={{ opacity: 0.18 }}
                            animate={{ opacity: [0.10, 0.22, 0.10] }}
                            transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
                            style={{
                                boxShadow:
                                    "0 0 0 1px hsl(191 92% 55% / 0.20), 0 0 18px hsl(191 92% 55% / 0.18)",
                            }}
                        />
                    </span>
                    <div className="flex flex-col leading-tight">
                        <span className="font-display text-sm sm:text-[15px] font-semibold tracking-tight text-white/95">
                            Cascade Oracle
                        </span>
                        <span className="hidden sm:block text-[10px] uppercase tracking-[0.18em] text-white/50">
                            Watershed Foresight
                        </span>
                    </div>
                </Link>

                <div className="hidden md:flex items-center gap-1 text-xs uppercase tracking-[0.16em] text-white/45">
                    <span>Washington</span>
                    <span className="text-white/30">•</span>
                    <span>Puget Sound / Cascades</span>
                </div>

                <div className="flex items-center gap-2 sm:gap-3">
                    <div
                        className="hidden sm:flex flex-col items-end leading-tight"
                        data-testid="nav-last-updated"
                    >
                        <span className="text-[10px] uppercase tracking-[0.16em] text-white/45">
                            Updated
                        </span>
                        <span className="font-mono text-xs text-white/85">
                            {timeAgo(lastUpdatedAt)}
                        </span>
                    </div>

                    <TooltipProvider delayDuration={200}>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={onRefresh}
                                    disabled={isRefreshing}
                                    className="h-9 w-9 border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] text-white/85"
                                    data-testid="nav-refresh-button"
                                    aria-label="Refresh data"
                                >
                                    <RefreshCw
                                        className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
                                    />
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="co-glass-strong text-xs">
                                Manual refresh • auto every 5 min
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>

                    <Link
                        to={isRoadmap ? "/" : "/roadmap"}
                        className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.04] px-2.5 sm:px-3 h-9 text-xs sm:text-sm text-white/80 hover:bg-white/[0.08] hover:text-white transition-colors"
                        data-testid="nav-roadmap-link"
                    >
                        <Compass className="h-3.5 w-3.5" />
                        <span className="hidden sm:inline">{isRoadmap ? "Dashboard" : "Roadmap"}</span>
                    </Link>
                </div>
            </div>
        </div>
    );
};
