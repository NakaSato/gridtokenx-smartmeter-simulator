"""Carbon offset / avoided-emissions endpoints.

Exposes the per-meter carbon model (``emissions.carbon``) over REST: list the
emission factors, quote an offset for arbitrary energy, and aggregate the live
fleet. The per-meter route lives next to the bill in ``meters_v1.py``.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from smart_meter_simulator.emissions import CarbonOffset, compute_offset

router = APIRouter(prefix="/carbon", tags=["Carbon"])


def _config():
    from smart_meter_simulator.config.settings import get_config

    return get_config()


def _get_engine():
    from smart_meter_simulator.core import app_state

    engine = app_state.engine
    if engine is None:
        raise HTTPException(status_code=503, detail="Simulation engine not running")
    return engine


def _offset_to_dict(offset: CarbonOffset) -> dict[str, Any]:
    data = asdict(offset)
    data["unit"] = "kg_co2e"
    return data


def _factors(config) -> dict[str, float]:
    return {
        "grid_intensity": config.carbon_grid_intensity_kgco2_per_kwh,
        "solar_intensity": config.carbon_solar_intensity_kgco2_per_kwh,
        "kg_per_tree_year": config.carbon_kg_per_tree_year,
    }


class OffsetInput(BaseModel):
    """Carbon-offset quote request. Energy in kWh; factors default to config."""

    import_kwh: float = Field(0.0, ge=0)
    export_kwh: float = Field(0.0, ge=0)
    # Optional overrides; default to the configured CARBON_* factors.
    grid_intensity: Optional[float] = Field(None, ge=0)
    solar_intensity: Optional[float] = Field(None, ge=0)


@router.get("/factors")
async def list_factors():
    """List the emission factors used by the carbon model."""
    config = _config()
    return {
        "unit": "kg_co2e_per_kwh",
        **_factors(config),
        "note": (
            "grid_intensity = Thailand grid-average emission factor (TGO); "
            "solar_intensity = IPCC AR5 median rooftop-PV life-cycle intensity; "
            "kg_per_tree_year = US EPA per-tree annual CO2 sequestration."
        ),
    }


@router.post("/quote")
async def quote_offset(data: OffsetInput):
    """Compute the carbon offset for the supplied import / export energy."""
    config = _config()
    factors = _factors(config)
    try:
        offset = compute_offset(
            import_kwh=data.import_kwh,
            export_kwh=data.export_kwh,
            grid_intensity=(
                data.grid_intensity
                if data.grid_intensity is not None
                else factors["grid_intensity"]
            ),
            solar_intensity=(
                data.solar_intensity
                if data.solar_intensity is not None
                else factors["solar_intensity"]
            ),
            kg_per_tree_year=factors["kg_per_tree_year"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _offset_to_dict(offset)


@router.get("/summary")
async def fleet_carbon_summary():
    """Aggregate the live fleet's accumulated import / export into one offset."""
    engine = _get_engine()
    config = _config()
    factors = _factors(config)

    total_import = sum(
        getattr(m, "cumulative_import_kwh", 0.0) for m in engine.meters
    )
    total_export = sum(
        getattr(m, "cumulative_export_kwh", 0.0) for m in engine.meters
    )
    offset = compute_offset(
        import_kwh=total_import,
        export_kwh=total_export,
        grid_intensity=factors["grid_intensity"],
        solar_intensity=factors["solar_intensity"],
        kg_per_tree_year=factors["kg_per_tree_year"],
    )
    data = _offset_to_dict(offset)
    data["meter_count"] = len(engine.meters)
    return data
