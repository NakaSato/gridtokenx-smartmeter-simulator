
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../src')
sys.path.append(src_dir)

import logging
# Configure logging to see qiskit output if needed
logging.basicConfig(level=logging.INFO)

try:
    from smart_meter_simulator.simulation.quantum_optimizer import QuantumOptimizer
except ImportError as e:
    print(f"ImportError: {e}")
    print("Ensure dependencies are installed and PYTHONPATH is correct.")
    sys.exit(1)

# Mock Callback
def mock_cost_callback(buyer_zone, seller_zone, amount):
    # Retrieve mock transaction cost
    class MockCost:
        def __init__(self, amount):
            self.total_cost = amount * 4.0 # Base price (placeholder)
            self.wheeling_charge = amount * 0.5
            self.loss_cost = amount * 0.1
    return MockCost(amount)

def test_optimization():
    print("Initializing QuantumOptimizer...")
    try:
        optimizer = QuantumOptimizer(use_quantum=True)
    except Exception as e:
        print(f"Failed to init optimizer: {e}")
        return

    bids = [
        {'id': 'b1', 'price': 5.0, 'amount': 10, 'zone': 1},
        {'id': 'b2', 'price': 4.5, 'amount': 15, 'zone': 1},
        {'id': 'b3', 'price': 4.0, 'amount': 20, 'zone': 2},
    ]
    
    asks = [
        {'id': 's1', 'price': 3.0, 'amount': 10, 'zone': 1}, # Spread: 5-3=2. High potential.
        {'id': 's2', 'price': 3.5, 'amount': 10, 'zone': 2},
        {'id': 's3', 'price': 4.2, 'amount': 10, 'zone': 3},
    ]
    
    print("Running optimization...")
    matches, meta = optimizer.optimize_matches(bids, asks, mock_cost_callback)
    
    print("-" * 50)
    print(f"Meta: {meta}")
    print(f"Matches Found: {len(matches)}")
    for m in matches:
        print(f"  {m.buyer_id} -> {m.seller_id}: {m.amount_kwh} kWh @ {m.price_per_kwh:.2f}")
    
    # Validation
    if len(matches) >= 2:
        print("SUCCESS: Matches found using VQE.")
    else:
        print("WARNING: Fewer matches than expected (should be at least b1-s1, b2-s2).")

if __name__ == "__main__":
    test_optimization()
