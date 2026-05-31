"""
Thai Retail Electricity Market — Double-Auction Clearing Engine.

Implements a double-auction market clearing mechanism adapted from TESP's
DSO+T Retail Market, with Thai-specific parameters:

- Currency: Thai Baht (฿)
- Price cap: 8.0 Baht/kWh
- Voltage-constrained nodal pricing
- PEA/MEA tariff structure integration

The market clears by intersecting aggregated supply and demand curves,
producing a uniform clearing price and per-meter allocations.

References:
    TESP DSO+T: dsot.retail_market.RetailMarket (PNNL)
    Market structure: https://tesp.readthedocs.io/en/latest/
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .curves import Bid, Offer, DemandCurve, SupplyCurve, find_intersection

logger = logging.getLogger(__name__)


@dataclass
class MarketResult:
    """Result of a market clearing cycle.

    Attributes:
        clearing_price: Uniform clearing price (Baht/kWh).
        clearing_quantity: Total cleared quantity (kW).
        total_demand: Total demand submitted (kW).
        total_supply: Total supply submitted (kW).
        nodal_prices: Per-meter nodal prices (Baht/kWh), including congestion adjustments.
        bid_allocations: Per-meter cleared buy quantities (kW).
        offer_allocations: Per-meter cleared sell quantities (kW).
        unserved_demand: Demand not met by supply (kW).
        curtailed_supply: Supply not accepted by market (kW).
        converged: Whether the market clearing converged.
    """
    clearing_price: float = 0.0
    clearing_quantity: float = 0.0
    total_demand: float = 0.0
    total_supply: float = 0.0
    nodal_prices: Dict[str, float] = field(default_factory=dict)
    bid_allocations: Dict[str, float] = field(default_factory=dict)
    offer_allocations: Dict[str, float] = field(default_factory=dict)
    unserved_demand: float = 0.0
    curtailed_supply: float = 0.0
    converged: bool = False


class ThaiRetailMarket:
    """Double-auction retail market clearing engine for the Thai electricity grid.

    Market clearing process:
    1. Collect bids (buy orders) from consuming meters
    2. Collect offers (sell orders) from generating meters
    3. Build aggregated supply and demand curves
    4. Find intersection → uniform clearing price
    5. Allocate quantities based on price priority
    6. Apply nodal price adjustments for congestion

    Args:
        price_cap: Maximum allowable price (Baht/kWh). Default 8.0.
        price_floor: Minimum allowable price (Baht/kWh). Default 0.0.
        default_price: Fallback price when no market activity. Default 3.50.
        voltage_threshold: Voltage (pu) below which congestion pricing applies.
        congestion_penalty: Price adder per 0.01 pu voltage drop below threshold.

    Usage::

        market = ThaiRetailMarket()
        market.submit_bids([Bid("meter_1", 5.0, 6.0)])
        market.submit_offers([Offer("meter_2", 3.0, 2.0)])
        result = market.clear_market()
    """

    def __init__(
        self,
        price_cap: float = 8.0,
        price_floor: float = 0.0,
        default_price: float = 3.50,
        voltage_threshold: float = 0.95,
        congestion_penalty: float = 0.50,
    ):
        self.price_cap = price_cap
        self.price_floor = price_floor
        self.default_price = default_price
        self.voltage_threshold = voltage_threshold
        self.congestion_penalty = congestion_penalty

        self._demand_curve = DemandCurve()
        self._supply_curve = SupplyCurve()
        self._last_result: Optional[MarketResult] = None

    def reset(self) -> None:
        """Reset the market for a new clearing cycle."""
        self._demand_curve = DemandCurve()
        self._supply_curve = SupplyCurve()

    def submit_bids(self, bids: List[Bid]) -> None:
        """Submit demand-side bids for the current clearing cycle."""
        for bid in bids:
            # Enforce price cap
            if bid.price > self.price_cap:
                bid.price = self.price_cap
            self._demand_curve.add_bid(bid)

    def submit_offers(self, offers: List[Offer]) -> None:
        """Submit supply-side offers for the current clearing cycle."""
        for offer in offers:
            # Enforce price floor
            if offer.price < self.price_floor:
                offer.price = self.price_floor
            self._supply_curve.add_offer(offer)

    def clear_market(self) -> MarketResult:
        """Execute the double-auction market clearing.

        Returns:
            MarketResult with clearing price, quantities, and per-meter allocations.
        """
        result = MarketResult()
        result.total_demand = self._demand_curve.total_quantity
        result.total_supply = self._supply_curve.total_quantity

        # Edge case: no market activity
        if result.total_demand == 0 and result.total_supply == 0:
            result.clearing_price = self.default_price
            result.converged = True
            self._last_result = result
            return result

        # Edge case: only demand (no supply) → price cap
        if result.total_supply == 0:
            result.clearing_price = self.price_cap
            result.clearing_quantity = 0.0
            result.unserved_demand = result.total_demand
            self._allocate_demand_only(result)
            result.converged = True
            self._last_result = result
            return result

        # Edge case: only supply (no demand) → price floor
        if result.total_demand == 0:
            result.clearing_price = self.price_floor
            result.clearing_quantity = 0.0
            result.curtailed_supply = result.total_supply
            self._allocate_supply_only(result)
            result.converged = True
            self._last_result = result
            return result

        # Build curves
        demand_q, demand_p = self._demand_curve.build()
        supply_q, supply_p = self._supply_curve.build()

        # Find intersection
        clearing_q, clearing_p = find_intersection(demand_q, demand_p, supply_q, supply_p)

        # Clamp clearing price
        clearing_p = max(self.price_floor, min(self.price_cap, clearing_p))

        result.clearing_price = clearing_p
        result.clearing_quantity = clearing_q
        result.unserved_demand = max(0, result.total_demand - clearing_q)
        result.curtailed_supply = max(0, result.total_supply - clearing_q)

        # Allocate quantities to individual meters
        self._allocate_bids(result, clearing_p)
        self._allocate_offers(result, clearing_p)

        result.converged = True
        self._last_result = result
        return result

    def get_nodal_prices(
        self, bus_voltages: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Get per-meter nodal prices including congestion adjustments.

        If bus voltages are provided, meters on buses with voltage below
        the threshold receive a congestion price adder (marginal pricing).

        Args:
            bus_voltages: Dict mapping bus name → voltage magnitude (pu).

        Returns:
            Dict mapping meter_id → nodal price (Baht/kWh).
        """
        if self._last_result is None:
            return {}

        prices = dict(self._last_result.nodal_prices)

        if bus_voltages:
            for meter_id, base_price in prices.items():
                # Apply congestion pricing if voltage is low
                # (In a full implementation, we'd look up the meter's bus)
                # For now, apply a uniform adjustment based on min voltage
                min_v = min(bus_voltages.values()) if bus_voltages else 1.0
                if min_v < self.voltage_threshold:
                    deficit = self.voltage_threshold - min_v
                    congestion_adder = deficit * 100 * self.congestion_penalty  # per 0.01 pu
                    prices[meter_id] = min(base_price + congestion_adder, self.price_cap)

        return prices

    def get_last_result(self) -> Optional[MarketResult]:
        """Get the result of the most recent market clearing."""
        return self._last_result

    # ── Allocation helpers ──────────────────────────────────────────────────

    def _allocate_bids(self, result: MarketResult, clearing_price: float) -> None:
        """Allocate cleared quantities to demand-side bidders."""
        sorted_bids = self._demand_curve.get_sorted_bids()
        remaining = result.clearing_quantity

        for bid in sorted_bids:
            if remaining <= 0:
                result.bid_allocations[bid.meter_id] = 0.0
            elif bid.price >= clearing_price:
                allocated = min(bid.quantity_kw, remaining)
                result.bid_allocations[bid.meter_id] = allocated
                remaining -= allocated
            else:
                result.bid_allocations[bid.meter_id] = 0.0

            result.nodal_prices[bid.meter_id] = clearing_price

    def _allocate_offers(self, result: MarketResult, clearing_price: float) -> None:
        """Allocate cleared quantities to supply-side offerers."""
        sorted_offers = self._supply_curve.get_sorted_offers()
        remaining = result.clearing_quantity

        for offer in sorted_offers:
            if remaining <= 0:
                result.offer_allocations[offer.meter_id] = 0.0
            elif offer.price <= clearing_price:
                allocated = min(offer.quantity_kw, remaining)
                result.offer_allocations[offer.meter_id] = allocated
                remaining -= allocated
            else:
                result.offer_allocations[offer.meter_id] = 0.0

            if offer.meter_id not in result.nodal_prices:
                result.nodal_prices[offer.meter_id] = clearing_price

    def _allocate_demand_only(self, result: MarketResult) -> None:
        """Set allocations when there is only demand (price cap scenario)."""
        for bid in self._demand_curve.get_sorted_bids():
            result.bid_allocations[bid.meter_id] = 0.0
            result.nodal_prices[bid.meter_id] = self.price_cap

    def _allocate_supply_only(self, result: MarketResult) -> None:
        """Set allocations when there is only supply (price floor scenario)."""
        for offer in self._supply_curve.get_sorted_offers():
            result.offer_allocations[offer.meter_id] = 0.0
            result.nodal_prices[offer.meter_id] = self.price_floor
