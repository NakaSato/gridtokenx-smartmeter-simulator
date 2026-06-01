"""
Transactive Energy Controller.
Models price-responsive bidding curves and load adjustments for smart meters.
Inspired by PNNL TESP's RECS (Retail Energy Control System) agent logic.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class TransactiveController:
    """
    Models consumer price bidding and elasticity-based load scaling.
    Keeps a historical rolling window of cleared retail electricity prices to represent consumer expectations.
    """

    def __init__(self, history_limit: int = 96):  # E.g., 24 hours at 15-minute steps
        self.history_limit = history_limit
        self.price_history: List[float] = []

    def record_price(self, price: float):
        """Record a cleared price point to the rolling history."""
        if price > 0:
            self.price_history.append(price)
            if len(self.price_history) > self.history_limit:
                self.price_history.pop(0)

    def get_average_price(self, default_price: float = 0.28) -> float:
        """Calculate the historical average price."""
        if not self.price_history:
            return default_price
        return sum(self.price_history) / len(self.price_history)

    def calculate_responsive_load(
        self,
        base_load: float,
        current_price: float,
        sensitivity: float,
        min_load: float,
        max_load: float,
    ) -> float:
        """
        Scale base load based on price deviation from the rolling historical average.
        
        Args:
            base_load: The normal uncontrolled load in kW.
            current_price: Cleared price for the current step.
            sensitivity: Elasticity coefficient (higher values mean more responsive load).
            min_load: Minimum critical load constraint in kW.
            max_load: Maximum load threshold in kW.
            
        Returns:
            The adjusted load in kW.
        """
        avg_price = self.get_average_price(default_price=current_price)
        if avg_price <= 0:
            return base_load

        # Determine physical boundaries for scaling factor based on limits
        min_factor = min_load / base_load if base_load > 0 else 0.0
        max_factor = max_load / base_load if base_load > 0 else 1.0

        # Compute price deviation relative to average price
        deviation = (current_price - avg_price) / avg_price

        # Compute load scale factor: high price reduces load; low price increases load
        factor = 1.0 - (sensitivity * deviation)

        # Safety boundaries: do not scale outside physical boundaries
        factor = max(min_factor, min(max_factor, factor))
        factor = max(0.0, factor)  # Guard against negative factors

        adjusted_load = base_load * factor
        clamped_load = max(min_load, min(max_load, adjusted_load))

        logger.debug(
            f"Transactive Scaling: Base={base_load:.2f}kW, Price={current_price:.4f} (Avg={avg_price:.4f}), "
            f"Factor={factor:.2f}, Final={clamped_load:.2f}kW"
        )
        return clamped_load

    def calculate_transactive_metrics(
        self,
        base_load: float,
        clamped_load: float,
        current_price: float,
        sensitivity: float,
        time_factor: float = 0.25,
    ) -> tuple[float, float, float]:
        """
        Calculate transactive metrics: consumer surplus, bid limit, and setpoint offset.
        
        Args:
            base_load: Base load in kW.
            clamped_load: Clamped price-responsive load in kW.
            current_price: Cleared retail price (nodal price) in currency/kWh.
            sensitivity: Elasticity coefficient.
            time_factor: Time interval fraction of an hour (e.g. 0.25 for 15 mins).
            
        Returns:
            A tuple of (consumer_surplus, bid_limit, setpoint_offset).
        """
        setpoint_offset = clamped_load - base_load
        
        avg_price = self.get_average_price(default_price=current_price)
        if sensitivity <= 0 or base_load <= 0 or avg_price <= 0:
            return 0.0, current_price, setpoint_offset
            
        # 1. Bid Limit (willingness to pay for the initial base_load / reservation price)
        # bid_limit is the price at which load becomes 0 if we project the linear slope.
        # factor = 1.0 - sensitivity * (price - avg_price) / avg_price = 0
        # => price = avg_price * (1.0 + 1.0 / sensitivity)
        bid_limit = avg_price * (1.0 + 1.0 / sensitivity)
        
        # 2. Consumer Surplus (integrating P_willing(q) - current_price from 0 to clamped_load)
        # Quantity in energy (kWh)
        q_energy = clamped_load * time_factor
        q_base_energy = base_load * time_factor
        
        # P_willing(q) = avg_price * (1.0 + (1.0 - q / Q_base) / sensitivity)
        # Integration of (P_willing(q) - current_price) dq from 0 to q_energy:
        # term1 = (avg_price * (1.0 + 1.0 / sensitivity) - current_price) * q_energy
        # term2 = (avg_price / (2.0 * q_base_energy * sensitivity)) * (q_energy ** 2)
        # surplus = term1 - term2
        term1 = (avg_price * (1.0 + 1.0 / sensitivity) - current_price) * q_energy
        term2 = (avg_price / (2.0 * q_base_energy * sensitivity)) * (q_energy ** 2)
        surplus = term1 - term2
        
        # Guard surplus to be at least 0.0
        consumer_surplus = max(0.0, surplus)
        
        return consumer_surplus, bid_limit, setpoint_offset
