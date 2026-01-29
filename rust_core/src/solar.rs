//! Solar generation calculator

use pyo3::prelude::*;
use rand::Rng;

#[pyclass]
#[derive(Debug, Clone)]
pub struct SolarCalculator {
    panel_efficiency: f64,
    temp_coefficient: f64,
}

#[pymethods]
impl SolarCalculator {
    #[new]
    #[pyo3(signature = (panel_efficiency = 0.18, temp_coefficient = 0.004))]
    pub fn new(panel_efficiency: f64, temp_coefficient: f64) -> Self {
        Self { panel_efficiency, temp_coefficient }
    }

    /// Calculate solar generation (kW) for given parameters
    #[pyo3(signature = (capacity_kw, hour, irradiance_factor, temperature_c, weather = "Clear"))]
    pub fn calculate(&self, capacity_kw: f64, hour: i32, irradiance_factor: f64, temperature_c: f64, weather: &str) -> f64 {
        if hour < 6 || hour >= 18 {
            return 0.0;
        }

        let hour_angle = ((hour as f64 - 6.0) / 12.0) * std::f64::consts::PI;
        let time_factor = hour_angle.sin().max(0.0);
        let temp_derate = (1.0 - self.temp_coefficient * (temperature_c - 25.0).max(0.0)).max(0.5);
        
        let weather_factor = match weather {
            "Clear" | "Sunny" => 1.0,
            "PartlyCloudy" => 0.7,
            "Cloudy" => 0.3,
            "Rainy" => 0.1,
            "Stormy" => 0.05,
            _ => 0.8,
        };

        let mut rng = rand::thread_rng();
        let noise = 1.0 + rng.gen_range(-0.02..0.02);

        (capacity_kw * time_factor * irradiance_factor * temp_derate * weather_factor * noise).max(0.0)
    }

    /// Calculate with EMA smoothing
    pub fn calculate_smooth(&self, current_value: f64, target_value: f64, alpha: f64) -> f64 {
        alpha * target_value + (1.0 - alpha) * current_value
    }

    fn __repr__(&self) -> String {
        format!("SolarCalculator(efficiency={:.2}, temp_coef={:.4})", self.panel_efficiency, self.temp_coefficient)
    }
}
