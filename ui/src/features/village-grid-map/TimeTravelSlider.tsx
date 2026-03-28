import { Activity } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface TimeTravelSliderProps {
    timeSlider: number;
    isHistorical: boolean;
    onTimeChange: (time: number) => void;
    onModeToggle: () => void;
}

export const TimeTravelSlider = ({
    timeSlider,
    isHistorical,
    onTimeChange,
    onModeToggle
}: TimeTravelSliderProps) => {
    const formatTime = (minutes: number) => {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    };

    return (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-10 w-full max-w-2xl px-6">
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-4 shadow-2xl shadow-black/50">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-400 flex items-center gap-2">
                        <Activity className={cn("h-3 w-3", !isHistorical ? "text-red-500 animate-pulse" : "text-slate-500")} />
                        {isHistorical ? "Historical Playback" : "Live Simulation"}
                    </span>
                    <span className="text-sm font-mono font-bold text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded">
                        {formatTime(timeSlider)}
                    </span>
                    <button
                        onClick={onModeToggle}
                        className={cn(
                            "text-[10px] uppercase tracking-widest font-bold px-2 py-1 rounded transition-colors",
                            isHistorical ? "bg-red-500/20 text-red-400 hover:bg-red-500/30" : "bg-green-500/20 text-green-400 hover:bg-green-500/30"
                        )}
                    >
                        {isHistorical ? "Reset to Live" : "Time Travel"}
                    </button>
                </div>
                <input
                    type="range"
                    min="0"
                    max="1440"
                    step="15"
                    value={timeSlider}
                    onChange={(e) => {
                        onTimeChange(parseInt(e.target.value));
                        if (!isHistorical) onModeToggle();
                    }}
                    className="w-full accent-orange-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between mt-2 text-[10px] text-slate-500 font-medium px-1">
                    <span>00:00</span>
                    <span>06:00</span>
                    <span>12:00</span>
                    <span>18:00</span>
                    <span>23:59</span>
                </div>
            </div>
        </div>
    );
};
