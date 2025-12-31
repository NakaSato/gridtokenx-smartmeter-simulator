from typing import Tuple
from ..config import SimulatorConfig


class MarketSystem:
    """
    Simulates a dynamic energy market.
    Prices fluctuate based on the Grid Load Ratio (Demand / Supply).
    """

    def __init__(self):
        self.base_sell_price = SimulatorConfig.MAX_SELL_PRICE
        self.base_buy_price = SimulatorConfig.MAX_BUY_PRICE
        self.current_sell_price = self.base_sell_price
        self.current_buy_price = self.base_buy_price

    def update(
        self, total_generation: float, total_consumption: float
    ) -> Tuple[float, float]:
        """
        Update market prices based on supply and demand.
        Returns (sell_price, buy_price).
        """
        if total_generation <= 0:
            load_ratio = 2.0  # High demand (infinite ratio technically, but capped)
        else:
            load_ratio = total_consumption / total_generation

        # Price Elasticity Logic
        # Ratio > 1.0: Deficit (High Demand) -> Prices UP
        # Ratio < 1.0: Surplus (High Supply) -> Prices DOWN

        # Dampening factor to prevent extreme volatility
        elasticity = 0.5

        # Calculate price multiplier
        # If ratio is 1.0 (Balanced), multiplier is 1.0
        # If ratio is 2.0 (High Demand), multiplier is 1.5
        # If ratio is 0.5 (High Supply), multiplier is 0.75
        multiplier = 1.0 + (load_ratio - 1.0) * elasticity

        # Clamp multiplier to realistic bounds (0.5x to 3.0x)
        multiplier = max(0.5, min(3.0, multiplier))

        # Update prices
        self.current_sell_price = self.base_sell_price * multiplier
        self.current_buy_price = self.base_buy_price * multiplier

        # Ensure Buy Price is always slightly higher than Sell Price (Grid Spread)
        # This prevents infinite arbitrage loops
        if self.current_buy_price <= self.current_sell_price:
            self.current_buy_price = self.current_sell_price * 1.05

        return self.current_sell_price, self.current_buy_price

    def get_prices(self) -> Tuple[float, float]:
        return self.current_sell_price, self.current_buy_price
