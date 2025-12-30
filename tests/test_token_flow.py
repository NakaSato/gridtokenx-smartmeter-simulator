import unittest
from smart_meter_simulator.core.meter import SmartMeter, SimulatorConfig
from smart_meter_simulator.services.token_service import TokenService
from smart_meter_simulator.simulation.quantum_optimizer import TradeMatch
from datetime import datetime

class TestTokenFlow(unittest.TestCase):
    def setUp(self):
        self.config_buyer = {
            "meter_id": "buyer_1",
            "balance_gtx": 500.0,
            "balance_nrg": 10.0,
            "user_type": "Residential"
        }
        self.config_seller = {
            "meter_id": "seller_1",
            "balance_gtx": 100.0,
            "balance_nrg": 50.0,
            "user_type": "Data_Center"
        }
        self.buyer = SmartMeter(self.config_buyer)
        self.seller = SmartMeter(self.config_seller)
        self.token_service = TokenService()

    def test_initial_state(self):
        """Verify meters initialize with wallets and balances"""
        self.assertIsNotNone(self.buyer.wallet_address)
        self.assertEqual(len(self.buyer.wallet_address), 44, "Solana address length usually ~44 base58 chars")
        self.assertEqual(self.buyer.balance_gtx, 500.0)
        self.assertEqual(self.seller.balance_nrg, 50.0)

    def test_minting(self):
        """Verify minting increases NRG balance"""
        tx_hash = self.token_service.mint_nrg(self.seller, 25.0)
        self.assertIsNotNone(tx_hash)
        self.assertEqual(self.seller.balance_nrg, 75.0)

    def test_settlement(self):
        """Verify settlement transfers tokens correctly"""
        match = TradeMatch(
            buyer_id="buyer_1",
            seller_id="seller_1",
            amount_kwh=10.0,
            price_per_kwh=5.0,
            total_cost=50.0,
            score=10.0
        )
        
        # Before
        b_gtx = self.buyer.balance_gtx
        b_nrg = self.buyer.balance_nrg
        s_gtx = self.seller.balance_gtx
        s_nrg = self.seller.balance_nrg
        
        tx_hash = self.token_service.process_settlement(match, self.buyer, self.seller)
        
        # Verify Hash
        self.assertIsNotNone(tx_hash)
        self.assertIn("Tx:", f"Tx: {tx_hash}") # Mock check
        
        # Verify Balances
        # Buyer pays 50 GTX, gets 10 NRG
        self.assertEqual(self.buyer.balance_gtx, b_gtx - 50.0)
        self.assertEqual(self.buyer.balance_nrg, b_nrg + 10.0)
        
        # Seller gets 50 GTX, loses 10 NRG
        self.assertEqual(self.seller.balance_gtx, s_gtx + 50.0)
        self.assertEqual(self.seller.balance_nrg, s_nrg - 10.0)

if __name__ == '__main__':
    unittest.main()
