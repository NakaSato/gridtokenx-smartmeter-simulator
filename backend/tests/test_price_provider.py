"""
Tests for Price Provider Module.
"""

import pytest
from datetime import datetime, timezone, timedelta

from smart_meter_simulator.core.price_provider import (
    TOUTariffPriceProvider,
    P2PMarketPriceProvider,
    PriceComparisonService,
    PriceHistoryManager,
    UtilityProvider,
    TariffCategory,
    P2P_MIN_PRICE,
    P2P_MAX_PRICE,
    P2P_BASE_PRICE,
    WHEELING_CHARGE_RESIDENTIAL,
    WHEELING_CHARGE_COMMERCIAL,
    GRID_LOSS_FACTOR,
)


# ============================================================================
# TOU Tariff Price Provider Tests
# ============================================================================

class TestTOUTariffPriceProvider:
    def setup_method(self):
        self.provider = TOUTariffPriceProvider()

    def test_calculate_utility_price_residential(self):
        result = self.provider.calculate_utility_price(
            energy_kwh=100.0,
            provider=UtilityProvider.PEA,
            category=TariffCategory.RESIDENTIAL_12,
        )
        assert result.provider == "PEA"
        assert result.tariff_category == "residential_1.2"
        assert result.total_amount_baht > 0
        assert result.energy_charge_baht > 0
        assert result.ft_charge_baht > 0
        assert result.vat_baht > 0
        assert result.average_rate_baht_kwh > 0

    def test_calculate_utility_price_commercial(self):
        result = self.provider.calculate_utility_price(
            energy_kwh=200.0,
            provider=UtilityProvider.MEA,
            category=TariffCategory.SMALL_BUSINESS_22,
        )
        assert result.provider == "MEA"
        assert result.tariff_category == "small_business_2.2"

    def test_calculate_zero_energy(self):
        result = self.provider.calculate_utility_price(
            energy_kwh=0.0,
        )
        assert result.total_amount_baht >= 0  # Service charge only
        assert result.average_rate_baht_kwh == 0.0

    def test_get_current_rate(self):
        rate = self.provider.get_current_rate()
        assert rate > 0

    def test_to_dict_has_all_fields(self):
        result = self.provider.calculate_utility_price(energy_kwh=50.0)
        d = result.to_dict()
        assert "provider" in d
        assert "energy_charge_baht" in d
        assert "total_amount_baht" in d
        assert "average_rate_baht_kwh" in d


# ============================================================================
# P2P Market Price Provider Tests
# ============================================================================

class TestP2PMarketPriceProvider:
    def setup_method(self):
        self.provider = P2PMarketPriceProvider()

    def test_calculate_mcp_in_range(self):
        mcp = self.provider.calculate_mcp()
        assert P2P_MIN_PRICE <= mcp <= P2P_MAX_PRICE

    def test_calculate_mcp_oversupply_low_price(self):
        self.provider.set_market_conditions(supply_demand_ratio=2.0)
        mcp = self.provider.calculate_mcp()
        # Oversupply should lower price
        assert mcp < P2P_BASE_PRICE * 1.2

    def test_calculate_mcp_shortage_high_price(self):
        self.provider.set_market_conditions(supply_demand_ratio=0.3)
        mcp = self.provider.calculate_mcp()
        # Shortage should raise price
        assert mcp > P2P_BASE_PRICE * 0.8

    def test_nodal_price_anchor(self):
        mcp = self.provider.calculate_mcp(nodal_price_avg=5.0)
        # Should be pulled toward nodal price
        assert mcp > 3.0  # Above baseline

    def test_calculate_p2p_breakdown(self):
        breakdown = self.provider.calculate_p2p_breakdown(energy_kwh=100.0)
        assert breakdown.market_clearing_price_baht_kwh > 0
        assert breakdown.wheeling_cost_baht_kwh > 0
        assert breakdown.buyer_total_baht_kwh > breakdown.market_clearing_price_baht_kwh
        assert breakdown.seller_net_baht_kwh < breakdown.market_clearing_price_baht_kwh
        assert breakdown.energy_cost_baht > 0
        assert breakdown.market_sentiment in ("buyer_favorable", "seller_favorable", "balanced")

    def test_p2p_breakdown_dict(self):
        breakdown = self.provider.calculate_p2p_breakdown(energy_kwh=50.0)
        d = breakdown.to_dict()
        assert "market_clearing_price_baht_kwh" in d
        assert "buyer_total_cost_baht" in d
        assert "market_sentiment" in d

    def test_market_sentiment_buyer_favorable(self):
        self.provider.set_market_conditions(supply_demand_ratio=2.0)
        breakdown = self.provider.calculate_p2p_breakdown(100.0)
        assert breakdown.market_sentiment == "buyer_favorable"

    def test_market_sentiment_seller_favorable(self):
        self.provider.set_market_conditions(supply_demand_ratio=0.1)
        # Force high price by setting base higher temporarily
        self.provider.base_price = 4.5
        breakdown = self.provider.calculate_p2p_breakdown(100.0)
        self.provider.base_price = P2P_BASE_PRICE  # Reset
        assert breakdown.market_sentiment == "seller_favorable"


# ============================================================================
# Price Comparison Service Tests
# ============================================================================

class TestPriceComparisonService:
    def setup_method(self):
        util = TOUTariffPriceProvider()
        p2p = P2PMarketPriceProvider()
        self.service = PriceComparisonService(util, p2p)

    def test_compare_basic(self):
        result = self.service.compare(energy_kwh=100.0)
        assert "timestamp" in result
        assert "energy_kwh" in result
        assert "utility" in result
        assert "p2p" in result
        assert "analysis" in result
        assert "recommendation" in result

    def test_compare_utility_has_all_fields(self):
        result = self.service.compare(energy_kwh=50.0)
        util = result["utility"]
        assert "provider" in util
        assert "energy_charge_baht" in util
        assert "total_amount_baht" in util
        assert "average_rate_baht_kwh" in util

    def test_compare_p2p_has_all_fields(self):
        result = self.service.compare(energy_kwh=50.0)
        p2p = result["p2p"]
        assert "market_clearing_price_baht_kwh" in p2p
        assert "buyer_total_cost_baht" in p2p
        assert "seller_net_revenue_baht" in p2p

    def test_compare_analysis_has_all_fields(self):
        result = self.service.compare(energy_kwh=50.0)
        analysis = result["analysis"]
        assert "buyer_savings_baht" in analysis
        assert "buyer_savings_percent" in analysis
        assert "is_p2p_beneficial" in analysis
        assert "break_even_price_baht_kwh" in analysis

    def test_compare_with_custom_p2p_price(self):
        result = self.service.compare(
            energy_kwh=100.0,
            p2p_price=2.0,  # Very cheap P2P
        )
        assert result["analysis"]["is_p2p_beneficial"] is True
        assert result["analysis"]["buyer_savings_baht"] > 0

    def test_compare_with_expensive_p2p(self):
        result = self.service.compare(
            energy_kwh=100.0,
            p2p_price=5.5,  # Expensive P2P
        )
        # May still be beneficial depending on utility rates
        assert "buyer_savings_baht" in result["analysis"]

    def test_compare_different_categories(self):
        result = self.service.compare(
            energy_kwh=200.0,
            category=TariffCategory.SMALL_BUSINESS_22,
        )
        assert result["utility"]["tariff_category"] == "small_business_2.2"

    def test_compare_recommendation_exists(self):
        result = self.service.compare(energy_kwh=100.0)
        assert len(result["recommendation"]) > 10
        assert "P2P" in result["recommendation"] or "utility" in result["recommendation"].lower()


# ============================================================================
# Price History Manager Tests
# ============================================================================

class TestPriceHistoryManager:
    def setup_method(self):
        self.history = PriceHistoryManager(max_entries=100)

    def test_record_creates_snapshot(self):
        snap = self.history.record(
            utility_avg=4.5,
            p2p_mcp=3.5,
            p2p_buyer_total=3.85,
        )
        assert snap.utility_avg_baht_kwh == 4.5
        assert snap.p2p_mcp_baht_kwh == 3.5
        assert snap.timestamp is not None

    def test_get_latest(self):
        self.history.record(utility_avg=4.0, p2p_mcp=3.0, p2p_buyer_total=3.3)
        self.history.record(utility_avg=4.5, p2p_mcp=3.5, p2p_buyer_total=3.85)
        latest = self.history.get_latest()
        assert latest is not None
        assert latest.utility_avg_baht_kwh == 4.5

    def test_get_latest_empty(self):
        assert self.history.get_latest() is None

    def test_get_history_returns_list(self):
        for i in range(5):
            self.history.record(
                utility_avg=4.0 + i,
                p2p_mcp=3.0 + i * 0.1,
                p2p_buyer_total=3.3 + i * 0.1,
            )
        history = self.history.get_history()
        assert len(history) == 5
        assert "timestamp" in history[0]

    def test_get_history_respects_limit(self):
        for i in range(20):
            self.history.record(
                utility_avg=4.0 + i * 0.1,
                p2p_mcp=3.0,
                p2p_buyer_total=3.3,
            )
        history = self.history.get_history(limit=5)
        assert len(history) == 5

    def test_get_stats(self):
        for i in range(10):
            self.history.record(
                utility_avg=4.0 + i * 0.1,
                p2p_mcp=3.0 + i * 0.05,
                p2p_buyer_total=3.3,
            )
        stats = self.history.get_stats()
        assert stats["count"] == 10
        assert "utility" in stats
        assert "p2p" in stats
        assert "min" in stats["utility"]
        assert "max" in stats["utility"]
        assert "avg" in stats["utility"]

    def test_get_stats_empty(self):
        stats = self.history.get_stats()
        assert stats["count"] == 0

    def test_max_entries_trimming(self):
        small_history = PriceHistoryManager(max_entries=5)
        for i in range(20):
            small_history.record(
                utility_avg=float(i),
                p2p_mcp=3.0,
                p2p_buyer_total=3.3,
            )
        assert len(small_history.history) == 5
        # Latest should be from last entry
        assert small_history.get_latest().utility_avg_baht_kwh == 19.0

    def test_clear(self):
        self.history.record(utility_avg=4.0, p2p_mcp=3.0, p2p_buyer_total=3.3)
        self.history.clear()
        assert len(self.history.history) == 0
        assert self.history.get_latest() is None


# ============================================================================
# Singleton Access Tests
# ============================================================================

class TestSingletonAccess:
    def test_get_utility_provider(self):
        from smart_meter_simulator.core.price_provider import get_utility_provider
        p1 = get_utility_provider()
        p2 = get_utility_provider()
        assert p1 is p2  # Same instance

    def test_get_p2p_provider(self):
        from smart_meter_simulator.core.price_provider import get_p2p_provider
        p1 = get_p2p_provider()
        p2 = get_p2p_provider()
        assert p1 is p2

    def test_get_comparison_service(self):
        from smart_meter_simulator.core.price_provider import get_comparison_service
        s1 = get_comparison_service()
        s2 = get_comparison_service()
        assert s1 is s2

    def test_get_price_history(self):
        from smart_meter_simulator.core.price_provider import get_price_history
        h1 = get_price_history()
        h2 = get_price_history()
        assert h1 is h2


# ============================================================================
# Constants Tests
# ============================================================================

class TestConstants:
    def test_wheeling_charges(self):
        assert WHEELING_CHARGE_RESIDENTIAL > 0
        assert WHEELING_CHARGE_COMMERCIAL > WHEELING_CHARGE_RESIDENTIAL

    def test_grid_loss_factor(self):
        assert 0 < GRID_LOSS_FACTOR < 1.0

    def test_p2p_price_bounds(self):
        assert P2P_MIN_PRICE < P2P_BASE_PRICE < P2P_MAX_PRICE

    def test_enum_values(self):
        assert UtilityProvider.PEA.value == "PEA"
        assert UtilityProvider.MEA.value == "MEA"
        assert TariffCategory.RESIDENTIAL_12.value == "residential_1.2"
        assert TariffCategory.SMALL_BUSINESS_22.value == "small_business_2.2"
