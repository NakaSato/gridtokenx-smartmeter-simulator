import pytest
import pandapower as pp
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter, EnergyReading
from smart_meter_simulator.core.market import MarketManager, MarketOrder
from smart_meter_simulator.core.billing import ThaiBillingEngine, TransactionType
from smart_meter_simulator.config.thai_market import TariffCategory, UtilityProvider

@pytest.mark.asyncio
async def test_lmp_end_to_end_settlement():
    """
    Test Phase 21: Locational Marginal Pricing (LMP) end-to-end.
    Verify: Congestion -> Nodal Price -> Market Surcharge -> Billing.
    """
    # 1. Setup Simulation Engine with 2 meters on a radial feeder
    # Bus 0 (Slack) -> Bus 1 (Meter 1) -> Bus 2 (Meter 2)
    net = pp.create_empty_network()
    pp.create_bus(net, 0.4, name="Slack")
    pp.create_bus(net, 0.4, name="Bus 1")
    pp.create_bus(net, 0.4, name="Bus 2")
    pp.create_ext_grid(net, 0)
    # Line 0-1 (Main feeder)
    pp.create_line(net, 0, 1, 0.1, "NAYY 4x50 SE", name="Line 0-1")
    # Line 1-2 (Downstream segment)
    pp.create_line(net, 1, 2, 0.1, "NAYY 4x50 SE", name="Line 1-2")
    
    # Meter 1 at Bus 1
    m1_cfg = {"meter_id": "M1", "bus_id": 1, "latitude": 13.0, "longitude": 100.0, "meter_type": "Residential"}
    meter1 = SmartMeter(m1_cfg)
    
    # Meter 2 at Bus 2
    m2_cfg = {"meter_id": "M2", "bus_id": 2, "latitude": 13.1, "longitude": 100.1, "meter_type": "Residential"}
    meter2 = SmartMeter(m2_cfg)
    
    transport = MagicMock()
    engine = SimulationEngine([meter1, meter2], transport)
    engine.net = net
    engine.meter_to_bus = {"M1": 1, "M2": 2}
    
    # Setup billing engines
    engine.billing_engines = {
        "M1": ThaiBillingEngine("M1", TariffCategory.TYPE_1_1_2, UtilityProvider.PEA),
        "M2": ThaiBillingEngine("M2", TariffCategory.TYPE_1_1_2, UtilityProvider.PEA)
    }
    
    # 2. Simulate Congestion on Line 0-1
    # Penalty threshold is 85%. Let's set it to 95%.
    line_loadings = {0: 95.0, 1: 50.0} 
    
    with patch.object(engine.net, 'res_line') as mock_res:
        mock_res.loading_percent = line_loadings
        
        # Calculate Nodal Prices
        nodal_prices = engine.calculate_nodal_prices()
        
        # Verification: Bus 1 and Bus 2 should have higher prices than Slack
        # Penalty = ((95 - 85) / 15) * (base * 0.5) 
        # Base is 3.78 (from thai_market) + TPA
        assert nodal_prices[1] > nodal_prices[0]
        assert nodal_prices[2] == nodal_prices[1] # Propagation should hit Bus 2 too
        
        # 3. Market Clearing with Congestion
        # M2 (downstream, expensive node) BUYS from M1 (upstream, cheaper node)
        timestamp = datetime(2026, 3, 27, 12, 0)
        
        # Buyer Order (M2)
        bid = MarketOrder(
            meter_id="M2", is_buy=True, amount=10.0, price=5.0, 
            timestamp=timestamp, bus_id=2
        )
        # Seller Order (M1)
        ask = MarketOrder(
            meter_id="M1", is_buy=False, amount=10.0, price=3.0, 
            timestamp=timestamp, bus_id=1
        )
        
        engine.market.submit_order(bid)
        engine.market.submit_order(ask)
        
        # Clear market with nodal prices
        market_results = engine.market.clear_market(timestamp, nodal_prices)
        
        # Verification: Locational Surcharge should be 0 if both are downstream of same bottleneck
        trade = market_results["trades"][0]
        assert trade["locational_surcharge"] == 0
        expected_surcharge = nodal_prices[2] - nodal_prices[1]
        # In this specific case, M2 and M1 both have the same penalty because they are both downstream 
        # of the congested line 0-1.
        # Wait, if Line 0-1 is congested, both Bus 1 and Bus 2 are downstream of the bottleneck.
        # So their prices are equal. Surcharge should be 0 between them.
        
        # Let's try congestion on Line 1-2 instead.
        # Then Bus 2 > Bus 1.
    
    # 4. Try Congestion on Line 1-2 (Segment between M1 and M2)
    line_loadings_2 = {0: 50.0, 1: 95.0} 
    with patch.object(engine.net, 'res_line') as mock_res2:
        mock_res2.loading_percent = line_loadings_2
        nodal_prices_2 = engine.calculate_nodal_prices()
        
        with open("debug_lmp.txt", "w") as f:
            f.write(f"nodal_prices_2 keys: {list(nodal_prices_2.keys())}\n")
            f.write(f"nodal_prices_2 types: {[type(k) for k in nodal_prices_2.keys()]}\n")
            f.write(f"bid.bus_id: {bid.bus_id}, type: {type(bid.bus_id)}\n")
            f.write(f"ask.bus_id: {ask.bus_id}, type: {type(ask.bus_id)}\n")
            f.write(f"nodal_prices_2[1]: {nodal_prices_2[1]}\n")
            f.write(f"nodal_prices_2[2]: {nodal_prices_2[2]}\n")
        
        assert nodal_prices_2[2] > nodal_prices_2[1]
        
        # Re-clear market with fresh orders
        bid2 = MarketOrder(
            meter_id="M2", is_buy=True, amount=10.0, price=5.0, 
            timestamp=timestamp, bus_id=2
        )
        ask2 = MarketOrder(
            meter_id="M1", is_buy=False, amount=10.0, price=3.0, 
            timestamp=timestamp, bus_id=1
        )
        engine.market.submit_order(bid2)
        engine.market.submit_order(ask2)
        market_results_2 = engine.market.clear_market(timestamp, nodal_prices_2)
        
        trade_2 = market_results_2["trades"][0]
        surcharge_2 = trade_2["locational_surcharge"]
        with open("debug_lmp.txt", "a") as f:
            f.write(f"trade_2: {trade_2}\n")
            f.write(f"surcharge_2: {surcharge_2}\n")
        
        assert surcharge_2 > 0
        assert surcharge_2 == pytest.approx(nodal_prices_2[2] - nodal_prices_2[1])
        
        # 5. Verify Billing
        # Process the trade in engine logic (mocked or partial)
        amt, prc = trade_2["amount"], trade_2["price"]
        engine.billing_engines["M2"].add_p2p_purchase(amt, prc, "M1", timestamp, locational_surcharge_baht_kwh=surcharge_2)
        
        # Check last transaction for M2
        last_tx = engine.billing_engines["M2"].transactions[-1]
        assert last_tx.transaction_type == TransactionType.P2P_BUY
        assert last_tx.locational_surcharge_baht > 0
        assert last_tx.total_baht == (amt * prc) + (amt * engine.billing_engines["M2"].wheeling_cost) + (amt * surcharge_2)
        
        print(f"\nLMP Verification Success!")
        print(f"Node 1 Price: {nodal_prices_2[1]:.4f}")
        print(f"Node 2 Price: {nodal_prices_2[2]:.4f}")
        print(f"Locational Surcharge: {surcharge_2:.4f} THB/kWh")
        print(f"Total Surcharge for 10kWh: {last_tx.locational_surcharge_baht:.4f} THB")

if __name__ == "__main__":
    asyncio.run(test_lmp_end_to_end_settlement())
