export interface MeterSummary {
    meter_id: string;
    meter_type: string;
    location?: string;
    location_name?: string;
    latitude?: number | null;
    longitude?: number | null;
    phase?: string | number;
    bus_idx?: number;
    node_id?: string;
    bus_name?: string;
    has_solar?: boolean;
    solar_capacity?: number;
    status?: string;
    generation?: number;
    consumption?: number;
    generation_kw?: number;
    consumption_kw?: number;
    voltage?: number;
    rated_voltage_v?: number;
    phase_count?: number;
    province?: string;
    min_load_kw?: number;
    max_load_kw?: number;
    metadata?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface MeterReading {
    reading_id?: string;
    meter_id?: string;
    meter_serial?: string;
    timestamp: string;
    energy_generated?: number;
    energy_consumed?: number;
    surplus_energy?: number;
    deficit_energy?: number;
    interval_seconds?: number;
    voltage?: number;
    voltage_pu?: number;
    power_factor?: number;
    frequency?: number;
    temperature?: number;
    latitude?: number;
    longitude?: number;
    meter_type?: string;
    is_compromised?: boolean;
    is_shed?: boolean;
    nodal_price?: number;
    [key: string]: unknown;
}

export interface MeterListResponse {
    meters: MeterSummary[];
    total: number;
    source?: string;
}

export interface GridTopologyBus {
    node_id: string;
    name: string;
    vn_kv: number;
    type: string;
    kind?: 'transformer' | 'feeder' | 'service' | string;
    source_type?: string;
    phases?: string;
    is_substation?: boolean;
    depth?: number;
    parent?: string | null;
    children?: string[];
    degree?: number;
    has_solar?: boolean;
    solar_capacity_kw?: number;
    meter_solar_capacity_kw?: number;
    topology_solar_capacity_kw?: number;
    static_load_kw?: number;
    static_load_kvar?: number;
    voltage_pu?: number;
    load_kw?: number;
    load_kvar?: number;
    meter_ids?: string[];
}

export interface GridTopologyLine {
    id?: string;
    name: string;
    from_bus: number;
    to_bus: number;
    from_node?: string;
    to_node?: string;
    raw_from_node?: string;
    raw_to_node?: string;
    raw_direction?: string;
    is_reversed?: boolean;
    from_depth?: number;
    to_depth?: number;
    length_m?: number;
    length_km?: number;
    source_type?: string;
    phases?: string;
    capacity_kw?: number;
    resistance_ohm_per_km?: number;
    reactance_ohm_per_km?: number;
    flow_kw?: number;
    flow_kvar?: number;
    utilization_pct?: number;
    loss_kw?: number;
    status?: 'normal' | 'loaded' | 'congested' | string;
    direction?: string;
}

export interface GridTopologyResponse {
    topology?: {
        substation?: string;
        mode?: string;
        num_buses?: number;
        num_lines?: number;
        meters?: number;
        [key: string]: unknown;
    };
    buses?: Record<string, GridTopologyBus>;
    lines?: GridTopologyLine[];
}

export interface GridTelemetryResponse {
    summary?: Record<string, number>;
    buses?: Record<string, { voltage_pu?: number; load_kw?: number; [key: string]: unknown }>;
    lines?: Record<string, { utilization_pct?: number; flow_kw?: number; loss_kw?: number; [key: string]: unknown }>;
    readings?: MeterReading[];
}

export interface SimulationStatusResponse {
    running: boolean;
    paused: boolean;
    weather: string;
    grid_stress_multiplier: number;
    total_meters: number;
    mode: string;
    current_sim_time?: string;
    topology?: Record<string, unknown>;
    last_tick?: Record<string, unknown>;
}

/** One point in a deterministic-run time-series (aggregate or per-meter). */
export interface RunSeriesPoint {
    time: string;
    energy_generated?: number | null;
    energy_consumed?: number | null;
    net?: number | null;
    frequency?: number | null;
    voltage?: number | null;
}

/** Response of GET /history/run/series. */
export interface RunSeriesResponse {
    run_id: string;
    meter_id: string | null;
    count: number;
    series: RunSeriesPoint[];
}
