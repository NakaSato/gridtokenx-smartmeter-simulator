import logging
import random
import hashlib
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenService:
    """
    Simulates the Token Layer for GridTokenX.
    Handles 'wallet' interactions, minting, and settlement transfers
    that would normally happen on the Solana Blockchain.
    """
    
    def __init__(self):
        pass

    def generate_tx_hash(self) -> str:
        """Generates a fake Solana transaction signature."""
        # Base58-like characters
        chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        # 88 chars is typical for Solana signature
        sig = "".join(random.choice(chars) for _ in range(88))
        return sig

    def mint_nrg(self, meter, amount_kwh: float) -> Optional[str]:
        """
        Simulate minting $NRG (Energy Attribute Certificate) for generation.
        Returns tx_hash if successful.
        """
        if amount_kwh <= 0:
            return None
            
        # 1 NRG = 1 kWh (Simulated)
        meter.balance_nrg += amount_kwh
        
        tx_hash = self.generate_tx_hash()
        logger.debug(f"Minted {amount_kwh:.2f} NRG to {meter.wallet_address}. Tx: {tx_hash[:8]}...")
        return tx_hash

    def process_settlement(self, match, buyer_meter, seller_meter) -> str:
        """
        Executes the financial settlement for a matched trade.
        1. Buyer pays GTX to Seller.
        2. Seller transfers NRG to Buyer (Certificate of Origin).
        
        Returns: tx_hash (Simulated)
        """
        # Calculate cost
        total_cost = match.total_cost
        amount = match.amount_kwh
        
        # 1. Payment (GTX)
        # Check balance (if we were strictly enforcing)
        # For simulation, we allow negative or just proceed
        buyer_meter.balance_gtx -= total_cost
        seller_meter.balance_gtx += total_cost
        
        # 2. Certificate Transfer (NRG)
        # Seller should have minted NRG earlier or we mint-on-demand/transfer
        # Usually NRG is minted upon generation. 
        # For simplicity, we assume Seller has it or we mint-and-transfer.
        # Let's assume transfer from Seller's balance.
        # If seller balance is low, we might allow negative (credit) for simulation flow
        seller_meter.balance_nrg -= amount
        buyer_meter.balance_nrg += amount
        
        tx_hash = self.generate_tx_hash()
        
        logger.info(
            f"Settlement Complete: "
            f"{buyer_meter.meter_id} paid {total_cost:.2f} GTX -> {seller_meter.meter_id}. "
            f"Tx: {tx_hash[:8]}..."
        )
        
        return tx_hash
