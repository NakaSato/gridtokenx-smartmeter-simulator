export interface VillageHouse {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    phase: 'A' | 'B' | 'C';
    generation: number;
    consumption: number;
    voltage: number;
    nodal_price?: number;
}

export interface MapStats {
    totalGeneration: number;
    totalConsumption: number;
    avgVoltage: number;
    phaseBalance: { A: number; B: number; C: number };
    selfSufficiency: number;
    carbonOffset: number;
}

export interface Trade {
    buyer: string;
    seller: string;
    energy_kwh: number;
    price: number;
    timestamp: string;
}

export const phaseColors = {
    'A': '#f97316',
    'B': '#3b82f6',
    'C': '#22c55e'
} as const;
