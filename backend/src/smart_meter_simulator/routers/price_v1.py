"""
Price & P2P API Router

REST endpoints for price comparison, utility rates, P2P dynamic pricing,
price history, statistics, and transaction cost calculation.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime, timezone

logger = __import__("logging").getLogger(__name__)

router = APIRouter(prefix="", tags=["Price"])


# ============================================================================
# Shared State Access
# ============================================================================


def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state

    return app_state


# ============================================================================
# Price & Revenue
# ============================================================================


@router.post("/price/compare")
async def price_compare(
    energy_kwh: float = Body(..., gt=0, description="Energy amount in kWh"),
    utility_provider: str = Body("PEA", description="Utility provider: PEA or MEA"),
    tariff_category: str = Body("residential_1.2", description="Tariff category"),
    p2p_price: float | None = Body(None, description="Override P2P price"),
):
    """Compare utility vs P2P pricing for given consumption."""
    from smart_meter_simulator.core.price_provider import (
        get_comparison_service,
        UtilityProvider,
        TariffCategory,
    )

    try:
        provider = UtilityProvider(utility_provider)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Unknown provider: {utility_provider}"
        )

    try:
        category = TariffCategory(tariff_category)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Unknown category: {tariff_category}"
        )

    svc = get_comparison_service()
    return svc.compare(
        energy_kwh=energy_kwh,
        provider=provider,
        category=category,
        p2p_price=p2p_price,
    )


@router.get("/price/utility-rates")
async def utility_rates():
    """Get current utility tariff rates for all categories."""
    from smart_meter_simulator.core.price_provider import (
        get_utility_provider,
        TARIFF_MAP,
    )

    get_utility_provider()
    rates = []
    for cat, tariff in TARIFF_MAP.items():
        rates.append(
            {
                "category": cat.value,
                "name": tariff.name,
                "on_peak_rate": tariff.on_peak_rate,
                "off_peak_rate": tariff.off_peak_rate,
                "service_charge": tariff.service_charge,
            }
        )

    return {"providers": [{"name": "PEA/MEA", "rates": rates}]}


@router.get("/price/p2p-dynamic")
async def p2p_dynamic_price():
    """Get current dynamic P2P market clearing price."""
    from smart_meter_simulator.core.price_provider import get_p2p_provider

    p2p = get_p2p_provider()
    mcp = p2p.calculate_mcp()
    return {
        "market_clearing_price_baht_kwh": mcp,
        "supply_demand_ratio": p2p.supply_demand_ratio,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/price/history")
async def price_history(limit: int = Query(100, gt=0, le=10000)):
    """Get historical price snapshots."""
    from smart_meter_simulator.core.price_provider import get_price_history

    history = get_price_history()
    return {"history": history.get_history(limit), "stats": history.get_stats()}


@router.get("/price/stats")
async def price_stats():
    """Get price statistics summary."""
    from smart_meter_simulator.core.price_provider import (
        get_price_history,
        get_p2p_provider,
        get_utility_provider,
    )

    util = get_utility_provider()
    p2p = get_p2p_provider()
    hist = get_price_history()

    return {
        "utility_current_rate": util.get_current_rate(),
        "p2p_current_mcp": p2p.calculate_mcp(),
        "history": hist.get_stats(),
    }


@router.post("/p2p/calculate-cost")
async def p2p_calculate_cost(
    buyer_zone_id: int = Body(..., description="Buyer zone ID"),
    seller_zone_id: int = Body(..., description="Seller zone ID"),
    energy_amount: float = Body(..., gt=0, description="Energy in kWh"),
    agreed_price: float = Body(..., gt=0, description="Agreed price Baht/kWh"),
):
    """Calculate P2P transaction cost with wheeling and loss factors."""
    from smart_meter_simulator.core.price_provider import (
        WHEELING_CHARGE_RESIDENTIAL,
        GRID_LOSS_FACTOR,
    )

    # Simple distance-based wheeling (zones same = low, different = higher)
    distance_km = abs(buyer_zone_id - seller_zone_id) * 5.0  # ~5 km per zone
    wheeling_rate = WHEELING_CHARGE_RESIDENTIAL * (1.0 + distance_km / 100.0)
    loss_factor = GRID_LOSS_FACTOR * (1.0 + distance_km / 200.0)

    energy_cost = agreed_price * energy_amount
    wheeling_cost = wheeling_rate * energy_amount
    loss_cost = energy_cost * loss_factor
    total_cost = energy_cost + wheeling_cost + loss_cost

    return {
        "energy_cost": round(energy_cost, 2),
        "wheeling_cost": round(wheeling_cost, 2),
        "loss_cost": round(loss_cost, 2),
        "total_cost": round(total_cost, 2),
        "breakdown": {
            "distance_km": round(distance_km, 1),
            "wheeling_rate": round(wheeling_rate, 4),
            "loss_factor": round(loss_factor, 4),
        },
    }
