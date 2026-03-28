import pytest
from datetime import datetime
from smart_meter_simulator.core.settlement import SettlementEngine
from smart_meter_simulator.models.reading import EnergyReading

def test_multi_token_account_initialization():
    engine = SettlementEngine()
    meter_id = "test-meter-1"
    
    acc = engine.get_account(meter_id)
    assert acc.thb_balance == 0.0
    assert acc.sol_balance == 0.1  # Initial simulation bonus
    assert acc.gtnx_balance == 0.0

def test_gtnx_minting_on_generation():
    engine = SettlementEngine()
    meter_id = "test-producer"
    ts = datetime.now()
    
    # 5.5 kWh generation, all surplus
    reading = EnergyReading(
        meter_id=meter_id,
        timestamp=ts,
        energy_generated=5.5,
        energy_consumed=0.0,
        surplus_energy=5.5,
        deficit_energy=0.0,
        location="Test",
        meter_type="prosumer",
        user_type="residential"
    )
    
    # No trades
    engine.process_interval(ts, [reading], {})
    
    acc = engine.get_account(meter_id)
    # GTNX should be minted 1:1 for generation
    assert acc.gtnx_balance == 5.5
    # Grid export (THB)
    assert acc.thb_balance > 0 

def test_sol_gas_fees_on_p2p():
    engine = SettlementEngine()
    seller_id = "seller-1"
    buyer_id = "buyer-1"
    ts = datetime.now()
    
    # Market result with a trade
    market_result = {
        "trades": [
            {
                "buyer": buyer_id,
                "seller": seller_id,
                "amount": 2.0,
                "price": 4.0
            }
        ]
    }
    
    # Empty readings for simplicity
    engine.process_interval(ts, [], market_result)
    
    seller_acc = engine.get_account(seller_id)
    buyer_acc = engine.get_account(buyer_id)
    
    # Both should pay gas fees in SOL (initial 0.1)
    assert seller_acc.sol_balance == 0.1 - 0.000005
    assert buyer_acc.sol_balance == 0.1 - 0.000005
    
    # Financials
    assert seller_acc.thb_balance == 8.0 # 2 * 4
    assert buyer_acc.thb_balance == -8.0

def test_wallet_summary():
    engine = SettlementEngine()
    meter_id = "test-prosumer"
    ts = datetime.now()
    
    reading = EnergyReading(
        meter_id=meter_id,
        timestamp=ts,
        energy_generated=10.0,
        energy_consumed=5.0,
        surplus_energy=5.0,
        deficit_energy=0.0,
        location="Test",
        meter_type="prosumer",
        user_type="residential"
    )
    
    market_result = {
        "trades": [
            {
                "buyer": "other",
                "seller": meter_id,
                "amount": 2.0,
                "price": 4.5
            }
        ]
    }
    
    engine.process_interval(ts, [reading], market_result)
    
    summary = engine.get_wallet_summary(meter_id)
    
    assert summary["balances"]["gtnx"] == 10.0
    assert summary["balances"]["sol"] == 0.1 - 0.000005
    assert summary["stats"]["green_rewards_earned"] == 10.0
