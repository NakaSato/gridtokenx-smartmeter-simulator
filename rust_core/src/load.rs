//! Load profile calculator

use pyo3::prelude::*;
use rand::Rng;

#[pyclass]
#[derive(Debug, Clone)]
pub struct LoadCalculator {
    base_load_kw: f64,
    profile_type: String,
    variation: f64,
}

#[pymethods]
impl LoadCalculator {
    #[new]
    #[pyo3(signature = (base_load_kw = 1.0, profile_type = "Residential", variation = 0.1))]
    pub fn new(base_load_kw: f64, profile_type: &str, variation: f64) -> Self {
        Self { base_load_kw, profile_type: profile_type.to_string(), variation }
    }

    /// Calculate consumption (kW) for given hour
    pub fn calculate(&self, hour: i32, temperature_c: f64, is_weekend: bool) -> f64 {
        let profile_factor = self.get_profile_factor(hour as u32, is_weekend);
        
        let temp_factor = if temperature_c < 20.0 {
            1.0 + (20.0 - temperature_c) * 0.03
        } else if temperature_c > 26.0 {
            1.0 + (temperature_c - 26.0) * 0.05
        } else {
            1.0
        };

        let mut rng = rand::thread_rng();
        let noise = 1.0 + rng.gen_range(-self.variation..self.variation);

        self.base_load_kw * profile_factor * temp_factor * noise
    }

    /// Calculate with EMA smoothing
    pub fn calculate_smooth(&self, current_value: f64, target_value: f64, alpha: f64) -> f64 {
        alpha * target_value + (1.0 - alpha) * current_value
    }

    fn get_profile_factor(&self, hour: u32, is_weekend: bool) -> f64 {
        match self.profile_type.as_str() {
            "Residential" => self.residential(hour, is_weekend),
            "Commercial" => self.commercial(hour, is_weekend),
            "Industrial" => 0.95,
            "Hospital" => self.hospital(hour),
            "University" => self.university(hour, is_weekend),
            _ => 1.0,
        }
    }

    fn residential(&self, hour: u32, is_weekend: bool) -> f64 {
        let base = match hour {
            0..=5 => 0.3,
            6..=8 => 0.8,
            9..=11 => 0.5,
            12..=13 => 0.6,
            14..=17 => 0.4,
            18..=21 => 1.0,
            22..=23 => 0.6,
            _ => 0.5,
        };
        if is_weekend && (9..=17).contains(&hour) { base * 1.5 }
        else if is_weekend { base * 1.1 }
        else { base }
    }

    fn commercial(&self, hour: u32, is_weekend: bool) -> f64 {
        if is_weekend { return 0.2; }
        match hour {
            7..=8 => 0.6,
            9..=17 => 1.0,
            18..=19 => 0.5,
            _ => 0.2,
        }
    }

    fn hospital(&self, hour: u32) -> f64 {
        match hour {
            0..=5 => 0.6,
            9..=17 => 1.0,
            _ => 0.8,
        }
    }

    fn university(&self, hour: u32, is_weekend: bool) -> f64 {
        if is_weekend { return 0.15; }
        match hour {
            7..=8 => 0.5,
            9..=16 => 1.0,
            17..=20 => 0.4,
            _ => 0.1,
        }
    }

    fn __repr__(&self) -> String {
        format!("LoadCalculator(base={:.2}kW, type='{}')", self.base_load_kw, self.profile_type)
    }
}
