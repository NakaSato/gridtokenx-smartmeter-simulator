"""
Price Provider Module
Provides utility rates, P2P market clearing prices, and price comparison.

Services:
- TOUTariffPriceProvider: Thai TOU tariff pricing (PEA/MEA)
- P2PMarketPriceProvider: Dynamic P2P market clearing price
- PriceComparisonService: Compare utility vs P2P pricing
- PriceHistoryManager: Store and query historical prices
- PriceStreamer: WebSocket real-time price streaming
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

from .billing import (
    FT_CHARGE,
    VAT_RATE,
    TOUTariff,
    TOU_RESIDENTIAL_12_LV,
    TOU_SMALL_BUSINESS_22_LV,
    is_on_peak,
    get_tou_rate,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

# Thai wheeling charges (Baht/kWh) — based on ERC/PEA regulations
WHEELING_CHARGE_RESIDENTIAL = 0.35
WHEELING_CHARGE_COMMERCIAL = 0.45

# Grid loss factor (%)
GRID_LOSS_FACTOR = 0.08  # 8% transmission/distribution loss

# P2P market parameters
P2P_MIN_PRICE = 1.50   # Minimum P2P price (Baht/kWh)
P2P_MAX_PRICE = 6.00   # Maximum P2P price (Baht/kWh)
P2P_BASE_PRICE = 3.50  # Baseline P2P price


# ============================================================================
# Utility Provider Enums
# ============================================================================

class UtilityProvider(str, Enum):
    PEA = "PEA"   # Provincial Electricity Authority
    MEA = "MEA"   # Metropolitan Electricity Authority


class TariffCategory(str, Enum):
    RESIDENTIAL_12 = "residential_1.2"
    SMALL_BUSINESS_22 = "small_business_2.2"
    MEDIUM_BUSINESS_3 = "medium_business_3"
    LARGE_INDUSTRIAL = "large_industrial_4"


# Tariff mapping
TARIFF_MAP = {
    TariffCategory.RESIDENTIAL_12: TOU_RESIDENTIAL_12_LV,
    TariffCategory.SMALL_BUSINESS_22: TOU_SMALL_BUSINESS_22_LV,
    TariffCategory.MEDIUM_BUSINESS_3: TOU_SMALL_BUSINESS_22_LV,
    TariffCategory.LARGE_INDUSTRIAL: TOU_SMALL_BUSINESS_22_LV,
}


# ============================================================================
# Price Data Models
# ============================================================================

@dataclass
class UtilityPriceBreakdown:
    """Detailed utility price breakdown."""
    provider: str
    tariff_category: str
    tariff_type: str
    energy_charge_baht: float
    ft_charge_baht: float
    service_charge_baht: float
    total_before_vat_baht: float
    vat_baht: float
    total_amount_baht: float
    average_rate_baht_kwh: float
    ft_rate_baht_kwh: float

    def to_dict(self) -> Dict:
        return {
            "provider": self.provider,
            "tariff_category": self.tariff_category,
            "tariff_type": self.tariff_type,
            "energy_charge_baht": round(self.energy_charge_baht, 2),
            "ft_charge_baht": round(self.ft_charge_baht, 2),
            "service_charge_baht": round(self.service_charge_baht, 2),
            "total_before_vat_baht": round(self.total_before_vat_baht, 2),
            "vat_baht": round(self.vat_baht, 2),
            "total_amount_baht": round(self.total_amount_baht, 2),
            "average_rate_baht_kwh": round(self.average_rate_baht_kwh, 3),
            "ft_rate_baht_kwh": round(self.ft_rate_baht_kwh, 3),
        }


@dataclass
class P2PPriceBreakdown:
    """Detailed P2P price breakdown."""
    market_clearing_price_baht_kwh: float
    wheeling_cost_baht_kwh: float
    buyer_total_baht_kwh: float
    seller_net_baht_kwh: float
    energy_cost_baht: float
    wheeling_charge_baht: float
    buyer_total_cost_baht: float
    seller_net_revenue_baht: float
    market_sentiment: str  # "buyer_favorable", "seller_favorable", "balanced"

    def to_dict(self) -> Dict:
        return {
            "market_clearing_price_baht_kwh": round(self.market_clearing_price_baht_kwh, 4),
            "wheeling_cost_baht_kwh": round(self.wheeling_cost_baht_kwh, 4),
            "buyer_total_baht_kwh": round(self.buyer_total_baht_kwh, 4),
            "seller_net_baht_kwh": round(self.seller_net_baht_kwh, 4),
            "energy_cost_baht": round(self.energy_cost_baht, 2),
            "wheeling_charge_baht": round(self.wheeling_charge_baht, 2),
            "buyer_total_cost_baht": round(self.buyer_total_cost_baht, 2),
            "seller_net_revenue_baht": round(self.seller_net_revenue_baht, 2),
            "market_sentiment": self.market_sentiment,
        }


@dataclass
class PriceAnalysis:
    """Comparison analysis between utility and P2P."""
    buyer_savings_baht: float
    buyer_savings_percent: float
    seller_gain_baht: float
    seller_gain_percent: float
    total_welfare_gain_baht: float
    is_p2p_beneficial: bool
    break_even_price_baht_kwh: float

    def to_dict(self) -> Dict:
        return {
            "buyer_savings_baht": round(self.buyer_savings_baht, 2),
            "buyer_savings_percent": round(self.buyer_savings_percent, 1),
            "seller_gain_baht": round(self.seller_gain_baht, 2),
            "seller_gain_percent": round(self.seller_gain_percent, 1),
            "total_welfare_gain_baht": round(self.total_welfare_gain_baht, 2),
            "is_p2p_beneficial": self.is_p2p_beneficial,
            "break_even_price_baht_kwh": round(self.break_even_price_baht_kwh, 4),
        }


@dataclass
class PriceSnapshot:
    """A point-in-time price record."""
    timestamp: datetime
    utility_avg_baht_kwh: float
    p2p_mcp_baht_kwh: float
    p2p_buyer_total_baht_kwh: float
    nodal_price_avg: float
    grid_demand_mw: float
    renewable_pct: float


# ============================================================================
# Price Providers
# ============================================================================

class TOUTariffPriceProvider:
    """
    Provides Thai TOU tariff pricing for utility billing.
    """

    def calculate_utility_price(
        self,
        energy_kwh: float,
        provider: UtilityProvider = UtilityProvider.PEA,
        category: TariffCategory = TariffCategory.RESIDENTIAL_12,
        timestamp: Optional[datetime] = None,
    ) -> UtilityPriceBreakdown:
        """
        Calculate utility price breakdown for given consumption.
        Uses TOU rates with Ft charge and VAT.
        """
        tariff = TARIFF_MAP.get(category, TOU_RESIDENTIAL_12_LV)
        ts = timestamp or datetime.now(timezone.utc)

        # For simplicity, assume 50/50 on-peak / off-peak split
        on_peak_kwh = energy_kwh * 0.5
        off_peak_kwh = energy_kwh * 0.5

        energy_charge = (
            on_peak_kwh * tariff.on_peak_rate
            + off_peak_kwh * tariff.off_peak_rate
        )

        ft = FT_CHARGE * energy_kwh
        service = tariff.service_charge  # Monthly, pro-rated per reading

        total_before_vat = energy_charge + ft + service
        vat = total_before_vat * VAT_RATE
        total = total_before_vat + vat

        avg_rate = total / energy_kwh if energy_kwh > 0 else 0.0

        return UtilityPriceBreakdown(
            provider=provider.value,
            tariff_category=category.value,
            tariff_type=tariff.name,
            energy_charge_baht=energy_charge,
            ft_charge_baht=ft,
            service_charge_baht=service,
            total_before_vat_baht=total_before_vat,
            vat_baht=vat,
            total_amount_baht=total,
            average_rate_baht_kwh=avg_rate,
            ft_rate_baht_kwh=FT_CHARGE,
        )

    def get_current_rate(
        self,
        category: TariffCategory = TariffCategory.RESIDENTIAL_12,
        timestamp: Optional[datetime] = None,
    ) -> float:
        """Get current Baht/kWh rate based on TOU period."""
        tariff = TARIFF_MAP.get(category, TOU_RESIDENTIAL_12_LV)
        ts = timestamp or datetime.now(timezone.utc)
        return get_tou_rate(ts, tariff)


class P2PMarketPriceProvider:
    """
    Dynamic P2P market clearing price provider.
    Simulates market dynamics based on supply/demand, time of day, and grid conditions.
    """

    def __init__(self):
        self.base_price = P2P_BASE_PRICE
        self.supply_demand_ratio = 1.0  # >1 = oversupply, <1 = shortage
        self._rng = np.random.default_rng(seed=42)

    def set_market_conditions(
        self,
        supply_demand_ratio: float = 1.0,
        renewable_pct: float = 20.0,
    ) -> None:
        """Update market conditions for price calculation."""
        self.supply_demand_ratio = max(0.1, supply_demand_ratio)
        self.renewable_pct = max(0.0, min(100.0, renewable_pct))

    def calculate_mcp(
        self,
        timestamp: Optional[datetime] = None,
        nodal_price_avg: Optional[float] = None,
    ) -> float:
        """
        Calculate Market Clearing Price (MCP) for P2P trading.
        Factors: base price, supply/demand, TOU period, nodal prices.
        """
        ts = timestamp or datetime.now(timezone.utc)

        # Base price with small random walk
        price = self.base_price + self._rng.uniform(-0.1, 0.1)

        # Supply/demand factor
        if self.supply_demand_ratio > 1.0:
            # Oversupply → lower prices
            price *= 1.0 - (self.supply_demand_ratio - 1.0) * 0.3
        else:
            # Shortage → higher prices
            price *= 1.0 + (1.0 - self.supply_demand_ratio) * 0.5

        # TOU adjustment: higher during on-peak
        if is_on_peak(ts):
            price *= 1.15
        else:
            price *= 0.85

        # Nodal price anchor (if available)
        if nodal_price_avg is not None and nodal_price_avg > 0:
            price = price * 0.6 + nodal_price_avg * 0.4

        # Clamp to valid range
        return max(P2P_MIN_PRICE, min(P2P_MAX_PRICE, round(price, 4)))

    def calculate_p2p_breakdown(
        self,
        energy_kwh: float,
        mcp: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        wheeling_per_kwh: float = WHEELING_CHARGE_RESIDENTIAL,
    ) -> P2PPriceBreakdown:
        """Full P2P price breakdown for given energy amount."""
        ts = timestamp or datetime.now(timezone.utc)
        mcp = mcp or self.calculate_mcp(ts)

        wheeling = wheeling_per_kwh
        buyer_rate = mcp + wheeling
        seller_net = mcp * (1.0 - GRID_LOSS_FACTOR)  # Seller pays loss factor

        energy_cost = mcp * energy_kwh
        wheeling_charge = wheeling * energy_kwh
        buyer_total = buyer_rate * energy_kwh
        seller_revenue = seller_net * energy_kwh

        # Market sentiment
        if mcp < 3.0:
            sentiment = "buyer_favorable"
        elif mcp > 4.5:
            sentiment = "seller_favorable"
        else:
            sentiment = "balanced"

        return P2PPriceBreakdown(
            market_clearing_price_baht_kwh=mcp,
            wheeling_cost_baht_kwh=wheeling,
            buyer_total_baht_kwh=buyer_rate,
            seller_net_baht_kwh=seller_net,
            energy_cost_baht=energy_cost,
            wheeling_charge_baht=wheeling_charge,
            buyer_total_cost_baht=buyer_total,
            seller_net_revenue_baht=seller_revenue,
            market_sentiment=sentiment,
        )


class PriceComparisonService:
    """
    Compares utility pricing vs P2P trading for consumer decision support.
    """

    def __init__(
        self,
        utility_provider: TOUTariffPriceProvider,
        p2p_provider: P2PMarketPriceProvider,
    ):
        self.utility = utility_provider
        self.p2p = p2p_provider

    def compare(
        self,
        energy_kwh: float,
        provider: UtilityProvider = UtilityProvider.PEA,
        category: TariffCategory = TariffCategory.RESIDENTIAL_12,
        p2p_price: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict:
        """
        Full comparison: utility vs P2P for given consumption.
        Returns dict matching the frontend PriceCompareResponse schema.
        """
        ts = timestamp or datetime.now(timezone.utc)

        # Utility pricing
        util = self.utility.calculate_utility_price(
            energy_kwh, provider, category, ts
        )

        # P2P pricing
        mcp = p2p_price or self.p2p.calculate_mcp(ts)
        p2p = self.p2p.calculate_p2p_breakdown(energy_kwh, mcp, ts)

        # Analysis
        savings = util.total_amount_baht - p2p.buyer_total_cost_baht
        savings_pct = (savings / util.total_amount_baht * 100) if util.total_amount_baht > 0 else 0

        seller_gain = p2p.seller_net_revenue_baht
        seller_gain_pct = (seller_gain / p2p.energy_cost_baht * 100) if p2p.energy_cost_baht > 0 else 0

        welfare = savings + seller_gain
        break_even = util.total_amount_baht / energy_kwh if energy_kwh > 0 else 0

        is_beneficial = savings > 0

        # Recommendation
        if is_beneficial:
            recommendation = f"Switch to P2P — save {abs(savings):.2f} ฿ ({abs(savings_pct):.1f}% cheaper)"
        else:
            recommendation = f"Stay with utility — P2P costs {abs(savings):.2f} ฿ more"

        return {
            "timestamp": ts.isoformat(),
            "energy_kwh": round(energy_kwh, 3),
            "utility": util.to_dict(),
            "p2p": p2p.to_dict(),
            "analysis": {
                "buyer_savings_baht": round(savings, 2),
                "buyer_savings_percent": round(savings_pct, 1),
                "seller_gain_baht": round(seller_gain, 2),
                "seller_gain_percent": round(seller_gain_pct, 1),
                "total_welfare_gain_baht": round(welfare, 2),
                "is_p2p_beneficial": is_beneficial,
                "break_even_price_baht_kwh": round(break_even, 4),
            },
            "recommendation": recommendation,
        }


# ============================================================================
# Price History Manager
# ============================================================================

class PriceHistoryManager:
    """Stores and queries historical price snapshots."""

    def __init__(self, max_entries: int = 10000):
        self.history: List[PriceSnapshot] = []
        self.max_entries = max_entries

    def record(
        self,
        utility_avg: float,
        p2p_mcp: float,
        p2p_buyer_total: float,
        nodal_avg: float = 0.0,
        grid_demand: float = 0.0,
        renewable_pct: float = 0.0,
    ) -> PriceSnapshot:
        snapshot = PriceSnapshot(
            timestamp=datetime.now(timezone.utc),
            utility_avg_baht_kwh=utility_avg,
            p2p_mcp_baht_kwh=p2p_mcp,
            p2p_buyer_total_baht_kwh=p2p_buyer_total,
            nodal_price_avg=nodal_avg,
            grid_demand_mw=grid_demand,
            renewable_pct=renewable_pct,
        )
        self.history.append(snapshot)
        # Trim old entries
        if len(self.history) > self.max_entries:
            self.history = self.history[-self.max_entries:]
        return snapshot

    def get_latest(self) -> Optional[PriceSnapshot]:
        return self.history[-1] if self.history else None

    def get_history(self, limit: int = 100) -> List[Dict]:
        entries = self.history[-limit:] if self.history else []
        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "utility_avg_baht_kwh": s.utility_avg_baht_kwh,
                "p2p_mcp_baht_kwh": s.p2p_mcp_baht_kwh,
                "p2p_buyer_total_baht_kwh": s.p2p_buyer_total_baht_kwh,
                "nodal_price_avg": s.nodal_price_avg,
            }
            for s in entries
        ]

    def get_stats(self) -> Dict:
        if not self.history:
            return {"count": 0}

        utilities = [s.utility_avg_baht_kwh for s in self.history]
        p2ps = [s.p2p_mcp_baht_kwh for s in self.history]

        return {
            "count": len(self.history),
            "utility": {
                "min": round(min(utilities), 3),
                "max": round(max(utilities), 3),
                "avg": round(np.mean(utilities), 3),
            },
            "p2p": {
                "min": round(min(p2ps), 4),
                "max": round(max(p2ps), 4),
                "avg": round(np.mean(p2ps), 4),
            },
        }

    def clear(self) -> None:
        self.history.clear()


# ============================================================================
# Singleton Access
# ============================================================================

_utility_provider: Optional[TOUTariffPriceProvider] = None
_p2p_provider: Optional[P2PMarketPriceProvider] = None
_comparison_service: Optional[PriceComparisonService] = None
_price_history: Optional[PriceHistoryManager] = None


def get_utility_provider() -> TOUTariffPriceProvider:
    global _utility_provider
    if _utility_provider is None:
        _utility_provider = TOUTariffPriceProvider()
    return _utility_provider


def get_p2p_provider() -> P2PMarketPriceProvider:
    global _p2p_provider
    if _p2p_provider is None:
        _p2p_provider = P2PMarketPriceProvider()
    return _p2p_provider


def get_comparison_service() -> PriceComparisonService:
    global _comparison_service
    if _comparison_service is None:
        _comparison_service = PriceComparisonService(
            get_utility_provider(), get_p2p_provider()
        )
    return _comparison_service


def get_price_history() -> PriceHistoryManager:
    global _price_history
    if _price_history is None:
        _price_history = PriceHistoryManager()
    return _price_history
