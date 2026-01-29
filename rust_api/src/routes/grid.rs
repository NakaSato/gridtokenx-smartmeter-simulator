//! Grid analysis API routes

use actix_web::{web, HttpResponse, Scope};
use std::sync::Arc;
use std::collections::HashMap;
use chrono::Utc;
use rand::Rng;

use crate::models::*;
use crate::state::AppState;

/// Configure grid routes
pub fn configure() -> Scope {
    web::scope("/grid")
        .route("/status", web::get().to(get_grid_status))
        .route("/zones", web::get().to(get_zones))
        .route("/state/{meter_id}", web::get().to(get_meter_grid_state))
        .route("/zone/{zone_id}/state", web::get().to(get_zone_state))
        .route("/zones/state", web::get().to(get_all_zone_states))
        .route("/analysis", web::get().to(get_grid_analysis))
        .route("/losses", web::get().to(get_loss_analysis))
        .route("/optimization-data", web::get().to(get_optimization_data))
        .route("/battery/dispatch", web::post().to(dispatch_battery))
        .route("/events", web::get().to(get_grid_events))
        .route("/health", web::get().to(grid_health))
        .route("/debug/stats", web::get().to(debug_stats))
        .route("/thailand/data", web::get().to(get_thailand_data))
}

/// Get aggregate grid status
async fn get_grid_status(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let meters = state.meters.read().unwrap();
    
    let mut total_generation = 0.0;
    let mut total_consumption = 0.0;
    let mut active_meters = 0;
    
    for meter in meters.values() {
        if meter.is_connected {
            active_meters += 1;
            if let Some(reading) = &meter.last_reading {
                total_generation += reading.energy_generated;
                total_consumption += reading.energy_consumed;
            }
        }
    }
    
    let net_balance = total_generation - total_consumption;
    let co2_saved_kg = total_generation * 0.5;
    
    HttpResponse::Ok().json(GridStatusResponse {
        total_generation: round_to(total_generation, 4),
        total_consumption: round_to(total_consumption, 4),
        net_balance: round_to(net_balance, 4),
        active_meters,
        co2_saved_kg: round_to(co2_saved_kg, 4),
        timestamp: Utc::now().to_rfc3339(),
    })
}

/// Get zones with meter assignments
async fn get_zones(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let zones = state.zones.read().unwrap();
    let meters = state.meters.read().unwrap();
    
    let mut zones_map = HashMap::new();
    for (id, zone) in zones.iter() {
        zones_map.insert(id.to_string(), ZoneInfo {
            zone_id: zone.zone_id,
            centroid_lat: zone.centroid_lat,
            centroid_lon: zone.centroid_lon,
            meter_count: zone.meter_ids.len() as i32,
            transformer_name: zone.transformer_name.clone(),
        });
    }
    
    let meter_list: Vec<MeterZoneInfo> = meters.values()
        .filter(|m| m.latitude.is_some() && m.longitude.is_some())
        .map(|m| MeterZoneInfo {
            meter_id: m.meter_id.clone(),
            latitude: m.latitude.unwrap_or(0.0),
            longitude: m.longitude.unwrap_or(0.0),
            zone_id: m.zone_id,
            meter_type: m.meter_type.clone(),
        })
        .collect();
    
    // Build wheeling/loss matrices
    let mut wheeling_charges = HashMap::new();
    let mut loss_factors = HashMap::new();
    
    for from_zone in zones.keys() {
        for to_zone in zones.keys() {
            let key = format!("{}_{}", from_zone, to_zone);
            wheeling_charges.insert(key.clone(), if from_zone == to_zone { 0.01 } else { 0.05 });
            loss_factors.insert(key, if from_zone == to_zone { 0.01 } else { 0.03 });
        }
    }
    
    HttpResponse::Ok().json(ZonesResponse {
        zones: zones_map,
        meters: meter_list,
        wheeling_charges,
        loss_factors,
    })
}

/// Get grid state for a specific meter
async fn get_meter_grid_state(
    state: web::Data<Arc<AppState>>,
    path: web::Path<String>,
) -> HttpResponse {
    let meter_id = path.into_inner();
    let meters = state.meters.read().unwrap();
    
    if let Some(meter) = meters.get(&meter_id) {
        let mut rng = rand::thread_rng();
        let hour = Utc::now().hour() as i32;
        let is_peak = (hour >= 9 && hour <= 14) || (hour >= 18 && hour <= 22);
        
        HttpResponse::Ok().json(GridStateResponse {
            meter_id: meter.meter_id.clone(),
            voltage_pu: round_to(1.0 + rng.gen_range(-0.02..0.02), 4),
            voltage_v: round_to(230.0 + rng.gen_range(-4.0..4.0), 1),
            frequency_hz: round_to(50.0 + rng.gen_range(-0.01..0.01), 3),
            power_factor: round_to(0.95 + rng.gen_range(-0.02..0.02), 3),
            thd_voltage: round_to(rng.gen_range(1.0..3.0), 2),
            thd_current: round_to(rng.gen_range(3.0..8.0), 2),
            is_on_peak: is_peak,
            temperature_c: round_to(25.0 + rng.gen_range(-2.0..5.0), 1),
        })
    } else {
        HttpResponse::NotFound().json(ErrorResponse::new(format!("Meter {} not found", meter_id)))
    }
}

use chrono::Timelike;

/// Get zone state
async fn get_zone_state(
    state: web::Data<Arc<AppState>>,
    path: web::Path<i32>,
) -> HttpResponse {
    let zone_id = path.into_inner();
    let zones = state.zones.read().unwrap();
    let meters = state.meters.read().unwrap();
    
    if let Some(zone) = zones.get(&zone_id) {
        let mut rng = rand::thread_rng();
        
        let mut total_load = 0.0;
        let mut total_gen = 0.0;
        let mut voltages = Vec::new();
        
        for meter_id in &zone.meter_ids {
            if let Some(meter) = meters.get(meter_id) {
                if let Some(reading) = &meter.last_reading {
                    total_load += reading.energy_consumed * 4.0; // Convert to kW
                    total_gen += reading.energy_generated * 4.0;
                    voltages.push(reading.voltage / 230.0);
                }
            }
        }
        
        let avg_v = if voltages.is_empty() { 1.0 } else { voltages.iter().sum::<f64>() / voltages.len() as f64 };
        let min_v = voltages.iter().cloned().fold(1.0, f64::min);
        let max_v = voltages.iter().cloned().fold(1.0, f64::max);
        
        let has_violation = min_v < 0.95 || max_v > 1.05;
        let has_overload = total_load > 100.0; // Arbitrary threshold
        
        let voltage_penalty = (1.0 - avg_v).abs() * 100.0;
        let mut health = (100.0 - voltage_penalty).max(0.0);
        if has_violation { health *= 0.8; }
        if has_overload { health *= 0.7; }
        
        HttpResponse::Ok().json(ZoneStateResponse {
            zone_id,
            avg_voltage_pu: round_to(avg_v, 4),
            min_voltage_pu: round_to(min_v, 4),
            max_voltage_pu: round_to(max_v, 4),
            total_load_kw: round_to(total_load, 2),
            total_generation_kw: round_to(total_gen, 2),
            net_power_kw: round_to(total_gen - total_load, 2),
            meter_count: zone.meter_ids.len() as i32,
            has_voltage_violation: has_violation,
            has_overload,
            health_score: round_to(health, 2),
        })
    } else {
        HttpResponse::NotFound().json(ErrorResponse::new(format!("Zone {} not found", zone_id)))
    }
}

/// Get all zone states
async fn get_all_zone_states(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let zones = state.zones.read().unwrap();
    let meters = state.meters.read().unwrap();
    
    let mut results = Vec::new();
    
    for (zone_id, zone) in zones.iter() {
        let mut total_load = 0.0;
        let mut total_gen = 0.0;
        let mut voltages = Vec::new();
        
        for meter_id in &zone.meter_ids {
            if let Some(meter) = meters.get(meter_id) {
                if let Some(reading) = &meter.last_reading {
                    total_load += reading.energy_consumed * 4.0;
                    total_gen += reading.energy_generated * 4.0;
                    voltages.push(reading.voltage / 230.0);
                }
            }
        }
        
        let avg_v = if voltages.is_empty() { 1.0 } else { voltages.iter().sum::<f64>() / voltages.len() as f64 };
        let has_violation = voltages.iter().any(|&v| v < 0.95 || v > 1.05);
        let has_overload = total_load > 100.0;
        
        let voltage_penalty = (1.0 - avg_v).abs() * 100.0;
        let mut health = (100.0 - voltage_penalty).max(0.0);
        if has_violation { health *= 0.8; }
        if has_overload { health *= 0.7; }
        
        results.push(serde_json::json!({
            "zone_id": zone_id,
            "health_score": round_to(health, 2),
            "has_overload": has_overload,
            "transformer_name": zone.transformer_name,
            "avg_voltage_pu": round_to(avg_v, 4),
            "net_power_kw": round_to(total_gen - total_load, 2)
        }));
    }
    
    HttpResponse::Ok().json(results)
}

/// Get grid analysis
async fn get_grid_analysis(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let meters = state.meters.read().unwrap();
    let zones = state.zones.read().unwrap();
    
    let mut total_load = 0.0;
    let mut total_gen = 0.0;
    
    for meter in meters.values() {
        if let Some(reading) = &meter.last_reading {
            total_load += reading.energy_consumed * 4.0 / 1000.0; // MW
            total_gen += reading.energy_generated * 4.0 / 1000.0;
        }
    }
    
    let total_loss = total_load * 0.02; // 2% loss estimate
    let loss_pct = if total_load > 0.0 { total_loss / total_load * 100.0 } else { 0.0 };
    
    HttpResponse::Ok().json(GridAnalysisResponse {
        timestamp: Utc::now().to_rfc3339(),
        power_flow_converged: true,
        total_load_mw: round_to(total_load, 4),
        total_generation_mw: round_to(total_gen, 4),
        total_loss_mw: round_to(total_loss, 4),
        loss_percentage: round_to(loss_pct, 2),
        zone_count: zones.len() as i32,
        voltage_violations: Vec::new(),
        overloaded_elements: Vec::new(),
        recommendations: vec!["System operating normally".to_string()],
    })
}

/// Get loss analysis
async fn get_loss_analysis(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let zones = state.zones.read().unwrap();
    
    let mut zone_losses = HashMap::new();
    for (zone_id, _) in zones.iter() {
        zone_losses.insert(zone_id.to_string(), serde_json::json!({
            "zone_id": zone_id,
            "loss_mw": 0.01,
            "loss_percent": 2.0,
            "recommendations": []
        }));
    }
    
    HttpResponse::Ok().json(serde_json::json!({
        "total_loss_mw": 0.03,
        "total_loss_percent": 2.0,
        "zone_losses": zone_losses
    }))
}

/// Get optimization data
async fn get_optimization_data(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let meters = state.meters.read().unwrap();
    
    let mut meter_data = Vec::new();
    let mut total_load = 0.0;
    let mut total_gen = 0.0;
    let mut meters_with_battery = 0;
    let mut meters_with_solar = 0;
    let mut available_battery = 0.0;
    
    for meter in meters.values() {
        let current_load = meter.last_reading.as_ref().map(|r| r.energy_consumed * 4.0).unwrap_or(0.0);
        let current_gen = meter.last_reading.as_ref().map(|r| r.energy_generated * 4.0).unwrap_or(0.0);
        
        total_load += current_load;
        total_gen += current_gen;
        
        let has_battery = meter.battery_capacity > 0.0;
        let has_solar = meter.solar_capacity > 0.0;
        
        if has_battery {
            meters_with_battery += 1;
            available_battery += meter.battery_capacity * meter.battery_level / 100.0;
        }
        if has_solar {
            meters_with_solar += 1;
        }
        
        meter_data.push(serde_json::json!({
            "meter_id": meter.meter_id,
            "zone_id": meter.zone_id,
            "current_load_kw": round_to(current_load, 2),
            "current_gen_kw": round_to(current_gen, 2),
            "has_battery": has_battery,
            "has_solar": has_solar,
            "battery_capacity": meter.battery_capacity,
            "battery_level": meter.battery_level,
            "solar_capacity": meter.solar_capacity
        }));
    }
    
    HttpResponse::Ok().json(serde_json::json!({
        "meters": meter_data,
        "summary": {
            "total_load_mw": round_to(total_load / 1000.0, 4),
            "total_gen_mw": round_to(total_gen / 1000.0, 4),
            "meters_with_battery": meters_with_battery,
            "meters_with_solar": meters_with_solar,
            "available_battery_kwh": round_to(available_battery, 2)
        }
    }))
}

/// Dispatch battery command
async fn dispatch_battery(
    state: web::Data<Arc<AppState>>,
    req: web::Json<BatteryDispatchRequest>,
) -> HttpResponse {
    let mut meters = state.meters.write().unwrap();
    
    if let Some(meter) = meters.get_mut(&req.meter_id) {
        if meter.battery_capacity <= 0.0 {
            return HttpResponse::BadRequest().json(ErrorResponse::new(
                format!("Meter {} does not have a battery", req.meter_id)
            ));
        }
        
        // Apply dispatch (simplified)
        let power_pct = req.power_kw / meter.battery_capacity * 100.0;
        if req.power_kw > 0.0 {
            // Discharge
            meter.battery_level = (meter.battery_level - power_pct.abs()).max(0.0);
        } else {
            // Charge
            meter.battery_level = (meter.battery_level + power_pct.abs()).min(100.0);
        }
        
        let action = if req.power_kw > 0.0 { "discharge" } else { "charge" };
        
        HttpResponse::Ok().json(BatteryDispatchResponse {
            success: true,
            meter_id: req.meter_id.clone(),
            power_kw: req.power_kw,
            new_battery_level: Some(meter.battery_level),
            message: format!("Battery {} command sent", action),
        })
    } else {
        HttpResponse::NotFound().json(ErrorResponse::new(format!("Meter {} not found", req.meter_id)))
    }
}

/// Get grid events
async fn get_grid_events(_state: web::Data<Arc<AppState>>) -> HttpResponse {
    // Return empty events for now
    HttpResponse::Ok().json(Vec::<serde_json::Value>::new())
}

/// Grid health check
async fn grid_health(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let meters = state.meters.read().unwrap();
    let is_running = *state.is_running.read().unwrap();
    let sim_time = state.current_sim_time.read().unwrap();
    
    HttpResponse::Ok().json(GridHealthResponse {
        healthy: true,
        meter_count: meters.len() as i32,
        simulation_time: sim_time.map(|t| t.to_rfc3339()),
        model_type: "rust_simulation".to_string(),
    })
}

/// Debug stats
async fn debug_stats(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let meters = state.meters.read().unwrap();
    let zones = state.zones.read().unwrap();
    
    HttpResponse::Ok().json(serde_json::json!({
        "meter_count": meters.len(),
        "zone_summary_count": zones.len(),
        "zones_keys": zones.keys().collect::<Vec<_>>(),
        "has_zoning_service": true,
        "model_type": "rust_simulation"
    }))
}

/// Get Thailand data (for demo)
async fn get_thailand_data(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let zones = state.zones.read().unwrap();
    let meters = state.meters.read().unwrap();
    
    let mut zones_map = HashMap::new();
    for (id, zone) in zones.iter() {
        zones_map.insert(id.to_string(), serde_json::json!({
            "zone_id": zone.zone_id,
            "centroid_lat": zone.centroid_lat,
            "centroid_lon": zone.centroid_lon,
            "meter_count": zone.meter_ids.len(),
            "transformer_name": format!("TR-{}", zone.zone_id)
        }));
    }
    
    let meter_list: Vec<serde_json::Value> = meters.values()
        .filter(|m| m.latitude.is_some() && m.longitude.is_some())
        .map(|m| serde_json::json!({
            "meter_id": m.meter_id,
            "latitude": m.latitude,
            "longitude": m.longitude,
            "zone_id": m.zone_id,
            "meter_type": m.meter_type,
            "contract_capacity": 15,
            "building_area": 500
        }))
        .collect();
    
    HttpResponse::Ok().json(serde_json::json!({
        "region": "Phaya Thai, Bangkok",
        "stats": {
            "total_meters": meter_list.len(),
            "total_transformers": zones.len()
        },
        "zones": zones_map,
        "meters": meter_list
    }))
}

fn round_to(value: f64, decimals: i32) -> f64 {
    let factor = 10_f64.powi(decimals);
    (value * factor).round() / factor
}
