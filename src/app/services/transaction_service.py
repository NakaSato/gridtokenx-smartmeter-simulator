"""
P2P Transaction Service for Energy Trading.

This module calculates the total cost of peer-to-peer energy transactions,
incorporating:
1. Base energy cost
2. Wheeling charges (zone-based transmission fees)
3. Technical loss allocation (receiver pays model)

The service uses the MicrogridZoningService for zone-aware calculations.
"""

import logging
from typing import Optional, Callable
from dataclasses import dataclass

from .zoning_service import (
    MicrogridZoningService,
    INTRA_ZONE_WHEELING,
    ADJACENT_ZONE_WHEELING,
    CROSS_ZONE_WHEELING,
    REMOTE_ZONE_WHEELING,
    INTRA_ZONE_LOSS,
    ADJACENT_ZONE_LOSS,
    CROSS_ZONE_LOSS,
    REMOTE_ZONE_LOSS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Default Pricing Constants (THB)
# =============================================================================
DEFAULT_BASE_PRICE = 4.00  # THB/kWh - Base P2P energy price
GRID_IMPORT_PRICE = 4.50   # THB/kWh - Price when buying from main grid
GRID_EXPORT_PRICE = 2.20   # THB/kWh - FiT rate when selling to main grid


@dataclass
class TransactionCost:
    """
    Complete breakdown of a P2P energy transaction cost.
    
    All monetary values are in THB (Thai Baht).
    
    Attributes:
        energy_cost: Base energy price × amount (THB)
        wheeling_charge: Zone-based transmission fee (THB)
        loss_cost: Monetized energy loss (THB)
        total_cost: Sum of all costs (THB)
        effective_energy: Energy received after losses (kWh)
        loss_factor: Loss percentage applied (decimal)
        loss_allocation: Loss payment model ("RECEIVER" or "SENDER")
        zone_distance_km: Distance between zones (km)
        buyer_zone: Buyer's zone ID
        seller_zone: Seller's zone ID
    """
    energy_cost: float
    wheeling_charge: float
    loss_cost: float
    total_cost: float
    effective_energy: float
    loss_factor: float
    loss_allocation: str
    zone_distance_km: float
    buyer_zone: int
    seller_zone: int
    is_grid_compliant: bool = True
    grid_violation_reason: Optional[str] = None


class P2PTransactionService:
    """
    Service for calculating P2P energy transaction costs.
    
    Implements the "Receiver Pays" loss allocation model where:
    - Seller generates X kWh
    - Buyer pays for X kWh but receives X * (1 - loss_factor) kWh
    - The difference is absorbed as grid losses
    
    This model is recommended for P2P trading as it:
    1. Simplifies metering (seller meter is source of truth)
    2. Incentivizes buyers to prefer local sellers
    3. Matches real-world utility loss allocation practices
    """
    
    def __init__(
        self,
        zoning_service: MicrogridZoningService,
        base_price: float = DEFAULT_BASE_PRICE,
        loss_allocation: str = "RECEIVER",
        grid_validator: Optional[Callable[[], bool]] = None
    ):
        """
        Initialize the transaction service.
        
        Args:
            zoning_service: The microgrid zoning service for zone calculations
            base_price: Default base energy price in THB/kWh
            loss_allocation: "RECEIVER" (buyer absorbs loss) or "SENDER" (seller absorbs loss)
            grid_validator: Optional function that returns True if grid is healthy
        """
        self.zoning = zoning_service
        self.base_price = base_price
        self.loss_allocation = loss_allocation.upper()
        self.grid_validator = grid_validator
        
        if self.loss_allocation not in ["RECEIVER", "SENDER"]:
            logger.warning(f"Invalid loss_allocation '{loss_allocation}', defaulting to RECEIVER")
            self.loss_allocation = "RECEIVER"
    
    def calculate_transaction_cost(
        self,
        buyer_zone: int,
        seller_zone: int,
        energy_amount: float,
        agreed_price: Optional[float] = None
    ) -> TransactionCost:
        """
        Calculate the complete transaction cost for a P2P energy trade.
        
        Example:
            Same Zone (0→0): 10 kWh at 4.00 THB/kWh
            - Energy: 40.00 THB
            - Wheeling: 5.00 THB (0.50 × 10)
            - Loss: 0.40 THB (1% of energy cost)
            - Total: 45.40 THB
            - Effective Energy: 9.90 kWh
        
        Args:
            buyer_zone: Buyer's zone ID
            seller_zone: Seller's zone ID
            energy_amount: Energy being purchased in kWh
            agreed_price: Negotiated price per kWh (defaults to base_price)
            
        Returns:
            TransactionCost with full breakdown
        """
        price = agreed_price if agreed_price is not None else self.base_price
        
        # Get zone-based calculations
        loss_factor = self.zoning.calculate_loss_factor(seller_zone, buyer_zone)
        wheeling_charge = self.zoning.calculate_wheeling_charge(
            from_zone=seller_zone, 
            to_zone=buyer_zone, 
            energy_amount=energy_amount
        )
        zone_distance = self.zoning.calculate_zone_distance(seller_zone, buyer_zone)
        
        logger.debug(f"P2P Cost Calc: {energy_amount:.4f} kWh from {seller_zone} to {buyer_zone}. Rate Wheel: {wheeling_charge/energy_amount if energy_amount > 0 else 0:.2f}, Loss: {loss_factor*100:.1f}%")
        
        # Calculate base energy cost
        energy_cost = energy_amount * price
        
        # Calculate loss cost (monetized physical loss)
        loss_energy = energy_amount * loss_factor
        loss_cost = loss_energy * price
        
        # Calculate effective energy received
        if self.loss_allocation == "RECEIVER":
            # Buyer pays full price but receives less energy
            effective_energy = energy_amount * (1 - loss_factor)
            total_cost = energy_cost + wheeling_charge  # Buyer absorbs inherent loss
        else:
            # Sender absorbs loss - buyer receives full energy
            effective_energy = energy_amount
            total_cost = energy_cost + wheeling_charge + loss_cost
        
        # For transparency, always include loss_cost in breakdown
        # but conceptually it's "absorbed" in the RECEIVER model
        
        # Validate Grid State
        is_compliant = True
        violation_reason = None
        if self.grid_validator:
            try:
                is_compliant = self.grid_validator()
                if not is_compliant:
                    violation_reason = "Voltage or Line Loading Violation Detected"
            except Exception as e:
                logger.error(f"Grid validation failed: {e}")
                is_compliant = False
                violation_reason = "Validator Error"
        
        
        return TransactionCost(
            energy_cost=round(energy_cost, 2),
            wheeling_charge=round(wheeling_charge, 2),
            loss_cost=round(loss_cost, 2),
            total_cost=round(total_cost, 2),
            effective_energy=round(effective_energy, 4),
            loss_factor=loss_factor,
            loss_allocation=self.loss_allocation,
            zone_distance_km=round(zone_distance, 2),
            buyer_zone=buyer_zone,
            seller_zone=seller_zone,
            is_grid_compliant=is_compliant,
            grid_violation_reason=violation_reason
        )
    
    def compare_with_grid(
        self,
        buyer_zone: int,
        seller_zone: int,
        energy_amount: float,
        agreed_price: Optional[float] = None
    ) -> dict:
        """
        Compare P2P transaction cost with grid import/export prices.
        
        This helps users understand the value proposition of P2P trading
        versus traditional grid interactions.
        
        Args:
            buyer_zone: Buyer's zone ID
            seller_zone: Seller's zone ID
            energy_amount: Energy amount in kWh
            agreed_price: Negotiated P2P price per kWh
            
        Returns:
            Comparison dictionary with P2P vs Grid analysis
        """
        p2p = self.calculate_transaction_cost(buyer_zone, seller_zone, energy_amount, agreed_price)
        
        # Grid costs for comparison
        grid_import_cost = energy_amount * GRID_IMPORT_PRICE
        grid_export_value = energy_amount * GRID_EXPORT_PRICE
        
        # Calculate savings/benefits
        buyer_savings = grid_import_cost - p2p.total_cost
        seller_premium = p2p.energy_cost - grid_export_value
        
        return {
            "p2p_transaction": p2p,
            "grid_import_cost": round(grid_import_cost, 2),
            "grid_export_value": round(grid_export_value, 2),
            "buyer_savings_thb": round(buyer_savings, 2),
            "seller_premium_thb": round(seller_premium, 2),
            "is_p2p_beneficial_for_buyer": buyer_savings > 0,
            "is_p2p_beneficial_for_seller": seller_premium > 0,
        }
    
    def get_pricing_summary(self) -> dict:
        """
        Get a summary of all pricing parameters.
        
        Returns:
            Dictionary with all pricing constants and matrices
        """
        return {
            "base_price_thb_kwh": self.base_price,
            "grid_import_price_thb_kwh": GRID_IMPORT_PRICE,
            "grid_export_price_thb_kwh": GRID_EXPORT_PRICE,
            "loss_allocation_model": self.loss_allocation,
            "wheeling_charges": self.zoning.get_wheeling_charge_matrix(),
            "loss_factors": self.zoning.get_loss_factor_matrix(),
        }
