//! SmartMeter Core - High-performance simulation engine in Rust
//! 
//! Provides:
//! - Data models (MeterConfig, EnergyReading, GridState, ZoneState)
//! - Solar generation calculator
//! - Load profile calculator  
//! - Battery state management
//! - Grid physics calculations
//! - Market pricing
//! - Emission tracking
//! - Weather simulation
//! - Power quality (THD)
//! - P2P Trading/Matching engine
//! - Zoning service
//! - Complete meter simulation
//!
//! Note: pandapower integration remains in Python

mod models;
mod solar;
mod load;
mod battery;
mod grid;
mod market;
mod emission;
mod weather;
mod power_quality;
mod trading;
mod zoning;
mod meter_sim;

use pyo3::prelude::*;

#[pymodule]
fn smartmeter_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Data models
    m.add_class::<models::MeterConfig>()?;
    m.add_class::<models::MeterState>()?;
    m.add_class::<models::EnergyReading>()?;
    m.add_class::<models::GridState>()?;
    m.add_class::<models::ZoneState>()?;
    m.add_class::<models::MarketPrices>()?;
    
    // Core Calculators
    m.add_class::<solar::SolarCalculator>()?;
    m.add_class::<load::LoadCalculator>()?;
    m.add_class::<battery::BatteryState>()?;
    m.add_class::<grid::GridPhysics>()?;
    m.add_class::<grid::ZoneAggregator>()?;
    m.add_class::<market::MarketCalculator>()?;
    m.add_class::<emission::EmissionCalculator>()?;
    
    // Weather system
    m.add_class::<weather::WeatherSystem>()?;
    
    // Power quality
    m.add_class::<power_quality::PowerQuality>()?;
    
    // P2P Trading
    m.add_class::<trading::TradeBid>()?;
    m.add_class::<trading::TradeAsk>()?;
    m.add_class::<trading::TradeMatch>()?;
    m.add_class::<trading::NetworkCost>()?;
    m.add_class::<trading::MatchingEngine>()?;
    
    // Zoning
    m.add_class::<zoning::ZoneInfo>()?;
    m.add_class::<zoning::ZoningService>()?;
    
    // Complete Meter Simulation
    m.add_class::<meter_sim::MeterSim>()?;
    m.add_class::<meter_sim::SimReading>()?;
    
    // Module info
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(is_rust_core, m)?)?;
    
    Ok(())
}

#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

#[pyfunction]
fn is_rust_core() -> bool {
    true
}

