import { MapPin, Sun, Zap, Battery, Thermometer, Activity, Gauge, Cpu, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/common';
import { useState } from 'react';

import type { Reading } from '@/lib/types';

export const MeterListItem = ({ reading }: { reading: Reading }) => {
    const [copied, setCopied] = useState(false);

    const handleCopySerial = async (e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await navigator.clipboard.writeText(reading.meter_id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };
    const themeColors: Record<string, { base: string, text: string, bg: string, border: string }> = {
        Solar_Prosumer: {
            base: "from-emerald-500/10 to-transparent",
            text: "text-emerald-400",
            bg: "bg-emerald-500/5",
            border: "border-emerald-500/20"
        },
        Grid_Consumer: {
            base: "from-blue-500/10 to-transparent",
            text: "text-blue-400",
            bg: "bg-blue-500/5",
            border: "border-blue-500/20"
        },
        Hybrid_Prosumer: {
            base: "from-purple-500/10 to-transparent",
            text: "text-purple-400",
            bg: "bg-purple-500/5",
            border: "border-purple-500/20"
        },
        Battery_Storage: {
            base: "from-rose-500/10 to-transparent",
            text: "text-rose-400",
            bg: "bg-rose-500/5",
            border: "border-rose-500/20"
        },
    };

    const theme = themeColors[reading.meter_type as keyof typeof themeColors] || {
        base: "from-slate-500/10 to-transparent",
        text: "text-slate-400",
        bg: "bg-slate-500/5",
        border: "border-slate-500/20"
    };

    const isCompromised = reading.is_compromised || (reading.norm_residual && reading.norm_residual > 4.0);

    return (
        <div className={cn(
            "group relative overflow-hidden rounded-2xl p-4 border transition-all duration-300",
            "hover:bg-white/5 active:scale-[0.99] cursor-pointer",
            "bg-gradient-to-r backdrop-blur-xl flex items-center gap-6",
            theme.base, theme.border
        )}>
            {/* Type Indicator Bar */}
            <div className={cn("absolute left-0 top-0 bottom-0 w-1",
                reading.meter_type === 'Solar_Prosumer' ? "bg-emerald-500" :
                    reading.meter_type === 'Grid_Consumer' ? "bg-blue-500" :
                        reading.meter_type === 'Battery_Storage' ? "bg-rose-500" : "bg-purple-500"
            )} />

            {/* ID & Location */}
            <div className="flex items-center gap-4 min-w-[200px]">
                <button
                    onClick={handleCopySerial}
                    className={cn(
                        "p-2 rounded-xl bg-slate-900/50 border border-white/5",
                        "hover:bg-slate-800/70 hover:border-white/20 hover:scale-110",
                        "active:scale-95 transition-all duration-200 cursor-pointer",
                        "group/clipboard relative"
                    )}
                    title="Click to copy serial number"
                >
                    {copied ? (
                        <Check className={cn("w-4 h-4 text-emerald-400 animate-in zoom-in duration-200")} />
                    ) : (
                        <Cpu className={cn("w-4 h-4", theme.text, "group-hover/clipboard:hidden")} />
                    )}
                    <Copy className={cn(
                        "w-4 h-4", theme.text,
                        "hidden group-hover/clipboard:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
                    )} />
                    <span className={cn(
                        "absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 rounded text-[10px] font-bold",
                        "bg-slate-800 border border-white/10 text-white/80 whitespace-nowrap",
                        "opacity-0 group-hover/clipboard:opacity-100 transition-opacity duration-200",
                        "pointer-events-none"
                    )}>
                        {copied ? 'Copied!' : 'Copy serial'}
                    </span>
                </button>
                <div className="space-y-0.5">
                    <h3 className="font-black text-sm tracking-tight text-white/90">
                        {reading.meter_id.split('-')[0]}<span className="opacity-30 text-[10px]">{reading.meter_id.split('-')[1] ? `-${reading.meter_id.split('-')[1]}` : ''}</span>
                    </h3>
                    <div className="flex items-center gap-1.5 opacity-60">
                        <MapPin className="w-2.5 h-2.5" />
                        <span className="text-[9px] font-bold uppercase tracking-widest">{reading.location}</span>
                    </div>
                </div>
            </div>

            {/* Type Badge */}
            <div className="hidden lg:block min-w-[120px]">
                <div className={cn("px-3 py-1 rounded-lg border text-[8px] font-black uppercase tracking-wider text-center", theme.bg, theme.text, theme.border)}>
                    {reading.meter_type.replace('_', ' ')}
                </div>
            </div>

            {/* Power Metrics */}
            <div className="flex items-center gap-8 flex-1">
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 opacity-40">
                        <Sun className="w-3 h-3 text-emerald-400" />
                        <span className="text-[7px] font-black uppercase tracking-widest">Gen</span>
                    </div>
                    <span className="text-xs font-black text-emerald-400">
                        {reading.energy_generated.toFixed(2)} <span className="text-[8px] opacity-40">kWh</span>
                    </span>
                </div>
                <div className="flex flex-col gap-1 text-rose-400">
                    <div className="flex items-center gap-1.5 opacity-40">
                        <Zap className="w-3 h-3" />
                        <span className="text-[7px] font-black uppercase tracking-widest">Cons</span>
                    </div>
                    <span className="text-xs font-black">
                        {reading.energy_consumed.toFixed(2)} <span className="text-[8px] opacity-40">kWh</span>
                    </span>
                </div>
            </div>

            {/* Electrical Stats */}
            <div className="hidden md:flex items-center gap-8 border-x border-white/5 px-8">
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 opacity-40">
                        <Gauge className="w-3 h-3 text-blue-400" />
                        <span className="text-[7px] font-black uppercase tracking-widest">Voltage</span>
                    </div>
                    <span className="text-xs font-black text-blue-300">
                        {reading.voltage_pu?.toFixed(3) || '1.000'} <span className="text-[8px] opacity-40">pu</span>
                    </span>
                </div>
                <div className="flex flex-col gap-1">
                    <span className="text-[7px] font-black uppercase tracking-widest opacity-40">Cyber Res</span>
                    <span className={cn(
                        "text-xs font-black",
                        (reading.norm_residual || 0) > 3.0 ? "text-rose-400" : "text-emerald-400"
                    )}>
                        {reading.norm_residual?.toFixed(3) || '0.012'}
                    </span>
                </div>
            </div>

            {/* Battery & Environmental */}
            <div className="flex items-center gap-6 min-w-[150px] justify-end">
                <div className="flex items-center gap-2">
                    <Battery className={cn("w-3.5 h-3.5", reading.battery_level > 20 ? "text-emerald-400" : "text-rose-400")} />
                    <span className="text-xs font-black">{reading.battery_level.toFixed(0)}%</span>
                </div>
                <div className="flex items-center gap-2">
                    <Thermometer className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-xs font-black text-slate-400">{reading.temperature.toFixed(1)}°</span>
                </div>
            </div>

            {/* Status Indicators */}
            <div className="min-w-[40px] flex justify-end">
                {isCompromised ? (
                    <div className="p-2 rounded-lg bg-rose-500/20 border border-rose-500/30" title="Anomaly Detected">
                        <Zap className="w-3 h-3 text-rose-400 animate-pulse" />
                    </div>
                ) : reading.surplus_energy > 0 ? (
                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20" title="Trading Active">
                        <Activity className="w-3 h-3 text-emerald-400 animate-pulse" />
                    </div>
                ) : (
                    <div className="w-3 h-3 rounded-full bg-slate-800 border border-white/5 opacity-20" />
                )}
            </div>
        </div>
    );
};
