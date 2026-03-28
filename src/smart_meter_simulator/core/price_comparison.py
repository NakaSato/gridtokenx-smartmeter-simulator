"""
Price Comparison Module: Single-Buyer vs Blockchain P2P

This module provides comparison between the traditional Single-Buyer (utility) 
model and the decentralized Blockchain P2P trading model for the Thai electricity
market.

Key Features:
- Calculate single-buyer model prices (utility tariffs)
- Track dynamic blockchain P2P prices
- Compare economics and calculate savings
- Generate price comparison reports
- Support for TOU and ladder tariff comparisons
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..config.thai_market import (
    TariffCategory,
    UtilityProvider,
    TOUPeriod,
    GRID_BUYBACK_RATE,
    GRID_PURCHASE_RATE_HIGH_TIER,
    TYPICAL_P2P_PRICE,
    RESIDENTIAL_WHEELING_COST_AVG,
    get_tou_period,
    TOU_RATES,
)
from .thai_tariff import ThaiTariffCalculator

logger = logging.getLogger(__name__)


class PricingModel(Enum):
    """Energy pricing models."""
    SINGLE_BUYER = "single_buyer"  # Traditional utility model
    BLOCKCHAIN_P2P = "blockchain_p2p"  # Decentralized P2P trading
    HYBRID = "hybrid"  # Mixed model


@dataclass
class SingleBuyerPrice:
    """Price from the single-buyer (utility) model."""
    timestamp: datetime
    tariff_type: str
    import_rate_baht_kwh: float  # Price to buy from utility
    export_rate_baht_kwh: float  # Price to sell to utility (feed-in)
    ft_rate_baht_kwh: float  # Fuel adjustment charge
    is_peak_period: bool
    breakdown: Dict = field(default_factory=dict)


@dataclass
class BlockchainP2PPrice:
    """Dynamic price from blockchain P2P market."""
    timestamp: datetime
    market_clearing_price_baht_kwh: float  # MCP from P2P market
    wheeling_cost_baht_kwh: float  # TPA wheeling charge
    buyer_total_baht_kwh: float  # MCP + wheeling
    seller_net_baht_kwh: float  # MCP - wheeling
    market_volume_kwh: float  # Trading volume
    market_sentiment: str  # "Bullish", "Bearish", "Stable"
    spread_vs_utility_baht_kwh: float  # vs grid purchase rate
    premium_vs_feedin_baht_kwh: float  # vs grid feed-in rate


@dataclass
class PriceComparison:
    """Comparison between single-buyer and blockchain P2P prices."""
    timestamp: datetime
    energy_kwh: float
    
    # Single-buyer model
    single_buyer_cost_baht: float
    single_buyer_rate_baht_kwh: float
    
    # Blockchain P2P model
    p2p_buyer_cost_baht: float
    p2p_buyer_rate_baht_kwh: float
    p2p_seller_revenue_baht: float
    p2p_seller_rate_baht_kwh: float
    
    # Savings analysis
    buyer_savings_baht: float  # Positive = P2P is cheaper
    buyer_savings_percent: float
    seller_gain_baht: float  # Positive = P2P earns more
    seller_gain_percent: float
    
    # Welfare analysis
    total_welfare_gain_baht: float
    is_p2p_beneficial: bool
    
    # Market context
    market_sentiment: str
    recommendation: str


@dataclass
class MonthlyComparisonReport:
    """Monthly comparison report between pricing models."""
    billing_month: int
    billing_year: int
    
    # Single-buyer totals
    single_buyer_total_cost_baht: float
    single_buyer_total_kwh: float
    single_buyer_avg_rate_baht_kwh: float
    
    # Blockchain P2P totals
    p2p_total_cost_baht: float
    p2p_total_kwh: float
    p2p_avg_rate_baht_kwh: float
    p2p_total_revenue_baht: float  # For sellers
    
    # Savings
    total_savings_baht: float
    savings_percent: float
    
    # Breakdown by period
    peak_savings_baht: float
    off_peak_savings_baht: float
    
    # Statistics
    num_p2p_trades: int
    avg_market_clearing_price_baht_kwh: float
    market_participation_rate: float  # % of energy traded via P2P


class SingleBuyerPricingModel:
    """
    Traditional Single-Buyer (Utility) Pricing Model.
    
    In this model, the utility (MEA/PEA) is the sole buyer and seller:
    - Consumers buy from utility at retail tariff rates
    - Prosumers sell to utility at feed-in tariff (2.20 Baht/kWh)
    - No direct peer-to-peer trading allowed
    """
    
    def __init__(
        self,
        tariff_category: TariffCategory = TariffCategory.TYPE_1_1_2,
        utility_provider: UtilityProvider = UtilityProvider.PEA,
        ft_rate: Optional[float] = None,
    ):
        """
        Initialize single-buyer pricing model.
        
        Args:
            tariff_category: Tariff type (1.1.1, 1.1.2, 1.2, etc.)
            utility_provider: Utility provider (MEA or PEA)
            ft_rate: Fuel adjustment charge rate
        """
        self.tariff_category = tariff_category
        self.utility_provider = utility_provider
        self.ft_rate = ft_rate if ft_rate is not None else 0.0972  # Current Ft
        
        self.tariff_calculator = ThaiTariffCalculator(
            tariff_category=tariff_category,
            ft_rate=self.ft_rate,
            utility_provider=utility_provider,
        )
    
    def get_price(self, timestamp: datetime) -> SingleBuyerPrice:
        """
        Get single-buyer price for a specific timestamp.
        
        Args:
            timestamp: Time to get price for
            
        Returns:
            SingleBuyerPrice with utility rates
        """
        # Determine tariff type and rates
        if self.tariff_category in [TariffCategory.TYPE_1_1_1, TariffCategory.TYPE_1_1_2]:
            # Ladder tariff - use average rate
            # For comparison purposes, use high-tier rate (marginal cost)
            import_rate = GRID_PURCHASE_RATE_HIGH_TIER
            tariff_type = f"Ladder ({self.tariff_category.value})"
            is_peak = False
        else:
            # TOU tariff - get rate for specific time
            tou_period = get_tou_period(
                timestamp.hour, 
                timestamp.weekday() >= 5
            )
            import_rate = TOU_RATES[tou_period]
            tariff_type = f"TOU ({self.tariff_category.value})"
            is_peak = (tou_period == TOUPeriod.ON_PEAK)
        
        return SingleBuyerPrice(
            timestamp=timestamp,
            tariff_type=tariff_type,
            import_rate_baht_kwh=import_rate,
            export_rate_baht_kwh=GRID_BUYBACK_RATE,
            ft_rate_baht_kwh=self.ft_rate,
            is_peak_period=is_peak,
            breakdown={
                "base_rate": import_rate - self.ft_rate,
                "ft_rate": self.ft_rate,
                "feed_in_rate": GRID_BUYBACK_RATE,
                "spread": import_rate - GRID_BUYBACK_RATE,
            }
        )
    
    def calculate_monthly_bill(
        self,
        consumption_kwh: float,
        month: int,
        year: int,
    ) -> Dict[str, float]:
        """
        Calculate monthly bill under single-buyer model.
        
        Args:
            consumption_kwh: Monthly consumption in kWh
            month: Billing month
            year: Billing year
            
        Returns:
            Dictionary with bill breakdown
        """
        result = self.tariff_calculator.calculate_monthly_bill(
            consumption_kwh=consumption_kwh,
            billing_month=month,
            billing_year=year,
        )
        
        return {
            "total_amount_baht": result.total_amount,
            "energy_charge_baht": result.energy_charge,
            "ft_charge_baht": result.ft_charge,
            "service_charge_baht": result.service_charge,
            "average_rate_baht_kwh": result.average_rate,
            "total_kwh": result.total_kwh,
        }


class BlockchainP2PPricingModel:
    """
    Blockchain-based P2P Dynamic Pricing Model.
    
    In this model, prices are determined by market forces:
    - Market Clearing Price (MCP) from supply/demand matching
    - Wheeling charges for grid usage (TPA)
    - Real-time price discovery via blockchain oracle
    - Transparent settlement on Solana
    """
    
    def __init__(
        self,
        wheeling_cost_baht_kwh: float = RESIDENTIAL_WHEELING_COST_AVG,
        grid_reference_rate: float = GRID_PURCHASE_RATE_HIGH_TIER,
        feedin_reference_rate: float = GRID_BUYBACK_RATE,
    ):
        """
        Initialize blockchain P2P pricing model.
        
        Args:
            wheeling_cost_baht_kwh: TPA wheeling charge
            grid_reference_rate: Grid purchase rate for comparison
            feedin_reference_rate: Grid feed-in rate for comparison
        """
        self.wheeling_cost = wheeling_cost_baht_kwh
        self.grid_rate = grid_reference_rate
        self.feedin_rate = feedin_reference_rate
        
        # Price history for trend analysis
        self.price_history: List[BlockchainP2PPrice] = []
    
    def get_price(
        self,
        timestamp: datetime,
        market_clearing_price: float,
        market_volume: float = 0.0,
        market_sentiment: str = "Stable",
    ) -> BlockchainP2PPrice:
        """
        Get blockchain P2P price for a specific timestamp.
        
        Args:
            timestamp: Time to get price for
            market_clearing_price: MCP from P2P market (Baht/kWh)
            market_volume: Trading volume in kWh
            market_sentiment: Market sentiment
            
        Returns:
            BlockchainP2PPrice with dynamic rates
        """
        # Calculate buyer and seller rates
        buyer_total = market_clearing_price + self.wheeling_cost
        seller_net = market_clearing_price - self.wheeling_cost
        
        # Calculate spreads vs utility
        spread_vs_utility = self.grid_rate - buyer_total
        premium_vs_feedin = seller_net - self.feedin_rate
        
        p2p_price = BlockchainP2PPrice(
            timestamp=timestamp,
            market_clearing_price_baht_kwh=market_clearing_price,
            wheeling_cost_baht_kwh=self.wheeling_cost,
            buyer_total_baht_kwh=buyer_total,
            seller_net_baht_kwh=seller_net,
            market_volume_kwh=market_volume,
            market_sentiment=market_sentiment,
            spread_vs_utility_baht_kwh=spread_vs_utility,
            premium_vs_feedin_baht_kwh=premium_vs_feedin,
        )
        
        # Store in history
        self.price_history.append(p2p_price)
        
        return p2p_price
    
    def simulate_market_price(
        self,
        timestamp: datetime,
        supply_kwh: float,
        demand_kwh: float,
        base_price: float = TYPICAL_P2P_PRICE,
        use_formula: bool = True,
    ) -> float:
        """
        Simulate market clearing price based on supply/demand.

        Implements the GridTokenX dynamic pricing formula from simulator_logic.md:
            p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min

        Where:
            - D_t = Demand - Supply (difference)
            - R_t = Demand / Supply (ratio)
            - p_min = Price floor (typically 2.20 Baht, the utility buy-back rate)

        Args:
            timestamp: Time of simulation
            supply_kwh: Available supply in kWh
            demand_kwh: Total demand in kWh
            base_price: Base price reference / p_min (Baht/kWh)
            use_formula: If True, use arctan formula; if False, use elasticity model

        Returns:
            Simulated market clearing price (Baht/kWh)

        Example:
            >>> calc = BlockchainP2PPricingModel()
            >>> # Balanced market (100 supply, 100 demand)
            >>> price = calc.simulate_market_price(datetime.now(), 100, 100)
            >>> # High demand (50 supply, 150 demand)
            >>> price = calc.simulate_market_price(datetime.now(), 50, 150)
        """
        import math

        # Price floor (p_min) - typically utility buy-back rate
        p_min = base_price  # Default 2.20-3.30 Baht/kWh

        if supply_kwh <= 0:
            # Scarcity pricing - maximum price
            return p_min * 1.5

        if use_formula:
            # GridTokenX Dynamic Pricing Formula
            # p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min
            #
            # Where:
            # - D_t = demand - supply (normalized to prevent overflow)
            # - R_t = demand / supply ratio

            # Normalize difference to prevent e^D overflow
            # Scale by 100 kWh to keep D_t in reasonable range
            D_t = (demand_kwh - supply_kwh) / 100.0

            # Supply-demand ratio
            R_t = demand_kwh / supply_kwh

            # Apply formula
            # arctan(e^D_t) ranges from 0 to π/2 (~1.57)
            # arctan(R_t)/10 ranges from 0 to ~0.157
            term1 = math.atan(math.exp(D_t))
            term2 = math.atan(R_t) / 10.0

            mcp = term1 + term2 + p_min

            # Clamp to reasonable range (2.0 - 5.5 Baht/kWh)
            mcp = max(2.0, min(5.5, mcp))
        else:
            # Legacy elasticity model (for backward compatibility)
            # Supply-demand ratio
            ratio = demand_kwh / supply_kwh if supply_kwh > 0 else 2.0

            # Price elasticity factor
            if ratio > 1.5:
                elasticity = 1.3  # High demand
            elif ratio > 1.0:
                elasticity = 1.1  # Moderate demand
            elif ratio > 0.7:
                elasticity = 1.0  # Balanced
            else:
                elasticity = 0.9  # Oversupply

            # Time-of-day adjustment (higher during peak)
            hour = timestamp.hour
            if 17 <= hour <= 21:  # Evening peak
                time_factor = 1.15
            elif 9 <= hour <= 16:  # Daytime (solar peak)
                time_factor = 0.95
            else:
                time_factor = 1.0

            mcp = base_price * elasticity * time_factor

            # Clamp to reasonable range
            mcp = max(2.0, min(5.5, mcp))

        return mcp
    
    def get_market_sentiment(self) -> str:
        """
        Get current market sentiment based on price history.
        
        Returns:
            Market sentiment string
        """
        if len(self.price_history) < 2:
            return "Stable"
        
        # Analyze recent price trend
        recent = self.price_history[-5:]
        prices = [p.market_clearing_price_baht_kwh for p in recent]
        
        if len(prices) < 2:
            return "Stable"
        
        # Calculate trend
        price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        
        if price_change > 0.1:
            return "Bullish (Rising Prices)"
        elif price_change < -0.1:
            return "Bearish (Falling Prices)"
        else:
            return "Stable"
    
    def get_average_mcp(self, hours: int = 24) -> float:
        """
        Get average market clearing price over recent hours.
        
        Args:
            hours: Number of hours to average
            
        Returns:
            Average MCP (Baht/kWh)
        """
        if not self.price_history:
            return TYPICAL_P2P_PRICE
        
        recent = self.price_history[-hours:]
        if not recent:
            return TYPICAL_P2P_PRICE
        
        return sum(p.market_clearing_price_baht_kwh for p in recent) / len(recent)


class PriceComparisonEngine:
    """
    Engine for comparing Single-Buyer and Blockchain P2P pricing models.
    
    Provides comprehensive economic analysis of:
    - Buyer savings from P2P vs utility
    - Seller gains from P2P vs feed-in tariff
    - Total welfare improvement
    - Market recommendations
    """
    
    def __init__(
        self,
        tariff_category: TariffCategory = TariffCategory.TYPE_1_1_2,
        utility_provider: UtilityProvider = UtilityProvider.PEA,
        ft_rate: Optional[float] = None,
        wheeling_cost: float = RESIDENTIAL_WHEELING_COST_AVG,
    ):
        """
        Initialize price comparison engine.
        
        Args:
            tariff_category: Tariff type for single-buyer model
            utility_provider: Utility provider
            ft_rate: Fuel adjustment charge rate
            wheeling_cost: TPA wheeling cost for P2P
        """
        self.single_buyer = SingleBuyerPricingModel(
            tariff_category=tariff_category,
            utility_provider=utility_provider,
            ft_rate=ft_rate,
        )
        
        self.blockchain_p2p = BlockchainP2PPricingModel(
            wheeling_cost_baht_kwh=wheeling_cost,
        )
        
        # Comparison history
        self.comparison_history: List[PriceComparison] = []
    
    def compare_prices(
        self,
        timestamp: datetime,
        energy_kwh: float,
        market_clearing_price: float,
        market_volume: float = 0.0,
        market_sentiment: str = "Stable",
    ) -> PriceComparison:
        """
        Compare single-buyer and blockchain P2P prices.
        
        Args:
            timestamp: Time of comparison
            energy_kwh: Energy amount for comparison
            market_clearing_price: P2P market clearing price
            market_volume: P2P trading volume
            market_sentiment: Market sentiment
            
        Returns:
            PriceComparison with detailed analysis
        """
        # Get single-buyer price
        sb_price = self.single_buyer.get_price(timestamp)
        
        # Get blockchain P2P price
        p2p_price = self.blockchain_p2p.get_price(
            timestamp=timestamp,
            market_clearing_price=market_clearing_price,
            market_volume=market_volume,
            market_sentiment=market_sentiment,
        )
        
        # Calculate costs
        single_buyer_cost = energy_kwh * sb_price.import_rate_baht_kwh
        
        # P2P buyer cost (includes wheeling)
        p2p_buyer_cost = energy_kwh * p2p_price.buyer_total_baht_kwh
        
        # P2P seller revenue (after wheeling)
        p2p_seller_revenue = energy_kwh * p2p_price.seller_net_baht_kwh
        
        # Calculate savings/gains
        buyer_savings = single_buyer_cost - p2p_buyer_cost
        buyer_savings_percent = (buyer_savings / single_buyer_cost * 100) if single_buyer_cost > 0 else 0
        
        # Seller gain vs feed-in tariff
        seller_feedin_revenue = energy_kwh * sb_price.export_rate_baht_kwh
        seller_gain = p2p_seller_revenue - seller_feedin_revenue
        seller_gain_percent = (seller_gain / seller_feedin_revenue * 100) if seller_feedin_revenue > 0 else 0
        
        # Total welfare gain
        total_welfare_gain = buyer_savings + seller_gain
        
        # Determine if P2P is beneficial
        is_p2p_beneficial = buyer_savings > 0 and seller_gain > 0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            buyer_savings=buyer_savings,
            seller_gain=seller_gain,
            market_sentiment=market_sentiment,
            is_p2p_beneficial=is_p2p_beneficial,
        )
        
        comparison = PriceComparison(
            timestamp=timestamp,
            energy_kwh=energy_kwh,
            single_buyer_cost_baht=single_buyer_cost,
            single_buyer_rate_baht_kwh=sb_price.import_rate_baht_kwh,
            p2p_buyer_cost_baht=p2p_buyer_cost,
            p2p_buyer_rate_baht_kwh=p2p_price.buyer_total_baht_kwh,
            p2p_seller_revenue_baht=p2p_seller_revenue,
            p2p_seller_rate_baht_kwh=p2p_price.seller_net_baht_kwh,
            buyer_savings_baht=buyer_savings,
            buyer_savings_percent=buyer_savings_percent,
            seller_gain_baht=seller_gain,
            seller_gain_percent=seller_gain_percent,
            total_welfare_gain_baht=total_welfare_gain,
            is_p2p_beneficial=is_p2p_beneficial,
            market_sentiment=market_sentiment,
            recommendation=recommendation,
        )
        
        # Store in history
        self.comparison_history.append(comparison)
        
        return comparison
    
    def _generate_recommendation(
        self,
        buyer_savings: float,
        seller_gain: float,
        market_sentiment: str,
        is_p2p_beneficial: bool,
    ) -> str:
        """
        Generate recommendation based on comparison results.
        
        Args:
            buyer_savings: Buyer savings from P2P
            seller_gain: Seller gain from P2P
            market_sentiment: Market sentiment
            is_p2p_beneficial: Whether P2P is mutually beneficial
            
        Returns:
            Recommendation string
        """
        if is_p2p_beneficial:
            if buyer_savings > 50 and seller_gain > 50:
                return "STRONG BUY: P2P trading offers significant savings for both parties"
            elif buyer_savings > 20 or seller_gain > 20:
                return "BUY: P2P trading is economically advantageous"
            else:
                return "HOLD: P2P trading offers modest benefits"
        else:
            if buyer_savings > 0:
                return "PARTIAL: P2P benefits buyers but not sellers"
            elif seller_gain > 0:
                return "PARTIAL: P2P benefits sellers but not buyers"
            else:
                return "AVOID: Single-buyer model is more economical"
    
    def generate_monthly_report(
        self,
        month: int,
        year: int,
    ) -> MonthlyComparisonReport:
        """
        Generate monthly comparison report.
        
        Args:
            month: Billing month
            year: Billing year
            
        Returns:
            MonthlyComparisonReport with comprehensive analysis
        """
        # Filter comparisons for the month
        monthly_comparisons = [
            c for c in self.comparison_history
            if c.timestamp.month == month and c.timestamp.year == year
        ]
        
        if not monthly_comparisons:
            return MonthlyComparisonReport(
                billing_month=month,
                billing_year=year,
                single_buyer_total_cost_baht=0,
                single_buyer_total_kwh=0,
                single_buyer_avg_rate_baht_kwh=0,
                p2p_total_cost_baht=0,
                p2p_total_kwh=0,
                p2p_avg_rate_baht_kwh=0,
                p2p_total_revenue_baht=0,
                total_savings_baht=0,
                savings_percent=0,
                peak_savings_baht=0,
                off_peak_savings_baht=0,
                num_p2p_trades=0,
                avg_market_clearing_price_baht_kwh=0,
                market_participation_rate=0,
            )
        
        # Aggregate totals
        total_single_buyer_cost = sum(c.single_buyer_cost_baht for c in monthly_comparisons)
        total_energy = sum(c.energy_kwh for c in monthly_comparisons)
        total_p2p_cost = sum(c.p2p_buyer_cost_baht for c in monthly_comparisons)
        total_p2p_revenue = sum(c.p2p_seller_revenue_baht for c in monthly_comparisons)
        total_savings = sum(c.buyer_savings_baht for c in monthly_comparisons)
        
        # Peak vs off-peak savings
        peak_comparisons = [
            c for c in monthly_comparisons
            if self.single_buyer.get_price(c.timestamp).is_peak_period
        ]
        off_peak_comparisons = [
            c for c in monthly_comparisons
            if c not in peak_comparisons
        ]
        
        peak_savings = sum(c.buyer_savings_baht for c in peak_comparisons)
        off_peak_savings = sum(c.buyer_savings_baht for c in off_peak_comparisons)
        
        # Beneficial trades count
        beneficial_trades = [c for c in monthly_comparisons if c.is_p2p_beneficial]
        
        # Average MCP
        avg_mcp = self.blockchain_p2p.get_average_mcp(hours=len(monthly_comparisons))
        
        return MonthlyComparisonReport(
            billing_month=month,
            billing_year=year,
            single_buyer_total_cost_baht=total_single_buyer_cost,
            single_buyer_total_kwh=total_energy,
            single_buyer_avg_rate_baht_kwh=total_single_buyer_cost / total_energy if total_energy > 0 else 0,
            p2p_total_cost_baht=total_p2p_cost,
            p2p_total_kwh=total_energy,
            p2p_avg_rate_baht_kwh=total_p2p_cost / total_energy if total_energy > 0 else 0,
            p2p_total_revenue_baht=total_p2p_revenue,
            total_savings_baht=total_savings,
            savings_percent=(total_savings / total_single_buyer_cost * 100) if total_single_buyer_cost > 0 else 0,
            peak_savings_baht=peak_savings,
            off_peak_savings_baht=off_peak_savings,
            num_p2p_trades=len(beneficial_trades),
            avg_market_clearing_price_baht_kwh=avg_mcp,
            market_participation_rate=len(beneficial_trades) / len(monthly_comparisons) * 100 if monthly_comparisons else 0,
        )
    
    def get_comparison_summary(self) -> Dict:
        """
        Get summary of all comparisons.
        
        Returns:
            Dictionary with comparison statistics
        """
        if not self.comparison_history:
            return {"message": "No comparisons available"}
        
        total_energy = sum(c.energy_kwh for c in self.comparison_history)
        total_savings = sum(c.buyer_savings_baht for c in self.comparison_history)
        total_seller_gain = sum(c.seller_gain_baht for c in self.comparison_history)
        total_welfare = sum(c.total_welfare_gain_baht for c in self.comparison_history)
        
        beneficial_count = sum(1 for c in self.comparison_history if c.is_p2p_beneficial)
        
        return {
            "total_comparisons": len(self.comparison_history),
            "total_energy_kwh": total_energy,
            "total_buyer_savings_baht": total_savings,
            "total_seller_gain_baht": total_seller_gain,
            "total_welfare_gain_baht": total_welfare,
            "beneficial_trades_count": beneficial_count,
            "beneficial_trades_percent": beneficial_count / len(self.comparison_history) * 100,
            "average_savings_per_kwh": total_savings / total_energy if total_energy > 0 else 0,
            "average_welfare_per_kwh": total_welfare / total_energy if total_energy > 0 else 0,
            "blockchain_p2p_avg_mcp": self.blockchain_p2p.get_average_mcp(),
            "market_sentiment": self.blockchain_p2p.get_market_sentiment(),
        }
    
    def clear_history(self):
        """Clear comparison history."""
        self.comparison_history = []
        self.blockchain_p2p.price_history = []
        logger.info("Cleared price comparison history")
