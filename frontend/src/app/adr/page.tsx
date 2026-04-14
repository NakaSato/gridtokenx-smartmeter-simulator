"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    ChevronLeft,
    AlertTriangle,
    Clock,
    DollarSign,
    Activity
} from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';
import { useNetwork } from '@/components/providers/NetworkProvider';
import type { GridHealth } from '@/lib/types';

const ADRDashboard = () => {
    const { getWsUrl } = useNetwork();
    const [health, setHealth] = useState<GridHealth | null>(null);

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

    const tariff = health?.tariff;
    const adr = health?.adr_event;

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
                            <h1 className="text-4xl font-black tracking-tighter text-white">ADR CONTROL</h1>
                        </div>
                        <p className="text-slate-400 font-medium pl-14">AUTOMATED DEMAND RESPONSE & DYNAMIC PRICING</p>
                    </div>

                    {adr && adr.active && (
                        <div className="bg-rose-500/10 border border-rose-500/20 px-6 py-4 rounded-2xl flex items-center gap-4 animate-pulse">
                            <div className="text-right">
                                <div className="text-xs font-bold text-rose-400 uppercase tracking-widest">Active Event</div>
                                <div className="text-xl font-black text-rose-500">{adr.type}</div>
                            </div>
                            <AlertTriangle className="w-8 h-8 text-rose-500" />
                        </div>
                    )}
                </div>

                {tariff ? (
                    <div className="space-y-8">
                        {/* Dynamic Pricing Section */}
                        <div>
                            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Current Tariff ({tariff.type})</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <StatCard
                                    title="Import Rate"
                                    value={tariff.import_rate.toFixed(3)}
                                    unit="SOL/kWh"
                                    icon={<DollarSign className="w-5 h-5 text-emerald-400" />}
                                    status={tariff.is_peak ? 'warning' : 'success'}
                                    trend={tariff.is_peak ? "PEAK" : "OFF-PEAK"}
                                    trendLabel="Period"
                                />
                                <StatCard
                                    title="Tariff Type"
                                    value={tariff.type}
                                    unit=""
                                    icon={<Clock className="w-5 h-5 text-blue-400" />}
                                    status="neutral"
                                />
                                <StatCard
                                    title="Event Status"
                                    value={adr?.active ? "Active" : "Normal"}
                                    unit=""
                                    icon={<Activity className="w-5 h-5 text-slate-400" />}
                                    status={adr?.active ? 'error' : 'success'}
                                />
                            </div>
                        </div>

                        {/* Forecast Chart Placeholder */}
                        {/* In a real app we'd use Recharts here to show the tariff.forecast array */}
                        <div className="mt-6 p-6 glass rounded-2xl border border-white/5">
                            <h3 className="text-lg font-bold text-white mb-2">Price Forecast (Next 6h)</h3>
                            <div className="h-40 flex items-end gap-1 w-full">
                                {tariff.forecast.map((price, i) => (
                                    <div
                                        key={i}
                                        className="bg-emerald-500/20 hover:bg-emerald-500/40 transition-colors rounded-t-sm w-full"
                                        style={{ height: `${(price / 0.5) * 100}%` }}
                                        title={`+${i * 15}min: ${price.toFixed(3)} SOL`}
                                    ></div>
                                ))}
                            </div>
                            <div className="flex justify-between text-xs text-slate-500 mt-2">
                                <span>Now</span>
                                <span>+6h</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="p-12 text-center text-slate-500">
                        Waiting for Tariff telemetry...
                    </div>
                )}
            </div>
        </div>
    );
};

export default ADRDashboard;
