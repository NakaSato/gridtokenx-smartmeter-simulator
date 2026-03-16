from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from .dependencies import get_engine

router = APIRouter(tags=["Market"])

@router.get("/api/v1/p2p/market-prices")
async def get_market_prices(engine=Depends(get_engine)):
    """Get summarized market pricing data"""
    now = engine.current_sim_time
    tariff = engine.market.tariff_manager.get_current_tariff(now)
    
    return {
        "base_price_thb_kwh": float(tariff.import_rate),
        "grid_import_price_thb_kwh": float(tariff.import_rate),
        "grid_export_price_thb_kwh": float(tariff.export_rate),
        "wheeling_charges": {"0": 0.0, "1": 0.05, "2": 0.08, "3": 0.12},
        "loss_factors": {"0": 1.0, "1": 1.02, "2": 1.05, "3": 1.08}
    }

@router.post("/api/v1/p2p/calculate-cost")
async def calculate_p2p_cost(request: dict, engine=Depends(get_engine)):
    """Calculate P2P transaction cost"""
    try:
        buyer_zone = int(request.get('buyer_zone_id', 0))
        seller_zone = int(request.get('seller_zone_id', 0))
        qty = float(request.get('energy_amount', 0.0))
        agreed_price = float(request.get('agreed_price', 0.25))
        
        distance = abs(buyer_zone - seller_zone)
        wheeling_rate = 0.02 + (0.015 * distance)
        loss_factor = 0.02 + (0.01 * distance)
        
        energy_cost = agreed_price * qty
        wheeling_charge = wheeling_rate * qty
        loss_cost = (energy_cost * loss_factor)
        
        return {
            "energy_cost": float(energy_cost),
            "wheeling_charge": float(wheeling_charge),
            "total_cost": float(energy_cost + wheeling_charge + loss_cost),
            "effective_energy": float(qty * (1.0 - loss_factor))
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/analytics/report")
async def get_analytics_report(engine=Depends(get_engine)):
    """Get summarized grid health report"""
    return jsonable_encoder(engine.analytics.get_summary())
