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
    deterministic?: boolean;
    seed?: number;
    start_time?: string;
    end_time?: string;
    run_id?: string;
    interval_seconds?: number;
    topology?: Record<string, unknown>;
    last_tick?: Record<string, unknown>;
    /** InfluxDB write-path health; null when persistence is disabled. */
    influx?: InfluxHealth | null;
}

/** Write-path health from GET /simulation/status (engine.influx_store.health()). */
export interface InfluxHealth {
    connected: boolean;
    bucket: string;
    writes_ok: number;
    writes_failed: number;
    last_error: string | null;
}

/** Preset run-window length, sent instead of an explicit end_time. */
export type SimTimeRange = 'hour' | 'day' | 'week' | 'month' | 'year';

/** Payload of POST /simulation/actions/start-deterministic. */
export interface StartDeterministicPayload {
    seed?: number;
    /** ISO-8601 sim-clock origin, e.g. 2026-06-10T08:00:00+00:00. */
    start_time?: string;
    /** ISO-8601 sim-clock end; window is [start, end). */
    end_time?: string;
    /** Preset window length — alternative to end_time. */
    time_range?: SimTimeRange;
    interval?: number;
    num_meters?: number;
    autostart?: boolean;
}

/** Response of GET /simulation/runtime — the sim-clock window + cursor. */
export interface SimulationRuntime {
    start_time?: string;
    end_time?: string;
    current_sim_time?: string;
    [key: string]: unknown;
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

/** One itemised line of a meter bill. */
export interface MeterBillLine {
    label: string;
    kwh: number;
    rate: number;
    amount: number;
}

/** Response of GET /meters/{id}/bill — accumulated import billed, surplus sold. */
export interface MeterBill {
    meter_id: string;
    tariff: string;
    currency: string;
    kwh_total: number;
    energy_charge: number;
    ft_charge: number;
    service_charge: number;
    subtotal: number;
    vat: number;
    total: number;
    average_rate_per_kwh: number;
    export_kwh: number;
    export_rate: number;
    export_credit: number;
    net_total: number;
    months: number;
    lines: MeterBillLine[];
}

/** Response of GET /carbon/factors — the emission factors used by the model. */
export interface CarbonFactors {
    unit: string;
    grid_intensity: number;
    solar_intensity: number;
    kg_per_tree_year: number;
    note: string;
}

/**
 * CO2 accounting for a meter or fleet.
 *   grid_emissions_kg = import × grid_intensity
 *   gross_offset_kg   = export × grid_intensity (ignores PV lifecycle)
 *   offset_kg         = export × (grid_intensity − solar_intensity), clamped ≥0
 *   net_emissions_kg  = grid_emissions − offset (negative = carbon-negative)
 *   trees_equivalent  = offset_kg / kg_per_tree_year
 */
export interface CarbonOffset {
    import_kwh: number;
    export_kwh: number;
    grid_intensity_kgco2_per_kwh: number;
    solar_intensity_kgco2_per_kwh: number;
    grid_emissions_kg: number;
    gross_offset_kg: number;
    offset_kg: number;
    net_emissions_kg: number;
    trees_equivalent: number;
    unit: string;
    /** Present on GET /meters/{id}/carbon, absent on quote. */
    meter_id?: string;
}

/** Response of GET /carbon/summary — fleet aggregate, adds meter_count. */
export interface CarbonSummary extends CarbonOffset {
    meter_count: number;
}

/** One on/off hardening layer in the security posture. */
export interface SecurityLayer {
    name: string;
    on: boolean;
}

/** DLMS metering egress posture. */
export interface SecurityMeteringEgress {
    enabled: boolean;
    endpoint: string;
    tls: boolean;
    tls_verify: boolean;
    mtls: boolean;
    payload_encryption: boolean;
    key_rotation: boolean;
    rotation_interval_s: number;
    key_grace_versions: number;
}

/** Operational/SCADA egress posture. */
export interface SecurityOperationalEgress {
    enabled: boolean;
    transport: string;
    endpoint: string;
    tls: boolean;
    mtls: boolean;
    api_key: boolean;
}

/** Response of GET /security/status — egress hardening posture + key versions. */
export interface SecurityStatusResponse {
    secure: boolean;
    layers: SecurityLayer[];
    metering_egress: SecurityMeteringEgress;
    operational_egress: SecurityOperationalEgress;
    keys: {
        rotation_active: boolean;
        meter_count: number;
        versions: Record<string, number>;
    };
}
