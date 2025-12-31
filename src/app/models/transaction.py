from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Transaction:
    """
    Represents an executed energy trade.
    """
    id: Optional[int]
    buyer_id: str
    seller_id: str
    amount_kwh: float
    price_per_kwh: float
    total_cost: float
    timestamp: datetime
    transaction_type: str = "QUANTUM" # QUANTUM, P2P_MANUAL, GRID
    zone_from: int = 0
    zone_to: int = 0
    tx_hash: Optional[str] = None
