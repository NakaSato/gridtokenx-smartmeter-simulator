from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/p2p", tags=["p2p"])

class CostCalculationRequest(BaseModel):
    buyer_zone_id: int
    seller_zone_id: int
    energy_amount: float
    agreed_price: Optional[float] = 4.0  # Default to base market price of 4.0 THB/kWh

@router.post("/calculate-cost")
async def calculate_p2p_cost(request: CostCalculationRequest, req: Request):
    """
    Calculate wheeling charges and technical losses for a P2P trade.
    Called by the API Gateway during matching and settlement.
    """
    engine = getattr(req.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulator engine not initialized")
    
    try:
        zoning_service = engine.zoning_service
        
        # 1. Calculate Wheeling Charge (THB)
        wheeling_charge = zoning_service.calculate_wheeling_charge(
            request.seller_zone_id, 
            request.buyer_zone_id, 
            request.energy_amount
        )
        
        # 2. Calculate Loss Factor (%)
        loss_factor = zoning_service.calculate_loss_factor(
            request.seller_zone_id, 
            request.buyer_zone_id
        )
        
        # 3. Calculate Energy Cost (THB)
        energy_cost = request.energy_amount * request.agreed_price
        
        # 4. Calculate Loss Cost (THB)
        # Loss cost is the value of energy lost at the agreed price
        loss_cost = request.energy_amount * loss_factor * request.agreed_price
        
        # 5. Calculate Effective Energy (kWh reaching the buyer)
        effective_energy = request.energy_amount * (1.0 - loss_factor)
        
        # 6. Calculate Total Cost (THB)
        total_cost = energy_cost + wheeling_charge + loss_cost
        
        # 7. Calculate zone distance (simplified - 0 for same zone, otherwise estimate)
        zone_distance_km = 0.0 if request.buyer_zone_id == request.seller_zone_id else 5.0
        
        return {
            "energy_cost": round(energy_cost, 4),
            "wheeling_charge": round(wheeling_charge, 4),
            "loss_cost": round(loss_cost, 4),
            "total_cost": round(total_cost, 4),
            "effective_energy": round(effective_energy, 4),
            "loss_factor": round(loss_factor, 4),
            "loss_allocation": "RECEIVER",  # Loss is paid by receiver
            "zone_distance_km": round(zone_distance_km, 2),
            "buyer_zone": request.buyer_zone_id,
            "seller_zone": request.seller_zone_id,
            "is_grid_compliant": True,
            "grid_violation_reason": None
        }
    except Exception as e:
        logger.error(f"Cost calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

