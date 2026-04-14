"""
Tests for Billing Engine: TOU tariffs, ERC ladder, net metering, aggregation.
"""

import pytest
from datetime import datetime, timezone, timedelta

from smart_meter_simulator.core.billing import (
    BillingEngine,
    TOUTariff,
    MeterBillingRecord,
    is_on_peak,
    get_tou_rate,
    calculate_erc_ladder_bill,
    calculate_tou_bill,
    calculate_net_metering_bill,
    TOU_RESIDENTIAL_12_LV,
    TOU_SMALL_BUSINESS_22_LV,
    FT_CHARGE,
    VAT_RATE,
    NET_METERING_FIT_RATE,
    ERC_LADDER_TIERS,
)


# ============================================================================
# TOU Time Period Tests
# ============================================================================

class TestTOUPeriods:
    def test_weekday_on_peak(self):
        # Monday 14:00
        dt = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        assert is_on_peak(dt) is True

    def test_weekday_off_peak_morning(self):
        # Monday 07:00
        dt = datetime(2026, 4, 13, 7, 0, tzinfo=timezone.utc)
        assert is_on_peak(dt) is False

    def test_weekday_off_peak_evening(self):
        # Monday 23:00
        dt = datetime(2026, 4, 13, 23, 0, tzinfo=timezone.utc)
        assert is_on_peak(dt) is False

    def test_saturday_all_day_off_peak(self):
        # Saturday 15:00
        dt = datetime(2026, 4, 18, 15, 0, tzinfo=timezone.utc)
        assert is_on_peak(dt) is False

    def test_sunday_all_day_off_peak(self):
        # Sunday 10:00
        dt = datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc)
        assert is_on_peak(dt) is False

    def test_boundary_9am_on_peak(self):
        dt = datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc)
        assert is_on_peak(dt) is True

    def test_boundary_10pm_off_peak(self):
        dt = datetime(2026, 4, 13, 22, 0, tzinfo=timezone.utc)
        assert is_on_peak(dt) is False


# ============================================================================
# TOU Rate Calculation Tests
# ============================================================================

class TestTOURates:
    def test_on_peak_rate(self):
        dt = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        rate = get_tou_rate(dt, TOU_RESIDENTIAL_12_LV)
        assert rate == pytest.approx(5.7982)

    def test_off_peak_rate(self):
        dt = datetime(2026, 4, 13, 7, 0, tzinfo=timezone.utc)
        rate = get_tou_rate(dt, TOU_RESIDENTIAL_12_LV)
        assert rate == pytest.approx(2.6369)

    def test_small_business_rates(self):
        dt_on = datetime(2026, 4, 14, 12, 0, tzinfo=timezone.utc)
        dt_off = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
        assert get_tou_rate(dt_on, TOU_SMALL_BUSINESS_22_LV) == pytest.approx(5.7982)
        assert get_tou_rate(dt_off, TOU_SMALL_BUSINESS_22_LV) == pytest.approx(2.6369)


# ============================================================================
# ERC Ladder Billing Tests
# ============================================================================

class TestERCLadder:
    def test_tier1_only(self):
        # 100 kWh in tier 1
        bill = calculate_erc_ladder_bill(100.0)
        expected = 100.0 * 3.2480
        assert bill == pytest.approx(expected, rel=0.01)

    def test_tier2_only(self):
        # 200 kWh: 150 in tier1, 50 in tier2
        bill = calculate_erc_ladder_bill(200.0)
        expected = 150.0 * 3.2480 + 50.0 * 4.2218
        assert bill == pytest.approx(expected, rel=0.01)

    def test_tier3(self):
        # 500 kWh: 150 tier1, 250 tier2, 100 tier3
        bill = calculate_erc_ladder_bill(500.0)
        expected = 150.0 * 3.2480 + 250.0 * 4.2218 + 100.0 * 4.4217
        assert bill == pytest.approx(expected, rel=0.01)

    def test_zero_consumption(self):
        bill = calculate_erc_ladder_bill(0.0)
        assert bill == pytest.approx(0.0)


# ============================================================================
# TOU Bill Calculation Tests
# ============================================================================

class TestTOUBill:
    def test_basic_bill(self):
        result = calculate_tou_bill(
            on_peak_kwh=100.0,
            off_peak_kwh=50.0,
            tariff=TOU_RESIDENTIAL_12_LV,
        )
        energy = 100.0 * 5.7982 + 50.0 * 2.6369
        ft = FT_CHARGE * 150.0
        svc = TOU_RESIDENTIAL_12_LV.service_charge
        subtotal = energy + ft + svc
        vat = subtotal * VAT_RATE
        total = subtotal + vat

        assert result["on_peak_kwh"] == 100.0
        assert result["off_peak_kwh"] == 50.0
        assert result["total_kwh"] == 150.0
        assert result["energy_charge_baht"] == pytest.approx(energy, rel=0.01)
        assert result["ft_charge_baht"] == pytest.approx(ft, rel=0.01)
        assert result["total_baht"] == pytest.approx(total, rel=0.01)

    def test_zero_consumption_bill(self):
        result = calculate_tou_bill(0.0, 0.0, tariff=TOU_RESIDENTIAL_12_LV)
        # Should still have service charge
        assert result["energy_charge_baht"] == 0.0
        assert result["total_baht"] > 0  # Service charge + VAT


# ============================================================================
# Net Metering Tests
# ============================================================================

class TestNetMetering:
    def test_net_positive(self):
        # Consumed 200 kWh, exported 50 kWh
        result = calculate_net_metering_bill(
            consumed_kwh=200.0,
            exported_kwh=50.0,
        )
        consumed_charge = 200.0 * TOU_RESIDENTIAL_12_LV.on_peak_rate
        export_credit = 50.0 * NET_METERING_FIT_RATE
        assert result["consumed_charge_baht"] == pytest.approx(consumed_charge, rel=0.01)
        assert result["export_credit_baht"] == pytest.approx(export_credit, rel=0.01)
        assert result["net_baht"] > 0

    def test_export_exceeds_consumption(self):
        # Net metering should not go negative
        result = calculate_net_metering_bill(
            consumed_kwh=10.0,
            exported_kwh=100.0,
        )
        assert result["net_baht"] >= 0

    def test_no_export(self):
        result = calculate_net_metering_bill(
            consumed_kwh=100.0,
            exported_kwh=0.0,
        )
        assert result["export_credit_baht"] == 0.0


# ============================================================================
# Billing Engine Integration Tests
# ============================================================================

class TestBillingEngine:
    def test_register_meter(self):
        engine = BillingEngine()
        rec = engine.register_meter("M001", "Residential")
        assert rec.meter_id == "M001"
        assert rec.tariff == TOU_RESIDENTIAL_12_LV
        assert "M001" in engine.meter_records

    def test_auto_register_on_consume(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 5.0, 2.0, ts)
        assert "M001" in engine.meter_records

    def test_consume_on_peak(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)  # Mon 14:00
        engine.consume_reading("M001", 10.0, 5.0, ts)
        rec = engine.meter_records["M001"]
        assert rec.on_peak_consumed == 10.0
        assert rec.off_peak_consumed == 0.0

    def test_consume_off_peak(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 2, 0, tzinfo=timezone.utc)  # Mon 02:00
        engine.consume_reading("M001", 8.0, 3.0, ts)
        rec = engine.meter_records["M001"]
        assert rec.off_peak_consumed == 8.0
        assert rec.on_peak_consumed == 0.0

    def test_consume_weekend(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 18, 15, 0, tzinfo=timezone.utc)  # Sat 15:00
        engine.consume_reading("M001", 12.0, 6.0, ts)
        rec = engine.meter_records["M001"]
        assert rec.off_peak_consumed == 12.0

    def test_multiple_readings_accumulate(self):
        engine = BillingEngine()
        ts1 = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 4, 13, 15, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 5.0, 2.0, ts1)
        engine.consume_reading("M001", 3.0, 1.0, ts2)
        rec = engine.meter_records["M001"]
        assert rec.on_peak_consumed == 8.0
        assert rec.on_peak_generated == 3.0

    def test_surplus_tracking(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        # Generated 10, consumed 3 => surplus 7
        engine.consume_reading("M001", 3.0, 10.0, ts)
        rec = engine.meter_records["M001"]
        assert rec.exported_to_grid == 7.0

    def test_no_surplus_when_consuming(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 10.0, 3.0, ts)
        rec = engine.meter_records["M001"]
        assert rec.exported_to_grid == 0.0

    def test_calculate_meter_bill_tou(self):
        engine = BillingEngine()
        ts_on = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        ts_off = datetime(2026, 4, 13, 23, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 100.0, 20.0, ts_on)
        engine.consume_reading("M001", 50.0, 10.0, ts_off)

        bill = engine.calculate_meter_bill("M001", method="tou")
        assert bill["on_peak_kwh"] == 100.0
        assert bill["off_peak_kwh"] == 50.0
        assert bill["total_baht"] > 0

    def test_calculate_meter_bill_erc(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 200.0, 0.0, ts)

        bill = engine.calculate_meter_bill("M001", method="erc")
        assert bill["total_kwh"] == 200.0
        assert bill["total_baht"] > 0

    def test_calculate_meter_bill_net_metering(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 50.0, 200.0, ts)  # Surplus 150

        bill = engine.calculate_meter_bill("M001", method="net_metering")
        assert bill["consumed_kwh"] == 50.0
        assert bill["exported_kwh"] == 150.0

    def test_calculate_all_bills(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 100.0, 20.0, ts)
        engine.consume_reading("M002", 80.0, 15.0, ts)

        bills = engine.calculate_all_bills(method="tou")
        assert len(bills) == 2
        assert engine.total_billed_baht > 0
        assert engine.meters_billed_count == 2

    def test_get_summary(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 100.0, 20.0, ts)
        engine.calculate_all_bills(method="tou")

        summary = engine.get_summary()
        assert "total_billed_thb" in summary
        assert "total_meters_billed" in summary
        assert summary["total_meters_billed"] == 1

    def test_get_meter_detail(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 100.0, 20.0, ts)

        detail = engine.get_meter_detail("M001")
        assert detail["meter_id"] == "M001"
        assert detail["on_peak_consumed_kwh"] == 100.0
        assert detail["tariff"] == "Residential 1.2"

    def test_get_meter_detail_not_found(self):
        engine = BillingEngine()
        assert engine.get_meter_detail("NONEXISTENT") is None

    def test_reset_billing_period(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 100.0, 20.0, ts)
        engine.calculate_all_bills(method="tou")

        engine.reset_billing_period()
        rec = engine.meter_records["M001"]
        assert rec.on_peak_consumed == 0.0
        assert rec.off_peak_consumed == 0.0
        assert rec.exported_to_grid == 0.0
        assert engine.total_billed_baht == 0.0

    def test_unknown_meter_bill(self):
        engine = BillingEngine()
        bill = engine.calculate_meter_bill("UNKNOWN", method="tou")
        assert "error" in bill

    def test_unknown_billing_method(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 10.0, 5.0, ts)

        bill = engine.calculate_meter_bill("M001", method="invalid_method")
        assert "error" in bill


# ============================================================================
# Tariff Mapping Tests
# ============================================================================

class TestTariffMapping:
    def test_residential_tariff(self):
        engine = BillingEngine()
        ts = datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc)
        engine.consume_reading("M001", 50.0, 10.0, ts)
        rec = engine.meter_records["M001"]
        assert rec.meter_type == "Unknown"  # Auto-registered

        engine2 = BillingEngine()
        engine2.register_meter("M002", "Solar_Prosumer")
        assert engine2.meter_records["M002"].tariff == TOU_RESIDENTIAL_12_LV

    def test_commercial_tariff(self):
        engine = BillingEngine()
        engine.register_meter("M001", "Commercial")
        assert engine.meter_records["M001"].tariff == TOU_SMALL_BUSINESS_22_LV

    def test_ev_charger_tariff(self):
        engine = BillingEngine()
        engine.register_meter("EV001", "EV_Charger")
        assert engine.meter_records["EV001"].tariff == TOU_SMALL_BUSINESS_22_LV

    def test_dc_fast_charger_tariff(self):
        engine = BillingEngine()
        engine.register_meter("DC001", "DC_Fast_Charger")
        assert engine.meter_records["DC001"].tariff == TOU_SMALL_BUSINESS_22_LV
