"use client";

import { MapPin, Sun, Zap, Battery, Thermometer, Activity, Gauge, Cpu, Copy, Check, Settings, Info, TrendingUp, TrendingDown, Shield, ShieldAlert, CreditCard, Trash2 } from 'lucide-react';
import { cn } from '@/lib/common';
import { useState } from 'react';
import { useNetwork } from '@/components/providers/NetworkProvider';

import type { Reading } from '@/lib/types';

export const MeterListItem = ({ reading, onEdit, onMeta, onDelete }: { reading: Reading, onEdit?: (reading: Reading) => void, onMeta?: (reading: Reading) => void, onDelete?: (meter_id: string) => void }) => {
    const { getApiUrl } = useNetwork();
    const [copied, setCopied] = useState(false);

    const handleDelete = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (confirm(`Are you sure you want to delete meter ${reading.meter_id}?`)) {
            try {
                const res = await fetch(getApiUrl(`/api/v1/meters/${reading.meter_id}`), {
                    method: 'DELETE',
                });
                if (res.ok && onDelete) {
                    onDelete(reading.meter_id);
                }
            } catch (err) {
                console.error('Failed to delete meter:', err);
            }
        }
    };

    const handleCopySerial = async (e: React.MouseEvent) => {
        e.stopPropagation();
        const copyText = reading.serial_number || reading.meter_id;
        try {
            await navigator.clipboard.writeText(copyText);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };
    
    const themeColors: Record<string, { base: string, text: string, bg: string, border: string, accent: string }> = {
        Solar_Prosumer: {
            base: "from-emerald-500/10 to-transparent",
            text: "text-emerald-400",
            bg: "bg-emerald-500/5",
            border: "border-emerald-500/20",
            accent: "bg-emerald-500"
        },
        Grid_Consumer: {
            base: "from-blue-500/10 to-transparent",
            text: "text-blue-400",
            bg: "bg-blue-500/5",
            border: "border-blue-500/20",
            accent: "bg-blue-500"
        },
        Hybrid_Prosumer: {
            base: "from-purple-500/10 to-transparent",
            text: "text-purple-400",
            bg: "bg-purple-500/5",
            border: "border-purple-500/20",
            accent: "bg-purple-500"
        },
        Battery_Storage: {
            base: "from-amber-500/10 to-transparent",
            text: "text-amber-400",
            bg: "bg-amber-500/5",
            border: "border-amber-500/20",
            accent: "bg-amber-500"
        },
        EV_Charger: {
            base: "from-cyan-500/10 to-transparent",
            text: "text-cyan-400",
            bg: "bg-cyan-500/5",
            border: "border-cyan-500/20",
            accent: "bg-cyan-500"
        },
    };

    const theme = themeColors[reading.meter_type as keyof typeof themeColors] || {
        base: "from-slate-500/10 to-transparent",
        text: "text-slate-400",
        bg: "bg-slate-500/5",
        border: "border-slate-500/20",
        accent: "bg-slate-500"
    };

    const isCompromised = reading.is_compromised || (reading.norm_residual && reading.norm_residual > 4.0);
    const energyGen = reading.energy_generated || 0;
    const energyCons = reading.energy_consumed || 0;
    const balance = energyGen - energyCons;
    const isNetProducer = energyGen > energyCons;

    return (
        <div className={cn(
            "group relative overflow-hidden rounded-2xl p-4 border transition-all duration-500",
            "hover:bg-white/[0.02] hover:border-white/20 active:scale-[0.995] cursor-pointer",
            "bg-slate-950/40 backdrop-blur-2xl flex items-center gap-6",
            theme.border,
            isCompromised ? "ring-1 ring-rose-500/30" : "",
            reading.is_shed ? "border-rose-500/30 bg-rose-950/5" : ""
        )}>
            {/* Type Indicator Bar */}
            <div className={cn("absolute left-0 top-0 bottom-0 w-1", reading.is_shed ? "bg-rose-500" : theme.accent)} />

            {/* ID & Quick Actions */}
            <div className="flex items-center gap-4 min-w-[240px]">
                <div className={cn(
                    "p-3 rounded-2xl bg-white/5 border border-white/5 transition-all duration-300 group-hover:scale-110",
                    theme.text
                )}>
                    <Cpu className="w-5 h-5" />
                </div>
                
                <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                        <h3 
                            onClick={(e) => { e.stopPropagation(); handleCopySerial(e); }}
                            className={cn(
                                "font-black text-sm tracking-tight uppercase group-hover:text-white transition-colors cursor-pointer",
                                copied ? "text-emerald-400" : "text-white hover:text-indigo-400"
                            )}
                            title="Click to copy ID"
                        >
                            {reading.location_name || 'Smart Meter'}
                        </h3>
                        <div className="flex items-center gap-1">
                            {onEdit && (
                                <button
                                    onClick={(e) => { e.stopPropagation(); onEdit(reading); }}
                                    className="px-2 py-0.5 rounded-md border border-white/5 text-[8px] font-black uppercase tracking-widest transition-all duration-200 hover:bg-white/10 text-slate-500 hover:text-indigo-400"
                                >
                                    Config
                                </button>
                            )}
                            {onDelete && (
                                <button
                                    onClick={handleDelete}
                                    className="px-2 py-0.5 rounded-md border border-white/5 text-[8px] font-black uppercase tracking-widest transition-all duration-200 hover:bg-rose-950/50 text-slate-500 hover:text-rose-400"
                                >
                                    <Trash2 className="w-3 h-3" />
                                </button>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-1.5 opacity-60">
                        <span className="text-[9px] font-black uppercase tracking-[0.15em] text-slate-500">{reading.location}</span>
                    </div>
                </div>
            </div>

            {/* Energy Mix */}
            <div className="hidden xl:flex items-center gap-8 min-w-[200px]">
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5">
                        <Activity className={cn("w-3 h-3", isNetProducer ? "text-emerald-400" : "text-rose-400")} />
                        <span className="text-[8px] font-black uppercase tracking-widest text-slate-600">Balance</span>
                    </div>
                    <div className={cn("text-base font-black tracking-tighter", isNetProducer ? "text-emerald-400" : "text-rose-400")}>
                        {isNetProducer ? '+' : ''}{balance.toFixed(1)} <span className="text-[10px] opacity-40 uppercase">kWh</span>
                    </div>
                </div>
                
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5">
                        <Thermometer className="w-3 h-3 text-slate-500" />
                        <span className="text-[8px] font-black uppercase tracking-widest text-slate-600">Temp</span>
                    </div>
                    <div className="text-base font-black text-slate-400 tracking-tighter">
                        {(reading.temperature || 20).toFixed(1)} <span className="text-[10px] opacity-40 uppercase">°C</span>
                    </div>
                </div>
            </div>

            {/* Power Metrics */}
            <div className="flex items-center gap-10 flex-1 border-x border-white/5 px-8">
                <div className="flex flex-col gap-1">
                    <span className="text-[8px] font-black uppercase tracking-widest text-slate-600">Generation</span>
                    <div className="flex items-center gap-2">
                        <Sun className="w-4 h-4 text-emerald-400/60" />
                        <span className="text-base font-black text-white tracking-tighter">
                            {energyGen.toFixed(2)} <span className="text-[10px] opacity-30 uppercase">kWh</span>
                        </span>
                    </div>
                </div>
                <div className="flex flex-col gap-1">
                    <span className="text-[8px] font-black uppercase tracking-widest text-slate-600">Consumption</span>
                    <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-rose-400/60" />
                        <span className="text-base font-black text-white tracking-tighter">
                            {energyCons.toFixed(2)} <span className="text-[10px] opacity-30 uppercase">kWh</span>
                        </span>
                    </div>
                </div>
                {/* Constraints in List */}
                <div className="hidden 2xl:flex items-center gap-6 border-l border-white/5 pl-8">
                    <div className="flex flex-col">
                        <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Min</span>
                        <span className="text-[10px] font-bold text-slate-500 font-mono">{(reading.min_load_kw ?? 0.1).toFixed(2)}</span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Max</span>
                        <span className="text-[10px] font-bold text-slate-500 font-mono">{(reading.max_load_kw ?? 500).toFixed(1)}</span>
                    </div>
                </div>
            </div>

            {/* Status Icons */}
            <div className="flex items-center gap-6 min-w-[140px] justify-end">
                <div className="flex flex-col items-end gap-1.5">
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/5 border border-white/5">
                        <Battery className={cn("w-3 h-3", (reading.battery_level || 0) > 20 ? "text-emerald-400" : "text-rose-400")} />
                        <span className="text-[10px] font-black text-slate-400">{(reading.battery_level || 0).toFixed(0)}%</span>
                    </div>
                    {reading.is_synced_with_solana && (
                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20">
                            <CreditCard className="w-3 h-3 text-indigo-400" />
                            <span className="text-[10px] font-black text-indigo-400">{(reading.solana_gtnx_balance ?? 0).toFixed(1)}</span>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    {reading.is_shed && (
                        <div className="px-2 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-[9px] font-black uppercase text-rose-400 animate-pulse" title="Load Shedding Active">
                            Shedded
                        </div>
                    )}
                    {isCompromised ? (
                        <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20" title="Anomaly Detected">
                            <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
                        </div>
                    ) : (
                        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
