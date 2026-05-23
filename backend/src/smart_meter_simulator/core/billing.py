"""
Billing Engine for Smart Meter Simulator
Implements Thai TOU tariff calculation, ERC ladder billing, net metering,
and per-meter billing aggregation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================================
# Thai TOU Tariff Constants (2026)
# ============================================================================


@dataclass
class TOUTariff:
    """Time-of-Use tariff for a customer category."""

    name: str
    voltage_kv: str
    on_peak_rate: float  # Baht/kWh
    off_peak_rate: float  # Baht/kWh
    service_charge: float  # Baht/month


# Residential Type 1.2 (< 22 kV)
TOU_RESIDENTIAL_12_LV = TOUTariff(
    name="Residential 1.2",
    voltage_kv="< 22 kV",
    on_peak_rate=5.7982,
    off_peak_rate=2.6369,
    service_charge=33.29,
)

# Small Business Type 2.2 (< 22 kV)
TOU_SMALL_BUSINESS_22_LV = TOUTariff(
    name="Small Business 2.2",
    voltage_kv="< 22 kV",
    on_peak_rate=5.7982,
    off_peak_rate=2.6369,
    service_charge=33.29,
)

# ERC progressive ladder rates (Baht/kWh)
ERC_LADDER_TIERS = [
    (0.0, 150.0, 3.2480),  # Tier 1: 0-150 kWh
    (150.0, 400.0, 4.2218),  # Tier 2: 151-400 kWh
    (400.0, float("inf"), 4.4217),  # Tier 3: 400+ kWh
]

# Additional charges
FT_CHARGE = 0.0972  # Fuel adjustment (Baht/kWh)
VAT_RATE = 0.07  # 7% VAT

# Net metering feed-in rate
NET_METERING_FIT_RATE = 2.20  # Baht/kWh for surplus export


def is_on_peak(dt: datetime) -> bool:
    """
    Check if datetime falls in on-peak period.
    On-Peak: Mon-Fri 09:00-22:00
    Off-Peak: Mon-Fri 22:00-09:00, Weekends, Holidays
    """
    # Weekend = off-peak all day
    if dt.weekday() >= 5:  # Sat=5, Sun=6
        return False

    # Weekday: 09:00-22:00 = on-peak
    return 9 <= dt.hour < 22


def get_tou_rate(dt: datetime, tariff: TOUTariff) -> float:
    """Get the applicable TOU rate for a given datetime."""
    if is_on_peak(dt):
        return tariff.on_peak_rate
    return tariff.off_peak_rate


def calculate_erc_ladder_bill(monthly_kwh: float) -> float:
    """
    Calculate bill using ERC progressive ladder rates.
    Returns total Baht before Ft and VAT.
    """
    total = 0.0
    remaining = monthly_kwh

    for tier_start, tier_end, rate in ERC_LADDER_TIERS:
        if remaining <= 0:
            break
        tier_width = tier_end - tier_start
        usage_in_tier = min(remaining, tier_width)
        total += usage_in_tier * rate
        remaining -= usage_in_tier

    return total


def calculate_tou_bill(
    on_peak_kwh: float,
    off_peak_kwh: float,
    tariff: TOUTariff = TOU_RESIDENTIAL_12_LV,
    include_ft: bool = True,
    include_vat: bool = True,
    service_charge: bool = True,
) -> Dict[str, float]:
    """
    Calculate bill using TOU tariff.
    Returns breakdown of charges.
    """
    energy_charge = (
        on_peak_kwh * tariff.on_peak_rate + off_peak_kwh * tariff.off_peak_rate
    )

    total_kwh = on_peak_kwh + off_peak_kwh
    ft_charge = FT_CHARGE * total_kwh if include_ft else 0.0
    svc_charge = tariff.service_charge if service_charge else 0.0

    subtotal = energy_charge + ft_charge + svc_charge
    vat = subtotal * VAT_RATE if include_vat else 0.0
    total = subtotal + vat

    return {
        "on_peak_kwh": round(on_peak_kwh, 3),
        "off_peak_kwh": round(off_peak_kwh, 3),
        "total_kwh": round(total_kwh, 3),
        "energy_charge_baht": round(energy_charge, 2),
        "ft_charge_baht": round(ft_charge, 2),
        "service_charge_baht": round(svc_charge, 2),
        "vat_baht": round(vat, 2),
        "total_baht": round(total, 2),
    }


def calculate_net_metering_bill(
    consumed_kwh: float,
    exported_kwh: float,
    tariff: TOUTariff = TOU_RESIDENTIAL_12_LV,
    fit_rate: float = NET_METERING_FIT_RATE,
    include_ft: bool = True,
    include_vat: bool = True,
) -> Dict[str, float]:
    """
    Calculate net metering bill: consumed at retail rate, exported at FiT rate.
    Net billing = (consumed × retail) - (exported × FiT)
    """
    consumed_charge = (
        consumed_kwh * tariff.on_peak_rate
    )  # Simplified: use on-peak as avg
    export_credit = exported_kwh * fit_rate

    ft_charge = FT_CHARGE * consumed_kwh if include_ft else 0.0
    subtotal = consumed_charge + ft_charge - export_credit
    vat = max(0.0, subtotal * VAT_RATE) if include_vat else 0.0
    total = max(0.0, subtotal + vat)  # Cannot go negative (credit carried forward)

    return {
        "consumed_kwh": round(consumed_kwh, 3),
        "exported_kwh": round(exported_kwh, 3),
        "consumed_charge_baht": round(consumed_charge, 2),
        "export_credit_baht": round(export_credit, 2),
        "ft_charge_baht": round(ft_charge, 2),
        "vat_baht": round(vat, 2),
        "net_baht": round(total, 2),
    }


# ============================================================================
# Per-Meter Billing Aggregator
# ============================================================================


@dataclass
class MeterBillingRecord:
    """Accumulated billing data for a single meter."""

    meter_id: str
    meter_type: str
    tariff: TOUTariff

    # Accumulated kWh
    on_peak_consumed: float = 0.0
    off_peak_consumed: float = 0.0
    on_peak_generated: float = 0.0
    off_peak_generated: float = 0.0
    exported_to_grid: float = 0.0

    # Period
    billing_start: Optional[datetime] = None
    billing_end: Optional[datetime] = None

    # Computed
    last_bill: Dict = field(default_factory=dict)

    @property
    def total_consumed_kwh(self) -> float:
        return self.on_peak_consumed + self.off_peak_consumed

    @property
    def total_generated_kwh(self) -> float:
        return self.on_peak_generated + self.off_peak_generated


class BillingEngine:
    """
    Manages per-meter billing with Thai TOU tariffs, ERC ladder,
    net metering, and aggregation.
    """

    def __init__(self):
        self.meter_records: Dict[str, MeterBillingRecord] = {}
        self.total_billed_baht = 0.0
        self.meters_billed_count = 0

        # Default tariff mapping by meter type
        self._tariff_map = {
            "Residential": TOU_RESIDENTIAL_12_LV,
            "Solar_Prosumer": TOU_RESIDENTIAL_12_LV,
            "Hybrid_Prosumer": TOU_RESIDENTIAL_12_LV,
            "Grid_Consumer": TOU_RESIDENTIAL_12_LV,
            "Commercial": TOU_SMALL_BUSINESS_22_LV,
            "EV_Charger": TOU_SMALL_BUSINESS_22_LV,
            "DC_Fast_Charger": TOU_SMALL_BUSINESS_22_LV,
            "Battery_Storage": TOU_SMALL_BUSINESS_22_LV,
        }

    def register_meter(
        self,
        meter_id: str,
        meter_type: str,
        tariff: Optional[TOUTariff] = None,
    ) -> MeterBillingRecord:
        """Register a meter for billing."""
        t = tariff or self._tariff_map.get(meter_type, TOU_RESIDENTIAL_12_LV)
        record = MeterBillingRecord(
            meter_id=meter_id,
            meter_type=meter_type,
            tariff=t,
            billing_start=datetime.now(timezone.utc),
        )
        self.meter_records[meter_id] = record
        logger.debug(f"Registered meter {meter_id} ({meter_type}) for billing")
        return record

    def consume_reading(
        self,
        meter_id: str,
        energy_consumed_kwh: float,
        energy_generated_kwh: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Accumulate a reading into the meter's billing record.
        Handles TOU period classification and net metering tracking.
        """
        if meter_id not in self.meter_records:
            # Auto-register on first reading
            self.register_meter(meter_id, "Unknown")

        record = self.meter_records[meter_id]
        ts = timestamp or datetime.now(timezone.utc)
        record.billing_end = ts

        peak = is_on_peak(ts)

        if peak:
            record.on_peak_consumed += energy_consumed_kwh
            record.on_peak_generated += energy_generated_kwh
        else:
            record.off_peak_consumed += energy_consumed_kwh
            record.off_peak_generated += energy_generated_kwh

        # Track exported energy (surplus = generated - consumed)
        surplus = max(0.0, energy_generated_kwh - energy_consumed_kwh)
        record.exported_to_grid += surplus

    def calculate_meter_bill(
        self,
        meter_id: str,
        method: str = "tou",
    ) -> Dict[str, float]:
        """
        Calculate bill for a single meter.

        Methods:
        - 'tou': TOU tariff with Ft + VAT
        - 'erc': ERC progressive ladder
        - 'net_metering': Net billing with FiT credit
        """
        if meter_id not in self.meter_records:
            return {"error": f"Meter {meter_id} not registered"}

        record = self.meter_records[meter_id]

        if method == "tou":
            bill = calculate_tou_bill(
                on_peak_kwh=record.on_peak_consumed,
                off_peak_kwh=record.off_peak_consumed,
                tariff=record.tariff,
            )
        elif method == "erc":
            base = calculate_erc_ladder_bill(record.total_consumed_kwh)
            ft = FT_CHARGE * record.total_consumed_kwh
            svc = record.tariff.service_charge
            subtotal = base + ft + svc
            vat = subtotal * VAT_RATE
            bill = {
                "total_kwh": round(record.total_consumed_kwh, 3),
                "ladder_charge_baht": round(base, 2),
                "ft_charge_baht": round(ft, 2),
                "service_charge_baht": round(svc, 2),
                "vat_baht": round(vat, 2),
                "total_baht": round(subtotal + vat, 2),
            }
        elif method == "net_metering":
            bill = calculate_net_metering_bill(
                consumed_kwh=record.total_consumed_kwh,
                exported_kwh=record.exported_to_grid,
                tariff=record.tariff,
            )
        else:
            return {"error": f"Unknown billing method: {method}"}

        record.last_bill = bill
        return bill

    def calculate_all_bills(
        self,
        method: str = "tou",
    ) -> Dict[str, Dict]:
        """Calculate bills for all registered meters."""
        results = {}
        self.total_billed_baht = 0.0
        self.meters_billed_count = 0

        for meter_id in self.meter_records:
            bill = self.calculate_meter_bill(meter_id, method)
            results[meter_id] = bill
            if "total_baht" in bill:
                self.total_billed_baht += bill["total_baht"]
                self.meters_billed_count += 1

        return results

    def reset_billing_period(self) -> None:
        """Reset all meters for a new billing period."""
        now = datetime.now(timezone.utc)
        for record in self.meter_records.values():
            record.on_peak_consumed = 0.0
            record.off_peak_consumed = 0.0
            record.on_peak_generated = 0.0
            record.off_peak_generated = 0.0
            record.exported_to_grid = 0.0
            record.billing_start = now
            record.billing_end = None
            record.last_bill = {}

        self.total_billed_baht = 0.0
        self.meters_billed_count = 0
        logger.info("Billing period reset")

    def get_summary(self) -> Dict:
        """Get billing summary across all meters."""
        return {
            "total_billed_thb": round(self.total_billed_baht, 2),
            "total_meters_billed": self.meters_billed_count,
            "period": (
                f"{self.meter_records[next(iter(self.meter_records))].billing_start.isoformat()}"
                f" - "
                f"{self.meter_records[next(iter(self.meter_records))].billing_end.isoformat()}"
                if self.meter_records
                and any(r.billing_end for r in self.meter_records.values())
                else ""
            ),
        }

    def get_meter_detail(self, meter_id: str) -> Optional[Dict]:
        """Get detailed billing info for a single meter."""
        if meter_id not in self.meter_records:
            return None

        record = self.meter_records[meter_id]
        return {
            "meter_id": meter_id,
            "meter_type": record.meter_type,
            "tariff": record.tariff.name,
            "on_peak_consumed_kwh": round(record.on_peak_consumed, 3),
            "off_peak_consumed_kwh": round(record.off_peak_consumed, 3),
            "total_consumed_kwh": round(record.total_consumed_kwh, 3),
            "total_generated_kwh": round(record.total_generated_kwh, 3),
            "exported_to_grid_kwh": round(record.exported_to_grid, 3),
            "last_bill": record.last_bill,
            "billing_start": record.billing_start.isoformat()
            if record.billing_start
            else None,
            "billing_end": record.billing_end.isoformat()
            if record.billing_end
            else None,
        }
