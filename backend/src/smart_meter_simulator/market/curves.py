"""
Supply and Demand Curves for Double-Auction Market Clearing.

Aggregates individual bids (demand) and offers (supply) into ordered curves
and finds the market-clearing price at their intersection.

References TESP's dsot.retail_market curve aggregation pattern.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Bid:
    """A demand-side bid (buy order).

    Attributes:
        meter_id: ID of the meter submitting the bid.
        quantity_kw: Maximum energy the meter wants to buy (kW).
        price: Maximum price the meter is willing to pay (Baht/kWh).
        flexibility: 0.0–1.0, how flexible the demand is (1 = fully flexible).
    """
    meter_id: str
    quantity_kw: float
    price: float
    flexibility: float = 1.0


@dataclass
class Offer:
    """A supply-side offer (sell order).

    Attributes:
        meter_id: ID of the meter submitting the offer.
        quantity_kw: Maximum energy the meter can sell (kW).
        price: Minimum price the meter is willing to accept (Baht/kWh).
        renewable_fraction: 0.0–1.0, fraction from renewable sources.
    """
    meter_id: str
    quantity_kw: float
    price: float
    renewable_fraction: float = 0.0


class DemandCurve:
    """Aggregated demand curve built from individual bids.

    Sorts bids by price in descending order (highest willingness-to-pay first),
    producing a monotonically non-increasing demand curve.
    """

    def __init__(self):
        self._bids: List[Bid] = []

    def add_bid(self, bid: Bid) -> None:
        """Add a bid to the demand curve."""
        if bid.quantity_kw > 0 and bid.price >= 0:
            self._bids.append(bid)

    @property
    def total_quantity(self) -> float:
        """Total demand across all bids (kW)."""
        return sum(b.quantity_kw for b in self._bids)

    def build(self) -> Tuple[np.ndarray, np.ndarray]:
        """Build the aggregated demand curve.

        Returns:
            Tuple of (cumulative_quantity, price) arrays, sorted by price descending.
        """
        if not self._bids:
            return np.array([0.0]), np.array([0.0])

        # Sort by price descending (highest willingness-to-pay first)
        sorted_bids = sorted(self._bids, key=lambda b: b.price, reverse=True)

        quantities = []
        prices = []
        cumulative = 0.0
        for bid in sorted_bids:
            cumulative += bid.quantity_kw
            quantities.append(cumulative)
            prices.append(bid.price)

        return np.array(quantities), np.array(prices)

    def get_sorted_bids(self) -> List[Bid]:
        """Return bids sorted by price descending."""
        return sorted(self._bids, key=lambda b: b.price, reverse=True)


class SupplyCurve:
    """Aggregated supply curve built from individual offers.

    Sorts offers by price in ascending order (lowest cost first),
    producing a monotonically non-decreasing supply curve.
    """

    def __init__(self):
        self._offers: List[Offer] = []

    def add_offer(self, offer: Offer) -> None:
        """Add an offer to the supply curve."""
        if offer.quantity_kw > 0 and offer.price >= 0:
            self._offers.append(offer)

    @property
    def total_quantity(self) -> float:
        """Total supply across all offers (kW)."""
        return sum(o.quantity_kw for o in self._offers)

    def build(self) -> Tuple[np.ndarray, np.ndarray]:
        """Build the aggregated supply curve.

        Returns:
            Tuple of (cumulative_quantity, price) arrays, sorted by price ascending.
        """
        if not self._offers:
            return np.array([0.0]), np.array([0.0])

        # Sort by price ascending (cheapest first)
        sorted_offers = sorted(self._offers, key=lambda o: o.price)

        quantities = []
        prices = []
        cumulative = 0.0
        for offer in sorted_offers:
            cumulative += offer.quantity_kw
            quantities.append(cumulative)
            prices.append(offer.price)

        return np.array(quantities), np.array(prices)

    def get_sorted_offers(self) -> List[Offer]:
        """Return offers sorted by price ascending."""
        return sorted(self._offers, key=lambda o: o.price)


def find_intersection(
    demand_q: np.ndarray, demand_p: np.ndarray,
    supply_q: np.ndarray, supply_p: np.ndarray,
) -> Tuple[float, float]:
    """Find the intersection of supply and demand curves.

    Uses piecewise-linear interpolation to find the crossing point.

    Args:
        demand_q: Cumulative demand quantities.
        demand_p: Demand prices (descending order).
        supply_q: Cumulative supply quantities.
        supply_p: Supply prices (ascending order).

    Returns:
        Tuple of (clearing_quantity, clearing_price).
    """
    # Extend both curves to cover full range
    max_q = max(demand_q[-1], supply_q[-1]) if len(demand_q) > 0 and len(supply_q) > 0 else 0.0
    max_p = max(demand_p[0], supply_p[-1]) if len(demand_p) > 0 and len(supply_p) > 0 else 0.0

    # Build step-wise functions for intersection search
    # Search from q=0 to max_q in fine increments
    n_steps = max(len(demand_q), len(supply_q)) * 10 + 1
    q_range = np.linspace(0, max_q * 1.1, n_steps)

    # Interpolate prices at each quantity
    if len(demand_q) > 1:
        d_prices = np.interp(q_range, demand_q, demand_p, right=0.0)
    else:
        d_prices = np.full(n_steps, demand_p[0] if len(demand_p) > 0 else 0.0)

    if len(supply_q) > 1:
        s_prices = np.interp(q_range, supply_q, supply_p, right=max_p * 2)
    else:
        s_prices = np.full(n_steps, supply_p[0] if len(supply_p) > 0 else 0.0)

    # Find crossing: demand_price - supply_price changes sign
    diff = d_prices - s_prices

    # Find last index where demand >= supply (demand exceeds supply)
    positive_mask = diff >= 0
    if not np.any(positive_mask):
        # Supply always exceeds demand → clearing at minimum price
        return float(demand_q[-1]) if len(demand_q) > 0 else 0.0, float(supply_p[0]) if len(supply_p) > 0 else 0.0

    if np.all(positive_mask):
        # Demand always exceeds supply → clearing at maximum price
        return float(supply_q[-1]) if len(supply_q) > 0 else 0.0, float(demand_p[0]) if len(demand_p) > 0 else 0.0

    # Find crossing point
    crossing_idx = np.where(~positive_mask)[0][0] - 1
    if crossing_idx < 0:
        crossing_idx = 0

    clearing_q = float(q_range[crossing_idx])
    clearing_p = float((d_prices[crossing_idx] + s_prices[crossing_idx]) / 2.0)

    return max(clearing_q, 0.0), max(clearing_p, 0.0)
