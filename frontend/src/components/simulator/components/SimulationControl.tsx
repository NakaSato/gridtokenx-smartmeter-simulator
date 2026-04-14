"use client";

import { useState, memo } from 'react';
import { 
    Sun, 
    Cloud, 
    CloudLightning, 
    Moon, 
    Activity, 
    Zap,
    ChevronUp,
    ChevronDown
} from 'lucide-react';
import { cn } from '@/lib/common';

interface SimulationControlProps {
    weatherMode: string;
    gridStress: number;
    onUpdateWeather: (mode: string) => Promise<void>;
    onUpdateStress: (multiplier: number) => Promise<void>;
    isLoading?: boolean;
}

export const SimulationControl = memo(({ 
    weatherMode, 
    gridStress, 
    onUpdateWeather, 
    onUpdateStress,
    isLoading 
}: SimulationControlProps) => {
    const [isExpanded, setIsExpanded] = useState(true);

    const weatherOptions = [
        { mode: 'Sunny', icon: Sun, color: 'text-amber-400', bg: 'bg-amber-400/10' },
        { mode: 'Cloudy', icon: Cloud, color: 'text-slate-400', bg: 'bg-slate-400/10' },
        { mode: 'Stormy', icon: CloudLightning, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
        { mode: 'Eclipse', icon: Moon, color: 'text-purple-400', bg: 'bg-purple-400/10' },
    ];

    return (
        <div className={cn(
            "fixed bottom-24 right-8 z-[2000] transition-all duration-300",
            isExpanded ? "w-72" : "w-14"
        )}>
            <div className="glass rounded-[2rem] border border-white/10 shadow-2xl overflow-hidden">
                {/* Header/Toggle */}
                <div 
                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400">
                            <Zap className="w-5 h-5 fill-current" />
                        </div>
                        {isExpanded && (
                            <span className="text-sm font-black uppercase tracking-widest text-white">Simulation</span>
                        )}
                    </div>
                    {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-500" />
                    ) : (
                        <ChevronUp className="w-4 h-4 text-slate-500" />
                    )}
                </div>

                {isExpanded && (
                    <div className="p-6 pt-2 space-y-8 animate-in slide-in-from-bottom-4 duration-300">
                        {/* Weather Selection */}
                        <div className="space-y-4">
                            <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Weather Mode</label>
                            <div className="grid grid-cols-2 gap-3">
                                {weatherOptions.map((opt) => (
                                    <button
                                        key={opt.mode}
                                        onClick={() => onUpdateWeather(opt.mode)}
                                        disabled={isLoading}
                                        className={cn(
                                            "flex flex-col items-center gap-2 p-3 rounded-2xl border transition-all active:scale-95 group",
                                            weatherMode === opt.mode 
                                                ? "bg-white/10 border-white/20 shadow-lg scale-105" 
                                                : "bg-black/20 border-white/5 hover:border-white/10 grayscale-[0.5] hover:grayscale-0"
                                        )}
                                    >
                                        <opt.icon className={cn("w-6 h-6", opt.color, "group-hover:scale-110 transition-transform")} />
                                        <span className="text-[10px] font-black text-slate-400">{opt.mode}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Grid Stress Slider */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-end">
                                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Grid Stress</label>
                                <span className={cn(
                                    "text-sm font-black tracking-tighter",
                                    gridStress > 1.2 ? "text-rose-400" : gridStress < 0.8 ? "text-emerald-400" : "text-amber-400"
                                )}>
                                    {gridStress.toFixed(1)}x
                                </span>
                            </div>
                            <div className="relative pt-1">
                                <input
                                    type="range"
                                    min="0.5"
                                    max="2.0"
                                    step="0.1"
                                    value={gridStress}
                                    onChange={(e) => onUpdateStress(parseFloat(e.target.value))}
                                    disabled={isLoading}
                                    className="w-full h-1.5 bg-black/40 rounded-full appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-400 transition-all"
                                />
                                <div className="flex justify-between mt-2">
                                    <span className="text-[8px] font-black text-slate-600">RELAX</span>
                                    <span className="text-[8px] font-black text-slate-600">CRITICAL</span>
                                </div>
                            </div>
                        </div>

                        {/* Status Footer */}
                        <div className="pt-2 flex items-center justify-between border-t border-white/5">
                            <div className="flex items-center gap-2">
                                <div className={cn(
                                    "w-1.5 h-1.5 rounded-full",
                                    weatherMode === 'Stormy' || gridStress > 1.5 ? "bg-rose-500 animate-pulse" : "bg-emerald-500"
                                )} />
                                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">
                                    {weatherMode === 'Eclipse' ? 'Extreme Event' : 'System Healthy'}
                                </span>
                            </div>
                            {isLoading && (
                                <Activity className="w-3 h-3 text-indigo-400 animate-spin" />
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
});

SimulationControl.displayName = 'SimulationControl';
