//! Core data models

use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct MeterConfig {
    pub meter_id: String,
    pub meter_type: String,
    pub location: String,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub zone_id: Option<i32>,
    pub wallet_address: Option<String>,
    pub has_solar: bool,
    pub solar_capacity_kw: f64,
    pub panel_efficiency: f64,
    pub has_battery: bool,
    pub battery_capacity_kwh: f64,
    pub max_charge_rate_kw: f64,
    pub max_discharge_rate_kw: f64,
    pub base_consumption_kw: f64,
    pub user_type: String,
}

#[pymethods]
impl MeterConfig {
    #[new]
    #[pyo3(signature = (
        meter_id,
        meter_type = "Grid_Consumer".to_string(),
        location = "Unknown".to_string(),
        latitude = None,
        longitude = None,
        zone_id = None,
        wallet_address = None,
        has_solar = false,
        solar_capacity_kw = 0.0,
        panel_efficiency = 0.18,
        has_battery = false,
        battery_capacity_kwh = 0.0,
        max_charge_rate_kw = 5.0,
        max_discharge_rate_kw = 5.0,
        base_consumption_kw = 1.0,
        user_type = "Residential".to_string()
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        meter_id: String,
        meter_type: String,
        location: String,
        latitude: Option<f64>,
        longitude: Option<f64>,
        zone_id: Option<i32>,
        wallet_address: Option<String>,
        has_solar: bool,
        solar_capacity_kw: f64,
        panel_efficiency: f64,
        has_battery: bool,
        battery_capacity_kwh: f64,
        max_charge_rate_kw: f64,
        max_discharge_rate_kw: f64,
        base_consumption_kw: f64,
        user_type: String,
    ) -> Self {
        Self {
            meter_id, meter_type, location, latitude, longitude, zone_id,
            wallet_address, has_solar, solar_capacity_kw, panel_efficiency,
            has_battery, battery_capacity_kwh, max_charge_rate_kw,
            max_discharge_rate_kw, base_consumption_kw, user_type,
        }
    }

    fn __repr__(&self) -> String {
        format!("MeterConfig(id='{}', type='{}', solar={}, battery={})",
            self.meter_id, self.meter_type, self.has_solar, self.has_battery)
    }
}

#[derive(Debug, Clone)]
#[pyclass(get_all, set_all)]
pub struct MeterState {
    pub meter_id: String,
    pub is_connected: bool,
    pub battery_level_pct: f64,
    pub battery_kwh: f64,
    pub weather: String,
    pub irradiance: f64,
    pub temperature_c: f64,
    pub buy_price: f64,
    pub sell_price: f64,
    pub total_generated_kwh: f64,
    pub total_consumed_kwh: f64,
    pub voltage_state: f64,
    pub frequency_state: f64,
    pub power_factor_state: f64,
    pub last_generation_kw: f64,
    pub last_consumption_kw: f64,
}

#[pymethods]
impl MeterState {
    #[new]
    fn new(meter_id: String) -> Self {
        Self {
            meter_id,
            is_connected: true,
            battery_level_pct: 50.0,
            battery_kwh: 0.0,
            weather: "Clear".to_string(),
            irradiance: 1.0,
            temperature_c: 25.0,
            buy_price: 0.28,
            sell_price: 0.12,
            total_generated_kwh: 0.0,
            total_consumed_kwh: 0.0,
            voltage_state: 230.0,
            frequency_state: 50.0,
            power_factor_state: 0.95,
            last_generation_kw: 0.0,
            last_consumption_kw: 0.0,
        }
    }

    fn __repr__(&self) -> String {
        format!("MeterState(id='{}', connected={}, battery={:.1}%)",
            self.meter_id, self.is_connected, self.battery_level_pct)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct EnergyReading {
    pub meter_id: String,
    pub timestamp: String,
    pub energy_generated_kwh: f64,
    pub energy_consumed_kwh: f64,
    pub surplus_kwh: f64,
    pub deficit_kwh: f64,
    pub battery_level_pct: f64,
    pub voltage_v: f64,
    pub current_a: f64,
    pub power_factor: f64,
    pub frequency_hz: f64,
    pub temperature_c: f64,
    pub net_emission_kg: f64,
    pub rec_eligible: bool,
    pub wallet_address: Option<String>,
    pub zone_id: Option<i32>,
}

#[pymethods]
impl EnergyReading {
    #[new]
    #[pyo3(signature = (
        meter_id,
        timestamp,
        energy_generated_kwh = 0.0,
        energy_consumed_kwh = 0.0,
        surplus_kwh = 0.0,
        deficit_kwh = 0.0,
        battery_level_pct = 0.0,
        voltage_v = 230.0,
        current_a = 0.0,
        power_factor = 0.95,
        frequency_hz = 50.0,
        temperature_c = 25.0,
        net_emission_kg = 0.0,
        rec_eligible = false,
        wallet_address = None,
        zone_id = None
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        meter_id: String, timestamp: String,
        energy_generated_kwh: f64, energy_consumed_kwh: f64,
        surplus_kwh: f64, deficit_kwh: f64, battery_level_pct: f64,
        voltage_v: f64, current_a: f64, power_factor: f64, frequency_hz: f64,
        temperature_c: f64, net_emission_kg: f64, rec_eligible: bool,
        wallet_address: Option<String>, zone_id: Option<i32>,
    ) -> Self {
        Self {
            meter_id, timestamp, energy_generated_kwh, energy_consumed_kwh,
            surplus_kwh, deficit_kwh, battery_level_pct, voltage_v, current_a,
            power_factor, frequency_hz, temperature_c, net_emission_kg,
            rec_eligible, wallet_address, zone_id,
        }
    }

    fn net_energy_kwh(&self) -> f64 {
        self.energy_generated_kwh - self.energy_consumed_kwh
    }

    fn real_power_w(&self) -> f64 {
        self.voltage_v * self.current_a * self.power_factor
    }

    fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    fn __repr__(&self) -> String {
        format!("EnergyReading(meter='{}', gen={:.3}kWh, cons={:.3}kWh)",
            self.meter_id, self.energy_generated_kwh, self.energy_consumed_kwh)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct GridState {
    pub meter_id: String,
    pub voltage_pu: f64,
    pub voltage_v: f64,
    pub frequency_hz: f64,
    pub power_factor: f64,
    pub thd_voltage_pct: f64,
    pub thd_current_pct: f64,
    pub is_on_peak: bool,
    pub temperature_c: f64,
    pub load_kw: f64,
    pub generation_kw: f64,
}

#[pymethods]
impl GridState {
    #[new]
    #[pyo3(signature = (meter_id, voltage_pu = 1.0, frequency_hz = 50.0, power_factor = 0.95))]
    fn new(meter_id: String, voltage_pu: f64, frequency_hz: f64, power_factor: f64) -> Self {
        Self {
            meter_id,
            voltage_pu,
            voltage_v: voltage_pu * 230.0,
            frequency_hz,
            power_factor,
            thd_voltage_pct: 2.0,
            thd_current_pct: 5.0,
            is_on_peak: false,
            temperature_c: 25.0,
            load_kw: 0.0,
            generation_kw: 0.0,
        }
    }

    fn is_voltage_normal(&self) -> bool {
        self.voltage_pu >= 0.95 && self.voltage_pu <= 1.05
    }

    fn is_frequency_normal(&self) -> bool {
        self.frequency_hz >= 49.5 && self.frequency_hz <= 50.5
    }

    fn __repr__(&self) -> String {
        format!("GridState(meter='{}', V={:.3}pu, f={:.2}Hz)",
            self.meter_id, self.voltage_pu, self.frequency_hz)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct ZoneState {
    pub zone_id: i32,
    pub transformer_name: String,
    pub meter_count: usize,
    pub avg_voltage_pu: f64,
    pub min_voltage_pu: f64,
    pub max_voltage_pu: f64,
    pub total_load_kw: f64,
    pub total_generation_kw: f64,
    pub net_power_kw: f64,
    pub has_voltage_violation: bool,
    pub has_overload: bool,
    pub health_score: f64,
}

impl ZoneState {
    /// Public constructor for Rust
    pub fn create(zone_id: i32, transformer_name: String) -> Self {
        Self {
            zone_id, transformer_name, meter_count: 0,
            avg_voltage_pu: 1.0, min_voltage_pu: 1.0, max_voltage_pu: 1.0,
            total_load_kw: 0.0, total_generation_kw: 0.0, net_power_kw: 0.0,
            has_voltage_violation: false, has_overload: false, health_score: 100.0,
        }
    }

    /// Public health score calculation for Rust
    pub fn compute_health_score(&mut self) {
        let voltage_penalty = (1.0 - self.avg_voltage_pu).abs() * 100.0;
        let mut score = 100.0 - voltage_penalty;
        if self.has_voltage_violation { score *= 0.8; }
        if self.has_overload { score *= 0.7; }
        self.health_score = score.max(0.0);
    }
}

#[pymethods]
impl ZoneState {
    #[new]
    fn new(zone_id: i32, transformer_name: String) -> Self {
        Self::create(zone_id, transformer_name)
    }

    fn calculate_health_score(&mut self) {
        self.compute_health_score();
    }

    fn __repr__(&self) -> String {
        format!("ZoneState(zone={}, meters={}, load={:.1}kW, health={:.1})",
            self.zone_id, self.meter_count, self.total_load_kw, self.health_score)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct MarketPrices {
    pub grid_buy_price: f64,
    pub grid_sell_price: f64,
    pub p2p_price: f64,
    pub is_peak_hour: bool,
    pub demand_multiplier: f64,
}

#[pymethods]
impl MarketPrices {
    #[new]
    #[pyo3(signature = (grid_buy_price = 0.28, grid_sell_price = 0.12, p2p_price = 0.18, is_peak_hour = false, demand_multiplier = 1.0))]
    fn new(grid_buy_price: f64, grid_sell_price: f64, p2p_price: f64, is_peak_hour: bool, demand_multiplier: f64) -> Self {
        Self { grid_buy_price, grid_sell_price, p2p_price, is_peak_hour, demand_multiplier }
    }

    fn __repr__(&self) -> String {
        format!("MarketPrices(buy={:.3}, sell={:.3}, peak={})",
            self.grid_buy_price, self.grid_sell_price, self.is_peak_hour)
    }
}
