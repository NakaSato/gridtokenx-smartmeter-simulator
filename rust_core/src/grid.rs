//! Grid physics calculations and zone aggregation

use pyo3::prelude::*;
use std::collections::HashMap;
use crate::models::ZoneState;

#[pyclass]
#[derive(Debug, Clone)]
pub struct GridPhysics {
    nominal_voltage: f64,
    nominal_frequency: f64,
    ema_alpha: f64,
}

#[pymethods]
impl GridPhysics {
    #[new]
    #[pyo3(signature = (nominal_voltage = 230.0, nominal_frequency = 50.0, ema_alpha = 0.05))]
    pub fn new(nominal_voltage: f64, nominal_frequency: f64, ema_alpha: f64) -> Self {
        Self { nominal_voltage, nominal_frequency, ema_alpha }
    }

    /// Apply EMA smoothing
    pub fn smooth_ema(&self, current: f64, target: f64) -> f64 {
        self.ema_alpha * target + (1.0 - self.ema_alpha) * current
    }

    /// Calculate voltage at a point
    pub fn calculate_voltage(&self, base_voltage: f64, load_kw: f64, generation_kw: f64, impedance_pu: f64) -> f64 {
        let net_load = load_kw - generation_kw;
        let voltage_drop_pu = net_load * impedance_pu / 100.0;
        let voltage = base_voltage * (1.0 - voltage_drop_pu);
        voltage.clamp(self.nominal_voltage * 0.9, self.nominal_voltage * 1.1)
    }

    /// Calculate frequency deviation
    pub fn calculate_frequency(&self, base_freq: f64, total_gen_mw: f64, total_load_mw: f64) -> f64 {
        let imbalance_pct = if total_load_mw > 0.0 {
            (total_gen_mw - total_load_mw) / total_load_mw
        } else { 0.0 };
        let freq_deviation = imbalance_pct * 0.5;
        (base_freq + freq_deviation).clamp(self.nominal_frequency - 0.5, self.nominal_frequency + 0.5)
    }

    /// Calculate power factor
    pub fn calculate_power_factor(&self, active_kw: f64, reactive_kvar: f64) -> f64 {
        if active_kw <= 0.0 { return 0.95; }
        let apparent = (active_kw * active_kw + reactive_kvar * reactive_kvar).sqrt();
        if apparent > 0.0 { (active_kw / apparent).clamp(0.7, 1.0) } else { 0.95 }
    }

    /// Calculate current from power
    pub fn calculate_current(&self, power_kw: f64, voltage: f64, power_factor: f64) -> f64 {
        if voltage <= 0.0 || power_factor <= 0.0 { return 0.0; }
        power_kw * 1000.0 / (voltage * power_factor)
    }

    fn __repr__(&self) -> String {
        format!("GridPhysics(V_nom={:.1}V, f_nom={:.1}Hz)", self.nominal_voltage, self.nominal_frequency)
    }
}

struct ZoneData {
    transformer_name: String,
    meters: Vec<String>,
    total_load_kw: f64,
    total_gen_kw: f64,
    voltages: Vec<f64>,
    capacity_kw: f64,
}

#[pyclass]
pub struct ZoneAggregator {
    zones: HashMap<i32, ZoneData>,
}

#[pymethods]
impl ZoneAggregator {
    #[new]
    fn new() -> Self {
        Self { zones: HashMap::new() }
    }

    fn add_zone(&mut self, zone_id: i32, transformer_name: String, capacity_kw: f64) {
        self.zones.insert(zone_id, ZoneData {
            transformer_name,
            meters: Vec::new(),
            total_load_kw: 0.0,
            total_gen_kw: 0.0,
            voltages: Vec::new(),
            capacity_kw,
        });
    }

    fn add_meter_to_zone(&mut self, zone_id: i32, meter_id: String) {
        if let Some(zone) = self.zones.get_mut(&zone_id) {
            zone.meters.push(meter_id);
        }
    }

    fn update_zone(&mut self, zone_id: i32, load_kw: f64, gen_kw: f64, voltage_pu: f64) {
        if let Some(zone) = self.zones.get_mut(&zone_id) {
            zone.total_load_kw += load_kw;
            zone.total_gen_kw += gen_kw;
            zone.voltages.push(voltage_pu);
        }
    }

    fn reset_zones(&mut self) {
        for zone in self.zones.values_mut() {
            zone.total_load_kw = 0.0;
            zone.total_gen_kw = 0.0;
            zone.voltages.clear();
        }
    }

    fn get_zone_state(&self, zone_id: i32) -> Option<ZoneState> {
        let zone = self.zones.get(&zone_id)?;
        
        if zone.voltages.is_empty() {
            return Some(ZoneState::create(zone_id, zone.transformer_name.clone()));
        }

        let avg_v = zone.voltages.iter().sum::<f64>() / zone.voltages.len() as f64;
        let min_v = zone.voltages.iter().cloned().fold(f64::INFINITY, f64::min);
        let max_v = zone.voltages.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        
        let has_voltage_violation = min_v < 0.95 || max_v > 1.05;
        let has_overload = zone.total_load_kw > zone.capacity_kw * 0.8;

        let mut state = ZoneState {
            zone_id,
            transformer_name: zone.transformer_name.clone(),
            meter_count: zone.meters.len(),
            avg_voltage_pu: avg_v,
            min_voltage_pu: min_v,
            max_voltage_pu: max_v,
            total_load_kw: zone.total_load_kw,
            total_generation_kw: zone.total_gen_kw,
            net_power_kw: zone.total_gen_kw - zone.total_load_kw,
            has_voltage_violation,
            has_overload,
            health_score: 100.0,
        };
        state.compute_health_score();
        Some(state)
    }

    fn zone_ids(&self) -> Vec<i32> {
        self.zones.keys().cloned().collect()
    }

    fn __repr__(&self) -> String {
        format!("ZoneAggregator(zones={})", self.zones.len())
    }
}
