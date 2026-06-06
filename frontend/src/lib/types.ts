export type LogType = 'info' | 'success' | 'warning' | 'error' | 'reading';
export type AttackMode = 'bias' | 'scale' | 'random' | string;

export interface ApiError {
    message: string;
    code?: string;
    timestamp: string;
}

export interface Reading {
    meter_id: string;
    meter_serial?: string;
    serial_number?: string;
    meter_type: string;
    location?: string;
    location_name?: string;
    latitude?: number | null;
    longitude?: number | null;
    phase?: string | number;
    timestamp?: string;
    energy_generated: number;
    energy_consumed: number;
    surplus_energy?: number;
    deficit_energy?: number;
    generation_kw?: number;
    consumption_kw?: number;
    voltage?: number;
    voltage_pu?: number;
    freq_hz?: number;
    frequency?: number;
    power_factor?: number;
    temperature?: number;
    battery_level: number;
    carbon_offset?: number;
    nodal_price?: number;
    min_load_kw?: number;
    max_load_kw?: number;
    has_solar?: boolean;
    solar_capacity?: number;
    has_battery?: boolean;
    battery_capacity_kwh?: number;
    is_compromised?: boolean;
    is_shed?: boolean;
    norm_residual?: number;
    is_synced_with_solana?: boolean;
    solana_sol_balance?: number;
    solana_gtnx_balance?: number;
    battery_capacity?: number;
    metadata?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface GridHealth {
    health_score?: number;
    total_generation_kw?: number;
    total_consumption_kw?: number;
    total_losses_kw?: number;
    congested_lines?: number;
    [key: string]: unknown;
}

export interface SimulatorStatus {
    running: boolean;
    paused: boolean;
    num_meters: number;
    mode: string;
    health: Record<string, unknown>;
    weather_mode: string;
    grid_stress: number;
}

export interface AttackStatus {
    active: boolean;
    targets: string[];
    mode: string;
    bias_kw: number;
}

export interface LogEntry {
    timestamp: string;
    message: string;
    type: LogType;
    reading?: Reading;
}
