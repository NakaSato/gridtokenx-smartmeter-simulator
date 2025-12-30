import unittest
from smart_meter_simulator.simulation.quantum_optimizer import QuantumOptimizer

class TestQuantumGridAware(unittest.TestCase):
    def setUp(self):
        # Use classical mode for fast, deterministic testing of the logic
        self.optimizer = QuantumOptimizer(use_quantum=False)
        
    def test_stability_incentive(self):
        """
        Test that a seller in a Low Voltage zone is preferred over a neutral zone,
        even if prices are identical.
        """
        # Scenario: 
        # Zone 1: Low Voltage (0.90 pu) - Needs Generation (Seller)
        # Zone 2: Normal Voltage (1.00 pu) - Neutral
        
        zone_voltages = {
            1: 0.90,
            2: 1.00
        }
        
        # Bids: Buyer in Zone 2 (Neutral)
        bids = [{
            'id': 'buyer_z2',
            'price': 5.0,
            'amount': 10.0,
            'zone': 2
        }]
        
        # Asks: Two identical sellers, one in Zone 1 (Helpful), one in Zone 2 (Neutral)
        asks = [
            {
                'id': 'seller_z1_helpful',
                'price': 4.0,
                'amount': 10.0,
                'zone': 1
            },
            {
                'id': 'seller_z2_neutral',
                'price': 4.0,
                'amount': 10.0,
                'zone': 2
            }
        ]
        
        # Mock Cost Callback (Zero cost to isolate incentive logic)
        def mock_cost(buyer, seller, amount):
            class Cost:
                total_cost = 0
                wheeling_charge = 0
                loss_cost = 0
            return Cost()
            
        matches, meta = self.optimizer.optimize_matches(bids, asks, mock_cost, zone_voltages=zone_voltages)
        
        self.assertTrue(len(matches) > 0)
        matched_seller = matches[0].seller_id
        
        # We expect 'seller_z1_helpful' to be chosen over 'seller_z2_neutral'
        # because Zone 1 has Low Voltage (0.90), so generation there gets a Bonus.
        # This increases Welfare.
        
        print(f"Matched Seller: {matched_seller}")
        self.assertEqual(matched_seller, 'seller_z1_helpful')

if __name__ == '__main__':
    unittest.main()
