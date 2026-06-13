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
        if (intensity < 150) return { label: 'CLEAN', color: 'var(--ok)' };
        if (intensity < 350) return { label: 'MIXED', color: 'var(--warn)' };
        return { label: 'DIRTY', color: 'var(--alarm)' };
    };

    const carbonStatus = getCarbonStatus(carbonIntensity);

    return (
        <div className="absolute bottom-4 right-4 sm:bottom-6 sm:right-6 z-[1000] flex flex-col gap-2 pointer-events-none">
            {/* Stats bar */}
            <div className="pointer-events-auto glass px-2.5 py-1.5 sm:px-4 sm:py-2 flex items-center gap-2 sm:gap-3 text-[10px] sm:text-xs max-w-[calc(100vw-2rem)] sm:max-w-none">
                <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
                    <span className={`hmi-dot shrink-0 ${isConnected ? '' : 'alarm'}`} />
                    <span className="font-medium" style={{ color: isConnected ? 'var(--ok)' : 'var(--alarm)' }}>
                        {isConnected ? 'LIVE' : 'OFF'}
                    </span>
                </div>
                <span className="text-[var(--line-2)] shrink-0">·</span>
                <span className="font-semibold shrink-0" style={{ color: carbonStatus.color }}>{carbonStatus.label}</span>
                <span className="text-[var(--lbl)] font-medium shrink-0 hidden sm:inline mono">{Math.round(carbonIntensity)} g/kWh</span>
                <span className="text-[var(--line-2)] shrink-0">·</span>
                <span className="text-[var(--lbl)] font-medium truncate mono">{metersCount} meters</span>
            </div>

            {/* Action buttons */}
            <div className="pointer-events-auto flex items-center gap-1 sm:gap-1.5 overflow-x-auto pb-0.5">
                <button
                    onClick={onToggleZones}
                    className={`hmi-btn ${showZones ? 'active' : ''}`}
                >
                    <Layers className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">{showZones ? 'Hide Zone' : 'Zones'}</span>
                </button>
                <button type="button" onClick={onRefresh} className="hmi-btn">
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Refresh</span>
                </button>
            </div>
        </div>
    );
};
