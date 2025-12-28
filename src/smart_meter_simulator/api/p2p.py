
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

# Import P2P Service and Types
# Note: We import from services directly. The running instance is accessed via app.state
from ..services.transaction_service import P2PTransactionService, TransactionCost

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/p2p",
    tags=["p2p"],
    responses={404: {"description": "Not found"}},
)

# --- Pydantic Models ---

class TransactionCostRequest(BaseModel):
    buyer_zone_id: int = Field(..., description="ID of the buyer's zone")
    seller_zone_id: int = Field(..., description="ID of the seller's zone")
    energy_amount: float = Field(..., gt=0, description="Amount of energy to trade in kWh")
    agreed_price: Optional[float] = Field(None, description="Negotiated price (THB/kWh). Defaults to market base price.")

class MarketPricesResponse(BaseModel):
    base_price_thb_kwh: float
    grid_import_price_thb_kwh: float
    grid_export_price_thb_kwh: float
    loss_allocation_model: str
    wheeling_charges: Dict[str, float]
    loss_factors: Dict[str, float]

# --- Dependency ---

def get_transaction_service(request: Request) -> P2PTransactionService:
    """
    Retrieve the P2PTransactionService from the active simulation engine.
    """
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation Engine not initialized")
    
    # Check if the engine has the transaction service (PhysicsSimulationEngine)
    if not hasattr(engine, "transaction_service"):
        raise HTTPException(status_code=501, detail="Current engine does not support P2P transactions. Ensure PhysicsSimulationEngine is active.")
        
    return engine.transaction_service

# --- Endpoints ---

@router.post("/calculate-cost", response_model=TransactionCost)
async def calculate_transaction_cost(
    request: TransactionCostRequest,
    service: P2PTransactionService = Depends(get_transaction_service)
):
    """
    Calculate the total cost and effective energy for a proposed P2P transaction.
    Applicable for 'Receiver Pays' or 'Sender Pays' models as configured.
    """
    try:
        cost = service.calculate_transaction_cost(
            buyer_zone=request.buyer_zone_id,
            seller_zone=request.seller_zone_id,
            energy_amount=request.energy_amount,
            agreed_price=request.agreed_price
        )
        return cost
    except Exception as e:
        logger.error(f"Error calculating transaction cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-prices", response_model=MarketPricesResponse)
async def get_market_prices(
    service: P2PTransactionService = Depends(get_transaction_service)
):
    """
    Get current market pricing configurations, including:
    - Base energy prices
    - Wheeling charge matrix (Distribution fees)
    - Technical loss factor matrix
    """
    try:
        summary = service.get_pricing_summary()
        return summary
    except Exception as e:
        logger.error(f"Error fetching market prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))
