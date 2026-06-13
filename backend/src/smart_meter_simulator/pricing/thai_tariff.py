"""Thai retail electricity tariff rate tables and bill computation.

Models the Metropolitan Electricity Authority (MEA) / Provincial Electricity
Authority (PEA) retail tariff. The structured **energy charge** here is the base
tariff schedule effective Nov 2018 (unchanged base block rates, in baht/kWh).
On top of the energy charge a retail bill carries three more components:

  * **Ft (fuel adjustment charge)** — a flat satang/kWh surcharge on *all* energy,
    revised by the ERC roughly quarterly. Volatile, so it is config-driven
    (``TARIFF_FT_PER_KWH``) rather than baked into the rate tables. The default
    here (0.3672 ฿/kWh) is the Jan–Apr 2025 retail value.
  * **Service charge** — a fixed baht/month charge that depends on tariff class.
  * **VAT** — 7% on (energy + Ft + service), config-driven (``TARIFF_VAT_RATE``).

Tariff classes modelled (all low-voltage, <12 kV retail):

  * ``residential_small``  — type 1.1.1, homes consuming ≤150 kWh/month (tiered).
  * ``residential_normal`` — type 1.1.2, homes consuming >150 kWh/month (tiered).
  * ``residential_tou``    — type 1.2.1, residential Time-of-Use (peak/off-peak).
  * ``small_business``     — type 2.1.2, small general service, normal (tiered).
  * ``small_business_tou`` — type 2.2.2, small general service, TOU.

TOU period definition (MEA/PEA):
  * **Peak**     — Mon–Fri 09:00–22:00, excluding national holidays.
  * **Off-peak** — Mon–Fri 22:00–09:00, plus all day Sat/Sun and national holidays.

All amounts are baht (THB). Energy/Ft rates carry 4 decimals (satang precision);
money totals are rounded to 2 decimals (1 satang).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Union

THB = float  # baht

# The MEA/PEA TOU window is defined in Thai local time (Indochina Time). Thailand
# observes no DST, so a fixed +07:00 offset is exact year-round.
THAI_TZ = timezone(timedelta(hours=7))


class TariffClass(str, Enum):
    """Retail tariff class. ``residential_auto`` selects small vs normal by usage."""

    RESIDENTIAL_AUTO = "residential_auto"
    RESIDENTIAL_SMALL = "residential_small"
    RESIDENTIAL_NORMAL = "residential_normal"
    RESIDENTIAL_TOU = "residential_tou"
    SMALL_BUSINESS = "small_business"
    SMALL_BUSINESS_TOU = "small_business_tou"


@dataclass(frozen=True)
class Tier:
    """One inclining block: ``rate`` applies to kWh in ``(prev_ceiling, up_to_kwh]``.

    ``up_to_kwh = None`` marks the unbounded top block.
    """

    up_to_kwh: Optional[float]
    rate: THB


@dataclass(frozen=True)
class TieredRate:
    """Progressive (inclining-block) energy charge plus a fixed service charge."""

    tiers: tuple[Tier, ...]
    service_charge: THB


@dataclass(frozen=True)
class TOURate:
    """Time-of-Use energy charge (flat peak / off-peak) plus a service charge."""

    peak: THB
    off_peak: THB
    service_charge: THB


# --- MEA base tariff (energy charge, ฿/kWh, Nov 2018 schedule) ---------------
# Source: MEA retail tariff schedule (https://www.mea.or.th). Ft excluded.

RESIDENTIAL_SMALL = TieredRate(  # type 1.1.1 — ≤150 kWh/month
    tiers=(
        Tier(15, 2.3488),
        Tier(25, 2.9882),
        Tier(35, 3.2405),
        Tier(100, 3.6237),
        Tier(150, 3.7171),
        Tier(400, 4.2218),
        Tier(None, 4.4217),
    ),
    service_charge=8.19,
)

RESIDENTIAL_NORMAL = TieredRate(  # type 1.1.2 — >150 kWh/month
    tiers=(
        Tier(150, 3.2484),
        Tier(400, 4.2218),
        Tier(None, 4.4217),
    ),
    service_charge=24.62,
)

RESIDENTIAL_TOU = TOURate(  # type 1.2.1 — residential TOU, <12 kV
    peak=5.7982,
    off_peak=2.6369,
    service_charge=24.62,
)

SMALL_BUSINESS = TieredRate(  # type 2.1.2 — small general service, normal, <12 kV
    tiers=(
        Tier(150, 3.2484),
        Tier(400, 4.2218),
        Tier(None, 4.4217),
    ),
    service_charge=33.29,
)

SMALL_BUSINESS_TOU = TOURate(  # type 2.2.2 — small general service TOU, <12 kV
    peak=5.7982,
    off_peak=2.6369,
    service_charge=33.29,
)

TARIFFS: dict[TariffClass, Union[TieredRate, TOURate]] = {
    TariffClass.RESIDENTIAL_SMALL: RESIDENTIAL_SMALL,
    TariffClass.RESIDENTIAL_NORMAL: RESIDENTIAL_NORMAL,
    TariffClass.RESIDENTIAL_TOU: RESIDENTIAL_TOU,
    TariffClass.SMALL_BUSINESS: SMALL_BUSINESS,
    TariffClass.SMALL_BUSINESS_TOU: SMALL_BUSINESS_TOU,
}

# Defaults — overridable per-call (and from config at the router layer).
DEFAULT_FT_PER_KWH: THB = 0.3672  # Jan–Apr 2025 retail Ft (satang/kWh / 100)
DEFAULT_VAT_RATE: float = 0.07

# Thailand operates **net billing** (not net metering): grid import is billed at
# the retail tariff above, while exported rooftop-PV surplus is bought back
# *separately* at a low flat rate — it is NOT deducted from import units before
# the tariff. 2.20 ฿/kWh is the residential rooftop scheme rate (systems ≤10 kW,
# PPA up to 10 yr). The buy-back credit carries no consumer VAT; it is netted off
# the VAT-inclusive import bill. The original 90 MW program quota was met in 2024,
# so new entrants may get 0 — set the rate to 0.0 to model that.
DEFAULT_EXPORT_PER_KWH: THB = 2.20

# Residential small-tariff eligibility ceiling (kWh/month).
RESIDENTIAL_SMALL_CEILING_KWH = 150.0


@dataclass
class BillLine:
    """One itemised line of the bill."""

    label: str
    kwh: float
    rate: THB
    amount: THB


@dataclass
class Bill:
    """An itemised electricity bill for one billing period (default 1 month)."""

    tariff: TariffClass
    kwh_total: float
    energy_charge: THB
    ft_rate: THB
    ft_charge: THB
    service_charge: THB
    subtotal: THB  # energy + ft + service
    vat_rate: float
    vat: THB
    total: THB  # import bill, VAT-inclusive (before any solar export credit)
    lines: list[BillLine] = field(default_factory=list)
    peak_kwh: Optional[float] = None
    off_peak_kwh: Optional[float] = None
    months: int = 1
    # Net-billing solar export buy-back (PV surplus sold to MEA/PEA). Credit is
    # netted off `total` to give `net_total`; carries no consumer VAT.
    export_kwh: float = 0.0
    export_rate: THB = 0.0
    export_credit: THB = 0.0
    net_total: THB = 0.0

    @property
    def average_rate_per_kwh(self) -> THB:
        """All-in import ฿/kWh (total / import kWh). 0 when no energy was billed."""
        return round(self.total / self.kwh_total, 4) if self.kwh_total > 0 else 0.0


def select_residential_class(kwh_per_month: float) -> TariffClass:
    """Pick the residential tier MEA applies: small ≤150 kWh/month, else normal."""
    if kwh_per_month <= RESIDENTIAL_SMALL_CEILING_KWH:
        return TariffClass.RESIDENTIAL_SMALL
    return TariffClass.RESIDENTIAL_NORMAL


def is_peak_period(dt: datetime, holidays: Optional[set[date]] = None) -> bool:
    """True if ``dt`` is in the TOU peak window: Mon–Fri 09:00–22:00, non-holiday.

    The window is Thai local time (ICT). Sim/meter timestamps are UTC (a naive
    ``dt`` is treated as UTC), so convert to ``THAI_TZ`` before bucketing — else
    the weekday/hour test is skewed 7 hours and peak/off-peak energy is mislabelled.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(THAI_TZ)
    if local.weekday() >= 5:  # Sat/Sun
        return False
    if holidays and local.date() in holidays:
        return False
    return 9 <= local.hour < 22


def split_tou_energy(
    samples: list[tuple[datetime, float]],
    holidays: Optional[set[date]] = None,
) -> tuple[float, float]:
    """Bucket ``(timestamp, kwh)`` samples into ``(peak_kwh, off_peak_kwh)``."""
    peak = 0.0
    off_peak = 0.0
    for ts, kwh in samples:
        if is_peak_period(ts, holidays):
            peak += kwh
        else:
            off_peak += kwh
    return peak, off_peak


def _tiered_energy_charge(kwh: float, rate: TieredRate) -> tuple[THB, list[BillLine]]:
    """Apply an inclining-block schedule to ``kwh``; return (amount, itemised lines)."""
    lines: list[BillLine] = []
    total = 0.0
    remaining = max(kwh, 0.0)
    prev_ceiling = 0.0
    for tier in rate.tiers:
        if remaining <= 0:
            break
        if tier.up_to_kwh is None:
            block_kwh = remaining
        else:
            block_kwh = min(remaining, tier.up_to_kwh - prev_ceiling)
            prev_ceiling = tier.up_to_kwh
        if block_kwh <= 0:
            continue
        amount = block_kwh * tier.rate
        total += amount
        ceiling_label = "+" if tier.up_to_kwh is None else f"≤{tier.up_to_kwh:g}"
        lines.append(
            BillLine(
                label=f"Energy {ceiling_label} kWh",
                kwh=round(block_kwh, 4),
                rate=tier.rate,
                amount=round(amount, 2),
            )
        )
        remaining -= block_kwh
    return total, lines


def _tou_energy_charge(
    peak_kwh: float, off_peak_kwh: float, rate: TOURate
) -> tuple[THB, list[BillLine]]:
    """Apply flat peak/off-peak rates; return (amount, itemised lines)."""
    peak_amount = max(peak_kwh, 0.0) * rate.peak
    off_amount = max(off_peak_kwh, 0.0) * rate.off_peak
    lines = [
        BillLine(
            label="Energy peak",
            kwh=round(max(peak_kwh, 0.0), 4),
            rate=rate.peak,
            amount=round(peak_amount, 2),
        ),
        BillLine(
            label="Energy off-peak",
            kwh=round(max(off_peak_kwh, 0.0), 4),
            rate=rate.off_peak,
            amount=round(off_amount, 2),
        ),
    ]
    return peak_amount + off_amount, lines


def compute_bill(
    tariff: TariffClass,
    *,
    kwh: Optional[float] = None,
    peak_kwh: Optional[float] = None,
    off_peak_kwh: Optional[float] = None,
    ft_per_kwh: THB = DEFAULT_FT_PER_KWH,
    vat_rate: float = DEFAULT_VAT_RATE,
    months: int = 1,
    export_kwh: float = 0.0,
    export_per_kwh: THB = DEFAULT_EXPORT_PER_KWH,
) -> Bill:
    """Compute an itemised Thai retail electricity bill.

    Tiered tariffs (residential/small-business normal) need ``kwh``. TOU tariffs
    need ``peak_kwh`` and ``off_peak_kwh`` (if only ``kwh`` is given for a TOU
    tariff it is treated as all off-peak). ``residential_auto`` resolves to small
    or normal by ``kwh``. ``months`` multiplies the fixed service charge (energy
    and Ft scale with the supplied kWh, which already span the period).

    ``kwh``/peak/off here are the **grid import** (deficit). Under Thailand's net
    billing scheme, exported PV surplus (``export_kwh``) is bought back separately
    at ``export_per_kwh`` (flat, no VAT) and netted off the import bill into
    ``net_total`` — it is NOT subtracted from import units before the tariff.

    Raises ``ValueError`` on an unknown tariff or missing required energy input.
    """
    if export_kwh < 0:
        raise ValueError("export_kwh must be >= 0")
    if months < 1:
        raise ValueError("months must be >= 1")

    if tariff == TariffClass.RESIDENTIAL_AUTO:
        if kwh is None:
            raise ValueError("residential_auto requires kwh")
        tariff = select_residential_class(kwh / months)

    rate = TARIFFS.get(tariff)
    if rate is None:
        raise ValueError(f"unknown tariff: {tariff}")

    if isinstance(rate, TOURate):
        if peak_kwh is None and off_peak_kwh is None:
            if kwh is None:
                raise ValueError(f"{tariff.value} requires peak_kwh/off_peak_kwh")
            peak_kwh, off_peak_kwh = 0.0, kwh
        peak_kwh = peak_kwh or 0.0
        off_peak_kwh = off_peak_kwh or 0.0
        kwh_total = peak_kwh + off_peak_kwh
        energy_charge, lines = _tou_energy_charge(peak_kwh, off_peak_kwh, rate)
        out_peak: Optional[float] = round(peak_kwh, 4)
        out_off_peak: Optional[float] = round(off_peak_kwh, 4)
    else:
        if kwh is None:
            raise ValueError(f"{tariff.value} requires kwh")
        kwh_total = kwh
        # Inclining-block tiers are defined per billing month. Bill the per-month
        # average through the blocks, then scale by months — running a multi-month
        # total straight through the blocks would wrongly push energy into the top
        # tiers and overstate the charge. (TOU/Ft are flat, so they stay linear.)
        monthly_charge, lines = _tiered_energy_charge(kwh / months, rate)
        energy_charge = monthly_charge * months
        if months != 1:
            for line in lines:
                line.kwh = round(line.kwh * months, 4)
                line.amount = round(line.amount * months, 2)
        out_peak = None
        out_off_peak = None

    ft_charge = kwh_total * ft_per_kwh
    service_charge = rate.service_charge * months
    subtotal = energy_charge + ft_charge + service_charge
    vat = subtotal * vat_rate
    total = subtotal + vat

    lines.append(
        BillLine(
            label="Ft (fuel adjustment)",
            kwh=round(kwh_total, 4),
            rate=ft_per_kwh,
            amount=round(ft_charge, 2),
        )
    )
    lines.append(
        BillLine(
            label="Service charge",
            kwh=0.0,
            rate=rate.service_charge,
            amount=round(service_charge, 2),
        )
    )

    export_credit = max(export_kwh, 0.0) * export_per_kwh
    net_total = total - export_credit
    if export_kwh > 0:
        lines.append(
            BillLine(
                label="Solar export credit (net billing)",
                kwh=round(export_kwh, 4),
                rate=export_per_kwh,
                amount=-round(export_credit, 2),
            )
        )

    return Bill(
        tariff=tariff,
        kwh_total=round(kwh_total, 4),
        energy_charge=round(energy_charge, 2),
        ft_rate=ft_per_kwh,
        ft_charge=round(ft_charge, 2),
        service_charge=round(service_charge, 2),
        subtotal=round(subtotal, 2),
        vat_rate=vat_rate,
        vat=round(vat, 2),
        total=round(total, 2),
        lines=lines,
        peak_kwh=out_peak,
        off_peak_kwh=out_off_peak,
        months=months,
        export_kwh=round(max(export_kwh, 0.0), 4),
        export_rate=export_per_kwh,
        export_credit=round(export_credit, 2),
        net_total=round(net_total, 2),
    )
