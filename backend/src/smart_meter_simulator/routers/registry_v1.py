"""
Registry API v1 Router

Thailand power plant registry endpoints:
- /api/v1/registry/thailand/plants       - List/search power plants
- /api/v1/registry/thailand/plants/stats - Aggregate statistics
- /api/v1/registry/thailand/plants/nearby - Geographic search
- /api/v1/registry/thailand/plants/{id}  - Plant details
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

logger = __import__("logging").getLogger(__name__)

router = APIRouter(prefix="", tags=["Registry"])


# ============================================================================
# Registry (Thailand Power Plants)
# ============================================================================


@router.get("/registry/thailand/plants")
async def list_thailand_plants(
    fuel: Optional[str] = Query(None, description="Filter by fuel type"),
    region: Optional[str] = Query(None, description="Filter by region"),
    status: Optional[str] = Query(None, description="Filter by status"),
    group_by: Optional[str] = Query(None, description="Group results by: fuel, region"),
    limit: int = Query(100),
    search: Optional[str] = Query(None, description="Search by name"),
):
    """List Thailand power plants with optional filters."""
    from smart_meter_simulator.core.power_plants import (
        FuelType,
        PlantRegion,
        get_registry,
    )

    registry = get_registry()

    if search:
        plants = registry.search(search)
    else:
        fuel_enum = FuelType(fuel) if fuel else None
        region_enum = PlantRegion(region) if region else None
        plants = registry.list_all(
            fuel=fuel_enum,
            region=region_enum,
            status=status,
            limit=limit,
        )

    if group_by:
        return {"grouped_by": group_by, "data": registry.group_by(group_by)}

    return {
        "plants": [registry._to_dict(p) for p in plants],
        "total": len(plants),
    }


@router.get("/registry/thailand/plants/stats")
async def thailand_plants_stats():
    """Get Thailand power plant statistics."""
    from smart_meter_simulator.core.power_plants import get_registry

    return get_registry().stats()


@router.get("/registry/thailand/plants/nearby")
async def nearby_plants(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50.0, gt=0),
):
    """Find power plants near coordinates."""
    from smart_meter_simulator.core.power_plants import get_registry

    registry = get_registry()
    plants = registry.nearby(lat, lon, radius_km)
    return {
        "plants": [registry._to_dict(p) for p in plants],
        "total": len(plants),
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
    }


@router.get("/registry/thailand/plants/{plant_id}")
async def get_thailand_plant(plant_id: str):
    """Get Thailand power plant details."""
    from smart_meter_simulator.core.power_plants import get_registry

    registry = get_registry()
    plant = registry.get_by_id(plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")
    return registry._to_dict(plant)
