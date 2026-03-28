import { Zap, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { MeterData } from './types';

interface MapLegendProps {
    meters: MeterData[];
}

export const MapLegend = ({ meters }: MapLegendProps) => {
    const stats = {
        totalHouses: meters.length,
        producers: meters.filter(m => m.generation > m.consumption).length,
        prosumers: meters.filter(m => m.generation > 0 && m.generation < m.consumption).length,
        consumers: meters.filter(m => m.generation === 0).length,
        netEnergy: meters.reduce((sum, m) => sum + m.generation - m.consumption, 0),
        totalGeneration: meters.reduce((sum, m) => sum + m.generation, 0),
        totalConsumption: meters.reduce((sum, m) => sum + m.consumption, 0)
    };

    const selfSufficiency = stats.totalGeneration > 0 
        ? ((stats.totalGeneration / stats.totalConsumption) * 100).toFixed(1)
        : '0';

    return (
        <div className="absolute bottom-6 right-6 z-[1000] glass p-5 rounded-2xl space-y-4 w-72 backdrop-blur-xl border border-white/10 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-black text-white flex items-center gap-2">
                    <div className="p-1.5 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-lg">
                        <Zap className="w-4 h-4 text-amber-400" />
                    </div>
                    Energy Status
                </h3>
                <div className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
                    stats.netEnergy > 0 
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                        : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                }`}>
                    {stats.netEnergy > 0 ? '+' : ''}{stats.netEnergy.toFixed(1)} kWh
                </div>
            </div>

            {/* Legend Items */}
            <div className="space-y-2.5">
                {/* Producer */}
                <div className="group flex items-center gap-3 p-2 rounded-xl bg-emerald-500/5 hover:bg-emerald-500/10 border border-transparent hover:border-emerald-500/20 transition-all duration-300">
                    <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)] border-2 border-white/30 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-emerald-300">Producer</span>
                            <span className="text-xs font-black text-emerald-400">{stats.producers}</span>
                        </div>
                        <span className="text-[10px] text-slate-500">Export to grid</span>
                    </div>
                </div>

                {/* Prosumer */}
                <div className="group flex items-center gap-3 p-2 rounded-xl bg-amber-500/5 hover:bg-amber-500/10 border border-transparent hover:border-amber-500/20 transition-all duration-300">
                    <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.6)] border-2 border-white/30 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-amber-300">Prosumer</span>
                            <span className="text-xs font-black text-amber-400">{stats.prosumers}</span>
                        </div>
                        <span className="text-[10px] text-slate-500">Solar + Grid</span>
                    </div>
                </div>

                {/* Consumer */}
                <div className="group flex items-center gap-3 p-2 rounded-xl bg-blue-500/5 hover:bg-blue-500/10 border border-transparent hover:border-blue-500/20 transition-all duration-300">
                    <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.6)] border-2 border-white/30 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-blue-300">Consumer</span>
                            <span className="text-xs font-black text-blue-400">{stats.consumers}</span>
                        </div>
                        <span className="text-[10px] text-slate-500">Grid only</span>
                    </div>
                </div>
            </div>

            {/* Divider */}
            <div className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

            {/* Statistics */}
            <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-1.5 mb-1">
                        <TrendingUp className="w-3 h-3 text-emerald-400" />
                        <span className="text-[10px] font-bold text-slate-400">Generation</span>
                    </div>
                    <div className="text-sm font-black text-emerald-400">
                        {stats.totalGeneration.toFixed(1)} <span className="text-xs">kWh</span>
                    </div>
                </div>
                
                <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-1.5 mb-1">
                        <TrendingDown className="w-3 h-3 text-rose-400" />
                        <span className="text-[10px] font-bold text-slate-400">Consumption</span>
                    </div>
                    <div className="text-sm font-black text-rose-400">
                        {stats.totalConsumption.toFixed(1)} <span className="text-xs">kWh</span>
                    </div>
                </div>
                
                <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-1.5 mb-1">
                        <Minus className="w-3 h-3 text-indigo-400" />
                        <span className="text-[10px] font-bold text-slate-400">Self-Sufficiency</span>
                    </div>
                    <div className="text-sm font-black text-indigo-400">
                        {selfSufficiency}<span className="text-xs">%</span>
                    </div>
                </div>
                
                <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-1.5 mb-1">
                        <Zap className="w-3 h-3 text-amber-400" />
                        <span className="text-[10px] font-bold text-slate-400">Total Houses</span>
                    </div>
                    <div className="text-sm font-black text-amber-400">
                        {stats.totalHouses}
                    </div>
                </div>
            </div>
        </div>
    );
};
