"use client";

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
    ChevronLeft,
    Zap,
    Sun,
    History,
    Activity,
    ArrowUpRight,
    ArrowDownRight,
    MapPin,
    Gauge,
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';
import { useSimulatorApi } from '@/hooks/useSimulatorApi';
import { StatCard } from '@/components/ui/StatCard';
import type { MeterSummary, MeterReading } from '@/lib/api/types';

const MeterDetails = () => {
    const { meterId } = useParams<{ meterId: string }>();
    const api = useSimulatorApi();

    const [metadata, setMetadata] = useState<MeterSummary | null>(null);
    const [readings, setReadings] = useState<MeterReading[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (!meterId) return;
        try {
            const [meta, hist] = await Promise.all([
                api.getMeter(meterId),
                api.getMeterReadings(meterId, 50),
            ]);
            setMetadata(meta);
            setReadings(hist?.readings ?? []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    }, [meterId, api]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    if (loading && !metadata) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (error || !metadata) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
                <div className="w-16 h-16 bg-rose-500/20 rounded-full flex items-center justify-center mb-4">
                    <Activity className="w-8 h-8 text-rose-500" />
                </div>
                <h2 className="text-2xl font-black text-white mb-2 uppercase">Meter Not Found</h2>
                <p className="text-slate-400 mb-6">{error || `Could not find data for ${meterId}`}</p>
                <Link href="/map" className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors">
                    Return to Map
                </Link>
            </div>
        );
    }

    // Readings come newest-first from the API; chart oldest -> newest left to right.
    const chartData = [...readings].reverse().map((r) => ({
        time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        generation: r.energy_generated ?? 0,
        consumption: r.energy_consumed ?? 0,
    }));

    const latest = readings[0];
    const totalGen = readings.reduce((s, r) => s + (r.energy_generated ?? 0), 0);
    const totalCons = readings.reduce((s, r) => s + (r.energy_consumed ?? 0), 0);
    const hasCoords = metadata.latitude != null && metadata.longitude != null;

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            <div className="max-w-7xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <Link href="/map" className="p-2 hover:bg-white/5 rounded-xl transition-colors text-slate-400 hover:text-white">
                                <ChevronLeft className="w-6 h-6" />
                            </Link>
                            <h1 className="text-4xl font-black tracking-tighter text-white uppercase">{metadata.location_name}</h1>
                        </div>
                        <div className="flex items-center gap-4 pl-14">
                            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                <Activity className="w-3.5 h-3.5" />
                                {metadata.meter_id}
                            </div>
                            {hasCoords && (
                                <>
                                    <div className="h-4 w-px bg-white/10" />
                                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                        <MapPin className="w-3.5 h-3.5" />
                                        {metadata.latitude!.toFixed(4)}, {metadata.longitude!.toFixed(4)}
                                    </div>
                                </>
                            )}
                            <div className="h-4 w-px bg-white/10" />
                            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                Bus {metadata.bus_name ?? '—'} · Phase {metadata.phase}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {metadata.has_solar && (
                            <div className="px-4 py-2 rounded-xl border font-black text-xs uppercase tracking-widest bg-amber-500/10 border-amber-500/20 text-amber-400 flex items-center gap-2">
                                <Sun className="w-3.5 h-3.5" /> {metadata.solar_capacity ?? 0} kW PV
                            </div>
                        )}
                        <div className="px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-xl font-black text-xs text-blue-400 uppercase tracking-widest">
                            {metadata.meter_type}
                        </div>
                        <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl font-black text-xs text-emerald-400 uppercase tracking-widest">
                            {metadata.status}
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard
                        title="Latest Generation"
                        value={(latest?.energy_generated ?? 0).toFixed(3)}
                        unit="kWh"
                        icon={<Sun className="w-5 h-5 text-amber-400" />}
                        status="neutral"
                        trend="Live"
                        trendLabel="Solar"
                    />
                    <StatCard
                        title="Latest Consumption"
                        value={(latest?.energy_consumed ?? 0).toFixed(3)}
                        unit="kWh"
                        icon={<Zap className="w-5 h-5 text-rose-400" />}
                        status="neutral"
                        trend="Live"
                        trendLabel="Load"
                    />
                    <StatCard
                        title="Voltage"
                        value={(latest?.voltage ?? metadata.voltage ?? 0).toFixed(1)}
                        unit="V"
                        icon={<Gauge className="w-5 h-5 text-indigo-400" />}
                        status="neutral"
                        trend={`PF ${(latest?.power_factor ?? 0).toFixed(2)}`}
                        trendLabel={`${(latest?.frequency ?? 0).toFixed(1)} Hz`}
                    />
                    <StatCard
                        title="Net (window)"
                        value={(totalGen - totalCons).toFixed(3)}
                        unit="kWh"
                        icon={(totalGen - totalCons) >= 0
                            ? <ArrowUpRight className="w-5 h-5 text-emerald-400" />
                            : <ArrowDownRight className="w-5 h-5 text-rose-400" />}
                        status={(totalGen - totalCons) >= 0 ? 'success' : 'warning'}
                        trend={`${readings.length} readings`}
                        trendLabel="Accumulated"
                    />
                </div>

                {/* History Chart */}
                <div className="glass rounded-3xl p-8 border border-white/5 space-y-6">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                            <History className="w-5 h-5 text-indigo-400" />
                            Energy History
                        </h3>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-amber-500 rounded-full" />
                                <span className="text-[10px] font-bold text-slate-500 uppercase">Gen</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-rose-500 rounded-full" />
                                <span className="text-[10px] font-bold text-slate-500 uppercase">Cons</span>
                            </div>
                        </div>
                    </div>

                    <div className="h-[400px] w-full mt-4">
                        {chartData.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                                No readings yet — start the simulation
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorGen" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="colorCons" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                    <XAxis dataKey="time" stroke="#475569" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} minTickGap={40} />
                                    <YAxis stroke="#475569" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px' }}
                                        labelStyle={{ color: '#94a3b8', fontWeight: 'bold', marginBottom: '4px' }}
                                    />
                                    <Area type="monotone" dataKey="generation" stroke="#f59e0b" fillOpacity={1} fill="url(#colorGen)" strokeWidth={3} />
                                    <Area type="monotone" dataKey="consumption" stroke="#f43f5e" fillOpacity={1} fill="url(#colorCons)" strokeWidth={3} />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                {/* Recent Readings Table */}
                <div className="glass rounded-3xl p-8 border border-white/5 space-y-6">
                    <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                        <Activity className="w-5 h-5 text-indigo-400" />
                        Recent Readings
                    </h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-white/5">
                                    <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Time</th>
                                    <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Generation</th>
                                    <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Consumption</th>
                                    <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Voltage</th>
                                    <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">PF</th>
                                    <th className="pb-4 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Temp</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {readings.slice(0, 15).map((r) => (
                                    <tr key={r.reading_id} className="hover:bg-white/5 transition-colors">
                                        <td className="py-4 text-xs font-bold text-slate-400">{new Date(r.timestamp).toLocaleTimeString()}</td>
                                        <td className="py-4 text-xs font-black text-amber-400">{(r.energy_generated ?? 0).toFixed(3)} kWh</td>
                                        <td className="py-4 text-xs font-black text-rose-400">{(r.energy_consumed ?? 0).toFixed(3)} kWh</td>
                                        <td className="py-4 text-xs font-bold text-white">{(r.voltage ?? 0).toFixed(1)} V</td>
                                        <td className="py-4 text-xs font-bold text-slate-400">{(r.power_factor ?? 0).toFixed(2)}</td>
                                        <td className="py-4 text-xs font-bold text-slate-400 text-right">{(r.temperature ?? 0).toFixed(1)} °C</td>
                                    </tr>
                                ))}
                                {readings.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="py-8 text-center text-xs font-bold text-slate-500 uppercase tracking-widest">
                                            No readings recorded yet
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MeterDetails;
