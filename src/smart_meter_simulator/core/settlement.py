import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..models.reading import EnergyReading
from ..config import get_config

logger = logging.getLogger(__name__)

@dataclass
class BillingStatement:
    meter_id: str
    period_start: str
    period_end: str
    grid_import_kwh: float
    grid_export_kwh: float
    p2p_buy_kwh: float
    p2p_sell_kwh: float
    grid_cost: float
    grid_revenue: float
    p2p_cost: float
    p2p_revenue: float
    total_bill: float

@dataclass
class MultiTokenAccount:
    """Account tracking multiple currencies in the GridTokenX ecosystem."""
    meter_id: str
    
    # Currency Balances
    thb_balance: float = 0.0    # Thai Baht (Utility/Standard)
    sol_balance: float = 0.1    # Solana (Gas/Blockchain)
    gtnx_balance: float = 0.0   # GridTokenX (Rewards/Governance)
    
    # Accumulators for the current billing period (Internal Energy Stats)
    grid_import_kwh: float = 0.0
    grid_export_kwh: float = 0.0
    p2p_buy_kwh: float = 0.0
    p2p_sell_kwh: float = 0.0
    
    # Financial aggregate (THB based)
    p2p_revenue_thb: float = 0.0
    p2p_cost_thb: float = 0.0
    
    last_update: Optional[datetime] = None

class SettlementEngine:
    """
    Enhanced Multi-Currency Settlement Engine.
    
    Economic Model:
    - THB: Main fiat-peg for grid billing and default P2P price.
    - SOL: Native gas token. Deducted (0.000005) per P2P transaction.
    - GTNX: Green Token. Minted (1 GTNX / 1 kWh) for solar generation.
    """
    
    def __init__(self):
        self.accounts: Dict[str, MultiTokenAccount] = {}
        self.billing_period_start = datetime.now()
        self.sol_gas_fee = 0.000005 # Fixed simulated fee per trade
        
    def get_account(self, meter_id: str) -> MultiTokenAccount:
        if meter_id not in self.accounts:
            self.accounts[meter_id] = MultiTokenAccount(meter_id=meter_id)
        return self.accounts[meter_id]
        
    def process_interval(self, 
                        timestamp: datetime, 
                        readings: List[EnergyReading], 
                        market_result: Dict[str, Any]):
        """
        Process a simulation interval with multi-token economics.
        """
        
        # 1. Process P2P Trades with SOL Gas Fees
        trades = market_result.get("trades", [])
        p2p_volumes = {} # meter_id -> net_p2p_kwh (+buy, -sell)
        
        for trade in trades:
            buyer_id = trade["buyer"]
            seller_id = trade["seller"]
            amount = trade["amount"]
            price = trade["price"]
            cost_thb = amount * price
            
            # Buyer: Pay THB + Pay SOL Gas
            buyer_acc = self.get_account(buyer_id)
            buyer_acc.thb_balance -= cost_thb
            buyer_acc.sol_balance -= self.sol_gas_fee
            buyer_acc.p2p_cost_thb += cost_thb
            buyer_acc.p2p_buy_kwh += amount
            
            # Seller: Receive THB + Pay SOL Gas
            seller_acc = self.get_account(seller_id)
            seller_acc.thb_balance += cost_thb
            seller_acc.sol_balance -= self.sol_gas_fee
            seller_acc.p2p_revenue_thb += cost_thb
            seller_acc.p2p_sell_kwh += amount
            
            # Volumes for physical reconcile
            p2p_volumes[buyer_id] = p2p_volumes.get(buyer_id, 0.0) + amount
            p2p_volumes[seller_id] = p2p_volumes.get(seller_id, 0.0) - amount
            
        # 2. Process Physical Grid & Green Rewards (GTNX)
        for reading in readings:
            meter_id = reading.meter_id
            acc = self.get_account(meter_id)
            
            # Energy Values
            surplus = reading.surplus_energy
            deficit = reading.deficit_energy
            gen = reading.energy_generated
            
            # GTNX MINTING: Reward for EVERY generated Green kWh
            if gen > 0:
                acc.gtnx_balance += gen # 1:1 reward ratio
            
            # P2P Net obtained from trades record
            p2p_net = p2p_volumes.get(meter_id, 0.0)
            
            # Physical Net at Grid Point (Import(+)/Export(-))
            physical_net = deficit - surplus
            financial_grid_flow = physical_net - p2p_net
            
            # Grid Settlement (THB)
            config = get_config()
            if financial_grid_flow > 0:
                cost = financial_grid_flow * config.grid_purchase_rate
                acc.grid_import_kwh += financial_grid_flow
                acc.thb_balance -= cost
            elif financial_grid_flow < 0:
                export_kwh = abs(financial_grid_flow)
                revenue = export_kwh * config.grid_feed_in_rate
                acc.grid_export_kwh += export_kwh
                acc.thb_balance += revenue
                
            acc.last_update = timestamp

    def get_wallet_summary(self, meter_id: str) -> Dict[str, Any]:
        """Expose multi-token balances for API/UI."""
        acc = self.get_account(meter_id)
        return {
            "meter_id": meter_id,
            "balances": {
                "thb": round(acc.thb_balance, 2),
                "sol": round(acc.sol_balance, 8),
                "gtnx": round(acc.gtnx_balance, 4)
            },
            "stats": {
                "grid_import_kwh": acc.grid_import_kwh,
                "grid_export_kwh": acc.grid_export_kwh,
                "p2p_volume_kwh": acc.p2p_buy_kwh + acc.p2p_sell_kwh,
                "green_rewards_earned": acc.gtnx_balance
            },
            "timestamp": acc.last_update.isoformat() if acc.last_update else None
        }

    def generate_bill(self, meter_id: str) -> BillingStatement:
        """Legacy Billing Support (THB focused)."""
        acc = self.get_account(meter_id)
        return BillingStatement(
            meter_id=meter_id,
            period_start=self.billing_period_start.isoformat(),
            period_end=datetime.now().isoformat(),
            grid_import_kwh=acc.grid_import_kwh,
            grid_export_kwh=acc.grid_export_kwh,
            p2p_buy_kwh=acc.p2p_buy_kwh,
            p2p_sell_kwh=acc.p2p_sell_kwh,
            grid_cost=acc.grid_import_kwh * get_config().grid_purchase_rate, # Approx
            grid_revenue=acc.grid_export_kwh * get_config().grid_feed_in_rate,
            p2p_cost=acc.p2p_cost_thb,
            p2p_revenue=acc.p2p_revenue_thb,
            total_bill=acc.thb_balance # Simplified for now
        )
