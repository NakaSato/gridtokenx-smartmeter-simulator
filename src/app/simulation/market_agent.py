"""
Market Agent Module for P2P Energy Trading Simulation.

This module implements game-theoretic agent behavior where Prosumers
actively adjust their bid/ask prices based on the physics-based grid state.

Key Principles:
1. Grid-Supportive Pricing: Agents sell cheaper when voltage is high (to encourage
   consumption and reduce voltage rise) and buy cheaper when voltage is low.
2. Surplus/Deficit Awareness: Agents with surplus energy are more aggressive sellers.
3. Time-of-Use Sensitivity: Agents adjust prices based on TOU tariff periods.
"""

import random
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TradingStrategy(Enum):
    """Trading strategy enum matching meter configuration."""
    CONSERVATIVE = "Conservative"   # Price close to market, low risk
    MODERATE = "Moderate"          # Balanced approach
    AGGRESSIVE = "Aggressive"      # Wide spreads, high reward/risk


@dataclass
class GridState:
    """Represents the current state of the grid for decision making."""
    voltage_pu: float = 1.0       # Per-unit voltage at connection point
    frequency_hz: float = 50.0    # Grid frequency
    thd_voltage: float = 0.0      # THD-V at connection point
    is_on_peak: bool = False      # TOU on-peak flag
    congestion_factor: float = 0.0  # 0-1, higher = more congested transformer/line


class MarketAgent:
    """
    Game-theoretic agent for P2P energy trading.
    
    Each SmartMeter can have an associated MarketAgent that adjusts
    bid/ask prices based on grid conditions and personal strategy.
    """
    
    def __init__(
        self,
        meter_id: str,
        strategy: TradingStrategy = TradingStrategy.MODERATE,
        base_sell_price: float = 2.50,  # THB/kWh
        base_buy_price: float = 4.40    # THB/kWh
    ):
        self.meter_id = meter_id
        self.strategy = strategy
        self.base_sell_price = base_sell_price
        self.base_buy_price = base_buy_price
        
        # Strategy-specific parameters
        self._configure_strategy()
        
    def _configure_strategy(self):
        """Sets trading parameters based on strategy."""
        if self.strategy == TradingStrategy.CONSERVATIVE:
            self.price_sensitivity = 0.05  # 5% max adjustment
            self.voltage_response = 0.5    # Low response to voltage
            self.spread_multiplier = 1.0   # Tight spread
        elif self.strategy == TradingStrategy.AGGRESSIVE:
            self.price_sensitivity = 0.20  # 20% max adjustment
            self.voltage_response = 2.0    # High response to voltage
            self.spread_multiplier = 1.5   # Wide spread
        else:  # MODERATE
            self.price_sensitivity = 0.10  # 10% max adjustment
            self.voltage_response = 1.0    # Normal response
            self.spread_multiplier = 1.2   # Moderate spread
    
    def calculate_prices(
        self,
        grid_state: GridState,
        surplus_kwh: float = 0.0,
        deficit_kwh: float = 0.0
    ) -> Tuple[float, float]:
        """
        Calculates dynamic bid/ask prices based on grid state.
        
        Returns:
            Tuple of (max_sell_price, max_buy_price)
        """
        sell_price = self.base_sell_price
        buy_price = self.base_buy_price
        
        # 1. Voltage-Based Adjustment (Grid Support)
        # High voltage (>1.02 pu) -> Lower sell price (encourage consumption)
        # Low voltage (<0.98 pu) -> Higher sell price (discourage injection)
        voltage_deviation = grid_state.voltage_pu - 1.0
        voltage_adjustment = voltage_deviation * self.voltage_response * self.price_sensitivity
        
        sell_price -= voltage_adjustment  # Lower price when voltage is high
        buy_price += voltage_adjustment   # Higher buy price when voltage is low
        
        # 2. TOU Adjustment
        if grid_state.is_on_peak:
            # On-peak: Increase sell price (energy is more valuable)
            sell_price *= 1.15
            buy_price *= 1.10
        
        # 3. Surplus/Deficit Urgency
        if surplus_kwh > 1.0:
            # Large surplus -> more willing to sell at lower price
            urgency_discount = min(0.1, surplus_kwh * 0.02)  # Up to 10% discount
            sell_price *= (1 - urgency_discount)
        
        if deficit_kwh > 1.0:
            # Large deficit -> more willing to pay higher price
            urgency_premium = min(0.1, deficit_kwh * 0.02)  # Up to 10% premium
            buy_price *= (1 + urgency_premium)
        
        # 4. Power Quality Adjustment
        # High THD -> discount prices (lower quality power)
        if grid_state.thd_voltage > 5.0:
            thd_discount = min(0.05, (grid_state.thd_voltage - 5.0) * 0.01)
            sell_price *= (1 - thd_discount)
        
        # 5. Randomization (Market Noise)
        noise = random.gauss(0, 0.02 * self.price_sensitivity)
        sell_price *= (1 + noise)
        buy_price *= (1 + noise)
        
        # Ensure valid price bounds (avoid negative or zero prices)
        sell_price = max(0.01, sell_price)
        buy_price = max(0.01, buy_price)
        
        # Ensure sell < buy (arbitrage-free)
        if sell_price >= buy_price:
            spread = 0.05  # Minimum spread
            sell_price = buy_price - spread
            if sell_price < 0.01:
                sell_price = 0.01
                buy_price = 0.06
        
        return round(sell_price, 4), round(buy_price, 4)
    
    def should_trade(self, surplus_kwh: float, deficit_kwh: float, grid_state: GridState) -> str:
        """
        Determines if the agent should actively trade.
        
        Returns:
            "SELL", "BUY", or "HOLD"
        """
        if surplus_kwh > 0.5 and grid_state.voltage_pu < 1.05:
            return "SELL"
        elif deficit_kwh > 0.5 and grid_state.voltage_pu > 0.95:
            return "BUY"
        else:
            return "HOLD"
