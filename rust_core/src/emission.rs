//! Carbon emission calculator

use pyo3::prelude::*;

#[pyclass]
#[derive(Debug, Clone)]
pub struct EmissionCalculator {
    grid_factor: f64,    // kgCO2/kWh for grid
    solar_factor: f64,   // kgCO2/kWh for solar (lifecycle)
}

#[pymethods]
impl EmissionCalculator {
    #[new]
    #[pyo3(signature = (grid_factor = 0.5, solar_factor = 0.05))]
    pub fn new(grid_factor: f64, solar_factor: f64) -> Self {
        Self { grid_factor, solar_factor }
    }

    /// Calculate net emissions (positive = emissions, negative = avoided)
    pub fn calculate_net_emission(&self, energy_consumed_kwh: f64, energy_generated_kwh: f64, energy_from_grid_kwh: f64) -> f64 {
        let grid_emissions = energy_from_grid_kwh * self.grid_factor;
        let solar_offset = energy_generated_kwh.min(energy_consumed_kwh) * (self.grid_factor - self.solar_factor);
        grid_emissions - solar_offset
    }

    /// Check if generation is REC eligible
    pub fn is_rec_eligible(&self, surplus_kwh: f64) -> bool {
        surplus_kwh > 0.0
    }

    fn __repr__(&self) -> String {
        format!("EmissionCalculator(grid={:.2}, solar={:.2})", self.grid_factor, self.solar_factor)
    }
}
