import { AmbientBackdrop } from "@/components/cascade/AmbientBackdrop";
import { NavBar } from "@/components/cascade/NavBar";
import { PhaseRoadmap } from "@/components/cascade/PhaseRoadmap";
import { SystemDisclaimer } from "@/components/cascade/SystemDisclaimer";

export default function Roadmap() {
    return (
        <div className="relative min-h-screen text-white">
            <AmbientBackdrop />
            <NavBar />
            <main
                className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-10 flex flex-col gap-6"
                data-testid="roadmap-main"
            >
                <header className="co-glass rounded-2xl px-5 py-6 sm:px-7 sm:py-8">
                    <span className="text-[10px] uppercase tracking-[0.22em] text-white/55">
                        Cascade Oracle • Vision
                    </span>
                    <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight mt-1 text-white">
                        A staged path from observation to foresight.
                    </h1>
                    <p className="mt-3 max-w-3xl text-sm sm:text-base text-white/65 leading-relaxed">
                        Cascade Oracle is a cinematic watershed intelligence platform.
                        It is intentionally built in phases so each capability can be
                        verified, traced back to credible sources, and improved
                        without sacrificing trust. Phase 1 is live today; phases 2–5
                        are deliberately not active and described here so the
                        architecture is transparent.
                    </p>
                    <p className="mt-3 max-w-3xl text-sm text-white/55">
                        <span className="text-white/85">Guiding principle:</span>{" "}
                        Prototype the experience. Operationalize the data. Then earn
                        the right to claim foresight.
                    </p>
                </header>

                <PhaseRoadmap variant="full" />

                <SystemDisclaimer />
            </main>
        </div>
    );
}
