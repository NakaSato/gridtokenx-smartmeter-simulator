//! Simulation control API routes

use actix_web::{web, HttpResponse, Scope};
use std::sync::Arc;
use std::time::Instant;
use chrono::Utc;

use crate::models::*;
use crate::state::AppState;

/// Configure simulation routes
pub fn configure() -> Scope {
    web::scope("/simulation")
        .route("/status", web::get().to(get_status))
        .route("/start", web::post().to(start_simulation))
        .route("/stop", web::post().to(stop_simulation))
        .route("/pause", web::post().to(pause_simulation))
        .route("/resume", web::post().to(resume_simulation))
        .route("/restart", web::post().to(restart_simulation))
        .route("/parameters", web::get().to(get_parameters))
        .route("/parameters", web::post().to(update_parameters))
}

/// Get simulation status
async fn get_status(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let is_running = *state.is_running.read().unwrap();
    let is_paused = *state.is_paused.read().unwrap();
    let tick_count = *state.tick_count.read().unwrap();
    let start_time = *state.start_time.read().unwrap();
    let current_time = *state.current_sim_time.read().unwrap();
    let meters = state.meters.read().unwrap();
    
    let uptime = start_time
        .map(|s| (Utc::now() - s).num_seconds() as f64)
        .unwrap_or(0.0);
    
    HttpResponse::Ok().json(SimulationStatusResponse {
        is_running,
        is_paused,
        current_time: current_time.map(|t| t.to_rfc3339()),
        meter_count: meters.len() as i32,
        tick_count,
        uptime_seconds: uptime,
    })
}

/// Start simulation
async fn start_simulation(state: web::Data<Arc<AppState>>) -> HttpResponse {
    {
        let mut is_running = state.is_running.write().unwrap();
        let mut is_paused = state.is_paused.write().unwrap();
        let mut start_time = state.start_time.write().unwrap();
        let mut current_time = state.current_sim_time.write().unwrap();
        
        if *is_running {
            return HttpResponse::Ok().json(serde_json::json!({
                "success": false,
                "message": "Simulation is already running"
            }));
        }
        
        *is_running = true;
        *is_paused = false;
        *start_time = Some(Utc::now());
        *current_time = Some(Utc::now());
    }
    
    // Generate initial readings for all meters
    {
        let mut meters = state.meters.write().unwrap();
        for meter in meters.values_mut() {
            meter.generate_reading();
        }
    }
    
    let meters = state.meters.read().unwrap();
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "message": "Simulation started",
        "status": {
            "is_running": true,
            "meter_count": meters.len(),
            "start_time": Utc::now().to_rfc3339()
        }
    }))
}

/// Stop simulation
async fn stop_simulation(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let mut is_running = state.is_running.write().unwrap();
    let mut is_paused = state.is_paused.write().unwrap();
    let mut tick_count = state.tick_count.write().unwrap();
    
    if !*is_running {
        return HttpResponse::Ok().json(serde_json::json!({
            "success": false,
            "message": "Simulation is not running"
        }));
    }
    
    *is_running = false;
    *is_paused = false;
    *tick_count = 0;
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "message": "Simulation stopped"
    }))
}

/// Pause simulation
async fn pause_simulation(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let is_running = *state.is_running.read().unwrap();
    let mut is_paused = state.is_paused.write().unwrap();
    
    if !is_running {
        return HttpResponse::Ok().json(serde_json::json!({
            "success": false,
            "message": "Simulation is not running"
        }));
    }
    
    if *is_paused {
        return HttpResponse::Ok().json(serde_json::json!({
            "success": false,
            "message": "Simulation is already paused"
        }));
    }
    
    *is_paused = true;
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "message": "Simulation paused"
    }))
}

/// Resume simulation
async fn resume_simulation(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let is_running = *state.is_running.read().unwrap();
    let mut is_paused = state.is_paused.write().unwrap();
    
    if !is_running {
        return HttpResponse::Ok().json(serde_json::json!({
            "success": false,
            "message": "Simulation is not running"
        }));
    }
    
    if !*is_paused {
        return HttpResponse::Ok().json(serde_json::json!({
            "success": false,
            "message": "Simulation is not paused"
        }));
    }
    
    *is_paused = false;
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "message": "Simulation resumed"
    }))
}

/// Restart simulation
async fn restart_simulation(state: web::Data<Arc<AppState>>) -> HttpResponse {
    // Stop first
    {
        let mut is_running = state.is_running.write().unwrap();
        let mut is_paused = state.is_paused.write().unwrap();
        let mut tick_count = state.tick_count.write().unwrap();
        
        *is_running = false;
        *is_paused = false;
        *tick_count = 0;
    }
    
    // Small delay
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    // Start again
    {
        let mut is_running = state.is_running.write().unwrap();
        let mut start_time = state.start_time.write().unwrap();
        let mut current_time = state.current_sim_time.write().unwrap();
        
        *is_running = true;
        *start_time = Some(Utc::now());
        *current_time = Some(Utc::now());
    }
    
    // Generate new readings
    {
        let mut meters = state.meters.write().unwrap();
        for meter in meters.values_mut() {
            meter.generate_reading();
        }
    }
    
    let meters = state.meters.read().unwrap();
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "message": "Simulation restarted",
        "status": {
            "is_running": true,
            "meter_count": meters.len()
        }
    }))
}

/// Get simulation parameters
async fn get_parameters(state: web::Data<Arc<AppState>>) -> HttpResponse {
    let params = state.parameters.read().unwrap();
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "parameters": *params
    }))
}

/// Update simulation parameters
async fn update_parameters(
    state: web::Data<Arc<AppState>>,
    req: web::Json<SimulationParameters>,
) -> HttpResponse {
    let mut params = state.parameters.write().unwrap();
    *params = req.into_inner();
    
    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "message": "Simulation parameters updated",
        "parameters": *params
    }))
}
