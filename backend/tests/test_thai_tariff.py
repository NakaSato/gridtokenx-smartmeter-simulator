"""Thai retail tariff bill-computation tests."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from smart_meter_simulator.pricing import (
    TariffClass,
    compute_bill,
    is_peak_period,
    select_residential_class,
    split_tou_energy,
)


def test_residential_small_single_tier():
    # 10 kWh stays inside the first block (≤15 @ 2.3488).
    bill = compute_bill(
        TariffClass.RESIDENTIAL_SMALL, kwh=10, ft_per_kwh=0.0, vat_rate=0.0
    )
    assert bill.energy_charge == pytest.approx(23.49, abs=0.01)  # 10 * 2.3488
    assert bill.service_charge == 8.19
    assert bill.total == pytest.approx(23.49 + 8.19, abs=0.01)


def test_residential_small_crosses_blocks():
    # 30 kWh: 15@2.3488 + 10@2.9882 + 5@3.2405
    expected = 15 * 2.3488 + 10 * 2.9882 + 5 * 3.2405
    bill = compute_bill(
        TariffClass.RESIDENTIAL_SMALL, kwh=30, ft_per_kwh=0.0, vat_rate=0.0
    )
    assert bill.energy_charge == pytest.approx(round(expected, 2), abs=0.01)


def test_residential_normal_tiers_and_ft_vat():
    # 300 kWh normal: 150@3.2484 + 150@4.2218
    energy = 150 * 3.2484 + 150 * 4.2218
    ft = 300 * 0.3672
    subtotal = energy + ft + 24.62
    total = subtotal * 1.07
    bill = compute_bill(
        TariffClass.RESIDENTIAL_NORMAL, kwh=300, ft_per_kwh=0.3672, vat_rate=0.07
    )
    assert bill.energy_charge == pytest.approx(round(energy, 2), abs=0.01)
    assert bill.ft_charge == pytest.approx(round(ft, 2), abs=0.01)
    assert bill.total == pytest.approx(round(total, 2), abs=0.02)
    assert 4.0 < bill.average_rate_per_kwh < 5.0  # sanity: ~4.5 ฿/kWh


def test_residential_auto_selects_small_then_normal():
    assert select_residential_class(150) == TariffClass.RESIDENTIAL_SMALL
    assert select_residential_class(151) == TariffClass.RESIDENTIAL_NORMAL
    small = compute_bill(TariffClass.RESIDENTIAL_AUTO, kwh=100)
    normal = compute_bill(TariffClass.RESIDENTIAL_AUTO, kwh=300)
    assert small.tariff == TariffClass.RESIDENTIAL_SMALL
    assert normal.tariff == TariffClass.RESIDENTIAL_NORMAL


def test_tou_bill_peak_offpeak():
    # 200 peak @5.7982 + 300 off @2.6369
    energy = 200 * 5.7982 + 300 * 2.6369
    bill = compute_bill(
        TariffClass.RESIDENTIAL_TOU,
        peak_kwh=200,
        off_peak_kwh=300,
        ft_per_kwh=0.0,
        vat_rate=0.0,
    )
    assert bill.energy_charge == pytest.approx(round(energy, 2), abs=0.01)
    assert bill.kwh_total == 500
    assert bill.peak_kwh == 200
    assert bill.off_peak_kwh == 300


def test_tou_kwh_only_treated_as_offpeak():
    bill = compute_bill(
        TariffClass.RESIDENTIAL_TOU, kwh=100, ft_per_kwh=0.0, vat_rate=0.0
    )
    assert bill.peak_kwh == 0
    assert bill.off_peak_kwh == 100
    assert bill.energy_charge == pytest.approx(100 * 2.6369, abs=0.01)


def test_small_business_service_charge():
    bill = compute_bill(TariffClass.SMALL_BUSINESS, kwh=100)
    assert bill.service_charge == 33.29


def test_small_business_tou_service_charge():
    # MEA type 2.2.2 (<12 kV) service charge is 33.29 — same as 2.1.2.
    bill = compute_bill(TariffClass.SMALL_BUSINESS_TOU, peak_kwh=100, off_peak_kwh=200)
    assert bill.service_charge == 33.29


def test_months_tier_per_month_and_scale_service():
    # `kwh` is the total spanning `months`; inclining-block tiers are per-month,
    # so 300 kWh over 3 months bills as 3 x (100 kWh, 1 month) for energy — not as
    # 300 kWh run through the blocks once.
    per_month = compute_bill(
        TariffClass.RESIDENTIAL_NORMAL, kwh=100, ft_per_kwh=0.3672, vat_rate=0.0
    )
    three = compute_bill(
        TariffClass.RESIDENTIAL_NORMAL,
        kwh=300,
        ft_per_kwh=0.3672,
        vat_rate=0.0,
        months=3,
    )
    # energy = 3 x the per-month tiered charge; service charge x3.
    assert three.energy_charge == pytest.approx(per_month.energy_charge * 3, abs=0.01)
    assert three.service_charge == pytest.approx(per_month.service_charge * 3, abs=0.01)
    # Ft is flat per kWh, so it scales with the total kWh either way.
    assert three.ft_charge == pytest.approx(300 * 0.3672, abs=0.01)


def test_is_peak_period():
    # Wed 2026-06-10 14:00 — peak.
    assert is_peak_period(datetime(2026, 6, 10, 14, 0))
    # Wed 23:00 — off-peak (after 22:00).
    assert not is_peak_period(datetime(2026, 6, 10, 23, 0))
    # Sat — off-peak all day.
    assert not is_peak_period(datetime(2026, 6, 13, 14, 0))
    # Holiday weekday — off-peak.
    assert not is_peak_period(
        datetime(2026, 6, 10, 14, 0), holidays={date(2026, 6, 10)}
    )


def test_split_tou_energy():
    samples = [
        (datetime(2026, 6, 10, 14, 0), 5.0),  # Wed peak
        (datetime(2026, 6, 10, 23, 0), 3.0),  # Wed off-peak
        (datetime(2026, 6, 13, 10, 0), 2.0),  # Sat off-peak
    ]
    peak, off = split_tou_energy(samples)
    assert peak == 5.0
    assert off == 5.0


def test_unknown_inputs_raise():
    with pytest.raises(ValueError):
        compute_bill(TariffClass.RESIDENTIAL_NORMAL)  # no kwh
    with pytest.raises(ValueError):
        compute_bill(TariffClass.RESIDENTIAL_AUTO, peak_kwh=10)  # auto needs kwh
    with pytest.raises(ValueError):
        compute_bill(TariffClass.RESIDENTIAL_NORMAL, kwh=100, months=0)


def test_net_billing_export_credit():
    # 300 kWh import, 100 kWh export @ 2.20 buy-back.
    bill = compute_bill(
        TariffClass.RESIDENTIAL_NORMAL,
        kwh=300,
        export_kwh=100,
        export_per_kwh=2.20,
    )
    assert bill.export_kwh == 100
    assert bill.export_rate == 2.20
    assert bill.export_credit == pytest.approx(220.0, abs=0.01)
    # net_total = VAT-inclusive import total minus the (un-VATed) export credit.
    assert bill.net_total == pytest.approx(bill.total - 220.0, abs=0.01)
    assert bill.net_total < bill.total
    # credit appears as a negative bill line.
    credit_line = next(line for line in bill.lines if "export" in line.label.lower())
    assert credit_line.amount == pytest.approx(-220.0, abs=0.01)


def test_no_export_no_credit_line():
    bill = compute_bill(TariffClass.RESIDENTIAL_NORMAL, kwh=300)
    assert bill.export_kwh == 0
    assert bill.export_credit == 0.0
    assert bill.net_total == bill.total
    assert not any("export" in line.label.lower() for line in bill.lines)


def test_export_does_not_offset_import_units():
    # Net billing, NOT net metering: export must not reduce the energy charge.
    no_export = compute_bill(TariffClass.RESIDENTIAL_NORMAL, kwh=300)
    with_export = compute_bill(
        TariffClass.RESIDENTIAL_NORMAL, kwh=300, export_kwh=300, export_per_kwh=2.20
    )
    assert with_export.energy_charge == no_export.energy_charge
    assert with_export.total == no_export.total  # import bill unchanged
    assert with_export.net_total < no_export.net_total  # only net payable drops


def test_negative_export_raises():
    with pytest.raises(ValueError):
        compute_bill(TariffClass.RESIDENTIAL_NORMAL, kwh=100, export_kwh=-5)


def test_zero_energy_bill():
    bill = compute_bill(TariffClass.RESIDENTIAL_NORMAL, kwh=0)
    assert bill.energy_charge == 0.0
    assert bill.average_rate_per_kwh == 0.0
    assert bill.service_charge == 24.62
    assert bill.total > 0  # service charge + vat still apply
