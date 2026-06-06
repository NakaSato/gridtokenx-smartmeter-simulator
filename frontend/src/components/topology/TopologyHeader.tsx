import Link from 'next/link';
import { ArrowLeft, Grid3X3 } from 'lucide-react';
import type { TopologyCounts } from '@/lib/topology/types';

export function TopologyHeader({ counts }: { counts: TopologyCounts }) {
    return (
        <div className="absolute top-0 left-0 right-0 z-10 p-6 bg-gradient-to-b from-slate-900/90 to-transparent pointer-events-none">
            <div className="flex items-center gap-4">
                <Link href="/dashboard" className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all text-slate-300 backdrop-blur-md border border-white/10 pointer-events-auto">
                    <ArrowLeft className="w-6 h-6" />
                </Link>
                <div>
                    <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
                        <Grid3X3 className="w-7 h-7 text-indigo-400" />
                        Network Graph
                    </h1>
                    <p className="text-xs font-black text-slate-400 mt-1">
                        กราฟเครือข่าย • Node-Link Diagram / แผนภาพโหนดและเส้นเชื่อม • {counts.buses} Buses • {counts.lines} Lines • {counts.meters} Meters
                    </p>
                </div>
            </div>
        </div>
    );
}
