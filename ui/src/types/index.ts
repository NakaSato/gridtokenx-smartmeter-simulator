export interface Reading {
    meter_id: string;
    meter_type: string;
    location: string;
    energy_generated: number;
    energy_consumed: number;
    surplus_energy: number;
    deficit_energy: number;
    battery_level: number;
    temperature: number;
    weather_condition: string;
    rec_eligible: boolean;
    carbon_offset: number;
    max_sell_price?: number;
    max_buy_price?: number;
    // Advanced Electrical Metrics
    voltage_pu?: number;
    current_a?: number;
    freq_hz?: number;
    power_factor?: number;
    // Cyber Security Metrics
    norm_residual?: number;
    ewma_residual?: number;
    is_compromised?: boolean;
    // On-chain Sync (Phase 25)
    is_synced_with_solana?: boolean;
    solana_sol_balance?: number;
    solana_gtnx_balance?: number;
}

export interface AttackAlert {
    meter_id: string;
    type: 'data_spike' | 'persistent_bias' | 'replay_attack';
    severity: 'low' | 'medium' | 'high';
    residual: number;
    ewma: number;
}

export interface GridHealth {
    timestamp: string;
    total_loss_mw: number;
    avg_voltage_pu: number;
    max_voltage_pu: number;
    min_voltage_pu: number;
    num_violations: number;
    loss_percentage: number;
    health_score: number;
    carbon_intensity: number; // gCO2/kWh
    avg_nodal_price: number; // $/kWh
    is_under_attack: boolean;
    anomaly_score: number;
    attack_alerts: AttackAlert[];
    total_consumption?: number;
    forecast?: {
        load: number[];
        generation: number[];
        net: number[];
    };
    market?: {
        mcp: number;
        volume_cleared: number;
        num_matches: number;
        total_demand: number;
        total_supply: number;
        timestamp: string;
    };
    vpp?: {
        cluster_id: string;
        resource_count: number;
        controllable_count: number;
        total_capacity_kwh: number;
        current_stored_kwh: number;
        flex_up_kw: number;
        flex_down_kw: number;
        soc_percentage: number;
        status: 'Normal' | 'Discharging' | 'Charging' | 'Idle' | 'Congested';
    };
    settlement?: {
        total_grid_revenue: number;
        total_grid_cost: number;
        total_p2p_volume: number;
    };
    tariff?: {
        type: string;
        import_rate: number;
        is_peak: boolean;
        forecast: number[];
    };
    adr_event?: {
        active: boolean;
        type: string | null;
    };
    frequency?: {
        value: number;
        rocof: number;
        angle: number;
    };
    island_status?: {
        is_islanded: boolean;
        forming_meter: string | null;
    };
}

export interface SolarPanel {
    id: number;
    geometry: {
        type: string;
        coordinates: [number, number] | [number, number][] | [number, number][][];
    };
    area_sqm: number;
    kwp_potential: number;
    confidence_score: number;
}

export interface SolarInventoryResponse {
    success: boolean;
    inventory: SolarPanel[];
    mapping: Record<string, number>;
}

// ============================================================================
// Price API Types
// ============================================================================

export interface PriceCompareRequest {
    energy_kwh: number;
    utility_provider: 'PEA' | 'MEA';
    tariff_category: string;
    billing_month: number;
    billing_year: number;
    p2p_price?: number;
    wheeling_cost?: number;
}

export interface PriceCompareResponse {
    timestamp: string;
    energy_kwh: number;
    utility: {
        provider: string;
        tariff_category: string;
        tariff_type: string;
        energy_charge_baht: number;
        ft_charge_baht: number;
        service_charge_baht: number;
        total_before_vat_baht: number;
        vat_baht: number;
        total_amount_baht: number;
        average_rate_baht_kwh: number;
        ft_rate_baht_kwh: number;
    };
    p2p: {
        market_clearing_price_baht_kwh: number;
        wheeling_cost_baht_kwh: number;
        buyer_total_baht_kwh: number;
        seller_net_baht_kwh: number;
        energy_cost_baht: number;
        wheeling_charge_baht: number;
        buyer_total_cost_baht: number;
        seller_net_revenue_baht: number;
        market_sentiment: string;
    };
    analysis: {
        buyer_savings_baht: number;
        buyer_savings_percent: number;
        seller_gain_baht: number;
        seller_gain_percent: number;
        total_welfare_gain_baht: number;
        is_p2p_beneficial: boolean;
        break_even_price_baht_kwh: number;
    };
    recommendation: string;
}

export interface UtilityRatesResponse {
    providers: Array<{
        name: string;
        rates: Array<{
            category: string;
            energy_charge: number;
            ft_charge: number;
        }>;
    }>;
}

export interface P2PCalculateCostRequest {
    buyer_zone_id: number;
    seller_zone_id: number;
    energy_amount: number;
    agreed_price: number;
}

export interface P2PCalculateCostResponse {
    energy_cost: number;
    wheeling_cost: number;
    loss_cost: number;
    total_cost: number;
    breakdown: {
        distance_km: number;
        wheeling_rate: number;
        loss_factor: number;
    };
}

// ============================================================================
// Dashboard and System Types
// ============================================================================

export type LogType = 'info' | 'success' | 'warning' | 'error' | 'reading';

export interface LogEntry {
    timestamp: string;
    message: string;
    type: LogType;
    reading?: Reading;
}

export interface SimulatorStatus {
    running: boolean;
    paused: boolean;
    num_meters: number;
    mode: 'random' | 'playback' | '-';
    health: Partial<GridHealth>;
    weather_mode: string;
    grid_stress: number;
}

export const ATTACK_MODES = ['bias', 'scale', 'random'] as const;
export type AttackMode = typeof ATTACK_MODES[number];

export interface AttackStatus {
    active: boolean;
    targets: string[];
    mode: AttackMode;
    bias_kw: number;
}

export interface AttackConfig {
    active: boolean;
    targets: string[];
    mode: AttackMode;
    bias: number;
    stealthy: boolean;
    scale: number;
}

export interface ApiError {
    message: string;
    code?: string;
    timestamp: string;
}

export interface WsMessage {
    tag?: 'READING_RECEIVED' | 'GRID_LOAD_UPDATE' | 'METER_ALERT';
    type?: 'meter_readings' | 'meter_reading' | 'grid_status';
    data?: unknown; // Generic data payload
    readings?: Reading[];
    reading?: Reading;
}
