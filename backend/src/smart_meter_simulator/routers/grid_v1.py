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
async def grid_map(
    format: str = Query("geojson", description="Format: geojson, mvt"),
    layers: str = Query("all", description="Comma-separated layers: egat, grid, meters, substations, all"),
    region: Optional[str] = Query(None, description="Filter by region (Central, North, South, etc.)"),
    bbox: Optional[str] = Query(None, description="Bounding box filter: min_lon,min_lat,max_lon,max_lat"),
    z: int = Query(10, ge=0, le=20, description="MVT zoom level"),
    x: int = Query(0, ge=0, description="MVT tile x"),
    y: int = Query(0, ge=0, description="MVT tile y"),
):
    """
    Get geographic grid data for map visualization.
    """
    from smart_meter_simulator.services.map_service import MapService
    layer_list = [l.strip() for l in layers.split(",")]
    
    if format == "geojson":
        return await MapService.render_grid_geojson(layer_list, region, bbox)
    
    if format == "mvt":
        tile_bytes = await MapService.render_grid_mvt(z, x, y, layer_list, region, bbox)
        if tile_bytes is None:
             from fastapi.responses import Response
             return Response(content=b"", media_type="application/x-protobuf")
        from fastapi.responses import Response
        return Response(content=tile_bytes, media_type="application/x-protobuf")

    raise HTTPException(status_code=400, detail="Unsupported format. Use geojson or mvt.")




@router.get("/grid/export")
async def grid_export(
    format: str = Query("geojson", description="Export format: geojson, cim, mvt"),
    subset: Optional[str] = Query("all", description="Subset: substations, lines, all"),
    z: int = Query(12, ge=0, le=18, description="MVT tile zoom level"),
    x: int = Query(0, ge=0, description="MVT tile x coordinate"),
    y: int = Query(0, ge=0, description="MVT tile y coordinate"),
):
    """
    Export grid data in various formats.
    """
    state = _get_app_state()
    engine = state.engine

    if format == "geojson":
        from smart_meter_simulator.services.map_service import MapService
        return await MapService.render_grid_geojson(layers=[subset])

    if format == "cim":
        from smart_meter_simulator.services.export_service import GridExportService
        return {"cim_data": GridExportService.generate_cim_rdf(engine)}

    if format == "mvt":
        from smart_meter_simulator.services.map_service import MapService
        tile_bytes = await MapService.render_grid_mvt(z, x, y, layers=[subset])
        if tile_bytes is None:
             from fastapi.responses import Response
             return Response(content=b"", media_type="application/x-protobuf")
        from fastapi.responses import Response
        return Response(content=tile_bytes, media_type="application/x-protobuf")

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")




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
