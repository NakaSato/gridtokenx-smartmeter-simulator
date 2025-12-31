"""
API routes for the Smart Meter Simulator.
"""

from fastapi import FastAPI
from .meters import router as meters_router
from .simulation import router as simulation_router
from .p2p import router as p2p_router
from .grid import router as grid_router

__all__ = [
    "meters_router",
    "simulation_router",
    "p2p_router",
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
    # P2P trading endpoints (already has prefix /api/v1/p2p in the router)
    app.include_router(p2p_router)
    # Grid topology endpoints
    app.include_router(grid_router, prefix="/api", tags=["grid"])

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
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

    # Determine paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 2 levels to get to src (src/smart_meter_simulator/api -> src/smart_meter_simulator -> src)
    src_dir = os.path.dirname(os.path.dirname(current_dir))
    # Go up one more level to get to project root
    root_dir = os.path.dirname(src_dir)

    # Templates and static are in src/
    # Templates and static are in src/
    templates_dir = os.path.join(src_dir, "templates")
    
    # Use built static files from dist/static
    static_dir = os.path.join(root_dir, "dist", "static")

    # Fallback to root level if not found in src (only for templates)
    if not os.path.exists(templates_dir):
        templates_dir = os.path.join(root_dir, "templates")
    # if static_dir/dist doesn't exist, maybe fallback to src/static? 
    # Method to debug paths
    print(f"DEBUG: Current dir: {current_dir}")
    print(f"DEBUG: Src dir: {src_dir}")
    print(f"DEBUG: Root dir: {root_dir}")
    print(f"DEBUG: Templates dir: {templates_dir} (Exists: {os.path.exists(templates_dir)})")
    print(f"DEBUG: Static dir definition: {static_dir}")
    
    if not os.path.exists(static_dir):
         print(f"DEBUG: Static dir {static_dir} not found, falling back to src/static")
         static_dir = os.path.join(src_dir, "static")
    
    print(f"DEBUG: Final Static dir: {static_dir} (Exists: {os.path.exists(static_dir)})")
    
    try:
        import aiofiles
        print("DEBUG: aiofiles is importable")
    except ImportError:
        print("DEBUG: aiofiles is NOT importable")

    

    @app.get("/static/css/main.css")
    async def serve_main_css():
        full_path = os.path.join(static_dir, "css", "main.css")
        if os.path.exists(full_path):
            return FileResponse(full_path)
        return HTMLResponse(content="Not Found", status_code=404)


    @app.get("/static/{file_path:path}")
    async def serve_static(file_path: str):
        full_path = os.path.join(static_dir, file_path)
        # Prevent directory traversal
        if not os.path.abspath(full_path).startswith(os.path.abspath(static_dir)):
            return HTMLResponse(content="Access denied", status_code=403)
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(full_path)
        
        return HTMLResponse(content=f"File not found: {full_path}", status_code=404)
        
    if not os.path.exists(static_dir):
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

    for route in app.routes:
        print(f"DEBUG: Route: {route.path} {route.name}")
        
    return app
