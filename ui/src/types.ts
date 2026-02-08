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
    is_under_attack: boolean;
    anomaly_score: number;
    attack_alerts: AttackAlert[];
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
