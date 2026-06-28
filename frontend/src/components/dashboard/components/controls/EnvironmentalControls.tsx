import { memo } from 'react';
import { Sun, Cloud, CloudLightning, Moon, Activity } from 'lucide-react';
import { cn } from '@/lib/common';
import type { SimulatorStatus } from '@/lib/types';

// Static — module scope so it isn't rebuilt every render (keeps a stable
// reference for the memoized component).
const weatherOptions = [
    { mode: 'Sunny', icon: Sun },
    { mode: 'Cloudy', icon: Cloud },
    { mode: 'Stormy', icon: CloudLightning },
    { mode: 'Eclipse', icon: Moon },
];

interface EnvironmentalControlsProps {
    status: SimulatorStatus;
    onUpdateWeather?: (mode: string) => Promise<void>;
    onUpdateStress?: (multiplier: number) => Promise<void>;
    isLoading?: boolean;
}

export const EnvironmentalControls = memo(({
    status, onUpdateWeather, onUpdateStress, isLoading
}: EnvironmentalControlsProps) => {
    return (
        <div className="flex flex-wrap items-center gap-6 bg-[var(--panel)] p-2 px-4 border border-[var(--line)]">
            <div className="flex items-center gap-2">
                {weatherOptions.map((opt) => (
                    <button
                        key={opt.mode}
                        onClick={() => onUpdateWeather?.(opt.mode)}
                        disabled={isLoading}
                        className={cn(
                            "hmi-btn p-2",
                            status.weather_mode === opt.mode && "active"
                        )}
                        title={opt.mode}
                    >
                        <opt.icon className="w-4 h-4 text-[var(--lbl)]" />
                    </button>
                ))}
            </div>

            <div className="h-8 w-px bg-[var(--line)] hidden sm:block" />

            <div className="flex items-center gap-4 min-w-[160px]">
                <div className="flex flex-col">
                    <span className="hmi-lbl leading-none mb-1">Stress</span>
                    <span className={cn(
                        "mono text-[11px]",
                        status.grid_stress > 1.2 ? "text-[var(--alarm)]" : status.grid_stress < 0.8 ? "text-[var(--ok)]" : "text-[var(--warn)]"
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
                        className="w-full h-1 bg-[var(--bar-bg)] appearance-none cursor-pointer accent-[var(--lbl)]"
                    />
                </div>
                {isLoading && (
                    <Activity className="w-3 h-3 text-[var(--lbl)] animate-spin" />
                )}
            </div>
        </div>
    );
});

EnvironmentalControls.displayName = 'EnvironmentalControls';
