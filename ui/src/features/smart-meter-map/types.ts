export interface MeterData {
    meter_id: string;
    location_name: string;
    latitude: number;
    longitude: number;
    phase: string;
    meter_type: string;
    generation: number;
    consumption: number;
    voltage: number;
    is_compromised?: boolean;
    nodal_price?: number;
}

export interface MapStats {
    totalHouses: number;
    producers: number;
    prosumers: number;
    consumers: number;
    netEnergy: number;
}

export const phaseColors = {
    'A': '#f97316',
    'B': '#3b82f6',
    'C': '#22c55e'
};
