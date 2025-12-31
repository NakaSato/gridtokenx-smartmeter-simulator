from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/thailand/data")
async def get_thailand_data(request: Request):
    """Get static structure of Thailand grid (Transformers/Zones and Meters)"""
    engine = getattr(request.app.state, "engine", None)
    if not engine:
         return {"error": "Simulator not initialized"}
    
    # Reuse /api/zones logic but exposed specifically for this demo to ensure clarity
    # Getting zone summary from zoning service which is now initialized with Thailand data
    try:
        zone_summary = engine.zoning_service.get_zone_summary()
        zones = {}
        for zone_id, info in zone_summary.items():
            zones[zone_id] = {
                "zone_id": int(info.zone_id),
                "centroid_lat": float(info.centroid_lat),
                "centroid_lon": float(info.centroid_lon),
                "meter_count": int(info.meter_count),
                "transformer_name": f"TR-{info.zone_id}", # Custom naming
            }
            
        meters = []
        for meter in engine.meters:
            if meter.latitude is not None and meter.longitude is not None:
                zid = getattr(meter, "grid_zone_id", None)
                meters.append({
                    "meter_id": str(meter.meter_id),
                    "latitude": float(meter.latitude),
                    "longitude": float(meter.longitude),
                    "zone_id": int(zid) if zid is not None else None,
                    "meter_type": str(meter.config.get("meter_type", "Unknown")),
                    "contract_capacity": meter.config.get("contract_capacity_kw", 0),
                    "building_area": meter.config.get("building_area_sqm", 0)
                })
        
        return {
            "region": "Phaya Thai, Bangkok",
            "stats": {
                "total_meters": len(meters),
                "total_transformers": len(zones)
            },
            "zones": zones,
            "meters": meters
        }
    except Exception as e:
        import traceback
        import logging
        logging.error(f"Error in get_thailand_data: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/zones")
async def get_zones(request: Request):
    """Get K-Means zone data including centroids and meter assignments"""
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        return {"error": "Simulator not initialized"}

    try:
        # Get zone summary from zoning service
        # Check if zoning_service is available
        if not hasattr(engine, "zoning_service"):
             return {"error": "Zoning service not available on engine"}

        zone_summary = engine.zoning_service.get_zone_summary()
        
        # Build zones dict with explicit type casting for JSON serialization
        zones = {}
        for zone_id, info in zone_summary.items():
            zones[zone_id] = {
                "zone_id": int(info.zone_id),
                "centroid_lat": float(info.centroid_lat),
                "centroid_lon": float(info.centroid_lon),
                "meter_count": int(info.meter_count),
                "transformer_name": str(info.transformer_name),
            }
        
        # Build meters list with zone assignments
        meters = []
        for meter in engine.meters:
            if meter.latitude is not None and meter.longitude is not None:
                zid = getattr(meter, "grid_zone_id", None)
                meters.append({
                    "meter_id": str(meter.meter_id),
                    "latitude": float(meter.latitude),
                    "longitude": float(meter.longitude),
                    "zone_id": int(zid) if zid is not None else None,
                    "meter_type": str(meter.config.get("meter_type", "Unknown")),
                })
        
        return {
            "zones": zones,
            "meters": meters,
            "wheeling_charges": engine.zoning_service.get_wheeling_charge_matrix(),
            "loss_factors": engine.zoning_service.get_loss_factor_matrix(),
        }
    except Exception as e:
        import traceback
        import logging
        logging.error(f"Error in get_zones: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}
