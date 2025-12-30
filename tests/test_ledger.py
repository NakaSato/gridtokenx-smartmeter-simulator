import unittest
import os
import shutil
from smart_meter_simulator.core.database import DatabaseManager
from smart_meter_simulator.services.ledger_service import LedgerService
from smart_meter_simulator.simulation.quantum_optimizer import TradeMatch

class TestLedgerService(unittest.TestCase):
    def setUp(self):
        # Use a temporary db for testing
        self.db_path = "test_ledger.db"
        self.db = DatabaseManager(self.db_path)
        self.ledger = LedgerService(self.db)
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_record_and_get_transactions(self):
        match = TradeMatch(
            buyer_id="buyer_1",
            seller_id="seller_1",
            amount_kwh=10.0,
            price_per_kwh=5.0,
            total_cost=50.0,
            score=10.0
        )
        
        tx_id = self.ledger.record_match(match, zones=(1, 2))
        self.assertGreater(tx_id, 0)
        
        txs = self.ledger.get_transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["buyer_id"], "buyer_1")
        self.assertEqual(txs[0]["total_cost"], 50.0)
        self.assertEqual(txs[0]["zone_from"], 2) # Seller zone
        self.assertEqual(txs[0]["zone_to"], 1)   # Buyer zone

if __name__ == '__main__':
    unittest.main()
