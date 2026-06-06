import { Activity, Gauge, Home, Power, SunDim, Zap } from 'lucide-react';
import { cn } from '@/lib/common';
import type { GridStats } from '@/lib/topology/types';

export function GridStatsPanel({ stats }: { stats: GridStats }) {
    return (
        <div className="absolute top-24 right-6 z-10 glass px-6 py-4 rounded-xl border-white/10 bg-slate-900/60 backdrop-blur-xl flex flex-col gap-4">
            <div className="flex items-center gap-8">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/20 rounded-xl"><Zap className="w-5 h-5 text-emerald-400" /></div>
                    <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase">Generation</div>
                        <div className="text-lg font-black text-emerald-400">{stats.totalGenerationKw.toFixed(1)} <span className="text-xs">kW</span></div>
                    </div>
                </div>
                <div className="h-10 w-px bg-white/10" />
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-rose-500/20 rounded-xl"><Activity className="w-5 h-5 text-rose-400" /></div>
                    <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase">Consumption</div>
                        <div className="text-lg font-black text-rose-400">{stats.totalConsumptionKw.toFixed(1)} <span className="text-xs">kW</span></div>
                    </div>
                </div>
            </div>
            <div className="h-px bg-white/10 w-full" />
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-xl"><Home className="w-5 h-5 text-blue-400" /></div>
                    <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase">Net Power</div>
                        <div className={cn("text-lg font-black", stats.totalGenerationKw > stats.totalConsumptionKw ? "text-emerald-400" : "text-rose-400")}>
                            {(stats.totalGenerationKw - stats.totalConsumptionKw).toFixed(1)} <span className="text-xs">kW</span>
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] font-black text-slate-400 uppercase">Avg Voltage</div>
                    <div className="text-lg font-black text-indigo-400">{stats.avgVoltage.toFixed(1)} <span className="text-xs">V</span></div>
                </div>
            </div>
            <div className="h-px bg-white/10 w-full" />
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-500/20 rounded-xl"><Gauge className="w-5 h-5 text-amber-400" /></div>
                    <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase">System Losses</div>
                        <div className="text-lg font-black text-amber-400">{stats.totalLossesKw.toFixed(1)} <span className="text-xs">kW</span></div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] font-black text-slate-400 uppercase">Congested Lines</div>
                    <div className={cn("text-lg font-black", stats.congestedLines > 0 ? "text-rose-400" : "text-emerald-400")}>{stats.congestedLines}</div>
                </div>
            </div>
            <div className="h-px bg-white/10 w-full" />
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-500/20 rounded-xl"><Power className="w-5 h-5 text-orange-400" /></div>
                    <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase">Transformer</div>
                        <div className="flex items-baseline gap-2">
                            <span className={cn("text-lg font-black", stats.transformerLoadingPct > 100 ? "text-rose-400" : stats.transformerLoadingPct > 80 ? "text-amber-400" : "text-orange-400")}>
                                {stats.transformerLoadingPct.toFixed(0)}<span className="text-xs">% load</span>
                            </span>
                            <span className="text-xs text-slate-400">{stats.transformerLossKw.toFixed(1)} kW loss</span>
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-[10px] font-black text-slate-400 uppercase flex items-center gap-1 justify-end"><SunDim className="w-3 h-3" /> PV Curtailed</div>
                    <div className={cn("text-lg font-black", stats.curtailedKw > 0.05 ? "text-amber-400" : "text-emerald-400")}>{stats.curtailedKw.toFixed(1)} <span className="text-xs">kW</span></div>
                </div>
            </div>
        </div>
    );
}
