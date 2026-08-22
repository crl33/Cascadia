import { motion } from "framer-motion";

/**
 * AmbientBackdrop
 *
 * Cinematic dark backdrop with:
 *  - solid deep navy canvas
 *  - subtle topographic SVG contour overlay
 *  - very mild gradient wash near top (≤20% viewport)
 *  - faint noise via SVG filter
 */
export const AmbientBackdrop = () => {
    return (
        <div
            aria-hidden="true"
            className="fixed inset-0 -z-10 overflow-hidden pointer-events-none"
            data-testid="ambient-backdrop"
        >
            {/* Solid base */}
            <div className="absolute inset-0 bg-[hsl(var(--co-bg-canvas))]" />

            {/* Top-only mild cyan/blue gradient (under 20% viewport) */}
            <div
                className="absolute inset-x-0 top-0 h-[18vh]"
                style={{
                    background:
                        "linear-gradient(180deg, hsl(199 80% 18% / 0.22) 0%, hsl(212 70% 14% / 0.10) 60%, transparent 100%)",
                }}
            />

            {/* Contour overlay (SVG pattern) */}
            <svg
                className="absolute inset-0 h-full w-full opacity-[0.06] mix-blend-screen"
                xmlns="http://www.w3.org/2000/svg"
                preserveAspectRatio="xMidYMid slice"
            >
                <defs>
                    <pattern
                        id="co-topo"
                        width="160"
                        height="160"
                        patternUnits="userSpaceOnUse"
                    >
                        <path
                            d="M0,80 C40,60 80,100 120,80 S200,60 240,80 M-20,120 C20,100 60,140 100,120 S180,100 220,120 M0,40 C40,20 80,60 120,40 S200,20 240,40"
                            fill="none"
                            stroke="hsl(191 92% 55%)"
                            strokeWidth="1"
                        />
                    </pattern>
                    <filter id="co-noise">
                        <feTurbulence
                            type="fractalNoise"
                            baseFrequency="0.9"
                            numOctaves="2"
                            stitchTiles="stitch"
                        />
                        <feColorMatrix type="saturate" values="0" />
                    </filter>
                </defs>
                <rect width="100%" height="100%" fill="url(#co-topo)" />
            </svg>

            {/* Faint noise */}
            <svg
                className="absolute inset-0 h-full w-full opacity-[0.025]"
                xmlns="http://www.w3.org/2000/svg"
            >
                <filter id="co-noise-2">
                    <feTurbulence
                        type="fractalNoise"
                        baseFrequency="0.85"
                        numOctaves="2"
                        stitchTiles="stitch"
                    />
                    <feColorMatrix type="saturate" values="0" />
                </filter>
                <rect width="100%" height="100%" filter="url(#co-noise-2)" />
            </svg>

            {/* Slow drifting cyan halo (very subtle) */}
            <motion.div
                aria-hidden="true"
                initial={{ opacity: 0.25, y: 0 }}
                animate={{ opacity: [0.18, 0.30, 0.18], y: [0, 12, 0] }}
                transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -top-32 left-1/3 h-[420px] w-[640px] rounded-full blur-3xl"
                style={{
                    background:
                        "radial-gradient(closest-side, hsl(191 92% 55% / 0.10), transparent 70%)",
                }}
            />
        </div>
    );
};
