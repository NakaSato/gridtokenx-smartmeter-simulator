//! P2P trading API routes

use actix_web::{web, HttpResponse, Scope};
use std::sync::Arc;

use crate::models::*;
use crate::state::AppState;

/// Configure P2P routes
pub fn configure() -> Scope {
    web::scope("/v1/p2p")
        .route("/calculate-cost", web::post().to(calculate_p2p_cost))
}

/// Calculate P2P trade cost including wheeling and losses
async fn calculate_p2p_cost(
    state: web::Data<Arc<AppState>>,
    req: web::Json<P2PCostRequest>,
) -> HttpResponse {
    // Calculate wheeling charge
    let wheeling_charge = state.calculate_wheeling_charge(
        req.seller_zone_id,
        req.buyer_zone_id,
        req.energy_amount,
    );
    
    // Calculate loss factor
    let loss_factor = state.calculate_loss_factor(
        req.seller_zone_id,
        req.buyer_zone_id,
    );
    
    // Calculate energy cost
    let energy_cost = req.energy_amount * req.agreed_price;
    
    // Calculate loss cost
    let loss_cost = req.energy_amount * loss_factor * req.agreed_price;
    
    // Calculate effective energy
    let effective_energy = req.energy_amount * (1.0 - loss_factor);
    
    // Calculate total cost
    let total_cost = energy_cost + wheeling_charge + loss_cost;
    
    // Zone distance (simplified)
    let zone_distance_km = if req.buyer_zone_id == req.seller_zone_id {
        0.0
    } else {
        5.0
    };
    
    HttpResponse::Ok().json(P2PCostResponse {
        energy_cost: round_to(energy_cost, 4),
        wheeling_charge: round_to(wheeling_charge, 4),
        loss_cost: round_to(loss_cost, 4),
        total_cost: round_to(total_cost, 4),
        effective_energy: round_to(effective_energy, 4),
        loss_factor: round_to(loss_factor, 4),
        loss_allocation: "RECEIVER".to_string(),
        zone_distance_km: round_to(zone_distance_km, 2),
        buyer_zone: req.buyer_zone_id,
        seller_zone: req.seller_zone_id,
        is_grid_compliant: true,
        grid_violation_reason: None,
    })
}

fn round_to(value: f64, decimals: i32) -> f64 {
    let factor = 10_f64.powi(decimals);
    (value * factor).round() / factor
}
