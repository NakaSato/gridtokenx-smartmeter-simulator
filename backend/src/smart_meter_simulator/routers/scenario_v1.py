"""
Scenario Management REST API.

Provides endpoints for listing, inspecting, and running TESP-inspired
simulation scenarios.

Endpoints:
    GET  /api/v1/scenarios              — List available scenarios
    GET  /api/v1/scenarios/{name}       — Get scenario details
    POST /api/v1/scenarios/{name}/run   — Apply and run a scenario
    POST /api/v1/scenarios/stop         — Stop current scenario
    GET  /api/v1/scenarios/status       — Current scenario status
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


@router.get("")
async def list_scenarios() -> Dict[str, str]:
    """List all available simulation scenarios.

    Returns a dict mapping scenario name to description.
    """
    from ..core.scenario_runner import list_scenarios as _list
    return _list()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get the current scenario status."""
    runner = _get_runner()
    return runner.get_status()


@router.get("/{name}")
async def get_scenario(name: str) -> Dict[str, Any]:
    """Get detailed information about a specific scenario.

    Args:
        name: Scenario name (e.g., "loadshed_standalone").
    """
    from ..core.scenario_runner import get_scenario as _get
    config = _get(name)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")

    return {
        "name": config.name,
        "description": config.description,
        "grid_topology": config.grid_topology,
        "meter_count": config.meter_count,
        "duration_hours": config.duration_hours,
        "simulation_interval": config.simulation_interval,
        "market": {
            "enabled": config.market.enabled,
            "type": config.market.market_type,
            "price_cap": config.market.price_cap,
        },
        "helics": {
            "enabled": config.helics.enabled,
            "federate_name": config.helics.federate_name,
        },
        "gridlabd": {
            "enabled": config.gridlabd.enabled,
            "mode": config.gridlabd.mode,
        },
        "tags": config.tags,
    }


@router.post("/{name}/run")
async def run_scenario(name: str) -> Dict[str, str]:
    """Apply a scenario configuration and start the simulation.

    This sets the scenario parameters as environment variables and
    triggers a simulation restart with the new configuration.

    Args:
        name: Scenario name to run.
    """
    from ..core.scenario_runner import get_scenario as _get
    config = _get(name)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")

    runner = _get_runner()
    runner.apply(config)

    logger.info(f"Scenario '{name}' applied — simulation will restart with new config")
    return {
        "status": "applied",
        "scenario": name,
        "message": (
            "Scenario configuration applied. Restart the simulator "
            "to run with the new settings."
        ),
    }


@router.post("/stop")
async def stop_scenario() -> Dict[str, str]:
    """Stop the current scenario and reset to defaults."""
    runner = _get_runner()
    runner._current_scenario = None
    return {"status": "stopped", "message": "Scenario reset to defaults"}


# ── Module-level runner singleton ────────────────────────────────────────

_runner: Any = None


def _get_runner():
    """Get or create the module-level ScenarioRunner singleton."""
    global _runner
    if _runner is None:
        from ..core.scenario_runner import ScenarioRunner
        _runner = ScenarioRunner()
    return _runner
