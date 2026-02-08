import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..models.reading import EnergyReading
from ..config import SimulatorConfig as Config

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
class Account:
    meter_id: str
    balance: float = 0.0
    
    # Accumulators for the current billing period
    # Grid
    grid_import_kwh: float = 0.0
    grid_export_kwh: float = 0.0
    grid_cost: float = 0.0
    grid_revenue: float = 0.0
    
    # P2P
    p2p_buy_kwh: float = 0.0
    p2p_sell_kwh: float = 0.0
    p2p_cost: float = 0.0
    p2p_revenue: float = 0.0
    
    last_update: Optional[datetime] = None

class SettlementEngine:
    """
    Handles financial reconciliation for the microgrid.
    Calculates costs/revenues from:
    1. Grid interaction (Tariffs)
    2. P2P Market Trading (Market Clearing Price)
    """
    
    
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.billing_period_start = datetime.now()
        # No need for last_readings if we assume surplus/deficit are interval values
        # Re-check confirmation: Yes, get_bid_params uses them as interval values.
        
    def get_account(self, meter_id: str) -> Account:
        if meter_id not in self.accounts:
            self.accounts[meter_id] = Account(meter_id=meter_id)
        return self.accounts[meter_id]
        
    def process_interval(self, 
                        timestamp: datetime, 
                        readings: List[EnergyReading], 
                        market_result: Dict[str, Any]):
        """
        Process a simulation interval.
        Updates accounts based on physical readings and market matches.
        """
        
        # 1. Process P2P Trades
        # Market result "trades" list contains dicts: {buyer, seller, amount, price}
        trades = market_result.get("trades", [])
        p2p_volumes = {} # meter_id -> net_p2p_kwh (+buy, -sell) to adjust physical reading
        
        for trade in trades:
            buyer_id = trade["buyer"]
            seller_id = trade["seller"]
            amount = trade["amount"] # kWh
            price = trade["price"]   # Currency/kWh
            cost = amount * price
            
            # Buyer Logic
            buyer_acc = self.get_account(buyer_id)
            buyer_acc.balance -= cost
            buyer_acc.p2p_cost += cost
            buyer_acc.p2p_buy_kwh += amount
            buyer_acc.last_update = timestamp
            
            # Seller Logic
            seller_acc = self.get_account(seller_id)
            seller_acc.balance += cost
            seller_acc.p2p_revenue += cost
            seller_acc.p2p_sell_kwh += amount
            seller_acc.last_update = timestamp
            
            # Track volumes to settle remaining against grid
            p2p_volumes[buyer_id] = p2p_volumes.get(buyer_id, 0.0) + amount
            p2p_volumes[seller_id] = p2p_volumes.get(seller_id, 0.0) - amount
            
            # 2. Process Grid Interaction (Residual)
        for reading in readings:
            meter_id = reading.meter_id
            acc = self.get_account(meter_id)
            
            # Available physical energy for this interval
            # surplus_energy: Excess generation (e.g. Solar > Load)
            # deficit_energy: Unmet load (e.g. Load > Solar)
            net_surplus = reading.surplus_energy
            net_deficit = reading.deficit_energy
            
            # Net P2P flow (+Buy/Import, -Sell/Export) obtained from trades
            p2p_net = p2p_volumes.get(meter_id, 0.0)
            
            # Physical Net at Grid Connection Point (Positive = Import, Negative = Export)
            physical_net = net_deficit - net_surplus
            
            # Financial Net (after backing out P2P virtual flows)
            # If we bought 5kWh P2P, we reduce our Grid Billing Import by 5kWh.
            # If we sold 5kWh P2P, we reduce our Grid Billing Export by 5kWh.
            financial_grid_flow = physical_net - p2p_net
            
            # Grid Settlement
            if financial_grid_flow > 0:
                # Net Import from Grid
                cost = financial_grid_flow * Config.GRID_PURCHASE_RATE
                acc.grid_import_kwh += financial_grid_flow
                acc.grid_cost += cost
                acc.balance -= cost
            else:
                # Net Export to Grid (Feed-in)
                export_kwh = abs(financial_grid_flow)
                revenue = export_kwh * Config.GRID_FEED_IN_RATE
                acc.grid_export_kwh += export_kwh
                acc.grid_revenue += revenue
                acc.balance += revenue
                
            acc.last_update = timestamp

    def generate_bill(self, meter_id: str) -> BillingStatement:
        """Generate a statement for the current period."""
        acc = self.get_account(meter_id)
        return BillingStatement(
            meter_id=meter_id,
            period_start=self.billing_period_start.isoformat(),
            period_end=datetime.now().isoformat(),
            grid_import_kwh=acc.grid_import_kwh,
            grid_export_kwh=acc.grid_export_kwh,
            p2p_buy_kwh=acc.p2p_buy_kwh,
            p2p_sell_kwh=acc.p2p_sell_kwh,
            grid_cost=acc.grid_cost,
            grid_revenue=acc.grid_revenue,
            p2p_cost=acc.p2p_cost,
            p2p_revenue=acc.p2p_revenue,
            total_bill=(acc.grid_cost + acc.p2p_cost) - (acc.grid_revenue + acc.p2p_revenue)
        )
