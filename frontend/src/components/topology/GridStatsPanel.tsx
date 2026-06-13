import { Activity, AudioWaveform, Gauge, Home, Power, SunDim, Zap } from 'lucide-react';
import { cn } from '@/lib/common';
import type { GridStats } from '@/lib/topology/types';

export function GridStatsPanel({ stats }: { stats: GridStats }) {
    return (
        <div className="absolute top-24 right-6 z-10 hmi-panel px-6 py-4 flex flex-col gap-4">
            <div className="flex items-center gap-8">
                <div className="flex items-center gap-3">
                    <div className="p-2 border border-[var(--line)] bg-[var(--panel-2)]"><Zap className="w-5 h-5 text-[var(--gen)]" /></div>
                    <div>
                        <div className="hmi-lbl">Generation</div>
                        <div className="mono text-lg font-semibold text-[var(--gen)]">{stats.totalGenerationKw.toFixed(1)} <span className="text-xs text-[var(--lbl)]">kW</span></div>
                    </div>
                </div>
                <div className="h-10 w-px bg-[var(--line)]" />
                <div className="flex items-center gap-3">
                    <div className="p-2 border border-[var(--line)] bg-[var(--panel-2)]"><Activity className="w-5 h-5 text-[var(--cons)]" /></div>
                    <div>
                        <div className="hmi-lbl">Consumption</div>
                        <div className="mono text-lg font-semibold text-[var(--cons)]">{stats.totalConsumptionKw.toFixed(1)} <span className="text-xs text-[var(--lbl)]">kW</span></div>
                    </div>
                </div>
            </div>
            <div className="h-px bg-[var(--line)] w-full" />
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 border border-[var(--line)] bg-[var(--panel-2)]"><Home className="w-5 h-5 text-[var(--lbl)]" /></div>
                    <div>
                        <div className="hmi-lbl">Net Power</div>
                        <div className={cn("mono text-lg font-semibold", stats.totalGenerationKw > stats.totalConsumptionKw ? "text-[var(--gen)]" : "text-[var(--cons)]")}>
                            {(stats.totalGenerationKw - stats.totalConsumptionKw).toFixed(1)} <span className="text-xs text-[var(--lbl)]">kW</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-6">
                    <div className="text-right">
                        <div className="hmi-lbl flex items-center gap-1 justify-end"><AudioWaveform className="w-3 h-3" /> Frequency</div>
                        <div className={cn("mono text-lg font-semibold", Math.abs(stats.frequencyHz - 50) > 0.4 ? "text-[var(--alarm)]" : Math.abs(stats.frequencyHz - 50) > 0.2 ? "text-[var(--warn)]" : "text-[var(--ok)]")}>
                            {stats.frequencyHz.toFixed(3)} <span className="text-xs text-[var(--lbl)]">Hz</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="hmi-lbl">Avg Voltage</div>
                        <div className="mono text-lg font-semibold text-[var(--txt-val)]">{stats.avgVoltage.toFixed(1)} <span className="text-xs text-[var(--lbl)]">V</span></div>
                    </div>
                </div>
            </div>
            <div className="h-px bg-[var(--line)] w-full" />
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 border border-[var(--line)] bg-[var(--panel-2)]"><Gauge className="w-5 h-5 text-[var(--lbl)]" /></div>
                    <div>
                        <div className="hmi-lbl">System Losses</div>
                        <div className="mono text-lg font-semibold text-[var(--txt-val)]">{stats.totalLossesKw.toFixed(1)} <span className="text-xs text-[var(--lbl)]">kW</span></div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="hmi-lbl">Congested Lines</div>
                    <div className={cn("mono text-lg font-semibold", stats.congestedLines > 0 ? "text-[var(--alarm)]" : "text-[var(--ok)]")}>{stats.congestedLines}</div>
                </div>
            </div>
            <div className="h-px bg-[var(--line)] w-full" />
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 border border-[var(--line)] bg-[var(--panel-2)]"><Power className="w-5 h-5 text-[var(--lbl)]" /></div>
                    <div>
                        <div className="hmi-lbl">Transformer</div>
                        <div className="flex items-baseline gap-2">
                            <span className={cn("mono text-lg font-semibold", stats.transformerLoadingPct > 100 ? "text-[var(--alarm)]" : stats.transformerLoadingPct > 80 ? "text-[var(--warn)]" : "text-[var(--txt-val)]")}>
                                {stats.transformerLoadingPct.toFixed(0)}<span className="text-xs text-[var(--lbl)]">% load</span>
                            </span>
                            <span className="mono text-xs text-[var(--lbl)]">{stats.transformerLossKw.toFixed(1)} kW loss</span>
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="hmi-lbl flex items-center gap-1 justify-end"><SunDim className="w-3 h-3" /> PV Curtailed</div>
                    <div className={cn("mono text-lg font-semibold", stats.curtailedKw > 0.05 ? "text-[var(--warn)]" : "text-[var(--ok)]")}>{stats.curtailedKw.toFixed(1)} <span className="text-xs text-[var(--lbl)]">kW</span></div>
                </div>
            </div>
        </div>
    );
}
