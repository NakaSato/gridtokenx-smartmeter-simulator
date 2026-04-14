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
