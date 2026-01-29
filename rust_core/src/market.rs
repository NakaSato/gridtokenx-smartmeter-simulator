//! Market price calculator

use pyo3::prelude::*;
use crate::models::MarketPrices;

#[pyclass]
pub struct MarketCalculator {
    base_buy_price: f64,
    base_sell_price: f64,
    peak_multiplier: f64,
    demand_sensitivity: f64,
}

#[pymethods]
impl MarketCalculator {
    #[new]
    #[pyo3(signature = (base_buy_price = 0.28, base_sell_price = 0.12, peak_multiplier = 1.5, demand_sensitivity = 0.1))]
    fn new(base_buy_price: f64, base_sell_price: f64, peak_multiplier: f64, demand_sensitivity: f64) -> Self {
        Self { base_buy_price, base_sell_price, peak_multiplier, demand_sensitivity }
    }

    /// Check if peak hour (Thailand: 9am-10pm weekdays)
    fn is_peak_hour(&self, hour: u32, is_weekend: bool) -> bool {
        if is_weekend { return false; }
        hour >= 9 && hour < 22
    }

    /// Calculate current market prices
    fn calculate_prices(&self, hour: u32, is_weekend: bool, total_gen_kw: f64, total_load_kw: f64) -> MarketPrices {
        let is_peak = self.is_peak_hour(hour, is_weekend);
        
        let demand_ratio = if total_gen_kw > 0.0 { total_load_kw / total_gen_kw } else { 1.5 };
        let demand_factor = 1.0 + (demand_ratio - 1.0) * self.demand_sensitivity;
        let peak_factor = if is_peak { self.peak_multiplier } else { 1.0 };
        
        let buy_price = self.base_buy_price * peak_factor * demand_factor;
        let sell_price = self.base_sell_price * peak_factor / demand_factor.max(0.5);
        let p2p_price = (buy_price + sell_price) / 2.0;
        
        MarketPrices {
            grid_buy_price: buy_price,
            grid_sell_price: sell_price,
            p2p_price,
            is_peak_hour: is_peak,
            demand_multiplier: demand_factor,
        }
    }

    fn __repr__(&self) -> String {
        format!("MarketCalculator(buy={:.2}, sell={:.2})", self.base_buy_price, self.base_sell_price)
    }
}
