"use client";

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
    MapPin,
    Sun,
    Zap,
    Battery,
    Thermometer,
    Gauge,
    Cpu,
    Copy,
    Check,
    TrendingUp,
    TrendingDown,
    Shield,
    ShieldAlert,
    Leaf,
    ArrowUpRight,
    Settings,
    Info,
    Activity,
    CreditCard
} from 'lucide-react';

import type { Reading } from '@/lib/types';
import { cn } from '@/lib/common';
import { calculateUtilityPrice } from '@/lib/pricing';
import { getMeterTheme } from './MeterTheme';
import { StatBox } from '@/components/ui/StatBox';
import { MetricItem } from '@/components/ui/MetricItem';

interface MeterCardProps {
    reading: Reading;
    onClick?: () => void;
    onEdit?: (reading: Reading) => void;
    onMeta?: (reading: Reading) => void;
    onDelete?: (meter_id: string) => void;
    compact?: boolean;
}

export const MeterCard = ({ reading, onClick, onEdit, onMeta, onDelete, compact = false }: MeterCardProps) => {
    const [copied, setCopied] = useState(false);
    const [isHovered, setIsHovered] = useState(false);

    // Calculate utility price for consumption
    const utilityPrice = useMemo(() => {
        return calculateUtilityPrice(reading.energy_consumed || 0);
    }, [reading.energy_consumed]);

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

    const theme = getMeterTheme(reading.meter_type);

    // Security status
    const isCompromised = reading.is_compromised || (reading.norm_residual && reading.norm_residual > 4.0);
    const securityStatus = isCompromised ? 'critical' : (reading.norm_residual && reading.norm_residual > 2.0) ? 'warning' : 'secure';

    // Energy balance
    const energyGen = reading.energy_generated || 0;
    const energyCons = reading.energy_consumed || 0;
    const total = energyGen + energyCons;
    const genPercent = total > 0 ? (energyGen / total) * 100 : 0;
    const isNetProducer = energyGen > energyCons;
    const balance = energyGen - energyCons;

    // Carbon offset
    const carbonOffset = reading.carbon_offset || ((reading.energy_generated || 0) * 0.431);

    if (compact) {
        return (
            <div
                onClick={onClick}
                className={cn(
                    'group relative overflow-hidden rounded-2xl p-4 border transition-all duration-300',
                    'active:scale-[0.98] cursor-pointer',
                    'bg-slate-900/40 backdrop-blur-xl',
                    theme.border,
                    isCompromised ? 'ring-1 ring-rose-500/50' : ''
                )}
            >
                {/* Background Glow */}
                <div className={cn(
                    'absolute -right-4 -top-4 w-24 h-24 blur-3xl rounded-full opacity-10',
                    theme.accent
                )} />

                <div className="flex items-center justify-between relative z-10">
                    <div className="flex items-center gap-3">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <div 
                                    onClick={(e) => { e.stopPropagation(); handleCopySerial(e); }}
                                    className={cn(
                                        "font-black text-sm tracking-tight leading-none transition-colors",
                                        copied ? "text-emerald-400" : "text-white hover:text-indigo-400"
                                    )}
                                    title="Click to copy ID"
                                >
                                    {reading.location_name || 'Smart Meter'}
                                </div>
                                {reading.is_shed && (
                                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" title="Shedded" />
                                )}
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleCopySerial(e); }}
                                        className={cn(
                                            'px-1.5 py-0.5 rounded-md border border-white/5 text-[8px] font-black uppercase tracking-widest transition-all duration-200',
                                            'hover:bg-white/10 active:scale-95',
                                            copied ? 'text-emerald-400 border-emerald-400/20' : 'text-slate-500'
                                        )}
                                    >
                                        {copied ? 'Copied' : 'Copy'}
                                    </button>
                                    {onEdit && (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onEdit(reading); }}
                                            className="px-1.5 py-0.5 rounded-md border border-white/5 text-[8px] font-black uppercase tracking-widest transition-all duration-200 hover:bg-white/10 text-slate-500 hover:text-indigo-400 active:scale-95"
                                        >
                                            Config
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center gap-1">
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{reading.location}</span>
                            </div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={cn('font-black text-lg tracking-tighter', isNetProducer ? 'text-emerald-400' : 'text-rose-400')}>
                            {isNetProducer ? '+' : ''}{balance.toFixed(2)} <span className="text-[10px] opacity-60">kWh</span>
                        </div>
                        <div className="flex items-center justify-end gap-1 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                            Net Balance
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onClick={onClick}
            className={cn(
                'group relative overflow-hidden rounded-[2rem] border transition-all duration-500',
                'active:scale-[0.99] cursor-pointer',
                'bg-slate-950/40 backdrop-blur-3xl',
                theme.border,
                isCompromised ? 'ring-2 ring-rose-500/50' : '',
                reading.is_shed ? 'border-rose-500/30 bg-rose-950/10' : ''
            )}
        >
            {/* Animated Glow effect */}
            <div className={cn(
                'absolute -inset-1 opacity-0 blur-2xl pointer-events-none',
                'bg-gradient-to-br from-white/5 via-transparent to-transparent'
            )} />

            {/* Corner Accent */}
            <div className={cn(
                'absolute -bottom-10 -right-10 w-40 h-40 rounded-full blur-[60px] opacity-20 transition-all duration-700',
                theme.accent
            )} />

            {/* Status indicators */}
            {(isCompromised || reading.is_shed) && (
                <div className="absolute top-5 right-5 z-20 flex flex-col gap-1.5 items-end">
                    {isCompromised && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-500/20 border border-rose-500/30 backdrop-blur-md shadow-lg shadow-rose-500/20">
                            <span className="text-[9px] font-black uppercase tracking-widest text-rose-400">System Compromised</span>
                        </div>
                    )}
                    {reading.is_shed && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-500/20 border border-rose-500/40 backdrop-blur-md shadow-lg shadow-rose-500/20 animate-pulse">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                            <span className="text-[9px] font-black uppercase tracking-widest text-rose-400">Shedded</span>
                        </div>
                    )}
                </div>
            )}


            <div className="p-7 space-y-6 relative z-10">
                {/* Header */}
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h3 
                                    onClick={(e) => { e.stopPropagation(); handleCopySerial(e); }}
                                    className={cn(
                                        "font-black text-xl tracking-tight uppercase transition-all duration-300",
                                        copied ? "text-emerald-400" : "text-white hover:text-indigo-400"
                                    )}
                                    title="Click to copy Meter ID"
                                >
                                    {reading.location_name || 'Smart Meter'}
                                </h3>
                                <div className="flex items-center gap-1 ml-2">
                                    {onEdit && (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onEdit(reading); }}
                                            className="px-2 py-1 rounded-lg border border-white/5 text-[9px] font-black uppercase tracking-widest transition-all duration-200 hover:bg-white/10 text-slate-500 hover:text-indigo-400 active:scale-95"
                                        >
                                            Config
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-1.5">
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none">{reading.location}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {reading.meter_type !== 'Solar_Prosumer' && (
                        <div className={cn(
                            'px-3 py-1 rounded-xl border backdrop-blur-xl shadow-lg transition-all duration-500',
                            theme.border,
                            theme.icon.replace('text-', 'bg-').replace('400', '500/10'),
                            theme.icon
                        )}>
                            <span className="text-[9px] font-black uppercase tracking-[0.2em]">
                                {(reading.meter_type || 'Unknown').replace(/_/g, ' ')}
                            </span>
                        </div>
                    )}
                </div>

                {/* Energy Dynamics */}
                <div className="space-y-4">
                    <div className="flex items-end justify-between px-1">
                        <div className="space-y-1">
                            <div className="flex items-center gap-2">
                                <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Generation</span>
                            </div>
                            <div className="text-2xl font-black text-white leading-none tracking-tighter">
                                {energyGen.toFixed(2)} <span className="text-xs opacity-40 font-bold uppercase">kWh</span>
                            </div>
                        </div>
                        
                        <div className="flex flex-col items-center gap-2">
                             <div className={cn(
                                'px-3 py-1 rounded-full text-[10px] font-black border backdrop-blur-md transition-all duration-500 tracking-widest',
                                isNetProducer ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                            )}>
                                {isNetProducer ? 'PROSUMER' : 'CONSUMER'}
                            </div>
                            {isNetProducer && (
                                <div className="flex items-center gap-1">
                                    <span className="text-[8px] font-black text-emerald-500/60 uppercase tracking-widest">Trading Active</span>
                                </div>
                            )}
                        </div>

                        <div className="space-y-1 text-right">
                            <div className="flex items-center justify-end gap-2">
                                <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Consumption</span>
                            </div>
                            <div className="text-2xl font-black text-white leading-none tracking-tighter">
                                {energyCons.toFixed(2)} <span className="text-xs opacity-40 font-bold uppercase">kWh</span>
                            </div>
                        </div>
                    </div>

                    {/* Industrial Progress Bar */}
                    <div className="h-5 w-full bg-slate-900 rounded-2xl overflow-hidden border border-white/5 relative p-1 group/bar">
                        <div className="absolute inset-1 flex gap-1.5">
                            <div
                                className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-l-xl transition-all duration-1000 ease-in-out relative"
                                style={{ width: `${genPercent}%` }}
                            >
                                <div className="absolute inset-0 bg-[url('/grid-pattern.png')] opacity-10" />
                            </div>
                            <div
                                className="h-full bg-gradient-to-l from-rose-600 to-rose-400 rounded-r-xl transition-all duration-1000 ease-in-out relative"
                                style={{ width: `${100 - genPercent}%` }}
                            >
                                <div className="absolute inset-0 bg-[url('/grid-pattern.png')] opacity-10" />
                            </div>
                        </div>
                        {/* Center Marker */}
                        <div className="absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-0.5 bg-white/10 z-10" />
                    </div>

                    {/* Operational Constraints */}
                    <div className="grid grid-cols-2 gap-px bg-white/5 rounded-xl overflow-hidden border border-white/5">
                        <div className="bg-slate-950/40 p-2 flex flex-col items-center">
                            <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-0.5">Min Load</span>
                            <span className="text-[10px] font-bold text-slate-400 font-mono">{(reading.min_load_kw ?? 0.1).toFixed(2)} kW</span>
                        </div>
                        <div className="bg-slate-950/40 p-2 flex flex-col items-center border-l border-white/5">
                            <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-0.5">Max Load</span>
                            <span className="text-[10px] font-bold text-slate-400 font-mono">{(reading.max_load_kw ?? 500).toFixed(1)} kW</span>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-4">
                    <StatBox
                        label="Energy Storage"
                        value={(reading.battery_level || 0).toFixed(0)}
                        unit="%"
                        theme={theme}
                    />

                    <StatBox
                        label="Carbon Offset"
                        value={carbonOffset.toFixed(1)}
                        unit="kg"
                        theme={theme}
                    />

                    {/* Solana / Economic Layer */}
                    {reading.is_synced_with_solana && (
                        <div className="col-span-2 group/solana bg-indigo-500/10 p-4 rounded-[1.5rem] border border-indigo-500/20 overflow-hidden transition-all duration-300 relative">
                            <div className="flex items-center gap-2 mb-3">
                                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400">Solana Sync Protocol</span>
                            </div>

                            <div className="grid grid-cols-2 gap-6 relative z-10">
                                <div className="space-y-1">
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Available Balance</div>
                                    <div className="font-black text-xl text-white tracking-tighter">
                                        {(reading.solana_sol_balance ?? 0).toFixed(4)} <span className="text-[10px] opacity-40 uppercase">SOL</span>
                                    </div>
                                </div>
                                <div className="space-y-1 text-right">
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">GTNX Assets</div>
                                    <div className="font-black text-xl text-emerald-400 tracking-tighter">
                                        {(reading.solana_gtnx_balance ?? 0).toFixed(2)} <span className="text-[10px] opacity-40 uppercase text-slate-400">GTX</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
 
                {/* Electrical Telemetry Panel */}
                <div className="rounded-2xl bg-white/[0.03] border border-white/5 p-5 backdrop-blur-xl">
                    <div className="grid grid-cols-3 gap-6">
                        <MetricItem
                            label="Voltage"
                            value={(reading.voltage_pu || 1.0).toFixed(3)}
                            unit="pu"
                            color="text-blue-400"
                            status={(reading.voltage_pu || 1.0) >= 0.95 && (reading.voltage_pu || 1.0) <= 1.05 ? 'good' : 'warning'}
                        />
 
                        <MetricItem
                            label="Frequency"
                            value={(reading.freq_hz || 50.0).toFixed(2)}
                            unit="Hz"
                            color="text-amber-400"
                            status={(reading.freq_hz || 50.0) >= 49.8 && (reading.freq_hz || 50.0) <= 50.2 ? 'good' : 'warning'}
                        />
 
                        <MetricItem
                            label="Power Factor"
                            value={(reading.power_factor || 0.98).toFixed(2)}
                            unit="cosφ"
                            color="text-violet-400"
                            status={(reading.power_factor || 0.98) >= 0.95 ? 'good' : 'warning'}
                        />
                    </div>
                </div>
 
                {/* Footer Section */}
                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <div className="flex items-center gap-8">
                        <div className="flex flex-col">
                            <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Ambient</span>
                            <span className="text-xs font-black text-slate-400 tracking-tight">{(reading.temperature || 20.0).toFixed(1)}°C</span>
                        </div>

                        <div className="flex flex-col">
                            <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Network</span>
                            <div className="flex items-center gap-1.5">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[9px] font-black text-emerald-500/80 uppercase">Live</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
