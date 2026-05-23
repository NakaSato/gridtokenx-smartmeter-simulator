"""
Power Plant API Router

Endpoints for managing Thailand power plants in PostGIS database.
Supports loading from GeoJSON, querying, filtering, and spatial searches.
"""

import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/power-plants", tags=["Power Plants"])


# ============================================================================
# Dependency: Get Repository
# ============================================================================


async def get_repository():
    """Get PostGIS repository instance."""
    try:
        from smart_meter_simulator.database.repository import PostGISRepository
        from smart_meter_simulator.config import get_config

        config = get_config()
        db_url = getattr(config, "gis_database_url", None) or getattr(
            config, "database_url", None
        )
        if db_url:
            return PostGISRepository(db_url)
    except Exception:
        pass
    # No DB available — return None, endpoints will use fallback
    return None


# ============================================================================
# Pydantic Models
# ============================================================================


class PowerPlantCreate(BaseModel):
    plant_id: str
    name: str
    name_th: Optional[str] = None
    plant_type: str
    fuel_type: Optional[str] = None
    technology: Optional[str] = None
    capacity_mw: float
    units: int = 1
    status: str = "operating"
    start_year: Optional[int] = None
    operator: str = "EGAT"
    latitude: float
    longitude: float
    province: Optional[str] = None
    region: Optional[str] = None
    voltage_level_kv: Optional[float] = None
    grid_connection_type: Optional[str] = None
    carbon_intensity_gco2_kwh: Optional[float] = None
    source: Optional[str] = "API Import"
    osm_id: Optional[int] = None


class PowerPlantResponse(BaseModel):
    id: int
    plant_id: str
    name: str
    plant_type: str
    capacity_mw: float
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_renewable: bool


class PowerPlantDetail(BaseModel):
    id: int
    plant_id: str
    name: str
    name_th: Optional[str] = None
    plant_type: str
    fuel_type: Optional[str] = None
    technology: Optional[str] = None
    capacity_mw: float
    units: int
    status: str
    start_year: Optional[int] = None
    operator: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    province: Optional[str] = None
    region: Optional[str] = None
    voltage_level_kv: Optional[float] = None
    grid_connection_type: Optional[str] = None
    is_renewable: bool
    carbon_intensity_gco2_kwh: Optional[float] = None
    source: Optional[str] = None


class BatchImportResponse(BaseModel):
    created: int
    errors: int
    error_details: List[str] = []


def _sanitize_plant(plant: dict) -> dict:
    """Redact location info for sensitive power plant tags."""
    plant_id = str(plant.get("plant_id", ""))
    plant_name = str(plant.get("name", ""))

    if plant_id.startswith("EGAT-TWR-") or plant_name.startswith("EGAT-TWR-"):
        # Redact location fields
        if "province" in plant:
            plant["province"] = "REDACTED"
        if "region" in plant:
            plant["region"] = "REDACTED"
        if "district" in plant:
            plant["district"] = "REDACTED"
        # Optional: Redact lat/lon if needed for list view
        # plant["latitude"] = None
        # plant["longitude"] = None
    return plant


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/import", response_model=BatchImportResponse)
async def import_power_plants_geojson(
    file: UploadFile = File(..., description="GeoJSON file with power plants"),
    repo=Depends(get_repository),
):
    """Import power plants from GeoJSON file."""
    try:
        content = await file.read()
        geojson = json.loads(content)

        if geojson.get("type") != "FeatureCollection":
            raise HTTPException(
                status_code=400, detail="Expected GeoJSON FeatureCollection"
            )

        plants_data = []
        for idx, feature in enumerate(geojson.get("features", [])):
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])

            if len(coords) < 2:
                continue

            # Support both OSM-style keys (Type, Capacity (MW)) and direct keys (plant_type, capacity_mw)
            plant_type_raw = (
                (
                    props.get("Type")
                    or props.get("plant_type")
                    or props.get("source")
                    or "unknown"
                )
                .lower()
                .replace(" ", "_")
            )

            capacity = (
                props.get("Capacity (MW)")
                or props.get("capacity_mw")
                or props.get("output_mw")
                or 0
            )
            # Convert string capacity to float
            try:
                capacity = float(capacity) if capacity else 0.0
            except (ValueError, TypeError):
                capacity = 0.0

            name = (
                props.get("Plant / Project name") or props.get("name") or f"Plant_{idx}"
            )

            plant_id = f"TH_{plant_type_raw.upper()[:10]}_{idx:04d}"

            plant_data = {
                "plant_id": plant_id,
                "name": str(name),
                "plant_type": plant_type_raw,
                "capacity_mw": capacity,
                "status": props.get("Status", "operating"),
                "technology": props.get("Technology") or props.get("method"),
                "fuel_type": props.get("Fuel") or props.get("source"),
                "start_year": props.get("Start year"),
                "operator": props.get("Operator") or props.get("operator") or "EGAT",
                "latitude": coords[1],
                "longitude": coords[0],
                "source": "GeoJSON Import",
            }

            plants_data.append(plant_data)

        if not plants_data:
            return BatchImportResponse(
                created=0, errors=0, error_details=["No valid features found"]
            )

        try:
            result = await repo.create_power_plants_batch(plants_data)
            logger.info(f"Imported {result['created']} plants from GeoJSON")
            return result
        except Exception as db_err:
            logger.warning(f"DB import failed: {db_err}")
            # Save to file as fallback
            import os

            os.makedirs("/tmp/power_plants", exist_ok=True)
            filepath = "/tmp/power_plants/imported.geojson"
            with open(filepath, "w") as f:
                json.dump(geojson, f, indent=2)
            return BatchImportResponse(
                created=len(plants_data),
                errors=0,
                error_details=[
                    f"DB unavailable. {len(plants_data)} plants saved to {filepath}"
                ],
            )

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON: {str(e)}")
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/", response_model=PowerPlantDetail)
async def create_power_plant(plant: PowerPlantCreate, repo=Depends(get_repository)):
    """Create a single power plant record"""
    try:
        plant_data = plant.model_dump()
        result = await repo.create_power_plant(plant_data)
        full_details = await repo.get_power_plant(result["plant_id"])
        return full_details
    except Exception as e:
        if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409, detail=f"Plant {plant.plant_id} already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=dict)
async def list_power_plants(
    plant_type: Optional[str] = Query(None, description="Filter by plant type"),
    status: Optional[str] = Query("operating", description="Filter by status"),
    region: Optional[str] = Query(None, description="Filter by region"),
    operator: Optional[str] = Query(None, description="Filter by operator"),
    renewable_only: bool = Query(False, description="Show only renewable plants"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    repo=Depends(get_repository),
):
    """List power plants with filtering and pagination"""
    # Fallback: read from saved file when DB unavailable
    import os

    filepath = "/tmp/power_plants/imported.geojson"

    if repo is None or not os.path.exists(filepath):
        if os.path.exists(filepath):
            with open(filepath) as f:
                geojson = json.load(f)
            renewable_sources = {
                "solar",
                "wind",
                "hydro",
                "biofuel",
                "biogas",
                "biomass",
                "geothermal",
            }
            plants = []
            for idx, feat in enumerate(geojson.get("features", [])):
                p = feat.get("properties", {})
                coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                src = (
                    p.get("Type") or p.get("plant_type") or p.get("source") or "unknown"
                )
                if renewable_only and src not in renewable_sources:
                    continue
                if plant_type and src != plant_type:
                    continue
                cap = (
                    p.get("Capacity (MW)")
                    or p.get("capacity_mw")
                    or p.get("output_mw")
                    or 0
                )
                try:
                    cap = float(cap) if cap else 0.0
                except (ValueError, TypeError):
                    cap = 0.0
                plants.append(
                    {
                        "id": idx,
                        "plant_id": f"TH_{src.upper()[:10]}_{idx:04d}",
                        "name": p.get("Plant / Project name")
                        or p.get("name")
                        or f"Plant_{idx}",
                        "plant_type": src,
                        "capacity_mw": cap,
                        "status": p.get("Status", "operating"),
                        "latitude": coords[1],
                        "longitude": coords[0],
                        "is_renewable": src in renewable_sources,
                    }
                )
            return {
                "plants": plants[offset : offset + limit],
                "total": len(plants),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < len(plants),
                "_source": "fallback_file",
            }
        raise HTTPException(status_code=500, detail="No plant data available")

    try:
        plants, total = await repo.get_power_plants(
            plant_type=plant_type,
            status=status,
            region=region,
            operator=operator,
            renewable_only=renewable_only,
            limit=limit,
            offset=offset,
        )
        return {
            "plants": [_sanitize_plant(p) for p in plants],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(plants) < total,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_plant_statistics(repo=Depends(get_repository)):
    """Get aggregate power plant statistics"""
    import os

    filepath = "/tmp/power_plants/imported.geojson"

    # Try DB first, fallback to file
    if repo is not None:
        try:
            stats = await repo.get_power_plant_stats()
            return stats
        except Exception:
            pass  # DB failed, try fallback

    # Fallback: read from saved file
    if os.path.exists(filepath):
        with open(filepath) as f:
            geojson = json.load(f)
        sources = {}
        total_mw = 0
        renewable_mw = 0
        renewable_sources = {
            "solar",
            "wind",
            "hydro",
            "biofuel",
            "biogas",
            "biomass",
            "geothermal",
        }
        for feat in geojson.get("features", []):
            p = feat.get("properties", {})
            src = p.get("Type") or p.get("plant_type") or p.get("source") or "unknown"
            sources[src] = sources.get(src, 0) + 1
            cap = (
                p.get("Capacity (MW)")
                or p.get("capacity_mw")
                or p.get("output_mw")
                or 0
            )
            try:
                cap = float(cap) if cap else 0.0
            except (ValueError, TypeError):
                cap = 0.0
            total_mw += cap
            if src in renewable_sources:
                renewable_mw += cap
        return {
            "total": {
                "count": len(geojson.get("features", [])),
                "capacity_mw": total_mw,
            },
            "renewable": {
                "capacity_mw": renewable_mw,
                "percentage": (renewable_mw / total_mw * 100) if total_mw > 0 else 0,
            },
            "by_type": {
                k: {"plant_count": v, "total_capacity_mw": 0, "avg_capacity_mw": 0}
                for k, v in sources.items()
            },
            "_source": "fallback_file",
        }
    raise HTTPException(
        status_code=404, detail="No plant data available. Import a GeoJSON file first."
    )


@router.get("/search/nearby")
async def search_nearby_plants(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_km: float = Query(50, description="Search radius in km"),
    plant_type: Optional[str] = Query(None, description="Filter by type"),
    status: str = Query("operating", description="Filter by status"),
    repo=Depends(get_repository),
):
    """Find power plants within radius (uses PostGIS spatial query)"""
    try:
        plants = await repo.get_power_plants_near(
            latitude=lat,
            longitude=lon,
            radius_km=radius_km,
            plant_type=plant_type,
            status=status,
        )
        return {
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
            "count": len(plants),
            "plants": [_sanitize_plant(p) for p in plants],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plant_id}", response_model=PowerPlantDetail)
async def get_power_plant(plant_id: str, repo=Depends(get_repository)):
    """Get details for a specific power plant"""
    if repo is None:
        raise HTTPException(status_code=503, detail="Database not available")
    plant = await repo.get_power_plant(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")
    return plant
