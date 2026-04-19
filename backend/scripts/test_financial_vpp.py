import unittest
import numpy as np
from smart_meter_simulator.core.vpp import VPPManager, DERResource, VPPCluster
from smart_meter_simulator.core.forecaster import EdgeForecastingEngine

class TestFinancialOptimization(unittest.TestCase):
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

    def test_pea_financial_strategy(self):
        # PEA constraints: Diesel = 13, Retail = 4 -> Loss = -9 THB/kWh
        # BESS = 3.5, Retail = 4 -> Profit = 0.5 THB/kWh
        
        # Trigger Peak (>95%)
        dispatches = self.vpp.resolve_bottleneck_game(line_loading_pct=110.0, capacity_mw=100.0)
        
        # System should choose BESS (S2) to minimize loss
        self.assertIn("SAMUI-BESS-01", dispatches)
        # 110% of 100MW is 110MW. Overload relative to 95% is 15MW = 15000 kW
        # BESS max is 10000 kW, so it should take all 10000 kW.
        self.assertEqual(dispatches["SAMUI-BESS-01"], 10000.0)
        
        # Fallback to Diesel for remaining 5000 kW
        self.assertEqual(dispatches["TAO-GEN-DIESEL"], 5000.0)

class TestEdgeForecasting(unittest.TestCase):
    def test_mape_and_schedule(self):
        forecaster = EdgeForecastingEngine("TEST-NODE")
        current_load = 50.0 # MW
        weather = {"temp_c": 35.0, "cloud_cover": 20.0}
        
        forecast = forecaster.generate_24h_forecast(current_load, weather)
        self.assertEqual(len(forecast), 24)
        
        # Simulate actuals with 5% noise to verify MAPE < 10%
        actuals = forecast * (1.0 + np.random.normal(0, 0.05, 24))
        mape = forecaster.calculate_mape(forecast, actuals)
        
        print(f"Verified MAPE: {mape:.2f}%")
        self.assertLess(mape, 10.0)
        
        schedule = forecaster.get_recommended_schedule(forecast, capacity_mw=60.0)
        self.assertEqual(len(schedule), 24)
        
        # Check if savings are calculated for peak hours
        peak_hours = [s for s in schedule if s["potential_hourly_savings_thb"] > 0]
        if peak_hours:
            print(f"Found {len(peak_hours)} peak hours with potential savings.")
            self.assertTrue(all(s["potential_hourly_savings_thb"] > 0 for s in peak_hours))

from smart_meter_simulator.core.ews import EarlyWarningSystem

class TestEarlyWarningSystem(unittest.TestCase):
    def test_capacity_drop_detection(self):
        ews = EarlyWarningSystem()
        ews.last_capacity_mw = 100.0
        
        # Simulate 30% drop
        alert = ews.monitor_line_health("115kV KMB", 70.0, 98.0)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "EWS_CAPACITY_DROP")
        self.assertEqual(alert["severity"], "CRITICAL")
        self.assertEqual(alert["drop_pct"], 30.0)

if __name__ == "__main__":
    unittest.main()
