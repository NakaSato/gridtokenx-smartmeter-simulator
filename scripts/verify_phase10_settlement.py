import logging
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from smart_meter_simulator.core.settlement import SettlementEngine
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.config import SimulatorConfig as Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def verify_settlement():
    logger.info("Starting Phase 10 Settlement Verification...")
    
    settlement = SettlementEngine()
    
    # Define Constants
    P2P_PRICE = 0.20
    AMOUNT_KWH = 5.0
    GRID_FEED_IN = Config.GRID_FEED_IN_RATE
    GRID_PURCHASE = Config.GRID_PURCHASE_RATE
    
    logger.info(f"Tariffs: Grid Buy={GRID_PURCHASE}, Grid Sell={GRID_FEED_IN}, P2P={P2P_PRICE}")
    
    # Scenario:
    # Seller: Surplus 8.0, Selling 5.0 P2P. Residual 3.0 to Grid.
    # Buyer: Deficit 10.0, Buying 5.0 P2P. Residual 5.0 from Grid.
    
    seller_id = "SELLER_01"
    buyer_id = "BUYER_01"
    timestamp = datetime.now()
    
    # 1. Readings
    readings = [
        EnergyReading(
            meter_id=seller_id,
            timestamp=timestamp,
            energy_generated=10, energy_consumed=2,
            surplus_energy=8.0, deficit_energy=0.0,
            battery_level=50, location="Loc A", meter_type="Solar_Prosumer", user_type="Res"
        ),
        EnergyReading(
            meter_id=buyer_id,
            timestamp=timestamp,
            energy_generated=0, energy_consumed=10,
            surplus_energy=0.0, deficit_energy=10.0,
            battery_level=0, location="Loc B", meter_type="Consumer", user_type="Res"
        )
    ]
    
    # 2. Market Results
    market_results = {
        "trades": [
            {
                "buyer": buyer_id,
                "seller": seller_id,
                "amount": AMOUNT_KWH,
                "price": P2P_PRICE
            }
        ]
    }
    
    logger.info("Processing Interval...")
    settlement.process_interval(timestamp, readings, market_results)
    
    # 3. Validation
    # Seller Account
    acc_s = settlement.get_account(seller_id)
    expected_p2p_rev = AMOUNT_KWH * P2P_PRICE # 5 * 0.20 = 1.0
    expected_grid_rev = (8.0 - AMOUNT_KWH) * GRID_FEED_IN # 3 * 0.12 = 0.36
    expected_balance_s = expected_p2p_rev + expected_grid_rev # 1.36
    
    assert acc_s.p2p_sell_kwh == AMOUNT_KWH
    assert abs(acc_s.p2p_revenue - expected_p2p_rev) < 1e-4
    assert abs(acc_s.grid_export_kwh - 3.0) < 1e-4
    assert abs(acc_s.grid_revenue - expected_grid_rev) < 1e-4
    assert abs(acc_s.balance - expected_balance_s) < 1e-4
    logger.info(f"✅ Seller Verified: Bal={acc_s.balance:.4f}, P2P_Rev={acc_s.p2p_revenue}, Grid_Rev={acc_s.grid_revenue}")
    
    # Buyer Account
    acc_b = settlement.get_account(buyer_id)
    expected_p2p_cost = AMOUNT_KWH * P2P_PRICE # 1.0
    expected_grid_cost = (10.0 - AMOUNT_KWH) * GRID_PURCHASE # 5 * 0.28 = 1.4
    expected_balance_b = -(expected_p2p_cost + expected_grid_cost) # -2.4
    
    assert acc_b.p2p_buy_kwh == AMOUNT_KWH
    assert abs(acc_b.p2p_cost - expected_p2p_cost) < 1e-4
    assert abs(acc_b.grid_import_kwh - 5.0) < 1e-4
    assert abs(acc_b.grid_cost - expected_grid_cost) < 1e-4
    assert abs(acc_b.balance - expected_balance_b) < 1e-4
    logger.info(f"✅ Buyer Verified: Bal={acc_b.balance:.4f}, P2P_Cost={acc_b.p2p_cost}, Grid_Cost={acc_b.grid_cost}")
    
    # 4. Generate Bill
    bill_s = settlement.generate_bill(seller_id)
    logger.info(f"Bill Generated for Seller: Net {bill_s.total_bill:.4f}")
    assert abs(bill_s.total_bill - (-1.36)) < 1e-4 # Bill uses Cost - Revenue. So Revenue is negative cost?
    # Let's check calculation in settlement.py:
    # total_bill=(acc.grid_cost + acc.p2p_cost) - (acc.grid_revenue + acc.p2p_revenue)
    # Seller: Cost=0, Rev=1.36. Bill = -1.36 (Credit). Correct.
    
    bill_b = settlement.generate_bill(buyer_id)
    logger.info(f"Bill Generated for Buyer: Net {bill_b.total_bill:.4f}")
    assert abs(bill_b.total_bill - 2.4) < 1e-4 # Cost=2.4. Bill = 2.4 (Debit). Correct.
    
    logger.info("----------------------------------------------------------------")
    logger.info("All Settlement verification tests passed! 🚀")

if __name__ == "__main__":
    asyncio.run(verify_settlement())
