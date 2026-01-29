//! P2P Trading and Matching Engine

use pyo3::prelude::*;
use std::collections::HashMap;

/// A trade bid (buyer)
#[pyclass]
#[derive(Debug, Clone)]
pub struct TradeBid {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub zone: i32,
    #[pyo3(get, set)]
    pub amount_kwh: f64,
    #[pyo3(get, set)]
    pub price: f64,
    #[pyo3(get, set)]
    pub wallet: String,
}

#[pymethods]
impl TradeBid {
    #[new]
    pub fn new(id: String, zone: i32, amount_kwh: f64, price: f64, wallet: String) -> Self {
        TradeBid { id, zone, amount_kwh, price, wallet }
    }
}

/// A trade ask (seller)
#[pyclass]
#[derive(Debug, Clone)]
pub struct TradeAsk {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub zone: i32,
    #[pyo3(get, set)]
    pub amount_kwh: f64,
    #[pyo3(get, set)]
    pub price: f64,
    #[pyo3(get, set)]
    pub wallet: String,
}

#[pymethods]
impl TradeAsk {
    #[new]
    pub fn new(id: String, zone: i32, amount_kwh: f64, price: f64, wallet: String) -> Self {
        TradeAsk { id, zone, amount_kwh, price, wallet }
    }
}

/// Result of a matched trade
#[pyclass]
#[derive(Debug, Clone)]
pub struct TradeMatch {
    #[pyo3(get)]
    pub buyer_id: String,
    #[pyo3(get)]
    pub seller_id: String,
    #[pyo3(get)]
    pub amount_kwh: f64,
    #[pyo3(get)]
    pub price_per_kwh: f64,
    #[pyo3(get)]
    pub total_cost: f64,
    #[pyo3(get)]
    pub welfare_score: f64,
    #[pyo3(get)]
    pub wheeling_charge: f64,
    #[pyo3(get)]
    pub same_zone: bool,
}

#[pymethods]
impl TradeMatch {
    #[new]
    pub fn new(
        buyer_id: String,
        seller_id: String,
        amount_kwh: f64,
        price_per_kwh: f64,
        wheeling_charge: f64,
        same_zone: bool,
    ) -> Self {
        let total_cost = amount_kwh * price_per_kwh + wheeling_charge;
        TradeMatch {
            buyer_id,
            seller_id,
            amount_kwh,
            price_per_kwh,
            total_cost,
            welfare_score: 0.0,
            wheeling_charge,
            same_zone,
        }
    }
}

/// Network cost parameters
#[pyclass]
#[derive(Debug, Clone)]
pub struct NetworkCost {
    #[pyo3(get)]
    pub wheeling_charge: f64,
    #[pyo3(get)]
    pub loss_cost: f64,
    #[pyo3(get)]
    pub total_cost: f64,
}

#[pymethods]
impl NetworkCost {
    #[new]
    pub fn new(wheeling_charge: f64, loss_cost: f64) -> Self {
        NetworkCost {
            wheeling_charge,
            loss_cost,
            total_cost: wheeling_charge + loss_cost,
        }
    }
}

/// P2P Trading matching engine
#[pyclass]
#[derive(Debug, Clone)]
pub struct MatchingEngine {
    same_zone_wheeling: f64,
    cross_zone_wheeling: f64,
    loss_factor: f64,
    stability_coeff: f64,
}

#[pymethods]
impl MatchingEngine {
    #[new]
    #[pyo3(signature = (same_zone_wheeling = 0.01, cross_zone_wheeling = 0.05, loss_factor = 0.02, stability_coeff = 0.5))]
    pub fn new(
        same_zone_wheeling: f64,
        cross_zone_wheeling: f64,
        loss_factor: f64,
        stability_coeff: f64,
    ) -> Self {
        MatchingEngine {
            same_zone_wheeling,
            cross_zone_wheeling,
            loss_factor,
            stability_coeff,
        }
    }
    
    /// Calculate network cost for a trade between zones
    pub fn calculate_network_cost(&self, from_zone: i32, to_zone: i32, amount_kwh: f64) -> NetworkCost {
        let wheeling = if from_zone == to_zone {
            self.same_zone_wheeling * amount_kwh
        } else {
            self.cross_zone_wheeling * amount_kwh
        };
        
        let loss = self.loss_factor * amount_kwh;
        
        NetworkCost::new(wheeling, loss)
    }
    
    /// Simple greedy matching algorithm
    /// Returns list of matches and total welfare
    pub fn match_greedy(
        &self,
        bids: Vec<TradeBid>,
        asks: Vec<TradeAsk>,
    ) -> (Vec<TradeMatch>, f64) {
        let mut matches = Vec::new();
        let mut total_welfare = 0.0;
        
        // Sort bids by price descending, asks by price ascending
        let mut sorted_bids = bids;
        let mut sorted_asks = asks;
        sorted_bids.sort_by(|a, b| b.price.partial_cmp(&a.price).unwrap());
        sorted_asks.sort_by(|a, b| a.price.partial_cmp(&b.price).unwrap());
        
        let mut bid_remaining: HashMap<String, f64> = sorted_bids
            .iter()
            .map(|b| (b.id.clone(), b.amount_kwh))
            .collect();
        let mut ask_remaining: HashMap<String, f64> = sorted_asks
            .iter()
            .map(|a| (a.id.clone(), a.amount_kwh))
            .collect();
        
        for bid in &sorted_bids {
            for ask in &sorted_asks {
                // Check if trade is profitable (bid price >= ask price)
                if bid.price < ask.price {
                    continue;
                }
                
                let bid_rem = *bid_remaining.get(&bid.id).unwrap_or(&0.0);
                let ask_rem = *ask_remaining.get(&ask.id).unwrap_or(&0.0);
                
                if bid_rem <= 0.0 || ask_rem <= 0.0 {
                    continue;
                }
                
                // Calculate match amount
                let match_amount = bid_rem.min(ask_rem);
                let same_zone = bid.zone == ask.zone;
                
                // Calculate clearing price (midpoint)
                let clearing_price = (bid.price + ask.price) / 2.0;
                
                // Calculate network cost
                let network_cost = self.calculate_network_cost(ask.zone, bid.zone, match_amount);
                
                // Calculate welfare (spread - friction)
                let energy_spread = (bid.price - ask.price) * match_amount;
                let welfare = energy_spread - network_cost.total_cost;
                
                if welfare >= 0.0 {
                    let mut trade = TradeMatch::new(
                        bid.id.clone(),
                        ask.id.clone(),
                        match_amount,
                        clearing_price,
                        network_cost.wheeling_charge,
                        same_zone,
                    );
                    trade.welfare_score = welfare;
                    
                    matches.push(trade);
                    total_welfare += welfare;
                    
                    // Update remaining amounts
                    bid_remaining.insert(bid.id.clone(), bid_rem - match_amount);
                    ask_remaining.insert(ask.id.clone(), ask_rem - match_amount);
                }
            }
        }
        
        (matches, total_welfare)
    }
    
    /// Match with voltage stability consideration
    pub fn match_with_stability(
        &self,
        bids: Vec<TradeBid>,
        asks: Vec<TradeAsk>,
        zone_voltages: HashMap<i32, f64>,
    ) -> (Vec<TradeMatch>, f64) {
        let mut matches = Vec::new();
        let mut total_welfare = 0.0;
        
        // Sort and prepare
        let mut sorted_bids = bids;
        let mut sorted_asks = asks;
        sorted_bids.sort_by(|a, b| b.price.partial_cmp(&a.price).unwrap());
        sorted_asks.sort_by(|a, b| a.price.partial_cmp(&b.price).unwrap());
        
        let mut bid_remaining: HashMap<String, f64> = sorted_bids
            .iter()
            .map(|b| (b.id.clone(), b.amount_kwh))
            .collect();
        let mut ask_remaining: HashMap<String, f64> = sorted_asks
            .iter()
            .map(|a| (a.id.clone(), a.amount_kwh))
            .collect();
        
        for bid in &sorted_bids {
            for ask in &sorted_asks {
                if bid.price < ask.price {
                    continue;
                }
                
                let bid_rem = *bid_remaining.get(&bid.id).unwrap_or(&0.0);
                let ask_rem = *ask_remaining.get(&ask.id).unwrap_or(&0.0);
                
                if bid_rem <= 0.0 || ask_rem <= 0.0 {
                    continue;
                }
                
                let match_amount = bid_rem.min(ask_rem);
                let same_zone = bid.zone == ask.zone;
                let clearing_price = (bid.price + ask.price) / 2.0;
                let network_cost = self.calculate_network_cost(ask.zone, bid.zone, match_amount);
                
                // Calculate stability bonus
                let v_buyer = *zone_voltages.get(&bid.zone).unwrap_or(&1.0);
                let v_seller = *zone_voltages.get(&ask.zone).unwrap_or(&1.0);
                let mut stability_bonus = 0.0;
                
                // Encourage exports from low-voltage zones (inject power)
                if v_seller < 0.96 {
                    stability_bonus += self.stability_coeff;
                } else if v_seller > 1.04 {
                    stability_bonus -= self.stability_coeff;
                }
                
                // Encourage imports to high-voltage zones (absorb power)
                if v_buyer > 1.04 {
                    stability_bonus += self.stability_coeff;
                } else if v_buyer < 0.96 {
                    stability_bonus -= self.stability_coeff;
                }
                
                // Calculate welfare
                let energy_spread = (bid.price - ask.price) * match_amount;
                let welfare = energy_spread - network_cost.total_cost + stability_bonus;
                
                if welfare >= 0.0 {
                    let mut trade = TradeMatch::new(
                        bid.id.clone(),
                        ask.id.clone(),
                        match_amount,
                        clearing_price,
                        network_cost.wheeling_charge,
                        same_zone,
                    );
                    trade.welfare_score = welfare;
                    
                    matches.push(trade);
                    total_welfare += welfare;
                    
                    bid_remaining.insert(bid.id.clone(), bid_rem - match_amount);
                    ask_remaining.insert(ask.id.clone(), ask_rem - match_amount);
                }
            }
        }
        
        (matches, total_welfare)
    }
}
