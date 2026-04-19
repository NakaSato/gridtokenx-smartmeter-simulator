"use client";

import dynamic from 'next/dynamic';
import { useState, useEffect, useMemo, useRef, type FC } from 'react';
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });
import * as THREE from 'three';
import Link from 'next/link';
import { ArrowLeft, Info, Zap, Activity, Home } from 'lucide-react';
import { useNetwork } from '@/components/providers/NetworkProvider';
import { cn } from '@/lib/common';

interface Bus {
    name: string;
    vn_kv: number;
    type: string;
    fx?: number;
    fy?: number;
    fz?: number;
}

interface House {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    phase: string;
    generation: number;
    consumption: number;
    voltage: number;
}

interface GridTopology3DProps {}

const GridTopology3D: FC<GridTopology3DProps> = () => {
    const [data, setData] = useState<{ buses: Record<string, Bus>; lines: any[] } | null>(null);
    const [stats, setStats] = useState({
        totalGeneration: 0,
        totalConsumption: 0,
        avgVoltage: 230,
        phaseBalance: { A: 0, B: 0, C: 0 } as Record<string, number>,
        producers: 0,
        prosumers: 0,
        consumers: 0
    });
    const { getApiUrl, getWsUrl } = useNetwork();
    const materialsRef = useRef<Record<string, THREE.ShaderMaterial>>({});
    const requestRef = useRef<number>(null);

    const [meters, setMeters] = useState<House[]>([]);

    useEffect(() => {
        let mounted = true;

        // Fetch base topology
        fetch(getApiUrl('/api/v1/grid/topology'))
            .then(res => res.json())
            .then(topo => {
                if (topo.error && mounted) {
                    console.log("Grid topology not available, will generate from meters...");
                } else if (mounted) {
                    setData(topo);
                }
            })
            .catch(err => {
                console.error("Failed to load topology:", err);
            });

        // Fetch meter status and generate fallback if needed
        fetch(getApiUrl('/api/v1/simulation/status'))
            .then(res => res.json())
            .then(statusData => {
                if (statusData.meters && mounted) {
                    const mappedHouses = statusData.meters.map((m: any, idx: number) => ({
                        id: m.meter_id,
                        name: m.location_name || `House ${idx + 1}`,
                        latitude: m.latitude || 9.528326082141575,
                        longitude: m.longitude || 99.99007762999207,
                        phase: m.phase || 'A',
                        generation: 0,
                        consumption: 0,
                        voltage: 230
                    }));
                    setMeters(mappedHouses);
                }
            })
            .catch(err => console.error("Failed to fetch meter status:", err));

        // WebSocket connection
        const wsUrl = getWsUrl('/ws');
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'meter_readings' && message.readings) {
                    const readings = message.readings;

                    setMeters(prev => prev.map(house => {
                        const reading = readings.find((r: any) => r.meter_id === house.id);
                        if (reading) {
                            return {
                                ...house,
                                generation: reading.energy_generated || 0,
                                consumption: reading.energy_consumed || 0,
                                voltage: reading.voltage || 230
                            };
                        }
                        return house;
                    }));

                    const totalGen = readings.reduce((sum: number, r: any) => sum + (r.energy_generated || 0), 0);
                    const totalCons = readings.reduce((sum: number, r: any) => sum + (r.energy_consumed || 0), 0);
                    const avgVolt = readings.reduce((sum: number, r: any) => sum + (r.voltage || 230), 0) / readings.length;
                    const phaseBalance: any = { A: 0, B: 0, C: 0 };
                    const producers = readings.filter((r: any) => r.energy_generated > r.energy_consumed).length;
                    const prosumers = readings.filter((r: any) => r.energy_generated > 0 && r.energy_generated < r.energy_consumed).length;
                    const consumers = readings.filter((r: any) => r.energy_generated === 0).length;

                    readings.forEach((r: any) => {
                        const phase = r.phase || 'A';
                        phaseBalance[phase] = (phaseBalance[phase] || 0) + 1;
                    });

                    setStats({
                        totalGeneration: totalGen,
                        totalConsumption: totalCons,
                        avgVoltage: avgVolt,
                        phaseBalance,
                        producers,
                        prosumers,
                        consumers
                    });
                }
            } catch (e) {
                console.error("WS error:", e);
            }
        };

        const animate = (t: number) => {
            Object.values(materialsRef.current).forEach(mat => {
                mat.uniforms.time.value = t / 1000;
            });
            requestRef.current = requestAnimationFrame(animate);
        };
        requestRef.current = requestAnimationFrame(animate);

        return () => {
            mounted = false;
            ws.close();
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [getWsUrl, getApiUrl]);

    // Generate fallback graph when meters are loaded but no grid topology
    useEffect(() => {
        if (!data && meters.length > 0) {
            const buses: Record<string, Bus> = {};
            const lines: any[] = [];

            // Create bus for each meter
            meters.forEach((house, idx) => {
                const busId = (idx + 1).toString(); // Start from 1 to avoid potential issues with 0
                buses[busId] = {
                    name: house.name,
                    vn_kv: 0.4,
                    type: 'b',
                    fx: (house.longitude - 99.99007762999207) * 111320,
                    fy: 4,
                    fz: (house.latitude - 9.528326082141575) * 111320
                };

                // Connect to previous meter (radial network)
                if (idx > 0) {
                    lines.push({
                        name: `Line ${idx}`,
                        from_bus: idx, // maps to busId (idx)
                        to_bus: idx + 1, // maps to busId (idx + 1)
                        length_km: 0.1
                    });
                }
            });

            // Add main transformer
            const transformerId = 0;
            buses[transformerId.toString()] = {
                name: 'Main Transformer',
                vn_kv: 11,
                type: 't',
                fx: 0,
                fy: 10,
                fz: 0
            };

            // Connect transformer to first meter
            if (meters.length > 0) {
                lines.push({
                    name: 'Main Feeder',
                    from_bus: transformerId,
                    to_bus: 1, // First meter busId
                    length_km: 0.5
                });
            }

            setData({ buses, lines });
        }
    }, [data, meters]);

    const graphData = useMemo(() => {
        if (!data) return { nodes: [], links: [] };

        const nodes = Object.entries(data.buses).map(([id, bus]) => {
            return {
                id: parseInt(id),
                name: bus.name,
                val: bus.vn_kv * 10,
                fx: bus.fx,
                fy: bus.fy,
                fz: bus.fz,
                color: bus.vn_kv > 1.0 ? '#f59e0b' : '#3b82f6',
                busType: bus.type,
                livePowerKw: 0,
                liveStatus: 'OFFLINE'
            };
        });

        const links = data.lines.map((line, idx) => {
            return {
                id: `link-${idx}`,
                source: parseInt(line.from_bus),
                target: parseInt(line.to_bus),
                name: line.name,
                loadingPercent: 0
            };
        });

        return { nodes, links };
    }, [data]);

    if (!data) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-slate-950 text-white">
                <div className="text-center">
                    <Zap className="w-12 h-12 text-amber-500 mx-auto mb-4 animate-pulse" />
                    <h2 className="text-xl font-black mb-2">Loading Grid Topology</h2>
                    <p className="text-slate-400 text-sm">Fetching 3D network data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen w-full relative bg-slate-950 overflow-hidden">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 z-10 p-6 bg-gradient-to-b from-slate-900/90 to-transparent">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="p-3 rounded-2xl bg-white/5 hover:bg-white/10 transition-all text-slate-300 backdrop-blur-md border border-white/10">
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
                            <Info className="w-7 h-7 text-indigo-400" />
                            Grid Topology 3D
                        </h1>
                        <p className="text-xs uppercase tracking-widest font-black text-slate-400 mt-1">
                            Force-Directed Graph • {Object.keys(data.buses).length} Buses • {data.lines.length} Lines
                        </p>
                    </div>
                </div>
            </div>

            {/* 3D Graph */}
            <ForceGraph3D
                graphData={graphData}
                backgroundColor="#020617"
                nodeLabel={(node: any) => {
                    const house = meters.find(h => h.id === node.name || h.id === node.id.toString());
                    const isHouse = !!house;
                    const powerHtml = Math.abs(node.livePowerKw) > 0
                        ? `<div class="text-[11px] font-black text-amber-400 mt-1">POWER: ${node.livePowerKw} kW</div>`
                        : '';
                     const isSensitive = node.name?.startsWith('EGAT-TWR-') || node.id?.toString().startsWith('EGAT-TWR-');
                     return `
                         <div class="glass p-3 rounded-xl border border-white/10 shadow-2xl bg-slate-900/95">
                            <div class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">
                                ${isHouse ? 'Smart Meter' : 'Bus Node'} • ${node.liveStatus}
                            </div>
                            <div class="text-sm font-black text-white">${node.name}</div>
                            <div class="text-[9px] font-bold text-slate-500 mt-2">TYPE: ${isSensitive ? 'REDACTED' : node.busType}</div>
                            <div class="text-[9px] font-bold text-slate-400">VOLTAGE: ${isSensitive ? 'REDACTED' : node.val / 10 + ' kV'}</div>
                            ${powerHtml}
                         </div>
                     `;
                }}
                nodeThreeObject={(node: any) => {
                    const house = meters.find(h => h.id === node.name || h.id === node.id.toString());
                    const isHouse = !!house;

                    let emissiveHex = 0x000000;

                    const nodeColor = isHouse
                        ? (house.generation > house.consumption ? '#10b981' : (house.generation > 0 ? '#f59e0b' : '#3b82f6'))
                        : node.color;

                    const material = new THREE.MeshPhongMaterial({
                        color: nodeColor,
                        emissive: emissiveHex,
                        emissiveIntensity: emissiveHex !== 0x000000 ? 0.8 : 0,
                        shininess: 50,
                        transparent: true,
                        opacity: 0.95
                    });

                    const size = Math.max(node.val, 5);
                    let geometry;

                    if (isHouse) {
                        const buildingHeight = 10 + (house.consumption / 10) * 15;
                        geometry = new THREE.BoxGeometry(size * 1.2, buildingHeight, size * 1.2);
                    } else if (node.val > 10) {
                        geometry = new THREE.BoxGeometry(size * 1.5, size * 1.5, size * 1.5);
                    } else if (node.busType === 'b') {
                        geometry = new THREE.OctahedronGeometry(size);
                    } else {
                        geometry = new THREE.CylinderGeometry(size, size, size * 0.4, 16);
                    }

                    const mesh = new THREE.Mesh(geometry, material);
                    const edges = new THREE.EdgesGeometry(geometry);
                    const edgeMaterial = new THREE.LineBasicMaterial({
                        color: 0xffffff,
                        transparent: true,
                        opacity: 0.2
                    });
                    const wireframe = new THREE.LineSegments(edges, edgeMaterial);
                    mesh.add(wireframe);

                    return mesh;
                }}
                nodeColor={(node: any) => node.color}
                nodeRelSize={2}
                linkThreeObject={(link: any) => {
                    const material = new THREE.LineBasicMaterial({
                        color: 0x3b82f6,
                        transparent: true,
                        opacity: 0.6
                    });
                    const curve = new THREE.LineCurve3(
                        new THREE.Vector3(link.source.x, link.source.y, link.source.z),
                        new THREE.Vector3(link.target.x, link.target.y, link.target.z)
                    );
                    const geometry = new THREE.TubeGeometry(curve, 32, 0.8, 8, false);
                    return new THREE.Mesh(geometry, material);
                }}
                onNodeClick={(_node: any) => {
                    // Node click handler
                }}
                showNavInfo={false}
            />

            {/* Stats HUD */}
            <div className="absolute top-24 right-6 z-10 glass px-6 py-4 rounded-2xl border-white/10 bg-slate-900/60 backdrop-blur-xl flex flex-col gap-4">
                <div className="flex items-center gap-8">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-500/20 rounded-xl">
                            <Zap className="w-5 h-5 text-emerald-400" />
                        </div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase">Generation</div>
                            <div className="text-lg font-black text-emerald-400">{stats.totalGeneration.toFixed(1)} <span className="text-xs">kWh</span></div>
                        </div>
                    </div>
                    <div className="h-10 w-px bg-white/10" />
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-rose-500/20 rounded-xl">
                            <Activity className="w-5 h-5 text-rose-400" />
                        </div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase">Consumption</div>
                            <div className="text-lg font-black text-rose-400">{stats.totalConsumption.toFixed(1)} <span className="text-xs">kWh</span></div>
                        </div>
                    </div>
                </div>
                <div className="h-px bg-white/10 w-full" />
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-xl">
                            <Home className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase">Net Energy</div>
                            <div className={cn(
                                "text-lg font-black",
                                stats.totalGeneration > stats.totalConsumption ? "text-emerald-400" : "text-rose-400"
                            )}>
                                {(stats.totalGeneration - stats.totalConsumption).toFixed(1)} <span className="text-xs">kWh</span>
                            </div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] font-black text-slate-400 uppercase">Avg Voltage</div>
                        <div className="text-lg font-black text-indigo-400">{stats.avgVoltage.toFixed(1)} <span className="text-xs">V</span></div>
                    </div>
                </div>
            </div>

            {/* Legend */}
            <div className="absolute bottom-6 left-6 z-10 glass p-4 rounded-xl space-y-3">
                <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_#3b82f6]" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Normal Line</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_#ef4444]" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Congested (&gt;80%)</span>
                </div>
                <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-green-500 shadow-[0_0_10px_#22c55e]" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active P2P Flow</span>
                </div>
            </div>
        </div>
    );
};

export default GridTopology3D;
