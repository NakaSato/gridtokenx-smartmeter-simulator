"""
Thai Market Calculators

Utility calculators for Thai electricity market economics:
- P2P trading economics with wheeling charges
- Solar ROI calculations with Royal Decree No. 805 tax incentives
- MEA/PEA jurisdiction detection
- P2P profitability analysis
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..config.thai_market import (
    SOLAR_TAX_INCENTIVE,
    SOLAR_BENCHMARKS,
    SolarSystemBenchmark,
    UTILITY_JURISDICTIONS,
    UtilityProvider,
    TPA_CHARGES,
    RESIDENTIAL_WHEELING_COST_AVG,
    RESIDENTIAL_WHEELING_COST_MIN,
    RESIDENTIAL_WHEELING_COST_MAX,
    GRID_BUYBACK_RATE,
    GRID_PURCHASE_RATE_HIGH_TIER,
    TYPICAL_P2P_PRICE,
    calculate_p2p_profitability,
)

logger = logging.getLogger(__name__)


# ============================================================================
# P2P Trading Economics Calculator
# ============================================================================

@dataclass
class P2PTradeEconomics:
    """Complete economics analysis for a P2P energy trade."""
    # Trade parameters
    energy_kwh: float
    p2p_price_baht_kwh: float
    wheeling_cost_baht_kwh: float
    
    # Seller economics
    seller_revenue_baht: float
    seller_net_baht: float  # After wheeling
    seller_vs_utility_gain_baht: float
    
    # Buyer economics
    buyer_cost_baht: float
    buyer_total_baht: float  # Including wheeling
    buyer_vs_utility_savings_baht: float
    
    # Grid economics
    total_welfare_gain_baht: float
    grid_wheeling_revenue_baht: float
    
    # Flags
    is_profitable_for_seller: bool
    is_profitable_for_buyer: bool
    is_mutually_beneficial: bool


@dataclass
class TPAWheelingBreakdown:
    """Detailed breakdown of TPA wheeling charges."""
    components: List[Dict[str, float]]  # [{name, rate, total}]
    total_wheeling_baht: float
    total_wheeling_per_kwh: float


class P2PEconomicsCalculator:
    """
    Calculator for P2P trading economics in the Thai market.
    
    Analyzes the profitability of P2P energy trades considering:
    - Grid buy-back rate (2.20 Baht/kWh)
    - Grid purchase rate (4.4217 Baht/kWh for high tier)
    - TPA wheeling charges (1.50-1.80 Baht/kWh)
    - P2P trading price
    """
    
    def __init__(
        self,
        wheeling_cost_baht_kwh: float = RESIDENTIAL_WHEELING_COST_AVG,
        grid_buyback_rate: float = GRID_BUYBACK_RATE,
        grid_purchase_rate: float = GRID_PURCHASE_RATE_HIGH_TIER,
    ):
        """
        Initialize P2P economics calculator.
        
        Args:
            wheeling_cost_baht_kwh: Wheeling cost (TPA charge) per kWh
            grid_buyback_rate: Utility buy-back rate (Baht/kWh)
            grid_purchase_rate: Utility purchase rate for high-tier consumers (Baht/kWh)
        """
        self.wheeling_cost = wheeling_cost_baht_kwh
        self.grid_buyback = grid_buyback_rate
        self.grid_purchase = grid_purchase_rate
        
        # Calculate arbitrage spread
        self.arbitrage_spread = self.grid_purchase - self.grid_buyback
    
    def analyze_trade(
        self,
        energy_kwh: float,
        p2p_price_baht_kwh: float = TYPICAL_P2P_PRICE,
        wheeling_split: float = 0.5,
    ) -> P2PTradeEconomics:
        """
        Analyze economics of a single P2P trade.
        
        Args:
            energy_kwh: Energy amount in kWh
            p2p_price_baht_kwh: P2P trading price per kWh
            wheeling_split: Fraction of wheeling cost paid by seller (0.0-1.0).
                           Default 0.5 means split 50-50.
            
        Returns:
            P2PTradeEconomics with complete analysis
            
        Example:
            >>> calc = P2PEconomicsCalculator()
            >>> economics = calc.analyze_trade(100.0, 3.30)
            >>> print(f"Seller gain: {economics.seller_vs_utility_gain_baht:.2f} Baht")
            >>> print(f"Buyer savings: {economics.buyer_vs_utility_savings_baht:.2f} Baht")
        """
        # Split wheeling cost between seller and buyer
        seller_wheeling_fraction = wheeling_split
        buyer_wheeling_fraction = 1 - wheeling_split
        
        # Seller economics
        seller_revenue = energy_kwh * p2p_price_baht_kwh
        seller_wheeling = energy_kwh * self.wheeling_cost * seller_wheeling_fraction
        seller_net = seller_revenue - seller_wheeling
        seller_utility_revenue = energy_kwh * self.grid_buyback
        seller_gain = seller_net - seller_utility_revenue
        
        # Buyer economics
        buyer_energy_cost = energy_kwh * p2p_price_baht_kwh
        buyer_wheeling = energy_kwh * self.wheeling_cost * buyer_wheeling_fraction
        buyer_total = buyer_energy_cost + buyer_wheeling
        buyer_utility_cost = energy_kwh * self.grid_purchase
        buyer_savings = buyer_utility_cost - buyer_total
        
        # Grid economics
        total_welfare = seller_gain + buyer_savings
        grid_revenue = seller_wheeling + buyer_wheeling
        
        return P2PTradeEconomics(
            energy_kwh=energy_kwh,
            p2p_price_baht_kwh=p2p_price_baht_kwh,
            wheeling_cost_baht_kwh=self.wheeling_cost,
            seller_revenue_baht=seller_revenue,
            seller_net_baht=seller_net,
            seller_vs_utility_gain_baht=seller_gain,
            buyer_cost_baht=buyer_energy_cost,
            buyer_total_baht=buyer_total,
            buyer_vs_utility_savings_baht=buyer_savings,
            total_welfare_gain_baht=total_welfare,
            grid_wheeling_revenue_baht=grid_revenue,
            is_profitable_for_seller=seller_gain > 0,
            is_profitable_for_buyer=buyer_savings > 0,
            is_mutually_beneficial=seller_gain > 0 and buyer_savings > 0,
        )
    
    def find_optimal_p2p_price(
        self,
        energy_kwh: float = 100.0,
        wheeling_split: float = 0.5,
    ) -> Dict[str, float]:
        """
        Find the optimal P2P price that maximizes mutual benefit.
        
        The optimal price is where seller gain equals buyer savings,
        maximizing the perceived fairness of the trade.
        
        Args:
            energy_kwh: Reference energy amount for calculations
            wheeling_split: Fraction of wheeling cost paid by seller
            
        Returns:
            Dictionary with optimal price and economics
        """
        # Calculate effective wheeling for each party
        seller_wheeling = self.wheeling_cost * wheeling_split
        buyer_wheeling = self.wheeling_cost * (1 - wheeling_split)
        
        # Seller minimum price (must beat grid buyback + seller wheeling)
        seller_min_price = self.grid_buyback + seller_wheeling
        
        # Buyer maximum price (must beat grid purchase - buyer wheeling)
        buyer_max_price = self.grid_purchase - buyer_wheeling
        
        if seller_min_price > buyer_max_price:
            # No mutually beneficial price exists
            return {
                "optimal_price_baht_kwh": None,
                "is_feasible": False,
                "seller_min_price": seller_min_price,
                "buyer_max_price": buyer_max_price,
                "reason": "Wheeling cost too high for mutually beneficial trade",
            }
        
        # Optimal price is midpoint
        optimal_price = (seller_min_price + buyer_max_price) / 2
        
        # Analyze at optimal price
        economics = self.analyze_trade(energy_kwh, optimal_price, wheeling_split)
        
        return {
            "optimal_price_baht_kwh": optimal_price,
            "is_feasible": True,
            "seller_min_price_baht_kwh": seller_min_price,
            "buyer_max_price_baht_kwh": buyer_max_price,
            "price_range_baht_kwh": buyer_max_price - seller_min_price,
            "seller_gain_baht": economics.seller_vs_utility_gain_baht,
            "buyer_savings_baht": economics.buyer_vs_utility_savings_baht,
            "total_welfare_baht": economics.total_welfare_gain_baht,
            "energy_kwh": energy_kwh,
        }
    
    def calculate_tpa_breakdown(
        self,
        energy_kwh: float,
    ) -> TPAWheelingBreakdown:
        """
        Calculate detailed TPA wheeling charge breakdown.
        
        Args:
            energy_kwh: Energy amount in kWh
            
        Returns:
            TPAWheelingBreakdown with component details
        """
        components = []
        total = 0.0
        
        for charge in TPA_CHARGES:
            charge_total = energy_kwh * charge.rate_baht_per_kwh
            components.append({
                "name": charge.name,
                "rate_baht_kwh": charge.rate_baht_per_kwh,
                "total_baht": charge_total,
                "is_variable": charge.is_variable,
            })
            total += charge_total
        
        return TPAWheelingBreakdown(
            components=components,
            total_wheeling_baht=total,
            total_wheeling_per_kwh=total / energy_kwh if energy_kwh > 0 else 0,
        )
    
    def sensitivity_analysis(
        self,
        energy_kwh: float = 100.0,
        price_range: Tuple[float, float, float] = (2.5, 4.0, 0.1),
        wheeling_split: float = 0.5,
    ) -> List[Dict]:
        """
        Perform sensitivity analysis on P2P price.
        
        Args:
            energy_kwh: Energy amount for analysis
            price_range: (min_price, max_price, step) in Baht/kWh
            wheeling_split: Fraction of wheeling cost paid by seller
            
        Returns:
            List of analysis results for each price point
        """
        min_price, max_price, step = price_range
        results = []
        
        current_price = min_price
        while current_price <= max_price + 1e-6:  # Epsilon for float comparison
            economics = self.analyze_trade(energy_kwh, current_price, wheeling_split)
            results.append({
                "price_baht_kwh": current_price,
                "seller_gain_baht": economics.seller_vs_utility_gain_baht,
                "buyer_savings_baht": economics.buyer_vs_utility_savings_baht,
                "total_welfare_baht": economics.total_welfare_gain_baht,
                "mutually_beneficial": economics.is_mutually_beneficial,
            })
            current_price += step
        
        return results


# ============================================================================
# Solar ROI Calculator with Royal Decree No. 805
# ============================================================================

@dataclass
class SolarROIResult:
    """Complete ROI analysis for a solar installation."""
    # System specifications
    capacity_kwp: float
    installation_cost_baht: float
    annual_generation_kwh: float
    
    # Financial metrics
    annual_savings_baht: float
    annual_p2p_revenue_baht: float
    total_annual_benefit_baht: float
    
    # Tax incentive (Royal Decree No. 805)
    tax_deduction_baht: float
    tax_savings_baht: float  # Based on tax bracket
    effective_installation_cost_baht: float
    
    # Payback analysis
    simple_payback_years: float
    roi_percent: float
    
    # 25-year lifetime analysis
    lifetime_savings_baht: float
    lifetime_revenue_baht: float
    lifetime_net_benefit_baht: float


@dataclass
class SolarBenchmarkComparison:
    """Comparison against industry benchmarks."""
    system_capacity_kwp: float
    user_cost_baht: float
    benchmark_cost_range_baht: Tuple[float, float]
    is_competitive: bool
    benchmark_payback_range_years: Tuple[float, float]
    user_payback_years: float


class SolarROICalculator:
    """
    Calculator for solar rooftop ROI with Thai tax incentives.
    
    Incorporates Royal Decree No. 805 tax deductions:
    - Up to 200,000 Baht deduction
    - For systems up to 10 kWp
    - Valid for installations 2026-03-03 to 2028-12-31
    """
    
    def __init__(
        self,
        grid_purchase_rate: float = GRID_PURCHASE_RATE_HIGH_TIER,
        grid_buyback_rate: float = GRID_BUYBACK_RATE,
        p2p_price: float = TYPICAL_P2P_PRICE,
        wheeling_cost: float = RESIDENTIAL_WHEELING_COST_AVG,
        system_lifetime_years: int = 25,
    ):
        """
        Initialize solar ROI calculator.
        
        Args:
            grid_purchase_rate: Grid electricity purchase rate (Baht/kWh)
            grid_buyback_rate: Grid feed-in tariff (Baht/kWh)
            p2p_price: P2P selling price (Baht/kWh)
            wheeling_cost: Wheeling cost for P2P (Baht/kWh)
            system_lifetime_years: Expected system lifetime
        """
        self.grid_rate = grid_purchase_rate
        self.buyback_rate = grid_buyback_rate
        self.p2p_price = p2p_price
        self.wheeling_cost = wheeling_cost
        self.lifetime_years = system_lifetime_years
        
        # P2P net price (after wheeling)
        self.p2p_net = p2p_price - wheeling_cost
    
    def calculate_roi(
        self,
        capacity_kwp: float,
        installation_cost_baht: float,
        annual_generation_kwh: float,
        self_consumption_ratio: float = 0.3,
        tax_bracket_percent: float = 20.0,
    ) -> SolarROIResult:
        """
        Calculate complete ROI analysis for a solar installation.
        
        Args:
            capacity_kwp: System capacity in kWp
            installation_cost_baht: Total installation cost (including VAT)
            annual_generation_kwh: Expected annual generation in kWh
            self_consumption_ratio: Ratio of generation self-consumed (0.0-1.0)
            tax_bracket_percent: Income tax bracket percentage
            
        Returns:
            SolarROIResult with complete financial analysis
            
        Example:
            >>> calc = SolarROICalculator()
            >>> result = calc.calculate_roi(
            ...     capacity_kwp=5.0,
            ...     installation_cost_baht=175_000,
            ...     annual_generation_kwh=7_500,
            ...     self_consumption_ratio=0.4,
            ...     tax_bracket_percent=20.0,
            ... )
            >>> print(f"Payback: {result.simple_payback_years:.1f} years")
            >>> print(f"Tax savings: {result.tax_savings_baht:.0f} Baht")
        """
        # Split generation between self-consumption and export
        self_consumption_kwh = annual_generation_kwh * self_consumption_ratio
        export_kwh = annual_generation_kwh * (1 - self_consumption_ratio)
        
        # Assume 50% of export goes to P2P, 50% to grid
        p2p_export_kwh = export_kwh * 0.5
        grid_export_kwh = export_kwh * 0.5
        
        # Annual savings from self-consumption (avoided grid purchase)
        annual_savings = self_consumption_kwh * self.grid_rate
        
        # Annual revenue from P2P sales (net of wheeling)
        p2p_revenue = p2p_export_kwh * self.p2p_net
        
        # Annual revenue from grid feed-in
        grid_revenue = grid_export_kwh * self.buyback_rate
        
        # Total annual benefit
        total_annual_benefit = annual_savings + p2p_revenue + grid_revenue
        
        # Calculate tax incentive (Royal Decree No. 805)
        tax_deduction = min(installation_cost_baht, SOLAR_TAX_INCENTIVE.max_deduction_baht)
        tax_savings = tax_deduction * (tax_bracket_percent / 100)
        
        # Effective installation cost after tax savings
        effective_cost = installation_cost_baht - tax_savings
        
        # Simple payback period
        payback_years = effective_cost / total_annual_benefit if total_annual_benefit > 0 else float('inf')
        
        # ROI percentage (annual return on investment)
        roi_percent = (total_annual_benefit / effective_cost * 100) if effective_cost > 0 else 0
        
        # Lifetime analysis (25 years)
        lifetime_savings = annual_savings * self.lifetime_years
        lifetime_revenue = (p2p_revenue + grid_revenue) * self.lifetime_years
        lifetime_net = (lifetime_savings + lifetime_revenue) - installation_cost_baht
        
        return SolarROIResult(
            capacity_kwp=capacity_kwp,
            installation_cost_baht=installation_cost_baht,
            annual_generation_kwh=annual_generation_kwh,
            annual_savings_baht=annual_savings,
            annual_p2p_revenue_baht=p2p_revenue,
            total_annual_benefit_baht=total_annual_benefit,
            tax_deduction_baht=tax_deduction,
            tax_savings_baht=tax_savings,
            effective_installation_cost_baht=effective_cost,
            simple_payback_years=payback_years,
            roi_percent=roi_percent,
            lifetime_savings_baht=lifetime_savings,
            lifetime_revenue_baht=lifetime_revenue,
            lifetime_net_benefit_baht=lifetime_net,
        )
    
    def compare_with_benchmark(
        self,
        capacity_kwp: float,
        installation_cost_baht: float,
    ) -> SolarBenchmarkComparison:
        """
        Compare installation cost with industry benchmarks.
        
        Args:
            capacity_kwp: System capacity in kWp
            installation_cost_baht: Quoted installation cost
            
        Returns:
            SolarBenchmarkComparison with competitive analysis
        """
        # Find closest benchmark
        closest_benchmark: Optional[SolarSystemBenchmark] = None
        min_diff = float('inf')
        
        for benchmark in SOLAR_BENCHMARKS:
            if abs(benchmark.capacity_kwp - capacity_kwp) < min_diff:
                min_diff = abs(benchmark.capacity_kwp - capacity_kwp)
                closest_benchmark = benchmark
        
        if closest_benchmark is None:
            return SolarBenchmarkComparison(
                system_capacity_kwp=capacity_kwp,
                user_cost_baht=installation_cost_baht,
                benchmark_cost_range_baht=(0, 0),
                is_competitive=False,
                benchmark_payback_range_years=(0, 0),
                user_payback_years=float('inf'),
            )
        
        # Check if cost is competitive
        is_competitive = (
            closest_benchmark.cost_min_baht 
            <= installation_cost_baht 
            <= closest_benchmark.cost_max_baht
        )
        
        # Calculate user payback
        roi_result = self.calculate_roi(
            capacity_kwp=capacity_kwp,
            installation_cost_baht=installation_cost_baht,
            annual_generation_kwh=(
                closest_benchmark.annual_generation_min_kwh 
                + closest_benchmark.annual_generation_max_kwh
            ) / 2,
        )
        
        return SolarBenchmarkComparison(
            system_capacity_kwp=capacity_kwp,
            user_cost_baht=installation_cost_baht,
            benchmark_cost_range_baht=(
                closest_benchmark.cost_min_baht,
                closest_benchmark.cost_max_baht,
            ),
            is_competitive=is_competitive,
            benchmark_payback_range_years=(
                closest_benchmark.payback_min_years,
                closest_benchmark.payback_max_years,
            ),
            user_payback_years=roi_result.simple_payback_years,
        )
    
    def generate_financial_projection(
        self,
        capacity_kwp: float,
        installation_cost_baht: float,
        annual_generation_kwh: float,
        self_consumption_ratio: float = 0.3,
        tax_bracket_percent: float = 20.0,
        degradation_rate_percent: float = 0.5,
    ) -> List[Dict]:
        """
        Generate year-by-year financial projection.
        
        Args:
            capacity_kwp: System capacity in kWp
            installation_cost_baht: Total installation cost
            annual_generation_kwh: First year generation
            self_consumption_ratio: Ratio self-consumed
            tax_bracket_percent: Tax bracket
            degradation_rate_percent: Annual panel degradation
            
        Returns:
            List of yearly projections (25 years)
        """
        projections = []
        cumulative_benefit = 0.0
        
        # First year calculation
        first_year = self.calculate_roi(
            capacity_kwp=capacity_kwp,
            installation_cost_baht=installation_cost_baht,
            annual_generation_kwh=annual_generation_kwh,
            self_consumption_ratio=self_consumption_ratio,
            tax_bracket_percent=tax_bracket_percent,
        )
        
        # Year 0: Installation
        projections.append({
            "year": 0,
            "generation_kwh": 0,
            "annual_benefit_baht": 0,
            "cumulative_benefit_baht": -installation_cost_baht,
            "tax_savings_baht": first_year.tax_savings_baht,
            "net_cash_flow_baht": -installation_cost_baht + first_year.tax_savings_baht,
        })
        
        # Years 1-25: Operation
        for year in range(1, self.lifetime_years + 1):
            # Apply degradation
            degradation_factor = (1 - degradation_rate_percent / 100) ** year
            year_generation = annual_generation_kwh * degradation_factor
            
            # Recalculate for this year (no tax savings after year 1)
            year_roi = self.calculate_roi(
                capacity_kwp=capacity_kwp,
                installation_cost_baht=0,  # No cost in subsequent years
                annual_generation_kwh=year_generation,
                self_consumption_ratio=self_consumption_ratio,
                tax_bracket_percent=0,  # No tax deduction after first year
            )
            
            cumulative_benefit += year_roi.total_annual_benefit_baht
            
            projections.append({
                "year": year,
                "generation_kwh": round(year_generation, 0),
                "annual_benefit_baht": round(year_roi.total_annual_benefit_baht, 2),
                "cumulative_benefit_baht": round(cumulative_benefit - installation_cost_baht, 2),
                "tax_savings_baht": 0,
                "net_cash_flow_baht": year_roi.total_annual_benefit_baht,
                "payback_achieved": cumulative_benefit >= installation_cost_baht,
            })
        
        return projections


# ============================================================================
# Utility Jurisdiction Helper
# ============================================================================

def detect_utility_provider(
    province: str,
    district: Optional[str] = None,
) -> UtilityProvider:
    """
    Detect utility provider based on location.
    
    Args:
        province: Province name
        district: District name (optional, for more accurate detection)
        
    Returns:
        UtilityProvider (MEA or PEA)
        
    Example:
        >>> provider = detect_utility_provider("Bangkok")
        >>> assert provider == UtilityProvider.MEA
        
        >>> provider = detect_utility_provider("Chiang Mai")
        >>> assert provider == UtilityProvider.PEA
    """
    # MEA service areas
    mea_areas = ["Bangkok", "Nonthaburi", "Samut Prakan"]
    
    # Normalize province name
    province_normalized = province.strip().title()
    
    if province_normalized in mea_areas:
        return UtilityProvider.MEA
    else:
        return UtilityProvider.PEA


def get_utility_info(provider: UtilityProvider) -> Dict:
    """
    Get detailed utility provider information.
    
    Args:
        provider: UtilityProvider enum
        
    Returns:
        Dictionary with utility information
    """
    jurisdiction = UTILITY_JURISDICTIONS.get(provider)
    
    if jurisdiction is None:
        return {"error": f"Unknown utility provider: {provider}"}
    
    return {
        "provider": jurisdiction.provider.value,
        "service_areas": jurisdiction.service_areas,
        "consumer_profile": jurisdiction.consumer_profile,
        "grid_complexity": jurisdiction.grid_complexity,
        "net_metering_active": jurisdiction.net_metering_active,
        "primary_challenge": jurisdiction.primary_challenge,
    }
