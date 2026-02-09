import { MapPin, Sun, Zap, Battery, Thermometer, Activity, Gauge, Cpu } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

import type { Reading } from '../types';

export const MeterCard = ({ reading }: { reading: Reading }) => {
    const themeColors: Record<string, { base: string, glow: string, border: string, text: string, bg: string }> = {
        Solar_Prosumer: {
            base: "from-emerald-500/10 to-emerald-500/5",
            glow: "group-hover:shadow-emerald-500/20",
            border: "border-emerald-500/20",
            text: "text-emerald-400",
            bg: "bg-emerald-500/10"
        },
        Grid_Consumer: {
            base: "from-blue-500/10 to-blue-500/5",
            glow: "group-hover:shadow-blue-500/20",
            border: "border-blue-500/20",
            text: "text-blue-400",
            bg: "bg-blue-500/10"
        },
        Hybrid_Prosumer: {
            base: "from-purple-500/10 to-purple-500/5",
            glow: "group-hover:shadow-purple-500/20",
            border: "border-purple-500/20",
            text: "text-purple-400",
            bg: "bg-purple-500/10"
        },
        Battery_Storage: {
            base: "from-rose-500/10 to-rose-500/5",
            glow: "group-hover:shadow-rose-500/20",
            border: "border-rose-500/20",
            text: "text-rose-400",
            bg: "bg-rose-500/10"
        },
    };

    const theme = themeColors[reading.meter_type as keyof typeof themeColors] || {
        base: "from-slate-500/10 to-slate-500/5",
        glow: "group-hover:shadow-slate-500/20",
        border: "border-slate-500/20",
        text: "text-slate-400",
        bg: "bg-slate-500/10"
    };

    const isCompromised = reading.is_compromised || (reading.norm_residual && reading.norm_residual > 4.0);

    // Calculate power balance percentage
    const total = reading.energy_generated + reading.energy_consumed;
    const genPercent = total > 0 ? (reading.energy_generated / total) * 100 : 0;

    return (
        <div className={cn(
            "group relative overflow-hidden rounded-[2.5rem] p-0 border transition-all duration-500",
            "hover:scale-[1.02] active:scale-[0.98] cursor-pointer",
            "bg-gradient-to-br backdrop-blur-3xl shadow-xl",
            theme.base, theme.border, theme.glow
        )}>
            {/* Top Glow Accent */}
            <div className={cn("absolute top-0 left-0 right-0 h-1 bg-gradient-to-r via-transparent opacity-50",
                reading.meter_type === 'Solar_Prosumer' ? "from-emerald-500" :
                    reading.meter_type === 'Grid_Consumer' ? "from-blue-500" :
                        reading.meter_type === 'Battery_Storage' ? "from-rose-500" : "from-purple-500"
            )} />

            <div className="p-7 space-y-6">
                {/* Header */}
                <div className="flex justify-between items-start">
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <Cpu className={cn("w-4 h-4", theme.text)} />
                            <h3 className="font-black text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
                                {reading.meter_id.split('-')[0]}<span className="opacity-40">{reading.meter_id.split('-')[1] ? `-${reading.meter_id.split('-')[1]}` : ''}</span>
                            </h3>
                        </div>
                        <div className="flex items-center gap-2 px-1">
                            <MapPin className="w-3 h-3 text-slate-500" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{reading.location}</span>
                        </div>
                    </div>
                    <div className={cn("px-4 py-1.5 rounded-2xl border backdrop-blur-md transition-colors", theme.bg, theme.border)}>
                        <span className={cn("text-[8px] font-black uppercase tracking-wider", theme.text)}>
                            {reading.meter_type.replace('_', ' ')}
                        </span>
                    </div>
                </div>

                {/* Power Balance Bar */}
                <div className="space-y-2">
                    <div className="flex justify-between text-[8px] font-black uppercase tracking-widest text-slate-500 px-1">
                        <span>Solar Gen</span>
                        <span>Grid Load</span>
                    </div>
                    <div className="h-2 w-full bg-slate-900/60 rounded-full p-0.5 overflow-hidden border border-white/5">
                        <div
                            className="h-full bg-gradient-to-r from-emerald-500 to-rose-500 rounded-full transition-all duration-1000 ease-out shadow-[0_0_8px_rgba(16,185,129,0.3)]"
                            style={{ width: `${genPercent}%` }}
                        />
                    </div>
                </div>

                {/* Core Stats Grid */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="relative group/stat bg-slate-900/40 p-4 rounded-3xl border border-white/5 space-y-1 overflow-hidden hover:bg-slate-900/60 transition-colors">
                        <div className="flex items-center gap-2">
                            <Sun className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Generation</span>
                        </div>
                        <div className="font-black text-xl text-emerald-400">{reading.energy_generated.toFixed(2)}<span className="text-[10px] ml-1.5 opacity-60">kWh</span></div>
                    </div>
                    <div className="relative group/stat bg-slate-900/40 p-4 rounded-3xl border border-white/5 space-y-1 overflow-hidden hover:bg-slate-900/60 transition-colors">
                        <div className="flex items-center gap-2">
                            <Zap className="w-3.5 h-3.5 text-rose-400" />
                            <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Consumption</span>
                        </div>
                        <div className="font-black text-xl text-rose-400">{reading.energy_consumed.toFixed(2)}<span className="text-[10px] ml-1.5 opacity-60">kWh</span></div>
                    </div>
                </div>

                {/* Electrical Panel - High Density */}
                <div className="bg-white/5 rounded-3xl p-4 border border-white/10 grid grid-cols-2 gap-y-4">
                    <div className="flex flex-col gap-1 border-r border-white/5 pr-4">
                        <div className="flex items-center gap-2 opacity-50">
                            <Gauge className="w-3 h-3" />
                            <span className="text-[7px] font-black uppercase tracking-[0.2em]">Voltage</span>
                        </div>
                        <span className="text-xs font-black text-blue-300">
                            {reading.voltage_pu?.toFixed(3) || '1.000'} <span className="text-[8px] font-bold opacity-40 uppercase ml-1">pu</span>
                        </span>
                    </div>
                    <div className="flex flex-col gap-1 pl-4">
                        <div className="flex items-center gap-2 opacity-50">
                            <Activity className="w-3 h-3 text-amber-400" />
                            <span className="text-[7px] font-black uppercase tracking-[0.2em]">Frequency</span>
                        </div>
                        <span className="text-xs font-black text-amber-300">
                            {reading.freq_hz?.toFixed(2) || '50.00'} <span className="text-[8px] font-bold opacity-40 uppercase ml-1">Hz</span>
                        </span>
                    </div>
                    <div className="flex flex-col gap-1 border-r border-white/5 pr-4">
                        <div className="flex items-center gap-2 opacity-50">
                            <Gauge className="w-3 h-3 text-indigo-400" />
                            <span className="text-[7px] font-black uppercase tracking-[0.2em]">P-Factor</span>
                        </div>
                        <span className="text-xs font-black text-indigo-300">
                            {reading.power_factor?.toFixed(2) || '0.98'} <span className="text-[8px] font-bold opacity-40 uppercase ml-1">avg</span>
                        </span>
                    </div>
                    <div className="flex flex-col gap-1 pl-4">
                        <div className="flex items-center gap-2 opacity-50">
                            <Activity className="w-3 h-3 text-rose-500" />
                            <span className="text-[7px] font-black uppercase tracking-[0.2em]">Cyber Res</span>
                        </div>
                        <span className={cn(
                            "text-xs font-black transition-colors",
                            (reading.norm_residual || 0) > 3.0 ? "text-rose-400" : "text-emerald-400"
                        )}>
                            {reading.norm_residual?.toFixed(3) || '0.012'}
                        </span>
                    </div>
                </div>

                {/* Footer Environmental */}
                <div className="flex items-center justify-between pt-2 px-1">
                    <div className="flex items-center gap-5">
                        <div className="flex items-center gap-2.5">
                            <div className="relative">
                                <Battery className={cn("w-4.5 h-4.5", reading.battery_level > 20 ? "text-emerald-400" : "text-rose-400")} />
                                {reading.battery_level > 80 && (
                                    <div className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full animate-ping opacity-50" />
                                )}
                            </div>
                            <span className="text-sm font-black tracking-tight">{reading.battery_level.toFixed(0)}%</span>
                        </div>
                        <div className="flex items-center gap-2.5">
                            <Thermometer className="w-4.5 h-4.5 text-slate-500" />
                            <span className="text-sm font-black text-slate-400 tracking-tight">{reading.temperature.toFixed(1)}°</span>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        {reading.surplus_energy > 0 && !isCompromised && (
                            <div className="flex items-center gap-2 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20 group/trading hover:bg-emerald-500/20 transition-all">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
                                <span className="text-[8px] font-black uppercase tracking-widest text-emerald-400">P2P Trade</span>
                            </div>
                        )}
                        {isCompromised && (
                            <div className="flex items-center gap-2 bg-rose-500/20 px-3 py-1.5 rounded-xl border border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.15)]">
                                <div className="relative">
                                    <Zap className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
                                </div>
                                <span className="text-[8px] font-black uppercase tracking-widest text-rose-400">Anomaly</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Background Decorative Layer */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-30">
                <div className={cn("absolute -top-24 -right-24 w-48 h-48 rounded-full blur-[80px]", theme.bg)} />
                <div className={cn("absolute -bottom-24 -left-24 w-48 h-48 rounded-full blur-[80px]", theme.bg)} />
            </div>
        </div>
    );
};
