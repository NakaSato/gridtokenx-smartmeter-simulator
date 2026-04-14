import { Zap } from 'lucide-react';
import type { MeterData } from './types';

interface MapLegendProps {
    meters: MeterData[];
}

export const MapLegend = ({ meters }: MapLegendProps) => {
    const stats = {
        totalHouses: meters.length,
        totalGeneration: meters.reduce((sum, m) => sum + m.generation, 0),
        totalConsumption: meters.reduce((sum, m) => sum + m.consumption, 0)
    };

    const netEnergy = stats.totalGeneration - stats.totalConsumption;

    return (
        <div className="absolute top-4 left-4 z-[1000] glass px-3 py-1.5 rounded-full flex items-center gap-2 text-xs font-bold border border-white/10 bg-slate-900/60 backdrop-blur-xl shadow-2xl">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-white">{stats.totalHouses} houses</span>
            <span className="text-white/30">|</span>
            <span className={netEnergy > 0 ? 'text-emerald-400' : 'text-rose-400'}>
                {netEnergy > 0 ? '+' : ''}{netEnergy.toFixed(1)} kWh
            </span>
        </div>
    );
};
