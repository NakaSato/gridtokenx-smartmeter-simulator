#!/usr/bin/env python3
"""
FastAPI Application for Smart Meter Simulator
Provides REST API endpoints and WebSocket support with HTML rendering
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from smart_meter_simulator.core import app_state
from smart_meter_simulator.lifespan import lifespan
from smart_meter_simulator.utils.telemetry import setup_telemetry
from smart_meter_simulator.routers.api_v1 import router as api_v1_router
from smart_meter_simulator.routers.power_plants_v1 import router as power_plants_router
from smart_meter_simulator.routers.forecast_v1 import forecast_router, optimize_router, ews_router

# Initialize Telemetry (OTEL + Logging)
otel_active = setup_telemetry("gridtokenx-smartmeter-simulator")

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Smart Meter Simulator",
        description="P2P Energy Trading Meter Simulator (Modular)",
        version="3.0.0",
        lifespan=lifespan
    )

    if otel_active:
        FastAPIInstrumentor().instrument_app(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static Assets setup
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
    UI_DIST_DIR = os.path.join(PROJECT_ROOT, "ui", "dist")

    if os.path.exists(UI_DIST_DIR):
        app.mount("/assets", StaticFiles(directory=os.path.join(UI_DIST_DIR, "assets")), name="ui-assets")

    # Register Routers
    app.include_router(api_v1_router)
    app.include_router(power_plants_router)
    app.include_router(forecast_router, prefix="/api/v1")
    app.include_router(optimize_router, prefix="/api/v1")
    app.include_router(ews_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        from datetime import datetime
        return {"status": "ok", "timestamp": datetime.now().isoformat()}

    # Prometheus metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi import Response
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Exception Handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        if request.url.path.startswith("/api"):
            return JSONResponse(content={"detail": "Not Found", "path": request.url.path}, status_code=404)
        
        index_path = os.path.join(UI_DIST_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, status_code=404)
        return HTMLResponse(content="<h1>404 - Not Found</h1>", status_code=404)

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc: HTTPException):
        if request.url.path.startswith("/api"):
            return JSONResponse(content={"detail": "Internal Server Error"}, status_code=500)
        
        index_path = os.path.join(UI_DIST_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, status_code=500)
        return HTMLResponse(content="<h1>500 - Server Error</h1>", status_code=500)

    # WebSocket for live dashboard
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await app_state.websocket_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await app_state.websocket_manager.disconnect(websocket)

    # Catch-all for SPA routing
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def catch_all(full_path: str, request: Request):
        if request.url.path.startswith("/api") or request.url.path in ["/health", "/metrics", "/ws"]:
            return JSONResponse(content={"detail": "Not Found", "path": request.url.path}, status_code=404)
        
        index_path = os.path.join(UI_DIST_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)

    return app

app = create_app()

def main():
    port = int(os.getenv("PORT", 8082))
    uvicorn.run("smart_meter_simulator.app:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()
