//! API Models for SmartMeter REST API

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

// =============================================================================
// Meter Models
// =============================================================================

/// Request model for creating a new meter
#[derive(Debug, Clone, Deserialize)]
pub struct MeterRequest {
    pub meter_type: String,
    #[serde(default)]
    pub location: String,
    #[serde(default = "default_solar_capacity")]
    pub solar_capacity: f64,
    #[serde(default = "default_battery_capacity")]
    pub battery_capacity: f64,
    #[serde(default = "default_trading_preference")]
    pub trading_preference: String,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub wallet_address: Option<String>,
    pub meter_id: Option<String>,
}

fn default_solar_capacity() -> f64 { 10.0 }
fn default_battery_capacity() -> f64 { 10.0 }
fn default_trading_preference() -> String { "Moderate".to_string() }

/// Request model for meter override
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MeterOverrideRequest {
    #[serde(default)]
    pub energy_generated: f64,
    #[serde(default)]
    pub energy_consumed: f64,
    #[serde(default = "default_battery_level")]
    pub battery_level: f64,
    #[serde(default = "default_voltage")]
    pub voltage: f64,
    #[serde(default)]
    pub current: f64,
    #[serde(default = "default_frequency")]
    pub frequency: f64,
    #[serde(default = "default_temperature")]
    pub temperature: f64,
    #[serde(default = "default_power_factor")]
    pub power_factor: f64,
    pub max_sell_price: Option<f64>,
    pub max_buy_price: Option<f64>,
}

fn default_battery_level() -> f64 { 50.0 }
fn default_voltage() -> f64 { 240.0 }
fn default_frequency() -> f64 { 50.0 }
fn default_temperature() -> f64 { 25.0 }
fn default_power_factor() -> f64 { 1.0 }

/// Response for meter list
#[derive(Debug, Clone, Serialize)]
pub struct MeterListResponse {
    pub meters: Vec<MeterStatus>,
    pub total_meters: usize,
}

/// Meter status
#[derive(Debug, Clone, Serialize)]
pub struct MeterStatus {
    pub meter_id: String,
    pub meter_type: String,
    pub user_type: String,
    pub location: String,
    pub is_connected: bool,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub zone_id: Option<i32>,
    pub wallet_address: Option<String>,
    pub last_reading: Option<MeterReading>,
}

/// Meter reading data
#[derive(Debug, Clone, Serialize)]
pub struct MeterReading {
    pub timestamp: String,
    pub energy_generated: f64,
    pub energy_consumed: f64,
    pub surplus_energy: f64,
    pub deficit_energy: f64,
    pub battery_level_pct: f64,
    pub voltage: f64,
    pub current: f64,
    pub frequency: f64,
    pub power_factor: f64,
    pub temperature: f64,
}

/// Response for add meter
#[derive(Debug, Clone, Serialize)]
pub struct AddMeterResponse {
    pub success: bool,
    pub message: String,
    pub meter: MeterInfo,
    pub total_meters: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct MeterInfo {
    pub meter_id: String,
    pub meter_type: String,
    pub location: String,
    pub solar_capacity: f64,
    pub battery_capacity: f64,
    pub trading_preference: String,
    pub meter_public_key: String,
}

/// Generic success response
#[derive(Debug, Clone, Serialize)]
pub struct SuccessResponse {
    pub success: bool,
    pub message: String,
}

// =============================================================================
// Grid Models
// =============================================================================

/// Grid state response for a specific meter
#[derive(Debug, Clone, Serialize)]
pub struct GridStateResponse {
    pub meter_id: String,
    pub voltage_pu: f64,
    pub voltage_v: f64,
    pub frequency_hz: f64,
    pub power_factor: f64,
    pub thd_voltage: f64,
    pub thd_current: f64,
    pub is_on_peak: bool,
    pub temperature_c: f64,
}

/// Zone state response
#[derive(Debug, Clone, Serialize)]
pub struct ZoneStateResponse {
    pub zone_id: i32,
    pub avg_voltage_pu: f64,
    pub min_voltage_pu: f64,
    pub max_voltage_pu: f64,
    pub total_load_kw: f64,
    pub total_generation_kw: f64,
    pub net_power_kw: f64,
    pub meter_count: i32,
    pub has_voltage_violation: bool,
    pub has_overload: bool,
    pub health_score: f64,
}

/// Grid status response
#[derive(Debug, Clone, Serialize)]
pub struct GridStatusResponse {
    pub total_generation: f64,
    pub total_consumption: f64,
    pub net_balance: f64,
    pub active_meters: i32,
    pub co2_saved_kg: f64,
    pub timestamp: String,
}

/// Zone info
#[derive(Debug, Clone, Serialize)]
pub struct ZoneInfo {
    pub zone_id: i32,
    pub centroid_lat: f64,
    pub centroid_lon: f64,
    pub meter_count: i32,
    pub transformer_name: String,
}

/// Zones response
#[derive(Debug, Clone, Serialize)]
pub struct ZonesResponse {
    pub zones: std::collections::HashMap<String, ZoneInfo>,
    pub meters: Vec<MeterZoneInfo>,
    pub wheeling_charges: std::collections::HashMap<String, f64>,
    pub loss_factors: std::collections::HashMap<String, f64>,
}

#[derive(Debug, Clone, Serialize)]
pub struct MeterZoneInfo {
    pub meter_id: String,
    pub latitude: f64,
    pub longitude: f64,
    pub zone_id: Option<i32>,
    pub meter_type: String,
}

/// Battery dispatch request
#[derive(Debug, Clone, Deserialize)]
pub struct BatteryDispatchRequest {
    pub meter_id: String,
    pub power_kw: f64,
}

/// Battery dispatch response
#[derive(Debug, Clone, Serialize)]
pub struct BatteryDispatchResponse {
    pub success: bool,
    pub meter_id: String,
    pub power_kw: f64,
    pub new_battery_level: Option<f64>,
    pub message: String,
}

/// Grid analysis response
#[derive(Debug, Clone, Serialize)]
pub struct GridAnalysisResponse {
    pub timestamp: String,
    pub power_flow_converged: bool,
    pub total_load_mw: f64,
    pub total_generation_mw: f64,
    pub total_loss_mw: f64,
    pub loss_percentage: f64,
    pub zone_count: i32,
    pub voltage_violations: Vec<String>,
    pub overloaded_elements: Vec<String>,
    pub recommendations: Vec<String>,
}

/// Grid health response
#[derive(Debug, Clone, Serialize)]
pub struct GridHealthResponse {
    pub healthy: bool,
    pub meter_count: i32,
    pub simulation_time: Option<String>,
    pub model_type: String,
}

// =============================================================================
// Simulation Models
// =============================================================================

/// Simulation status response
#[derive(Debug, Clone, Serialize)]
pub struct SimulationStatusResponse {
    pub is_running: bool,
    pub is_paused: bool,
    pub current_time: Option<String>,
    pub meter_count: i32,
    pub tick_count: u64,
    pub uptime_seconds: f64,
}

/// Simulation parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimulationParameters {
    pub real_time_interval: f64,
    pub sim_interval: f64,
    pub weather: String,
    pub solar_multiplier: f64,
    pub consumption_multiplier: f64,
    pub grid_buy_price: f64,
    pub grid_sell_price: f64,
}

impl Default for SimulationParameters {
    fn default() -> Self {
        Self {
            real_time_interval: 5.0,
            sim_interval: 900.0,
            weather: "Auto".to_string(),
            solar_multiplier: 1.0,
            consumption_multiplier: 1.0,
            grid_buy_price: 0.28,
            grid_sell_price: 0.12,
        }
    }
}

// =============================================================================
// P2P Models
// =============================================================================

/// P2P cost calculation request
#[derive(Debug, Clone, Deserialize)]
pub struct P2PCostRequest {
    pub buyer_zone_id: i32,
    pub seller_zone_id: i32,
    pub energy_amount: f64,
    #[serde(default = "default_agreed_price")]
    pub agreed_price: f64,
}

fn default_agreed_price() -> f64 { 4.0 }

/// P2P cost calculation response
#[derive(Debug, Clone, Serialize)]
pub struct P2PCostResponse {
    pub energy_cost: f64,
    pub wheeling_charge: f64,
    pub loss_cost: f64,
    pub total_cost: f64,
    pub effective_energy: f64,
    pub loss_factor: f64,
    pub loss_allocation: String,
    pub zone_distance_km: f64,
    pub buyer_zone: i32,
    pub seller_zone: i32,
    pub is_grid_compliant: bool,
    pub grid_violation_reason: Option<String>,
}

// =============================================================================
// Error Response
// =============================================================================

/// Error response
#[derive(Debug, Clone, Serialize)]
pub struct ErrorResponse {
    pub error: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub detail: Option<String>,
}

impl ErrorResponse {
    pub fn new(error: impl Into<String>) -> Self {
        Self {
            error: error.into(),
            detail: None,
        }
    }
    
    pub fn with_detail(error: impl Into<String>, detail: impl Into<String>) -> Self {
        Self {
            error: error.into(),
            detail: Some(detail.into()),
        }
    }
}
