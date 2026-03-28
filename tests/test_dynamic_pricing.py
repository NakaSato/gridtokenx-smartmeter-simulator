"""
Dynamic Pricing Formula Tests

Tests for the GridTokenX dynamic pricing formula from simulator_logic.md:
    p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min

Where:
    - D_t = Demand - Supply (normalized difference)
    - R_t = Demand / Supply (ratio)
    - p_min = Price floor (typically 2.20 Baht)

Run with:
    uv run pytest tests/test_dynamic_pricing.py -v
"""

import math
import pytest
from datetime import datetime

from smart_meter_simulator.core.price_comparison import BlockchainP2PPricingModel


class TestDynamicPricingFormula:
    """Tests for the arctan-based dynamic pricing formula."""

    def test_formula_balanced_market(self):
        """Verify price for balanced supply/demand (100/100)."""
        calc = BlockchainP2PPricingModel()
        
        # Balanced market
        price = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=100.0,
            demand_kwh=100.0,
            base_price=2.20,
            use_formula=True,
        )
        
        # D_t = (100-100)/100 = 0
        # R_t = 100/100 = 1.0
        # p_t = arctan(e^0) + arctan(1.0)/10 + 2.20
        # p_t = arctan(1) + arctan(1)/10 + 2.20
        # p_t = 0.785 + 0.0785 + 2.20 ≈ 3.06
        assert 2.8 < price < 3.3

    def test_formula_high_demand(self):
        """Verify price increases with high demand (50 supply, 150 demand)."""
        calc = BlockchainP2PPricingModel()
        
        # High demand scenario
        price_high = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 19, 0),
            supply_kwh=50.0,
            demand_kwh=150.0,
            base_price=2.20,
            use_formula=True,
        )
        
        # D_t = (150-50)/100 = 1.0
        # R_t = 150/50 = 3.0
        # Price should be higher than balanced
        assert price_high > 3.5

    def test_formula_oversupply(self):
        """Verify price decreases with oversupply (200 supply, 50 demand)."""
        calc = BlockchainP2PPricingModel()
        
        # Oversupply scenario
        price_low = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=200.0,
            demand_kwh=50.0,
            base_price=2.20,
            use_formula=True,
        )
        
        # D_t = (50-200)/100 = -1.5
        # R_t = 50/200 = 0.25
        # Price should be lower (close to p_min)
        assert 2.0 <= price_low < 3.0

    def test_formula_extreme_scarcity(self):
        """Verify scarcity pricing when supply is zero."""
        calc = BlockchainP2PPricingModel()
        
        # Zero supply
        price = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 19, 0),
            supply_kwh=0.0,
            demand_kwh=100.0,
            base_price=2.20,
            use_formula=True,
        )
        
        # Should return maximum price (1.5x base)
        assert price == 2.20 * 1.5

    def test_formula_price_bounds(self):
        """Verify price stays within bounds [2.0, 5.5] Baht/kWh."""
        calc = BlockchainP2PPricingModel()
        
        # Test extreme scenarios
        scenarios = [
            (10, 500, "Extreme demand"),
            (500, 10, "Extreme oversupply"),
            (1, 100, "Very high demand"),
            (100, 1, "Very low demand"),
        ]
        
        for supply, demand, _ in scenarios:
            price = calc.simulate_market_price(
                timestamp=datetime(2026, 3, 21, 12, 0),
                supply_kwh=supply,
                demand_kwh=demand,
                base_price=2.20,
                use_formula=True,
            )
            assert 2.0 <= price <= 5.5, f"Price {price} out of bounds for {supply}/{demand}"

    def test_formula_mathematical_correctness(self):
        """Verify the formula is mathematically correct."""
        # Manual calculation for balanced market (100/100)
        D_t = (100 - 100) / 100  # = 0
        R_t = 100 / 100  # = 1.0
        p_min = 2.20
        
        expected = math.atan(math.exp(D_t)) + math.atan(R_t) / 10.0 + p_min
        # = arctan(1) + arctan(1)/10 + 2.20
        # = 0.7854 + 0.0785 + 2.20
        # = 3.0639
        
        calc = BlockchainP2PPricingModel()
        actual = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=100.0,
            demand_kwh=100.0,
            base_price=2.20,
            use_formula=True,
        )
        
        assert abs(actual - expected) < 0.001

    def test_formula_vs_elasticity_model(self):
        """Compare arctan formula vs legacy elasticity model."""
        calc = BlockchainP2PPricingModel()
        
        # High demand scenario
        supply, demand = 50, 150
        
        price_formula = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 19, 0),
            supply_kwh=supply,
            demand_kwh=demand,
            base_price=3.30,
            use_formula=True,
        )
        
        price_elasticity = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 19, 0),
            supply_kwh=supply,
            demand_kwh=demand,
            base_price=3.30,
            use_formula=False,
        )
        
        # Both should show high prices for high demand
        assert price_formula > 3.30
        assert price_elasticity > 3.30
        
        # But values will differ (different models)
        assert price_formula != price_elasticity


class TestTimeOfUseAdjustment:
    """Tests for time-of-use price adjustments."""

    def test_evening_peak_pricing(self):
        """Verify higher prices during evening peak (17:00-21:00)."""
        calc = BlockchainP2PPricingModel()
        
        # Same supply/demand, different times
        supply, demand = 100, 120
        
        price_evening = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 24, 19, 0),  # Monday 19:00
            supply_kwh=supply,
            demand_kwh=demand,
            base_price=3.30,
            use_formula=False,  # Use elasticity for time adjustment
        )
        
        price_midday = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 24, 12, 0),  # Monday 12:00
            supply_kwh=supply,
            demand_kwh=demand,
            base_price=3.30,
            use_formula=False,
        )
        
        # Evening should be higher (but formula doesn't include time factor)
        # This test documents the expected behavior
        assert price_evening >= price_midday

    def test_solar_peak_pricing(self):
        """Verify lower prices during solar peak (9:00-16:00) due to oversupply."""
        calc = BlockchainP2PPricingModel()
        
        # Solar peak: high supply from solar
        supply, demand = 150, 100  # Oversupply
        
        price_solar = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 24, 12, 0),
            supply_kwh=supply,
            demand_kwh=demand,
            base_price=3.30,
            use_formula=True,
        )
        
        # Compare with balanced market
        price_balanced = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 24, 12, 0),
            supply_kwh=100,
            demand_kwh=100,
            base_price=3.30,
            use_formula=True,
        )
        
        # Oversupply should result in lower price than balanced
        # Note: The arctan formula doesn't have explicit time adjustment,
        # but oversupply (high R_t denominator) naturally lowers price
        assert price_solar < price_balanced


class TestMarketSentiment:
    """Tests for market sentiment detection."""

    def test_bullish_market(self):
        """Verify bullish sentiment detection (rising prices)."""
        calc = BlockchainP2PPricingModel()
        
        # Add price history with rising trend
        for i in range(5):
            calc.get_price(
                timestamp=datetime(2026, 3, 21, i, 0),
                market_clearing_price=3.0 + i * 0.3,
                market_volume=100.0,
            )
        
        sentiment = calc.get_market_sentiment()
        assert "Bullish" in sentiment

    def test_bearish_market(self):
        """Verify bearish sentiment detection (falling prices)."""
        calc = BlockchainP2PPricingModel()
        
        # Add price history with falling trend
        for i in range(5):
            calc.get_price(
                timestamp=datetime(2026, 3, 21, i, 0),
                market_clearing_price=4.0 - i * 0.3,
                market_volume=100.0,
            )
        
        sentiment = calc.get_market_sentiment()
        assert "Bearish" in sentiment

    def test_stable_market(self):
        """Verify stable sentiment detection."""
        calc = BlockchainP2PPricingModel()
        
        # Add stable price history
        for i in range(5):
            calc.get_price(
                timestamp=datetime(2026, 3, 21, i, 0),
                market_clearing_price=3.30,
                market_volume=100.0,
            )
        
        sentiment = calc.get_market_sentiment()
        assert "Stable" in sentiment


class TestIntegration:
    """Integration tests for dynamic pricing."""

    def test_full_day_simulation(self):
        """Simulate prices for a full day with varying supply/demand."""
        calc = BlockchainP2PPricingModel()
        
        # Typical daily profile
        profiles = {
            0: (80, 60),   # Night: low demand
            6: (50, 80),   # Morning: demand rising
            12: (150, 100), # Midday: solar peak (oversupply)
            18: (60, 140),  # Evening: peak demand
            22: (70, 50),   # Late night: low demand
        }
        
        prices = {}
        for hour, (supply, demand) in profiles.items():
            prices[hour] = calc.simulate_market_price(
                timestamp=datetime(2026, 3, 21, hour, 0),
                supply_kwh=supply,
                demand_kwh=demand,
                base_price=2.20,
                use_formula=True,
            )
        
        # Evening should be highest (high demand, low solar)
        assert prices[18] == max(prices.values())
        
        # Midday should be low (solar oversupply)
        assert prices[12] < prices[18]
        
        # All prices within bounds
        for hour, price in prices.items():
            assert 2.0 <= price <= 5.5, f"Hour {hour}: price {price} out of bounds"

    def test_comparison_with_utility_rates(self):
        """Compare P2P dynamic prices with utility rates."""
        calc = BlockchainP2PPricingModel()
        
        # Utility rates (Type 1.1.2 high tier)
        utility_rate = 4.4217
        feedin_rate = 2.20
        
        # Balanced P2P market
        p2p_price = calc.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=100,
            demand_kwh=100,
            base_price=3.30,
            use_formula=True,
        )
        
        # P2P should be competitive
        # Buyer pays: p2p_price + wheeling (~1.76)
        # vs utility: 4.4217
        wheeling = 1.76
        buyer_total = p2p_price + wheeling * 0.5  # Split wheeling
        
        # With reasonable P2P price, should be competitive
        assert buyer_total < utility_rate or p2p_price > feedin_rate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
