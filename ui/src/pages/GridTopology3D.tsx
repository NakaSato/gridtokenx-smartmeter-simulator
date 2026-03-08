import { useState, useEffect, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';
import { Link } from 'react-router-dom';
import { ArrowLeft, Box, Info } from 'lucide-react';
import { useNetwork } from '../context/NetworkContext';

interface Bus {
    name: string;
    vn_kv: number;
    type: string;
    lat?: number;
    lng?: number;
    fx?: number;
    fy?: number;
    fz?: number;
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
    const [liveNodes, setLiveNodes] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(true);
    const { getApiUrl } = useNetwork();

    useEffect(() => {
        // Fetch base topology
        fetch(getApiUrl('/api/grid/topology'))
            .then(res => res.json())
            .then(topo => {
                setData(topo);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load topology:", err);
                setLoading(false);
            });

        // Connect to Live Feed via WebSocket
        const wsUrl = getApiUrl('/ws').replace(/^http/, 'ws');
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'C2C_LIVE_FEED') {
                    const payload = message.data;
                    setLiveNodes(prev => ({
                        ...prev,
                        [payload.node_id]: payload
                    }));
                }
            } catch (e) {
                console.error("WebSocket message parse error:", e);
            }
        };

        return () => ws.close();
    }, []);

    const graphData = useMemo(() => {
        if (!data) return { nodes: [], links: [] };

        const nodes = Object.entries(data.buses).map(([id, bus]) => {
            // Check if we have live data for this node
            // Assuming node_id for live feed is the bus name or id. We map to name for lookup.
            const liveData = liveNodes[bus.name] || liveNodes[id] || {};

            // Determine active color based on live status
            let color = bus.vn_kv > 1.0 ? '#f59e0b' : '#3b82f6';
            if (liveData.status === 'CHARGING') color = '#22c55e'; // Green
            if (liveData.status === 'DISCHARGING') color = '#ef4444'; // Red

            return {
                id: parseInt(id),
                name: bus.name,
                val: bus.vn_kv * 10, // Base size based on voltage
                fx: bus.fx, // Spatial Persistence: fixed X
                fy: bus.fy, // Spatial Persistence: fixed Y
                fz: bus.fz, // Spatial Persistence: fixed Z
                color,
                busType: bus.type,
                livePowerKw: liveData.power_kw || 0,
                liveStatus: liveData.status || 'OFFLINE'
            };
        });

        const links = data.lines.map(line => {
            // Infer power flow based on to_bus live power for demo visualization
            const targetLive = liveNodes[line.to_bus] || {};
            const powerKw = targetLive.power_kw || 0;

            return {
                source: line.from_bus,
                target: line.to_bus,
                name: line.name,
                flowPower: Math.abs(powerKw)
            };
        });

        return { nodes, links };
    }, [data, liveNodes]);

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
                    nodeLabel={(node: any) => {
                        const isCharging = node.liveStatus === 'CHARGING';
                        const colorClass = isCharging ? 'text-green-400' : 'text-indigo-400';
                        const powerHtml = Math.abs(node.livePowerKw) > 0
                            ? `<div class="text-[11px] font-black text-amber-400 mt-1">POWER: ${node.livePowerKw} kW</div>`
                            : '';

                        return `
                            <div class="glass p-3 rounded-xl border border-white/10 shadow-2xl">
                               <div class="text-[10px] font-black ${colorClass} uppercase tracking-widest mb-1">
                                   Bus Node • ${node.liveStatus}
                               </div>
                               <div class="text-sm font-black text-white">${node.name}</div>
                               <div class="text-[9px] font-bold text-slate-500 mt-2">TYPE: ${node.busType}</div>
                               <div class="text-[9px] font-bold text-slate-400">DESIGN KV: ${node.val / 10} kV</div>
                               ${powerHtml}
                            </div>
                        `;
                    }}
                    nodeThreeObject={(node: any) => {
                        let geometry;
                        const isCharging = node.liveStatus === 'CHARGING';
                        const isDischarging = node.liveStatus === 'DISCHARGING';

                        // Define dynamic emissive glowing colors
                        let emissiveHex = 0x000000;
                        if (isCharging) emissiveHex = 0x22c55e;
                        if (isDischarging) emissiveHex = 0xef4444;

                        const material = new THREE.MeshPhongMaterial({
                            color: node.color,
                            emissive: emissiveHex,
                            emissiveIntensity: emissiveHex !== 0x000000 ? 0.8 : 0,
                            shininess: 50,
                            transparent: true,
                            opacity: 0.95
                        });

                        const size = Math.max(node.val, 5); // Ensure a minimum visible scale

                        // Substation / High Voltage
                        if (node.val > 10) {
                            // Large main cube block
                            geometry = new THREE.BoxGeometry(size * 1.5, size * 1.5, size * 1.5);
                        }
                        // Specific type rendering based on implicit type from Pandapower (e.g., 'b' bus, 'n' node)
                        else if (node.busType === 'b') {
                            // Hexagon / Diamond profile for primary distribution nodes
                            geometry = new THREE.OctahedronGeometry(size);
                        }
                        else {
                            // Flat cylinder to represent a standard consumer/asset (like a building/meter unit)
                            geometry = new THREE.CylinderGeometry(size, size, size * 0.4, 16);
                        }

                        // Combine into Mesh
                        const mesh = new THREE.Mesh(geometry, material);

                        // Add an optional wireframe outline layer for extra UI flair
                        const edges = new THREE.EdgesGeometry(geometry);
                        const edgeMaterial = new THREE.LineBasicMaterial({
                            color: isCharging ? 0x4ade80 : 0xffffff,
                            transparent: true,
                            opacity: isCharging ? 0.9 : 0.2
                        });
                        const wireframe = new THREE.LineSegments(edges, edgeMaterial);
                        mesh.add(wireframe);

                        return mesh;
                    }}
                    nodeColor={(node: any) => node.color}
                    nodeRelSize={2}
                    linkWidth={(link: any) => link.flowPower > 0 ? 2 : 1}
                    linkDirectionalParticles={(link: any) => link.flowPower > 0 ? 2 : 0}
                    linkDirectionalParticleSpeed={(link: any) => Math.min(link.flowPower * 0.005, 0.05)}
                    linkColor={(link: any) => link.flowPower > 0 ? '#10b981' : '#475569'}
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
