//! Meter management API routes

use actix_web::{web, HttpResponse, Scope};
use std::sync::Arc;

use crate::models::*;
use crate::state::{AppState, MeterState};

/// Configure meter routes
pub fn configure() -> Scope {
    web::scope("/meters")
        .route("", web::get().to(list_meters))
        .route("/", web::get().to(list_meters))
        .route("/add", web::post().to(add_meter))
        .route("/overrides", web::get().to(get_overrides))
        .route("/{meter_id}", web::delete().to(delete_meter))
        .route("/{meter_id}/status", web::get().to(get_meter_status))
        .route("/{meter_id}/override", web::post().to(set_override))
        .route("/{meter_id}/override", web::delete().to(delete_override))
}

/// List all meters
async fn list_meters(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let meters = state.meters.read().unwrap();
    
    let meter_list: Vec<MeterStatus> = meters
        .values()
        .map(|m| m.to_status())
        .collect();
    
    HttpResponse::Ok().json(MeterListResponse {
        total_meters: meter_list.len(),
        meters: meter_list,
    })
}

/// Add a new meter
async fn add_meter(
    state: web::Data<Arc<AppState>>,
    req: web::Json<MeterRequest>,
) -> HttpResponse {
    let mut meters = state.meters.write().unwrap();
    
    let meter = MeterState::new(&req);
    let meter_id = meter.meter_id.clone();
    let meter_type = meter.meter_type.clone();
    let location = meter.location.clone();
    let solar_capacity = meter.solar_capacity;
    let battery_capacity = meter.battery_capacity;
    let trading_preference = meter.trading_preference.clone();
    
    // Generate a mock public key
    let public_key = format!("0x{:0>64}", uuid::Uuid::new_v4().simple());
    
    meters.insert(meter_id.clone(), meter);
    let total = meters.len();
    
    HttpResponse::Ok().json(AddMeterResponse {
        success: true,
        message: format!("Successfully added {} meter", meter_type),
        meter: MeterInfo {
            meter_id,
            meter_type,
            location,
            solar_capacity,
            battery_capacity,
            trading_preference,
            meter_public_key: public_key,
        },
        total_meters: total,
    })
}

/// Delete a meter
async fn delete_meter(
    state: web::Data<Arc<AppState>>,
    path: web::Path<String>,
) -> HttpResponse {
    let meter_id = path.into_inner();
    let mut meters = state.meters.write().unwrap();
    
    if meters.remove(&meter_id).is_some() {
        HttpResponse::Ok().json(serde_json::json!({
            "success": true,
            "message": format!("Successfully removed meter {}", meter_id),
            "total_meters": meters.len()
        }))
    } else {
        HttpResponse::NotFound().json(ErrorResponse::new(format!("Meter {} not found", meter_id)))
    }
}

/// Get meter status
async fn get_meter_status(
    state: web::Data<Arc<AppState>>,
    path: web::Path<String>,
) -> HttpResponse {
    let meter_id = path.into_inner();
    let meters = state.meters.read().unwrap();
    
    if let Some(meter) = meters.get(&meter_id) {
        HttpResponse::Ok().json(meter.to_status())
    } else {
        HttpResponse::NotFound().json(ErrorResponse::new(format!("Meter {} not found", meter_id)))
    }
}

/// Set meter override
async fn set_override(
    state: web::Data<Arc<AppState>>,
    path: web::Path<String>,
    req: web::Json<MeterOverrideRequest>,
) -> HttpResponse {
    let meter_id = path.into_inner();
    let mut meters = state.meters.write().unwrap();
    
    if let Some(meter) = meters.get_mut(&meter_id) {
        meter.override_data = Some(req.into_inner());
        HttpResponse::Ok().json(serde_json::json!({
            "success": true,
            "message": format!("Manual override set for {}", meter_id),
            "override": meter.override_data
        }))
    } else {
        HttpResponse::NotFound().json(ErrorResponse::new(format!("Meter {} not found", meter_id)))
    }
}

/// Delete meter override
async fn delete_override(
    state: web::Data<Arc<AppState>>,
    path: web::Path<String>,
) -> HttpResponse {
    let meter_id = path.into_inner();
    let mut meters = state.meters.write().unwrap();
    
    if let Some(meter) = meters.get_mut(&meter_id) {
        meter.override_data = None;
        HttpResponse::Ok().json(SuccessResponse {
            success: true,
            message: format!("Override removed for {}, returned to auto mode", meter_id),
        })
    } else {
        HttpResponse::NotFound().json(ErrorResponse::new(format!("Meter {} not found", meter_id)))
    }
}

/// Get all overrides
async fn get_overrides(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let meters = state.meters.read().unwrap();
    
    let overrides: std::collections::HashMap<String, &MeterOverrideRequest> = meters
        .iter()
        .filter_map(|(id, m)| m.override_data.as_ref().map(|o| (id.clone(), o)))
        .collect();
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "overrides": overrides
    }))
}
