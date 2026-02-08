import asyncio
import logging
from datetime import datetime, timezone
from smart_meter_simulator.core.forecaster import ForecastingEngine
from smart_meter_simulator.core.optimizer import OptimizationEngine
from smart_meter_simulator.core.market import MarketManager, MarketOrder
from smart_meter_simulator.core.data_source import ProfileDataSource
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_forecasting():
    logger.info("Testing Forecasting Engine...")
    ds = ProfileDataSource()
    forecaster = ForecastingEngine(ds)
    now = datetime.now(timezone.utc)
    
    # Test Solar Forecast
    solar_f = forecaster.forecast_solar(now, horizon_steps=24, weather_forecast=["Sunny"]*24)
    assert len(solar_f) == 24
    assert np.max(solar_f) > 0
    logger.info("✅ Solar forecast generated")
    
    # Test Load Forecast
    load_f = forecaster.forecast_load("AMI_TEST_001", now, horizon_steps=24)
    assert len(load_f) == 24
    logger.info("✅ Load forecast generated")

async def test_optimization():
    logger.info("Testing Optimization Engine...")
    optimizer = OptimizationEngine()
    
    # Test Battery Discharge (Deficit)
    net_f = np.array([-2.0, -2.0, -2.0]) # Deficit
    dispatch = optimizer.optimize_battery_dispatch("M001", 50.0, net_f)
    assert dispatch > 0 # Should discharge
    logger.info(f"✅ Optimization check: Discharge signal {dispatch} kW during deficit")
    
    # Test Battery Charge (Surplus)
    net_f = np.array([3.0, 3.0, 3.0]) # Surplus
    dispatch = optimizer.optimize_battery_dispatch("M001", 30.0, net_f)
    assert dispatch < 0 # Should charge
    logger.info(f"✅ Optimization check: Charge signal {dispatch} kW during surplus")

async def test_market():
    logger.info("Testing Market Manager...")
    market = MarketManager()
    now = datetime.now(timezone.utc)
    
    # Bids (Buyers)
    market.submit_order(MarketOrder("B1", True, 5.0, 0.35, now))
    market.submit_order(MarketOrder("B2", True, 5.0, 0.30, now))
    
    # Asks (Sellers)
    market.submit_order(MarketOrder("S1", False, 4.0, 0.20, now))
    market.submit_order(MarketOrder("S2", False, 10.0, 0.25, now))
    
    results = market.clear_market(now)
    logger.info(f"Market Results: MCP={results['mcp']:.3f}, Cleared={results['volume_cleared']:.2f}")
    
    assert results['volume_cleared'] > 0
    assert 0.20 <= results['mcp'] <= 0.35
    logger.info("✅ Market cleared successfully")

if __name__ == "__main__":
    asyncio.run(test_forecasting())
    asyncio.run(test_optimization())
    asyncio.run(test_market())
    print("\n--- Phase 9 Verification Complete ---")
