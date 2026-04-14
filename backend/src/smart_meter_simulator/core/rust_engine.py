"""
Rust-accelerated meter reading generation with Python fallback.

This module provides a transparent interface to the Rust extension module.
If Rust is available (via PyO3), it uses the high-performance implementation.
Otherwise, it falls back to the pure Python implementation.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Rust extension module
USE_RUST_ENGINE = False
rust_engine = None

try:
    from gridtokenx_sim import MeterConfig as RustMeterConfig
    from gridtokenx_sim import generate_readings as rust_generate_readings
    
    USE_RUST_ENGINE = True
    logger.info("✅ Rust acceleration engine loaded")
except ImportError as e:
    logger.warning(f"⚠️  Rust engine not available, using Python fallback: {e}")
    USE_RUST_ENGINE = False


class RustAcceleratedMeter:
    """
    Wrapper that provides Rust-accelerated meter reading generation.
    Maintains compatibility with existing SmartMeter interface.
    """
    
    def __init__(self):
        self._use_rust = USE_RUST_ENGINE
    
    @staticmethod
    def convert_meter_to_rust_config(meter_config: Dict[str, Any]) -> 'RustMeterConfig':
        """Convert Python meter config dict to Rust MeterConfig."""
        if not USE_RUST_ENGINE:
            raise RuntimeError("Rust engine not available")

        meter_type = meter_config.get('meter_type', 'residential')
        is_dc_fast_charger = meter_type == 'DC_Fast_Charger'

        return RustMeterConfig(
            meter_id=meter_config.get('meter_id', 'unknown'),
            meter_type=meter_type,
            has_solar=meter_config.get('has_solar', False),
            has_battery=meter_config.get('has_battery', False),
            solar_capacity=meter_config.get('solar_capacity', 5.0),
            battery_capacity=meter_config.get('battery_capacity', 10.0),
            base_consumption=meter_config.get('base_consumption', 1.0),
            panel_efficiency=meter_config.get('panel_efficiency', 0.18),
            current_battery_level=meter_config.get('current_battery_level', 0.0),
            price_elasticity=meter_config.get('price_elasticity', 0.15),
            accuracy_class=meter_config.get('accuracy_class', 2.0),
            # EV-specific fields
            ev_battery_capacity_kwh=meter_config.get('ev_battery_capacity', 60.0),
            ev_charge_rate_kw=meter_config.get('ev_charge_rate_kw', 7.4),
            ev_v2g_discharge_rate_kw=meter_config.get('ev_v2g_discharge_rate_kw', 5.0),
            ev_v2g_threshold_soc=meter_config.get('ev_v2g_threshold_soc', 0.4),
            is_dc_fast_charger=is_dc_fast_charger,
            connector_count=meter_config.get('connector_count', 4),
            max_station_capacity_kw=meter_config.get('max_station_capacity_kw', 600.0),
        )
    
    @staticmethod
    def generate_readings_batch(
        meters: List[Dict[str, Any]],
        timestamp: datetime,
        weather_factor: float = 1.0,
        interval_seconds: int = 900,
    ) -> List[Dict[str, Any]]:
        """
        Generate readings for a batch of meters using Rust engine.
        
        Args:
            meters: List of meter configuration dictionaries
            timestamp: Simulation timestamp
            weather_factor: Weather impact factor (0.0-1.0)
            interval_seconds: Simulation interval in seconds
            
        Returns:
            List of energy reading dictionaries
        """
        if USE_RUST_ENGINE:
            return RustAcceleratedMeter._generate_with_rust(
                meters, timestamp, weather_factor, interval_seconds
            )
        else:
            return RustAcceleratedMeter._generate_with_python(
                meters, timestamp, weather_factor, interval_seconds
            )
    
    @staticmethod
    def _generate_with_rust(
        meters: List[Dict[str, Any]],
        timestamp: datetime,
        weather_factor: float,
        interval_seconds: int,
    ) -> List[Dict[str, Any]]:
        """Generate readings using Rust extension (10-50x faster)."""
        hour = timestamp.hour + timestamp.minute / 60.0
        weekday = timestamp.weekday() < 5
        is_peak = 18 <= timestamp.hour <= 21  # Peak pricing hours
        
        # Convert meters to Rust configs
        rust_configs = [
            RustAcceleratedMeter.convert_meter_to_rust_config(m)
            for m in meters
        ]
        
        # Call Rust function
        readings = rust_generate_readings(
            rust_configs,
            hour,
            weekday,
            weather_factor,
            is_peak,
            float(interval_seconds),
        )
        
        # Convert Rust readings to Python dicts
        return [reading.to_dict() for reading in readings]
    
    @staticmethod
    def _generate_with_python(
        meters: List[Dict[str, Any]],
        timestamp: datetime,
        weather_factor: float,
        interval_seconds: int,
    ) -> List[Dict[str, Any]]:
        """Fallback to Python implementation (slower but functional)."""
        # Import here to avoid circular imports
        from smart_meter_simulator.core.meter import SmartMeter
        
        readings = []
        for meter_config in meters:
            meter = SmartMeter(meter_config)
            meter.update_weather("Sunny")  # Default, should be set by engine
            
            reading = meter.generate_reading(
                timestamp=timestamp,
                interval_seconds=interval_seconds,
            )
            
            # Convert to dict
            readings.append({
                'meter_id': reading.meter_id,
                'energy_generated_kwh': reading.energy_generated,
                'energy_consumed_kwh': reading.energy_consumed,
                'surplus_energy': reading.surplus_energy,
                'deficit_energy': reading.deficit_energy,
                'battery_level': reading.battery_level,
                'voltage': reading.voltage,
                'current': reading.current,
                'frequency': reading.frequency,
                'power_factor': reading.power_factor,
                'reactive_power': reading.reactive_power_kvar,
            })
        
        return readings


def get_engine_status() -> Dict[str, Any]:
    """Get the status of the Rust acceleration engine."""
    return {
        'rust_enabled': USE_RUST_ENGINE,
        'engine_type': 'Rust (PyO3)' if USE_RUST_ENGINE else 'Python (fallback)',
        'expected_speedup': '10-50x' if USE_RUST_ENGINE else '1x (baseline)',
    }
