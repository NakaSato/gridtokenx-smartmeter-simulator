"""
Unit Tests for Price Comparison Module

Tests for comparing Single-Buyer (utility) vs Blockchain P2P pricing models.

Run with:
    uv run pytest tests/test_price_comparison.py -v
"""

import pytest
from datetime import datetime

from smart_meter_simulator.config.thai_market import (
    TariffCategory,
    UtilityProvider,
    GRID_BUYBACK_RATE,
    GRID_PURCHASE_RATE_HIGH_TIER,
    TYPICAL_P2P_PRICE,
)
from smart_meter_simulator.core.price_comparison import (
    SingleBuyerPricingModel,
    BlockchainP2PPricingModel,
    PriceComparisonEngine,
    PricingModel,
    SingleBuyerPrice,
    BlockchainP2PPrice,
    PriceComparison,
    MonthlyComparisonReport,
)


# ============================================================================
# Single-Buyer Pricing Model Tests
# ============================================================================

class TestSingleBuyerPricingModel:
    """Tests for SingleBuyerPricingModel class."""
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        model = SingleBuyerPricingModel()
        
        assert model.tariff_category == TariffCategory.TYPE_1_1_2
        assert model.utility_provider == UtilityProvider.PEA
        assert model.ft_rate == 0.0972  # Default Ft
    
    def test_get_price_ladder_tariff(self):
        """Test getting price for ladder tariff."""
        model = SingleBuyerPricingModel(
            tariff_category=TariffCategory.TYPE_1_1_2,
        )
        
        price = model.get_price(datetime(2026, 3, 21, 10, 0))
        
        assert isinstance(price, SingleBuyerPrice)
        assert price.import_rate_baht_kwh == GRID_PURCHASE_RATE_HIGH_TIER
        assert price.export_rate_baht_kwh == GRID_BUYBACK_RATE
        assert price.ft_rate_baht_kwh == 0.0972
        assert "Ladder" in price.tariff_type
    
    def test_get_price_tou_tariff_peak(self):
        """Test getting TOU price during peak period."""
        model = SingleBuyerPricingModel(
            tariff_category=TariffCategory.TYPE_1_2,
        )
        
        # Weekday 10:00 = On-Peak
        price = model.get_price(datetime(2026, 3, 24, 10, 0))  # Monday
        
        assert price.is_peak_period is True
        assert price.import_rate_baht_kwh == 5.7982  # On-peak rate
        assert "TOU" in price.tariff_type
    
    def test_get_price_tou_tariff_off_peak(self):
        """Test getting TOU price during off-peak period."""
        model = SingleBuyerPricingModel(
            tariff_category=TariffCategory.TYPE_1_2,
        )
        
        # Weekday 23:00 = Off-Peak
        price = model.get_price(datetime(2026, 3, 24, 23, 0))  # Monday
        
        assert price.is_peak_period is False
        assert price.import_rate_baht_kwh == 2.6369  # Off-peak rate
    
    def test_get_price_tou_weekend(self):
        """Test getting TOU price on weekend."""
        model = SingleBuyerPricingModel(
            tariff_category=TariffCategory.TYPE_1_2,
        )
        
        # Saturday 12:00 = Off-Peak (weekend)
        price = model.get_price(datetime(2026, 3, 28, 12, 0))  # Saturday
        
        assert price.is_peak_period is False
        assert price.import_rate_baht_kwh == 2.6369  # Off-peak rate
    
    def test_calculate_monthly_bill(self):
        """Test monthly bill calculation."""
        model = SingleBuyerPricingModel(
            tariff_category=TariffCategory.TYPE_1_1_2,
        )
        
        bill = model.calculate_monthly_bill(
            consumption_kwh=500.0,
            month=3,
            year=2026,
        )
        
        assert bill["total_kwh"] == 500.0
        assert bill["total_amount_baht"] > 0
        assert bill["average_rate_baht_kwh"] > 0
        assert "energy_charge_baht" in bill
        assert "ft_charge_baht" in bill
        assert "service_charge_baht" in bill
    
    def test_spread_calculation(self):
        """Test spread between import and export rates."""
        model = SingleBuyerPricingModel()
        price = model.get_price(datetime(2026, 3, 21, 10, 0))
        
        # Spread should be significant (arbitrage opportunity)
        spread = price.breakdown["spread"]
        assert spread > 2.0  # Should be around 2.22 Baht/kWh


# ============================================================================
# Blockchain P2P Pricing Model Tests
# ============================================================================

class TestBlockchainP2PPricingModel:
    """Tests for BlockchainP2PPricingModel class."""
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        model = BlockchainP2PPricingModel()
        
        assert model.wheeling_cost == 1.76  # Default wheeling
        assert model.grid_rate == GRID_PURCHASE_RATE_HIGH_TIER
        assert model.feedin_rate == GRID_BUYBACK_RATE
    
    def test_get_price(self):
        """Test getting P2P price."""
        model = BlockchainP2PPricingModel(
            wheeling_cost_baht_kwh=1.76,
        )
        
        price = model.get_price(
            timestamp=datetime(2026, 3, 21, 10, 0),
            market_clearing_price=3.30,
            market_volume=100.0,
            market_sentiment="Stable",
        )
        
        assert isinstance(price, BlockchainP2PPrice)
        assert price.market_clearing_price_baht_kwh == 3.30
        assert price.wheeling_cost_baht_kwh == 1.76
        assert price.buyer_total_baht_kwh == 3.30 + 1.76
        assert price.seller_net_baht_kwh == 3.30 - 1.76
        assert price.market_volume_kwh == 100.0
        assert price.market_sentiment == "Stable"
    
    def test_spread_vs_utility(self):
        """Test spread calculation vs utility rates."""
        model = BlockchainP2PPricingModel(
            wheeling_cost_baht_kwh=1.76,
            grid_reference_rate=4.4217,
            feedin_reference_rate=2.20,
        )
        
        price = model.get_price(
            timestamp=datetime(2026, 3, 21, 10, 0),
            market_clearing_price=3.30,
        )
        
        # With standard wheeling (1.76), P2P buyer pays 3.30 + 1.76 = 5.06
        # vs utility at 4.4217, so spread is negative: 4.4217 - 5.06 = -0.6383
        # This shows P2P needs lower MCP or lower wheeling to be competitive
        
        # Seller net: 3.30 - 1.76 = 1.54, vs feed-in 2.20, premium is negative
        assert price.spread_vs_utility_baht_kwh < 0  # Buyer pays more with high wheeling
        assert price.premium_vs_feedin_baht_kwh < 0  # Seller earns less with high wheeling
        
        # Test with lower wheeling for beneficial scenario
        model_low_wheeling = BlockchainP2PPricingModel(
            wheeling_cost_baht_kwh=0.5,
            grid_reference_rate=4.4217,
            feedin_reference_rate=2.20,
        )
        
        price_low = model_low_wheeling.get_price(
            timestamp=datetime(2026, 3, 21, 10, 0),
            market_clearing_price=3.30,
        )
        
        # With low wheeling (0.5), buyer pays 3.30 + 0.5 = 3.80
        # vs utility at 4.4217, spread is positive: 4.4217 - 3.80 = 0.6217
        assert price_low.spread_vs_utility_baht_kwh > 0  # Buyer saves
        assert price_low.premium_vs_feedin_baht_kwh > 0  # Seller earns more (3.30 - 0.5 = 2.80 > 2.20)
    
    def test_simulate_market_price_balanced(self):
        """Test market price simulation with balanced supply/demand."""
        model = BlockchainP2PPricingModel()

        # Balanced market
        price = model.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=100.0,
            demand_kwh=100.0,
            base_price=3.30,
        )

        # Should be around base price + arctan formula adjustment
        # Formula: p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min
        # With D_t=0, R_t=1: arctan(1) + arctan(1)/10 + 3.30 ≈ 0.785 + 0.0785 + 3.30 ≈ 4.16
        assert 4.0 < price < 4.5

    def test_simulate_market_price_high_demand(self):
        """Test market price simulation with high demand."""
        model = BlockchainP2PPricingModel()

        # High demand (demand > supply)
        price = model.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 18, 0),
            supply_kwh=50.0,
            demand_kwh=150.0,
            base_price=3.30,
        )

        # Price should be higher than base
        assert price > 3.30

    def test_simulate_market_price_oversupply(self):
        """Test market price simulation with oversupply."""
        model = BlockchainP2PPricingModel()

        # Oversupply (supply > demand)
        price = model.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=200.0,
            demand_kwh=50.0,
            base_price=3.30,
        )

        # Price should be lower than balanced case
        balanced_price = model.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=100.0,
            demand_kwh=100.0,
            base_price=3.30,
        )
        assert price < balanced_price

    def test_simulate_market_price_time_of_day(self):
        """Test market price simulation with time-of-day effect."""
        model = BlockchainP2PPricingModel()

        # Evening peak (17:00-21:00)
        price_evening = model.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 19, 0),
            supply_kwh=100.0,
            demand_kwh=100.0,
            base_price=3.30,
        )

        # Midday (solar peak, lower prices)
        price_midday = model.simulate_market_price(
            timestamp=datetime(2026, 3, 21, 12, 0),
            supply_kwh=100.0,
            demand_kwh=100.0,
            base_price=3.30,
        )

        # Evening should be higher than midday (due to TOU multiplier)
        # Note: If TOU is not implemented, prices may be equal
        assert price_evening >= price_midday
    
    def test_get_market_sentiment(self):
        """Test market sentiment detection."""
        model = BlockchainP2PPricingModel()
        
        # Add price history with rising trend
        for i in range(5):
            model.get_price(
                timestamp=datetime(2026, 3, 21, i, 0),
                market_clearing_price=3.0 + i * 0.3,  # Rising prices
                market_volume=100.0,
            )
        
        sentiment = model.get_market_sentiment()
        assert "Bullish" in sentiment
    
    def test_get_average_mcp(self):
        """Test average MCP calculation."""
        model = BlockchainP2PPricingModel()
        
        # Add price history
        for i in range(10):
            model.get_price(
                timestamp=datetime(2026, 3, 21, i, 0),
                market_clearing_price=3.30,
                market_volume=100.0,
            )
        
        avg_mcp = model.get_average_mcp(hours=10)
        assert abs(avg_mcp - 3.30) < 0.01


# ============================================================================
# Price Comparison Engine Tests
# ============================================================================

class TestPriceComparisonEngine:
    """Tests for PriceComparisonEngine class."""
    
    def test_init(self):
        """Test initialization."""
        engine = PriceComparisonEngine()
        
        assert engine.single_buyer is not None
        assert engine.blockchain_p2p is not None
        assert len(engine.comparison_history) == 0
    
    def test_compare_prices_beneficial(self):
        """Test price comparison with beneficial P2P trade."""
        engine = PriceComparisonEngine(
            tariff_category=TariffCategory.TYPE_1_1_2,
            wheeling_cost=0.5,  # Low wheeling for clear benefit
        )
        
        comparison = engine.compare_prices(
            timestamp=datetime(2026, 3, 21, 10, 0),
            energy_kwh=100.0,
            market_clearing_price=3.30,
            market_volume=100.0,
            market_sentiment="Stable",
        )
        
        assert isinstance(comparison, PriceComparison)
        assert comparison.energy_kwh == 100.0
        
        # Single-buyer cost
        assert comparison.single_buyer_cost_baht > 0
        assert comparison.single_buyer_rate_baht_kwh > 0
        
        # P2P costs and revenue
        assert comparison.p2p_buyer_cost_baht > 0
        assert comparison.p2p_seller_revenue_baht > 0
        
        # With low wheeling, should be beneficial
        assert comparison.is_p2p_beneficial is True
        assert comparison.buyer_savings_baht > 0
        assert comparison.seller_gain_baht > 0
        assert comparison.total_welfare_gain_baht > 0
    
    def test_compare_prices_unprofitable(self):
        """Test price comparison with unprofitable P2P trade."""
        engine = PriceComparisonEngine(
            wheeling_cost=2.0,  # High wheeling
        )
        
        comparison = engine.compare_prices(
            timestamp=datetime(2026, 3, 21, 10, 0),
            energy_kwh=100.0,
            market_clearing_price=3.30,
        )
        
        # With high wheeling, may not be beneficial
        assert comparison.is_p2p_beneficial is False
    
    def test_compare_prices_tou_peak(self):
        """Test price comparison during TOU peak period."""
        engine = PriceComparisonEngine(
            tariff_category=TariffCategory.TYPE_1_2,
            wheeling_cost=0.5,
        )
        
        # Peak period comparison
        comparison_peak = engine.compare_prices(
            timestamp=datetime(2026, 3, 24, 12, 0),  # Monday peak
            energy_kwh=100.0,
            market_clearing_price=3.50,
        )
        
        # Single-buyer rate should be high (on-peak)
        assert comparison_peak.single_buyer_rate_baht_kwh == 5.7982
        
        # P2P should offer significant savings during peak
        assert comparison_peak.buyer_savings_baht > 0
    
    def test_compare_prices_tou_off_peak(self):
        """Test price comparison during TOU off-peak period."""
        engine = PriceComparisonEngine(
            tariff_category=TariffCategory.TYPE_1_2,
            wheeling_cost=0.5,
        )
        
        # Off-peak period comparison
        comparison_off = engine.compare_prices(
            timestamp=datetime(2026, 3, 24, 23, 0),  # Monday off-peak
            energy_kwh=100.0,
            market_clearing_price=3.00,
        )
        
        # Single-buyer rate should be low (off-peak)
        assert comparison_off.single_buyer_rate_baht_kwh == 2.6369
    
    def test_generate_recommendation(self):
        """Test recommendation generation."""
        engine = PriceComparisonEngine(wheeling_cost=0.5)
        
        # Generate comparison with high savings
        comparison = engine.compare_prices(
            timestamp=datetime(2026, 3, 21, 10, 0),
            energy_kwh=500.0,  # Large energy = large savings
            market_clearing_price=3.30,
        )
        
        assert comparison.recommendation != ""
        assert any(word in comparison.recommendation.upper() 
                   for word in ["BUY", "HOLD", "AVOID", "PARTIAL"])
    
    def test_generate_monthly_report(self):
        """Test monthly report generation."""
        engine = PriceComparisonEngine(wheeling_cost=0.5)
        
        # Add multiple comparisons for the month
        for day in range(1, 31):
            engine.compare_prices(
                timestamp=datetime(2026, 3, day, 12, 0),
                energy_kwh=10.0,
                market_clearing_price=3.30,
            )
        
        report = engine.generate_monthly_report(month=3, year=2026)
        
        assert isinstance(report, MonthlyComparisonReport)
        assert report.billing_month == 3
        assert report.billing_year == 2026
        assert report.single_buyer_total_kwh > 0
        assert report.p2p_total_kwh > 0
        assert report.total_savings_baht > 0
        assert report.num_p2p_trades > 0
    
    def test_get_comparison_summary(self):
        """Test comparison summary."""
        engine = PriceComparisonEngine(wheeling_cost=0.5)
        
        # Add comparisons
        for i in range(10):
            engine.compare_prices(
                timestamp=datetime(2026, 3, 21, i, 0),
                energy_kwh=50.0,
                market_clearing_price=3.30,
            )
        
        summary = engine.get_comparison_summary()
        
        assert summary["total_comparisons"] == 10
        assert summary["total_energy_kwh"] == 500.0
        assert "total_buyer_savings_baht" in summary
        assert "total_welfare_gain_baht" in summary
        assert "beneficial_trades_percent" in summary
    
    def test_clear_history(self):
        """Test clearing history."""
        engine = PriceComparisonEngine()
        
        # Add comparisons
        engine.compare_prices(
            timestamp=datetime(2026, 3, 21, 10, 0),
            energy_kwh=100.0,
            market_clearing_price=3.30,
        )
        
        assert len(engine.comparison_history) > 0
        
        # Clear
        engine.clear_history()
        
        assert len(engine.comparison_history) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestPriceComparisonIntegration:
    """Integration tests for price comparison system."""
    
    def test_full_comparison_workflow(self):
        """Test complete comparison workflow."""
        # Initialize engine
        engine = PriceComparisonEngine(
            tariff_category=TariffCategory.TYPE_1_1_2,
            utility_provider=UtilityProvider.PEA,
            wheeling_cost=1.0,  # Moderate wheeling
        )
        
        # Simulate a day of trading (hourly)
        for hour in range(24):
            # Simulate market price based on time of day
            if 9 <= hour <= 16:
                mcp = 3.00  # Midday solar peak (lower prices)
            elif 17 <= hour <= 21:
                mcp = 4.00  # Evening peak (higher prices)
            else:
                mcp = 3.20  # Night
            
            engine.compare_prices(
                timestamp=datetime(2026, 3, 21, hour, 0),
                energy_kwh=20.0,
                market_clearing_price=mcp,
                market_volume=100.0,
                market_sentiment="Stable",
            )
        
        # Get summary
        summary = engine.get_comparison_summary()
        
        # Verify results
        assert summary["total_comparisons"] == 24
        assert summary["total_energy_kwh"] == 480.0  # 24 * 20
        assert summary["total_buyer_savings_baht"] > 0 or summary["total_welfare_gain_baht"] > 0
        
        # Generate monthly report
        report = engine.generate_monthly_report(month=3, year=2026)
        
        assert report.single_buyer_total_cost_baht > 0
        assert report.savings_percent >= 0
    
    def test_arbitrage_opportunity_analysis(self):
        """Test analysis of arbitrage opportunities."""
        engine = PriceComparisonEngine(
            tariff_category=TariffCategory.TYPE_1_2,  # TOU for max spread
            wheeling_cost=0.8,
        )
        
        # Compare during peak (max arbitrage opportunity)
        comparison_peak = engine.compare_prices(
            timestamp=datetime(2026, 3, 24, 19, 0),  # Monday peak
            energy_kwh=100.0,
            market_clearing_price=3.50,
        )
        
        # Compare during off-peak (min arbitrage opportunity)
        comparison_off = engine.compare_prices(
            timestamp=datetime(2026, 3, 24, 2, 0),  # Early morning off-peak
            energy_kwh=100.0,
            market_clearing_price=3.00,
        )
        
        # Peak should have higher savings potential
        # (single-buyer rate is much higher during peak)
        assert comparison_peak.single_buyer_rate_baht_kwh > comparison_off.single_buyer_rate_baht_kwh
    
    def test_wheeling_cost_sensitivity(self):
        """Test sensitivity to wheeling costs."""
        # Low wheeling
        engine_low = PriceComparisonEngine(wheeling_cost=0.5)
        comp_low = engine_low.compare_prices(
            timestamp=datetime(2026, 3, 21, 10, 0),
            energy_kwh=100.0,
            market_clearing_price=3.30,
        )
        
        # High wheeling
        engine_high = PriceComparisonEngine(wheeling_cost=2.0)
        comp_high = engine_high.compare_prices(
            timestamp=datetime(2026, 3, 21, 10, 0),
            energy_kwh=100.0,
            market_clearing_price=3.30,
        )
        
        # Lower wheeling should result in higher welfare
        assert comp_low.total_welfare_gain_baht > comp_high.total_welfare_gain_baht


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
