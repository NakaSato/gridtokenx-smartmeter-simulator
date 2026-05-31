"""
Transactive Agent — per-meter bid/offer generation.

Each meter in the simulation has a TransactiveAgent that generates market
bids (for consumption) or offers (for generation) based on:

- Current device state (load, generation, battery SOC)
- Price forecast from the TOU engine
- Flexibility and comfort settings
- Device type (residential, commercial, prosumer, EV charger, etc.)

References TESP's agent bidding patterns from the DSO+T study.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .curves import Bid, Offer
from .tou_engine import TOUEngine

logger = logging.getLogger(__name__)


class TransactiveAgent:
    """Per-meter agent that generates bids and offers for the transactive market.

    The agent's bidding strategy varies by device type:

    +-------------------------+------------------------------------------+
    | Device Type             | Market Behavior                          |
    +=========================+==========================================+
    | Residential Consumer    | Bids at TOU rate × flexibility factor    |
    | Solar Prosumer          | Offers excess solar at marginal cost     |
    | Hybrid Prosumer         | Both bids and offers based on net load   |
    | Battery Storage         | Offers at SOC-weighted price             |
    | EV Charger              | Bids at flexible TOU rate                |
    | DC Fast Charger         | Bids at premium rate (low flexibility)   |
    | Commercial              | Bids at business-rate premium            |
    +-------------------------+------------------------------------------+

    Args:
        meter_id: Unique meter identifier.
        tou_engine: TOU tariff engine for price reference.
        flexibility: Demand flexibility factor (0.0 = none, 1.0 = fully flexible).
        comfort_threshold: Max price the consumer will accept before curtailment.
    """

    def __init__(
        self,
        meter_id: str,
        tou_engine: Optional[TOUEngine] = None,
        flexibility: float = 0.7,
        comfort_threshold: float = 7.0,
    ):
        self.meter_id = meter_id
        self.tou_engine = tou_engine or TOUEngine()
        self.flexibility = flexibility
        self.comfort_threshold = comfort_threshold

    def generate_bid(
        self,
        meter: Any,
        price_forecast: Optional[float] = None,
        sim_time: Optional[datetime] = None,
    ) -> Optional[Bid]:
        """Generate a demand bid for a consuming meter.

        The bid price is based on the TOU rate adjusted by flexibility:
        - High flexibility → bid closer to TOU rate (willing to curtail)
        - Low flexibility → bid above TOU rate (needs power)

        Args:
            meter: SmartMeter object with current state.
            price_forecast: Expected market price (Baht/kWh).
            sim_time: Current simulation time.

        Returns:
            A Bid if the meter has net consumption, else None.
        """
        # Get current load
        active_power_kw = getattr(meter, "active_power_kw", 0.0) or 0.0
        if active_power_kw <= 0:
            return None  # Net generator, not a consumer

        # Get base price from TOU or forecast
        if price_forecast is not None:
            base_price = price_forecast
        elif sim_time is not None:
            tou_result = self.tou_engine.calculate(sim_time)
            base_price = tou_result.total_rate
        else:
            base_price = self.tou_engine.on_peak_rate + self.tou_engine.ft_adjustment

        # Adjust bid price based on flexibility and device type
        config = getattr(meter, "config", {})
        meter_type = config.get("meter_type", "residential")

        if meter_type == "dc_fast_charger":
            # DC fast chargers have low flexibility — bid aggressively
            bid_price = base_price * 1.3
            flex = 0.2
        elif meter_type == "commercial":
            # Commercial: moderate flexibility during business hours
            bid_price = base_price * 1.1
            flex = self.flexibility * 0.5
        elif meter_type == "ev_charger":
            # EV chargers: flexible (can delay charging)
            bid_price = base_price * 0.9
            flex = min(self.flexibility * 1.5, 1.0)
        else:
            # Residential: standard flexibility
            bid_price = base_price * (0.8 + 0.2 * (1 - self.flexibility))
            flex = self.flexibility

        # Check comfort threshold — don't bid above it
        bid_price = min(bid_price, self.comfort_threshold)

        return Bid(
            meter_id=self.meter_id,
            quantity_kw=active_power_kw,
            price=bid_price,
            flexibility=flex,
        )

    def generate_offer(
        self,
        meter: Any,
        price_forecast: Optional[float] = None,
        sim_time: Optional[datetime] = None,
    ) -> Optional[Offer]:
        """Generate a supply offer for a generating meter.

        The offer price is based on the marginal cost of generation:
        - Solar: near-zero marginal cost (0.5 Baht/kWh base)
        - Battery: depends on SOC and time-of-day

        Args:
            meter: SmartMeter object with current state.
            price_forecast: Expected market price (Baht/kWh).
            sim_time: Current simulation time.

        Returns:
            An Offer if the meter has net generation, else None.
        """
        # Get current generation
        gen_kw = getattr(meter, "active_power_kw", 0.0) or 0.0
        if gen_kw >= 0:
            # Check for battery discharge
            bess = getattr(meter, "bess", None)
            if bess:
                discharge_kw = getattr(bess, "discharge_kw", 0.0) or 0.0
                if discharge_kw > 0:
                    gen_kw = discharge_kw
                else:
                    return None
            else:
                return None  # Net consumer, not a generator

        gen_kw = abs(gen_kw)  # Make positive

        config = getattr(meter, "config", {})
        meter_type = config.get("meter_type", "residential")

        # Offer price based on generation source
        if meter_type in ("solar_prosumer", "hybrid_prosumer"):
            # Solar: very low marginal cost
            offer_price = 0.5  # Baht/kWh (near-zero marginal cost)
            renewable_frac = 1.0
        elif meter_type == "battery_storage":
            # Battery: offer price depends on SOC
            bess = getattr(meter, "bess", None)
            soc = getattr(bess, "soc", 0.5) if bess else 0.5
            # Higher SOC → willing to sell cheaper (battery is full)
            offer_price = 1.0 + (1.0 - soc) * 3.0  # 1-4 Baht/kWh
            renewable_frac = 0.0
        else:
            # Default: offer at TOU rate
            offer_price = 2.0
            renewable_frac = 0.0

        return Offer(
            meter_id=self.meter_id,
            quantity_kw=gen_kw,
            price=offer_price,
            renewable_fraction=renewable_frac,
        )

    def apply_dispatch(
        self,
        meter: Any,
        cleared_price: float,
        cleared_quantity: float,
        is_buyer: bool = True,
    ) -> None:
        """Apply the market clearing result to the meter.

        For buyers: if clearing price exceeds comfort threshold, curtail load.
        For sellers: set generation/dispatch target to cleared quantity.

        Args:
            meter: SmartMeter object to update.
            cleared_price: The market clearing price (Baht/kWh).
            cleared_quantity: The allocated quantity (kW).
            is_buyer: Whether this meter is buying (True) or selling (False).
        """
        if is_buyer:
            if cleared_price > self.comfort_threshold:
                # Curtail load — reduce by flexibility amount
                curtailment = getattr(meter, "active_power_kw", 0) * self.flexibility
                if hasattr(meter, "vpp_dispatch_kw"):
                    meter.vpp_dispatch_kw = -curtailment  # Negative = reduce load
                logger.debug(
                    f"Market curtailment for {self.meter_id}: "
                    f"{curtailment:.1f}kW at {cleared_price:.2f} Baht/kWh"
                )
        else:
            # Seller: set dispatch target
            if hasattr(meter, "vpp_dispatch_kw"):
                meter.vpp_dispatch_kw = cleared_quantity
