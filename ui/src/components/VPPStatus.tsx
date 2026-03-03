import { Zap, Activity } from 'lucide-react';
import { cn } from '../utils';
import type { GridHealth } from '../types';

interface VPPStatusProps {
    vppData?: GridHealth['vpp'];
}

export function VPPStatus({ vppData }: VPPStatusProps) {
    if (!vppData) return null;

    const {
        total_capacity_kwh,
        current_stored_kwh,
        soc_percentage,
        status,
        flex_up_kw,
        flex_down_kw
    } = vppData;

    // Determine status color
    let statusColor = 'text-slate-400';
    let statusBg = 'bg-slate-800';

    if (status === 'Discharging') {
        statusColor = 'text-amber-400';
        statusBg = 'bg-amber-500/20';
    } else if (status === 'Charging') {
        statusColor = 'text-blue-400';
        statusBg = 'bg-blue-500/20';
    } else if (status === 'Congested') {
        statusColor = 'text-rose-400';
        statusBg = 'bg-rose-500/20';
    } else {
        statusColor = 'text-emerald-400';
        statusBg = 'bg-emerald-500/20';
    }

    return (
        <div className="glass rounded-3xl p-6 bg-gradient-to-br from-slate-900/50 to-transparent border-white/5 space-y-4 hover:border-white/10 transition-all">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-indigo-400" />
                    <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">VPP Operations</h3>
                </div>
                <div className={cn(
                    "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest transition-colors",
                    statusBg, statusColor
                )}>
                    {status}
                </div>
            </div>

            <div className="flex items-center gap-4 py-2">
                <div className="flex-1 space-y-1">
                    <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase">
                        <span>Storage</span>
                        <span>{(soc_percentage * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-indigo-500 transition-all duration-1000 ease-out"
                            style={{ width: `${Math.min(soc_percentage * 100, 100)}%` }}
                        />
                    </div>
                    <div className="text-xs text-slate-400 font-mono text-right">
                        {current_stored_kwh.toFixed(1)} <span className="text-slate-600">/</span> {total_capacity_kwh.toFixed(1)} kWh
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-900/40 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-3 h-3 text-emerald-400" />
                        <span className="text-[9px] font-black text-slate-500 uppercase">Flex Up</span>
                    </div>
                    <div className="text-lg font-black text-emerald-400">{flex_up_kw.toFixed(1)} <span className="textxs text-slate-600">kW</span></div>
                </div>
                <div className="bg-slate-900/40 p-3 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-3 h-3 text-amber-400" />
                        <span className="text-[9px] font-black text-slate-500 uppercase">Flex Down</span>
                    </div>
                    <div className="text-lg font-black text-amber-400">{flex_down_kw.toFixed(1)} <span className="textxs text-slate-600">kW</span></div>
                </div>
            </div>
        </div>
    );
}
