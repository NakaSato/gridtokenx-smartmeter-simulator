import { memo } from 'react';
import { Sun, Cloud, CloudLightning, Moon, Activity } from 'lucide-react';
import { cn } from '@/lib/common';
import type { SimulatorStatus } from '@/lib/types';

interface EnvironmentalControlsProps {
    status: SimulatorStatus;
    onUpdateWeather?: (mode: string) => Promise<void>;
    onUpdateStress?: (multiplier: number) => Promise<void>;
    isLoading?: boolean;
}

export const EnvironmentalControls = memo(({
    status, onUpdateWeather, onUpdateStress, isLoading
}: EnvironmentalControlsProps) => {
    const weatherOptions = [
        { mode: 'Sunny', icon: Sun, color: 'text-amber-400' },
        { mode: 'Cloudy', icon: Cloud, color: 'text-slate-400' },
        { mode: 'Stormy', icon: CloudLightning, color: 'text-indigo-400' },
        { mode: 'Eclipse', icon: Moon, color: 'text-purple-400' },
    ];

    return (
        <div className="flex flex-wrap items-center gap-6 bg-slate-900/50 p-2 px-4 rounded-2xl border border-white/5">
            <div className="flex items-center gap-2">
                {weatherOptions.map((opt) => (
                    <button
                        key={opt.mode}
                        onClick={() => onUpdateWeather?.(opt.mode)}
                        disabled={isLoading}
                        className={cn(
                            "p-2 rounded-xl border transition-all active:scale-95 group relative",
                            status.weather_mode === opt.mode 
                                ? "bg-white/10 border-white/20 shadow-lg" 
                                : "bg-black/20 border-white/5 hover:border-white/10 grayscale-[0.5] hover:grayscale-0"
                        )}
                        title={opt.mode}
                    >
                        <opt.icon className={cn("w-4 h-4", opt.color)} />
                    </button>
                ))}
            </div>

            <div className="h-8 w-px bg-white/10 hidden sm:block" />

            <div className="flex items-center gap-4 min-w-[160px]">
                <div className="flex flex-col">
                    <span className="text-[8px] font-black uppercase tracking-widest text-slate-500 leading-none mb-1">Stress</span>
                    <span className={cn(
                        "text-[10px] font-black tracking-tighter",
                        status.grid_stress > 1.2 ? "text-rose-400" : status.grid_stress < 0.8 ? "text-emerald-400" : "text-amber-400"
                    )}>
                        {status.grid_stress.toFixed(1)}x
                    </span>
                </div>
                <div className="flex-1 flex flex-col justify-center">
                    <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={status.grid_stress}
                        onChange={(e) => onUpdateStress?.(parseFloat(e.target.value))}
                        disabled={isLoading}
                        className="w-full h-1 bg-black/40 rounded-full appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-400 transition-all"
                    />
                </div>
                {isLoading && (
                    <Activity className="w-3 h-3 text-indigo-400 animate-spin" />
                )}
            </div>
        </div>
    );
});

EnvironmentalControls.displayName = 'EnvironmentalControls';
