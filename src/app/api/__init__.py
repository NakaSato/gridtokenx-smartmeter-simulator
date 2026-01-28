"""
API routes for the Smart Meter Simulator.
"""

from fastapi import FastAPI
from .meters import router as meters_router
from .simulation import router as simulation_router
from .grid import router as grid_router
from .p2p import router as p2p_router

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
    # Grid topology endpoints
    app.include_router(grid_router, prefix="/api", tags=["grid"])
    app.include_router(p2p_router, prefix="/api", tags=["p2p"])

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

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            container = get_container()
            return {
                "status": "healthy",
                "version": "2.0.0",
                "container_status": "configured",
                "services": list(container._services.keys()),
            }
        except Exception:
            return {"status": "unhealthy"}

    # Serve static files
    import os
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
    from fastapi import Request
    from fastapi.templating import Jinja2Templates

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

    if not os.path.exists(static_dir):
        print(f"Warning: Static directory not found at {static_dir}")
    else:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Initialize templates
    templates = Jinja2Templates(directory=templates_dir)

    # Define specific routes first (these take priority)
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        # Detect development mode
        dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        
        manifest = {}
        if not dev_mode:
            try:
                manifest_path = os.path.join(static_dir, ".vite", "manifest.json")
                if os.path.exists(manifest_path):
                    import json
                    with open(manifest_path, "r") as f:
                        manifest_data = json.load(f)
                        if "index.html" in manifest_data:
                            entry = manifest_data["index.html"]
                            manifest["main.js"] = entry["file"]
                            if "css" in entry and entry["css"]:
                                manifest["main.css"] = entry["css"][0]
            except Exception as e:
                print(f"Error loading manifest: {e}")

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "dev_mode": dev_mode,
                "manifest": manifest,
            },
        )

    @app.get("/how-it-works", response_class=HTMLResponse)
    async def read_how_it_works(request: Request):
        return templates.TemplateResponse(
            "how_it_works.html",
            {"request": request, "title": "How It Works - Smart Meter Simulator"},
        )

    @app.get("/maps", response_class=HTMLResponse)
    async def maps_page(request: Request):
        """Interactive map view of smart meters"""
        return templates.TemplateResponse(
            "maps.html",
            {"request": request, "title": "Smart Meter Map - GridTokenX"},
        )

    @app.get("/thailand-demo", response_class=HTMLResponse)
    async def thailand_demo_page(request: Request):
        """Thailand GIS Data Demo Page"""
        return templates.TemplateResponse(
            "thailand_demo.html",
            {"request": request, "title": "Thailand Smart Grid Demo (Phaya Thai)"},
        )

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

    # Serve static assets (js, css, images, etc.) - catch-all route AFTER specific routes
    # This matches Vite's build output with base: '/'
    @app.get("/{full_path:path}")
    async def serve_static_assets(full_path: str):
        print(f"DEBUG: Catch-all received path: {full_path}")
        file_path = os.path.join(static_dir, full_path)
        
        # Prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(static_dir)):
            return HTMLResponse(content="Access denied", status_code=403)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        return HTMLResponse(content="Not found", status_code=404)

    for route in app.routes:
        print(f"DEBUG: Route: {route.path} {route.name}")
        
    return app
