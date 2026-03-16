from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import math
import random
import re
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from .dependencies import get_engine

router = APIRouter(prefix="/api/grid", tags=["Grid"])

@router.get("/status")
async def get_grid_status(engine=Depends(get_engine)):
    """Get summarized grid topology status"""
    if not engine.net:
        return {"error": "Grid model not initialized"}
    
    net = engine.net
    return {
        "num_buses": len(net.bus),
        "num_lines": len(net.line),
        "num_loads": len(net.load),
        "num_sgens": len(net.sgen),
        "has_external_grid": len(net.ext_grid) > 0,
        "voltage_levels": net.bus.vn_kv.unique().tolist()
    }

@router.get("/legacy-topology")
async def get_legacy_topology(engine=Depends(get_engine)):
    """Get topology in legacy format for frontend compatibility (zones/meters)"""
    zones = {}
    meters_list = []
    
    base_lat = 13.757559
    base_lon = 100.688338
    
    for meter in engine.meters:
        zone_id = 1
        parts = meter.config.get('location', '').split('_')
        if len(parts) >= 2 and parts[0] == "Zone":
             try:
                 zone_id = int(parts[1])
             except:
                 pass
        
        if zone_id not in zones:
             offset_lat = (zone_id - 1) * 0.005
             offset_lon = (zone_id - 1) * 0.005
             
             zones[zone_id] = {
                 "zone_id": zone_id,
                 "transformer_name": f"Transformer Zone {zone_id}",
                 "centroid_lat": base_lat + offset_lat,
                 "centroid_lon": base_lon + offset_lon,
                 "radius_km": 0.5
             }
        
        meters_list.append({
            "meter_id": meter.meter_id,
            "meter_serial": meter.meter_id,
            "zone_id": zone_id,
            "type": meter.config.get('meter_type', 'unknown'),
            "location": meter.config.get('location', 'Unknown'),
            "latitude": zones[zone_id]["centroid_lat"] + random.uniform(-0.002, 0.002),
            "longitude": zones[zone_id]["centroid_lon"] + random.uniform(-0.002, 0.002),
            "status": "active"
        })
        
    return {
        "zones": zones,
        "meters": meters_list
    }

@router.get("/estimation")
async def get_estimation_results(engine=Depends(get_engine)):
    """Get latest state estimation results"""
    if not engine.last_estimation_results:
        return {"error": "No estimation results available"}
    
    res = engine.last_estimation_results
    return {
        "converged": res.converged,
        "iterations": res.iterations,
        "num_measurements": res.num_measurements,
        "chi2": res.chi2_statistic,
        "mean_absolute_error": round(float(res.mean_absolute_error), 6) if res.mean_absolute_error is not None else 0.0,
        "max_residual": round(float(res.max_residual), 6) if res.max_residual is not None else 0.0,
        "v_deviation_avg": round(float(res.v_deviation_avg), 6) if res.v_deviation_avg is not None else 0.0,
        "total_losses_mw": round(float(res.total_losses_mw), 6) if hasattr(res, 'total_losses_mw') and res.total_losses_mw is not None else 0.0,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/measurements")
async def get_grid_measurements(engine=Depends(get_engine)):
    """Get current measurements used for estimation"""
    if not engine.net or engine.net.measurement.empty:
        return {"measurements": []}
    
    meas = engine.net.measurement
    return {
        "measurements": meas.to_dict(orient='records')
    }

@router.get("/topology")
async def get_grid_topology(engine=Depends(get_engine)):
    """Get detailed grid topology"""
    if not engine.net:
        return {"error": "No grid model available"}
    
    net = engine.net
    buses = net.bus[['name', 'vn_kv', 'type']].to_dict(orient='index')
    
    base_lat = 13.7563
    base_lng = 100.6610
    
    for idx in buses:
        bus_data = buses[idx]
        lat, lng = None, None
        if 'bus_geocoord' in net and idx in net.bus_geocoord.index:
            lng = float(net.bus_geocoord.at[idx, 'x'])
            lat = float(net.bus_geocoord.at[idx, 'y'])
            bus_data['lat'] = lat
            bus_data['lng'] = lng

        if lat is not None and lng is not None:
            bus_data['fx'] = (lng - base_lng) * 111320.0
            bus_data['fz'] = (lat - base_lat) * 111320.0
        else:
            node_id_str = str(idx) + bus_data.get('name', '')
            hashed = int(hashlib.md5(node_id_str.encode()).hexdigest(), 16)
            bus_data['fx'] = (hashed % 1000) - 500
            bus_data['fz'] = ((hashed // 1000) % 1000) - 500
            
        bus_data['fy'] = bus_data.get('vn_kv', 0.4) * 10
    
    lines = net.line[['name', 'from_bus', 'to_bus', 'length_km', 'max_i_ka']].to_dict(orient='records')
    
    return {
        "buses": buses,
        "lines": lines
    }

@router.get("/snapshot")
async def get_grid_snapshot(timestamp: Optional[str] = None, engine=Depends(get_engine)):
    """
    Get a snapshot of the grid state (meter readings + trades) for a specific time.
    """
    if timestamp:
        try:
            target_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO8601.")
    else:
        target_time = engine.current_sim_time

    meter_data = []
    time_factor = 1.0
    if timestamp:
        hour = target_time.hour + target_time.minute / 60.0
        time_factor = 0.5 + 0.5 * math.sin(math.pi * (hour - 6) / 12)

    for meter in engine.meters:
        cons = meter.last_cons_noise if hasattr(meter, 'last_cons_noise') else 1.0
        gen = meter.last_gen_noise if hasattr(meter, 'last_gen_noise') else 0.0
        
        if timestamp:
            cons *= time_factor
            if 6 <= target_time.hour <= 18:
                gen *= (math.sin(math.pi * (target_time.hour - 6) / 12) ** 2)
            else:
                gen = 0
                
        meter_data.append({
            "meter_id": meter.meter_id,
            "consumption_kw": round(cons, 3),
            "generation_kw": round(gen, 3),
            "battery_level": meter.battery_level,
            "phase": meter.config.get('phase', 'A'),
            "is_compromised": getattr(meter.last_reading, 'is_compromised', False) if hasattr(meter, 'last_reading') else False
        })

    current_trades = []
    if engine.market and engine.market.history:
        nearest = None
        min_diff = timedelta(days=1)
        for h in engine.market.history:
            h_time = datetime.fromisoformat(h['timestamp'])
            diff = abs(h_time - target_time.replace(tzinfo=None))
            if diff < min_diff:
                min_diff = diff
                nearest = h
        
        if nearest and min_diff < timedelta(minutes=16):
            current_trades = nearest.get('trades', [])

    line_data = []
    if engine.net is not None:
        for idx, line in engine.net.line.iterrows():
            loading = 0.0
            if 'res_line' in engine.net and idx in engine.net.res_line.index:
                loading = float(engine.net.res_line.at[idx, 'loading_percent'])
            
            if timestamp:
                loading *= (time_factor * 1.2)
                loading = min(loading, 100.0)

            line_data.append({
                "line_id": idx,
                "loading_percent": round(loading, 2)
            })

    return {
        "timestamp": target_time.isoformat(),
        "meters": meter_data,
        "trades": current_trades,
        "lines": line_data,
        "market_summary": {
            "mcp": engine.market.current_mcp,
            "sentiment": engine.market.get_market_sentiment()
        }
    }

@router.get("/geojson")
async def get_grid_geojson(engine=Depends(get_engine)):
    """Get grid topology in GeoJSON format for Mapbox"""
    from ..core.app_state import mapbox_matcher # Import from app_state instead of app
    if not engine.net:
        return {"type": "FeatureCollection", "features": []}
    
    net = engine.net
    features = []
    
    for idx, bus in net.bus.iterrows():
        lng, lat = 0.0, 0.0
        if 'bus_geocoord' in net and idx in net.bus_geocoord.index:
            lng = float(net.bus_geocoord.at[idx, 'x'])
            lat = float(net.bus_geocoord.at[idx, 'y'])
        
        bus_name = str(bus.get('name', f"Bus {idx}"))
        phase_match = re.search(r'\(Phase ([ABC])\)', bus_name)
        phase = phase_match.group(1) if phase_match else ["A", "B", "C"][idx % 3]
        
        vm_pu = 1.0
        if 'res_bus' in net and idx in net.res_bus.index:
            vm_pu = float(net.res_bus.at[idx, 'vm_pu'])
        
        meter_id = next((m_id for m_id, b_idx in engine.meter_to_bus.items() if b_idx == idx), None)
        
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": {
                "id": str(idx),
                "name": str(bus.get('name', f"Bus {idx}")),
                "element_type": "bus",
                "type": "transformer" if bus.get('type') == 't' else "bus",
                "vn_kv": float(bus.get('vn_kv', 0.4)),
                "vm_pu": vm_pu,
                "phase": phase,
                "meter_id": meter_id
            }
        })
        
    line_tasks = []
    line_props = []

    for idx, line in net.line.iterrows():
        from_bus = int(line.from_bus)
        to_bus = int(line.to_bus)
        
        coords = []
        if 'line_geodata' in net and idx in net.line_geodata.index:
            line_geo = net.line_geodata.at[idx, 'coords']
            coords = [[float(p[0]), float(p[1])] for p in line_geo]
        
        if not coords and 'bus_geocoord' in net:
            if from_bus in net.bus_geocoord.index and to_bus in net.bus_geocoord.index:
                coords = [
                    [float(net.bus_geocoord.at[from_bus, 'x']), float(net.bus_geocoord.at[from_bus, 'y'])],
                    [float(net.bus_geocoord.at[to_bus, 'x']), float(net.bus_geocoord.at[to_bus, 'y'])]
                ]
        
        if not coords:
            coords = [[0.0, 0.0], [0.0, 0.0]]
            
        from_bus_name = str(net.bus.at[from_bus, 'name']) if from_bus in net.bus.index else ""
        phase_match = re.search(r'\(Phase ([ABC])\)', from_bus_name)
        phase = phase_match.group(1) if phase_match else ["A", "B", "C"][from_bus % 3]
        
        loading_percent = 0.0
        i_ka = 0.0
        if 'res_line' in net and idx in net.res_line.index:
            loading_percent = float(net.res_line.at[idx, 'loading_percent'])
            i_ka = float(net.res_line.at[idx, 'i_ka'])

        line_tasks.append(mapbox_matcher.match_route(coords))
        
        line_name = str(line.get('name', ''))
        style_type = "feeder" if "Main_Feeder" in line_name else ("service_drop" if "Service_Drop" in line_name else "line")

        line_props.append({
            "id": f"line_{idx}",
            "name": line_name or f"Line {idx}",
            "from_bus": from_bus,
            "to_bus": to_bus,
            "length_km": float(line.get('length_km', 0.1)),
            "phase": phase,
            "element_type": "line",
            "style_type": style_type,
            "loading_percent": loading_percent,
            "i_ka": i_ka,
            "voltage_level": "LV" if line.get('vn_kv', 0.4) < 1.0 else "MV"
        })

    import asyncio
    matched_results = await asyncio.gather(*line_tasks)
    
    R_OHM_KM = 0.32
    V_NOMINAL = 416

    for props, result in zip(line_props, matched_results):
        geometry, length_m = result
        i_a = props.get("i_ka", 0.0) * 1000
        length_km = length_m / 1000
        v_drop_v = (1.732 * i_a * R_OHM_KM * length_km)
        v_drop_pct = (v_drop_v / V_NOMINAL) * 100
        
        props.update({
            "real_length_m": round(length_m, 2),
            "v_drop_v": round(v_drop_v, 2),
            "v_drop_pct": round(v_drop_pct, 2)
        })

        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": geometry},
            "properties": props
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/history")
async def get_grid_history(limit: int = 50, engine=Depends(get_engine)):
    """Get historical grid metrics."""
    if not engine.db_manager:
        return {"success": False, "message": "Database not initialized"}
    
    history = await engine.db_manager.get_grid_history(limit=limit)
    return {
        "success": True,
        "history": history
    }

@router.get("/export/cim")
async def export_cim(engine=Depends(get_engine)):
    """Export current grid state as CIM XML"""
    from ..adapters.cim_adapter import CIMAdapter
    from fastapi import Response
    adapter = CIMAdapter()
    try:
        xml_content = adapter.export_to_xml(engine.net)
        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        return {"success": False, "message": str(e)}
