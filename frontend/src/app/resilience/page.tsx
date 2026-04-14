"use client";

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
    Activity,
    ChevronLeft,
    AlertTriangle,
    Shield,
    Wifi,
    WifiOff,
    RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/common';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';
import { StatCard } from '@/components/ui/StatCard';
import { useNetwork } from '@/components/providers/NetworkProvider';
import type { GridHealth } from '@/lib/types';

const ResilienceDashboard = () => {
    const { getApiUrl, getWsUrl } = useNetwork();
    const [health, setHealth] = useState<GridHealth | null>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [isActionLoading, setIsActionLoading] = useState(false);

    const fetchHistory = useCallback(async () => {
        try {
            const res = await fetch(getApiUrl('/api/v1/grid/history?limit=30'));
            const data = await res.json();
            if (data.success) {
                // Reverse to have chronological order for chart
                setHistory(data.history.reverse());
            }
        } catch (e) {
            console.error("Failed to fetch history", e);
        }
    }, [getApiUrl]);

    useEffect(() => {
        const ws = new WebSocket(getWsUrl('ws'));
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

        fetchHistory();
        const interval = setInterval(fetchHistory, 15000); // Refresh history every 15s

        return () => {
            ws.close();
            clearInterval(interval);
        };
    }, [getWsUrl, fetchHistory]);

    const handleControlAction = async (action: 'island' | 'reconnect') => {
        setIsActionLoading(true);
        try {
            const res = await fetch(getApiUrl(`/api/v1/simulation/scenarios/${action}`), { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                console.log(`Grid ${action} successful`);
            } else {
                alert(`Action failed: ${data.message}`);
            }
        } catch (e) {
            console.error(`Action ${action} error`, e);
            alert(`Network error during ${action}`);
        } finally {
            setIsActionLoading(false);
        }
    };

    const freq = health?.frequency;
    const isIslanded = health?.island_status?.is_islanded || false;

    // Determine status color based on frequency deviation
    const freqDeviation = freq ? Math.abs(freq.value - 50.0) : 0;
    let freqStatus: 'success' | 'warning' | 'error' = 'success';
    if (freqDeviation > 0.5) freqStatus = 'error'; // +/- 0.5 Hz is critical
    else if (freqDeviation > 0.2) freqStatus = 'warning';

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
                            <h1 className="text-4xl font-black tracking-tighter text-white uppercase">Grid Resilience</h1>
                        </div>
                        <p className="text-slate-400 font-medium pl-14 uppercase tracking-tight">Frequency Stability & Microgrid Control</p>
                    </div>

                    <div className={`px-6 py-4 rounded-2xl flex items-center gap-4 ${isIslanded ? 'bg-amber-500/10 border-amber-500/20' : 'bg-emerald-500/10 border-emerald-500/20'} border`}>
                        <div className="text-right">
                            <div className={`text-xs font-bold uppercase tracking-widest ${isIslanded ? 'text-amber-400' : 'text-emerald-400'}`}>Grid Mode</div>
                            <div className={`text-xl font-black ${isIslanded ? 'text-amber-500' : 'text-emerald-500'}`}>
                                {isIslanded ? 'ISLANDED' : 'CONNECTED'}
                            </div>
                        </div>
                        {isIslanded ? <WifiOff className="w-8 h-8 text-amber-500" /> : <Wifi className="w-8 h-8 text-emerald-500" />}
                    </div>
                </div>

                {freq ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Main Frequency Gauge */}
                        <div className="lg:col-span-2 glass p-6 rounded-3xl relative overflow-hidden flex flex-col justify-center items-center">
                            <div className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-2">System Frequency</div>
                            <div className={`text-7xl font-black tracking-tighter ${freqStatus === 'success' ? 'text-white' :
                                freqStatus === 'warning' ? 'text-amber-400' : 'text-rose-500'
                                }`}>
                                {freq.value.toFixed(3)} <span className="text-2xl text-slate-500 font-bold">Hz</span>
                            </div>
                            <div className="mt-4 flex gap-2">
                                <div className="px-3 py-1 bg-white/5 rounded-full text-xs text-slate-400">
                                    Target: 50.00 Hz
                                </div>
                                <div className={`px-3 py-1 rounded-full text-xs font-bold ${freqDeviation < 0.05 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                                    }`}>
                                    Dev: {(freq.value - 50.0).toFixed(3)}
                                </div>
                            </div>
                        </div>

                        <StatCard
                            title="RoCoF"
                            value={freq.rocof.toFixed(4)}
                            unit="Hz/s"
                            icon={<Activity className="w-5 h-5 text-blue-400" />}
                            status={Math.abs(freq.rocof) > 0.1 ? 'warning' : 'neutral'}
                            trend="Inertia"
                            trendLabel="System"
                        />

                        <StatCard
                            title="Health Score"
                            value={health.health_score.toFixed(1)}
                            unit="pts"
                            icon={<Shield className="w-5 h-5 text-emerald-400" />}
                            status={health.health_score > 90 ? 'success' : 'warning'}
                            trend={health.health_score > 95 ? "Excellent" : "Nominal"}
                            trendLabel="Status"
                        />

                        {/* Frequency Chart */}
                        <div className="lg:col-span-2 glass p-6 rounded-3xl h-[300px]">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Frequency Stability (Hz)</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={history}>
                                    <defs>
                                        <linearGradient id="colorFreq" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                    <XAxis dataKey="timestamp" hide />
                                    <YAxis domain={[49.5, 50.5]} hide />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                        labelStyle={{ display: 'none' }}
                                    />
                                    <Area type="monotone" dataKey="frequency_hz" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorFreq)" strokeWidth={3} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Imbalance Chart */}
                        <div className="lg:col-span-2 glass p-6 rounded-3xl h-[300px]">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Power Balance (MW)</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={history}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                    <XAxis dataKey="timestamp" hide />
                                    <YAxis hide />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                        labelStyle={{ display: 'none' }}
                                    />
                                    <Line type="monotone" dataKey="imbalance_mw" stroke="#10b981" strokeWidth={3} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                ) : (
                    <div className="p-12 text-center text-slate-500 uppercase tracking-widest font-black flex flex-col items-center gap-4">
                        <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
                        Waiting for PMU telemetry...
                    </div>
                )}

                {/* Control Actions */}
                <div className="p-8 glass rounded-3xl border border-white/5">
                    <h3 className="text-lg font-bold text-white mb-6 uppercase tracking-tight">Operator Resilience Control</h3>
                    <div className="flex gap-4">
                        <button
                            disabled={isActionLoading || isIslanded}
                            onClick={() => handleControlAction('island')}
                            className={cn(
                                "relative overflow-hidden px-8 py-4 rounded-2xl uppercase text-[10px] font-black tracking-widest transition-all active:scale-95 border",
                                isIslanded
                                    ? "bg-slate-800 text-slate-600 border-white/5 grayscale cursor-not-allowed"
                                    : "bg-rose-500/10 text-rose-400 border-rose-500/20 hover:bg-rose-500/20 hover:border-rose-500/40 shadow-lg shadow-rose-500/10",
                                isActionLoading && "opacity-50 animate-pulse pointer-events-none"
                            )}
                        >
                            Emergency Islanding
                        </button>
                        <button
                            disabled={isActionLoading || !isIslanded}
                            onClick={() => handleControlAction('reconnect')}
                            className={cn(
                                "relative overflow-hidden px-8 py-4 rounded-2xl uppercase text-[10px] font-black tracking-widest transition-all active:scale-95 border",
                                !isIslanded
                                    ? "bg-slate-800 text-slate-600 border-white/5 grayscale cursor-not-allowed"
                                    : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20 hover:border-emerald-500/40 shadow-lg shadow-emerald-500/10",
                                isActionLoading && "opacity-50 animate-pulse pointer-events-none"
                            )}
                        >
                            Grid Resynchronization
                        </button>
                    </div>
                    {isIslanded && (
                        <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center gap-4 animate-pulse">
                            <AlertTriangle className="w-5 h-5 text-amber-500" />
                            <p className="text-xs font-bold text-amber-500 uppercase tracking-widest leading-none">
                                Currently Islanded: Grid stability relies on local DER and Battery resources.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ResilienceDashboard;
