"""
Unit Tests for Thai Electricity Market Module

Tests for:
- Thai tariff configuration (config/thai_market.py)
- Thai tariff calculator (core/thai_tariff.py)
- Thai calculators (utils/thai_calculators.py)
- Thai billing engine (core/billing.py)

Run with:
    uv run pytest tests/test_thai_market.py -v
"""

import pytest
from datetime import datetime, date
from typing import List, Tuple

from smart_meter_simulator.config.thai_market import (
    TariffCategory,
    UtilityProvider,
    TOUPeriod,
    TYPE_1_1_1_TIERS,
    TYPE_1_1_2_TIERS,
    TOU_RATES,
    SERVICE_CHARGES,
    CURRENT_FT_RATE,
    CURRENT_BASE_TARIFF,
    GRID_BUYBACK_RATE,
    GRID_PURCHASE_RATE_HIGH_TIER,
    TYPICAL_P2P_PRICE,
    SOLAR_TAX_INCENTIVE,
    RESIDENTIAL_WHEELING_COST_AVG,
    get_ft_for_month,
    get_total_tariff,
    get_tou_period,
    calculate_p2p_profitability,
)
from smart_meter_simulator.core.thai_tariff import (
    ThaiTariffCalculator,
    TariffResult,
    calculate_thai_electricity_bill,
    compare_tariff_options,
)
from smart_meter_simulator.utils.thai_calculators import (
    P2PEconomicsCalculator,
    SolarROICalculator,
    detect_utility_provider,
    get_utility_info,
)
from smart_meter_simulator.core.billing import (
    ThaiBillingEngine,
    TransactionType,
    MonthlyBill,
)


# ============================================================================
# Configuration Tests
# ============================================================================

class TestThaiMarketConfig:
    """Tests for Thai market configuration constants."""
    
    def test_utility_providers(self):
        """Test utility provider enum values."""
        assert UtilityProvider.MEA.value == "MEA"
        assert UtilityProvider.PEA.value == "PEA"
        assert UtilityProvider.EGAT.value == "EGAT"
    
    def test_tariff_categories(self):
        """Test tariff category enum values."""
        assert TariffCategory.TYPE_1_1_1.value == "1.1.1"
        assert TariffCategory.TYPE_1_1_2.value == "1.1.2"
        assert TariffCategory.TYPE_1_2.value == "1.2"
        assert TariffCategory.TYPE_1_3.value == "1.3"
    
    def test_tou_periods(self):
        """Test TOU period enum values."""
        assert TOUPeriod.ON_PEAK.value == "on_peak"
        assert TOUPeriod.OFF_PEAK_WEEKDAY.value == "off_peak_weekday"
        assert TOUPeriod.OFF_PEAK_WEEKEND.value == "off_peak_weekend"
    
    def test_ladder_tiers_type_1_1_1(self):
        """Test Type 1.1.1 ladder tier structure."""
        assert len(TYPE_1_1_1_TIERS) == 5
        assert TYPE_1_1_1_TIERS[0].min_kwh == 0
        assert TYPE_1_1_1_TIERS[0].max_kwh == 15
        assert TYPE_1_1_1_TIERS[0].rate_baht_per_kwh == 2.3488
        
        # Top tier
        assert TYPE_1_1_1_TIERS[-1].min_kwh == 101
        assert TYPE_1_1_1_TIERS[-1].max_kwh == 150
    
    def test_ladder_tiers_type_1_1_2(self):
        """Test Type 1.1.2 ladder tier structure."""
        assert len(TYPE_1_1_2_TIERS) == 3
        assert TYPE_1_1_2_TIERS[0].rate_baht_per_kwh == 3.2484
        assert TYPE_1_1_2_TIERS[-1].max_kwh is None  # Unlimited top tier
        assert TYPE_1_1_2_TIERS[-1].rate_baht_per_kwh == 4.4217
    
    def test_tou_rates(self):
        """Test TOU rate structure."""
        assert TOU_RATES[TOUPeriod.ON_PEAK] == 5.7982
        assert TOU_RATES[TOUPeriod.OFF_PEAK_WEEKDAY] == 2.6369
        assert TOU_RATES[TOUPeriod.OFF_PEAK_WEEKEND] == 2.6369
        
        # On-peak should be highest
        assert TOU_RATES[TOUPeriod.ON_PEAK] > TOU_RATES[TOUPeriod.OFF_PEAK_WEEKDAY]
    
    def test_service_charges(self):
        """Test service charge by tariff category."""
        assert SERVICE_CHARGES[TariffCategory.TYPE_1_1_1] == 8.19
        assert SERVICE_CHARGES[TariffCategory.TYPE_1_1_2] == 24.62
        assert SERVICE_CHARGES[TariffCategory.TYPE_1_2] == 33.29
    
    def test_ft_rate_constants(self):
        """Test Ft rate constants."""
        assert CURRENT_FT_RATE == 0.0972  # Jan-Apr 2026
        assert CURRENT_BASE_TARIFF == 3.78
        assert abs(get_total_tariff() - 3.8772) < 0.001
    
    def test_grid_rates(self):
        """Test grid buy-back and purchase rates."""
        assert GRID_BUYBACK_RATE == 2.20
        assert GRID_PURCHASE_RATE_HIGH_TIER == 4.4217
        assert GRID_PURCHASE_RATE_HIGH_TIER > GRID_BUYBACK_RATE
        
        # Arbitrage spread
        spread = GRID_PURCHASE_RATE_HIGH_TIER - GRID_BUYBACK_RATE
        assert abs(spread - 2.2217) < 0.001
    
    def test_solar_tax_incentive(self):
        """Test Royal Decree No. 805 solar tax incentive."""
        assert SOLAR_TAX_INCENTIVE.max_deduction_baht == 200_000
        assert SOLAR_TAX_INCENTIVE.capacity_limit_kwp == 10
        assert SOLAR_TAX_INCENTIVE.start_date == "2026-03-03"
        assert SOLAR_TAX_INCENTIVE.end_date == "2028-12-31"


# ============================================================================
# Helper Function Tests
# ============================================================================

class TestHelperFunctions:
    """Tests for helper functions in thai_market module."""
    
    def test_get_ft_for_month_jan_apr(self):
        """Test Ft rate for Jan-Apr period."""
        for month in [1, 2, 3, 4]:
            assert get_ft_for_month(month) == 0.0972
    
    def test_get_ft_for_month_may_aug(self):
        """Test Ft rate for May-Aug period."""
        for month in [5, 6, 7, 8]:
            ft = get_ft_for_month(month)
            assert ft == 0.18  # Projected rate
    
    def test_get_ft_for_month_sep_dec(self):
        """Test Ft rate for Sep-Dec period."""
        for month in [9, 10, 11, 12]:
            ft = get_ft_for_month(month)
            assert ft == 0.1572  # 2025 rate
    
    def test_get_total_tariff(self):
        """Test total tariff calculation."""
        # With default Ft (0.0972)
        total = get_total_tariff()
        assert abs(total - 3.8772) < 0.001
        
        # With custom Ft
        total = get_total_tariff(ft_rate=0.15)
        assert abs(total - 3.93) < 0.001
    
    def test_get_tou_period_weekday(self):
        """Test TOU period detection for weekdays."""
        # On-peak: 09:00-22:00
        for hour in [9, 12, 15, 18, 21]:
            dt = datetime(2026, 3, 23, hour, 0)  # Monday
            assert get_tou_period(hour, is_weekend=False) == TOUPeriod.ON_PEAK
        
        # Off-peak: 22:00-09:00
        for hour in [0, 3, 6, 22, 23]:
            dt = datetime(2026, 3, 23, hour, 0)  # Monday
            assert get_tou_period(hour, is_weekend=False) == TOUPeriod.OFF_PEAK_WEEKDAY
    
    def test_get_tou_period_weekend(self):
        """Test TOU period detection for weekends."""
        # All day off-peak on weekends
        for hour in range(24):
            assert get_tou_period(hour, is_weekend=True) == TOUPeriod.OFF_PEAK_WEEKEND
    
    def test_calculate_p2p_profitability(self):
        """Test P2P profitability calculation."""
        result = calculate_p2p_profitability(
            p2p_price=3.30,
            wheeling_cost=1.76
        )
        
        # Note: The helper function charges wheeling to both parties (conservative)
        # For more realistic analysis, use P2PEconomicsCalculator with wheeling_split
        
        # Seller economics (net of full wheeling)
        assert result["seller_p2p_net_baht_kwh"] == 3.30 - 1.76
        
        # Buyer economics (includes full wheeling)
        assert result["buyer_p2p_total_baht_kwh"] == 3.30 + 1.76
        
        # With full wheeling on both sides, may not be mutually beneficial
        # This is the conservative scenario


# ============================================================================
# Thai Tariff Calculator Tests
# ============================================================================

class TestThaiTariffCalculator:
    """Tests for ThaiTariffCalculator class."""
    
    def test_calculate_ladder_tariff_type_1_1_1_low(self):
        """Test Type 1.1.1 tariff for low consumption."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_1_1)
        result = calc.calculate_ladder_tariff(100.0)
        
        assert result.total_kwh == 100.0
        assert result.tariff_type == "1.1.1"
        assert result.service_charge == 8.19
        assert result.total_amount > 0
        
        # Average rate should be in the 3.x Baht/kWh range
        assert 3.0 < result.average_rate < 4.0
    
    def test_calculate_ladder_tariff_type_1_1_1_boundary(self):
        """Test Type 1.1.1 tariff at 150 kWh boundary."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_1_1)
        result = calc.calculate_ladder_tariff(150.0)
        
        # Should use all 5 tiers
        breakdown = result.breakdown["tier_breakdown"]
        assert len(breakdown.tier_consumptions) == 5
    
    def test_calculate_ladder_tariff_type_1_1_2_medium(self):
        """Test Type 1.1.2 tariff for medium consumption."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_1_2)
        result = calc.calculate_ladder_tariff(300.0)
        
        assert result.total_kwh == 300.0
        assert result.tariff_type == "1.1.2"
        assert result.service_charge == 24.62
        
        # Average rate should be around 4.x Baht/kWh
        assert 3.5 < result.average_rate < 4.5
    
    def test_calculate_ladder_tariff_type_1_1_2_high(self):
        """Test Type 1.1.2 tariff for high consumption (>400 kWh)."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_1_2)
        result = calc.calculate_ladder_tariff(500.0)
        
        # Should include top tier (4.4217 Baht/kWh)
        breakdown = result.breakdown["tier_breakdown"]
        top_tier = breakdown.tier_consumptions[-1]
        assert top_tier[0] == 401  # min_kwh
        
        # Average rate should be around 4.1+ Baht/kWh (blended across tiers)
        assert result.average_rate > 4.0
    
    def test_calculate_tou_tariff_weekday_peak(self):
        """Test TOU tariff for weekday peak consumption."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_2)
        
        # All consumption during on-peak
        profile = [
            (datetime(2026, 3, 23, 10, 0), 10.0),  # Monday 10:00
            (datetime(2026, 3, 23, 15, 0), 15.0),  # Monday 15:00
            (datetime(2026, 3, 24, 12, 0), 20.0),  # Tuesday 12:00
        ]
        
        result = calc.calculate_tou_tariff(profile)
        
        assert result.total_kwh == 45.0
        assert "TOU" in result.tariff_type
        
        # All should be at on-peak rate
        expected_energy_charge = 45.0 * TOU_RATES[TOUPeriod.ON_PEAK]
        assert abs(result.energy_charge - expected_energy_charge) < 0.01
    
    def test_calculate_tou_tariff_mixed_periods(self):
        """Test TOU tariff with mixed peak/off-peak consumption."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_2)
        
        profile = [
            (datetime(2026, 3, 23, 10, 0), 10.0),  # Monday on-peak
            (datetime(2026, 3, 23, 23, 0), 10.0),  # Monday off-peak
            (datetime(2026, 3, 28, 12, 0), 10.0),  # Saturday off-peak
        ]
        
        result = calc.calculate_tou_tariff(profile)
        
        assert result.total_kwh == 30.0
        
        # Check period breakdown
        period_consumption = result.breakdown["period_consumption"]
        assert period_consumption["on_peak"] == 10.0
        assert period_consumption["off_peak_weekday"] == 10.0
        assert period_consumption["off_peak_weekend"] == 10.0
    
    def test_calculate_monthly_bill_with_ft(self):
        """Test monthly bill with automatic Ft rate selection."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_1_2)
        
        # January (Ft = 0.0972)
        result_jan = calc.calculate_monthly_bill(300.0, billing_month=1, billing_year=2026)
        assert result_jan.breakdown["ft_rate"] == 0.0972
        
        # September (Ft = 0.1572)
        result_sep = calc.calculate_monthly_bill(300.0, billing_month=9, billing_year=2026)
        assert result_sep.breakdown["ft_rate"] == 0.1572
        
        # Higher Ft should result in higher total
        assert result_sep.total_amount > result_jan.total_amount
    
    def test_invalid_tariff_category(self):
        """Test error handling for invalid tariff category."""
        calc = ThaiTariffCalculator(TariffCategory.TYPE_1_2)
        
        with pytest.raises(ValueError):
            calc.calculate_ladder_tariff(100.0)


# ============================================================================
# P2P Economics Calculator Tests
# ============================================================================

class TestP2PEconomicsCalculator:
    """Tests for P2PEconomicsCalculator class."""
    
    def test_analyze_trade_profitable(self):
        """Test P2P trade analysis for profitable scenario with split wheeling."""
        calc = P2PEconomicsCalculator(
            wheeling_cost_baht_kwh=1.76,
            grid_buyback_rate=2.20,
            grid_purchase_rate=4.4217,
        )
        
        # With 50-50 wheeling split, both parties should benefit
        economics = calc.analyze_trade(
            energy_kwh=100.0, 
            p2p_price_baht_kwh=3.30,
            wheeling_split=0.5,  # Split wheeling 50-50
        )
        
        # Seller should gain vs utility buyback (after paying half wheeling)
        # Seller net: 330 - 88 = 242, vs utility: 220, gain = 22 Baht
        assert economics.seller_vs_utility_gain_baht > 0
        
        # Buyer should save vs utility purchase (after paying half wheeling)
        # Buyer total: 330 + 88 = 418, vs utility: 442.17, savings = 24.17 Baht
        assert economics.buyer_vs_utility_savings_baht > 0
        
        # Trade should be mutually beneficial
        assert economics.is_mutually_beneficial is True
    
    def test_analyze_trade_unprofitable_high_wheeling(self):
        """Test P2P trade with high wheeling cost."""
        calc = P2PEconomicsCalculator(
            wheeling_cost_baht_kwh=3.0,  # Very high wheeling
            grid_buyback_rate=2.20,
            grid_purchase_rate=4.4217,
        )
        
        economics = calc.analyze_trade(
            energy_kwh=100.0, 
            p2p_price_baht_kwh=3.30,
            wheeling_split=0.5,
        )
        
        # High wheeling should make it unprofitable
        assert economics.is_mutually_beneficial is False
    
    def test_find_optimal_p2p_price(self):
        """Test optimal P2P price calculation."""
        calc = P2PEconomicsCalculator(
            wheeling_cost_baht_kwh=1.76,
            grid_buyback_rate=2.20,
            grid_purchase_rate=4.4217,
        )
        
        result = calc.find_optimal_p2p_price(
            energy_kwh=100.0,
            wheeling_split=0.5,
        )
        
        assert result["is_feasible"] is True
        assert result["optimal_price_baht_kwh"] is not None
        
        # Optimal price should be between min and max
        assert result["optimal_price_baht_kwh"] > result["seller_min_price_baht_kwh"]
        assert result["optimal_price_baht_kwh"] < result["buyer_max_price_baht_kwh"]
    
    def test_calculate_tpa_breakdown(self):
        """Test TPA wheeling charge breakdown."""
        calc = P2PEconomicsCalculator()
        
        breakdown = calc.calculate_tpa_breakdown(energy_kwh=100.0)
        
        assert len(breakdown.components) > 0
        assert breakdown.total_wheeling_baht > 0
        assert breakdown.total_wheeling_per_kwh > 0
        
        # Sum of components should equal total
        component_sum = sum(c["total_baht"] for c in breakdown.components)
        assert abs(component_sum - breakdown.total_wheeling_baht) < 0.01
    
    def test_sensitivity_analysis(self):
        """Test P2P price sensitivity analysis."""
        calc = P2PEconomicsCalculator()
        
        results = calc.sensitivity_analysis(
            energy_kwh=100.0,
            price_range=(2.5, 4.0, 0.1),
            wheeling_split=0.5,
        )
        
        assert len(results) > 0
        
        # Should show some profitable scenarios with reasonable wheeling split
        profitable_count = sum(1 for r in results if r["mutually_beneficial"])
        assert profitable_count > 0


# ============================================================================
# Solar ROI Calculator Tests
# ============================================================================

class TestSolarROICalculator:
    """Tests for SolarROICalculator class."""
    
    def test_calculate_roi_basic(self):
        """Test basic solar ROI calculation."""
        calc = SolarROICalculator()
        
        result = calc.calculate_roi(
            capacity_kwp=5.0,
            installation_cost_baht=175_000,
            annual_generation_kwh=7_500,
            self_consumption_ratio=0.3,
            tax_bracket_percent=20.0,
        )
        
        assert result.capacity_kwp == 5.0
        assert result.installation_cost_baht == 175_000
        assert result.annual_generation_kwh == 7_500
        
        # Should have positive savings
        assert result.annual_savings_baht > 0
        assert result.total_annual_benefit_baht > 0
        
        # Tax incentive should apply
        assert result.tax_deduction_baht > 0
        assert result.tax_savings_baht > 0
        
        # Effective cost should be lower than installation cost
        assert result.effective_installation_cost_baht < result.installation_cost_baht
        
        # Payback should be reasonable (3-10 years)
        assert 3 < result.simple_payback_years < 10
    
    def test_calculate_roi_with_p2p(self):
        """Test solar ROI with P2P trading."""
        calc = SolarROICalculator(
            p2p_price=3.30,
            wheeling_cost=1.76,
        )
        
        result = calc.calculate_roi(
            capacity_kwp=5.0,
            installation_cost_baht=175_000,
            annual_generation_kwh=7_500,
            self_consumption_ratio=0.3,
        )
        
        # Should have P2P revenue
        assert result.annual_p2p_revenue_baht > 0
    
    def test_compare_with_benchmark(self):
        """Test solar benchmark comparison."""
        calc = SolarROICalculator()
        
        # Competitive cost
        comparison = calc.compare_with_benchmark(
            capacity_kwp=5.0,
            installation_cost_baht=175_000,
        )
        
        assert comparison.system_capacity_kwp == 5.0
        assert comparison.benchmark_cost_range_baht[0] > 0
        assert comparison.benchmark_cost_range_baht[1] > 0
    
    def test_generate_financial_projection(self):
        """Test year-by-year financial projection."""
        calc = SolarROICalculator()
        
        projections = calc.generate_financial_projection(
            capacity_kwp=5.0,
            installation_cost_baht=175_000,
            annual_generation_kwh=7_500,
            self_consumption_ratio=0.3,
        )
        
        # Should have 26 entries (year 0 + 25 years)
        assert len(projections) == 26
        
        # Year 0 should show installation cost
        assert projections[0]["year"] == 0
        assert projections[0]["net_cash_flow_baht"] < 0
        
        # Year 1 should show positive cash flow
        assert projections[1]["net_cash_flow_baht"] > 0
        
        # Should eventually achieve payback
        payback_years = [p for p in projections if p.get("payback_achieved", False)]
        assert len(payback_years) > 0


# ============================================================================
# Utility Provider Tests
# ============================================================================

class TestUtilityProvider:
    """Tests for utility provider detection."""
    
    def test_detect_utility_provider_mea(self):
        """Test MEA jurisdiction detection."""
        assert detect_utility_provider("Bangkok") == UtilityProvider.MEA
        assert detect_utility_provider("Nonthaburi") == UtilityProvider.MEA
        assert detect_utility_provider("Samut Prakan") == UtilityProvider.MEA
    
    def test_detect_utility_provider_pea(self):
        """Test PEA jurisdiction detection."""
        assert detect_utility_provider("Chiang Mai") == UtilityProvider.PEA
        assert detect_utility_provider("Phuket") == UtilityProvider.PEA
        assert detect_utility_provider("Khon Kaen") == UtilityProvider.PEA
    
    def test_get_utility_info(self):
        """Test utility information retrieval."""
        info = get_utility_info(UtilityProvider.MEA)
        
        assert "provider" in info
        assert info["provider"] == "MEA"
        assert "Bangkok" in info["service_areas"]
        assert info["net_metering_active"] is True
        
        info = get_utility_info(UtilityProvider.PEA)
        assert info["provider"] == "PEA"


# ============================================================================
# Billing Engine Tests
# ============================================================================

class TestThaiBillingEngine:
    """Tests for ThaiBillingEngine class."""
    
    def test_add_grid_consumption(self):
        """Test recording grid consumption."""
        engine = ThaiBillingEngine(
            account_id="TEST-001",
            tariff_category=TariffCategory.TYPE_1_1_2,
        )
        
        tx = engine.add_grid_consumption(
            energy_kwh=100.0,
            timestamp=datetime(2026, 3, 21, 10, 0),
        )
        
        assert tx.transaction_type == TransactionType.GRID_PURCHASE
        assert tx.energy_kwh == 100.0
        assert tx.meter_id == "TEST-001"
    
    def test_add_p2p_transactions(self):
        """Test recording P2P transactions."""
        engine = ThaiBillingEngine(account_id="TEST-001")
        
        # P2P purchase
        buy_tx = engine.add_p2p_purchase(
            energy_kwh=50.0,
            price_baht_kwh=3.30,
            seller_id="SELLER-001",
            timestamp=datetime(2026, 3, 21, 10, 0),
        )
        
        assert buy_tx.transaction_type == TransactionType.P2P_BUY
        assert buy_tx.wheeling_cost_baht > 0
        
        # P2P sale
        sell_tx = engine.add_p2p_sale(
            energy_kwh=30.0,
            price_baht_kwh=3.30,
            buyer_id="BUYER-001",
            timestamp=datetime(2026, 3, 21, 12, 0),
        )
        
        assert sell_tx.transaction_type == TransactionType.P2P_SELL
        assert sell_tx.wheeling_cost_baht > 0
    
    def test_add_solar_generation(self):
        """Test recording solar generation."""
        engine = ThaiBillingEngine(account_id="TEST-001")
        
        self_consumption_tx, export_tx = engine.add_solar_generation(
            energy_kwh=100.0,
            timestamp=datetime(2026, 3, 21, 12, 0),
            self_consumption_ratio=0.3,
        )
        
        # Self-consumption transaction
        assert self_consumption_tx.transaction_type == TransactionType.SOLAR_SELF_CONSUMPTION
        assert self_consumption_tx.energy_kwh == 30.0  # 30% of 100
        
        # Export transaction
        assert export_tx is not None
        assert export_tx.transaction_type == TransactionType.GRID_EXPORT
        assert export_tx.energy_kwh == 70.0  # 70% of 100
    
    def test_generate_monthly_bill(self):
        """Test monthly bill generation."""
        engine = ThaiBillingEngine(
            account_id="TEST-001",
            tariff_category=TariffCategory.TYPE_1_1_2,
        )
        
        # Add various transactions
        engine.add_grid_consumption(200.0, datetime(2026, 3, 15, 10, 0))
        engine.add_solar_generation(50.0, datetime(2026, 3, 15, 12, 0))
        engine.add_p2p_sale(20.0, 3.30, "BUYER-001", datetime(2026, 3, 15, 14, 0))
        
        bill = engine.generate_monthly_bill(billing_month=3, billing_year=2026)
        
        assert bill.billing_month == 3
        assert bill.billing_year == 2026
        assert bill.account_id == "TEST-001"
        assert bill.grid_consumption_kwh > 0
        assert bill.net_amount_baht >= 0
    
    def test_billing_summary_recommendations(self):
        """Test billing summary recommendations."""
        engine = ThaiBillingEngine(
            account_id="TEST-001",
            tariff_category=TariffCategory.TYPE_1_1_2,
        )
        
        # Add high consumption
        engine.add_grid_consumption(500.0, datetime(2026, 3, 15, 10, 0))
        
        summary = engine.get_billing_summary(billing_month=3, billing_year=2026)
        
        assert len(summary.recommendations) > 0
        
        # Should recommend reducing consumption or adding solar
        rec_text = " ".join(summary.recommendations).lower()
        assert "consumption" in rec_text or "solar" in rec_text
    
    def test_clear_transactions(self):
        """Test clearing transactions."""
        engine = ThaiBillingEngine(account_id="TEST-001")
        
        engine.add_grid_consumption(100.0, datetime(2026, 3, 15, 10, 0))
        assert len(engine.transactions) > 0
        
        engine.clear_transactions()
        assert len(engine.transactions) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestThaiMarketIntegration:
    """Integration tests for Thai market modules."""
    
    def test_complete_billing_flow(self):
        """Test complete billing flow with all components."""
        # Create billing engine
        engine = ThaiBillingEngine(
            account_id="TH-2026-001",
            tariff_category=TariffCategory.TYPE_1_1_2,
            utility_provider=UtilityProvider.PEA,
        )
        
        # Simulate a month of activity
        # Grid consumption (daily)
        for day in range(1, 31):
            engine.add_grid_consumption(
                energy_kwh=10.0,
                timestamp=datetime(2026, 3, day, 18, 0),
            )
        
        # Solar generation (daily, sunny days)
        for day in range(1, 31):
            engine.add_solar_generation(
                energy_kwh=20.0,
                timestamp=datetime(2026, 3, day, 12, 0),
                self_consumption_ratio=0.3,
            )
        
        # P2P sales (surplus)
        for day in range(1, 31):
            engine.add_p2p_sale(
                energy_kwh=5.0,
                price_baht_kwh=3.30,
                buyer_id=f"BUYER-{day:02d}",
                timestamp=datetime(2026, 3, day, 14, 0),
            )
        
        # Generate bill
        bill = engine.generate_monthly_bill(billing_month=3, billing_year=2026)
        
        # Verify bill components
        assert bill.grid_consumption_kwh == 300.0  # 10 kWh × 30 days
        assert bill.solar_generation_kwh == 600.0  # 20 kWh × 30 days
        assert bill.p2p_sales_kwh == 150.0  # 5 kWh × 30 days
        
        # Get summary
        summary = engine.get_billing_summary(billing_month=3, billing_year=2026)
        assert summary.carbon_offset_kg > 0
        assert len(summary.recommendations) > 0
    
    def test_tariff_comparison(self):
        """Test tariff option comparison."""
        # Create TOU profile for typical household
        tou_profile: List[Tuple[datetime, float]] = []
        
        # Weekday consumption pattern
        for day in [23, 24, 25, 26, 27]:  # Mon-Fri
            tou_profile.append((datetime(2026, 3, day, 8, 0), 2.0))   # Off-peak
            tou_profile.append((datetime(2026, 3, day, 12, 0), 3.0))  # On-peak
            tou_profile.append((datetime(2026, 3, day, 19, 0), 4.0))  # On-peak
            tou_profile.append((datetime(2026, 3, day, 23, 0), 1.0))  # Off-peak
        
        # Weekend consumption
        for day in [28, 29]:  # Sat-Sun
            tou_profile.append((datetime(2026, 3, day, 12, 0), 5.0))  # Off-peak
        
        total_kwh = sum(kwh for _, kwh in tou_profile)
        
        # Compare tariffs
        comparison = compare_tariff_options(
            monthly_consumption_kwh=total_kwh,
            tou_profile=tou_profile,
        )
        
        assert "all_options" in comparison
        assert "recommended" in comparison
        assert "potential_savings_baht" in comparison


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
