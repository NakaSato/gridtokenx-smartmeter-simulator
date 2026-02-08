import { useState, useEffect, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { Link } from 'react-router-dom';
import { ArrowLeft, Box, Info } from 'lucide-react';

interface Bus {
    name: string;
    vn_kv: number;
    type: string;
    lat?: number;
    lng?: number;
}

interface Line {
    name: string;
    from_bus: number;
    to_bus: number;
    length_km: number;
    max_i_ka: number;
}

interface TopologyData {
    buses: Record<string, Bus>;
    lines: Line[];
}

const GridTopology3D = () => {
    const [data, setData] = useState<TopologyData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/grid/topology')
            .then(res => res.json())
            .then(topo => {
                setData(topo);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load topology:", err);
                setLoading(false);
            });
    }, []);

    const graphData = useMemo(() => {
        if (!data) return { nodes: [], links: [] };

        const nodes = Object.entries(data.buses).map(([id, bus]) => ({
            id: parseInt(id),
            name: bus.name,
            val: bus.vn_kv * 10, // Size based on voltage
            color: bus.vn_kv > 1.0 ? '#f59e0b' : '#3b82f6',
            busType: bus.type
        }));

        const links = data.lines.map(line => ({
            source: line.from_bus,
            target: line.to_bus,
            name: line.name
        }));

        return { nodes, links };
    }, [data]);

    return (
        <div className="h-screen w-full bg-slate-950 relative overflow-hidden">
            {/* Header Overlay */}
            <div className="absolute top-0 left-0 right-0 z-[1000] p-6 flex justify-between items-start pointer-events-none">
                <div className="pointer-events-auto flex items-center gap-4">
                    <Link to="/dashboard" className="glass p-3 rounded-xl hover:bg-white/10 transition-colors text-slate-300">
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div className="glass px-6 py-3 rounded-xl">
                        <div className="flex items-center gap-3">
                            <Box className="w-6 h-6 text-indigo-400" />
                            <h1 className="text-xl font-black text-white">3D Grid Topology</h1>
                        </div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">
                            Digital Twin • Spatial Persistence • Live Feed
                        </p>
                    </div>
                </div>

                <div className="pointer-events-auto glass p-4 rounded-xl max-w-xs space-y-3">
                    <div className="flex items-center gap-2 text-indigo-400">
                        <Info className="w-4 h-4" />
                        <span className="text-[10px] font-black uppercase tracking-widest">Controls</span>
                    </div>
                    <p className="text-[10px] font-medium text-slate-400 leading-relaxed">
                        Left-click to rotate. Right-click to pan. Scroll to zoom. Hover on nodes to inspect Bus Voltage (kV) and Topology Type.
                    </p>
                </div>
            </div>

            {loading ? (
                <div className="h-full flex flex-col items-center justify-center space-y-4">
                    <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
                    <p className="text-xs font-black text-slate-500 uppercase tracking-widest italic animate-pulse">Mapping Neural Path...</p>
                </div>
            ) : (
                <ForceGraph3D
                    graphData={graphData}
                    backgroundColor="#020617"
                    nodeLabel={(node: any) => `
                        <div class="glass p-3 rounded-xl border border-white/10 shadow-2xl">
                           <div class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">Bus Node</div>
                           <div class="text-sm font-black text-white">${node.name}</div>
                           <div class="text-[9px] font-bold text-slate-500 mt-2">TYPE: ${node.busType}</div>
                           <div class="text-[9px] font-bold text-slate-400">MAGNITUDE: ${node.val / 10} kV</div>
                        </div>
                    `}
                    nodeColor={(node: any) => node.color}
                    nodeRelSize={2}
                    linkWidth={1}
                    linkColor={() => '#475569'}
                    showNavInfo={false}
                />
            )}

            {/* Legend Overlay */}
            <div className="absolute bottom-6 left-6 z-[1000] glass p-4 rounded-xl space-y-3">
                <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_10px_#f59e0b]" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">High Voltage Bus</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_#3b82f6]" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Distribution Bus</span>
                </div>
                <div className="h-px bg-white/10" />
                <div className="flex items-center gap-3">
                    <div className="w-8 h-0.5 bg-slate-600" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Substation Line</span>
                </div>
            </div>
        </div>
    );
};

export default GridTopology3D;
