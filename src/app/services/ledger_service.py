"""
Ledger Service for Grid Event Logging.

This module provides logging and retrieval of grid events, readings,
and any transactions that occur in the simulation.

Note: P2P trading/matching is handled by the API Gateway and Blockchain.
This service focuses on local event logging for simulation analysis.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from ..core.database import DatabaseManager
from ..models.transaction import Transaction

logger = logging.getLogger(__name__)


@dataclass
class GridEvent:
    """
    Represents a grid event for logging purposes.
    
    Can be used to log:
    - Voltage violations
    - Transformer overloads
    - Battery dispatch actions
    - Solar generation milestones
    """
    event_type: str
    meter_id: Optional[str]
    zone_id: Optional[int]
    description: str
    value: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LedgerService:
    """
    Manages the recording and retrieval of grid events and transactions.
    
    This service provides:
    - Grid event logging (violations, dispatch actions)
    - Transaction history (for local analysis, not P2P matching)
    - Energy generation/consumption summaries
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._event_log: List[GridEvent] = []
        self._max_events = 1000  # Keep last 1000 events in memory

    def log_event(self, event: GridEvent) -> None:
        """Log a grid event."""
        self._event_log.append(event)
        
        # Trim old events
        if len(self._event_log) > self._max_events:
            self._event_log = self._event_log[-self._max_events:]
        
        logger.debug(f"Grid Event: {event.event_type} - {event.description}")

    def log_voltage_violation(
        self, 
        meter_id: str, 
        zone_id: int, 
        voltage_pu: float,
        threshold: str = "LOW"  # "LOW" or "HIGH"
    ) -> None:
        """Log a voltage violation event."""
        event = GridEvent(
            event_type="VOLTAGE_VIOLATION",
            meter_id=meter_id,
            zone_id=zone_id,
            description=f"{threshold} voltage at {voltage_pu:.3f} pu",
            value=voltage_pu
        )
        self.log_event(event)

    def log_battery_dispatch(
        self,
        meter_id: str,
        zone_id: int,
        power_kw: float,
        new_level: float
    ) -> None:
        """Log a battery dispatch action."""
        action = "DISCHARGE" if power_kw > 0 else "CHARGE"
        event = GridEvent(
            event_type=f"BATTERY_{action}",
            meter_id=meter_id,
            zone_id=zone_id,
            description=f"Battery {action.lower()} {abs(power_kw):.2f} kW, level: {new_level:.1f}%",
            value=power_kw
        )
        self.log_event(event)

    def log_generation_milestone(
        self,
        meter_id: str,
        zone_id: int,
        total_kwh: float,
        milestone_type: str = "DAILY"
    ) -> None:
        """Log solar generation milestone."""
        event = GridEvent(
            event_type=f"GENERATION_{milestone_type}",
            meter_id=meter_id,
            zone_id=zone_id,
            description=f"Generated {total_kwh:.2f} kWh ({milestone_type.lower()})",
            value=total_kwh
        )
        self.log_event(event)

    def record_transaction(
        self,
        buyer_id: str,
        seller_id: str,
        amount_kwh: float,
        price_per_kwh: float,
        tx_type: str = "GRID_EXPORT",
        zone_from: int = 0,
        zone_to: int = 0,
        tx_hash: Optional[str] = None
    ) -> int:
        """
        Record a transaction (grid export/import or local transfer).
        
        Returns:
            Transaction ID or -1 on failure
        """
        try:
            transaction = Transaction(
                id=None,
                buyer_id=buyer_id,
                seller_id=seller_id,
                amount_kwh=amount_kwh,
                price_per_kwh=price_per_kwh,
                total_cost=amount_kwh * price_per_kwh,
                timestamp=datetime.now(),
                transaction_type=tx_type,
                zone_from=zone_from,
                zone_to=zone_to,
                tx_hash=tx_hash
            )
            
            tx_id = self.db_manager.save_transaction(transaction)
            if tx_id > 0:
                logger.debug(f"Recorded transaction {tx_id}: {seller_id} -> {buyer_id}")
            return tx_id
            
        except Exception as e:
            logger.error(f"Failed to record transaction: {e}")
            return -1

    def get_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent transactions."""
        return self.db_manager.get_recent_transactions(limit)

    def get_events(
        self, 
        event_type: Optional[str] = None,
        zone_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent grid events with optional filtering.
        
        Args:
            event_type: Filter by event type (e.g., "VOLTAGE_VIOLATION")
            zone_id: Filter by zone
            limit: Maximum number of events to return
        """
        events = self._event_log
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if zone_id is not None:
            events = [e for e in events if e.zone_id == zone_id]
        
        # Return most recent first
        events = events[-limit:][::-1]
        
        return [
            {
                "event_type": e.event_type,
                "meter_id": e.meter_id,
                "zone_id": e.zone_id,
                "description": e.description,
                "value": e.value,
                "timestamp": e.timestamp.isoformat()
            }
            for e in events
        ]

    def get_zone_summary(self, zone_id: int) -> Dict[str, Any]:
        """Get event summary for a specific zone."""
        zone_events = [e for e in self._event_log if e.zone_id == zone_id]
        
        violations = [e for e in zone_events if "VIOLATION" in e.event_type]
        dispatches = [e for e in zone_events if "BATTERY" in e.event_type]
        
        return {
            "zone_id": zone_id,
            "total_events": len(zone_events),
            "voltage_violations": len(violations),
            "battery_dispatches": len(dispatches),
            "recent_events": self.get_events(zone_id=zone_id, limit=10)
        }
