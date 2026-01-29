//! Battery state management

use pyo3::prelude::*;

#[pyclass(get_all, set_all)]
#[derive(Debug, Clone)]
pub struct BatteryState {
    pub capacity_kwh: f64,
    pub current_kwh: f64,
    pub max_charge_rate_kw: f64,
    pub max_discharge_rate_kw: f64,
    pub efficiency: f64,
    pub min_soc: f64,
    pub max_soc: f64,
}

#[pymethods]
impl BatteryState {
    #[new]
    #[pyo3(signature = (capacity_kwh, max_charge_rate_kw = 5.0, max_discharge_rate_kw = 5.0, efficiency = 0.95, initial_soc = 0.5))]
    pub fn new(capacity_kwh: f64, max_charge_rate_kw: f64, max_discharge_rate_kw: f64, efficiency: f64, initial_soc: f64) -> Self {
        Self {
            capacity_kwh,
            current_kwh: capacity_kwh * initial_soc,
            max_charge_rate_kw,
            max_discharge_rate_kw,
            efficiency,
            min_soc: 0.1,
            max_soc: 0.95,
        }
    }

    /// Get state of charge (0-1)
    pub fn soc(&self) -> f64 {
        if self.capacity_kwh <= 0.0 { return 0.0; }
        (self.current_kwh / self.capacity_kwh).clamp(0.0, 1.0)
    }

    /// Get level as percentage
    pub fn level_pct(&self) -> f64 {
        self.soc() * 100.0
    }

    /// Charge battery, returns actual energy stored (kWh)
    pub fn charge(&mut self, energy_kwh: f64, duration_hours: f64) -> f64 {
        let max_energy = self.max_charge_rate_kw * duration_hours;
        let energy_to_charge = energy_kwh.min(max_energy);
        let max_storable = (self.max_soc * self.capacity_kwh) - self.current_kwh;
        let actual_stored = (energy_to_charge * self.efficiency).min(max_storable.max(0.0));
        self.current_kwh += actual_stored;
        actual_stored
    }

    /// Discharge battery, returns actual energy delivered (kWh)
    pub fn discharge(&mut self, energy_kwh: f64, duration_hours: f64) -> f64 {
        let max_energy = self.max_discharge_rate_kw * duration_hours;
        let energy_requested = energy_kwh.min(max_energy);
        let min_level = self.min_soc * self.capacity_kwh;
        let available = (self.current_kwh - min_level).max(0.0);
        let actual_discharge = energy_requested.min(available);
        self.current_kwh -= actual_discharge;
        actual_discharge * self.efficiency
    }

    fn __repr__(&self) -> String {
        format!("BatteryState(capacity={:.1}kWh, SOC={:.1}%)", self.capacity_kwh, self.level_pct())
    }
}
