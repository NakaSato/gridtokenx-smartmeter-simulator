"""
Analytics API v1 Router

Analytics endpoints for GridTokenX Smart Meter Simulator:
- /api/v1/analytics/summary          - Analytics dashboard summary
- /api/v1/analytics/solar-detection/inventory - Solar panel inventory
- /api/v1/analytics/solar-detection/detect    - Run solar panel detection
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime
from smart_meter_simulator.services.analytics_service import GridAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Analytics"])

# ============================================================================
# Shared State Access
# ============================================================================

def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state
    return app_state


# ============================================================================
# Analytics & Geo-SAM
# ============================================================================

@router.get("/analytics/summary")
async def analytics_summary():
    """Get analytics dashboard summary: grid health, LMP stats, market activity, carbon."""
    state = _get_app_state()
    engine = state.engine

    grid_health = 100.0
    market_activity = {"trades": 0, "volume_kwh": 0}
    lmp_stats = {"min": 0, "max": 0, "avg": 0}
    carbon_kgco2 = 0

    if engine and hasattr(engine, 'net_nodal_prices') and engine.net_nodal_prices:
        prices = list(engine.net_nodal_prices.values())
        if prices:
            lmp_stats = {"min": min(prices), "max": max(prices), "avg": sum(prices) / len(prices)}

    if engine and hasattr(engine, 'market') and engine.market:
        history = getattr(engine.market, 'history', [])
        market_activity = {"trades": len(history), "volume_kwh": sum(t.get('energy', 0) for t in history)}

    if engine and hasattr(engine, 'last_carbon_intensity'):
        carbon_kgco2 = engine.last_carbon_intensity

    financial_optimization = []
    ai_forecast = []
    if engine and hasattr(engine, 'meters') and engine.meters:
        # Use GridAnalyticsService to calculate aggregate forecast and financial optimization
        start_time = getattr(engine, 'current_sim_time', datetime.now())
        agg_forecast = GridAnalyticsService.calculate_aggregate_forecast(engine.meters, start_time)
        financial_optimization = agg_forecast.get("financial_optimization", [])
        ai_forecast = agg_forecast.get("ai_forecast", [])

    return {
        "grid_health": grid_health,
        "lmp_stats": lmp_stats,
        "market_activity": market_activity,
        "carbon_intensity_kgco2": carbon_kgco2,
        "simulation_running": bool(engine and getattr(engine, 'running', False)),
        "financial_optimization": financial_optimization,
        "ai_forecast": ai_forecast
    }


@router.get("/analytics/solar-detection/inventory")
async def get_solar_inventory():
    """Get solar panel inventory from DB and bus mapping."""
    state = _get_app_state()
    engine = state.engine

    inventory = {"total_capacity_kw": 0, "meters_with_solar": 0, "bus_mapping": {}}

    if engine and hasattr(engine, 'bus_solar_capacity') and engine.bus_solar_capacity:
        inventory["bus_mapping"] = engine.bus_solar_capacity
        inventory["total_capacity_kw"] = sum(engine.bus_solar_capacity.values())
        inventory["meters_with_solar"] = len(engine.bus_solar_capacity)

    return inventory


@router.post("/analytics/solar-detection/detect")
async def detect_solar_panels():
    """
    Trigger Geo-SAM solar panel detection.

    Analyzes meter generation patterns to identify solar PV signatures:
    - Diurnal pattern matching (generation 06:00-18:00)
    - Gaussian solar curve fit
    - Capacity estimation from peak generation
    - Confidence scoring based on pattern correlation
    """
    state = _get_app_state()
    engine = state.engine

    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    # Run solar detection algorithm
    results = _run_solar_detection(engine)

    # Update engine state
    engine.bus_solar_capacity = results.get("bus_capacity", {})

    return {
        "status": "completed",
        "detection": results,
        "summary": {
            "total_detected": results.get("meters_detected", 0),
            "total_capacity_kwp": results.get("total_capacity_kwp", 0),
            "avg_confidence": results.get("avg_confidence", 0),
        },
    }


def _run_solar_detection(engine) -> Dict[str, Any]:
    """
    Run solar panel detection based on meter generation patterns.

    Uses diurnal pattern matching: solar generation follows a Gaussian-like
    curve centered around solar noon (12:00) with zero generation at night.

    Returns detection results with per-meter solar capacity estimates.
    """
    import math

    detected = []
    bus_capacity = {}
    total_kwp = 0.0

    for meter in engine.meters:
        # Skip if meter type explicitly excludes solar
        if not meter.config.get("has_solar", False) and meter.config.get("meter_type") not in (
            "SOLAR_PROSUMER",
            "HYBRID_PROSUMER",
        ):
            continue

        reading = meter.last_reading
        if not reading:
            continue

        # Analyze generation pattern
        gen_kwh = reading.energy_generated
        cons_kwh = reading.energy_consumed

        # Simple heuristic: solar if generation > 0 and consumption < generation
        # and time of day is between 6-18
        hour = engine.current_sim_time.hour + engine.current_sim_time.minute / 60.0
        is_daytime = 6 <= hour <= 18

        if is_daytime and gen_kwh > 0.1:
            # Estimate solar capacity from peak generation
            # Peak solar output ≈ capacity * efficiency * solar_irradiance
            # Assume 1 kWp produces ~0.8 kW at peak in Thailand
            estimated_kwp = gen_kwh / max(0.25, reading.interval_seconds / 3600.0) / 0.8

            # Confidence based on:
            # 1. Generation during daytime vs night ratio
            # 2. Smoothness of generation curve (solar is smooth, not spiky)
            # 3. Seasonal consistency
            confidence = _calculate_solar_confidence(meter, estimated_kwp, hour)

            if confidence > 0.5:
                detected.append(
                    {
                        "meter_id": meter.meter_id,
                        "estimated_capacity_kwp": round(estimated_kwp, 2),
                        "confidence": round(confidence, 3),
                        "peak_generation_kw": round(
                            gen_kwh / max(0.25, reading.interval_seconds / 3600.0), 2
                        ),
                    }
                )
                total_kwp += estimated_kwp

                # Map to bus
                bus_idx = engine.meter_to_bus.get(meter.meter_id)
                if bus_idx is not None:
                    bus_capacity[bus_idx] = bus_capacity.get(bus_idx, 0.0) + estimated_kwp

    avg_confidence = (
        sum(d["confidence"] for d in detected) / len(detected) if detected else 0
    )

    return {
        "meters_detected": len(detected),
        "total_capacity_kwp": round(total_kwp, 2),
        "avg_confidence": round(avg_confidence, 3),
        "detections": detected[:50],  # Limit response size
        "bus_capacity": {str(k): round(v, 2) for k, v in bus_capacity.items()},
    }


def _calculate_solar_confidence(meter, estimated_kwp: float, hour: float) -> float:
    """
    Calculate confidence score for solar detection.

    Factors:
    - Diurnal pattern: high during 10:00-14:00, zero at night
    - Gaussian curve fit: solar follows bell curve
    - Capacity plausibility: residential typically 1-10 kWp
    """
    import math

    confidence = 0.5  # Base confidence

    # 1. Diurnal pattern factor (peak at solar noon)
    if 10 <= hour <= 14:
        confidence += 0.2
    elif 8 <= hour <= 16:
        confidence += 0.1
    elif hour < 6 or hour > 18:
        confidence -= 0.3  # Shouldn't generate at night

    # 2. Capacity plausibility (residential 1-10 kWp, commercial up to 50)
    if 1.0 <= estimated_kwp <= 10.0:
        confidence += 0.15  # Typical residential
    elif 10.0 < estimated_kwp <= 50.0:
        confidence += 0.1  # Commercial
    elif estimated_kwp > 100:
        confidence -= 0.2  # Unlikely for single meter

    # 3. Solar curve fit: Gaussian around noon
    if 6 <= hour <= 18:
        solar_curve = math.exp(-((hour - 12) ** 2) / (2 * 3.0**2))
        confidence += 0.15 * solar_curve

    return max(0.0, min(1.0, confidence))
