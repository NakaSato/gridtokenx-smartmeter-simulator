//! Power quality and THD (Total Harmonic Distortion) calculations

use pyo3::prelude::*;
use rand::Rng;
use std::collections::HashMap;

/// Power quality calculator for THD estimation
#[pyclass]
#[derive(Debug, Clone)]
pub struct PowerQuality {
    base_thd_v: f64,
    base_thd_i: f64,
}

#[pymethods]
impl PowerQuality {
    #[new]
    #[pyo3(signature = (base_thd_v = 1.5, base_thd_i = 5.0))]
    pub fn new(base_thd_v: f64, base_thd_i: f64) -> Self {
        PowerQuality { base_thd_v, base_thd_i }
    }
    
    /// Estimate THD for a bus based on connected loads
    /// Returns (thd_voltage_percent, thd_current_percent)
    #[pyo3(signature = (has_ev_charger = false, has_solar_inverter = false, ev_power_kw = 0.0, solar_power_kw = 0.0))]
    pub fn estimate_thd(
        &self,
        has_ev_charger: bool,
        has_solar_inverter: bool,
        ev_power_kw: f64,
        solar_power_kw: f64,
    ) -> (f64, f64) {
        let mut rng = rand::thread_rng();
        let mut thd_v = self.base_thd_v;
        let mut thd_i = self.base_thd_i;
        
        // EV Charger contribution
        if has_ev_charger && ev_power_kw > 0.0 {
            let ev_thd: f64 = 8.0 + rng.gen::<f64>() * 4.0 - 2.0;
            thd_i += ev_thd * (ev_power_kw / 50.0);
            thd_v += 0.5 * (ev_power_kw / 100.0);
        }
        
        // Solar inverter contribution
        if has_solar_inverter && solar_power_kw > 0.0 {
            let inv_thd: f64 = 3.0 + rng.gen::<f64>() * 2.0 - 1.0;
            thd_i += inv_thd * (solar_power_kw / 10.0);
            thd_v += 0.2 * (solar_power_kw / 50.0);
        }
        
        // Add noise
        thd_v = (thd_v + rng.gen::<f64>() * 0.6 - 0.3).max(0.5).min(15.0);
        thd_i = (thd_i + rng.gen::<f64>() * 2.0 - 1.0).max(1.0).min(50.0);
        
        (round_to(thd_v, 2), round_to(thd_i, 2))
    }
    
    /// Get power quality assessment string
    pub fn get_assessment(&self, thd_v: f64, thd_i: f64) -> String {
        if thd_v <= 3.0 && thd_i <= 8.0 {
            "Excellent".to_string()
        } else if thd_v <= 5.0 && thd_i <= 15.0 {
            "Good".to_string()
        } else if thd_v <= 8.0 && thd_i <= 25.0 {
            "Acceptable".to_string()
        } else if thd_v <= 12.0 && thd_i <= 40.0 {
            "Poor".to_string()
        } else {
            "Critical".to_string()
        }
    }
    
    /// Calculate harmonic spectrum from THD
    pub fn harmonic_spectrum(&self, thd_percent: f64, fundamental: f64) -> HashMap<i32, f64> {
        let mut spectrum = HashMap::new();
        
        if thd_percent <= 0.0 {
            return spectrum;
        }
        
        // Typical harmonic ratios for power electronics
        let ratios: [(i32, f64); 5] = [
            (3, 0.1),   // Triplen
            (5, 0.4),   // Dominant 6-pulse
            (7, 0.25),
            (11, 0.15),
            (13, 0.10),
        ];
        
        let total_ratio: f64 = ratios.iter().map(|(_, r)| r).sum();
        
        for (order, ratio) in ratios.iter() {
            let amplitude = fundamental * (thd_percent / 100.0) * (ratio / total_ratio);
            spectrum.insert(*order, round_to(amplitude, 4));
        }
        
        spectrum
    }
}

fn round_to(value: f64, decimals: i32) -> f64 {
    let factor = 10_f64.powi(decimals);
    (value * factor).round() / factor
}
