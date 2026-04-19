"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Battery,
    BatteryCharging,
    Zap,
    ChevronLeft,
    Box,
    Shield,
    AlertTriangle,
    CheckCircle2,
} from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';
import { useNetwork } from '@/components/providers/NetworkProvider';
import type { GridHealth } from '@/lib/types';

interface GridEvent {
    id?: number;
    timestamp: string;
    event_type: string;
    severity: 'info' | 'warning' | 'critical';
    message: string;
    metadata?: Record<string, any>;
}

const VPPDashboard = () => {
    const { getWsUrl, getApiUrl } = useNetwork();
    const [health, setHealth] = useState<GridHealth | null>(null);
    const [events, setEvents] = useState<GridEvent[]>([]);

    useEffect(() => {
        const fetchEvents = async () => {
            try {
                const res = await fetch(getApiUrl('/api/v1/grid/events?limit=20'));
                if (res.ok) {
                    const data = await res.json();
                    setEvents(data.events || []);
                }
            } catch { /* silent */ }
        };
        fetchEvents();
        const interval = setInterval(fetchEvents, 10000);
        return () => clearInterval(interval);
    }, [getApiUrl]);

    useEffect(() => {
        const ws = new WebSocket(getWsUrl('/ws'));
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'grid_status') {
                    setHealth(data.data);
                }
            } catch (e) {
                console.error("WS invalid JSON", e);
            }
        };
        return () => ws.close();
    }, []);

    const vpp = health?.vpp;

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <Link href="/dashboard" className="p-2 hover:bg-white/5 rounded-xl transition-colors text-slate-400 hover:text-white">
                                <ChevronLeft className="w-6 h-6" />
                            </Link>
                            <h1 className="text-4xl font-black tracking-tighter text-white">VPP OPERATIONS</h1>
                        </div>
                        <p className="text-slate-400 font-medium pl-14">VIRTUAL POWER PLANT DISPATCH & AGGREGATION</p>
                    </div>

                    {vpp && (
                        <div className="glass px-6 py-4 rounded-2xl flex items-center gap-4">
                            <div className="text-right">
                                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">Active Cluster</div>
                                <div className="text-xl font-black text-emerald-400">{vpp.cluster_id}</div>
                            </div>
                            <Box className="w-8 h-8 text-emerald-500" />
                        </div>
                    )}
                </div>

                {vpp ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
                        <StatCard
                            title="Resource Count"
                            value={vpp.resource_count}
                            unit="Assets"
                            icon={<Box className="w-5 h-5 text-emerald-400" />}
                            trend={vpp.controllable_count}
                            trendLabel="Flex-Ready"
                            status="success"
                        />
                        <StatCard
                            title="Total Capacity"
                            value={vpp.total_capacity_kwh.toFixed(1)}
                            unit="kWh"
                            icon={<Battery className="w-5 h-5 text-slate-400" />}
                            status="neutral"
                        />
                        <StatCard
                            title="Flexibility Up"
                            value={vpp.flex_up_kw.toFixed(1)}
                            unit="kW"
                            icon={<Zap className="w-5 h-5 text-amber-400" />}
                            trend={vpp.total_capacity_kwh > 0 ? ((vpp.flex_up_kw / vpp.total_capacity_kwh) * 100).toFixed(0) : "0"}
                            trendLabel="% of Cap"
                            status="warning"
                        />
                        <StatCard
                            title="Grid Health"
                            value={health.health_score.toFixed(1)}
                            unit="pts"
                            icon={<Shield className="w-5 h-5 text-emerald-400" />}
                            trend={health.health_score > 90 ? "Optimal" : "Degraded"}
                            trendLabel="Stability"
                            status={health.health_score > 90 ? 'success' : 'warning'}
                        />
                        <StatCard
                            title="Carbon Saved"
                            value={((vpp.carbon_saved_g ?? 0) / 1000).toFixed(2)}
                            unit="kg"
                            icon={<Zap className="w-5 h-5 text-emerald-400" />}
                            trend={vpp.carbon_saved_g && vpp.carbon_saved_g > 0 ? "BESS Active" : "Diesel"}
                            trendLabel="Strategy"
                            status={(vpp.carbon_saved_g ?? 0) > 0 ? 'success' : 'neutral'}
                        />
                    </div>
                ) : (
                    <div className="p-12 text-center text-slate-500">
                        Waiting for VPP telemetry...
                    </div>
                )}

                {vpp && health?.settlement && (
                    <div className="space-y-4 pt-4 border-t border-white/5">
                        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1">Financial Settlement</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <StatCard
                                title="Grid Revenue"
                                value={health.settlement.total_grid_revenue.toFixed(2)}
                                unit="SOL"
                                icon={<Zap className="w-5 h-5 text-emerald-400" />}
                                status="success"
                            />
                            <StatCard
                                title="Grid Cost"
                                value={health.settlement.total_grid_cost.toFixed(2)}
                                unit="SOL"
                                icon={<Box className="w-5 h-5 text-rose-400" />}
                                status="error"
                            />
                            <StatCard
                                title="P2P Volume"
                                value={health.settlement.total_p2p_volume.toFixed(1)}
                                unit="kWh"
                                icon={<BatteryCharging className="w-5 h-5 text-blue-400" />}
                                status="info"
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* Grid Events */}
            <div className="space-y-3 pt-4 border-t border-white/5">
                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1">Grid Events</h2>
                {events.length === 0 ? (
                    <div className="text-center text-slate-600 text-sm py-8">No events recorded yet</div>
                ) : (
                    <div className="space-y-2">
                        {events.map((ev, i) => (
                            <div key={ev.id ?? i} className={`glass rounded-xl px-4 py-3 flex items-start gap-3 border ${
                                ev.severity === 'critical' ? 'border-rose-500/20' :
                                ev.severity === 'warning' ? 'border-amber-500/20' : 'border-white/5'
                            }`}>
                                {ev.severity === 'critical' || ev.severity === 'warning'
                                    ? <AlertTriangle className={`w-4 h-4 mt-0.5 shrink-0 ${ev.severity === 'critical' ? 'text-rose-400' : 'text-amber-400'}`} />
                                    : <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0 text-emerald-400" />
                                }
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className={`text-xs font-bold uppercase tracking-widest ${
                                            ev.severity === 'critical' ? 'text-rose-400' :
                                            ev.severity === 'warning' ? 'text-amber-400' : 'text-emerald-400'
                                        }`}>{ev.severity}</span>
                                        <span className="text-xs text-slate-500 font-mono">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                    <p className="text-sm text-slate-300 mt-0.5">{ev.message}</p>
                                    {ev.metadata && (
                                        <div className="mt-1 flex flex-wrap gap-2">
                                            {ev.metadata.loading_pct !== undefined && (
                                                <span className="text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded text-slate-400">
                                                    Loading: {Number(ev.metadata.loading_pct).toFixed(1)}%
                                                </span>
                                            )}
                                            {ev.metadata.line && (
                                                <span className="text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded text-slate-400">
                                                    {ev.metadata.line}
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default VPPDashboard;
