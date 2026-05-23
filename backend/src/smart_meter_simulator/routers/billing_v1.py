"""
Billing API v1 Router

Billing endpoints for GridTokenX Smart Meter Simulator:
- /api/v1/billing/summary      - Billing summary across all meters
- /api/v1/billing/meters       - Billing for all meters
- /api/v1/billing/meters/{id}  - Billing for specific meter
- /api/v1/billing/reset        - Reset billing period
"""

from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Billing"])


# ============================================================================
# Shared State Access
# ============================================================================


def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state

    return app_state


# ============================================================================
# Billing
# ============================================================================


@router.get("/billing/summary")
async def billing_summary():
    """Get billing summary across all meters."""
    state = _get_app_state()
    engine = state.engine
    engine.billing.calculate_all_bills(method="tou")
    return engine.billing.get_summary()


@router.get("/billing/meters/{meter_id}")
async def billing_meter(meter_id: str):
    """Get billing details for a single meter."""
    state = _get_app_state()
    engine = state.engine
    engine.billing.calculate_meter_bill(meter_id, method="tou")
    detail = engine.billing.get_meter_detail(meter_id)
    if detail is None:
        raise HTTPException(
            status_code=404, detail=f"Meter {meter_id} not found in billing records"
        )
    return detail


@router.get("/billing/meters")
async def billing_all_meters(method: str = "tou"):
    """Get billing for all meters."""
    state = _get_app_state()
    engine = state.engine
    bills = engine.billing.calculate_all_bills(method=method)
    return {"meters": bills, "total_billed_thb": engine.billing.total_billed_baht}


@router.post("/billing/reset")
async def billing_reset():
    """Reset billing period for all meters."""
    state = _get_app_state()
    engine = state.engine
    engine.billing.reset_billing_period()
    return {"status": "ok", "message": "Billing period reset"}
