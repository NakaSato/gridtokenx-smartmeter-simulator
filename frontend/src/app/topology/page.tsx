"use client";

import { useState, useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import Link from 'next/link';
import { ArrowLeft, Info, Zap, Activity, Home, X, Gauge } from 'lucide-react';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import type { GridTopologyBus, GridTopologyLine, MeterSummary } from '@/lib/api/types';
import { cn } from '@/lib/common';

/** Convert per-interval energy (kWh) to average power (kW). Mirrors backend `_to_kw`. */
const toKw = (energyKwh: number, intervalSeconds: number): number =>
    intervalSeconds > 0 ? (energyKwh * 3600) / intervalSeconds : 0;

const METER_COLORS: Record<string, string> = {
    Solar_Prosumer: '#f59e0b',
    Hybrid_Prosumer: '#10b981',
    Battery_Storage: '#8b5cf6',
    EV_Charger: '#ec4899',
    DC_Fast_Charger: '#ef4444',
    Grid_Consumer: '#3b82f6',
};

/** Voltage-health class from per-unit voltage. */
const voltageClass = (pu: number): string =>
    pu < 0.95 ? 'v-under' : pu > 1.05 ? 'v-over' : 'v-ok';

type TopologyNodeKind = 'transformer' | 'feeder' | 'service' | 'meter';

interface SelectedNodeData {
    id: string;
    label: string;
    kind: TopologyNodeKind;
    busName?: string;
    meterId?: string;
    meterType?: string;
    vnKv?: number;
    voltagePu?: number;
    voltageV?: number;
    loadKw?: number;
    meterCount?: number;
    generationKw?: number;
    consumptionKw?: number;
}

type BreadthfirstLayoutOptions = cytoscape.LayoutOptions & {
    roots?: string;
    direction?: 'downward' | 'upward' | 'rightward' | 'leftward';
    directed?: boolean;
    spacingFactor?: number;
    avoidOverlap?: boolean;
    grid?: boolean;
    fit?: boolean;
    padding?: number;
    boundingBox?: { x1: number; y1: number; w: number; h: number };
};

const GridTopologyView = () => {
    const api = useSimulatorApi();
    const containerRef = useRef<HTMLDivElement>(null);
    const cyRef = useRef<cytoscape.Core | null>(null);
    const busNameToIdRef = useRef<Record<string, string>>({});
    const lineNameToIdRef = useRef<Record<string, string>>({});

    const [ready, setReady] = useState(false);
    const [counts, setCounts] = useState({ buses: 0, lines: 0, meters: 0 });
    const [stats, setStats] = useState({
        totalGenerationKw: 0,
        totalConsumptionKw: 0,
        avgVoltage: 230,
        totalLossesKw: 0,
        congestedLines: 0,
    });
    const [selectedNode, setSelectedNode] = useState<SelectedNodeData | null>(null);

    useEffect(() => {
        let mounted = true;
        let pollId: ReturnType<typeof setInterval> | null = null;

        const init = async () => {
            const [topo, metersData] = await Promise.all([
                api.getGridTopology().catch(() => null),
                api.listMeters({ limit: 10000 }).catch(() => null),
            ]);
            if (!mounted || !containerRef.current) return;
            const container = containerRef.current;

            const meterTypeById: Record<string, string> = {};
            (metersData?.meters ?? []).forEach((m: MeterSummary) => {
                meterTypeById[m.meter_id] = m.meter_type || 'Grid_Consumer';
            });

            const elements: cytoscape.ElementDefinition[] = [];
            const busNameToId: Record<string, string> = {};
            const lineNameToId: Record<string, string> = {};

            const buses: Record<string, GridTopologyBus> = topo?.buses ?? {};
            const lines: GridTopologyLine[] = topo?.lines ?? [];

            // Bus / transformer nodes.
            Object.entries(buses).forEach(([idx, bus]) => {
                const nodeId = `bus-${idx}`;
                busNameToId[bus.name] = nodeId;
                const kind: TopologyNodeKind = bus.type === 't' ? 'transformer' : bus.vn_kv > 1.0 ? 'feeder' : 'service';
                elements.push({
                    data: {
                        id: nodeId,
                        label: bus.name,
                        kind,
                        busName: bus.name,
                        vnKv: bus.vn_kv,
                        voltagePu: 1.0,
                        voltageV: bus.vn_kv * 1000,
                        loadKw: 0,
                        meterCount: (bus.meter_ids ?? []).length,
                        color: kind === 'transformer' ? '#f59e0b' : kind === 'feeder' ? '#6366f1' : '#3b82f6',
                    },
                    classes: 'v-ok',
                });

                // Meter leaf nodes hanging off their bus.
                (bus.meter_ids ?? []).forEach((meterId: string) => {
                    const mType = meterTypeById[meterId] || 'Grid_Consumer';
                    elements.push({
                        data: {
                            id: `meter-${meterId}`,
                            label: meterId.slice(0, 6),
                            kind: 'meter',
                            meterType: mType,
                            meterId,
                            generationKw: 0,
                            consumptionKw: 0,
                            voltageV: 230,
                            color: METER_COLORS[mType] || '#3b82f6',
                        },
                    });
                    elements.push({
                        data: { id: `mlink-${meterId}`, source: nodeId, target: `meter-${meterId}`, kind: 'service-drop' },
                    });
                });
            });

            // Electrical lines between buses.
            lines.forEach((line, i) => {
                const edgeId = `line-${i}`;
                lineNameToId[line.name] = edgeId;
                elements.push({
                    data: {
                        id: edgeId,
                        source: `bus-${line.from_bus}`,
                        target: `bus-${line.to_bus}`,
                        label: line.name,
                        lineName: line.name,
                        kind: 'line',
                        utilization: 0,
                        flowKw: 0,
                    },
                });
            });

            busNameToIdRef.current = busNameToId;
            lineNameToIdRef.current = lineNameToId;
            setCounts({
                buses: Object.keys(buses).length,
                lines: lines.length,
                meters: Object.keys(meterTypeById).length,
            });

            const cy = cytoscape({
                container,
                elements,
                style: [
                    {
                        selector: 'node',
                        style: {
                            'background-color': 'data(color)',
                            label: 'data(label)',
                            color: '#e2e8f0',
                            'font-size': '9px',
                            'font-weight': 'bold',
                            'text-valign': 'bottom',
                            'text-margin-y': 4,
                            'text-halign': 'center',
                            width: 24,
                            height: 24,
                            'border-width': 2,
                            'border-color': '#0f172a',
                        },
                    },
                    { selector: 'node[kind="transformer"]', style: { shape: 'round-rectangle', width: 46, height: 46, 'font-size': '11px' } },
                    { selector: 'node[kind="feeder"]', style: { shape: 'round-diamond', width: 34, height: 34 } },
                    { selector: 'node[kind="service"]', style: { shape: 'ellipse', width: 28, height: 28 } },
                    { selector: 'node[kind="meter"]', style: { shape: 'round-rectangle', width: 16, height: 16, 'font-size': '7px' } },
                    // Voltage health rings on buses.
                    { selector: 'node.v-under', style: { 'border-color': '#3b82f6', 'border-width': 4 } },
                    { selector: 'node.v-over', style: { 'border-color': '#ef4444', 'border-width': 4 } },
                    { selector: 'node.v-ok', style: { 'border-color': '#22c55e', 'border-width': 3 } },
                    { selector: 'node:selected', style: { 'border-color': '#ffffff', 'border-width': 4 } },
                    {
                        selector: 'edge',
                        style: {
                            width: 2,
                            'line-color': '#334155',
                            'target-arrow-color': '#334155',
                            'target-arrow-shape': 'triangle',
                            'arrow-scale': 0.7,
                            'curve-style': 'bezier',
                        },
                    },
                    { selector: 'edge[kind="service-drop"]', style: { width: 1, 'line-color': '#1e293b', 'line-style': 'dashed', 'target-arrow-shape': 'none' } },
                    { selector: 'edge.loaded', style: { 'line-color': '#f59e0b', 'target-arrow-color': '#f59e0b', width: 4 } },
                    { selector: 'edge.congested', style: { 'line-color': '#ef4444', 'target-arrow-color': '#ef4444', width: 6 } },
                ],
            });

            // Hierarchical top-down layout. Explicit roots and bounds avoid
            // a flat zero-height layout when Cytoscape cannot infer them.
            const rootBusIndex = Object.entries(buses).find(([, bus]) => bus.name === topo?.topology?.substation)?.[0]
                ?? Object.keys(buses)[0];
            const layoutOptions: BreadthfirstLayoutOptions = {
                name: 'breadthfirst',
                directed: false,
                roots: rootBusIndex ? `#bus-${rootBusIndex}` : undefined,
                direction: 'downward',
                spacingFactor: 0.85,
                avoidOverlap: true,
                grid: false,
                fit: true,
                padding: 40,
                boundingBox: {
                    x1: 0,
                    y1: 0,
                    w: Math.max(container.clientWidth, window.innerWidth, 960),
                    h: Math.max(container.clientHeight, window.innerHeight, 720),
                },
            };
            cy.layout(layoutOptions).run();
            cy.resize();
            cy.fit(undefined, 40);

            cy.on('tap', 'node', (evt) => setSelectedNode(evt.target.data() as SelectedNodeData));
            cy.on('tap', (evt) => {
                if (evt.target === cy) setSelectedNode(null);
            });

            cyRef.current = cy;
            setReady(true);

            // Live telemetry: mutate node/edge data in place — no re-layout, no flicker.
            const poll = async () => {
                if (!mounted) return;
                const tele = await api.getGridTelemetry().catch(() => null);
                if (!tele || !cyRef.current) return;
                const c = cyRef.current;

                c.batch(() => {
                    // Buses.
                    Object.entries(tele.buses ?? {}).forEach(([name, b]) => {
                        const id = busNameToIdRef.current[name];
                        if (!id) return;
                        const node = c.getElementById(id);
                        if (node.empty()) return;
                        const pu = b.voltage_pu ?? 1.0;
                        node.data('voltagePu', pu);
                        node.data('voltageV', pu * (node.data('vnKv') || 0.23) * 1000);
                        node.data('loadKw', b.load_kw ?? 0);
                        node.removeClass('v-under v-ok v-over').addClass(voltageClass(pu));
                    });

                    // Lines.
                    const lineStates = tele.lines ?? {};
                    Object.entries(lineStates).forEach(([name, l]) => {
                        const id = lineNameToIdRef.current[name];
                        if (!id) return;
                        const edge = c.getElementById(id);
                        if (edge.empty()) return;
                        const util = l.utilization_pct ?? 0;
                        edge.data('utilization', util);
                        edge.data('flowKw', l.flow_kw ?? 0);
                        edge.removeClass('loaded congested');
                        if (util > 80) edge.addClass('congested');
                        else if (util > 40) edge.addClass('loaded');
                    });

                    // Meter readings.
                    const readings = tele.readings ?? [];
                    readings.forEach((r) => {
                        const mid = r.meter_serial ?? r.meter_id;
                        if (!mid) return;
                        const node = c.getElementById(`meter-${mid}`);
                        if (node.empty()) return;
                        const interval = r.interval_seconds || 15;
                        node.data('generationKw', toKw(r.energy_generated || 0, interval));
                        node.data('consumptionKw', toKw(r.energy_consumed || 0, interval));
                        node.data('voltageV', r.voltage || 230);
                    });
                });

                // HUD stats.
                const readings = tele.readings ?? [];
                const summary = tele.summary ?? {};
                const congested = Object.values(tele.lines ?? {}).filter((l) => (l.utilization_pct ?? 0) > 80).length;
                if (readings.length > 0) {
                    setStats({
                        totalGenerationKw: readings.reduce((s, r) => s + toKw(r.energy_generated || 0, r.interval_seconds || 15), 0),
                        totalConsumptionKw: readings.reduce((s, r) => s + toKw(r.energy_consumed || 0, r.interval_seconds || 15), 0),
                        avgVoltage: readings.reduce((s, r) => s + (r.voltage || 230), 0) / readings.length,
                        totalLossesKw: summary.total_losses_kw ?? 0,
                        congestedLines: congested,
                    });
                } else {
                    setStats((prev) => ({ ...prev, totalLossesKw: summary.total_losses_kw ?? prev.totalLossesKw, congestedLines: congested }));
                }

                // Keep the inspect panel live for the selected node.
                setSelectedNode((prev) => {
                    if (!prev || !cyRef.current) return prev;
                    const n = cyRef.current.getElementById(prev.id);
                    return n.empty() ? prev : ({ ...n.data() } as SelectedNodeData);
                });
            };

            poll();
            pollId = setInterval(poll, 2000);
        };

        init().catch((e) => console.error('[topo] init failed:', e));

        return () => {
            mounted = false;
            if (pollId) clearInterval(pollId);
            cyRef.current?.destroy();
            cyRef.current = null;
        };
    }, [api]);

    return (
        <div className="h-screen w-full relative bg-slate-950 overflow-hidden">
            {/* Cytoscape canvas */}
            <div ref={containerRef} className="absolute inset-0" />

            {/* Header */}
            <div className="absolute top-0 left-0 right-0 z-10 p-6 bg-gradient-to-b from-slate-900/90 to-transparent pointer-events-none">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="p-3 rounded-2xl bg-white/5 hover:bg-white/10 transition-all text-slate-300 backdrop-blur-md border border-white/10 pointer-events-auto">
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
                            <Info className="w-7 h-7 text-indigo-400" />
                            Grid Topology
                        </h1>
                        <p className="text-xs uppercase tracking-widest font-black text-slate-400 mt-1">
                            Hierarchical • {counts.buses} Buses • {counts.lines} Lines • {counts.meters} Meters
                        </p>
                    </div>
                </div>
            </div>

            {!ready && (
                <div className="absolute inset-0 flex items-center justify-center text-white">
                    <div className="text-center">
                        <Zap className="w-12 h-12 text-amber-500 mx-auto mb-4 animate-pulse" />
                        <h2 className="text-xl font-black mb-2">Loading Grid Topology</h2>
                        <p className="text-slate-400 text-sm">Building hierarchical network…</p>
                    </div>
                </div>
            )}

            {/* Stats HUD */}
            <div className="absolute top-24 right-6 z-10 glass px-6 py-4 rounded-2xl border-white/10 bg-slate-900/60 backdrop-blur-xl flex flex-col gap-4">
                <div className="flex items-center gap-8">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-500/20 rounded-xl"><Zap className="w-5 h-5 text-emerald-400" /></div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase">Generation</div>
                            <div className="text-lg font-black text-emerald-400">{stats.totalGenerationKw.toFixed(1)} <span className="text-xs">kW</span></div>
                        </div>
                    </div>
                    <div className="h-10 w-px bg-white/10" />
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-rose-500/20 rounded-xl"><Activity className="w-5 h-5 text-rose-400" /></div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase">Consumption</div>
                            <div className="text-lg font-black text-rose-400">{stats.totalConsumptionKw.toFixed(1)} <span className="text-xs">kW</span></div>
                        </div>
                    </div>
                </div>
                <div className="h-px bg-white/10 w-full" />
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-xl"><Home className="w-5 h-5 text-blue-400" /></div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase">Net Power</div>
                            <div className={cn("text-lg font-black", stats.totalGenerationKw > stats.totalConsumptionKw ? "text-emerald-400" : "text-rose-400")}>
                                {(stats.totalGenerationKw - stats.totalConsumptionKw).toFixed(1)} <span className="text-xs">kW</span>
                            </div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] font-black text-slate-400 uppercase">Avg Voltage</div>
                        <div className="text-lg font-black text-indigo-400">{stats.avgVoltage.toFixed(1)} <span className="text-xs">V</span></div>
                    </div>
                </div>
                <div className="h-px bg-white/10 w-full" />
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-amber-500/20 rounded-xl"><Gauge className="w-5 h-5 text-amber-400" /></div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase">System Losses</div>
                            <div className="text-lg font-black text-amber-400">{stats.totalLossesKw.toFixed(1)} <span className="text-xs">kW</span></div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] font-black text-slate-400 uppercase">Congested Lines</div>
                        <div className={cn("text-lg font-black", stats.congestedLines > 0 ? "text-rose-400" : "text-emerald-400")}>{stats.congestedLines}</div>
                    </div>
                </div>
            </div>

            {/* Node Inspect Panel */}
            {selectedNode && (
                <div className="absolute bottom-6 right-6 z-20 glass px-5 py-4 rounded-2xl border border-white/10 bg-slate-900/80 backdrop-blur-xl w-72">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <div className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">{selectedNode.kind}</div>
                            <div className="text-sm font-black text-white break-all">{selectedNode.busName || selectedNode.meterId || selectedNode.label}</div>
                        </div>
                        <button onClick={() => setSelectedNode(null)} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 transition-all"><X className="w-4 h-4" /></button>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3">
                        <div>
                            <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Voltage</div>
                            <div className="text-sm font-black text-white">{(selectedNode.voltageV ?? 0).toFixed(1)} V</div>
                            {selectedNode.voltagePu !== undefined && <div className="text-[9px] font-bold text-slate-500">{selectedNode.voltagePu.toFixed(3)} pu</div>}
                        </div>
                        {selectedNode.kind === 'meter' ? (
                            <>
                                <div>
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Type</div>
                                    <div className="text-sm font-black text-white">{(selectedNode.meterType || '').replace('_', ' ')}</div>
                                </div>
                                <div>
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Generation</div>
                                    <div className="text-sm font-black text-emerald-400">{(selectedNode.generationKw ?? 0).toFixed(2)} kW</div>
                                </div>
                                <div>
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Consumption</div>
                                    <div className="text-sm font-black text-rose-400">{(selectedNode.consumptionKw ?? 0).toFixed(2)} kW</div>
                                </div>
                            </>
                        ) : (
                            <>
                                <div>
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Load</div>
                                    <div className="text-sm font-black text-white">{(selectedNode.loadKw ?? 0).toFixed(2)} kW</div>
                                </div>
                                <div>
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Meters</div>
                                    <div className="text-sm font-black text-white">{selectedNode.meterCount ?? 0}</div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Legend */}
            <div className="absolute bottom-6 left-6 z-10 glass p-4 rounded-xl space-y-2.5">
                <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Hierarchy</div>
                <div className="flex items-center gap-3"><div className="w-3 h-3 rounded bg-amber-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Transformer</span></div>
                <div className="flex items-center gap-3"><div className="w-3 h-3 rotate-45 bg-indigo-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Feeder (MV)</span></div>
                <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-blue-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Service Bus / Meter</span></div>
                <div className="h-px bg-white/10 w-full" />
                <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Voltage Ring</div>
                <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full border-2 border-green-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Nominal</span></div>
                <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full border-2 border-blue-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Under / Over-volt</span></div>
                <div className="h-px bg-white/10 w-full" />
                <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Line Loading</div>
                <div className="flex items-center gap-3"><div className="w-4 h-1 bg-amber-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Loaded (&gt;40%)</span></div>
                <div className="flex items-center gap-3"><div className="w-4 h-1 bg-red-500" /><span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Congested (&gt;80%)</span></div>
            </div>
        </div>
    );
};

export default GridTopologyView;
