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
    ArrowUpRight
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
    compact?: boolean;
}

export const MeterCard = ({ reading, onClick, compact = false }: MeterCardProps) => {
    const [copied, setCopied] = useState(false);
    const [isHovered, setIsHovered] = useState(false);

    // Calculate utility price for consumption
    const utilityPrice = useMemo(() => {
        return calculateUtilityPrice(reading.energy_consumed);
    }, [reading.energy_consumed]);

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

    const theme = getMeterTheme(reading.meter_type);

    // Security status
    const isCompromised = reading.is_compromised || (reading.norm_residual && reading.norm_residual > 4.0);
    const securityStatus = isCompromised ? 'critical' : (reading.norm_residual && reading.norm_residual > 2.0) ? 'warning' : 'secure';

    // Energy balance
    const total = reading.energy_generated + reading.energy_consumed;
    const genPercent = total > 0 ? (reading.energy_generated / total) * 100 : 0;
    const isNetProducer = reading.energy_generated > reading.energy_consumed;
    const balance = reading.energy_generated - reading.energy_consumed;

    // Carbon offset
    const carbonOffset = reading.carbon_offset || (reading.energy_generated * 0.431);

    if (compact) {
        return (
            <div
                onClick={onClick}
                className={cn(
                    'group relative overflow-hidden rounded-2xl p-4 border transition-all duration-300',
                    'hover:scale-[1.02] active:scale-[0.98] cursor-pointer',
                    'bg-gradient-to-br backdrop-blur-xl',
                    theme.gradient,
                    theme.border,
                    isCompromised ? 'ring-1 ring-rose-500/50' : ''
                )}
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={cn('p-2 rounded-xl bg-white/5', theme.icon)}>
                            <Cpu className="w-4 h-4" />
                        </div>
                        <div>
                            <div className="font-bold text-sm text-white">{reading.meter_id}</div>
                            <div className="text-xs text-slate-400">{reading.location}</div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={cn('font-black text-lg', isNetProducer ? theme.icon : 'text-rose-400')}>
                            {isNetProducer ? '+' : ''}{balance.toFixed(1)} <span className="text-xs">kWh</span>
                        </div>
                        <div className="text-xs text-slate-500">Net</div>
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
                'group relative overflow-hidden rounded-3xl border transition-all duration-500',
                'hover:shadow-2xl hover:scale-[1.01] active:scale-[0.99] cursor-pointer',
                'bg-gradient-to-br backdrop-blur-2xl',
                theme.gradient,
                theme.border,
                theme.glow,
                isCompromised ? 'ring-2 ring-rose-500/50 animate-pulse' : ''
            )}
        >
            {/* Animated background glow */}
            <div className={cn(
                'absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700',
                'bg-gradient-to-br via-white/5 pointer-events-none'
            )} />

            {/* Security status indicator */}
            {isCompromised && (
                <div className="absolute top-4 right-4 z-10">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-500/20 border border-rose-500/30 backdrop-blur-md">
                        <ShieldAlert className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
                        <span className="text-[8px] font-black uppercase tracking-wider text-rose-400">Alert</span>
                    </div>
                </div>
            )}

            <div className="p-6 space-y-5">
                {/* Header */}
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            'p-3 rounded-2xl bg-white/5 backdrop-blur-md transition-all duration-300',
                            isHovered ? 'scale-110 rotate-3' : '',
                            theme.icon
                        )}>
                            <Cpu className="w-5 h-5" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h3 className="font-black text-lg tracking-tight text-white">
                                    {reading.meter_id}
                                </h3>
                                <button
                                    onClick={handleCopySerial}
                                    className={cn(
                                        'p-1.5 rounded-lg transition-all duration-200',
                                        'hover:bg-white/10 active:scale-90',
                                        copied ? 'text-emerald-400' : 'text-slate-500 hover:text-white'
                                    )}
                                    title={copied ? 'Copied!' : 'Copy serial number'}
                                >
                                    {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                                </button>
                            </div>
                            <div className="flex items-center gap-1.5 mt-1">
                                <MapPin className="w-3 h-3 text-slate-500" />
                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{reading.location}</span>
                            </div>
                        </div>
                    </div>

                    <div className={cn(
                        'px-3 py-1.5 rounded-xl border backdrop-blur-md transition-all duration-300',
                        isHovered ? 'scale-105' : '',
                        theme.border,
                        theme.icon.replace('text-', 'bg-').replace('400', '500/10'),
                        theme.icon
                    )}>
                        <span className="text-[9px] font-black uppercase tracking-wider">
                            {reading.meter_type.replace(/_/g, ' ')}
                        </span>
                    </div>
                </div>

                {/* Energy Balance Visualization */}
                <div className="relative">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <Sun className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Generation</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Consumption</span>
                            <Zap className="w-3.5 h-3.5 text-rose-400" />
                        </div>
                    </div>

                    {/* Progress bar with dual gradient */}
                    <div className="h-3 w-full bg-slate-900/80 rounded-full overflow-hidden border border-white/5 relative">
                        <div className="absolute inset-0 flex">
                            <div
                                className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-700 ease-out relative"
                                style={{ width: `${genPercent}%` }}
                            >
                                <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent" />
                            </div>
                            <div
                                className="h-full bg-gradient-to-r from-rose-400 to-rose-500 transition-all duration-700 ease-out relative"
                                style={{ width: `${100 - genPercent}%` }}
                            >
                                <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent" />
                            </div>
                        </div>
                    </div>

                    {/* Balance indicator */}
                    <div className="flex items-center justify-center mt-2">
                        <div className={cn(
                            'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black transition-all duration-300',
                            isNetProducer ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        )}>
                            {isNetProducer ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            <span>{isNetProducer ? '+' : ''}{balance.toFixed(1)} kWh</span>
                            <span className="text-slate-500 font-bold">|</span>
                            <span className="text-slate-400">{genPercent.toFixed(0)}% solar</span>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3">
                    {/* Generation */}
                    <StatBox
                        icon={Sun}
                        iconColor="text-emerald-400"
                        label="Generation"
                        value={reading.energy_generated.toFixed(2)}
                        unit="kWh"
                        theme={theme}
                    />

                    {/* Consumption */}
                    <StatBox
                        icon={Zap}
                        iconColor="text-rose-400"
                        label="Consumption"
                        value={reading.energy_consumed.toFixed(2)}
                        unit="kWh"
                        theme={theme}
                        price={utilityPrice.totalAmount}
                    />

                    {/* Battery */}
                    <StatBox
                        icon={Battery}
                        iconColor={reading.battery_level > 50 ? 'text-emerald-400' : reading.battery_level > 20 ? 'text-amber-400' : 'text-rose-400'}
                        label="Battery"
                        value={reading.battery_level.toFixed(0)}
                        unit="%"
                        theme={theme}
                        badge={reading.battery_level > 80 ? 'Full' : undefined}
                    />

                    {/* Carbon Offset */}
                    <StatBox
                        icon={Leaf}
                        iconColor="text-green-400"
                        label="CO₂ Offset"
                        value={carbonOffset.toFixed(1)}
                        unit="kg"
                        theme={theme}
                    />

                    {/* Solana Wallet Overlay if synced */}
                    {reading.is_synced_with_solana && (
                        <div className="col-span-2 relative group/solana bg-blue-500/10 p-3.5 rounded-2xl border border-blue-500/20 overflow-hidden transition-all duration-300 hover:bg-blue-500/20">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <Shield className="w-3.5 h-3.5 text-blue-400" />
                                    <span className="text-[9px] font-black uppercase tracking-wider text-blue-400">Solana Wallet</span>
                                </div>
                                <span className="text-[7px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded-md bg-blue-500/20 text-blue-400">
                                    Live
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-0.5">
                                    <div className="text-[7px] font-bold text-slate-500 uppercase">SOL Balance</div>
                                    <div className="font-black text-sm text-white">
                                        {(reading.solana_sol_balance ?? 0).toFixed(4)} <span className="text-[8px] opacity-50">SOL</span>
                                    </div>
                                </div>
                                <div className="space-y-0.5">
                                    <div className="text-[7px] font-bold text-slate-500 uppercase">GTNX Tokens</div>
                                    <div className="font-black text-sm text-emerald-400">
                                        {(reading.solana_gtnx_balance ?? 0).toFixed(2)} <span className="text-[8px] opacity-50">GRX</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Electrical Metrics Panel */}
                <div className="rounded-2xl bg-white/5 border border-white/10 p-4 backdrop-blur-md">
                    <div className="flex items-center gap-2 mb-3">
                        <Gauge className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-xs font-black uppercase tracking-widest text-slate-500">Electrical Metrics</span>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
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
                            unit=""
                            color="text-violet-400"
                            status={(reading.power_factor || 0.98) >= 0.95 ? 'good' : 'warning'}
                        />
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-2">
                    {/* Environmental */}
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Thermometer className="w-4 h-4 text-slate-500" />
                            <span className="text-sm font-bold text-slate-400">{reading.temperature.toFixed(1)}°C</span>
                        </div>

                        {/* Security Status */}
                        <div className={cn(
                            'flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition-all',
                            securityStatus === 'secure' ? 'bg-emerald-500/10' : securityStatus === 'warning' ? 'bg-amber-500/10' : 'bg-rose-500/20'
                        )}>
                            {securityStatus === 'secure' ? (
                                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                            ) : securityStatus === 'warning' ? (
                                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                            ) : (
                                <ShieldAlert className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
                            )}
                            <span className={cn(
                                'text-[8px] font-black uppercase tracking-wider',
                                securityStatus === 'secure' ? 'text-emerald-400' : securityStatus === 'warning' ? 'text-amber-400' : 'text-rose-400'
                            )}>
                                {securityStatus}
                            </span>
                        </div>
                    </div>

                    {/* Trading Status */}
                    <div className="flex items-center gap-2">
                        <Link 
                            href={`/meter/${reading.meter_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-500/20 border border-indigo-500/30 backdrop-blur-md hover:bg-indigo-500/40 transition-colors group/btn"
                        >
                            <ArrowUpRight className="w-3.5 h-3.5 text-indigo-400 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
                            <span className="text-[8px] font-black uppercase tracking-wider text-indigo-400">Analytics</span>
                        </Link>
                        {reading.is_synced_with_solana && (
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-500/20 border border-blue-500/30 backdrop-blur-md">
                                <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                                <span className="text-[8px] font-black uppercase tracking-wider text-blue-400">Synced</span>
                            </div>
                        )}
                        {reading.surplus_energy > 0 && !isCompromised && (
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/20 border border-emerald-500/30 backdrop-blur-md">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
                                <span className="text-[8px] font-black uppercase tracking-wider text-emerald-400">P2P Active</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Corner accent */}
            <div className={cn(
                'absolute bottom-0 right-0 w-24 h-24 rounded-tl-full opacity-20 blur-2xl transition-all duration-700',
                isHovered ? 'opacity-40 scale-110' : '',
                theme.accent
            )} />
        </div>
    );
};
