"""
Market Handler — orchestrates market clearing within the simulation tick cycle.

Plugs into the SimulationEngine's tick cycle between the VPP pre-processing
step and reading generation. Coordinates:
1. Collecting meter states
2. Having each TransactiveAgent generate bids/offers
3. Clearing the retail market
4. Distributing nodal prices to meters
5. Applying dispatch signals

Integration point in engine.tick():

    # 1. Frequency/VPP (existing)
    # 2. Market Clearing (NEW)  ← MarketHandler.run_market_clearing()
    # 3. Generate Readings (existing)
    # 4. Grid Update (existing)
    # 5. Billing (existing)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .retail_market import ThaiRetailMarket, MarketResult
from .market_agent import TransactiveAgent
from .tou_engine import TOUEngine

logger = logging.getLogger(__name__)


class MarketHandler:
    """Orchestrates transactive market clearing within the simulation tick.

    Args:
        market: The retail market clearing engine.
        tou_engine: TOU tariff engine for price references.
        clearing_interval: How often to clear the market (seconds).
            If the simulation tick interval doesn't match, the market
            clears at the nearest tick.

    Usage::

        from .market import ThaiRetailMarket, MarketHandler

        market = ThaiRetailMarket()
        handler = MarketHandler(market)
        handler.register_meters(meters)

        # In engine.tick():
        result = handler.run_market_clearing(meters, sim_time)
        nodal_prices = handler.get_nodal_prices()
    """

    def __init__(
        self,
        market: Optional[ThaiRetailMarket] = None,
        tou_engine: Optional[TOUEngine] = None,
        clearing_interval: int = 900,
    ):
        self.market = market or ThaiRetailMarket()
        self.tou_engine = tou_engine or TOUEngine()
        self.clearing_interval = clearing_interval

        self._agents: Dict[str, TransactiveAgent] = {}
        self._last_result: Optional[MarketResult] = None
        self._last_clearing_time: Optional[datetime] = None
        self._clearing_count: int = 0

    def register_meters(self, meters: List[Any]) -> None:
        """Register meters with the market handler.

        Creates a TransactiveAgent for each meter with appropriate
        flexibility settings based on device type.

        Args:
            meters: List of SmartMeter objects.
        """
        for meter in meters:
            meter_id = meter.meter_id
            config = getattr(meter, "config", {})
            meter_type = config.get("meter_type", "residential")

            # Set flexibility based on device type
            flexibility_map = {
                "residential": 0.7,
                "grid_consumer": 0.3,
                "commercial": 0.5,
                "solar_prosumer": 0.8,
                "hybrid_prosumer": 0.9,
                "battery_storage": 1.0,
                "ev_charger": 0.85,
                "dc_fast_charger": 0.15,
            }
            flexibility = flexibility_map.get(meter_type, 0.5)

            self._agents[meter_id] = TransactiveAgent(
                meter_id=meter_id,
                tou_engine=self.tou_engine,
                flexibility=flexibility,
            )

        logger.info(f"Registered {len(self._agents)} meters with MarketHandler")

    def run_market_clearing(
        self,
        meters: List[Any],
        sim_time: datetime,
    ) -> MarketResult:
        """Execute one market clearing cycle.

        Steps:
        1. Reset the market
        2. Each agent generates bids (consumers) and offers (generators)
        3. Submit bids and offers to the market
        4. Clear the market
        5. Apply dispatch signals to meters

        Args:
            meters: List of SmartMeter objects with current state.
            sim_time: Current simulation timestamp.

        Returns:
            MarketResult with clearing prices and allocations.
        """
        self.market.reset()

        # Get TOU price forecast for this period
        tou_result = self.tou_engine.calculate(sim_time)
        price_forecast = tou_result.total_rate

        # Collect bids and offers from all agents
        bids = []
        offers = []

        for meter in meters:
            agent = self._agents.get(meter.meter_id)
            if agent is None:
                continue

            # Generate bid (for consumers)
            bid = agent.generate_bid(meter, price_forecast, sim_time)
            if bid is not None:
                bids.append(bid)

            # Generate offer (for generators)
            offer = agent.generate_offer(meter, price_forecast, sim_time)
            if offer is not None:
                offers.append(offer)

        # Submit to market
        self.market.submit_bids(bids)
        self.market.submit_offers(offers)

        # Clear
        result = self.market.clear_market()
        self._last_result = result
        self._last_clearing_time = sim_time
        self._clearing_count += 1

        # Apply dispatch signals
        for meter in meters:
            agent = self._agents.get(meter.meter_id)
            if agent is None:
                continue

            # Check if this meter was allocated
            buy_qty = result.bid_allocations.get(meter.meter_id, 0.0)
            sell_qty = result.offer_allocations.get(meter.meter_id, 0.0)

            if buy_qty > 0:
                agent.apply_dispatch(meter, result.clearing_price, buy_qty, is_buyer=True)
            elif sell_qty > 0:
                agent.apply_dispatch(meter, result.clearing_price, sell_qty, is_buyer=False)

        logger.info(
            f"Market cleared #{self._clearing_count}: "
            f"price={result.clearing_price:.2f} Baht/kWh, "
            f"qty={result.clearing_quantity:.1f}kW, "
            f"bids={len(bids)}, offers={len(offers)}, "
            f"period={tou_result.period_name}"
        )

        return result

    def get_nodal_prices(self) -> Dict[str, float]:
        """Get per-meter nodal prices from the last market clearing.

        Returns:
            Dict mapping meter_id → nodal price (Baht/kWh).
        """
        if self._last_result is None:
            return {}
        return dict(self._last_result.nodal_prices)

    def get_clearing_price(self) -> float:
        """Get the last market clearing price (Baht/kWh)."""
        if self._last_result is None:
            return self.tou_engine.on_peak_rate + self.tou_engine.ft_adjustment
        return self._last_result.clearing_price

    def get_last_result(self) -> Optional[MarketResult]:
        """Get the result of the most recent market clearing."""
        return self._last_result
