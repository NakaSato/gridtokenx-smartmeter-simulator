import { Link } from 'react-router-dom';
import { ArrowLeft, Zap } from 'lucide-react';
import type { MapStats } from './types';

interface MapHeaderProps {
    housesCount: number;
    stats: MapStats;
}

export const MapHeader = ({ housesCount, stats }: MapHeaderProps) => {
    return (
        <div className="z-20 flex justify-between items-center px-8 py-4 bg-[#0f172ab0] backdrop-blur-md border-b border-white/10 shrink-0">
            <div className="flex items-center gap-6">
                <Link to="/dashboard" className="p-2.5 rounded-2xl bg-white/5 hover:bg-white/10 transition-all text-slate-400 hover:text-white group">
                    <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                </Link>
                <div>
                    <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-3">
                        <Zap className="w-6 h-6 text-amber-400 fill-amber-400/20" />
                        Village Microgrid Map
                    </h1>
                    <p className="text-[10px] uppercase tracking-widest font-black text-slate-500 mt-0.5">
                        {housesCount} Houses • Real-Time P2P Energy Trading
                    </p>
                </div>
            </div>

            <div className="glass px-5 py-3 rounded-2xl border-white/10 bg-slate-900/40 flex items-center gap-6">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-black text-slate-400 uppercase">Generation</span>
                    <span className="text-sm font-black text-emerald-400">{stats.totalGeneration.toFixed(1)} kWh</span>
                </div>
                <div className="h-6 w-px bg-white/10" />
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-rose-500" />
                    <span className="text-[10px] font-black text-slate-400 uppercase">Consumption</span>
                    <span className="text-sm font-black text-rose-400">{stats.totalConsumption.toFixed(1)} kWh</span>
                </div>
                <div className="h-6 w-px bg-white/10" />
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    <span className="text-[10px] font-black text-slate-400 uppercase">Voltage</span>
                    <span className="text-sm font-black text-blue-400">{((stats.avgVoltage / 230) * 100).toFixed(1)}%</span>
                </div>
                <div className="h-6 w-px bg-white/10" />
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-orange-500" />
                        <span className="text-[10px] font-bold text-slate-300">A:{stats.phaseBalance.A}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                        <span className="text-[10px] font-bold text-slate-300">B:{stats.phaseBalance.B}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        <span className="text-[10px] font-bold text-slate-300">C:{stats.phaseBalance.C}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
