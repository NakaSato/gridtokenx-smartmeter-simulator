"use client";

import { Home, ArrowRight, Zap, Sun, MapPin } from 'lucide-react';
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
}

interface MeterPopupProps {
    meter: MeterData;
}

export function MeterPopup({ meter }: MeterPopupProps) {
    const netEnergy = (meter.generation || 0) - (meter.consumption || 0);
    const voltagePercent = (((meter.voltage || 230) / 230) * 100).toFixed(0);
    const isProducer = netEnergy > 0;
    const isProsumer = (meter.generation || 0) > 0 && !isProducer;

    const badgeClass = isProducer
        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
        : isProsumer
            ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
            : 'bg-blue-500/20 text-blue-400 border-blue-500/30';

    const roleLabel = isProducer ? 'Producer' : isProsumer ? 'Prosumer' : 'Consumer';
    const iconBg = isProducer ? 'bg-emerald-500/20' : isProsumer ? 'bg-amber-500/20' : 'bg-blue-500/20';
    const iconColor = isProducer ? 'text-emerald-400' : isProsumer ? 'text-amber-400' : 'text-blue-400';

    return (
        <div className="w-[260px] overflow-hidden rounded-xl bg-[#0f172a]/95 backdrop-blur-xl border border-white/10 shadow-2xl">
            {/* Header */}
            <div className="px-3 pt-3 pb-2">
                <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-lg ${iconBg}`}>
                        <Zap className={`w-4 h-4 ${iconColor}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <h3 className="font-bold text-white text-xs truncate">{meter.location_name || meter.meter_id}</h3>
                        <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[9px] text-slate-500 font-mono">{meter.meter_id}</span>
                            {meter.phase && (
                                <span className="text-[9px] text-slate-600">Ph{meter.phase}</span>
                            )}
                        </div>
                    </div>
                </div>
                <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-1 text-[9px] text-slate-500">
                        <MapPin className="w-2.5 h-2.5" />
                        <span>{meter.latitude?.toFixed(4)}, {meter.longitude?.toFixed(4)}</span>
                    </div>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold border ${badgeClass}`}>
                        {roleLabel}
                    </span>
                </div>
            </div>

            <div className="mx-3 border-t border-white/5" />

            {/* Stats Grid */}
            <div className="px-3 py-2">
                <div className="grid grid-cols-2 gap-1.5">
                    <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/10 px-2 py-1.5">
                        <div className="flex items-center gap-1 mb-0.5">
                            <Sun className="w-2.5 h-2.5 text-emerald-500/60" />
                            <span className="text-[8px] text-slate-500 font-bold uppercase">Gen</span>
                        </div>
                        <p className="text-xs font-bold text-emerald-400">{(meter.generation || 0).toFixed(2)} <span className="text-[8px] text-slate-600">kWh</span></p>
                    </div>
                    <div className="rounded-lg bg-amber-500/5 border border-amber-500/10 px-2 py-1.5">
                        <div className="flex items-center gap-1 mb-0.5">
                            <Zap className="w-2.5 h-2.5 text-amber-500/60" />
                            <span className="text-[8px] text-slate-500 font-bold uppercase">Use</span>
                        </div>
                        <p className="text-xs font-bold text-amber-400">{(meter.consumption || 0).toFixed(2)} <span className="text-[8px] text-slate-600">kWh</span></p>
                    </div>
                </div>

                {/* Net Energy */}
                <div className="mt-1.5 rounded-lg bg-slate-800/50 border border-white/5 px-2 py-1.5 flex items-center justify-between">
                    <span className="text-[8px] text-slate-500 font-bold uppercase">Net Energy</span>
                    <span className={`text-xs font-bold ${netEnergy > 0 ? 'text-emerald-400' : netEnergy < 0 ? 'text-amber-400' : 'text-slate-400'}`}>
                        {netEnergy > 0 ? '+' : ''}{netEnergy.toFixed(2)} kWh
                    </span>
                </div>

                {/* Voltage bar */}
                <div className="mt-1.5 rounded-lg bg-slate-800/50 border border-white/5 px-2 py-1.5">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-[8px] text-slate-500 font-bold uppercase">Voltage</span>
                        <span className="text-[8px] text-slate-500">{meter.voltage}V ({voltagePercent}%)</span>
                    </div>
                    <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full bg-blue-500/60"
                            style={{ width: `${Math.min(100, Number(voltagePercent))}%` }}
                        />
                    </div>
                </div>

                {/* Nodal price */}
                {meter.nodal_price && (
                    <div className="mt-1.5 rounded-lg bg-slate-800/50 border border-white/5 px-2 py-1.5 flex items-center justify-between">
                        <span className="text-[8px] text-slate-500 font-bold uppercase">Nodal Price</span>
                        <span className="text-xs font-bold text-white">{meter.nodal_price.toFixed(2)} ฿/kWh</span>
                    </div>
                )}
            </div>

            <div className="mx-3 border-t border-white/5" />

            {/* Footer */}
            <div className="px-3 py-2">
                <Link
                    href={`/meter/${meter.meter_id}`}
                    className="flex items-center justify-center gap-1.5 w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-[9px] font-bold rounded-lg transition-all active:scale-[0.98] group"
                >
                    <span>View Details</span>
                    <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </Link>
            </div>
        </div>
    );
}
