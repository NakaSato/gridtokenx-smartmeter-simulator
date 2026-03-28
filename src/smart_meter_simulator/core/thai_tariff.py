"""
Thai Tariff Calculator

Provides calculation functions for Thai electricity tariffs including:
- Progressive ladder tariff calculations (Type 1.1.1 and 1.1.2)
- Time of Use (TOU) tariff calculations (Type 1.2/1.3)
- Fuel Adjustment Charge (Ft) calculations
- Monthly billing with all components

References:
    TOU.md - Analysis of the Thai Residential Electricity Market
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ..config.thai_market import (
    LadderTier,
    TYPE_1_1_1_TIERS,
    TYPE_1_1_2_TIERS,
    SERVICE_CHARGES,
    TOU_RATES,
    TOUPeriod,
    FT_PERIODS,
    CURRENT_FT_RATE,
    CURRENT_BASE_TARIFF,
    CURRENT_TOTAL_TARIFF,
    TariffCategory,
    UtilityProvider,
)

logger = logging.getLogger(__name__)


@dataclass
class TariffResult:
    """Result of a tariff calculation."""
    energy_charge: float  # Base energy charge (Baht)
    ft_charge: float  # Fuel adjustment charge (Baht)
    service_charge: float  # Monthly service charge (Baht)
    total_amount: float  # Total amount (Baht)
    total_kwh: float  # Total consumption (kWh)
    average_rate: float  # Average rate per kWh (Baht/kWh)
    tariff_type: str  # Type of tariff used
    breakdown: dict  # Detailed breakdown


@dataclass
class LadderBillBreakdown:
    """Detailed breakdown of ladder tariff calculation."""
    tier_consumptions: List[Tuple[int, int, float, float]]  # (min, max, kwh, charge)
    total_energy_charge: float


class ThaiTariffCalculator:
    """
    Calculator for Thai residential electricity tariffs.
    
    Supports:
    - Type 1.1.1: Small residential (≤150 kWh/month)
    - Type 1.1.2: Standard residential (>150 kWh/month)
    - Type 1.2/1.3: Time of Use (TOU) tariffs
    """
    
    def __init__(
        self,
        tariff_category: TariffCategory = TariffCategory.TYPE_1_1_2,
        ft_rate: Optional[float] = None,
        utility_provider: UtilityProvider = UtilityProvider.PEA,
    ):
        """
        Initialize the tariff calculator.
        
        Args:
            tariff_category: Tariff category (1.1.1, 1.1.2, 1.2, etc.)
            ft_rate: Fuel adjustment charge rate (Baht/kWh). 
                     If None, uses current default rate.
            utility_provider: Utility provider (MEA or PEA)
        """
        self.tariff_category = tariff_category
        self.ft_rate = ft_rate if ft_rate is not None else CURRENT_FT_RATE
        self.utility_provider = utility_provider
        
        # Select appropriate tiers
        if tariff_category == TariffCategory.TYPE_1_1_1:
            self.tiers = TYPE_1_1_1_TIERS
        elif tariff_category == TariffCategory.TYPE_1_1_2:
            self.tiers = TYPE_1_1_2_TIERS
        else:
            self.tiers = []  # TOU doesn't use ladder tiers
    
    def calculate_ladder_tariff(self, consumption_kwh: float) -> TariffResult:
        """
        Calculate electricity bill using progressive ladder tariff.
        
        Args:
            consumption_kwh: Total consumption in kWh for the billing period
            
        Returns:
            TariffResult with detailed breakdown
            
        Example:
            >>> calc = ThaiTariffCalculator(TariffCategory.TYPE_1_1_2)
            >>> result = calc.calculate_ladder_tariff(450.0)
            >>> print(f"Total: {result.total_amount:.2f} Baht")
        """
        if self.tariff_category not in [TariffCategory.TYPE_1_1_1, TariffCategory.TYPE_1_1_2]:
            raise ValueError(
                f"Ladder tariff only supports TYPE_1_1_1 or TYPE_1_1_2, "
                f"got {self.tariff_category}"
            )
        
        # Calculate energy charge using progressive tiers
        energy_charge, breakdown = self._calculate_progressive_charge(consumption_kwh)
        
        # Calculate Ft charge
        ft_charge = consumption_kwh * self.ft_rate
        
        # Get service charge
        service_charge = SERVICE_CHARGES[self.tariff_category]
        
        # Calculate total
        total_amount = energy_charge + ft_charge + service_charge
        
        # Calculate average rate
        average_rate = total_amount / consumption_kwh if consumption_kwh > 0 else 0.0
        
        return TariffResult(
            energy_charge=energy_charge,
            ft_charge=ft_charge,
            service_charge=service_charge,
            total_amount=total_amount,
            total_kwh=consumption_kwh,
            average_rate=average_rate,
            tariff_type=self.tariff_category.value,
            breakdown={
                "tier_breakdown": breakdown,
                "ft_rate": self.ft_rate,
                "service_charge": service_charge,
            }
        )
    
    def _calculate_progressive_charge(
        self, 
        consumption_kwh: float
    ) -> Tuple[float, LadderBillBreakdown]:
        """
        Calculate charge using progressive ladder tiers.
        
        The Thai ladder tariff is cumulative - each tier applies only to
        consumption within that tier's range.
        
        Args:
            consumption_kwh: Total consumption in kWh
            
        Returns:
            Tuple of (total_charge, breakdown)
        """
        total_charge = 0.0
        tier_consumptions = []
        remaining_kwh = consumption_kwh
        
        for tier in self.tiers:
            if remaining_kwh <= 0:
                break
            
            # Calculate consumption in this tier
            tier_max = tier.max_kwh if tier.max_kwh is not None else float('inf')
            tier_range = tier_max - tier.min_kwh + 1  # +1 for inclusive range
            
            # Consumption in current tier is minimum of:
            # 1. Remaining consumption
            # 2. Tier capacity
            consumption_in_tier = min(remaining_kwh, tier_range)
            
            # Ensure we don't go below the tier minimum
            if tier.min_kwh > 0:
                # Only count consumption above tier minimum
                actual_consumption = max(0, consumption_in_tier)
            else:
                actual_consumption = consumption_in_tier
            
            if actual_consumption > 0:
                charge_for_tier = actual_consumption * tier.rate_baht_per_kwh
                total_charge += charge_for_tier
                tier_consumptions.append((
                    tier.min_kwh,
                    tier.max_kwh if tier.max_kwh is not None else 999_999,
                    actual_consumption,
                    charge_for_tier
                ))
                remaining_kwh -= actual_consumption
        
        breakdown = LadderBillBreakdown(
            tier_consumptions=tier_consumptions,
            total_energy_charge=total_charge
        )
        
        return total_charge, breakdown
    
    def calculate_tou_tariff(
        self,
        consumption_profile: List[Tuple[datetime, float]],
    ) -> TariffResult:
        """
        Calculate electricity bill using Time of Use (TOU) tariff.
        
        Args:
            consumption_profile: List of (timestamp, consumption_kwh) tuples.
                                 Timestamps determine the applicable rate.
                                 
        Returns:
            TariffResult with detailed breakdown
            
        Example:
            >>> calc = ThaiTariffCalculator(TariffCategory.TYPE_1_2)
            >>> profile = [
            ...     (datetime(2026, 3, 21, 10, 0), 5.0),  # On-peak
            ...     (datetime(2026, 3, 21, 23, 0), 3.0),  # Off-peak
            ...     (datetime(2026, 3, 22, 12, 0), 4.0),  # Weekend off-peak
            ... ]
            >>> result = calc.calculate_tou_tariff(profile)
        """
        if self.tariff_category not in [TariffCategory.TYPE_1_2, TariffCategory.TYPE_1_3]:
            raise ValueError(
                f"TOU tariff only supports TYPE_1_2 or TYPE_1_3, "
                f"got {self.tariff_category}"
            )
        
        total_energy_charge = 0.0
        period_consumption = {period: 0.0 for period in TOUPeriod}
        period_charge = {period: 0.0 for period in TOUPeriod}
        
        for timestamp, consumption_kwh in consumption_profile:
            # Determine TOU period
            tou_period = self._get_tou_period(timestamp)
            
            # Get rate for this period
            rate = TOU_RATES[tou_period]
            
            # Calculate charge
            charge = consumption_kwh * rate
            total_energy_charge += charge
            
            # Accumulate for breakdown
            period_consumption[tou_period] += consumption_kwh
            period_charge[tou_period] += charge
        
        # Total consumption
        total_kwh = sum(period_consumption.values())
        
        # Calculate Ft charge
        ft_charge = total_kwh * self.ft_rate
        
        # Get service charge
        service_charge = SERVICE_CHARGES[self.tariff_category]
        
        # Calculate total
        total_amount = total_energy_charge + ft_charge + service_charge
        
        # Calculate average rate
        average_rate = total_amount / total_kwh if total_kwh > 0 else 0.0
        
        return TariffResult(
            energy_charge=total_energy_charge,
            ft_charge=ft_charge,
            service_charge=service_charge,
            total_amount=total_amount,
            total_kwh=total_kwh,
            average_rate=average_rate,
            tariff_type=f"TOU ({self.tariff_category.value})",
            breakdown={
                "period_consumption": {
                    period.value: period_consumption[period]
                    for period in TOUPeriod
                },
                "period_charge": {
                    period.value: period_charge[period]
                    for period in TOUPeriod
                },
                "tou_rates": {
                    period.value: TOU_RATES[period]
                    for period in TOUPeriod
                },
                "ft_rate": self.ft_rate,
                "service_charge": service_charge,
            }
        )
    
    @staticmethod
    def _get_tou_period(timestamp: datetime) -> TOUPeriod:
        """
        Determine TOU period from timestamp.
        
        Thai TOU periods:
        - On-Peak: Monday-Friday, 09:00-22:00
        - Off-Peak: Monday-Friday, 22:00-09:00
        - Off-Peak: Saturday, Sunday, Public Holidays (all day)
        
        Args:
            timestamp: Datetime to classify
            
        Returns:
            TOUPeriod enum value
        """
        # Check if weekend (Saturday=5, Sunday=6)
        is_weekend = timestamp.weekday() >= 5
        
        # TODO: Add public holiday check for Thailand
        # For now, treat weekends as off-peak
        
        if is_weekend:
            return TOUPeriod.OFF_PEAK_WEEKEND
        
        # Weekday - check hour
        hour = timestamp.hour
        
        # On-Peak: 09:00-22:00 (9 AM to 10 PM)
        if 9 <= hour < 22:
            return TOUPeriod.ON_PEAK
        else:
            return TOUPeriod.OFF_PEAK_WEEKDAY
    
    def get_ft_for_date(self, target_date: date) -> float:
        """
        Get the applicable Ft rate for a specific date.
        
        Ft rates change every 4 months (Jan-Apr, May-Aug, Sep-Dec).
        
        Args:
            target_date: Date to get Ft rate for
            
        Returns:
            Ft rate in Baht/kWh
        """
        month = target_date.month
        
        for period in FT_PERIODS:
            if period.start_month <= month <= period.end_month:
                return period.ft_rate_baht
        
        # Default to current rate if not found
        logger.warning(
            f"No Ft period found for month {month}, using default {CURRENT_FT_RATE}"
        )
        return CURRENT_FT_RATE
    
    def calculate_monthly_bill(
        self,
        consumption_kwh: float,
        billing_month: int,
        billing_year: int,
    ) -> TariffResult:
        """
        Calculate monthly bill with automatic Ft rate selection.
        
        Args:
            consumption_kwh: Total monthly consumption in kWh
            billing_month: Month (1-12)
            billing_year: Year (e.g., 2026)
            
        Returns:
            TariffResult with appropriate Ft rate for the billing period
        """
        # Get Ft rate for billing month
        ft_rate = self.get_ft_for_date(date(billing_year, billing_month, 1))
        
        # Create calculator with correct Ft rate
        calculator = ThaiTariffCalculator(
            tariff_category=self.tariff_category,
            ft_rate=ft_rate,
            utility_provider=self.utility_provider,
        )
        
        # Calculate based on tariff type
        if self.tariff_category in [TariffCategory.TYPE_1_1_1, TariffCategory.TYPE_1_1_2]:
            return calculator.calculate_ladder_tariff(consumption_kwh)
        else:
            raise ValueError(
                "For TOU tariffs, use calculate_tou_tariff() with consumption profile"
            )


def compare_tariff_options(
    monthly_consumption_kwh: float,
    tou_profile: Optional[List[Tuple[datetime, float]]] = None,
) -> dict:
    """
    Compare different tariff options for a given consumption pattern.
    
    Args:
        monthly_consumption_kwh: Total monthly consumption for ladder tariffs
        tou_profile: Consumption profile for TOU tariff (if available)
        
    Returns:
        Dictionary with comparison results
        
    Example:
        >>> comparison = compare_tariff_options(
        ...     monthly_consumption_kwh=500.0,
        ...     tou_profile=[...]  # Hourly profile
        ... )
        >>> print(f"Best option: {comparison['recommended']}")
    """
    results = {}
    
    # Calculate Type 1.1.1 (if applicable)
    if monthly_consumption_kwh <= 150:
        calc_111 = ThaiTariffCalculator(TariffCategory.TYPE_1_1_1)
        result_111 = calc_111.calculate_ladder_tariff(monthly_consumption_kwh)
        results["Type 1.1.1"] = result_111.total_amount
    
    # Calculate Type 1.1.2
    calc_112 = ThaiTariffCalculator(TariffCategory.TYPE_1_1_2)
    result_112 = calc_112.calculate_ladder_tariff(monthly_consumption_kwh)
    results["Type 1.1.2"] = result_112.total_amount
    
    # Calculate Type 1.2 (TOU) if profile provided
    if tou_profile:
        calc_12 = ThaiTariffCalculator(TariffCategory.TYPE_1_2)
        result_12 = calc_12.calculate_tou_tariff(tou_profile)
        results["Type 1.2 (TOU)"] = result_12.total_amount
    
    # Find best option
    best_option = min(results, key=results.get)
    best_price = results[best_option]
    
    # Calculate savings vs default (1.1.2)
    default_price = results.get("Type 1.1.2", float('inf'))
    savings = default_price - best_price
    
    return {
        "all_options": results,
        "recommended": best_option,
        "best_price_baht": best_price,
        "default_price_baht": default_price,
        "potential_savings_baht": savings,
        "potential_savings_percent": (savings / default_price * 100) if default_price > 0 else 0,
    }


# ============================================================================
# Convenience Functions
# ============================================================================

def calculate_thai_electricity_bill(
    consumption_kwh: float,
    tariff_type: str = "1.1.2",
    month: int = 3,
    year: int = 2026,
) -> TariffResult:
    """
    Convenience function to calculate Thai electricity bill.
    
    Args:
        consumption_kwh: Monthly consumption in kWh
        tariff_type: Tariff type ("1.1.1", "1.1.2", "1.2")
        month: Billing month (1-12)
        year: Billing year
        
    Returns:
        TariffResult with complete bill breakdown
        
    Example:
        >>> result = calculate_thai_electricity_bill(450.0, "1.1.2", 3, 2026)
        >>> print(f"Total: {result.total_amount:.2f} Baht")
        >>> print(f"Average rate: {result.average_rate:.2f} Baht/kWh")
    """
    # Map tariff type string to enum
    tariff_map = {
        "1.1.1": TariffCategory.TYPE_1_1_1,
        "1.1.2": TariffCategory.TYPE_1_1_2,
        "1.2": TariffCategory.TYPE_1_2,
    }
    
    tariff_category = tariff_map.get(tariff_type, TariffCategory.TYPE_1_1_2)
    
    calculator = ThaiTariffCalculator(
        tariff_category=tariff_category,
    )
    
    if tariff_category in [TariffCategory.TYPE_1_1_1, TariffCategory.TYPE_1_1_2]:
        return calculator.calculate_monthly_bill(
            consumption_kwh=consumption_kwh,
            billing_month=month,
            billing_year=year,
        )
    else:
        raise ValueError(
            "TOU tariffs require a consumption profile. "
            "Use ThaiTariffCalculator.calculate_tou_tariff() directly."
        )
