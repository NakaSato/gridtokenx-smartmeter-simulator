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
        <div className="absolute top-4 left-4 z-[1000] glass px-3 py-1.5 flex items-center gap-2 text-xs">
            <Zap className="w-3.5 h-3.5 text-[var(--lbl)]" />
            <span className="text-[var(--txt-val)] font-medium mono">{stats.totalHouses} houses</span>
            <span className="text-[var(--line-2)]">|</span>
            <span className="font-medium mono" style={{ color: netEnergy >= 0 ? 'var(--ok)' : 'var(--alarm)' }}>
                {netEnergy > 0 ? '+' : ''}{netEnergy.toFixed(1)} kWh
            </span>
        </div>
    );
};
