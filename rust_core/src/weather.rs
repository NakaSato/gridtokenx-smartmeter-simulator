//! Weather simulation system with Markov chain transitions

use pyo3::prelude::*;
use rand::Rng;
use std::collections::HashMap;

/// Weather conditions
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum WeatherCondition {
    Sunny,
    PartlyCloudy,
    Cloudy,
    Rainy,
    Stormy,
}

impl WeatherCondition {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "sunny" | "clear" => WeatherCondition::Sunny,
            "partly cloudy" | "partlycloudy" | "partly_cloudy" => WeatherCondition::PartlyCloudy,
            "cloudy" | "overcast" => WeatherCondition::Cloudy,
            "rainy" | "rain" | "drizzle" => WeatherCondition::Rainy,
            "stormy" | "storm" | "thunderstorm" => WeatherCondition::Stormy,
            _ => WeatherCondition::PartlyCloudy,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            WeatherCondition::Sunny => "Sunny",
            WeatherCondition::PartlyCloudy => "PartlyCloudy",
            WeatherCondition::Cloudy => "Cloudy",
            WeatherCondition::Rainy => "Rainy",
            WeatherCondition::Stormy => "Stormy",
        }
    }
}

/// Weather system with Markov chain state transitions
#[pyclass]
#[derive(Debug, Clone)]
pub struct WeatherSystem {
    state: WeatherCondition,
    transitions: HashMap<WeatherCondition, Vec<(WeatherCondition, f64)>>,
    irradiance: HashMap<WeatherCondition, f64>,
    temp_offset: HashMap<WeatherCondition, f64>,
}

#[pymethods]
impl WeatherSystem {
    #[new]
    #[pyo3(signature = (initial_state = "Sunny"))]
    pub fn new(initial_state: &str) -> Self {
        let state = WeatherCondition::from_str(initial_state);
        
        // Build transition probabilities
        let mut transitions = HashMap::new();
        
        transitions.insert(WeatherCondition::Sunny, vec![
            (WeatherCondition::Sunny, 0.7),
            (WeatherCondition::PartlyCloudy, 0.2),
            (WeatherCondition::Cloudy, 0.1),
        ]);
        
        transitions.insert(WeatherCondition::PartlyCloudy, vec![
            (WeatherCondition::Sunny, 0.3),
            (WeatherCondition::PartlyCloudy, 0.4),
            (WeatherCondition::Cloudy, 0.2),
            (WeatherCondition::Rainy, 0.1),
        ]);
        
        transitions.insert(WeatherCondition::Cloudy, vec![
            (WeatherCondition::Sunny, 0.1),
            (WeatherCondition::PartlyCloudy, 0.3),
            (WeatherCondition::Cloudy, 0.4),
            (WeatherCondition::Rainy, 0.2),
        ]);
        
        transitions.insert(WeatherCondition::Rainy, vec![
            (WeatherCondition::PartlyCloudy, 0.1),
            (WeatherCondition::Cloudy, 0.3),
            (WeatherCondition::Rainy, 0.5),
            (WeatherCondition::Stormy, 0.1),
        ]);
        
        transitions.insert(WeatherCondition::Stormy, vec![
            (WeatherCondition::Cloudy, 0.2),
            (WeatherCondition::Rainy, 0.4),
            (WeatherCondition::Stormy, 0.4),
        ]);
        
        // Irradiance factors
        let mut irradiance = HashMap::new();
        irradiance.insert(WeatherCondition::Sunny, 1.0);
        irradiance.insert(WeatherCondition::PartlyCloudy, 0.7);
        irradiance.insert(WeatherCondition::Cloudy, 0.4);
        irradiance.insert(WeatherCondition::Rainy, 0.1);
        irradiance.insert(WeatherCondition::Stormy, 0.05);
        
        // Temperature offsets
        let mut temp_offset = HashMap::new();
        temp_offset.insert(WeatherCondition::Sunny, 2.0);
        temp_offset.insert(WeatherCondition::PartlyCloudy, 0.0);
        temp_offset.insert(WeatherCondition::Cloudy, -2.0);
        temp_offset.insert(WeatherCondition::Rainy, -4.0);
        temp_offset.insert(WeatherCondition::Stormy, -5.0);
        
        WeatherSystem {
            state,
            transitions,
            irradiance,
            temp_offset,
        }
    }
    
    /// Get current weather state as string (Python property)
    #[getter]
    pub fn current_state(&self) -> String {
        self.state.as_str().to_string()
    }
    
    /// Get current weather state as string
    pub fn current(&self) -> String {
        self.state.as_str().to_string()
    }
    
    /// Update weather using Markov chain transition
    pub fn update(&mut self) -> String {
        let mut rng = rand::thread_rng();
        let random_val: f64 = rng.gen();
        
        if let Some(probs) = self.transitions.get(&self.state) {
            let mut cumulative = 0.0;
            for (next_state, prob) in probs {
                cumulative += prob;
                if random_val <= cumulative {
                    self.state = *next_state;
                    break;
                }
            }
        }
        
        self.state.as_str().to_string()
    }
    
    /// Step: update and return (irradiance, temperature, state)
    /// For compatibility with Python test code
    pub fn step(&mut self) -> (f64, f64, String) {
        self.update();
        let irr = self.get_irradiance(None) * 1000.0;  // W/m2
        let temp = 25.0 + self.get_temp_offset(None);   // base temp + offset
        (irr, temp, self.state.as_str().to_string())
    }
    
    /// Get irradiance factor for current or specified state
    #[pyo3(signature = (state = None))]
    pub fn get_irradiance(&self, state: Option<&str>) -> f64 {
        let target = match state {
            Some(s) => WeatherCondition::from_str(s),
            None => self.state,
        };
        *self.irradiance.get(&target).unwrap_or(&1.0)
    }
    
    /// Get temperature offset for current or specified state
    #[pyo3(signature = (state = None))]
    pub fn get_temp_offset(&self, state: Option<&str>) -> f64 {
        let target = match state {
            Some(s) => WeatherCondition::from_str(s),
            None => self.state,
        };
        *self.temp_offset.get(&target).unwrap_or(&0.0)
    }
    
    /// Get both irradiance and temp offset as tuple
    #[pyo3(signature = (state = None))]
    pub fn get_factors(&self, state: Option<&str>) -> (f64, f64) {
        (self.get_irradiance(state.clone()), self.get_temp_offset(state))
    }
    
    /// Set weather state directly
    pub fn set_state(&mut self, state_name: &str) {
        self.state = WeatherCondition::from_str(state_name);
    }
}
