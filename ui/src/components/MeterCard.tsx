import { MapPin, Sun, Zap, Battery, Thermometer } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Re-using the Reading interface (we should probably extract this to a types file later)
import type { Reading } from '../types';

export const MeterCard = ({ reading }: { reading: Reading }) => {
    const typeColors: Record<string, string> = {
        Solar_Prosumer: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/30",
        Grid_Consumer: "from-blue-500/20 to-blue-500/5 border-blue-500/30",
        Hybrid_Prosumer: "from-purple-500/20 to-purple-500/5 border-purple-500/30",
        Battery_Storage: "from-rose-500/20 to-rose-500/5 border-rose-500/30",
    };

    return (
        <div className={cn(
            "relative overflow-hidden glass rounded-3xl p-6 border transition-all hover:scale-[1.02] hover:shadow-2xl active:scale-[0.98] cursor-pointer bg-gradient-to-br",
            typeColors[reading.meter_type as keyof typeof typeColors] || "from-slate-500/20 to-slate-500/5 border-slate-500/30"
        )}>
            <div className="relative z-10 space-y-4">
                <div className="flex justify-between items-start">
                    <div className="space-y-1">
                        <h3 className="font-black text-lg tracking-tight">{reading.meter_id}</h3>
                        <div className="flex items-center gap-2">
                            <MapPin className="w-3 h-3 text-slate-500" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{reading.location}</span>
                        </div>
                    </div>
                    <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10">
                        <span className="text-[8px] font-black uppercase tracking-tighter text-slate-400">{reading.meter_type.replace('_', ' ')}</span>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/40 p-3 rounded-2xl border border-white/5 space-y-1">
                        <div className="flex items-center gap-2">
                            <Sun className="w-3 h-3 text-emerald-400" />
                            <span className="text-[8px] font-black uppercase tracking-widest text-slate-500">Gen</span>
                        </div>
                        <div className="font-black text-emerald-400">{reading.energy_generated.toFixed(2)}<span className="text-[8px] ml-1">kWh</span></div>
                    </div>
                    <div className="bg-slate-900/40 p-3 rounded-2xl border border-white/5 space-y-1">
                        <div className="flex items-center gap-2">
                            <Zap className="w-3 h-3 text-rose-400" />
                            <span className="text-[8px] font-black uppercase tracking-widest text-slate-500">Cons</span>
                        </div>
                        <div className="font-black text-rose-400">{reading.energy_consumed.toFixed(2)}<span className="text-[8px] ml-1">kWh</span></div>
                    </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Battery className={cn("w-4 h-4", reading.battery_level > 20 ? "text-emerald-400" : "text-rose-400")} />
                            <span className="text-xs font-black">{reading.battery_level.toFixed(0)}%</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Thermometer className="w-4 h-4 text-slate-500" />
                            <span className="text-xs font-black text-slate-400">{reading.temperature.toFixed(1)}°</span>
                        </div>
                    </div>
                    {reading.surplus_energy > 0 && (
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse" />
                            <span className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Trading</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
