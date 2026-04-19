"""
Grid Infrastructure API v1 Router

REST API for Grid Physical Infrastructure:
- /api/v1/grid/status - Grid topology summary
- /api/v1/grid/topology - Detailed topology
- /api/v1/grid/telemetry - Grid telemetry
- /api/v1/grid/state-estimation - State estimation results
- /api/v1/grid/snapshots - Grid snapshots
- /api/v1/grid/export - Export (geojson, cim, mvt)
- /api/v1/grid/substations - List substations
- /api/v1/grid/substations/{sub_id} - Substation detail
- /api/v1/grid/transformers/nearest - Nearest transformers
- /api/v1/grid/stats - Grid statistics
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Grid"])

# ============================================================================
# Shared State Access
# ============================================================================

def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state
    return app_state


async def _get_postgis_repo():
    """Get PostGIS repository if available."""
    from smart_meter_simulator.database import PostGISRepository
    return PostGISRepository()


# ============================================================================
# Grid (Physical Infrastructure)
# ============================================================================

@router.get("/grid/status")
async def grid_status():
    """Get grid status."""
    state = _get_app_state()
    return {
        "status": "running" if state.engine and state.engine.running else "stopped",
        "meters_online": 0,
        "grid_frequency_hz": 50.0,
    }


@router.get("/grid/topology")
async def grid_topology(version: Optional[str] = Query(None, description="Topology version (legacy=current)")):
    """Get grid topology. Use ?version=legacy for legacy format."""
    state = _get_app_state()
    topology = {}
    if state.engine and state.engine.pandapower_net:
        net = state.engine.pandapower_net
        topology = {
            "buses": len(net.bus),
            "lines": len(net.line),
            "trafos": len(net.trafo),
            "loads": len(net.load),
            "sgens": len(net.sgen),
        }
    return {"topology": topology, "version": version or "current"}


@router.get("/grid/telemetry")
async def grid_telemetry():
    """Get real-time grid telemetry (sensor readings)."""
    state = _get_app_state()
    return {
        "measurements": [],
        "timestamp": None,
    }


@router.get("/grid/state-estimation")
async def grid_state_estimation():
    """Get latest state estimation results."""
    state = _get_app_state()
    return {
        "converged": False,
        "results": {},
    }


@router.get("/grid/snapshots")
async def grid_snapshots():
    """List grid snapshots."""
    return {"snapshots": []}


# ============================================================================
# Grid Map Rendering API
# ============================================================================

@router.get("/grid/map")
async def grid_map_render(
    format: str = Query("geojson", description="Render format: geojson, mvt"),
    layers: str = Query("all", description="Comma-separated layers: egat,grid,meters,substations,all"),
    region: Optional[str] = Query(None, description="Filter by Thai region (North, Central, Northeast, East, South)"),
    # MVT tile params
    z: Optional[int] = Query(None, ge=0, le=18, description="MVT tile zoom"),
    x: Optional[int] = Query(None, ge=0, description="MVT tile x"),
    y: Optional[int] = Query(None, ge=0, description="MVT tile y"),
    # Bounds filter
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
):
    """
    Render Thai grid on a map.

    Layers available:
    - egat: EGAT transmission network (500/230/115 kV)
    - grid: Active pandapower distribution network
    - meters: Simulator meter positions
    - substations: Substation locations
    - all: All layers combined

    Formats:
    - geojson: For Leaflet, Mapbox GL, MapLibre
    - mvt: Mapbox Vector Tiles for high-performance rendering

    Example (GeoJSON all layers):
        GET /api/v1/grid/map?format=geojson&layers=all

    Example (MVT tile):
        GET /api/v1/grid/map?format=mvt&layers=egat&z=8&x=196&y=119

    Example (Regional):
        GET /api/v1/grid/map?format=geojson&layers=egat&region=Central
    """
    layer_list = [l.strip() for l in layers.split(",")]

    if format == "mvt":
        if z is None or x is None or y is None:
            raise HTTPException(status_code=400, detail="MVT format requires z, x, y tile coordinates")
        return await _render_grid_mvt(z, x, y, layer_list, region, bbox)

    return await _render_grid_geojson(layer_list, region, bbox)


async def _render_grid_geojson(
    layers: List[str],
    region: Optional[str],
    bbox: Optional[str],
) -> dict:
    """
    Build GeoJSON FeatureCollection for map rendering.

    Combines multiple data sources:
    - EGAT transmission network
    - Active pandapower distribution network
    - Simulator meters
    - Substations
    """
    features = []
    requested_layers = set(layers)

    # Parse bounding box filter
    bounds = None
    if bbox:
        try:
            parts = [float(p.strip()) for p in bbox.split(",")]
            if len(parts) == 4:
                bounds = {"min_lon": parts[0], "min_lat": parts[1],
                          "max_lon": parts[2], "max_lat": parts[3]}
        except (ValueError, IndexError):
            pass

    # ── Layer 1: EGAT Transmission ──────────────────────────────────
    if "egat" in requested_layers or "all" in requested_layers:
        try:
            from smart_meter_simulator.adapters.egat_transmission import (
                EGATTransmissionBuilder,
            )
            builder = EGATTransmissionBuilder()

            if region:
                subs = builder.get_substations(region=region)
                lines = builder.get_lines(region=region)
            else:
                subs = builder.get_substations()
                lines = builder.get_lines()

            # Substation Point features
            for sub in subs:
                if bounds and not (bounds["min_lon"] <= sub.longitude <= bounds["max_lon"] and
                                   bounds["min_lat"] <= sub.latitude <= bounds["max_lat"]):
                    continue

                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [sub.longitude, sub.latitude],
                    },
                    "properties": _sanitize_infra_props({
                        "layer": "egat_substation",
                        "id": sub.sub_id,
                        "name": sub.name_en,
                        "name_th": sub.name,
                        "voltage_kv": sub.voltage_kv,
                        "type": sub.sub_type.value,
                        "province": sub.province,
                        "region": sub.region,
                        "capacity_mva": sub.capacity_mva,
                        "marker_color": _voltage_color(sub.voltage_kv),
                        "marker_size": _voltage_marker_size(sub.voltage_kv),
                    }),
                })

            # Line LineString features
            for line in lines:
                from_sub = builder.substations.get(line.from_substation)
                to_sub = builder.substations.get(line.to_substation)
                if not from_sub or not to_sub:
                    continue

                # Check bounds (midpoint)
                mid_lon = (from_sub.longitude + to_sub.longitude) / 2
                mid_lat = (from_sub.latitude + to_sub.latitude) / 2
                if bounds and not (bounds["min_lon"] <= mid_lon <= bounds["max_lon"] and
                                   bounds["min_lat"] <= mid_lat <= bounds["max_lat"]):
                    continue

                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [from_sub.longitude, from_sub.latitude],
                            [to_sub.longitude, to_sub.latitude],
                        ],
                    },
                    "properties": {
                        "layer": "egat_line",
                        "id": line.line_id,
                        "from": line.from_substation,
                        "to": line.to_substation,
                        "voltage_kv": line.voltage_kv,
                        "length_km": line.length_km,
                        "circuit": line.circuit,
                        "conductor": line.conductor,
                        "line_color": _voltage_color(line.voltage_kv),
                        "line_weight": _voltage_line_weight(line.voltage_kv),
                    },
                })

            # Power Plant Point features
            plants = builder.get_power_plants(region=region)
            for plant in plants:
                if bounds and not (bounds["min_lon"] <= plant.longitude <= bounds["max_lon"] and
                                   bounds["min_lat"] <= plant.latitude <= bounds["max_lat"]):
                    continue

                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [plant.longitude, plant.latitude],
                    },
                    "properties": {
                        "layer": "egat_plant",
                        "id": plant.plant_id,
                        "name": plant.name,
                        "plant_type": plant.plant_type,
                        "capacity_mw": plant.capacity_mw,
                        "status": plant.status,
                        "source": plant.source,
                        "marker_color": "#e11d48", # rose-600
                        "marker_size": 20,
                    },
                })

        except ImportError:
            pass  # EGAT module not available

    # ── Layer 2: Active Pandapower Distribution Grid ────────────────
    if "grid" in requested_layers or "all" in requested_layers:
        state = _get_app_state()
        if state.engine and state.engine.net is not None:
            net = state.engine.net
            features.extend(_pandapower_to_geojson(net, bounds))

    # ── Layer 3: Simulator Meters ───────────────────────────────────
    if "meters" in requested_layers or "all" in requested_layers:
        state = _get_app_state()
        if state.engine and state.engine.meters:
            for idx, meter in enumerate(state.engine.meters):
                reading = meter.last_reading
                # Meter location from config or estimated
                lat = meter.config.get("latitude", 13.70 + (idx * 0.003) % 0.3)
                lon = meter.config.get("longitude", 100.45 + (idx * 0.005) % 0.4)

                if bounds and not (bounds["min_lon"] <= lon <= bounds["max_lon"] and
                                   bounds["min_lat"] <= lat <= bounds["max_lat"]):
                    continue

                props = {
                    "layer": "meter",
                    "meter_id": meter.meter_id,
                    "meter_type": meter.config.get("meter_type", "unknown"),
                    "gen_kwh": round(reading.energy_generated, 3) if reading else 0,
                    "cons_kwh": round(reading.energy_consumed, 3) if reading else 0,
                    "voltage_v": round(reading.voltage, 1) if reading else 230,
                    "battery_kwh": round(reading.battery, 2) if reading and hasattr(reading, "battery") else None,
                    "marker_color": "#22c55e" if (reading and reading.energy_generated > reading.energy_consumed) else "#3b82f6",
                }
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": props,
                })

    # ── Layer 4: Substations ────────────────────────────────────────
    if "substations" in requested_layers or "all" in requested_layers:
        subs_list = await _get_substations_geojson()
        for sub in subs_list:
            coords = sub["geometry"]["coordinates"]
            if bounds and not (bounds["min_lon"] <= coords[0] <= bounds["max_lon"] and
                               bounds["min_lat"] <= coords[1] <= bounds["max_lat"]):
                continue
            features.append(sub)

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_features": len(features),
            "layers_requested": layers,
            "region_filter": region,
            "bbox_filter": bbox,
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        },
    }


async def _render_grid_mvt(
    z: int, x: int, y: int,
    layers: List[str],
    region: Optional[str],
    bbox: Optional[str],
):
    """
    Generate Mapbox Vector Tile for the requested tile coordinates.

    Each GeoJSON layer becomes an MVT layer:
    - egat_substations
    - egat_lines
    - grid_lines
    - grid_buses
    - meters
    - substations
    """
    try:
        import mapbox_vector_tile
        import mercantile
    except ImportError:
        raise HTTPException(status_code=503, detail="MVT libraries not installed: pip install mapbox-vector-tile mercantile")

    bounds = mercantile.bounds(x, y, z)
    w, s, e, n = bounds.west, bounds.south, bounds.east, bounds.north

    # Get GeoJSON data and filter by tile bounds
    geojson_data = await _render_grid_geojson(layers, region, f"{w},{s},{e},{n}")

    mvt_layers = {}

    for feature in geojson_data.get("features", []):
        layer_name = feature["properties"].get("layer", "unknown")

        if layer_name not in mvt_layers:
            mvt_layers[layer_name] = []
        mvt_layers[layer_name].append(feature)

    if not mvt_layers:
        from fastapi.responses import Response
        return Response(content=b"", media_type="application/x-protobuf")

    # Build MVT layer structure
    layer_list = []
    for name, feats in mvt_layers.items():
        layer_list.append({
            "name": name,
            "features": feats,
        })

    try:
        tile_bytes = mapbox_vector_tile.encode(layer_list)
        from fastapi.responses import Response
        return Response(content=tile_bytes, media_type="application/x-protobuf")
    except Exception as e:
        logger.warning(f"MVT encode failed: {e}, returning JSON fallback")
        return {
            "layers": list(mvt_layers.keys()),
            "tile": f"{z}/{x}/{y}",
            "feature_count": sum(len(f) for f in mvt_layers.values()),
        }


def _pandapower_to_geojson(net, bounds: Optional[dict] = None) -> list:
    """Convert pandapower network to GeoJSON features."""
    features = []
    import pandas as pd

    # ── Buses ───────────────────────────────────────────────────────
    if hasattr(net, "bus") and len(net.bus) > 0:
        geodata = None
        if hasattr(net, "res_bus_geodata") and len(net.res_bus_geodata) > 0:
            geodata = net.res_bus_geodata
        elif hasattr(net, "bus_geodata") and len(net.bus_geodata) > 0:
            geodata = net.bus_geodata

        for idx, row in net.bus.iterrows():
            lat, lon = None, None
            if geodata is not None and idx in geodata.index:
                gd_row = geodata.loc[idx]
                lon, lat = float(gd_row[0]), float(gd_row[1])
            else:
                continue  # Skip buses without geo data

            if bounds and not (bounds["min_lon"] <= lon <= bounds["max_lon"] and
                               bounds["min_lat"] <= lat <= bounds["max_lat"]):
                continue

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "layer": "grid_bus",
                    "bus_index": int(idx),
                    "name": str(row.get("name", f"Bus_{idx}")),
                    "voltage_kv": float(row.get("vn_kv", 0)),
                    "in_service": bool(row.get("in_service", True)),
                    "zone": str(row.get("zone", "")),
                },
            })

    # ── Lines ───────────────────────────────────────────────────────
    if hasattr(net, "line") and len(net.line) > 0 and geodata is not None:
        for idx, row in net.line.iterrows():
            from_bus = int(row.from_bus)
            to_bus = int(row.to_bus)

            lon1, lat1 = None, None
            lon2, lat2 = None, None
            if from_bus in geodata.index:
                gd = geodata.loc[from_bus]
                lon1, lat1 = float(gd[0]), float(gd[1])
            if to_bus in geodata.index:
                gd = geodata.loc[to_bus]
                lon2, lat2 = float(gd[0]), float(gd[1])

            if lon1 is None or lon2 is None:
                continue

            # Check midpoint bounds
            mid_lon = (lon1 + lon2) / 2
            mid_lat = (lat1 + lat2) / 2
            if bounds and not (bounds["min_lon"] <= mid_lon <= bounds["max_lon"] and
                               bounds["min_lat"] <= mid_lat <= bounds["max_lat"]):
                continue

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon1, lat1], [lon2, lat2]],
                },
                "properties": {
                    "layer": "grid_line",
                    "line_index": int(idx),
                    "name": str(row.get("name", f"Line_{idx}")),
                    "length_km": float(row.get("length_km", 0)),
                    "std_type": str(row.get("std_type", "")),
                    "parallel": int(row.get("parallel", 1)),
                    "in_service": bool(row.get("in_service", True)),
                },
            })

    # ── Transformers ────────────────────────────────────────────────
    if hasattr(net, "trafo") and len(net.trafo) > 0 and geodata is not None:
        for idx, row in net.trafo.iterrows():
            hv_bus = int(row.hv_bus)
            lv_bus = int(row.lv_bus)

            if hv_bus in geodata.index and lv_bus in geodata.index:
                gd_hv = geodata.loc[hv_bus]
                gd_lv = geodata.loc[lv_bus]
                lon_hv, lat_hv = float(gd_hv[0]), float(gd_hv[1])
                lon_lv, lat_lv = float(gd_lv[0]), float(gd_lv[1])

                mid_lon = (lon_hv + lon_lv) / 2
                mid_lat = (lat_hv + lat_lv) / 2
                if bounds and not (bounds["min_lon"] <= mid_lon <= bounds["max_lon"] and
                                   bounds["min_lat"] <= mid_lat <= bounds["max_lat"]):
                    continue

                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[lon_hv, lat_hv], [lon_lv, lat_lv]],
                    },
                    "properties": {
                        "layer": "grid_transformer",
                        "trafo_index": int(idx),
                        "name": str(row.get("name", f"Trafo_{idx}")),
                        "sn_mva": float(row.get("sn_mva", 0)),
                        "vn_hv_kv": float(row.get("vn_hv_kv", 0)),
                        "vn_lv_kv": float(row.get("vn_lv_kv", 0)),
                    },
                })

    return features


async def _get_substations_geojson() -> list:
    """Get substations as GeoJSON from existing sources."""
    features = []

    # From EGAT transmission data
    try:
        from smart_meter_simulator.adapters.egat_transmission import EGAT_SUBSTATIONS
        for sub_id, sub in EGAT_SUBSTATIONS.items():
            sub_type = sub["type"]
            type_str = sub_type.value if hasattr(sub_type, "value") else str(sub_type)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [sub["longitude"], sub["latitude"]],
                },
                "properties": _sanitize_infra_props({
                    "layer": "substation",
                    "id": sub_id,
                    "name": sub["name_en"],
                    "name_th": sub["name"],
                    "voltage_kv": sub["voltage_kv"],
                    "type": type_str,
                    "province": sub["province"],
                    "region": sub["region"],
                }),
            })
    except ImportError:
        pass

    # Fallback: default Thai substations
    if not features:
        thai_substations = [
            {"id": "TH-SUB-001", "name": "สถานไฟฟ้าย่อย บางเขน", "voltage_kv": 22.0, "type": "distribution", "province": "Bangkok", "lat": 13.8788, "lon": 100.6025},
            {"id": "TH-SUB-002", "name": "สถานไฟฟ้าย่อย ปทุมวัน", "voltage_kv": 22.0, "type": "distribution", "province": "Bangkok", "lat": 13.7465, "lon": 100.5347},
            {"id": "TH-SUB-003", "name": "สถานไฟฟ้าย่อย อยุธยา", "voltage_kv": 22.0, "type": "distribution", "province": "Ayutthaya", "lat": 14.3532, "lon": 100.5775},
            {"id": "TH-SUB-004", "name": "สถานไฟฟ้าย่อย เชียงใหม่", "voltage_kv": 115.0, "type": "sub_transmission", "province": "Chiang Mai", "lat": 18.7883, "lon": 98.9853},
            {"id": "TH-SUB-005", "name": "สถานไฟฟ้าย่อย ขอนแก่น", "voltage_kv": 115.0, "type": "sub_transmission", "province": "Khon Kaen", "lat": 16.4418, "lon": 102.8360},
            {"id": "TH-SUB-006", "name": "สถานไฟฟ้าย่อย ภูเก็ต", "voltage_kv": 22.0, "type": "distribution", "province": "Phuket", "lat": 7.8804, "lon": 98.3923},
        ]
        for sub in thai_substations:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [sub["lon"], sub["lat"]]},
                "properties": {
                    "layer": "substation",
                    "id": sub["id"],
                    "name": sub["name"],
                    "voltage_kv": sub["voltage_kv"],
                    "type": sub.get("type", "distribution"),
                    "province": sub["province"],
                },
            })

    return features


def _voltage_color(voltage_kv: float) -> str:
    """Map voltage level to map marker color."""
    if voltage_kv >= 500:
        return "#dc2626"  # red
    elif voltage_kv >= 230:
        return "#f59e0b"  # amber
    elif voltage_kv >= 115:
        return "#3b82f6"  # blue
    elif voltage_kv >= 22:
        return "#22c55e"  # green
    else:
        return "#6b7280"  # gray


def _voltage_marker_size(voltage_kv: float) -> int:
    """Map voltage to marker pixel size."""
    if voltage_kv >= 500:
        return 24
    elif voltage_kv >= 230:
        return 18
    elif voltage_kv >= 115:
        return 14
    else:
        return 10


def _voltage_line_weight(voltage_kv: float) -> int:
    """Map voltage to line stroke weight."""
    if voltage_kv >= 500:
        return 6
    elif voltage_kv >= 230:
        return 4
    elif voltage_kv >= 115:
        return 3
    else:
        return 2


@router.get("/grid/export")
async def grid_export(
    format: str = Query("geojson", description="Export format: geojson, cim, mvt"),
    subset: Optional[str] = Query(None, description="Subset: substations, lines, all"),
    z: int = Query(12, ge=0, le=18, description="MVT tile zoom level"),
    x: int = Query(0, ge=0, description="MVT tile x coordinate"),
    y: int = Query(0, ge=0, description="MVT tile y coordinate"),
):
    """
    Export grid data in various formats.

    Formats: geojson, cim, mvt (Mapbox Vector Tiles)
    """
    state = _get_app_state()
    engine = state.engine

    if format == "geojson":
        features = []
        if engine and engine.meters:
            for i, m in enumerate(engine.meters):
                reading = m.last_reading
                # Generate realistic Thailand coordinates
                lat = 13.70 + (i * 0.003) % 0.3
                lon = 100.45 + (i * 0.005) % 0.4
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "meter_id": m.meter_id,
                        "meter_type": m.config.get("meter_type", "unknown"),
                        "gen_kwh": round(reading.energy_generated, 3) if reading else 0,
                        "cons_kwh": round(reading.energy_consumed, 3) if reading else 0,
                        "voltage_v": round(reading.voltage, 1) if reading else 230,
                    },
                })
        return {"type": "FeatureCollection", "features": features}

    elif format == "cim":
        return {"cim_data": _generate_cim(engine) if engine else ""}

    elif format == "mvt":
        return await _generate_mvt(engine, z, x, y, subset)

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


async def _generate_mvt(engine, z: int, x: int, y: int, subset: Optional[str]):
    """Generate Mapbox Vector Tile from grid data."""
    import mapbox_vector_tile
    import mercantile

    bounds = mercantile.bounds(x, y, z)
    # mercantile returns LngLatBbox with west/south/east/north attributes
    w, s, e, n = bounds.west, bounds.south, bounds.east, bounds.north
    layers = {}

    if subset in (None, "all", "meters"):
        meter_features = []
        if engine and engine.meters:
            for i, m in enumerate(engine.meters):
                reading = m.last_reading
                lat = 13.70 + (i * 0.003) % 0.3
                lon = 100.45 + (i * 0.005) % 0.4
                if w <= lon <= e and s <= lat <= n:
                    props = {
                        "id": m.meter_id,
                        "type": m.config.get("meter_type", "unknown"),
                        "gen_kwh": round(reading.energy_generated, 3) if reading else 0,
                        "cons_kwh": round(reading.energy_consumed, 3) if reading else 0,
                    }
                    meter_features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": props,
                    })
        if meter_features:
            layers["meters"] = {"features": meter_features}

    if subset in (None, "all", "lines"):
        line_features = []
        if engine and hasattr(engine, "net") and engine.net:
            net = engine.net
            if hasattr(net, "line") and len(net.line) > 0:
                for idx, row in net.line.iterrows():
                    from_bus = int(row.from_bus)
                    to_bus = int(row.to_bus)
                    lat1 = 13.75 + from_bus * 0.001
                    lon1 = 100.50 + from_bus * 0.001
                    lat2 = 13.75 + to_bus * 0.001
                    lon2 = 100.50 + to_bus * 0.001
                    mid_lat = (lat1 + lat2) / 2
                    mid_lon = (lon1 + lon2) / 2
                    if w <= mid_lon <= e and s <= mid_lat <= n:
                        line_features.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [[lon1, lat1], [lon2, lat2]],
                            },
                            "properties": {
                                "from_bus": from_bus,
                                "to_bus": to_bus,
                                "length_km": round(row.length_km, 2) if "length_km" in row else 0.1,
                            },
                        })
        if line_features:
            layers["lines"] = {"features": line_features}

    if subset in (None, "all", "substations"):
        sub_features = []
        if engine and hasattr(engine, "net") and engine.net and hasattr(engine.net, "ext_grid"):
            for idx, row in engine.net.ext_grid.iterrows():
                bus_idx = int(row.bus)
                lat = 13.75 + bus_idx * 0.001
                lon = 100.50 + bus_idx * 0.001
                if w <= lon <= e and s <= lat <= n:
                    sub_features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {"bus": bus_idx, "vm_pu": row.get("vm_pu", 1.0)},
                    })
        if sub_features:
            layers["substations"] = {"features": sub_features}

    if not layers:
        return {"layers": [], "tile": f"{z}/{x}/{y}", "bounds": [w, s, e, n]}

    try:
        # mapbox_vector_tile.encode expects a list of layer dicts with 'name' key
        layer_list = [{"name": name, "features": data["features"]} for name, data in layers.items()]
        tile_bytes = mapbox_vector_tile.encode(layer_list)
        from fastapi.responses import Response
        return Response(content=tile_bytes, media_type="application/x-protobuf")
    except Exception as e:
        logger.warning(f"MVT encode failed: {e}, returning JSON fallback")
        return {"layers": list(layers.keys()), "tile": f"{z}/{x}/{y}", "feature_count": sum(len(l["features"]) for l in layers.values())}


def _generate_cim(engine):
    """Generate CIM RDF/XML from grid data."""
    if not engine or not engine.net:
        return ""

    rdf = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rdf += '<rdf:RDF xmlns:cim="http://iec.ch/TC57/CIM100#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'

    # Add base voltage levels
    if hasattr(engine.net, "bus") and len(engine.net.bus) > 0:
        for idx, row in engine.net.bus.iterrows():
            rdf += f'  <cim:BaseVoltage rdf:ID="BV_{idx}">\n'
            rdf += f'    <cim:BaseVoltage.nominalVoltage>{row.vn_kv * 1000:.0f}</cim:BaseVoltage.nominalVoltage>\n'
            rdf += f"  </cim:BaseVoltage>\n"

    # Add generating units
    if hasattr(engine.net, "sgen") and len(engine.net.sgen) > 0:
        for idx, row in engine.net.sgen.iterrows():
            rdf += f'  <cim:SynchronousMachine rdf:ID="SGEN_{idx}">\n'
            rdf += f'    <cim:SynchronousMachine.p>{row.p_mw * 1000:.2f}</cim:SynchronousMachine.p>\n'
            rdf += f'    <cim:SynchronousMachine.ratedS>{row.sn_mw * 1000:.2f}</cim:SynchronousMachine.ratedS>\n' if "sn_mw" in row else ""
            rdf += f"  </cim:SynchronousMachine>\n"

    # Add loads
    if hasattr(engine.net, "load") and len(engine.net.load) > 0:
        for idx, row in engine.net.load.iterrows():
            rdf += f'  <cim:EnergyConsumer rdf:ID="LOAD_{idx}">\n'
            rdf += f'    <cim:EnergyConsumer.pFixed>{row.p_mw * 1000:.2f}</cim:EnergyConsumer.pFixed>\n'
            rdf += f"  </cim:EnergyConsumer>\n"

    # Add power transformers
    if hasattr(engine.net, "trafo") and len(engine.net.trafo) > 0:
        for idx, row in engine.net.trafo.iterrows():
            rdf += f'  <cim:PowerTransformer rdf:ID="TRF_{idx}">\n'
            rdf += f'    <cim:PowerTransformer.u1>{row.vn_hv_kv * 1000:.0f}</cim:PowerTransformer.u1>\n'
            rdf += f'    <cim:PowerTransformer.u2>{row.vn_lv_kv * 1000:.0f}</cim:PowerTransformer.u2>\n'
            rdf += f"  </cim:PowerTransformer>\n"

    rdf += "</rdf:RDF>\n"
    return rdf


@router.get("/grid/substations")
async def list_substations(
    operator: Optional[str] = Query(None, description="Filter by operator (EGAT/MEA/PEA)"),
    limit: int = Query(100),
):
    """List substations from pandapower network and Thai grid topology."""
    state = _get_app_state()
    engine = state.engine
    substations = []

    # Primary: extract from pandapower network (slack buses = substations)
    if engine and engine.net is not None:
        net = engine.net
        # External grid connections represent substations
        ext_grids = getattr(net, 'ext_grid', None)
        if ext_grids is not None and len(ext_grids) > 0:
            for idx, eg in ext_grids.iterrows():
                bus_idx = int(eg.get('bus', -1))
                if bus_idx < 0 or bus_idx >= len(net.bus):
                    continue
                bus_name = str(net.bus.at[bus_idx, 'name']) if 'name' in net.bus.columns else f"Bus_{bus_idx}"
                vn_kv = float(net.bus.at[bus_idx, 'vn_kv']) if 'vn_kv' in net.bus.columns else 22.0

                sub = {
                    "id": f"sub_{idx}",
                    "name": bus_name,
                    "operator": "MEA",
                    "voltage_kv": vn_kv,
                    "type": "distribution",
                    "status": "in_service",
                    "bus_index": bus_idx,
                }
                substations.append(sub)

        # If no ext_grids, fall back to bus-based heuristic (MV buses = substations)
        if not substations and hasattr(net, 'bus') and len(net.bus) > 0:
            for bus_idx in range(min(len(net.bus), 10)):
                vn_kv = float(net.bus.at[bus_idx, 'vn_kv']) if 'vn_kv' in net.bus.columns else 22.0
                bus_name = str(net.bus.at[bus_idx, 'name']) if 'name' in net.bus.columns else f"Bus_{bus_idx}"
                sub = {
                    "id": f"sub_{bus_idx}",
                    "name": bus_name,
                    "operator": "PEA",
                    "voltage_kv": vn_kv,
                    "type": "distribution",
                    "status": "in_service",
                    "bus_index": bus_idx,
                }
                substations.append(sub)

    # Fallback: Thai grid topology default substations
    if not substations:
        from smart_meter_simulator.adapters.thai_grid_topology import ThaiRegion
        thai_substations = [
            {"id": "TH-SUB-001", "name": "สถานไฟฟ้าย่อย บางเขน", "operator": "MEA", "voltage_kv": 22.0, "type": "distribution", "province": "Bangkok", "lat": 13.8788, "lon": 100.6025, "status": "in_service"},
            {"id": "TH-SUB-002", "name": "สถานไฟฟ้าย่อย ปทุมวัน", "operator": "MEA", "voltage_kv": 22.0, "type": "distribution", "province": "Bangkok", "lat": 13.7465, "lon": 100.5347, "status": "in_service"},
            {"id": "TH-SUB-003", "name": "สถานไฟฟ้าย่อย อยุธยา", "operator": "PEA", "voltage_kv": 22.0, "type": "distribution", "province": "Ayutthaya", "lat": 14.3532, "lon": 100.5775, "status": "in_service"},
            {"id": "TH-SUB-004", "name": "สถานไฟฟ้าย่อย เชียงใหม่", "operator": "PEA", "voltage_kv": 115.0, "type": "sub_transmission", "province": "Chiang Mai", "lat": 18.7883, "lon": 98.9853, "status": "in_service"},
            {"id": "TH-SUB-005", "name": "สถานไฟฟ้าย่อย ขอนแก่น", "operator": "PEA", "voltage_kv": 115.0, "type": "sub_transmission", "province": "Khon Kaen", "lat": 16.4418, "lon": 102.8360, "status": "in_service"},
            {"id": "TH-SUB-006", "name": "สถานไฟฟ้าย่อย ภูเก็ต", "operator": "PEA", "voltage_kv": 22.0, "type": "distribution", "province": "Phuket", "lat": 7.8804, "lon": 98.3923, "status": "in_service"},
        ]
        substations = thai_substations

    # Filter by operator
    if operator:
        substations = [s for s in substations if s.get("operator", "").upper() == operator.upper()]

    # Add lat/lon for pandapower-derived substations that lack them
    for s in substations:
        if "lat" not in s:
            s["lat"] = None
            s["lon"] = None

    return {"substations": substations[:limit], "total": len(substations)}


@router.get("/grid/substations/{sub_id}")
async def get_substation(sub_id: str):
    """Get substation details."""
    return {
        "id": sub_id,
        "name": "",
        "operator": "",
        "voltage_kv": 22,
        "lat": None,
        "lon": None,
    }


@router.get("/grid/transformers/nearest")
async def find_nearest_transformers(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(5),
):
    """Find nearest transformers to a location."""
    return {"transformers": [], "total": 0}


@router.get("/grid/stats")
async def grid_statistics():
    """Get grid statistics."""
    return {
        "total_substations": 0,
        "total_transformers": 0,
        "total_lines_km": 0,
        "total_meters": 0,
    }


# ============================================================================
# EGAT Transmission Network Endpoints
# ============================================================================

@router.get("/grid/egat/transmission")
async def egat_transmission_network(
    region: Optional[str] = Query(None, description="Filter by region (North, Central, Northeast, East, South)"),
    voltage_kv: Optional[float] = Query(None, description="Filter by voltage level (500, 230, 115)"),
):
    """
    Get EGAT transmission network.

    Returns the full transmission network or filtered by region/voltage.
    Includes 500 kV backbone, 230 kV regional, and 115 kV sub-transmission.
    """
    try:
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder

        builder = EGATTransmissionBuilder()

        if region:
            net = builder.build_regional_network(region=region)
        else:
            net = builder.build_full_network()

        # Get filtered substations
        subs = builder.get_substations(voltage_kv=voltage_kv, region=region)
        lines = builder.get_lines(voltage_kv=voltage_kv, region=region)

        return {
            "network_type": "egat_transmission",
            "region": region or "all",
            "voltage_filter_kv": voltage_kv,
            "substations": [
                {
                    "id": s.sub_id,
                    "name": s.name,
                    "name_en": s.name_en,
                    "voltage_kv": s.voltage_kv,
                    "type": s.sub_type.value,
                    "province": s.province,
                    "region": s.region,
                    "capacity_mva": s.capacity_mva,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                }
                for s in subs
            ],
            "lines": [
                {
                    "id": l.line_id,
                    "from": l.from_substation,
                    "to": l.to_substation,
                    "voltage_kv": l.voltage_kv,
                    "length_km": l.length_km,
                    "circuit": l.circuit,
                    "conductor": l.conductor,
                    "type": l.line_type,
                }
                for l in lines
            ],
            "statistics": builder.get_network_statistics(),
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="EGAT transmission module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid/egat/statistics")
async def egat_statistics():
    """
    Get EGAT transmission network statistics.

    Returns counts of substations, lines, and total capacity by voltage level.
    """
    try:
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder

        builder = EGATTransmissionBuilder()
        return builder.get_network_statistics()
    except ImportError:
        raise HTTPException(status_code=503, detail="EGAT transmission module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid/egat/geojson")
async def egat_geojson():
    """
    Export EGAT transmission network as GeoJSON.

    Returns a FeatureCollection with substations (Point) and lines (LineString).
    """
    try:
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder

        builder = EGATTransmissionBuilder()
        return builder.export_geojson()
    except ImportError:
        raise HTTPException(status_code=503, detail="EGAT transmission module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Cache TTL: OSM grid data is static between rebuilds
_OSM_CACHE_MAX_AGE = 3600  # 1 hour


@router.get("/grid/osm")
async def grid_osm(
    request: Request,
    area: str = Query("korat", description="Area name (e.g., korat, thailand)"),
    include_geojson: bool = Query(True, description="Include GeoJSON features"),
    include_mapping: bool = Query(True, description="Include OSM→pandapower mapping"),
    include_way: bool = Query(False, description="Include full OSM way coordinates"),
):
    """
    Get real power grid data from OpenStreetMap.

    Returns pandapower network topology, OSM mapping, and GeoJSON features
    for areas built from real OpenStreetMap power infrastructure.

    Query Parameters:
        area: Area name (default: "korat")
            - korat: Nakhon Ratchasima provincial grid
        include_geojson: Include GeoJSON for map rendering (default: true)
        include_mapping: Include OSM→pandapower ID mapping (default: true)
        include_way: Include full OSM way coordinate arrays (default: false)

    Example:
        GET /api/v1/grid/osm
        GET /api/v1/grid/osm?area=korat&include_mapping=false

    Caching:
        Response includes ETag + Cache-Control (1 hour).
        Browser/fetch clients should send If-None-Match on subsequent
        requests — server returns 304 with no body when data unchanged.

        JS client pattern:
          const res = await fetch('/api/v1/grid/osm')
          const etag = res.headers.get('etag')
          const data = await res.json()
          // Later…
          const res2 = await fetch('/api/v1/grid/osm', {
            headers: { 'If-None-Match': etag }
          })
          if (res2.status === 304) { /* use cached data */ }
    """
    from pathlib import Path
    import json

    # Path: backend/src/smart_meter_simulator/routers/ → backend/data/{area}/
    data_dir = Path(__file__).parent.parent.parent.parent / "data" / area

    if not data_dir.exists():
        raise HTTPException(status_code=404, detail=f"OSM area '{area}' not found. Available: korat")

    try:
        net_file = data_dir / "pandapower_network.json"
        mapping_file = data_dir / "pandapower_mapping.json"
        coords_file = data_dir / "way_402761973_coords.json"

        if not net_file.exists():
            raise HTTPException(status_code=404, detail=f"Pandapower network not found for '{area}'. Run build_pandapower_from_osm.py")

        result: dict[str, Any] = {
            "source": "OpenStreetMap via Overpass API",
            "area": area,
            "data_dir": str(data_dir.relative_to(Path(__file__).parent.parent.parent.parent)),
        }

        # OSM→pandapower mapping
        if include_mapping and mapping_file.exists():
            with open(mapping_file) as f:
                result["mapping"] = json.load(f)

        # Featured OSM way (e.g., way 402761973 for Korat)
        if coords_file.exists():
            with open(coords_file) as f:
                way_data = json.load(f)
            result["featured_line"] = {
                "osm_id": way_data["osm_id"],
                "name": way_data["name"],
                "voltage": way_data["voltage"],
                "operator": way_data["operator"],
                "num_points": way_data["num_points"],
                "bounds": way_data["bounds"],
            }
            if include_way:
                result["featured_line"]["coordinates"] = way_data["coordinates"]

        # GeoJSON from pandapower
        if include_geojson:
            try:
                import pandapower as pp
                net = pp.from_json(str(net_file))

                if include_mapping and "mapping" in result:
                    mapping = result["mapping"]
                elif mapping_file.exists():
                    with open(mapping_file) as f:
                        mapping = json.load(f)
                else:
                    mapping = {}

                features = []

                # Substations → Points
                for osm_id, sub_info in mapping.get("substations", {}).items():
                    bus_idx = sub_info["bus_idx"]
                    if bus_idx in net.bus.index:
                        bus = net.bus.loc[bus_idx]
                        geo = net.bus_geodata.loc[bus_idx] if hasattr(net, "bus_geodata") and bus_idx in net.bus_geodata.index else None

                        features.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [geo.x, geo.y] if geo is not None else [0, 0],
                            },
                            "properties": {
                                "osm_id": osm_id,
                                "name": bus["name"],
                                "type": "substation",
                                "voltage_kv": sub_info["vn_kv"],
                                "category": sub_info["category"],
                            },
                        })

                # Power lines → LineStrings
                for line_idx, line_row in net.line.iterrows():
                    from_bus = int(line_row["from_bus"])
                    to_bus = int(line_row["to_bus"])

                    from_geo = net.bus_geodata.loc[from_bus] if hasattr(net, "bus_geodata") and from_bus in net.bus_geodata.index else None
                    to_geo = net.bus_geodata.loc[to_bus] if hasattr(net, "bus_geodata") and to_bus in net.bus_geodata.index else None

                    coords = []
                    if from_geo:
                        coords.append([from_geo.x, from_geo.y])
                    if to_geo:
                        coords.append([to_geo.x, to_geo.y])

                    if len(coords) >= 2:
                        features.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coords,
                            },
                            "properties": {
                                "name": line_row.get("name", f"Line-{line_idx}"),
                                "type": "power_line",
                                "length_km": line_row["length_km"],
                                "voltage_kv": line_row.get("vn_kv"),
                                "cable_type": line_row.get("std_type"),
                            },
                        })

                result["geojson"] = {
                    "type": "FeatureCollection",
                    "features": features,
                }

            except ImportError:
                result["geojson"] = {"type": "FeatureCollection", "features": []}

        # Network summary (always included)
        import pandapower as pp
        net = pp.from_json(str(net_file))
        pp.runpp(net)

        result["summary"] = {
            "buses": len(net.bus),
            "lines": len(net.line),
            "loads": len(net.load),
            "external_grids": len(net.ext_grid),
            "total_load_mw": round(float(net.load.p_mw.sum()), 2),
            "total_loss_mw": round(float(net.res_line.pl_mw.sum()), 4),
        }

        # Bus voltage status
        result["bus_status"] = []
        for idx, row in net.res_bus.iterrows():
            bus_name = net.bus.at[idx, "name"]
            result["bus_status"].append({
                "bus_idx": int(idx),
                "name": bus_name,
                "voltage_kv": float(net.bus.at[idx, "vn_kv"]),
                "vm_pu": round(float(row["vm_pu"]), 4),
                "va_degree": round(float(row["va_degree"]), 2),
                "status": "ok" if 0.9 <= row["vm_pu"] <= 1.1 else "alert",
            })

        # Build ETag from content hash
        etag = hashlib.md5(json.dumps(result, sort_keys=True).encode()).hexdigest()[:12]

        # Check If-None-Match for conditional request
        if_none_match = request.headers.get("if-none-match", "").strip('"')
        if if_none_match == etag:
            return JSONResponse(status_code=304, content=None, headers={
                "Cache-Control": f"public, max-age={_OSM_CACHE_MAX_AGE}",
                "ETag": f'"{etag}"',
            })

        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": f"public, max-age={_OSM_CACHE_MAX_AGE}",
                "ETag": f'"{etag}"',
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load OSM grid for '{area}': {str(e)}")


@router.get("/grid/egat/substations/{sub_id}")
async def egat_substation_detail(sub_id: str):
    """
    Get detailed information for a specific EGAT substation.

    Args:
        sub_id: Substation identifier (e.g., Mae_Moh_500, Phra_Nakhon_500)
    """
    try:
        from smart_meter_simulator.adapters.egat_transmission import EGATTransmissionBuilder, EGAT_SUBSTATIONS

        if sub_id not in EGAT_SUBSTATIONS:
            raise HTTPException(status_code=404, detail=f"Substation {sub_id} not found")

        sub_data = EGAT_SUBSTATIONS[sub_id]
        return {
            "id": sub_id,
            "name": sub_data["name"],
            "name_en": sub_data["name_en"],
            "voltage_kv": sub_data["voltage_kv"],
            "type": sub_data["type"].value,
            "province": sub_data["province"],
            "region": sub_data["region"],
            "capacity_mva": sub_data["capacity_mva"],
            "latitude": sub_data["latitude"],
            "longitude": sub_data["longitude"],
            "connected_generators": sub_data.get("connected_generators", []),
            "notes": sub_data.get("notes", ""),
            "status": "operational",
        }
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="EGAT transmission module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid/thai/combined")
async def thai_combined_grid(
    region: str = Query("Central", description="Thai region (North, Central, Northeast, East, South)"),
    households_per_substation: int = Query(50, description="Households per distribution network"),
):
    """
    Get combined Thai grid with EGAT transmission + MEA/PEA distribution.

    Creates a multi-voltage network combining:
    - 500/230/115 kV: EGAT transmission backbone
    - 22/0.4 kV: MEA/PEA distribution with household connections
    """
    try:
        from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder

        builder = ThaiGridBuilder()
        net = builder.build_combined_transmission_distribution(
            region=region,
            num_households_per_substation=households_per_substation,
        )

        return {
            "network_type": "thai_combined",
            "region": region,
            "buses": len(net.bus),
            "lines": len(net.line),
            "transformers": len(net.trafo),
            "external_grids": len(net.ext_grid),
            "loads": len(net.load),
            "static_generators": len(net.sgen),
            "voltage_levels": sorted(net.bus['vn_kv'].unique().tolist()),
        }
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Module not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid/thai/statistics")
async def thai_grid_statistics():
    """
    Get comprehensive Thai grid statistics from all available sources.

    Includes EGAT transmission and PyPSA-TH model statistics.
    """
    try:
        from smart_meter_simulator.adapters.thai_grid_topology import get_thai_grid_statistics as get_stats
        return get_stats()
    except ImportError:
        raise HTTPException(status_code=503, detail="Thai grid modules not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/grid/events")
async def grid_events(limit: int = Query(50, ge=1, le=500)):
    """Retrieve historical grid events (bottlenecks, frequency deviations)."""
    state = _get_app_state()
    if not state.engine or not state.engine.db_manager:
        raise HTTPException(status_code=503, detail="Persistence layer not initialized")
    
    events = await state.engine.db_manager.get_grid_events(limit=limit)
    return {"events": events, "count": len(events)}

@router.get("/grid/nodes/{node_id}/history")
async def grid_node_history(node_id: str, limit: int = Query(100, ge=1, le=1000)):
    """
    Retrieve historical performance metrics for a specific grid node.
    This provides the 'New Assumption' analysis data from the ETL pipeline.
    """
    state = _get_app_state()
    if not state.engine or not state.engine.db_manager:
        raise HTTPException(status_code=503, detail="Persistence layer not initialized")
    
    history = await state.engine.db_manager.get_node_history(node_id, limit=limit)
    if not history:
        return {"node_id": node_id, "history": [], "message": "No history found for this node"}
        
    return {
        "node_id": node_id,
        "history": history,
        "count": len(history),
        "last_updated": history[0]["timestamp"] if history else None
    }
