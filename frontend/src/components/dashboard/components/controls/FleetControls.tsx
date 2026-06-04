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
    <div className="flex flex-wrap items-center gap-2 bg-slate-900/50 px-4 py-2 rounded-xl ml-2 shadow-inner">
        <Activity className="w-3 h-3 text-slate-500" />
        <input
            type="number"
            value={meterCount}
            onChange={(e) => setMeterCount(parseInt(e.target.value) || 20)}
            className="bg-transparent w-10 text-[10px] font-black text-slate-400 outline-none text-center"
            min="1"
            max="10000"
        />
        <input
            type="number"
            value={genMin}
            onChange={(e) => setGenMin(parseFloat(e.target.value) || 0)}
            className="bg-transparent w-8 text-[10px] font-black text-amber-400 outline-none text-center"
            placeholder="Min"
        />
        <input
            type="number"
            value={genMax}
            onChange={(e) => setGenMax(parseFloat(e.target.value) || 0)}
            className="bg-transparent w-8 text-[10px] font-black text-amber-400 outline-none text-center"
            placeholder="Max"
        />
        <button
            onClick={updateMeters}
            className="p-1 hover:bg-white/10 rounded transition-colors"
            title="Update Fleet Config"
        >
            <Plus className="w-3 h-3 text-emerald-400" />
        </button>
    </div>
));

FleetControls.displayName = 'FleetControls';
