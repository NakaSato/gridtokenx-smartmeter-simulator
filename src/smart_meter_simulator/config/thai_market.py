"""
Thai Electricity Market Configuration

This module contains all tariff structures, rates, and regulatory parameters
for the Thai residential electricity market as of 2026.

Source: TOU.md - Analysis of the Thai Residential Electricity Market
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class UtilityProvider(Enum):
    """Thai electricity utility providers."""
    MEA = "MEA"  # Metropolitan Electricity Authority (Bangkok metro)
    PEA = "PEA"  # Provincial Electricity Authority (74 provinces)
    EGAT = "EGAT"  # Electricity Generating Authority of Thailand (wholesale)


class TariffCategory(Enum):
    """Residential tariff categories."""
    TYPE_1_1_1 = "1.1.1"  # Small residential (≤150 kWh/month)
    TYPE_1_1_2 = "1.1.2"  # Standard residential (>150 kWh/month)
    TYPE_1_2 = "1.2"  # Time of Use (TOU)
    TYPE_1_3 = "1.3"  # Time of Use with EV


class TOUPeriod(Enum):
    """Time of Use periods for Thai TOU tariffs."""
    ON_PEAK = "on_peak"
    OFF_PEAK_WEEKDAY = "off_peak_weekday"
    OFF_PEAK_WEEKEND = "off_peak_weekend"


# ============================================================================
# Progressive Ladder Tariff Rates (Type 1.1)
# ============================================================================

@dataclass
class LadderTier:
    """Represents a single tier in the progressive ladder tariff."""
    min_kwh: float
    max_kwh: Optional[float]  # None for unlimited top tier
    rate_baht_per_kwh: float


# Type 1.1.1: Small Residential (≤150 kWh/month)
TYPE_1_1_1_TIERS: List[LadderTier] = [
    LadderTier(0, 15, 2.3488),
    LadderTier(16, 25, 2.9882),
    LadderTier(26, 35, 3.2405),
    LadderTier(36, 100, 3.6237),
    LadderTier(101, 150, 3.7171),
]

# Type 1.1.2: Standard Residential (>150 kWh/month)
TYPE_1_1_2_TIERS: List[LadderTier] = [
    LadderTier(0, 150, 3.2484),  # Flat rate for first 150 kWh
    LadderTier(151, 400, 4.2218),
    LadderTier(401, None, 4.4217),  # Top tier (unlimited)
]

# Service charges by tariff type
SERVICE_CHARGES: Dict[TariffCategory, float] = {
    TariffCategory.TYPE_1_1_1: 8.19,  # Baht/month
    TariffCategory.TYPE_1_1_2: 24.62,  # Baht/month
    TariffCategory.TYPE_1_2: 33.29,  # Baht/month
    TariffCategory.TYPE_1_3: 33.29,  # Baht/month
}

# ============================================================================
# Time of Use (TOU) Tariff Rates (Type 1.2/1.3)
# ============================================================================

TOU_RATES: Dict[TOUPeriod, float] = {
    TOUPeriod.ON_PEAK: 5.7982,  # Mon-Fri 09:00-22:00
    TOUPeriod.OFF_PEAK_WEEKDAY: 2.6369,  # Mon-Fri 22:00-09:00
    TOUPeriod.OFF_PEAK_WEEKEND: 2.6369,  # Sat, Sun, Public Holidays (all day)
}

# ============================================================================
# Fuel Adjustment Charge (Ft) Configuration
# ============================================================================

@dataclass
class FtPeriod:
    """Represents a 4-month Ft adjustment period."""
    start_month: int  # 1=Jan, 5=May, 9=Sep
    end_month: int
    ft_rate_baht: float
    base_tariff_baht: float
    notes: str = ""


# Current and historical Ft rates (2025-2026)
FT_PERIODS: List[FtPeriod] = [
    FtPeriod(
        start_month=9, end_month=12,
        ft_rate_baht=0.1572,  # 15.72 satang
        base_tariff_baht=3.78,
        notes="Sep-Dec 2025"
    ),
    FtPeriod(
        start_month=1, end_month=4,
        ft_rate_baht=0.0972,  # 9.72 satang - "New Year Gift"
        base_tariff_baht=3.78,
        notes="Jan-Apr 2026 - LNG price drop"
    ),
    # Projected Ft for May-Aug 2026 (Middle East oil crisis impact)
    FtPeriod(
        start_month=5, end_month=8,
        ft_rate_baht=0.1800,  # Projected increase
        base_tariff_baht=3.78,
        notes="May-Aug 2026 - Projected (oil crisis)"
    ),
]

# Default current Ft (Jan-Apr 2026)
CURRENT_FT_RATE = 0.0972  # Baht/unit
CURRENT_BASE_TARIFF = 3.78  # Baht/unit
CURRENT_TOTAL_TARIFF = 3.8772  # Baht/unit (excl. VAT)

# ============================================================================
# Grid Buy-Back and P2P Trading Parameters
# ============================================================================

# Utility grid rates
GRID_BUYBACK_RATE = 2.20  # Baht/kWh - Rate prosumers sell to grid
GRID_PURCHASE_RATE_HIGH_TIER = 4.4217  # Baht/kWh - Top tier rate

# P2P trading economics
P2P_ARBITRAGE_SPREAD = GRID_PURCHASE_RATE_HIGH_TIER - GRID_BUYBACK_RATE  # 2.2217 Baht/kWh
TYPICAL_P2P_PRICE = 3.30  # Baht/kWh - Midpoint for P2P trades

# ============================================================================
# Third-Party Access (TPA) and Wheeling Charges
# ============================================================================

@dataclass
class TPACharge:
    """Third-Party Access charge components."""
    name: str
    rate_baht_per_kwh: float
    description: str
    is_variable: bool = False


TPA_CHARGES: List[TPACharge] = [
    TPACharge(
        name="Wheeling (T&D)",
        rate_baht_per_kwh=1.1218,
        description="Transmission & Distribution at ≥69 kV"
    ),
    TPACharge(
        name="System Security",
        rate_baht_per_kwh=0.4978,
        description="Ancillary services (spinning reserve, voltage regulation)"
    ),
    TPACharge(
        name="Policy Expense",
        rate_baht_per_kwh=0.1447,
        description="State policy costs (varies with Ft)",
        is_variable=True
    ),
]

# One-time and recurring fees
TPA_CONNECTION_FEE = 10_000  # Baht (one-time)
TPA_ANNUAL_PARTICIPATION_FEE = 120_000  # Baht (for large entities)

# Estimated total wheeling cost for residential P2P
RESIDENTIAL_WHEELING_COST_MIN = 1.50  # Baht/kWh
RESIDENTIAL_WHEELING_COST_MAX = 1.80  # Baht/kWh
RESIDENTIAL_WHEELING_COST_AVG = 1.76  # Baht/kWh

# ============================================================================
# Solar Rooftop Incentives (Royal Decree No. 805)
# ============================================================================

@dataclass
class SolarTaxIncentive:
    """Royal Decree No. 805 solar tax deduction parameters."""
    max_deduction_baht: int = 200_000
    capacity_limit_kwp: int = 10
    start_date: str = "2026-03-03"
    end_date: str = "2028-12-31"
    requires_grid_connection: bool = True
    requires_vat_invoice: bool = True


SOLAR_TAX_INCENTIVE = SolarTaxIncentive()

# ============================================================================
# Solar Installation Cost Benchmarks (2026)
# ============================================================================

@dataclass
class SolarSystemBenchmark:
    """Solar installation cost and performance benchmarks."""
    capacity_kwp: float
    cost_min_baht: float
    cost_max_baht: float
    annual_generation_min_kwh: float
    annual_generation_max_kwh: float
    payback_min_years: float
    payback_max_years: float


SOLAR_BENCHMARKS: List[SolarSystemBenchmark] = [
    SolarSystemBenchmark(
        capacity_kwp=3.0,
        cost_min_baht=90_000,
        cost_max_baht=130_000,
        annual_generation_min_kwh=4_200,
        annual_generation_max_kwh=4_800,
        payback_min_years=5,
        payback_max_years=6
    ),
    SolarSystemBenchmark(
        capacity_kwp=5.0,
        cost_min_baht=150_000,
        cost_max_baht=200_000,
        annual_generation_min_kwh=7_000,
        annual_generation_max_kwh=8_000,
        payback_min_years=4,
        payback_max_years=5
    ),
    SolarSystemBenchmark(
        capacity_kwp=8.0,
        cost_min_baht=240_000,
        cost_max_baht=320_000,
        annual_generation_min_kwh=11_200,
        annual_generation_max_kwh=12_800,
        payback_min_years=4,
        payback_max_years=4
    ),
    SolarSystemBenchmark(
        capacity_kwp=10.0,
        cost_min_baht=300_000,
        cost_max_baht=400_000,
        annual_generation_min_kwh=14_000,
        annual_generation_max_kwh=16_000,
        payback_min_years=3.5,
        payback_max_years=4
    ),
    SolarSystemBenchmark(
        capacity_kwp=10.0,
        cost_min_baht=400_000,  # With 14kWh battery
        cost_max_baht=400_000,
        annual_generation_min_kwh=14_000,
        annual_generation_max_kwh=16_000,
        payback_min_years=5,
        payback_max_years=7
    ),
]

# ============================================================================
# MEA vs PEA Jurisdiction Configuration
# ============================================================================

@dataclass
class UtilityJurisdiction:
    """Utility provider jurisdiction configuration."""
    provider: UtilityProvider
    service_areas: List[str]
    consumer_profile: str
    grid_complexity: str
    net_metering_active: bool
    primary_challenge: str


UTILITY_JURISDICTIONS: Dict[UtilityProvider, UtilityJurisdiction] = {
    UtilityProvider.MEA: UtilityJurisdiction(
        provider=UtilityProvider.MEA,
        service_areas=["Bangkok", "Nonthaburi", "Samut Prakan"],
        consumer_profile="High-density urban, high-rise, commercial",
        grid_complexity="High-voltage underground, dense urban load",
        net_metering_active=True,
        primary_challenge="Peak load management in urban heat islands"
    ),
    UtilityProvider.PEA: UtilityJurisdiction(
        provider=UtilityProvider.PEA,
        service_areas=["All other 74 provinces in Thailand"],
        consumer_profile="Rural, residential, industrial, agricultural",
        grid_complexity="Long-distance transmission, decentralized",
        net_metering_active=True,
        primary_challenge="Grid stability in remote or disaster-hit areas"
    ),
}

# ============================================================================
# Macro-Economic Parameters
# ============================================================================

# LNG price assumptions (2026)
LNG_PRICE_EXPECTED_USD = 11.6  # USD per MMBtu (Jan-Apr 2026)
LNG_PRICE_CRISIS_USD = 12.5  # USD per MMBtu (expected before drop)

# Oil crisis parameters (March 2026)
BRENT_CRUDE_CRISIS_USD = 119.50  # USD per barrel
THAILAND_GAS_DEPENDENCY_PERCENT = 60  # % of electricity from natural gas

# Currency assumption (for calculations)
THB_PER_USD = 35.0  # Approximate exchange rate

# ============================================================================
# Regulatory Constraints
# ============================================================================

# Foreign ownership restrictions (draft regulation)
MAX_FOREIGN_SHAREHOLDING_PERCENT = 49
MAX_FOREIGN_DIRECTORS_RATIO = 0.5

# Green quota for strategic industries
GREEN_QUOTA_MW = 2_000
DATA_CENTER_INVESTMENT_2025_BAHT = 746_000_000_000  # 746 billion Baht

# ============================================================================
# Helper Functions
# ============================================================================

def get_ft_for_month(month: int) -> float:
    """Get the Ft rate for a given month (1-12)."""
    for period in FT_PERIODS:
        if period.start_month <= month <= period.end_month:
            return period.ft_rate_baht
    # Default to current rate if not found
    return CURRENT_FT_RATE


def get_total_tariff(ft_rate: Optional[float] = None) -> float:
    """Calculate total tariff including Ft adjustment."""
    ft = ft_rate if ft_rate is not None else CURRENT_FT_RATE
    return CURRENT_BASE_TARIFF + ft


def get_tou_period(hour: int, is_weekend: bool) -> TOUPeriod:
    """Determine TOU period based on hour and day type."""
    if is_weekend:
        return TOUPeriod.OFF_PEAK_WEEKEND
    
    # Weekday TOU periods
    if 9 <= hour < 22:
        return TOUPeriod.ON_PEAK
    else:
        return TOUPeriod.OFF_PEAK_WEEKDAY


def calculate_p2p_profitability(
    p2p_price: float = TYPICAL_P2P_PRICE,
    wheeling_cost: float = RESIDENTIAL_WHEELING_COST_AVG
) -> Dict[str, float]:
    """
    Calculate P2P trading profitability metrics.
    
    Returns:
        Dictionary with profitability analysis
    """
    # Seller economics
    seller_utility_rate = GRID_BUYBACK_RATE
    seller_p2p_net = p2p_price - wheeling_cost
    seller_gain = seller_p2p_net - seller_utility_rate
    
    # Buyer economics
    buyer_utility_rate = GRID_PURCHASE_RATE_HIGH_TIER
    buyer_p2p_net = p2p_price + wheeling_cost
    buyer_savings = buyer_utility_rate - buyer_p2p_net
    
    # Total welfare gain
    total_welfare_gain = seller_gain + buyer_savings
    
    return {
        "p2p_price_baht_kwh": p2p_price,
        "wheeling_cost_baht_kwh": wheeling_cost,
        "seller_utility_rate_baht_kwh": seller_utility_rate,
        "seller_p2p_net_baht_kwh": seller_p2p_net,
        "seller_gain_baht_kwh": seller_gain,
        "buyer_utility_rate_baht_kwh": buyer_utility_rate,
        "buyer_p2p_total_baht_kwh": buyer_p2p_net,
        "buyer_savings_baht_kwh": buyer_savings,
        "total_welfare_gain_baht_kwh": total_welfare_gain,
        "is_profitable_for_seller": seller_gain > 0,
        "is_profitable_for_buyer": buyer_savings > 0,
        "is_mutually_beneficial": seller_gain > 0 and buyer_savings > 0,
    }
