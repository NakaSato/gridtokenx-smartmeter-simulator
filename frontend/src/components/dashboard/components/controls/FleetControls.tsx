import { memo } from 'react';
import { Plus, Activity } from 'lucide-react';

interface FleetControlsProps {
    meterCount: number;
    setMeterCount: (count: number) => void;
    updateMeters: () => void;
    genMin: number;
    setGenMin: (val: number) => void;
    genMax: number;
    setGenMax: (val: number) => void;
}

export const FleetControls = memo(({
    meterCount, setMeterCount, updateMeters, genMin, setGenMin, genMax, setGenMax
}: FleetControlsProps) => (
    <div className="flex flex-wrap items-center gap-2 bg-[var(--panel)] px-4 py-2 ml-2 border border-[var(--line)]">
        <Activity className="w-3 h-3 text-[var(--lbl)]" />
        <input
            type="number"
            value={meterCount}
            onChange={(e) => setMeterCount(parseInt(e.target.value) || 20)}
            className="hmi-input mono w-12 px-1 py-0.5 text-center"
            min="1"
            max="10000"
        />
        <input
            type="number"
            value={genMin}
            onChange={(e) => setGenMin(parseFloat(e.target.value) || 0)}
            className="hmi-input mono w-12 px-1 py-0.5 text-center"
            placeholder="Min"
        />
        <input
            type="number"
            value={genMax}
            onChange={(e) => setGenMax(parseFloat(e.target.value) || 0)}
            className="hmi-input mono w-12 px-1 py-0.5 text-center"
            placeholder="Max"
        />
        <button
            onClick={updateMeters}
            className="hmi-btn p-1"
            title="Update Fleet Config"
        >
            <Plus className="w-3 h-3" />
        </button>
    </div>
));

FleetControls.displayName = 'FleetControls';
