//! SmartMeter API Server
//!
//! High-performance REST API server built with Actix-web

mod models;
mod state;
mod routes;

use actix_cors::Cors;
use actix_web::{web, App, HttpResponse, HttpServer, middleware};
use std::sync::Arc;
use log::info;

use state::AppState;

/// Health check endpoint
async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "service": "smartmeter-api",
        "version": env!("CARGO_PKG_VERSION")
    }))
}

/// Root endpoint
async fn index() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({
        "service": "SmartMeter Simulator API",
        "version": env!("CARGO_PKG_VERSION"),
        "endpoints": {
            "health": "/health",
            "meters": "/api/meters",
            "grid": "/api/grid",
            "simulation": "/api/simulation",
            "p2p": "/api/v1/p2p"
        }
    }))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize logger
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));
    
    // Get port from env or default
    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8000);
    
    let host = std::env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    
    info!("Starting SmartMeter API server on {}:{}", host, port);
    
    // Create shared application state
    let app_state = Arc::new(AppState::new());
    
    // Initialize with default meters
    app_state.init_default_meters();
    info!("Initialized {} default meters", app_state.meters.read().unwrap().len());
    
    // Clone for background task
    let state_for_tick = app_state.clone();
    
    // Spawn background tick task
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(5));
        loop {
            interval.tick().await;
            
            let is_running = *state_for_tick.is_running.read().unwrap();
            let is_paused = *state_for_tick.is_paused.read().unwrap();
            
            if is_running && !is_paused {
                // Update tick count
                {
                    let mut tick = state_for_tick.tick_count.write().unwrap();
                    *tick += 1;
                }
                
                // Update simulation time
                {
                    let mut sim_time = state_for_tick.current_sim_time.write().unwrap();
                    *sim_time = Some(chrono::Utc::now());
                }
                
                // Generate readings for all meters
                {
                    let mut meters = state_for_tick.meters.write().unwrap();
                    for meter in meters.values_mut() {
                        if meter.is_connected {
                            meter.generate_reading();
                        }
                    }
                }
            }
        }
    });
    
    // Start HTTP server
    HttpServer::new(move || {
        // Configure CORS
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);
        
        App::new()
            .app_data(web::Data::new(app_state.clone()))
            .wrap(cors)
            .wrap(middleware::Logger::default())
            .wrap(middleware::Compress::default())
            // Root routes
            .route("/", web::get().to(index))
            .route("/health", web::get().to(health_check))
            // API routes
            .service(
                web::scope("/api")
                    .service(routes::meters::configure())
                    .service(routes::grid::configure())
                    .service(routes::simulation::configure())
                    .service(routes::p2p::configure())
            )
    })
    .bind((host.as_str(), port))?
    .run()
    .await
}
