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
    app.include_router(meters_router, prefix="/api/v1/meters", tags=["meters"])
    app.include_router(simulation_router, prefix="/api/v1/simulation", tags=["simulation"])
    
    return app
