"use client";

import { Home, ArrowRight, Zap, Sun, MapPin, Activity, Cpu, Check, Copy } from 'lucide-react';
import { useState } from 'react';
import Link from 'next/link';

export interface MeterData {
    meter_id: string;
    meter_type?: string;
    latitude: number;
    longitude: number;
    generation?: number;
    consumption?: number;
    voltage?: number;
    is_compromised?: boolean;
    nodal_price?: number;
    location_name?: string;
    phase?: string;
    is_shed?: boolean;
}

interface MeterPopupProps {
    meter: MeterData;
}

export function MeterPopup({ meter }: MeterPopupProps) {
    const [copied, setCopied] = useState(false);
    const netEnergy = (meter.generation || 0) - (meter.consumption || 0);
    const isProducer = netEnergy > 0;
    const isProsumer = (meter.generation || 0) > 0 && !isProducer;

    const roleLabel = isProducer ? 'Producer' : isProsumer ? 'Prosumer' : 'Consumer';
    const iconBg = isProducer ? 'bg-emerald-500/20' : isProsumer ? 'bg-amber-500/20' : 'bg-blue-500/20';
    const iconColor = isProducer ? 'text-emerald-400' : isProsumer ? 'text-amber-400' : 'text-blue-400';

    const handleCopy = async (e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await navigator.clipboard.writeText(meter.meter_id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <div className="w-[280px] overflow-hidden rounded-[1.5rem] bg-[#0f172a]/95 backdrop-blur-2xl border border-white/10 shadow-2xl p-4 space-y-4">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${iconBg} border border-white/5`}>
                    <Cpu className={`w-4 h-4 ${iconColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 
                        onClick={handleCopy}
                        className={`font-black text-sm uppercase tracking-tight truncate leading-tight cursor-pointer transition-colors ${copied ? 'text-emerald-400' : 'text-white hover:text-indigo-400'}`}
                        title="Click to copy ID"
                    >
                        {meter.location_name || 'Smart Meter'}
                    </h3>
                    <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">
                            {meter.meter_type?.replace(/_/g, ' ') || 'SMART METER'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-2">
                <div className="bg-white/5 border border-white/5 rounded-xl p-2.5 space-y-1">
                    <div className="flex items-center gap-1.5">
                        <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Generation</span>
                    </div>
                    <p className="text-sm font-black text-white tracking-tighter">
                        {(meter.generation || 0).toFixed(2)} <span className="text-[9px] opacity-40">kWh</span>
                    </p>
                </div>
                <div className="bg-white/5 border border-white/5 rounded-xl p-2.5 space-y-1">
                    <div className="flex items-center gap-1.5">
                        <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Consumption</span>
                    </div>
                    <p className="text-sm font-black text-white tracking-tighter">
                        {(meter.consumption || 0).toFixed(2)} <span className="text-[9px] opacity-40">kWh</span>
                    </p>
                </div>
            </div>

            {/* Constraints & Environment */}
            <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-900/50 border border-white/5 rounded-xl p-2 flex flex-col items-center">
                    <span className="text-[7px] font-black text-slate-600 uppercase tracking-widest">Limits (Min/Max)</span>
                    <span className="text-[10px] font-bold text-slate-400 font-mono">0.1 / 500</span>
                </div>
                <div className="bg-slate-900/50 border border-white/5 rounded-xl p-2 flex flex-col items-center">
                    <span className="text-[7px] font-black text-slate-600 uppercase tracking-widest">Ambient Temp</span>
                    <span className="text-[10px] font-bold text-slate-400 font-mono">31.4°C</span>
                </div>
            </div>

            {/* Electrical Integrity */}
            {meter.is_shed ? (
                <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 flex items-center justify-between animate-pulse">
                    <div className="flex items-center gap-2">
                        <span className="text-[9px] font-black text-rose-400 uppercase tracking-widest">Status</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-black text-rose-400 uppercase tracking-widest">SHEDDED</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                    </div>
                </div>
            ) : (
                <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-xl p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Grid Sync</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-black text-white">{meter.voltage}V</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    </div>
                </div>
            )}

            {/* Footer */}
            <Link
                href={`/meter/${meter.meter_id}`}
                className="flex items-center justify-center gap-2 w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest rounded-xl transition-all active:scale-[0.98] group shadow-lg shadow-indigo-600/20"
            >
                <span>Full Telemetry</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
        </div>
    );
}
