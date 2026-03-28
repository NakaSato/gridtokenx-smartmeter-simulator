import { useMemo } from 'react';
import * as turf from '@turf/turf';

export interface VoltageMetrics {
    lengthM: number;
    vDropV: number;
    vDropPct: number;
}

/**
 * React hook to calculate real-time voltage drop for a grid segment.
 * Uses the 3-phase formula: ΔV = √3 * I * R * L
 * Includes a 3% sag factor for high-fidelity distance.
 */
export const useVoltageAnalysis = (
    coordinates: number[][] | null,
    currentA: number = 50,
    resistancePerKm: number = 0.32,
    voltageNominal: number = 416
) => {
    return useMemo((): VoltageMetrics | null => {
        if (!coordinates || coordinates.length < 2) return null;

        try {
            const line = turf.lineString(coordinates);
            const rawLengthKm = turf.length(line, { units: 'kilometers' });
            
            // 3% Sag Factor (CONSISTENT WITH BACKEND)
            const realLengthKm = rawLengthKm * 1.03;
            const realLengthM = realLengthKm * 1000;

            // ΔV = (√3 * I * R * L)
            const vDropV = 1.732 * currentA * resistancePerKm * realLengthKm;
            const vDropPct = (vDropV / voltageNominal) * 100;

            return {
                lengthM: parseFloat(realLengthM.toFixed(1)),
                vDropV: parseFloat(vDropV.toFixed(2)),
                vDropPct: parseFloat(vDropPct.toFixed(2))
            };
        } catch (err) {
            console.error('Turf calculation failed:', err);
            return null;
        }
    }, [coordinates, currentA, resistancePerKm, voltageNominal]);
};
