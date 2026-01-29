//! Complete smart meter simulation in Rust

use pyo3::prelude::*;
use pyo3::types::PyDict;
use chrono::{DateTime, Utc, Timelike, Datelike};
use rand::Rng;

use crate::solar::SolarCalculator;
use crate::load::LoadCalculator;
use crate::battery::BatteryState;
use crate::grid::GridPhysics;
use crate::emission::EmissionCalculator;

/// Complete meter configuration
#[pyclass]
#[derive(Debug, Clone)]
pub struct MeterSim {
    #[pyo3(get)]
    pub meter_id: String,
    #[pyo3(get)]
    pub meter_type: String,
    #[pyo3(get)]
    pub user_type: String,
    #[pyo3(get)]
    pub latitude: Option<f64>,
    #[pyo3(get)]
    pub longitude: Option<f64>,
    #[pyo3(get)]
    pub zone_id: Option<i32>,
    #[pyo3(get)]
    pub wallet_address: Option<String>,
    
    // Solar
    #[pyo3(get)]
    pub has_solar: bool,
    #[pyo3(get)]
    pub solar_capacity_kw: f64,
    
    // Battery
    #[pyo3(get)]
    pub has_battery: bool,
    #[pyo3(get)]
    pub battery_capacity_kwh: f64,
    
    // Base load
    #[pyo3(get)]
    pub base_consumption_kw: f64,
    
    // State tracking
    #[pyo3(get)]
    pub voltage_state: f64,
    #[pyo3(get)]
    pub frequency_state: f64,
    #[pyo3(get)]
    pub power_factor_state: f64,
    #[pyo3(get)]
    pub temperature_state: f64,
    
    // Accumulators
    #[pyo3(get)]
    pub total_energy_consumed: f64,
    #[pyo3(get)]
    pub total_energy_generated: f64,
    
    // Last values for smoothing
    #[pyo3(get)]
    pub last_consumption: f64,
    #[pyo3(get)]
    pub last_generation: f64,
    
    // Weather state
    #[pyo3(get)]
    pub weather: String,
    #[pyo3(get)]
    pub irradiance_factor: f64,
    #[pyo3(get)]
    pub temp_offset: f64,
    
    // Market prices
    #[pyo3(get)]
    pub sell_price: f64,
    #[pyo3(get)]
    pub buy_price: f64,
    
    // Connection status
    #[pyo3(get)]
    pub is_connected: bool,
    
    // Internal calculators (not exposed to Python)
    solar_calc: Option<SolarCalculator>,
    load_calc: Option<LoadCalculator>,
    battery: Option<BatteryState>,
    grid_physics: Option<GridPhysics>,
    emission_calc: Option<EmissionCalculator>,
}

/// Reading output
#[pyclass]
#[derive(Debug, Clone)]
pub struct SimReading {
    #[pyo3(get)]
    pub meter_id: String,
    #[pyo3(get)]
    pub timestamp: String,
    
    // Energy (kWh)
    #[pyo3(get)]
    pub energy_generated: f64,
    #[pyo3(get)]
    pub energy_consumed: f64,
    #[pyo3(get)]
    pub surplus_energy: f64,
    #[pyo3(get)]
    pub deficit_energy: f64,
    
    // Power (kW)
    #[pyo3(get)]
    pub power_generated: f64,
    #[pyo3(get)]
    pub power_consumed: f64,
    
    // Totals
    #[pyo3(get)]
    pub total_energy_generated: f64,
    #[pyo3(get)]
    pub total_energy_consumed: f64,
    
    // Battery
    #[pyo3(get)]
    pub battery_level_pct: f64,
    
    // Grid state
    #[pyo3(get)]
    pub voltage: f64,
    #[pyo3(get)]
    pub current: f64,
    #[pyo3(get)]
    pub frequency: f64,
    #[pyo3(get)]
    pub power_factor: f64,
    #[pyo3(get)]
    pub temperature: f64,
    
    // Market
    #[pyo3(get)]
    pub sell_price: f64,
    #[pyo3(get)]
    pub buy_price: f64,
    
    // Emissions
    #[pyo3(get)]
    pub net_emission: f64,
    #[pyo3(get)]
    pub rec_eligible: bool,
    #[pyo3(get)]
    pub carbon_offset: f64,
    
    // Metadata
    #[pyo3(get)]
    pub weather: String,
    #[pyo3(get)]
    pub zone_id: Option<i32>,
    #[pyo3(get)]
    pub wallet_address: Option<String>,
    #[pyo3(get)]
    pub latitude: Option<f64>,
    #[pyo3(get)]
    pub longitude: Option<f64>,
}

#[pymethods]
impl MeterSim {
    #[new]
    #[pyo3(signature = (
        meter_id,
        meter_type = "Grid_Consumer",
        user_type = "Residential",
        latitude = None,
        longitude = None,
        zone_id = None,
        wallet_address = None,
        has_solar = false,
        solar_capacity_kw = 0.0,
        has_battery = false,
        battery_capacity_kwh = 0.0,
        base_consumption_kw = 1.0,
        initial_battery_pct = 50.0
    ))]
    pub fn new(
        meter_id: String,
        meter_type: &str,
        user_type: &str,
        latitude: Option<f64>,
        longitude: Option<f64>,
        zone_id: Option<i32>,
        wallet_address: Option<String>,
        has_solar: bool,
        solar_capacity_kw: f64,
        has_battery: bool,
        battery_capacity_kwh: f64,
        base_consumption_kw: f64,
        initial_battery_pct: f64,
    ) -> Self {
        let mut rng = rand::thread_rng();
        
        // Initialize calculators
        let solar_calc = if has_solar && solar_capacity_kw > 0.0 {
            Some(SolarCalculator::new(0.18, 0.004))
        } else {
            None
        };
        
        let load_calc = Some(LoadCalculator::new(base_consumption_kw, user_type, 0.1));
        
        let battery = if has_battery && battery_capacity_kwh > 0.0 {
            Some(BatteryState::new(
                battery_capacity_kwh,
                5.0,
                5.0,
                0.95,
                initial_battery_pct / 100.0,
            ))
        } else {
            None
        };
        
        let grid_physics = Some(GridPhysics::new(230.0, 50.0, 0.05));
        let emission_calc = Some(EmissionCalculator::new(0.5, 0.05));
        
        // Random initial totals for "lived-in" feel
        let total_consumed = rng.gen_range(500.0..5000.0);
        let total_generated = if has_solar {
            rng.gen_range(500.0..5000.0)
        } else {
            0.0
        };
        
        MeterSim {
            meter_id,
            meter_type: meter_type.to_string(),
            user_type: user_type.to_string(),
            latitude,
            longitude,
            zone_id,
            wallet_address,
            has_solar,
            solar_capacity_kw,
            has_battery,
            battery_capacity_kwh,
            base_consumption_kw,
            voltage_state: 230.0,
            frequency_state: 50.0,
            power_factor_state: 0.95,
            temperature_state: 25.0,
            total_energy_consumed: total_consumed,
            total_energy_generated: total_generated,
            last_consumption: base_consumption_kw,
            last_generation: 0.0,
            weather: "Clear".to_string(),
            irradiance_factor: 1.0,
            temp_offset: 0.0,
            sell_price: 0.12,
            buy_price: 0.28,
            is_connected: true,
            solar_calc,
            load_calc,
            battery,
            grid_physics,
            emission_calc,
        }
    }
    
    /// Update weather state
    pub fn update_weather(&mut self, weather: &str, irradiance: f64, temp_offset: f64) {
        self.weather = weather.to_string();
        self.irradiance_factor = irradiance;
        self.temp_offset = temp_offset;
    }
    
    /// Update market prices
    pub fn update_prices(&mut self, sell_price: f64, buy_price: f64) {
        self.sell_price = sell_price;
        self.buy_price = buy_price;
    }
    
    /// Set zone ID
    pub fn set_zone(&mut self, zone_id: i32) {
        self.zone_id = Some(zone_id);
    }
    
    /// Get battery level percentage
    pub fn battery_level(&self) -> f64 {
        self.battery.as_ref().map(|b| b.level_pct()).unwrap_or(0.0)
    }
    
    /// Generate a reading for the given timestamp
    pub fn generate_reading(&mut self, timestamp_iso: &str) -> SimReading {
        let mut rng = rand::thread_rng();
        
        // Parse timestamp
        let timestamp: DateTime<Utc> = timestamp_iso.parse().unwrap_or_else(|_| Utc::now());
        let hour = timestamp.hour() as i32;
        let is_weekend = timestamp.weekday().num_days_from_monday() >= 5;
        let temperature = 25.0 + self.temp_offset;
        
        // Simulation interval (15 minutes = 0.25 hours)
        let interval_hours = 0.25;
        
        // 1. Calculate solar generation
        let mut power_generated = 0.0;
        if let Some(ref solar) = self.solar_calc {
            if self.has_solar && self.solar_capacity_kw > 0.0 {
                let raw_gen = solar.calculate(
                    self.solar_capacity_kw,
                    hour,
                    self.irradiance_factor,
                    temperature,
                    &self.weather,
                );
                // Smooth
                self.last_generation = solar.calculate_smooth(self.last_generation, raw_gen, 0.025);
                power_generated = self.last_generation;
            }
        }
        
        // 2. Calculate consumption
        let mut power_consumed = self.base_consumption_kw;
        if let Some(ref load) = self.load_calc {
            let raw_cons = load.calculate(hour, temperature, is_weekend);
            self.last_consumption = load.calculate_smooth(self.last_consumption, raw_cons, 0.025);
            power_consumed = self.last_consumption;
        }
        
        // 3. Update grid physics with EMA
        if let Some(ref physics) = self.grid_physics {
            let target_v = 230.0 + rng.gen::<f64>() * 0.2 - 0.1;
            let target_f = 50.0 + rng.gen::<f64>() * 0.004 - 0.002;
            let target_pf = (0.95 + rng.gen::<f64>() * 0.002 - 0.001).min(1.0);
            let target_temp = 20.0 + self.temp_offset + rng.gen::<f64>() * 0.1 - 0.05;
            
            self.voltage_state = physics.smooth_ema(self.voltage_state, target_v);
            self.frequency_state = physics.smooth_ema(self.frequency_state, target_f);
            self.power_factor_state = physics.smooth_ema(self.power_factor_state, target_pf);
            self.temperature_state = physics.smooth_ema(self.temperature_state, target_temp);
        }
        
        // 4. Convert power to energy
        let energy_generated = power_generated * interval_hours;
        let energy_consumed = power_consumed * interval_hours;
        
        // Update accumulators
        self.total_energy_generated += energy_generated;
        self.total_energy_consumed += energy_consumed;
        
        // 5. Battery logic
        let mut battery_level_pct = 0.0;
        if let Some(ref mut batt) = self.battery {
            let net = energy_generated - energy_consumed;
            if net > 0.0 {
                batt.charge(net, interval_hours);
            } else {
                batt.discharge(-net, interval_hours);
            }
            battery_level_pct = batt.level_pct();
        }
        
        // 6. Calculate net energy
        let net_energy = energy_generated - energy_consumed;
        let surplus = net_energy.max(0.0);
        let deficit = (-net_energy).max(0.0);
        
        // 7. Emissions
        let (net_emission, rec_eligible, carbon_offset) = if let Some(ref emission) = self.emission_calc {
            let net_em = emission.calculate_net_emission(energy_consumed, energy_generated, deficit);
            let rec = emission.is_rec_eligible(surplus);
            let offset = if rec { energy_generated * 0.5 } else { 0.0 }; // 0.5 kgCO2/kWh offset rate
            (net_em, rec, offset)
        } else {
            (0.0, false, 0.0)
        };
        
        // 8. Calculate current
        let total_power = power_generated + power_consumed;
        let current = if let Some(ref physics) = self.grid_physics {
            physics.calculate_current(total_power, self.voltage_state, self.power_factor_state)
        } else {
            0.0
        };
        
        SimReading {
            meter_id: self.meter_id.clone(),
            timestamp: timestamp_iso.to_string(),
            energy_generated: round_to(energy_generated, 6),
            energy_consumed: round_to(energy_consumed, 6),
            surplus_energy: round_to(surplus, 6),
            deficit_energy: round_to(deficit, 6),
            power_generated: round_to(power_generated, 4),
            power_consumed: round_to(power_consumed, 4),
            total_energy_generated: round_to(self.total_energy_generated, 4),
            total_energy_consumed: round_to(self.total_energy_consumed, 4),
            battery_level_pct: round_to(battery_level_pct, 2),
            voltage: round_to(self.voltage_state, 2),
            current: round_to(current, 3),
            frequency: round_to(self.frequency_state, 2),
            power_factor: round_to(self.power_factor_state, 2),
            temperature: round_to(self.temperature_state, 1),
            sell_price: round_to(self.sell_price, 4),
            buy_price: round_to(self.buy_price, 4),
            net_emission: round_to(net_emission, 4),
            rec_eligible,
            carbon_offset: round_to(carbon_offset, 4),
            weather: self.weather.clone(),
            zone_id: self.zone_id,
            wallet_address: self.wallet_address.clone(),
            latitude: self.latitude,
            longitude: self.longitude,
        }
    }
}

#[pymethods]
impl SimReading {
    /// Convert to dict for JSON serialization
    pub fn to_dict(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = PyDict::new_bound(py);
        dict.set_item("meter_id", &self.meter_id)?;
        dict.set_item("timestamp", &self.timestamp)?;
        dict.set_item("energy_generated", self.energy_generated)?;
        dict.set_item("energy_consumed", self.energy_consumed)?;
        dict.set_item("surplus_energy", self.surplus_energy)?;
        dict.set_item("deficit_energy", self.deficit_energy)?;
        dict.set_item("power_generated", self.power_generated)?;
        dict.set_item("power_consumed", self.power_consumed)?;
        dict.set_item("total_energy_generated", self.total_energy_generated)?;
        dict.set_item("total_energy_consumed", self.total_energy_consumed)?;
        dict.set_item("battery_level_pct", self.battery_level_pct)?;
        dict.set_item("voltage", self.voltage)?;
        dict.set_item("current", self.current)?;
        dict.set_item("frequency", self.frequency)?;
        dict.set_item("power_factor", self.power_factor)?;
        dict.set_item("temperature", self.temperature)?;
        dict.set_item("sell_price", self.sell_price)?;
        dict.set_item("buy_price", self.buy_price)?;
        dict.set_item("net_emission", self.net_emission)?;
        dict.set_item("rec_eligible", self.rec_eligible)?;
        dict.set_item("carbon_offset", self.carbon_offset)?;
        dict.set_item("weather", &self.weather)?;
        dict.set_item("zone_id", self.zone_id)?;
        dict.set_item("wallet_address", &self.wallet_address)?;
        dict.set_item("latitude", self.latitude)?;
        dict.set_item("longitude", self.longitude)?;
        Ok(dict.into())
    }
    
    /// Net energy (generation - consumption)
    pub fn net_energy(&self) -> f64 {
        self.energy_generated - self.energy_consumed
    }
}

fn round_to(value: f64, decimals: i32) -> f64 {
    let factor = 10_f64.powi(decimals);
    (value * factor).round() / factor
}
