import logging
from datetime import datetime, timedelta
from typing import List, Any, Dict, Tuple
import numpy as np
from ..models.reading import EnergyReading
from ..config import get_config, SimulationMode
from .data_source import ProfileDataSource
from .optimizer import OptimizationEngine

logger = logging.getLogger(__name__)

class ReadingManager:
    """
    Handles generation of smart meter readings, including batch processing
    with Rust and fallback to Python logic.
    """
    def __init__(self, data_source: ProfileDataSource):
        self.data_source = data_source
        self.optimizer = OptimizationEngine()

    def generate_all(self, meters: List[Any], timestamp: datetime, interval: int, mode: SimulationMode, playback_profile: str, weather_mode: str, grid_stress: float) -> Tuple[List[EnergyReading], Dict[str, Any]]:
        """Generate readings for all meters at the given timestamp."""
        
        # 1. Weather updates
        for meter in meters:
            meter.update_weather(weather_mode)

        # 2. Playback data
        playback_data = {}
        if mode == SimulationMode.PLAYBACK and playback_profile:
            playback_data = self.data_source.get_values_batch(playback_profile, timestamp)
            self._apply_playback_overrides(meters, playback_data)

        # 3. Batch Rust generation (Fast path)
        readings, success = self._generate_rust_batch(meters, timestamp, interval, weather_mode, grid_stress)
        if success:
            return readings, playback_data

        # 4. Python per-meter generation (Slow path)
        readings = self._generate_python_loop(meters, timestamp, interval, playback_data, grid_stress)
        return readings, playback_data

    def _apply_playback_overrides(self, meters: List[Any], playback_data: Dict[str, Any]):
        for m in meters:
            if m.meter_id in playback_data:
                val = playback_data[m.meter_id]
                if val < 0:
                    m.manual_override_gen, m.manual_override_cons = abs(val), 0.0
                else:
                    m.manual_override_cons, m.manual_override_gen = abs(val), 0.0

    def _generate_rust_batch(self, meters: List[Any], timestamp: datetime, interval: int, weather: str, stress: float) -> Tuple[List[EnergyReading], bool]:
        config = get_config()
        if not config.rust_acceleration_enabled or stress != 1.0:
            return [], False

        try:
            from .rust_engine import RustAcceleratedMeter
            weather_factor = 1.0 if weather == "Sunny" else 0.7
            
            meter_configs = [self._get_meter_config_for_rust(m) for m in meters]
            rust_readings = RustAcceleratedMeter.generate_readings_batch(
                meters=meter_configs,
                timestamp=timestamp,
                weather_factor=weather_factor,
                interval_seconds=interval
            )

            readings = []
            for meter, rr in zip(meters, rust_readings):
                reading = self._create_reading_from_rust(meter, rr, timestamp, interval, weather)
                readings.append(reading)
                meter.last_reading = reading
            
            return readings, True
        except Exception as e:
            logger.warning(f"Rust batch failed: {e}")
            return [], False

    def _generate_python_loop(self, meters: List[Any], timestamp: datetime, interval: int, playback: Dict[str, Any], stress: float) -> List[EnergyReading]:
        readings = []
        for meter in meters:
            gen_override = playback.get(f"{meter.meter_id}_GEN")
            cons_override = playback.get(f"{meter.meter_id}_CONS") or playback.get(meter.meter_id)
            
            if hasattr(meter, 'manual_override_gen'): gen_override = meter.manual_override_gen
            if hasattr(meter, 'manual_override_cons'): cons_override = meter.manual_override_cons

            forced_dispatch = None
            if meter.config.get('has_battery'):
                forced_dispatch = self.optimizer.optimize_battery_dispatch(meter.meter_id, meter.battery_level, np.zeros(24), None)

            reading = meter.generate_reading(
                timestamp,
                override_gen=gen_override,
                override_cons=cons_override,
                forced_dispatch=forced_dispatch,
                interval_seconds=interval,
                grid_stress=stress
            )
            readings.append(reading)
            meter.last_reading = reading
        return readings

    def _get_meter_config_for_rust(self, m: Any) -> Dict:
        return {
            'meter_id': m.meter_id,
            'meter_type': m.config['meter_type'],
            'has_solar': m.config.get('has_solar', False),
            'has_battery': m.config.get('has_battery', False),
            'solar_capacity': m.config.get('solar_capacity', 0.0),
            'battery_capacity': m.config.get('battery_capacity', 0.0),
            'base_consumption': m.config.get('base_consumption', 1.0),
            'panel_efficiency': m.config.get('panel_efficiency', 0.18),
            'current_battery_level': m.battery_level,
            'price_elasticity': m.config.get('price_elasticity', 0.15),
            'accuracy_class': getattr(m.accuracy_class, 'value', 2.0),
        }

    def _create_reading_from_rust(self, meter: Any, rr: Dict, ts: datetime, interval: int, weather: str) -> EnergyReading:
        return EnergyReading(
            meter_id=rr['meter_id'],
            timestamp=ts,
            energy_generated=rr['energy_generated_kwh'],
            energy_consumed=rr['energy_consumed_kwh'],
            surplus_energy=rr['surplus_energy'],
            deficit_energy=rr['deficit_energy'],
            interval_seconds=interval,
            battery_level=rr['battery_level'],
            location=meter.config.get('location', 'Unknown'),
            meter_type=meter.config.get('meter_type', 'Unknown'),
            user_type=meter.config.get('user_type', 'Unknown'),
            voltage=rr['voltage'],
            current=rr['current'],
            reactive_power_kvar=rr['reactive_power'],
            frequency=rr['frequency'],
            temperature=20.0,
            power_factor=rr['power_factor'],
            nodal_price=0.50,
            carbon_intensity=0.0,
            max_sell_price=meter.config.get('max_sell_price', 0.50),
            max_buy_price=meter.config.get('max_buy_price', 0.30),
            rec_eligible=meter.config.get('has_solar', False),
            carbon_offset=0.0,
            weather_condition=weather,
        )
