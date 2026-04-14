import { RefreshCw, Layers } from 'lucide-react';

interface MapControlsProps {
    showZones: boolean;
    onToggleZones: () => void;
    onRefresh: () => void;
    carbonIntensity?: number;
    metersCount: number;
    isConnected: boolean;
}

export const MapControls = ({
    showZones,
    onToggleZones,
    onRefresh,
    carbonIntensity = 250,
    metersCount,
    isConnected
}: MapControlsProps) => {
    const getCarbonStatus = (intensity: number) => {
        if (intensity < 150) return { label: 'CLEAN', color: 'text-emerald-400' };
        if (intensity < 350) return { label: 'MIXED', color: 'text-amber-400' };
        return { label: 'DIRTY', color: 'text-rose-400' };
    };

    const carbonStatus = getCarbonStatus(carbonIntensity);

    return (
        <div className="absolute bottom-4 right-4 sm:bottom-6 sm:right-6 z-[1000] flex flex-col gap-2 pointer-events-none">
            {/* Stats bar */}
            <div className="pointer-events-auto glass px-2.5 py-1.5 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl flex items-center gap-2 sm:gap-3 text-[10px] sm:text-xs shadow-xl max-w-[calc(100vw-2rem)] sm:max-w-none">
                <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
                    <div className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full shrink-0 ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                    <span className={`font-bold ${isConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isConnected ? 'LIVE' : 'OFF'}
                    </span>
                </div>
                <span className="text-slate-700 shrink-0">·</span>
                <span className={`font-black shrink-0 ${carbonStatus.color}`}>{carbonStatus.label}</span>
                <span className="text-slate-500 font-medium shrink-0 hidden sm:inline">{Math.round(carbonIntensity)} g/kWh</span>
                <span className="text-slate-700 shrink-0">·</span>
                <span className="text-slate-400 font-medium truncate">{metersCount} meters</span>
            </div>

            {/* Action buttons */}
            <div className="pointer-events-auto flex items-center gap-1 sm:gap-1.5 overflow-x-auto pb-0.5">
                <button
                    onClick={onToggleZones}
                    className={`glass px-3 py-2 rounded-lg flex items-center gap-1.5 text-xs font-bold transition-all ${
                        showZones ? 'bg-indigo-500/25 text-indigo-400' : 'text-slate-400 hover:text-white hover:bg-white/10'
                    }`}
                >
                    <Layers className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">{showZones ? 'Hide Zone' : 'Zones'}</span>
                </button>
                <button
                    onClick={onRefresh}
                    className="glass px-3 py-2 rounded-lg flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                >
                    <RefreshCw className="w-3.5 h-3.5 hover:rotate-180 transition-transform duration-500" />
                    <span className="hidden sm:inline">Refresh</span>
                </button>
            </div>
        </div>
    );
};
