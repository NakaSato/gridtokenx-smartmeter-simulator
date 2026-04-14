import { Clock, Shield } from 'lucide-react';

interface MapInfoCardProps {
    metersCount: number;
    healthScore?: number;
    carbonSaved?: number;
    anomalyCount?: number;
}

export const MapInfoCard = ({ 
    metersCount, 
    healthScore = 100, 
    carbonSaved = 0,
    anomalyCount = 0 
}: MapInfoCardProps) => {
    return (
        <div className="absolute top-20 right-4 sm:top-24 sm:right-6 z-[1000] glass px-3 sm:px-4 py-2 sm:py-3 rounded-lg sm:rounded-2xl border-white/10 bg-slate-900/60 backdrop-blur-xl max-w-[200px] sm:max-w-xs shadow-2xl">
            <div className="flex items-start">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                        <h4 className="text-sm font-black text-white tracking-tight">Village Microgrid</h4>
                        <div className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            healthScore > 90 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                            {healthScore.toFixed(0)}% HEALTH
                        </div>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed mb-4">
                        Real-time monitoring of {metersCount} smart meters with solar generation and VPP coordination.
                    </p>
                    
                    <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">CO2 Saved</span>
                            <span className="text-xs font-black text-emerald-400">{(carbonSaved / 1000).toFixed(2)} kg</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Anomalies</span>
                            <span className={`text-xs font-black ${anomalyCount > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                                {anomalyCount} detected
                            </span>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-3 pt-3 border-t border-white/10">
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-slate-500" />
                            <span className="text-[10px] font-bold text-slate-400">Real-time</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Shield className="w-3.5 h-3.5 text-slate-500" />
                            <span className="text-[10px] font-bold text-slate-400">Signed</span>
                        </div>
                        <div className="flex-1" />
                        <span className="text-[10px] font-black text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
                            AMI Enabled
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};
