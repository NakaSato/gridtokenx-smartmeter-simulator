import random
import math
from datetime import datetime
from typing import Dict, Any, Optional

from ..models.reading import EnergyReading
from ..utils.crypto import KeyManager
from ..config import AccuracyClass, METER_TYPE_CHANNELS, MeterType, get_config
from .meter_logic import profiles, electrical

class SmartMeter:
    """
    Represents a single smart meter instance.
    Delegates complex generation/consumption and physics logic to modular utilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config['meter_id']
        self.config = config
        self.key_manager = KeyManager()
        
        self.battery_level = config.get('current_battery_level', 0.0)
        self.current_weather = "Sunny"
        self.current_frequency = 50.0
        self.last_cons_noise = 0.0
        self.last_gen_noise = 0.0
        self.vpp_dispatch_kw = 0.0
        self.priority = config.get('priority', 2)
        self.is_shed = False
        
        meter_type_enum = MeterType(self.config['meter_type'])
        accuracy_defaults = {
            MeterType.RESIDENTIAL: AccuracyClass.CLASS_2_0, MeterType.GRID_CONSUMER: AccuracyClass.CLASS_2_0,
            MeterType.COMMERCIAL: AccuracyClass.CLASS_1_0, MeterType.SOLAR_PROSUMER: AccuracyClass.CLASS_1_0,
            MeterType.HYBRID_PROSUMER: AccuracyClass.CLASS_1_0, MeterType.BATTERY_STORAGE: AccuracyClass.CLASS_0_5,
            MeterType.FEEDER: AccuracyClass.CLASS_0_5, MeterType.SUBSTATION: AccuracyClass.CLASS_0_2,
            MeterType.EV_CHARGER: AccuracyClass.CLASS_1_0, MeterType.DC_FAST_CHARGER: AccuracyClass.CLASS_0_5,
        }
        self.accuracy_class = accuracy_defaults.get(meter_type_enum, AccuracyClass.CLASS_2_0)
        self.channels = METER_TYPE_CHANNELS.get(meter_type_enum, set())

    def update_weather(self, weather: str): self.current_weather = weather
    def receive_frequency(self, frequency_hz: float): self.current_frequency = frequency_hz
    def receive_dispatch(self, dispatch_kw: float): self.vpp_dispatch_kw = dispatch_kw
        
    def generate_reading(
        self, timestamp: datetime, override_gen: Optional[float] = None,
        override_cons: Optional[float] = None, forced_dispatch: Optional[float] = None,
        interval_seconds: int = 900, nodal_price: float = 0.50,
        carbon_intensity: float = 0.0, grid_stress: float = 1.0
    ) -> EnergyReading:
        time_factor = interval_seconds / 3600.0
        if self.vpp_dispatch_kw != 0: forced_dispatch = self.vpp_dispatch_kw
        
        # 1. Generation & Consumption
        gen, self.last_gen_noise = profiles.calculate_solar_generation(timestamp, self.config, self.current_weather, self.last_gen_noise) if override_gen is None and self.config.get('has_solar') else (override_gen or 0.0, self.last_gen_noise)
        cons, self.last_cons_noise = profiles.calculate_consumption(timestamp, self.config, self.meter_id, self.last_cons_noise) if override_cons is None else (override_cons, self.last_cons_noise)
        
        if grid_stress != 1.0 and override_cons is None: cons *= grid_stress
        if self.is_shed: cons = 0.0

        # 2. Physics & Controls
        gen, cons = electrical.apply_droop_control(gen, cons, self.current_frequency)
        
        if self.config.get('has_battery'):
            self._update_battery(gen, cons, forced_dispatch)

        if MeterType(self.config['meter_type']) in (MeterType.EV_CHARGER, MeterType.DC_FAST_CHARGER):
             ev_gen, ev_cons = self._calculate_ev_behavior(timestamp)
             gen += ev_gen
             cons += ev_cons

        # 3. Electrical parameters with noise
        e_params = electrical.calculate_electrical_params(gen, cons, self.accuracy_class.value, self.channels)
            
        reading = EnergyReading(
            meter_id=self.meter_id, timestamp=timestamp,
            energy_generated=round(gen * time_factor, 6), energy_consumed=round(cons * time_factor, 6),
            surplus_energy=round(max(0, (gen - cons) * time_factor), 6), deficit_energy=round(max(0, (cons - gen) * time_factor), 6),
            interval_seconds=interval_seconds, battery_level=round(self.battery_level, 1),
            location=self.config.get('location', 'Unknown'), meter_type=self.config.get('meter_type', 'Unknown'),
            user_type=self.config.get('user_type', 'Unknown'),
            voltage=round(e_params.get("voltage"), 2) if "voltage" in e_params else None,
            current=round(e_params.get("current"), 3) if "current" in e_params else None,
            reactive_power_kvar=round(e_params.get("reactive_power"), 3) if "reactive_power" in e_params else None,
            frequency=round(e_params.get("frequency"), 2) if "frequency" in e_params else None,
            power_factor=round(e_params.get("power_factor"), 2) if "power_factor" in e_params else None,
            temperature=round(random.gauss(20.0, 5.0), 1), nodal_price=nodal_price,
            carbon_intensity=carbon_intensity, rec_eligible=False, carbon_offset=0.0,
            weather_condition=self.current_weather
        )
        
        # 4. Signing
        kwh_str = f"{reading.energy_generated:.6f}"
        reading.meter_signature = self.key_manager.sign_data(f"{kwh_str}|{reading.timestamp.isoformat()}")
        return reading

    def _calculate_ev_behavior(self, timestamp: datetime) -> tuple:
        """
        Simulate EV charging and V2G behavior.
        Returns (generation_kwh, consumption_kwh)
        """
        meter_type = MeterType(self.config['meter_type'])
        is_dc_fast_charger = meter_type == MeterType.DC_FAST_CHARGER

        if is_dc_fast_charger:
            return self._calculate_dc_charger_behavior(timestamp)

        # Original EV charger behavior (AC Level 2)
        hour = timestamp.hour + timestamp.minute / 60.0

        # Determine if vehicle is at home/charging station
        is_at_station = hour >= 18 or hour <= 8

        if not is_at_station:
            if 8 < hour < 18:
                self.battery_level = max(20.0, self.battery_level - random.uniform(0.1, 0.8))
            return 0.0, 0.0

        gen_kwh = 0.0
        cons_kwh = 0.0
        config = get_config()

        is_peak = 18 <= hour <= 21
        if is_peak and self.battery_level > (config.ev_v2g_threshold_soc * 100):
            discharge_power = config.ev_v2g_discharge_rate_kw
            gen_kwh = discharge_power / 4.0
            capacity_kwh = self.config.get('ev_battery_capacity', config.ev_battery_capacity_max)
            self.battery_level = max(0.0, self.battery_level - (gen_kwh / capacity_kwh) * 100)
            return gen_kwh, cons_kwh

        if self.battery_level < 90.0:
            charge_power = config.ev_charge_rate_kw * random.uniform(0.8, 1.0)
            cons_kwh = charge_power / 4.0
            capacity_kwh = self.config.get('ev_battery_capacity', config.ev_battery_capacity_max)
            self.battery_level = min(100.0, self.battery_level + (cons_kwh / capacity_kwh) * 100)

        return gen_kwh, cons_kwh

    def _calculate_dc_charger_behavior(self, timestamp: datetime) -> tuple:
        """Simulate DC fast charger behavior."""
        hour = timestamp.hour + timestamp.minute / 60.0
        config = get_config()

        if 8 <= hour <= 22: utilization = random.uniform(0.6, 0.95)
        elif 6 <= hour < 8 or 22 < hour <= 24: utilization = random.uniform(0.3, 0.6)
        else: utilization = random.uniform(0.1, 0.3)

        connector_count = self.config.get('connector_count', 4)
        charge_rate_kw = self.config.get('ev_charge_rate_kw', config.dc_charge_rate_kw)
        max_station_capacity_kw = self.config.get('max_station_capacity_kw', config.dc_max_station_capacity_kw)

        active_ports = max(1, int(connector_count * utilization))
        base_consumption_kw = charge_rate_kw * active_ports
        actual_consumption_kw = min(base_consumption_kw, max_station_capacity_kw)

        soc_fraction = self.battery_level / 100.0
        if soc_fraction > 0.8: actual_consumption_kw *= (1.0 - ((soc_fraction - 0.8) / 0.2) * 0.6)
        elif soc_fraction < 0.2: actual_consumption_kw *= (0.7 + (soc_fraction / 0.2) * 0.3)

        cons_kwh = actual_consumption_kw / 4.0
        capacity_kwh = self.config.get('ev_battery_capacity', 60.0)
        if capacity_kwh > 0:
            self.battery_level = min(100.0, self.battery_level + (cons_kwh / capacity_kwh) * 100)

        return 0.0, cons_kwh

    def _update_battery(self, gen: float, cons: float, forced_dispatch: Optional[float] = None):
        capacity = self.config.get('battery_capacity', 10.0)
        net = gen - cons
        if forced_dispatch is not None:
            if forced_dispatch > 0: self.battery_level -= min(forced_dispatch, self.battery_level)
            else: self.battery_level += min(abs(forced_dispatch), capacity - self.battery_level)
        else:
            if net > 0: self.battery_level += min(net, capacity - self.battery_level)
            else: self.battery_level -= min(abs(net), self.battery_level)
        self.battery_level = max(0, min(capacity, self.battery_level))
