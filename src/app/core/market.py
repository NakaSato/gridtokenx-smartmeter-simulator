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
        self, 
        total_generation: float, 
        total_consumption: float,
        zone_loads: dict = None
    ) -> Tuple[float, float]:
        """
        Update market prices based on supply and demand.
        Accepts optional zone_loads to calculate congestion premiums.
        Returns (sell_price, buy_price).
        """
        if total_generation <= 0:
            load_ratio = 2.0  # High demand
        else:
            load_ratio = total_consumption / total_generation

        # 1. Market Elasticity Logic (Global)
        elasticity = 0.5
        multiplier = 1.0 + (load_ratio - 1.0) * elasticity
        
        # 2. Congestion Pricing Logic (New)
        # If any zone is overloaded (>90% of aggregate capacity), add a reliability premium
        congestion_premium = 0.0
        if zone_loads:
            overloaded_zones = [z for z, l in zone_loads.items() if l > 0.9] # >90% utilization
            if overloaded_zones:
                congestion_premium = 0.1 * len(overloaded_zones) # 10% premium per overloaded zone
        
        final_multiplier = multiplier + congestion_premium
        
        # Clamp multiplier to realistic bounds (0.5x to 4.0x)
        final_multiplier = max(0.5, min(4.0, final_multiplier))

        # Update prices
        self.current_sell_price = self.base_sell_price * final_multiplier
        self.current_buy_price = self.base_buy_price * final_multiplier

        # Ensure Buy Price is always slightly higher than Sell Price (Grid Spread)
        if self.current_buy_price <= self.current_sell_price:
            self.current_buy_price = self.current_sell_price * 1.05

        return self.current_sell_price, self.current_buy_price

    def get_prices(self) -> Tuple[float, float]:
        return self.current_sell_price, self.current_buy_price
