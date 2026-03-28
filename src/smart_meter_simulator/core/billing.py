"""
Thai Billing Engine

Comprehensive billing engine for the Thai electricity market that combines:
- Grid electricity billing (ladder and TOU tariffs)
- P2P trading settlement
- Solar generation accounting
- Fuel Adjustment Charge (Ft)
- TPA wheeling charges

This engine provides the complete financial settlement layer for GridTokenX
operations in the Thai market.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..config.thai_market import (
    TariffCategory,
    UtilityProvider,
    CURRENT_FT_RATE,
    GRID_BUYBACK_RATE,
    TYPICAL_P2P_PRICE,
    RESIDENTIAL_WHEELING_COST_AVG,
)
from .thai_tariff import (
    ThaiTariffCalculator,
    TariffResult,
    compare_tariff_options,
)
from ..utils.thai_calculators import (
    P2PEconomicsCalculator,
    P2PTradeEconomics,
    SolarROICalculator,
    SolarROIResult,
    detect_utility_provider,
)

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Types of energy transactions."""
    GRID_PURCHASE = "grid_purchase"
    GRID_EXPORT = "grid_export"
    P2P_BUY = "p2p_buy"
    P2P_SELL = "p2p_sell"
    SOLAR_SELF_CONSUMPTION = "solar_self_consumption"


@dataclass
class EnergyTransaction:
    """Represents a single energy transaction."""
    timestamp: datetime
    transaction_type: TransactionType
    energy_kwh: float
    price_baht_kwh: float
    total_baht: float
    meter_id: str
    counterparty_id: Optional[str] = None  # For P2P trades
    wheeling_cost_baht: float = 0.0  # For P2P trades
    locational_surcharge_baht: float = 0.0 # For congestion (Phase 21)


@dataclass
class MonthlyBill:
    """Complete monthly bill for a Thai electricity consumer."""
    # Billing period
    billing_month: int
    billing_year: int
    account_id: str
    
    # Grid transactions
    grid_consumption_kwh: float
    grid_consumption_charge_baht: float
    grid_export_kwh: float
    grid_export_credit_baht: float
    
    # P2P transactions
    p2p_purchase_kwh: float
    p2p_purchase_cost_baht: float
    p2p_sales_kwh: float
    p2p_sales_revenue_baht: float
    p2p_wheeling_cost_baht: float
    p2p_locational_surcharge_baht: float
    
    # Solar generation
    solar_generation_kwh: float
    solar_self_consumption_kwh: float
    solar_self_consumption_savings_baht: float
    
    # Tariff details
    tariff_type: str
    energy_charge_baht: float
    ft_charge_baht: float
    service_charge_baht: float
    carbon_saved_kg: float
    
    # Totals
    gross_amount_baht: float
    net_amount_baht: float  # After all credits and P2P
    
    # Breakdown
    breakdown: Dict = field(default_factory=dict)


@dataclass
class BillingSummary:
    """Summary of billing analysis with recommendations."""
    total_grid_cost_baht: float
    total_p2p_savings_baht: float
    total_solar_savings_baht: float
    net_billing_amount_baht: float
    average_cost_per_kwh_baht: float
    carbon_offset_kg: float  # Estimated from solar
    recommendations: List[str]


class ThaiBillingEngine:
    """
    Comprehensive billing engine for Thai electricity market.
    
    Integrates:
    - Grid tariff calculations (ladder and TOU)
    - P2P trading settlement with wheeling charges
    - Solar generation accounting
    - Net billing with feed-in tariff
    
    Example:
        >>> engine = ThaiBillingEngine(
        ...     account_id="TH-2026-001",
        ...     tariff_category=TariffCategory.TYPE_1_1_2,
        ...     utility_provider=UtilityProvider.PEA,
        ... )
        >>> 
        >>> # Add transactions
        >>> engine.add_grid_consumption(100.0, datetime(2026, 3, 21, 10, 0))
        >>> engine.add_solar_generation(50.0, datetime(2026, 3, 21, 12, 0))
        >>> engine.add_p2p_sale(20.0, 3.30, "buyer-123")
        >>> 
        >>> # Generate monthly bill
        >>> bill = engine.generate_monthly_bill(3, 2026)
        >>> print(f"Net amount: {bill.net_amount_baht:.2f} Baht")
    """
    
    def __init__(
        self,
        account_id: str,
        tariff_category: TariffCategory = TariffCategory.TYPE_1_1_2,
        utility_provider: UtilityProvider = UtilityProvider.PEA,
        ft_rate: Optional[float] = None,
        grid_buyback_rate: float = GRID_BUYBACK_RATE,
        p2p_price: float = TYPICAL_P2P_PRICE,
        wheeling_cost: float = RESIDENTIAL_WHEELING_COST_AVG,
    ):
        """
        Initialize the billing engine.
        
        Args:
            account_id: Customer account identifier
            tariff_category: Tariff category (1.1.1, 1.1.2, 1.2, etc.)
            utility_provider: Utility provider (MEA or PEA)
            ft_rate: Fuel adjustment charge rate (None for default)
            grid_buyback_rate: Feed-in tariff rate (Baht/kWh)
            p2p_price: Default P2P trading price (Baht/kWh)
            wheeling_cost: TPA wheeling cost (Baht/kWh)
        """
        self.account_id = account_id
        self.tariff_category = tariff_category
        self.utility_provider = utility_provider
        self.ft_rate = ft_rate if ft_rate is not None else CURRENT_FT_RATE
        self.grid_buyback = grid_buyback_rate
        self.p2p_price = p2p_price
        self.wheeling_cost = wheeling_cost
        
        # Transaction logs
        self.transactions: List[EnergyTransaction] = []
        
        # Initialize calculators
        self.tariff_calculator = ThaiTariffCalculator(
            tariff_category=tariff_category,
            ft_rate=self.ft_rate,
            utility_provider=utility_provider,
        )
        
        self.p2p_calculator = P2PEconomicsCalculator(
            wheeling_cost_baht_kwh=wheeling_cost,
            grid_buyback_rate=grid_buyback_rate,
        )
        
        self.solar_calculator = SolarROICalculator(
            grid_purchase_rate=self._get_grid_rate_for_tariff(),
            grid_buyback_rate=grid_buyback_rate,
            p2p_price=p2p_price,
            wheeling_cost=wheeling_cost,
        )
    
    def _get_grid_rate_for_tariff(self) -> float:
        """Get appropriate grid rate based on tariff category."""
        if self.tariff_category == TariffCategory.TYPE_1_2:
            # TOU average (simplified)
            return 4.20
        return 4.4217  # High tier rate
    
    def add_grid_consumption(
        self,
        energy_kwh: float,
        timestamp: datetime,
    ) -> EnergyTransaction:
        """
        Record grid electricity consumption.
        
        Args:
            energy_kwh: Energy consumed in kWh
            timestamp: Time of consumption
            
        Returns:
            EnergyTransaction record
        """
        # Determine price based on tariff type
        if self.tariff_category in [TariffCategory.TYPE_1_1_1, TariffCategory.TYPE_1_1_2]:
            # For ladder tariff, use average rate (will be calculated precisely in billing)
            price = self.tariff_calculator.calculate_ladder_tariff(100).average_rate
        else:
            # For TOU, get rate for specific time
            from ..config.thai_market import get_tou_period, TOU_RATES
            tou_period = get_tou_period(timestamp.hour, timestamp.weekday() >= 5)
            price = TOU_RATES[tou_period]
        
        transaction = EnergyTransaction(
            timestamp=timestamp,
            transaction_type=TransactionType.GRID_PURCHASE,
            energy_kwh=energy_kwh,
            price_baht_kwh=price,
            total_baht=energy_kwh * price,
            meter_id=self.account_id,
        )
        
        self.transactions.append(transaction)
        return transaction
    
    def add_grid_export(
        self,
        energy_kwh: float,
        timestamp: datetime,
    ) -> EnergyTransaction:
        """
        Record electricity export to grid (feed-in).
        
        Args:
            energy_kwh: Energy exported in kWh
            timestamp: Time of export
            
        Returns:
            EnergyTransaction record
        """
        transaction = EnergyTransaction(
            timestamp=timestamp,
            transaction_type=TransactionType.GRID_EXPORT,
            energy_kwh=energy_kwh,
            price_baht_kwh=self.grid_buyback,
            total_baht=energy_kwh * self.grid_buyback,
            meter_id=self.account_id,
        )
        
        self.transactions.append(transaction)
        return transaction
    
    def add_p2p_purchase(
        self,
        energy_kwh: float,
        price_baht_kwh: float,
        seller_id: str,
        timestamp: datetime,
        locational_surcharge_baht_kwh: float = 0.0,
    ) -> EnergyTransaction:
        """
        Record P2P energy purchase.
        
        Args:
            energy_kwh: Energy purchased in kWh
            price_baht_kwh: P2P price per kWh
            seller_id: Seller account identifier
            timestamp: Time of transaction
            
        Returns:
            EnergyTransaction record
        """
        wheeling = energy_kwh * self.wheeling_cost
        surcharge = energy_kwh * locational_surcharge_baht_kwh
        total = (energy_kwh * price_baht_kwh) + wheeling + surcharge
        
        transaction = EnergyTransaction(
            timestamp=timestamp,
            transaction_type=TransactionType.P2P_BUY,
            energy_kwh=energy_kwh,
            price_baht_kwh=price_baht_kwh,
            total_baht=total,
            meter_id=self.account_id,
            counterparty_id=seller_id,
            wheeling_cost_baht=wheeling,
            locational_surcharge_baht=surcharge,
        )
        
        self.transactions.append(transaction)
        return transaction
    
    def add_p2p_sale(
        self,
        energy_kwh: float,
        price_baht_kwh: float,
        buyer_id: str,
        timestamp: datetime,
    ) -> EnergyTransaction:
        """
        Record P2P energy sale.
        
        Args:
            energy_kwh: Energy sold in kWh
            price_baht_kwh: P2P price per kWh
            buyer_id: Buyer account identifier
            timestamp: Time of transaction
            
        Returns:
            EnergyTransaction record
        """
        wheeling = energy_kwh * self.wheeling_cost
        revenue = (energy_kwh * price_baht_kwh) - wheeling
        
        transaction = EnergyTransaction(
            timestamp=timestamp,
            transaction_type=TransactionType.P2P_SELL,
            energy_kwh=energy_kwh,
            price_baht_kwh=price_baht_kwh,
            total_baht=revenue,
            meter_id=self.account_id,
            counterparty_id=buyer_id,
            wheeling_cost_baht=wheeling,
        )
        
        self.transactions.append(transaction)
        return transaction
    
    def add_solar_generation(
        self,
        energy_kwh: float,
        timestamp: datetime,
        self_consumption_ratio: float = 0.3,
    ) -> Tuple[EnergyTransaction, Optional[EnergyTransaction]]:
        """
        Record solar generation with self-consumption and export split.
        
        Args:
            energy_kwh: Total solar generation in kWh
            timestamp: Time of generation
            self_consumption_ratio: Ratio consumed on-site (0.0-1.0)
            
        Returns:
            Tuple of (self_consumption_transaction, export_transaction)
        """
        self_consumption_kwh = energy_kwh * self_consumption_ratio
        export_kwh = energy_kwh * (1 - self_consumption_ratio)
        
        # Self-consumption transaction (savings, not revenue)
        self_consumption_tx = EnergyTransaction(
            timestamp=timestamp,
            transaction_type=TransactionType.SOLAR_SELF_CONSUMPTION,
            energy_kwh=self_consumption_kwh,
            price_baht_kwh=self._get_grid_rate_for_tariff(),
            total_baht=self_consumption_kwh * self._get_grid_rate_for_tariff(),
            meter_id=self.account_id,
        )
        
        self.transactions.append(self_consumption_tx)
        
        # Export transaction (if any)
        export_tx = None
        if export_kwh > 0:
            export_tx = self.add_grid_export(export_kwh, timestamp)
        
        return self_consumption_tx, export_tx
    
    def generate_monthly_bill(
        self,
        billing_month: int,
        billing_year: int,
    ) -> MonthlyBill:
        """
        Generate comprehensive monthly bill.
        
        Args:
            billing_month: Month (1-12)
            billing_year: Year (e.g., 2026)
            
        Returns:
            MonthlyBill with complete breakdown
        """
        # Filter transactions for billing period
        period_transactions = [
            tx for tx in self.transactions
            if tx.timestamp.month == billing_month and tx.timestamp.year == billing_year
        ]
        
        # Aggregate by transaction type
        grid_consumption = []
        grid_exports = []
        p2p_purchases = []
        p2p_sales = []
        solar_self_consumption = []
        
        for tx in period_transactions:
            if tx.transaction_type == TransactionType.GRID_PURCHASE:
                grid_consumption.append(tx)
            elif tx.transaction_type == TransactionType.GRID_EXPORT:
                grid_exports.append(tx)
            elif tx.transaction_type == TransactionType.P2P_BUY:
                p2p_purchases.append(tx)
            elif tx.transaction_type == TransactionType.P2P_SELL:
                p2p_sales.append(tx)
            elif tx.transaction_type == TransactionType.SOLAR_SELF_CONSUMPTION:
                solar_self_consumption.append(tx)
        
        # Calculate grid consumption charge
        total_grid_consumption = sum(tx.energy_kwh for tx in grid_consumption)
        
        if self.tariff_category in [TariffCategory.TYPE_1_1_1, TariffCategory.TYPE_1_1_2]:
            # Use ladder tariff calculation
            tariff_result = self.tariff_calculator.calculate_ladder_tariff(
                total_grid_consumption
            )
            energy_charge = tariff_result.energy_charge
            ft_charge = tariff_result.ft_charge
            service_charge = tariff_result.service_charge
        else:
            # For TOU, sum individual transaction costs
            energy_charge = sum(tx.total_baht for tx in grid_consumption)
            ft_charge = total_grid_consumption * self.ft_rate
            from ..config.thai_market import SERVICE_CHARGES
            service_charge = SERVICE_CHARGES.get(self.tariff_category, 33.29)
        
        # Grid export credit
        total_grid_export = sum(tx.energy_kwh for tx in grid_exports)
        grid_export_credit = sum(tx.total_baht for tx in grid_exports)
        
        # P2P purchases
        total_p2p_purchase = sum(tx.energy_kwh for tx in p2p_purchases)
        p2p_purchase_cost = sum(tx.total_baht for tx in p2p_purchases)
        p2p_purchase_wheeling = sum(tx.wheeling_cost_baht for tx in p2p_purchases)
        
        # P2P sales
        total_p2p_sales = sum(tx.energy_kwh for tx in p2p_sales)
        p2p_sales_revenue = sum(tx.total_baht for tx in p2p_sales)
        p2p_sales_wheeling = sum(tx.wheeling_cost_baht for tx in p2p_sales)
        
        # Locational surcharges (aggregate from purchases)
        total_p2p_surcharge = sum(tx.locational_surcharge_baht for tx in p2p_purchases)
        
        # Solar self-consumption savings
        total_solar_self = sum(tx.energy_kwh for tx in solar_self_consumption)
        solar_savings = sum(tx.total_baht for tx in solar_self_consumption)
        
        # Calculate Carbon Savings (Phase 22)
        # 0.5 kg CO2 per kWh for local generation/VPP discharge
        carbon_saved = (total_solar_self + total_grid_export + total_p2p_sales) * 0.5
        
        # Calculate totals
        gross_amount = energy_charge + ft_charge + service_charge + p2p_purchase_cost
        credits = grid_export_credit + p2p_sales_revenue + solar_savings
        net_amount = gross_amount - credits
        
        return MonthlyBill(
            billing_month=billing_month,
            billing_year=billing_year,
            account_id=self.account_id,
            grid_consumption_kwh=total_grid_consumption,
            grid_consumption_charge_baht=energy_charge + ft_charge,
            grid_export_kwh=total_grid_export,
            grid_export_credit_baht=grid_export_credit,
            p2p_purchase_kwh=total_p2p_purchase,
            p2p_purchase_cost_baht=p2p_purchase_cost,
            p2p_sales_kwh=total_p2p_sales,
            p2p_sales_revenue_baht=p2p_sales_revenue,
            p2p_wheeling_cost_baht=p2p_purchase_wheeling + p2p_sales_wheeling,
            p2p_locational_surcharge_baht=total_p2p_surcharge,
            solar_generation_kwh=total_solar_self + total_grid_export,
            solar_self_consumption_kwh=total_solar_self,
            solar_self_consumption_savings_baht=solar_savings,
            tariff_type=self.tariff_category.value,
            energy_charge_baht=energy_charge,
            ft_charge_baht=ft_charge,
            service_charge_baht=service_charge,
            carbon_saved_kg=carbon_saved,
            gross_amount_baht=gross_amount,
            net_amount_baht=net_amount,
            breakdown={
                "grid_transactions": len(grid_consumption) + len(grid_exports),
                "p2p_transactions": len(p2p_purchases) + len(p2p_sales),
                "solar_transactions": len(solar_self_consumption),
                "total_transactions": len(period_transactions),
            }
        )
    
    def get_billing_summary(
        self,
        billing_month: int,
        billing_year: int,
    ) -> BillingSummary:
        """
        Generate billing summary with recommendations.
        
        Args:
            billing_month: Month (1-12)
            billing_year: Year
            
        Returns:
            BillingSummary with analysis and recommendations
        """
        bill = self.generate_monthly_bill(billing_month, billing_year)
        
        # Calculate metrics
        total_energy = (
            bill.grid_consumption_kwh 
            + bill.p2p_purchase_kwh 
            + bill.solar_self_consumption_kwh
        )
        
        avg_cost = bill.net_amount_baht / total_energy if total_energy > 0 else 0
        
        # Estimate carbon offset (0.5 kg CO2 per kWh solar)
        carbon_offset = bill.solar_generation_kwh * 0.5
        
        # Generate recommendations
        recommendations = []
        
        if bill.grid_consumption_kwh > 400:
            recommendations.append(
                "High consumption detected (>400 kWh). Consider increasing solar capacity "
                "or optimizing usage patterns."
            )
        
        if bill.p2p_sales_kwh == 0 and bill.solar_generation_kwh > 0:
            recommendations.append(
                "You have solar generation but no P2P sales. Consider joining the P2P "
                "market to earn higher returns than the grid feed-in tariff."
            )
        
        if self.tariff_category in [TariffCategory.TYPE_1_1_1, TariffCategory.TYPE_1_1_2]:
            if bill.grid_consumption_kwh > 150:
                recommendations.append(
                    "Consider switching to TOU tariff (Type 1.2) if you can shift "
                    "consumption to off-peak hours (22:00-09:00 or weekends)."
                )
        
        if bill.p2p_wheeling_cost_baht > 0:
            wheeling_per_kwh = bill.p2p_wheeling_cost_baht / (
                bill.p2p_purchase_kwh + bill.p2p_sales_kwh
            ) if (bill.p2p_purchase_kwh + bill.p2p_sales_kwh) > 0 else 0
            if wheeling_per_kwh > RESIDENTIAL_WHEELING_COST_AVG:
                recommendations.append(
                    "Your average wheeling cost is above the residential average. "
                    "Consider local P2P trades to reduce wheeling charges."
                )
        
        if not recommendations:
            recommendations.append(
                "Your energy portfolio is well-optimized. Continue monitoring for "
                "further savings opportunities."
            )
        
        return BillingSummary(
            total_grid_cost_baht=bill.grid_consumption_charge_baht,
            total_p2p_savings_baht=(
                (bill.grid_buyback_rate - self.p2p_price) * bill.p2p_sales_kwh
                if hasattr(bill, 'grid_buyback_rate') else 0
            ),
            total_solar_savings_baht=bill.solar_self_consumption_savings_baht,
            net_billing_amount_baht=bill.net_amount_baht,
            average_cost_per_kwh_baht=avg_cost,
            carbon_offset_kg=carbon_offset,
            recommendations=recommendations,
        )
    
    def clear_transactions(self):
        """Clear all recorded transactions."""
        self.transactions = []
        logger.info(f"Cleared transactions for account {self.account_id}")
