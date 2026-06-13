import Link from 'next/link';
import { ArrowLeft, Grid3X3 } from 'lucide-react';
import type { TopologyCounts } from '@/lib/topology/types';

export function TopologyHeader({ counts }: { counts: TopologyCounts }) {
    return (
        <div className="absolute top-0 left-0 right-0 z-10 p-6 pointer-events-none">
            <div className="flex items-center gap-4">
                <Link href="/dashboard" className="hmi-btn pointer-events-auto p-3" aria-label="Back to dashboard">
                    <ArrowLeft className="w-6 h-6" />
                </Link>
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight text-[var(--txt-val)] flex items-center gap-3">
                        <Grid3X3 className="w-7 h-7 text-[var(--lbl)]" />
                        Network Graph
                    </h1>
                    <p className="hmi-lbl mt-1">
                        กราฟเครือข่าย • Node-Link Diagram / แผนภาพโหนดและเส้นเชื่อม • <span className="mono">{counts.buses}</span> Buses • <span className="mono">{counts.lines}</span> Lines • <span className="mono">{counts.meters}</span> Meters
                    </p>
                </div>
            </div>
        </div>
    );
}
