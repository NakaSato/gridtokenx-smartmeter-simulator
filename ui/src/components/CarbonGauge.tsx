import { Leaf } from 'lucide-react';
import { cn } from '../utils';

interface CarbonGaugeProps {
    intensity: number; // gCO2/kWh
}

export function CarbonGauge({ intensity }: CarbonGaugeProps) {
    // Normalization: 0 to 600g
    const max = 600;
    const normalized = Math.min(Math.max(intensity, 0), max);
    const percentage = (normalized / max) * 100;

    // Determine color based on intensity
    let color = 'text-emerald-400';
    let label = 'Clean';
    let bg = 'bg-emerald-500/20';

    if (intensity > 400) {
        color = 'text-rose-400';
        label = 'High Carbon';
        bg = 'bg-rose-500/20';
    } else if (intensity > 200) {
        color = 'text-amber-400';
        label = 'Moderate';
        bg = 'bg-amber-500/20';
    }

    return (
        <div className="glass rounded-3xl p-6 bg-gradient-to-br from-slate-900/50 to-transparent border-white/5 relative overflow-hidden group hover:border-white/10 transition-all">
            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-3">
                    <Leaf className={cn("w-5 h-5", color)} />
                    <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">Carbon Intensity</h3>
                </div>
                <div className={cn(
                    "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest transition-colors",
                    bg, color
                )}>
                    {label}
                </div>
            </div>

            <div className="relative flex items-center justify-center py-4 z-10">
                {/* SVG Gauge */}
                <svg className="w-32 h-32 transform -rotate-90">
                    <circle
                        cx="64"
                        cy="64"
                        r="56"
                        stroke="currentColor"
                        strokeWidth="12"
                        fill="transparent"
                        className="text-slate-800"
                    />
                    <circle
                        cx="64"
                        cy="64"
                        r="56"
                        stroke="currentColor"
                        strokeWidth="12"
                        fill="transparent"
                        strokeDasharray={351.86}
                        strokeDashoffset={351.86 - (351.86 * percentage) / 100}
                        className={cn("transition-all duration-1000 ease-out", color)}
                        strokeLinecap="round"
                    />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <span className={cn("text-3xl font-black", color)}>{intensity.toFixed(0)}</span>
                    <span className="text-[10px] font-bold text-slate-500 uppercase">gCO2/kWh</span>
                </div>
            </div>

            {/* Background Glow */}
            <div className={cn(
                "absolute -right-12 -bottom-12 w-48 h-48 rounded-full blur-3xl opacity-10 transition-colors duration-700",
                color === 'text-emerald-400' ? 'bg-emerald-500' :
                    color === 'text-amber-400' ? 'bg-amber-500' : 'bg-rose-500'
            )} />
        </div>
    );
}
