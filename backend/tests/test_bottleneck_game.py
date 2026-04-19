import unittest
from smart_meter_simulator.core.vpp import VPPManager, DERResource, VPPCluster

class TestBottleneckGame(unittest.TestCase):
    def setUp(self):
        self.vpp = VPPManager()
        
        # Setup Samui Cluster with BESS
        self.vpp.clusters["SAMUI-FEEDER"] = VPPCluster(cluster_id="SAMUI-FEEDER")
        self.bess = DERResource(
            meter_id="SAMUI-BESS-01",
            feeder_id="SAMUI-FEEDER",
            type="battery",
            capacity_kw=50000.0,
            capacity_kwh=50000.0,
            current_soc_kwh=25000.0,
            max_discharge_kw=10000.0,
            enabled=True
        )
        self.vpp.clusters["SAMUI-FEEDER"].resources["SAMUI-BESS-01"] = self.bess
        
        # Setup Tao Cluster with Diesel
        self.vpp.clusters["TAO-FEEDER"] = VPPCluster(cluster_id="TAO-FEEDER")
        self.diesel = DERResource(
            meter_id="TAO-GEN-DIESEL",
            feeder_id="TAO-FEEDER",
            type="diesel",
            capacity_kw=10000.0,
            enabled=True
        )
        self.vpp.clusters["TAO-FEEDER"].resources["TAO-GEN-DIESEL"] = self.diesel

    def test_normal_state_no_dispatch(self):
        # Loading < 95% -> NORMAL state
        dispatches = self.vpp.resolve_bottleneck_game(line_loading_pct=80.0, capacity_mw=100.0)
        self.assertEqual(dispatches, {})

    def test_peak_state_bess_priority(self):
        # Loading > 95% -> PEAK state
        # Overload = 100 * (98 - 95) / 100 = 3 MW = 3000 kW
        dispatches = self.vpp.resolve_bottleneck_game(line_loading_pct=98.0, capacity_mw=100.0)
        
        # S2_BESS should be selected
        self.assertIn("SAMUI-BESS-01", dispatches)
        self.assertEqual(dispatches["SAMUI-BESS-01"], 3000.0)
        self.assertNotIn("TAO-GEN-DIESEL", dispatches)

    def test_peak_state_bess_exhaustion_fallback(self):
        # Limit BESS capacity
        self.bess.max_discharge_kw = 1000.0
        
        # Overload = 3000 kW
        dispatches = self.vpp.resolve_bottleneck_game(line_loading_pct=98.0, capacity_mw=100.0)
        
        # Should use all 1000 kW from BESS and fallback to Diesel for 2000 kW
        self.assertEqual(dispatches["SAMUI-BESS-01"], 1000.0)
        self.assertEqual(dispatches["TAO-GEN-DIESEL"], 2000.0)

if __name__ == "__main__":
    unittest.main()
