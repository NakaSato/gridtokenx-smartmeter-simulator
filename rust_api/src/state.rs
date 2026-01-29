//! Application state for the API server

use std::sync::{Arc, RwLock};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use rand::Rng;

use crate::models::*;

/// Simulation engine state
#[derive(Debug, Clone)]
pub struct MeterState {
    pub meter_id: String,
    pub meter_type: String,
    pub user_type: String,
    pub location: String,
    pub is_connected: bool,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub zone_id: Option<i32>,
    pub wallet_address: Option<String>,
    pub solar_capacity: f64,
    pub battery_capacity: f64,
    pub battery_level: f64,
    pub trading_preference: String,
    pub last_reading: Option<MeterReading>,
    pub override_data: Option<MeterOverrideRequest>,
    // Internal state for simulation
    pub total_energy_generated: f64,
    pub total_energy_consumed: f64,
}

impl MeterState {
    pub fn new(config: &MeterRequest) -> Self {
        let mut rng = rand::thread_rng();
        let meter_id = config.meter_id.clone()
            .unwrap_or_else(|| uuid::Uuid::new_v4().to_string());
        
        let is_prosumer = config.meter_type.contains("Prosumer");
        let has_battery = config.meter_type.contains("Hybrid") || config.meter_type.contains("Battery");
        
        Self {
            meter_id,
            meter_type: config.meter_type.clone(),
            user_type: if is_prosumer { "Prosumer".to_string() } else { "Consumer".to_string() },
            location: if config.location.is_empty() {
                format!("Zone_{}_Building_{}", rng.gen_range(1..=5), rng.gen_range(1..=10))
            } else {
                config.location.clone()
            },
            is_connected: true,
            latitude: config.latitude,
            longitude: config.longitude,
            zone_id: None,
            wallet_address: config.wallet_address.clone(),
            solar_capacity: if is_prosumer { config.solar_capacity } else { 0.0 },
            battery_capacity: if has_battery { config.battery_capacity } else { 0.0 },
            battery_level: if has_battery { rng.gen_range(20.0..80.0) } else { 0.0 },
            trading_preference: config.trading_preference.clone(),
            last_reading: None,
            override_data: None,
            total_energy_generated: rng.gen_range(100.0..1000.0),
            total_energy_consumed: rng.gen_range(100.0..1000.0),
        }
    }
    
    pub fn to_status(&self) -> MeterStatus {
        MeterStatus {
            meter_id: self.meter_id.clone(),
            meter_type: self.meter_type.clone(),
            user_type: self.user_type.clone(),
            location: self.location.clone(),
            is_connected: self.is_connected,
            latitude: self.latitude,
            longitude: self.longitude,
            zone_id: self.zone_id,
            wallet_address: self.wallet_address.clone(),
            last_reading: self.last_reading.clone(),
        }
    }
    
    pub fn generate_reading(&mut self) -> MeterReading {
        let mut rng = rand::thread_rng();
        let hour = Utc::now().hour() as i32;
        
        // Solar generation based on time of day
        let solar_factor = if hour >= 6 && hour <= 18 {
            let noon_distance = (hour - 12).abs() as f64;
            1.0 - (noon_distance / 6.0) * 0.8
        } else {
            0.0
        };
        
        let energy_generated = if self.solar_capacity > 0.0 {
            self.solar_capacity * solar_factor * rng.gen_range(0.1..0.3) * 0.25 // 15-min interval
        } else {
            0.0
        };
        
        // Consumption with time-of-day pattern
        let consumption_factor = if hour >= 18 && hour <= 22 {
            1.5 // Evening peak
        } else if hour >= 6 && hour <= 9 {
            1.2 // Morning peak
        } else if hour >= 0 && hour <= 5 {
            0.5 // Night low
        } else {
            1.0
        };
        
        let energy_consumed = rng.gen_range(0.3..0.8) * consumption_factor * 0.25;
        
        let surplus = (energy_generated - energy_consumed).max(0.0);
        let deficit = (energy_consumed - energy_generated).max(0.0);
        
        // Update battery
        if self.battery_capacity > 0.0 {
            if surplus > 0.0 {
                self.battery_level = (self.battery_level + surplus / self.battery_capacity * 100.0).min(100.0);
            } else if deficit > 0.0 {
                self.battery_level = (self.battery_level - deficit / self.battery_capacity * 100.0).max(0.0);
            }
        }
        
        // Update totals
        self.total_energy_generated += energy_generated;
        self.total_energy_consumed += energy_consumed;
        
        let reading = MeterReading {
            timestamp: Utc::now().to_rfc3339(),
            energy_generated: round_to(energy_generated, 4),
            energy_consumed: round_to(energy_consumed, 4),
            surplus_energy: round_to(surplus, 4),
            deficit_energy: round_to(deficit, 4),
            battery_level_pct: round_to(self.battery_level, 1),
            voltage: round_to(230.0 + rng.gen_range(-2.0..2.0), 1),
            current: round_to((energy_consumed * 1000.0 / 230.0) + rng.gen_range(0.0..0.5), 2),
            frequency: round_to(50.0 + rng.gen_range(-0.01..0.01), 3),
            power_factor: round_to(0.95 + rng.gen_range(-0.02..0.02), 3),
            temperature: round_to(25.0 + rng.gen_range(-2.0..5.0), 1),
        };
        
        self.last_reading = Some(reading.clone());
        reading
    }
}

use chrono::Timelike;

fn round_to(value: f64, decimals: i32) -> f64 {
    let factor = 10_f64.powi(decimals);
    (value * factor).round() / factor
}

/// Zone state
#[derive(Debug, Clone)]
pub struct ZoneState {
    pub zone_id: i32,
    pub centroid_lat: f64,
    pub centroid_lon: f64,
    pub transformer_name: String,
    pub meter_ids: Vec<String>,
}

/// Application state shared across handlers
pub struct AppState {
    pub meters: RwLock<HashMap<String, MeterState>>,
    pub zones: RwLock<HashMap<i32, ZoneState>>,
    pub is_running: RwLock<bool>,
    pub is_paused: RwLock<bool>,
    pub tick_count: RwLock<u64>,
    pub start_time: RwLock<Option<DateTime<Utc>>>,
    pub current_sim_time: RwLock<Option<DateTime<Utc>>>,
    pub parameters: RwLock<SimulationParameters>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            meters: RwLock::new(HashMap::new()),
            zones: RwLock::new(HashMap::new()),
            is_running: RwLock::new(false),
            is_paused: RwLock::new(false),
            tick_count: RwLock::new(0),
            start_time: RwLock::new(None),
            current_sim_time: RwLock::new(None),
            parameters: RwLock::new(SimulationParameters::default()),
        }
    }
    
    /// Initialize with default meters
    pub fn init_default_meters(&self) {
        let mut meters = self.meters.write().unwrap();
        let mut zones = self.zones.write().unwrap();
        
        // Create 3 zones
        for i in 1..=3 {
            let zone = ZoneState {
                zone_id: i,
                centroid_lat: 13.75 + (i as f64) * 0.01,
                centroid_lon: 100.50 + (i as f64) * 0.01,
                transformer_name: format!("Transformer_{}", i),
                meter_ids: Vec::new(),
            };
            zones.insert(i, zone);
        }
        
        // Create default meters
        let meter_types = vec![
            ("Solar_Prosumer", 1),
            ("Solar_Prosumer", 1),
            ("Hybrid_Prosumer", 2),
            ("Grid_Consumer", 2),
            ("Grid_Consumer", 3),
            ("Battery_Storage", 3),
        ];
        
        for (i, (mtype, zone_id)) in meter_types.iter().enumerate() {
            let req = MeterRequest {
                meter_type: mtype.to_string(),
                location: format!("Zone_{}_Building_{}", zone_id, i + 1),
                solar_capacity: 5.0,
                battery_capacity: 10.0,
                trading_preference: "Moderate".to_string(),
                latitude: Some(13.75 + (*zone_id as f64) * 0.01 + (i as f64) * 0.001),
                longitude: Some(100.50 + (*zone_id as f64) * 0.01 + (i as f64) * 0.001),
                wallet_address: Some(format!("0x{:0>40}", i)),
                meter_id: Some(format!("meter-{:03}", i + 1)),
            };
            
            let mut meter = MeterState::new(&req);
            meter.zone_id = Some(*zone_id);
            
            // Add to zone
            if let Some(zone) = zones.get_mut(zone_id) {
                zone.meter_ids.push(meter.meter_id.clone());
            }
            
            meters.insert(meter.meter_id.clone(), meter);
        }
    }
    
    /// Get zone info
    pub fn get_zone_info(&self, zone_id: i32) -> Option<ZoneInfo> {
        let zones = self.zones.read().unwrap();
        let meters = self.meters.read().unwrap();
        
        zones.get(&zone_id).map(|z| {
            ZoneInfo {
                zone_id: z.zone_id,
                centroid_lat: z.centroid_lat,
                centroid_lon: z.centroid_lon,
                meter_count: z.meter_ids.len() as i32,
                transformer_name: z.transformer_name.clone(),
            }
        })
    }
    
    /// Calculate wheeling charge
    pub fn calculate_wheeling_charge(&self, from_zone: i32, to_zone: i32, amount: f64) -> f64 {
        if from_zone == to_zone {
            amount * 0.01 // 1% for same zone
        } else {
            amount * 0.05 // 5% for cross-zone
        }
    }
    
    /// Calculate loss factor
    pub fn calculate_loss_factor(&self, from_zone: i32, to_zone: i32) -> f64 {
        if from_zone == to_zone {
            0.01 // 1% loss same zone
        } else {
            0.03 // 3% loss cross-zone
        }
    }
}

impl Default for AppState {
    fn default() -> Self {
        Self::new()
    }
}
