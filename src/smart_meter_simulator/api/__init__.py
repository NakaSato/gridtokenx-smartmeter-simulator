"""
API routes for the Smart Meter Simulator.
"""

from fastapi import FastAPI
from .meters import router as meters_router
from .simulation import router as simulation_router

__all__ = [
    "meters_router",
    "simulation_router",
    "create_app",
]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Smart Meter Simulator API",
        description="API for smart meter simulation and management",
        version="2.0.0",
    )

    # Include routers
    # Mount at paths expected by dashboard.js
    app.include_router(meters_router, prefix="/api/meters", tags=["meters"])
    app.include_router(simulation_router, prefix="/api/control", tags=["simulation"])

    # Add /api/status endpoint which dashboard expects
    from ..services.simulation_service import SimulationService
    from ..container import get_container

    @app.get("/api/status")
    async def get_api_status():
        try:
            container = get_container()
            if container.has(SimulationService):
                sim_service = container.get(SimulationService)
                return sim_service.get_simulation_status()
            return {"error": "Simulation service not available"}
        except Exception as e:
            return {"error": str(e)}

    # Serve static files
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse

    # Determine paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 2 levels to get to src (src/smart_meter_simulator/api -> src/smart_meter_simulator -> src)
    src_dir = os.path.dirname(os.path.dirname(current_dir))
    # Go up one more level to get to project root
    root_dir = os.path.dirname(src_dir)

    # Templates and static are in src/
    templates_dir = os.path.join(src_dir, "templates")
    static_dir = os.path.join(src_dir, "static")

    # Fallback to root level if not found in src
    if not os.path.exists(templates_dir):
        templates_dir = os.path.join(root_dir, "templates")
    if not os.path.exists(static_dir):
        static_dir = os.path.join(root_dir, "static")

    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    else:
        print(f"Warning: Static directory not found at {static_dir}")

    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        dashboard_path = os.path.join(templates_dir, "dashboard.html")
        if os.path.exists(dashboard_path):
            with open(dashboard_path, "r") as f:
                return f.read()
        return HTMLResponse(content="Dashboard not found", status_code=404)

    @app.get("/how-it-works", response_class=HTMLResponse)
    async def read_how_it_works():
        page_path = os.path.join(templates_dir, "how_it_works.html")
        if os.path.exists(page_path):
            with open(page_path, "r") as f:
                return f.read()
        return HTMLResponse(content="Page not found", status_code=404)

    # WebSocket endpoint
    from fastapi import WebSocket, WebSocketDisconnect

    from ..transport.websocket import WebSocketManager

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        container = get_container()
        if not container.has(WebSocketManager):
            await websocket.close(code=1000, reason="WebSocket support not enabled")
            return

        ws_manager = container.get(WebSocketManager)
        await ws_manager.connect(websocket)

        try:
            while True:
                # Keep connection alive and handle incoming messages if needed
                # For now we just listen but don't process incoming messages
                await websocket.receive_text()
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
        except Exception:
            await ws_manager.disconnect(websocket)

    return app
