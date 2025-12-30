import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.database import DatabaseManager
from ..models.transaction import Transaction
from ..simulation.quantum_optimizer import TradeMatch

logger = logging.getLogger(__name__)

class LedgerService:
    """
    Manages the recording and retrieval of energy trade transactions.
    Functions as the 'Blockchain' or 'Ledger' abstraction for the simulator.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def record_match(self, match: TradeMatch, type: str = "QUANTUM", zones: Optional[tuple] = None) -> int:
        """
        Records a trade match as a persistent transaction.
        """
        try:
            timestamp = datetime.now()
            
            # zones is (buyer_zone, seller_zone) if provided
            zone_from = zones[1] if zones else 0 # Seller Zone
            zone_to = zones[0] if zones else 0   # Buyer Zone
            
            transaction = Transaction(
                id=None,
                buyer_id=match.buyer_id,
                seller_id=match.seller_id,
                amount_kwh=match.amount_kwh,
                price_per_kwh=match.price_per_kwh,
                total_cost=match.total_cost,
                timestamp=timestamp,
                transaction_type=type,
                zone_from=zone_from,
                zone_to=zone_to,
                tx_hash=match.tx_hash if hasattr(match, 'tx_hash') else None
            )
            
            tx_id = self.db_manager.save_transaction(transaction)
            if tx_id > 0:
                logger.debug(f"Recorded transaction {tx_id}: {match.buyer_id} -> {match.seller_id}")
            return tx_id
            
        except Exception as e:
            logger.error(f"Failed to record match: {e}")
            return -1

    def get_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves recent transactions.
        """
        return self.db_manager.get_recent_transactions(limit)
