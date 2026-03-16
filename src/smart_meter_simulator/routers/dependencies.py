from fastapi import HTTPException
from ..core import app_state

async def get_engine():
    if app_state.engine is None:
        raise HTTPException(status_code=503, detail="Simulator engine not initialized")
    return app_state.engine

async def get_websocket_manager():
    return app_state.websocket_manager

async def get_mapbox_matcher():
    return app_state.mapbox_matcher
