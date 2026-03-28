"""
Real-time P2P Price Streaming

Broadcasts P2P market prices to connected WebSocket clients.
Prices are based on Time-of-Use (ToU) tariffs.

Future: Will support API Gateway for dynamic prices.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..config.thai_market import (
    GRID_BUYBACK_RATE,
    GRID_PURCHASE_RATE_HIGH_TIER,
    RESIDENTIAL_WHEELING_COST_AVG,
)
from ..transport.websocket import WebSocketManager
from .price_history import PriceHistoryManager
from .price_provider import ToUPriceProvider, PriceProvider

logger = logging.getLogger(__name__)


class PriceStreamer:
    """
    Streams real-time P2P market prices via WebSocket.

    Prices are based on ToU tariffs (current implementation):
    - ON_PEAK (Mon-Fri 09:00-22:00): 5.7982 Baht/kWh
    - OFF_PEAK_WEEKDAY (Mon-Fri 22:00-09:00): 2.6369 Baht/kWh
    - OFF_PEAK_WEEKEND (Sat-Sun all day): 2.6369 Baht/kWh

    P2P Price = ToU Rate × (1 - discount)
    
    Future: Will support API Gateway for dynamic prices.
    """

    def __init__(
        self,
        websocket_manager: WebSocketManager,
        broadcast_interval: float = 5.0,
        wheeling_cost: float = RESIDENTIAL_WHEELING_COST_AVG,
        history_manager: Optional[PriceHistoryManager] = None,
        price_provider: Optional[PriceProvider] = None,
        p2p_discount: float = 0.10,  # 10% discount vs ToU rate
    ):
        """
        Initialize price streamer.
        
        Args:
            websocket_manager: WebSocket manager for broadcasting
            broadcast_interval: Update interval in seconds
            wheeling_cost: Wheeling cost in Baht/kWh
            history_manager: Optional price history manager
            price_provider: Price provider (uses ToU if not provided)
            p2p_discount: P2P discount rate (used if price_provider not provided)
        """
        self.websocket_manager = websocket_manager
        self.broadcast_interval = broadcast_interval
        self.wheeling_cost = wheeling_cost
        self.history_manager = history_manager
        
        # Use provided price provider or create default ToU provider
        self.price_provider = price_provider or ToUPriceProvider(p2p_discount=p2p_discount)
        self.p2p_discount = p2p_discount  # Keep for backward compatibility

        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Market state (for display, not used in pricing)
        self.current_supply = 100.0  # kWh
        self.current_demand = 100.0  # kWh
        self.last_price: Optional[float] = None

    async def start(self):
        """Start the price streaming background task."""
        if self._running:
            logger.warning("PriceStreamer already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._stream_loop())
        logger.info(f"PriceStreamer started (interval={self.broadcast_interval}s, source=ToU)")

    async def stop(self):
        """Stop the price streaming background task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("PriceStreamer stopped")

    async def _stream_loop(self):
        """Main streaming loop."""
        while self._running:
            try:
                # Calculate current market price (ToU-based)
                price_data = self._calculate_price()

                # Record to history (async if database enabled)
                if self.history_manager:
                    if self.history_manager._db:
                        await self.history_manager.add_price_async(
                            supply_kwh=self.current_supply,
                            demand_kwh=self.current_demand,
                        )
                    else:
                        self.history_manager.add_price(
                            supply_kwh=self.current_supply,
                            demand_kwh=self.current_demand,
                        )

                # Broadcast to all connected clients
                await self.websocket_manager.broadcast(price_data)

                # Simulate supply/demand changes (for demo)
                self._simulate_market_dynamics()

                await asyncio.sleep(self.broadcast_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in price stream loop: {e}")
                await asyncio.sleep(self.broadcast_interval)

    def _calculate_price(self) -> Dict[str, Any]:
        """Calculate current market price using price provider."""
        now = datetime.now(timezone.utc)

        # Get price from provider (ToU or API Gateway in future)
        mcp = self.price_provider.get_price_sync()
        self.last_price = mcp

        # Get TOU period for display
        tou_period = self.price_provider.get_tou_period(now)
        tou_rate = self.price_provider.get_tou_rate(now) if hasattr(self.price_provider, 'get_tou_rate') else 0.0

        # Calculate buyer/seller rates
        buyer_rate = mcp + (self.wheeling_cost * 0.5)
        seller_net = mcp - (self.wheeling_cost * 0.5)

        # Market sentiment (based on simulated supply/demand)
        ratio = self.current_demand / self.current_supply if self.current_supply > 0 else 999
        if ratio > 1.5:
            sentiment = "HIGH_DEMAND"
        elif ratio < 0.7:
            sentiment = "LOW_DEMAND"
        else:
            sentiment = "BALANCED"

        return {
            "type": "price_update",
            "timestamp": now.isoformat(),
            "data": {
                "market_clearing_price_baht_kwh": round(mcp, 4),
                "buyer_total_baht_kwh": round(buyer_rate, 4),
                "seller_net_baht_kwh": round(seller_net, 4),
                "wheeling_cost_baht_kwh": self.wheeling_cost,
                "spread_vs_utility_baht_kwh": round(mcp - GRID_BUYBACK_RATE, 4),
                "premium_vs_feedin_baht_kwh": round(mcp - GRID_BUYBACK_RATE, 4),
                "market_sentiment": sentiment,
                "tou_period": tou_period.value,
                "tou_rate_baht_kwh": round(tou_rate, 4),
                "p2p_discount_percent": round(self.p2p_discount * 100, 2),
                "supply_kwh": round(self.current_supply, 2),
                "demand_kwh": round(self.current_demand, 2),
                "demand_ratio": round(ratio, 3),
            },
            "pricing": {
                "source": "ToU Tariff",
                "tou_period": tou_period.value,
                "tou_rate_baht_kwh": round(tou_rate, 4),
                "p2p_discount_percent": round(self.p2p_discount * 100, 2),
                "formula": "P2P_Price = ToU_Rate × (1 - discount)",
                "note": "API Gateway integration planned for dynamic pricing",
            },
            "comparison": {
                "utility_retail_rate_baht_kwh": tou_rate,
                "utility_buyback_rate_baht_kwh": GRID_BUYBACK_RATE,
                "p2p_savings_percent": round(
                    (tou_rate - buyer_rate) / tou_rate * 100, 2
                ),
                "seller_premium_percent": round(
                    (mcp - GRID_BUYBACK_RATE) / GRID_BUYBACK_RATE * 100, 2
                ),
            },
        }

    def _simulate_market_dynamics(self):
        """Simulate realistic supply/demand fluctuations."""
        import random
        import math
        
        now = datetime.now(timezone.utc)
        hour = now.hour + now.minute / 60.0
        
        # Solar generation pattern (bell curve around noon)
        solar_factor = math.exp(-((hour - 13) ** 2) / 50)  # Peak at 13:00
        self.current_supply = 80 + 60 * solar_factor + random.uniform(-5, 5)
        
        # Demand pattern (double peak: morning and evening)
        morning_peak = math.exp(-((hour - 8) ** 2) / 20)
        evening_peak = math.exp(-((hour - 19) ** 2) / 20)
        self.current_demand = 70 + 50 * (morning_peak + evening_peak) + random.uniform(-5, 5)
        
        # Ensure positive values
        self.current_supply = max(10, self.current_supply)
        self.current_demand = max(10, self.current_demand)

    def update_market_state(self, supply_kwh: float, demand_kwh: float):
        """
        Update market state from external source.
        
        Args:
            supply_kwh: Current market supply
            demand_kwh: Current market demand
        """
        self.current_supply = max(10, supply_kwh)
        self.current_demand = max(10, demand_kwh)
        logger.debug(f"Market state updated: supply={supply_kwh}, demand={demand_kwh}")
