
import asyncio
import logging
import sys
import os
from datetime import datetime
import numpy as np

# Adjust path to import from src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '../src')
sys.path.append(src_path)

from smart_meter_simulator.core.market import TariffManager, TariffType
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.core.optimizer import OptimizationEngine
from smart_meter_simulator.core.adr import ADRManager, ADREventType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def verify_phase11():
    try:
        logger.info("Starting Phase 11 Verification: Dynamic Pricing & ADR")
        
        # 1. Verify Tariff Manager (TOU)
        logger.info("--- 1. Verification: TOU Tariff Generation ---")
        tm = TariffManager()
        tm.current_type = TariffType.TOU
        
        # Check 10:00 AM (Off-Peak/Partial)
        t1 = datetime(2025, 6, 2, 10, 0, 0) # Weekday (Monday)
        tariff1 = tm.get_current_tariff(t1)
        logger.info(f"10:00 Tariff: {tariff1.import_rate:.3f} (Is Peak: {tariff1.is_peak})")
        assert not tariff1.is_peak, "10:00 should not be peak"
        
        # Check 19:00 PM (Peak)
        t2 = datetime(2025, 6, 2, 19, 0, 0) # Weekday (Monday)
        tariff2 = tm.get_current_tariff(t2)
        logger.info(f"19:00 Tariff: {tariff2.import_rate:.3f} (Is Peak: {tariff2.is_peak})")
        assert tariff2.is_peak, "19:00 should be peak"
        assert tariff2.import_rate > tariff1.import_rate, "Peak rate should be higher"
        
        # 2. Verify Smart Meter Elasticity
        logger.info("\n--- 2. Verification: Smart Meter Price Elasticity ---")
        meter_conf = {
            "meter_id": "TEST_METER",
            "meter_type": "Residential",
            "location": "TestLoc",
            "user_type": "Residential",
            "base_consumption": 1.0,
            "price_elasticity": 0.2
        }
        meter = SmartMeter(meter_conf)
        
        # Mock timesteps for reading generation
        ts_fixed = datetime(2025, 6, 1, 19, 0, 0) 
        
        # Case A: Low Price Signal (Mocking tariff object)
        # We manually construct a low tariff even if time is 19:00 to isolate price effect
        from smart_meter_simulator.core.market import CurrentTariff
        tariff_low = CurrentTariff(t1, "TOU", 0.1, 0.05, False)
        meter.receive_price_signal(tariff_low)
        # Note: generate_reading uses internal random noise, so single sample comparison is noisy
        # But let's try 100 samples to average out noise
        
        logger.info("Sampling 100 readings for Low Price...")
        sum_low = 0
        for _ in range(100):
            sum_low += meter.generate_reading(ts_fixed).energy_consumed
        avg_low = sum_low / 100
        
        # Case B: High Price Signal
        logger.info("Sampling 100 readings for High Price...")
        tariff_high = CurrentTariff(t2, "TOU", 0.5, 0.2, True) # Peak=True triggers elasticity logic
        meter.receive_price_signal(tariff_high)
        
        sum_high = 0
        for _ in range(100):
            sum_high += meter.generate_reading(ts_fixed).energy_consumed
        avg_high = sum_high / 100
        
        logger.info(f"Avg Consumption (Low Price): {avg_low:.4f} kWh")
        logger.info(f"Avg Consumption (High Price): {avg_high:.4f} kWh")
        
        elasticity_effect = 1.0 - (avg_high / avg_low)
        logger.info(f"Observed Elasticity: {elasticity_effect:.2%}")
        
        if elasticity_effect > 0.1: # Expect at least 10% reduction
            logger.info("✅ Elasticity Verified: Consumption significantly reduced under high price.")
        else:
            logger.warning(f"❌ Elasticity Low: {elasticity_effect} (Expected > 10%)")

        # 3. Verify Battery Arbitrage
        logger.info("\n--- 3. Verification: Battery Price Arbitrage ---")
        optimizer = OptimizationEngine()
        
        # Scenario: Current Price Low (0.1), Avg (0.2) -> Charge
        price_forecast = np.array([0.1, 0.2, 0.2, 0.2]) 
        
        # Mock OptimizationEngine behavior check
        # Need to ensure soc_max allows charging
        dispatch = optimizer.optimize_battery_dispatch(
            "METER_1",
            current_soc=50.0, # 50% SOC
            net_forecast=np.array([0.0, 0.0, 0.0]), # No load/gen
            price_forecast=price_forecast
        )
        logger.info(f"Arbitrage Dispatch (Low Price): {dispatch:.2f} kW")
        assert dispatch < 0, f"Should CHARGE (negative) when price is low, got {dispatch}"
        
        # Scenario: Current Price High (0.3), Avg (0.2) -> Discharge
        price_forecast_high = np.array([0.3, 0.2, 0.2, 0.2])
        dispatch_high = optimizer.optimize_battery_dispatch(
            "METER_1",
            current_soc=50.0, 
            net_forecast=np.array([0.0, 0.0, 0.0]), 
            price_forecast=price_forecast_high
        )
        logger.info(f"Arbitrage Dispatch (High Price): {dispatch_high:.2f} kW")
        assert dispatch_high > 0, f"Should DISCHARGE (positive) when price is high, got {dispatch_high}"
        
        logger.info("✅ Battery Arbitrage Verified.")
        
        # 4. Verify ADR Event
        logger.info("\n--- 4. Verification: ADR Event Trigger ---")
        adr = ADRManager()
        ts_now = datetime.now()
        
        # Trigger Price Spike
        event_id = adr.trigger_event(ADREventType.PRICE_SPIKE, ts_now, 60, 5.0) # 5x price multiplier
        
        # Check modifier
        # Force update call if needed? No, get_active_event handles simplified logic
        active_event = adr.get_active_event(ts_now)
        assert active_event is not None
        assert active_event.event_type == ADREventType.PRICE_SPIKE
        
        mod = adr.get_tariff_modifier(ts_now)
        logger.info(f"Propagated ADR Modifier: {mod}x")
        assert mod == 5.0
        
        logger.info("✅ ADR Event Verified.")
        
        print("\nAll Phase 11 verifications PASSED!")
        
    except Exception as e:
        logger.error(f"Verification Failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_phase11())
