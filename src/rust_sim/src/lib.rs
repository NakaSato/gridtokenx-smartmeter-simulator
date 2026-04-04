use pyo3::prelude::*;
use rand::Rng;
use rand_distr::{Distribution, Normal};
use std::collections::HashMap;

/// Meter configuration from Python
#[derive(Debug, Clone)]
#[pyclass]
pub struct MeterConfig {
    #[pyo3(get, set)]
    pub meter_id: String,
    #[pyo3(get, set)]
    pub meter_type: String,
    #[pyo3(get, set)]
    pub has_solar: bool,
    #[pyo3(get, set)]
    pub has_battery: bool,
    #[pyo3(get, set)]
    pub solar_capacity: f64,
    #[pyo3(get, set)]
    pub battery_capacity: f64,
    #[pyo3(get, set)]
    pub base_consumption: f64,
    #[pyo3(get, set)]
    pub panel_efficiency: f64,
    #[pyo3(get, set)]
    pub current_battery_level: f64,
    #[pyo3(get, set)]
    pub price_elasticity: f64,
    #[pyo3(get, set)]
    pub accuracy_class: f64,
}

#[pymethods]
impl MeterConfig {
    #[new]
    #[pyo3(signature = (
        meter_id,
        meter_type,
        has_solar = false,
        has_battery = false,
        solar_capacity = 5.0,
        battery_capacity = 10.0,
        base_consumption = 1.0,
        panel_efficiency = 0.18,
        current_battery_level = 0.0,
        price_elasticity = 0.15,
        accuracy_class = 2.0
    ))]
    fn new(
        meter_id: String,
        meter_type: String,
        has_solar: bool,
        has_battery: bool,
        solar_capacity: f64,
        battery_capacity: f64,
        base_consumption: f64,
        panel_efficiency: f64,
        current_battery_level: f64,
        price_elasticity: f64,
        accuracy_class: f64,
    ) -> Self {
        Self {
            meter_id,
            meter_type,
            has_solar,
            has_battery,
            solar_capacity,
            battery_capacity,
            base_consumption,
            panel_efficiency,
            current_battery_level,
            price_elasticity,
            accuracy_class,
        }
    }
}

/// Energy reading result
#[derive(Debug, Clone)]
#[pyclass]
pub struct EnergyReading {
    #[pyo3(get)]
    pub meter_id: String,
    #[pyo3(get)]
    pub energy_generated_kwh: f64,
    #[pyo3(get)]
    pub energy_consumed_kwh: f64,
    #[pyo3(get)]
    pub surplus_energy: f64,
    #[pyo3(get)]
    pub deficit_energy: f64,
    #[pyo3(get)]
    pub battery_level: f64,
    #[pyo3(get)]
    pub voltage: f64,
    #[pyo3(get)]
    pub current: f64,
    #[pyo3(get)]
    pub frequency: f64,
    #[pyo3(get)]
    pub power_factor: f64,
    #[pyo3(get)]
    pub reactive_power: f64,
}

#[pymethods]
impl EnergyReading {
    fn to_dict(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let dict = pyo3::types::PyDict::new(py);
            dict.set_item("meter_id", &self.meter_id)?;
            dict.set_item("energy_generated_kwh", self.energy_generated_kwh)?;
            dict.set_item("energy_consumed_kwh", self.energy_consumed_kwh)?;
            dict.set_item("surplus_energy", self.surplus_energy)?;
            dict.set_item("deficit_energy", self.deficit_energy)?;
            dict.set_item("battery_level", self.battery_level)?;
            dict.set_item("voltage", self.voltage)?;
            dict.set_item("current", self.current)?;
            dict.set_item("frequency", self.frequency)?;
            dict.set_item("power_factor", self.power_factor)?;
            dict.set_item("reactive_power", self.reactive_power)?;
            Ok(dict.into())
        })
    }
}

/// Calculate solar generation for a single meter
fn calculate_solar_generation(
    solar_capacity: f64,
    panel_efficiency: f64,
    hour: f64,
    weather_factor: f64,
    last_gen_noise: f64,
    rng: &mut impl Rng,
) -> (f64, f64) {
    // Check if solar is active (6 AM - 6 PM)
    if hour < 6.0 || hour > 18.0 {
        return (0.0, last_gen_noise);
    }

    // Solar curve: sin^2 pattern
    let time_factor = (std::f64::consts::PI * (hour - 6.0) / 12.0).sin().powi(2);
    
    // Base generation
    let base_gen = solar_capacity * time_factor * panel_efficiency * 2.0;
    
    // Autocorrelated noise (Brownian motion)
    if let Ok(normal) = Normal::new(0.0, base_gen * 0.02) {
        let innovation = normal.sample(rng);
        let new_noise = 0.8 * last_gen_noise + innovation;
        let generation = base_gen * weather_factor + new_noise;
        return (generation.max(0.0), new_noise);
    }
    
    (0.0, last_gen_noise)
}

/// Calculate consumption for a single meter
fn calculate_consumption(
    meter_type: &str,
    base_consumption: f64,
    price_elasticity: f64,
    hour: f64,
    weekday: bool,
    is_peak: bool,
    meter_id: &str,
    last_cons_noise: f64,
    rng: &mut impl Rng,
) -> (f64, f64) {
    let meter_offset = (meter_id.bytes().fold(0u64, |acc, b| acc.wrapping_add(b as u64)) % 100) as f64 / 100.0;
    
    let mut factor = 1.0;
    
    match meter_type {
        "Residential" | "Solar_Prosumer" | "Hybrid_Prosumer" => {
            // Residential Profile: Morning and Evening Peaks
            let m_peak_time = 7.5 + meter_offset * 1.5;
            let e_peak_time = 18.5 + meter_offset * 2.0;
            
            let m_peak = 0.8 * (-((hour - m_peak_time).powi(2)) / (2.0 * 1.2f64.powi(2))).exp();
            let e_peak = 1.5 * (-((hour - e_peak_time).powi(2)) / (2.0 * 2.5f64.powi(2))).exp();
            
            if !weekday {
                factor = 1.2 + m_peak * 0.5 + e_peak * 1.2 + 0.3 * (std::f64::consts::PI * hour / 24.0).sin();
            } else {
                factor = 0.6 + m_peak + e_peak;
            }
        }
        "Commercial" => {
            if weekday {
                let mut business_hours = if hour >= 9.0 && hour <= 17.0 { 1.8 } else { 0.4 };
                
                if hour >= 7.0 && hour < 9.0 {
                    business_hours = 0.4 + (1.4 * (hour - 7.0) / 2.0);
                } else if hour > 17.0 && hour <= 19.0 {
                    business_hours = 1.8 - (1.4 * (hour - 17.0) / 2.0);
                }
                
                factor = business_hours + meter_offset * 0.2;
            } else {
                factor = 0.3 + meter_offset * 0.1;
            }
        }
        "EV_Charger" => {
            factor = 0.05 + meter_offset * 0.05;
        }
        _ => {
            factor = 1.0 + 0.2 * (2.0 * std::f64::consts::PI * hour / 24.0).sin() + meter_offset;
        }
    }
    
    let mut consumption = base_consumption * factor;
    
    // Price elasticity response
    if is_peak {
        let response = price_elasticity * rng.gen_range(0.8..1.2);
        consumption *= 1.0 - response;
    }
    
    // Autocorrelated noise
    if let Ok(normal) = Normal::new(0.0, consumption * 0.015) {
        let innovation = normal.sample(rng);
        let new_noise = 0.85 * last_cons_noise + innovation;
        return ((consumption + new_noise).max(0.1), new_noise);
    }
    
    (consumption.max(0.1), last_cons_noise)
}

/// Apply measurement noise based on accuracy class
fn apply_noise(value: f64, accuracy_class: f64, multiplier: f64, rng: &mut impl Rng) -> f64 {
    if value == 0.0 {
        return 0.0;
    }
    let sigma = (accuracy_class / 300.0) * value.abs() * multiplier;
    if let Ok(normal) = Normal::new(value, sigma) {
        return normal.sample(rng);
    }
    value
}

/// Generate readings for a batch of meters
#[pyfunction]
#[pyo3(signature = (meters, hour, weekday, weather_factor, is_peak, interval_seconds = 900.0))]
fn generate_readings(
    py: Python,
    meters: Vec<Py<MeterConfig>>,
    hour: f64,
    weekday: bool,
    weather_factor: f64,
    is_peak: bool,
    interval_seconds: f64,
) -> PyResult<Vec<EnergyReading>> {
    use rand::rngs::StdRng;
    use rand::SeedableRng;
    
    let mut rng = StdRng::from_entropy();
    let time_factor = interval_seconds / 3600.0;
    
    let mut readings = Vec::with_capacity(meters.len());
    
    for meter_py in meters {
        let meter = meter_py.borrow(py);
        
        let mut _last_gen_noise = 0.0;
        let mut _last_cons_noise = 0.0;
        
        // Solar generation
        let (energy_generated, new_gen_noise) = if meter.has_solar {
            calculate_solar_generation(
                meter.solar_capacity,
                meter.panel_efficiency,
                hour,
                weather_factor,
                _last_gen_noise,
                &mut rng,
            )
        } else {
            (0.0, _last_gen_noise)
        };
        _last_gen_noise = new_gen_noise;
        
        // Consumption
        let (energy_consumed, new_cons_noise) = calculate_consumption(
            &meter.meter_type,
            meter.base_consumption,
            meter.price_elasticity,
            hour,
            weekday,
            is_peak,
            &meter.meter_id,
            _last_cons_noise,
            &mut rng,
        );
        _last_cons_noise = new_cons_noise;
        
        // Scale to interval energy
        let energy_gen_kwh = energy_generated * time_factor;
        let energy_cons_kwh = energy_consumed * time_factor;
        
        // Net energy
        let net_energy = energy_gen_kwh - energy_cons_kwh;
        let surplus = net_energy.max(0.0);
        let deficit = (-net_energy).max(0.0);
        
        // Battery logic (simplified)
        let mut battery_level = meter.current_battery_level;
        if meter.has_battery {
            let net = energy_generated - energy_consumed;
            if net > 0.0 {
                let charge = net.min(meter.battery_capacity - battery_level);
                battery_level += charge;
            } else {
                let discharge = net.abs().min(battery_level);
                battery_level -= discharge;
            }
            battery_level = battery_level.max(0.0).min(meter.battery_capacity);
        }
        
        // Electrical parameters with noise
        let voltage = apply_noise(240.0, meter.accuracy_class, 1.0, &mut rng);
        let apparent_power = (energy_consumed.powi(2) + energy_generated.powi(2)).sqrt();
        let current = if voltage > 0.0 {
            (apparent_power * 1000.0) / voltage
        } else {
            0.0
        };
        let current = apply_noise(current, meter.accuracy_class, 1.0, &mut rng);
        
        let power_factor = apply_noise(0.95, meter.accuracy_class, 0.5, &mut rng).min(1.0);
        let frequency = apply_noise(50.0, meter.accuracy_class, 0.1, &mut rng);
        
        // Reactive power
        let p_eff = energy_consumed - energy_generated;
        let q_factor = if power_factor > 0.0 {
            (1.0 - power_factor.powi(2)).sqrt() / power_factor
        } else {
            0.0
        };
        let reactive_power = p_eff * q_factor;
        
        readings.push(EnergyReading {
            meter_id: meter.meter_id.clone(),
            energy_generated_kwh: (energy_gen_kwh * 1_000_000.0).round() / 1_000_000.0,
            energy_consumed_kwh: (energy_cons_kwh * 1_000_000.0).round() / 1_000_000.0,
            surplus_energy: (surplus * 1_000_000.0).round() / 1_000_000.0,
            deficit_energy: (deficit * 1_000_000.0).round() / 1_000_000.0,
            battery_level: (battery_level * 10.0).round() / 10.0,
            voltage: (voltage * 100.0).round() / 100.0,
            current: (current * 1000.0).round() / 1000.0,
            frequency: (frequency * 100.0).round() / 100.0,
            power_factor: (power_factor * 100.0).round() / 100.0,
            reactive_power: (reactive_power * 1000.0).round() / 1000.0,
        });
    }
    
    Ok(readings)
}

// ============================================================================
// VPP Dispatch Structures (Phase 2)
// ============================================================================

/// DER Resource for VPP dispatch
#[derive(Debug, Clone)]
#[pyclass]
pub struct DERResource {
    #[pyo3(get, set)]
    pub meter_id: String,
    #[pyo3(get, set)]
    pub feeder_id: String,
    #[pyo3(get, set)]
    pub capacity_kw: f64,
    #[pyo3(get, set)]
    pub capacity_kwh: f64,
    #[pyo3(get, set)]
    pub current_soc_kwh: f64,
    #[pyo3(get, set)]
    pub max_charge_kw: f64,
    #[pyo3(get, set)]
    pub max_discharge_kw: f64,
    #[pyo3(get, set)]
    pub is_controllable: bool,
    #[pyo3(get, set)]
    pub enabled: bool,
    #[pyo3(get, set)]
    pub reputation_score: f64,
    #[pyo3(get, set)]
    pub priority: u8,
    #[pyo3(get, set)]
    pub current_cons_kw: f64,
    #[pyo3(get, set)]
    pub current_gen_kw: f64,
}

#[pymethods]
impl DERResource {
    #[new]
    #[pyo3(signature = (
        meter_id,
        feeder_id = "default",
        capacity_kw = 10.0,
        capacity_kwh = 20.0,
        current_soc_kwh = 10.0,
        max_charge_kw = 5.0,
        max_discharge_kw = 5.0,
        is_controllable = true,
        enabled = true,
        reputation_score = 1.0,
        priority = 2,
        current_cons_kw = 0.0,
        current_gen_kw = 0.0
    ))]
    fn new(
        meter_id: String,
        feeder_id: &str,
        capacity_kw: f64,
        capacity_kwh: f64,
        current_soc_kwh: f64,
        max_charge_kw: f64,
        max_discharge_kw: f64,
        is_controllable: bool,
        enabled: bool,
        reputation_score: f64,
        priority: u8,
        current_cons_kw: f64,
        current_gen_kw: f64,
    ) -> Self {
        Self {
            meter_id,
            feeder_id: feeder_id.to_string(),
            capacity_kw,
            capacity_kwh,
            current_soc_kwh,
            max_charge_kw,
            max_discharge_kw,
            is_controllable,
            enabled,
            reputation_score,
            priority,
            current_cons_kw,
            current_gen_kw,
        }
    }

    #[getter]
    pub fn soc_percent(&self) -> f64 {
        if self.capacity_kwh <= 0.0 {
            return 0.0;
        }
        (self.current_soc_kwh / self.capacity_kwh) * 100.0
    }

    #[getter]
    pub fn max_flexibility_up_kw(&self) -> f64 {
        if !self.enabled || !self.is_controllable {
            return 0.0;
        }
        let energy_limited = self.current_soc_kwh / 0.25;
        self.max_discharge_kw.min(energy_limited)
    }

    #[getter]
    pub fn max_flexibility_down_kw(&self) -> f64 {
        if !self.enabled || !self.is_controllable {
            return 0.0;
        }
        let space_kwh = self.capacity_kwh - self.current_soc_kwh;
        let energy_limited = space_kwh / 0.25;
        self.max_charge_kw.min(energy_limited)
    }
}

/// Dispatch result from VPP optimization
#[derive(Debug, Clone)]
#[pyclass]
pub struct DispatchResult {
    #[pyo3(get)]
    pub dispatches: HashMap<String, f64>,
    #[pyo3(get)]
    pub carbon_saved_g: f64,
    #[pyo3(get)]
    pub cluster_health: f64,
    #[pyo3(get)]
    pub execution_time_us: u64,
}

#[pymethods]
impl DispatchResult {
    fn to_dict(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let dict = pyo3::types::PyDict::new(py);
            dict.set_item("dispatches", self.dispatches.clone())?;
            dict.set_item("carbon_saved_g", self.carbon_saved_g)?;
            dict.set_item("cluster_health", self.cluster_health)?;
            dict.set_item("execution_time_us", self.execution_time_us)?;
            Ok(dict.into())
        })
    }
}

/// VPP Dispatch Engine for optimized multi-objective dispatch
#[pyclass]
pub struct VPPDispatchEngine {
    seed: u64,
}

#[pymethods]
impl VPPDispatchEngine {
    #[new]
    fn new(seed: u64) -> Self {
        Self { seed }
    }

    /// Calculate AFRR (automatic Frequency Restoration Reserve) response
    /// 
    /// Args:
    ///     frequency_hz: Current grid frequency (nominal 50 Hz)
    ///     max_flexibility_up_kw: Maximum upward flexibility (discharge)
    ///     max_flexibility_down_kw: Maximum downward flexibility (charge)
    /// 
    /// Returns:
    ///     Required power adjustment in kW (positive=discharge, negative=charge)
    #[pyo3(text_signature = "(self, frequency_hz, max_flexibility_up_kw, max_flexibility_down_kw)")]
    fn calculate_afrr(
        &self,
        frequency_hz: f64,
        max_flexibility_up_kw: f64,
        max_flexibility_down_kw: f64,
    ) -> f64 {
        let deadband = 0.02; // Hz (20 mHz)
        let deviation = frequency_hz - 50.0;

        if deviation.abs() < deadband {
            return 0.0;
        }

        // Standard droop: 5% = 20 pu/pu gain
        // Scaled gain: 10 MW/Hz for simulation
        let gain = 10.0;
        let mut target = -deviation * gain;

        // Clip to cluster limits
        if target > 0.0 {
            target.min(max_flexibility_up_kw)
        } else {
            target.max(-max_flexibility_down_kw)
        }
    }

    /// Multi-objective dispatch: SOC balance (30%), Price (40%), Carbon (30%)
    /// 
    /// Args:
    ///     resources: List of DER resources to dispatch
    ///     target_kw: Total target power (positive=discharge, negative=charge)
    ///     nodal_prices: Nodal prices per meter_id
    ///     carbon_intensity: Grid carbon intensity (gCO2/kWh), optional
    ///     interval_hours: Dispatch interval in hours (default 0.25 = 15 min)
    /// 
    /// Returns:
    ///     DispatchResult with per-meter dispatches and carbon savings
    #[pyo3(signature = (resources, target_kw, nodal_prices, carbon_intensity=None, interval_hours=0.25))]
    fn dispatch(
        &self,
        resources: Vec<Py<DERResource>>,
        target_kw: f64,
        nodal_prices: HashMap<String, f64>,
        carbon_intensity: Option<f64>,
        interval_hours: f64,
    ) -> PyResult<DispatchResult> {
        if target_kw == 0.0 || resources.is_empty() {
            return Ok(DispatchResult {
                dispatches: HashMap::new(),
                carbon_saved_g: 0.0,
                cluster_health: 0.0,
                execution_time_us: 0,
            });
        }

        Python::with_gil(|py| {
            let mut weights = Vec::new();
            let mut total_weight = 0.0;
            let mut total_flex_up = 0.0;
            let mut total_flex_down = 0.0;
            let mut total_soc = 0.0;
            let mut total_rep = 0.0;

            // Calculate weights for each resource
            for resource_py in &resources {
                let r = resource_py.borrow(py);
                
                // 1. SOC Weight
                let soc_w = if target_kw > 0.0 {
                    r.soc_percent() / 100.0 // Prefer high SOC when discharging
                } else {
                    (100.0 - r.soc_percent()) / 100.0 // Prefer low SOC when charging
                };

                // 2. Price Weight
                let price = nodal_prices.get(&r.meter_id).copied().unwrap_or(0.25);
                let price_w = if target_kw > 0.0 {
                    price / 0.5 // Prefer high price when discharging
                } else {
                    1.0 - (price / 0.5) // Prefer low price when charging
                };

                // 3. Carbon Weight
                let c_intensity = carbon_intensity.unwrap_or(250.0);
                let carbon_w = if target_kw > 0.0 {
                    c_intensity / 500.0 // Prefer high intensity when discharging
                } else {
                    1.0 - (c_intensity / 500.0) // Prefer low intensity when charging
                };

                // Combined Weight: SOC (30%), Price (40%), Carbon (30%)
                let weight = (soc_w * 0.3 + price_w * 0.4 + carbon_w * 0.3) * r.reputation_score;
                total_weight += weight;
                total_flex_up += r.max_flexibility_up_kw();
                total_flex_down += r.max_flexibility_down_kw();
                total_soc += r.soc_percent();
                total_rep += r.reputation_score;

                weights.push((r.meter_id.clone(), weight, r.max_flexibility_up_kw(), r.max_flexibility_down_kw()));
            }

            // Normalize and allocate
            let mut dispatches = HashMap::new();
            
            if total_weight <= 0.0 {
                // Equal distribution fallback
                let equal = target_kw / resources.len() as f64;
                for resource_py in &resources {
                    let r = resource_py.borrow(py);
                    dispatches.insert(r.meter_id.clone(), equal);
                }
            } else {
                for (meter_id, weight, max_up, max_down) in weights {
                    let raw_dispatch = (weight / total_weight) * target_kw;
                    let dispatch = if target_kw > 0.0 {
                        raw_dispatch.min(max_up)
                    } else {
                        raw_dispatch.max(-max_down)
                    };
                    dispatches.insert(meter_id, dispatch);
                }
            }

            // Calculate carbon savings
            let carbon_saved = if target_kw > 0.0 && carbon_intensity.is_some() {
                target_kw * interval_hours * carbon_intensity.unwrap()
            } else {
                0.0
            };

            // Calculate cluster health (0-100)
            let n = resources.len() as f64;
            let avg_soc = total_soc / n;
            let avg_rep = total_rep / n;
            let cluster_health = ((avg_soc + avg_rep * 100.0) / 200.0) * 100.0;

            Ok(DispatchResult {
                dispatches,
                carbon_saved_g: carbon_saved,
                cluster_health,
                execution_time_us: 0, // Can't measure in this context
            })
        })
    }

    /// Batch dispatch multiple clusters simultaneously
    /// 
    /// Args:
    ///     clusters_data: List of (resources, target_kw, nodal_prices, carbon_intensity) tuples
    ///     interval_hours: Dispatch interval in hours
    /// 
    /// Returns:
    ///     List of DispatchResult, one per cluster
    fn batch_dispatch(
        &self,
        clusters_data: Vec<(Vec<Py<DERResource>>, f64, HashMap<String, f64>, Option<f64>)>,
        interval_hours: f64,
    ) -> PyResult<Vec<DispatchResult>> {
        let mut results = Vec::new();

        for (resources, target_kw, nodal_prices, carbon_intensity) in clusters_data {
            let result = self.dispatch(resources, target_kw, nodal_prices, carbon_intensity, interval_hours)?;
            results.push(result);
        }

        Ok(results)
    }
}

/// Python module definition
#[pymodule]
fn gridtokenx_sim(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MeterConfig>()?;
    m.add_class::<EnergyReading>()?;
    m.add_function(wrap_pyfunction!(generate_readings, m)?)?;
    
    // VPP Dispatch (Phase 2)
    m.add_class::<DERResource>()?;
    m.add_class::<DispatchResult>()?;
    m.add_class::<VPPDispatchEngine>()?;
    
    Ok(())
}
