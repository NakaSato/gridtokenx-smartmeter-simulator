from fastapi import APIRouter, Depends
from typing import Dict, Any, List
import logging
from datetime import datetime

from ..core import app_state
from ..config.enums import MeterType

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)

@router.get("/summary")
async def get_dashboard_summary() -> Dict[str, Any]:
    """
    Get aggregated status for the high-level dashboard KPIs.
    """
    engine = app_state.engine
    if not engine:
        return {"status": "error", "message": "Engine not initialized"}

    # 1. Grid Health
    avg_loading = 0.0
    if engine.net is not None and hasattr(engine.net, 'res_line'):
        avg_loading = engine.net.res_line.loading_percent.mean()
    
    # 2. LMP Stats
    min_price = 0.0
    max_price = 0.0
    avg_price = 0.0
    avg_consumer_price = 0.0
    avg_prosumer_price = 0.0

    if engine.net_nodal_prices:
        prices = list(engine.net_nodal_prices.values())
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        # 2.1 Role-specific prices
        consumer_prices = []
        prosumer_prices = []
        
        for m in engine.meters:
            b_idx = engine.meter_to_bus.get(m.meter_id)
            if b_idx is not None and b_idx in engine.net_nodal_prices:
                price = engine.net_nodal_prices[b_idx]
                if m.config.get('meter_type') == MeterType.GRID_CONSUMER.value:
                    consumer_prices.append(price)
                else:
                    prosumer_prices.append(price)
        
        if consumer_prices:
            avg_consumer_price = sum(consumer_prices) / len(consumer_prices)
        if prosumer_prices:
            avg_prosumer_price = sum(prosumer_prices) / len(prosumer_prices)

    # 3. Market Activity (Last cycle)
    last_matches = 0
    if hasattr(engine.market, 'history') and engine.market.history:
        last_matches = len(engine.market.history[-1].get("trades", []))

    # 4. Carbon Metrics
    carbon_intensity = getattr(engine, 'last_carbon_intensity', 0.0)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "grid": {
            "avg_loading_percent": float(avg_loading),
            "num_buses": len(engine.net.bus) if engine.net else 0,
            "num_lines": len(engine.net.line) if engine.net else 0,
        },
        "market": {
            "min_nodal_price": float(min_price),
            "max_nodal_price": float(max_price),
            "avg_nodal_price": float(avg_price),
            "avg_consumer_price": float(avg_consumer_price or avg_price),
            "avg_prosumer_price": float(avg_prosumer_price or avg_price),
            "last_matches_count": last_matches,
            "currency": "THB/kWh"
        },
        "environmental": {
            "carbon_intensity_g_kwh": float(carbon_intensity),
            "grid_status": "Clean" if carbon_intensity < 100 else "Moderate" if carbon_intensity < 400 else "Dirty"
        },
        "simulation": {
            "running": engine.running and not engine.paused,
            "mode": engine.mode.value,
            "num_meters": len(engine.meters),
            "num_consumers": sum(1 for m in engine.meters if m.config.get('meter_type') == MeterType.GRID_CONSUMER.value),
            "num_prosumers": sum(1 for m in engine.meters if m.config.get('meter_type') != MeterType.GRID_CONSUMER.value)
        }
    }
