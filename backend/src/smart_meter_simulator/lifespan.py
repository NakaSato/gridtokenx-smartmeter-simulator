"""FastAPI lifespan for the GLM grid simulator."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from smart_meter_simulator.config import get_config
from smart_meter_simulator.core import app_state
from smart_meter_simulator.core.engine import SimulationEngine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    logger.info(
        "Initializing GLM grid simulator with topology %s", config.grid_topology
    )

    app_state.engine = SimulationEngine(grid_topology=config.grid_topology)
    if config.autostart_simulation:
        await app_state.engine.start()
    else:
        app_state.engine.grid.initialize_network(app_state.engine.meters)
        app_state.engine.paused = True

    try:
        yield
    finally:
        if app_state.engine:
            await app_state.engine.stop()
        app_state.engine = None
        logger.info("GLM grid simulator shutdown complete")
