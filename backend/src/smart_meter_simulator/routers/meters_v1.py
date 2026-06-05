"""Meter endpoints for the GLM grid model simulator."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="", tags=["Meters"])


def _get_engine():
    from smart_meter_simulator.core import app_state

    engine = app_state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    return engine


def _meter_payload(meter: Any) -> Dict[str, Any]:
    config = getattr(meter, "config", {})
    last_reading = getattr(meter, "last_reading", None)

    return {
        "meter_id": meter.meter_id,
        "meter_type": config.get("meter_type", "unknown"),
        "location_name": config.get("location_name", "Unknown"),
        "latitude": config.get("latitude"),
        "longitude": config.get("longitude"),
        "phase": config.get("phase"),
        "bus_idx": config.get("bus_idx"),
        "node_id": config.get("node_id") or config.get("bus_name"),
        "bus_name": config.get("bus_name") or config.get("node_id"),
        "has_solar": config.get("has_solar", False),
        "solar_capacity": config.get("solar_capacity", 0.0),
        "status": "active",
        # Energy per interval (kWh) — use for billing / carbon / REC math.
        "generation": last_reading.energy_generated if last_reading else 0,
        "consumption": last_reading.energy_consumed if last_reading else 0,
        # Instantaneous average power (kW) — use for display.
        "generation_kw": _to_kw(last_reading, "energy_generated"),
        "consumption_kw": _to_kw(last_reading, "energy_consumed"),
        "voltage": last_reading.voltage if last_reading else 230,
    }


def _to_kw(reading: Any, field: str) -> float:
    """Convert a per-interval energy reading (kWh) back to average power (kW)."""
    if not reading:
        return 0.0
    energy_kwh = getattr(reading, field, 0) or 0
    interval_seconds = getattr(reading, "interval_seconds", 0) or 0
    if interval_seconds <= 0:
        return 0.0
    return round(energy_kwh * 3600.0 / interval_seconds, 6)


class MeterCreateInput(BaseModel):
    meter_type: str = "Grid_Consumer"
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy_class: Optional[str] = None
    has_solar: Optional[bool] = None
    solar_capacity: Optional[float] = None


class MeterPatchInput(BaseModel):
    meter_type: Optional[str] = None
    has_solar: Optional[bool] = None
    solar_capacity: Optional[float] = None
    min_load_kw: Optional[float] = None
    max_load_kw: Optional[float] = None


class MeterOverrideInput(BaseModel):
    value: float
    field: str = "consumption"


@router.get("/meters")
async def list_meters(
    type: Optional[str] = Query(None, description="Filter by meter type"),
    limit: int = Query(1000, ge=1, le=10000),
):
    engine = _get_engine()
    meters = [_meter_payload(meter) for meter in engine.meters]
    if type:
        meters = [meter for meter in meters if meter["meter_type"] == type]
    return {
        "meters": meters[:limit],
        "total": min(len(meters), limit),
        "source": "engine",
    }


@router.post("/meters")
async def create_meter(data: MeterCreateInput):
    from smart_meter_simulator.devices.ami import SmartMeter
    from smart_meter_simulator.meter_generator import MeterGenerator

    engine = _get_engine()
    generator = MeterGenerator(num_meters=1)
    meter_config = generator.create_meter(
        meter_type=data.meter_type,
        lat=data.lat,
        lon=data.lon,
        accuracy_class=data.accuracy_class,
        has_solar=data.has_solar,
        solar_capacity=data.solar_capacity,
    )
    meter = SmartMeter(meter_config)
    await engine.add_meter(meter)
    return {"status": "created", "meter": _meter_payload(meter)}


@router.get("/meters/{meter_id}")
async def get_meter(meter_id: str):
    engine = _get_engine()
    for meter in engine.meters:
        if meter.meter_id == meter_id:
            return _meter_payload(meter)
    raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")


@router.patch("/meters/{meter_id}")
async def patch_meter(meter_id: str, data: MeterPatchInput):
    engine = _get_engine()
    patch = data.model_dump(exclude_none=True)
    for meter in engine.meters:
        if meter.meter_id == meter_id:
            meter.config.update(patch)
            return {
                "status": "updated",
                "meter_id": meter_id,
                "patched_fields": list(patch.keys()),
            }
    raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")


@router.delete("/meters/{meter_id}")
async def remove_meter(meter_id: str):
    engine = _get_engine()
    if not await engine.remove_meter(meter_id):
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")
    return {"status": "deleted", "meter_id": meter_id}


@router.delete("/meters")
async def clear_meters():
    engine = _get_engine()
    await engine.clear_meters()
    return {"status": "cleared"}


@router.get("/meters/{meter_id}/readings")
async def get_meter_readings(meter_id: str, limit: int = Query(100, ge=1, le=1000)):
    engine = _get_engine()
    readings = [
        reading.to_telemetry_payload()
        for reading in engine.last_readings
        if reading.meter_id == meter_id
    ][:limit]
    return {"meter_id": meter_id, "readings": readings, "total": len(readings)}


@router.post("/meters/{meter_id}/readings/override")
async def override_meter_reading(meter_id: str, data: MeterOverrideInput):
    engine = _get_engine()
    for meter in engine.meters:
        if meter.meter_id == meter_id:
            if data.field == "generation":
                meter.manual_override_gen = data.value
            else:
                meter.manual_override_cons = data.value
            return {
                "status": "overridden",
                "meter_id": meter_id,
                "field": data.field,
                "value": data.value,
            }
    raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")


@router.put("/meters/count")
async def update_meter_count(request: dict = Body(...)):
    from smart_meter_simulator.devices.ami import SmartMeter
    from smart_meter_simulator.meter_generator import MeterGenerator

    engine = _get_engine()
    new_count = int(request.get("count", len(engine.meters)))
    if new_count < 1 or new_count > 10000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10000")

    generator = MeterGenerator(new_count)
    for request_key, config_key in {
        "solar_ratio": "solar_prosumer_ratio",
        "consumer_ratio": "grid_consumer_ratio",
        "hybrid_ratio": "hybrid_prosumer_ratio",
        "gen_min": "base_generation_min",
        "gen_max": "base_generation_max",
    }.items():
        if request_key in request:
            setattr(generator.config, config_key, float(request[request_key]))

    if engine.grid.topology and engine.grid.topology.buses:
        pv_capacity_by_node = {
            pv.bus: pv.capacity_kw for pv in engine.grid.topology.pvs
        }
        configs = generator.generate_ieee_meters(
            num_nodes=len(engine.grid.topology.buses),
            target_meters=new_count,
            pv_on_every_bus=bool(
                request.get("pv_on_every_bus", engine.config.pv_on_every_bus)
            ),
            node_ids=[bus.name for bus in engine.grid.topology.buses],
            pv_capacity_kw_by_node=pv_capacity_by_node,
        )
    else:
        configs = generator.generate_meters()

    engine.meters = [SmartMeter(config) for config in configs]
    engine.grid.initialize_network(engine.meters)

    from smart_meter_simulator.core.metrics import ACTIVE_METERS

    ACTIVE_METERS.set(len(engine.meters))
    return {"status": "updated", "new_count": len(engine.meters)}
