"""
Python wrapper for Rust core simulation engine.

This module provides a unified interface to the Rust-based simulation engine.
pandapower integration remains in Python since it's a Python-only library.

Falls back to pure Python implementations if Rust extension is unavailable.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Try to import Rust extension
_RUST_AVAILABLE = False
try:
    import smartmeter_core as _rust
    _RUST_AVAILABLE = True
    logger.info(f"Rust core v{_rust.version()} loaded")
except ImportError as e:
    logger.warning(f"Rust core not available, using Python fallback: {e}")

def is_rust_available() -> bool:
    """Check if Rust core engine is available."""
    return _RUST_AVAILABLE


# =============================================================================
# Export Rust classes or Python fallbacks
# =============================================================================

if _RUST_AVAILABLE:
    # Data models
    MeterConfig = _rust.MeterConfig
    MeterState = _rust.MeterState
    EnergyReading = _rust.EnergyReading
    GridState = _rust.GridState
    ZoneState = _rust.ZoneState
    MarketPrices = _rust.MarketPrices
    
    # Calculators
    SolarCalculator = _rust.SolarCalculator
    LoadCalculator = _rust.LoadCalculator
    BatteryState = _rust.BatteryState
    GridPhysics = _rust.GridPhysics
    ZoneAggregator = _rust.ZoneAggregator
    MarketCalculator = _rust.MarketCalculator
    EmissionCalculator = _rust.EmissionCalculator

else:
    # Python fallback implementations
    import math
    import random
    from dataclasses import dataclass, field
    
    @dataclass
    class MeterConfig:
        meter_id: str
        meter_type: str = "Grid_Consumer"
        location: str = "Unknown"
        latitude: Optional[float] = None
        longitude: Optional[float] = None
        zone_id: Optional[int] = None
        wallet_address: Optional[str] = None
        has_solar: bool = False
        solar_capacity_kw: float = 0.0
        panel_efficiency: float = 0.18
        has_battery: bool = False
        battery_capacity_kwh: float = 0.0
        max_charge_rate_kw: float = 5.0
        max_discharge_rate_kw: float = 5.0
        base_consumption_kw: float = 1.0
        user_type: str = "Residential"
    
    @dataclass
    class MeterState:
        meter_id: str
        is_connected: bool = True
        battery_level_pct: float = 50.0
        battery_kwh: float = 0.0
        weather: str = "Clear"
        irradiance: float = 1.0
        temperature_c: float = 25.0
        buy_price: float = 0.28
        sell_price: float = 0.12
        total_generated_kwh: float = 0.0
        total_consumed_kwh: float = 0.0
        voltage_state: float = 230.0
        frequency_state: float = 50.0
        power_factor_state: float = 0.95
        last_generation_kw: float = 0.0
        last_consumption_kw: float = 0.0
    
    @dataclass
    class EnergyReading:
        meter_id: str
        timestamp: str
        energy_generated_kwh: float = 0.0
        energy_consumed_kwh: float = 0.0
        surplus_kwh: float = 0.0
        deficit_kwh: float = 0.0
        battery_level_pct: float = 0.0
        voltage_v: float = 230.0
        current_a: float = 0.0
        power_factor: float = 0.95
        frequency_hz: float = 50.0
        temperature_c: float = 25.0
        net_emission_kg: float = 0.0
        rec_eligible: bool = False
        wallet_address: Optional[str] = None
        zone_id: Optional[int] = None
        
        def net_energy_kwh(self) -> float:
            return self.energy_generated_kwh - self.energy_consumed_kwh
        
        def real_power_w(self) -> float:
            return self.voltage_v * self.current_a * self.power_factor
    
    @dataclass
    class GridState:
        meter_id: str
        voltage_pu: float = 1.0
        voltage_v: float = 230.0
        frequency_hz: float = 50.0
        power_factor: float = 0.95
        thd_voltage_pct: float = 2.0
        thd_current_pct: float = 5.0
        is_on_peak: bool = False
        temperature_c: float = 25.0
        load_kw: float = 0.0
        generation_kw: float = 0.0
        
        def is_voltage_normal(self) -> bool:
            return 0.95 <= self.voltage_pu <= 1.05
        
        def is_frequency_normal(self) -> bool:
            return 49.5 <= self.frequency_hz <= 50.5
    
    @dataclass
    class ZoneState:
        zone_id: int
        transformer_name: str = ""
        meter_count: int = 0
        avg_voltage_pu: float = 1.0
        min_voltage_pu: float = 1.0
        max_voltage_pu: float = 1.0
        total_load_kw: float = 0.0
        total_generation_kw: float = 0.0
        net_power_kw: float = 0.0
        has_voltage_violation: bool = False
        has_overload: bool = False
        health_score: float = 100.0
        
        def calculate_health_score(self):
            voltage_penalty = abs(1.0 - self.avg_voltage_pu) * 100.0
            score = 100.0 - voltage_penalty
            if self.has_voltage_violation: score *= 0.8
            if self.has_overload: score *= 0.7
            self.health_score = max(0.0, score)
    
    @dataclass
    class MarketPrices:
        grid_buy_price: float = 0.28
        grid_sell_price: float = 0.12
        p2p_price: float = 0.18
        is_peak_hour: bool = False
        demand_multiplier: float = 1.0
    
    class SolarCalculator:
        def __init__(self, panel_efficiency: float = 0.18, temp_coefficient: float = 0.004):
            self.panel_efficiency = panel_efficiency
            self.temp_coefficient = temp_coefficient
        
        def calculate(self, capacity_kw: float, hour: int, irradiance_factor: float, temperature_c: float, weather: str = "Clear") -> float:
            if hour < 6 or hour >= 18:
                return 0.0
            
            hour_angle = ((hour - 6) / 12.0) * math.pi
            time_factor = max(0.0, math.sin(hour_angle))
            temp_derate = max(0.5, 1.0 - self.temp_coefficient * max(0.0, temperature_c - 25.0))
            
            weather_factors = {"Clear": 1.0, "Sunny": 1.0, "PartlyCloudy": 0.7, "Cloudy": 0.3, "Rainy": 0.1, "Stormy": 0.05}
            weather_factor = weather_factors.get(weather, 0.8)
            noise = 1.0 + random.uniform(-0.02, 0.02)
            
            return max(0.0, capacity_kw * time_factor * irradiance_factor * temp_derate * weather_factor * noise)
        
        def calculate_smooth(self, current_value: float, target_value: float, alpha: float) -> float:
            return alpha * target_value + (1.0 - alpha) * current_value
    
    class LoadCalculator:
        def __init__(self, base_load_kw: float = 1.0, profile_type: str = "Residential", variation: float = 0.1):
            self.base_load_kw = base_load_kw
            self.profile_type = profile_type
            self.variation = variation
        
        def calculate(self, hour: int, temperature_c: float, is_weekend: bool) -> float:
            profile_factors = {
                "Residential": self._residential(hour, is_weekend),
                "Commercial": self._commercial(hour, is_weekend),
                "Industrial": 0.95,
                "Hospital": self._hospital(hour),
                "University": self._university(hour, is_weekend),
            }
            profile_factor = profile_factors.get(self.profile_type, 1.0)
            
            if temperature_c < 20.0:
                temp_factor = 1.0 + (20.0 - temperature_c) * 0.03
            elif temperature_c > 26.0:
                temp_factor = 1.0 + (temperature_c - 26.0) * 0.05
            else:
                temp_factor = 1.0
            
            noise = 1.0 + random.uniform(-self.variation, self.variation)
            return self.base_load_kw * profile_factor * temp_factor * noise
        
        def calculate_smooth(self, current_value: float, target_value: float, alpha: float) -> float:
            return alpha * target_value + (1.0 - alpha) * current_value
        
        def _residential(self, hour: int, is_weekend: bool) -> float:
            profiles = {0: 0.3, 6: 0.8, 9: 0.5, 12: 0.6, 14: 0.4, 18: 1.0, 22: 0.6}
            base = 0.5
            for h, v in sorted(profiles.items()):
                if hour >= h: base = v
            if is_weekend and 9 <= hour <= 17: base *= 1.5
            elif is_weekend: base *= 1.1
            return base
        
        def _commercial(self, hour: int, is_weekend: bool) -> float:
            if is_weekend: return 0.2
            if 9 <= hour <= 17: return 1.0
            if 7 <= hour <= 8 or 18 <= hour <= 19: return 0.6
            return 0.2
        
        def _hospital(self, hour: int) -> float:
            if 9 <= hour <= 17: return 1.0
            if 0 <= hour <= 5: return 0.6
            return 0.8
        
        def _university(self, hour: int, is_weekend: bool) -> float:
            if is_weekend: return 0.15
            if 9 <= hour <= 16: return 1.0
            if 7 <= hour <= 8: return 0.5
            if 17 <= hour <= 20: return 0.4
            return 0.1
    
    class BatteryState:
        def __init__(self, capacity_kwh: float, max_charge_rate_kw: float = 5.0, max_discharge_rate_kw: float = 5.0, efficiency: float = 0.95, initial_soc: float = 0.5):
            self.capacity_kwh = capacity_kwh
            self.current_kwh = capacity_kwh * initial_soc
            self.max_charge_rate_kw = max_charge_rate_kw
            self.max_discharge_rate_kw = max_discharge_rate_kw
            self.efficiency = efficiency
            self.min_soc = 0.1
            self.max_soc = 0.95
        
        def soc(self) -> float:
            if self.capacity_kwh <= 0: return 0.0
            return max(0.0, min(1.0, self.current_kwh / self.capacity_kwh))
        
        def level_pct(self) -> float:
            return self.soc() * 100.0
        
        def charge(self, energy_kwh: float, duration_hours: float) -> float:
            max_energy = self.max_charge_rate_kw * duration_hours
            energy_to_charge = min(energy_kwh, max_energy)
            max_storable = (self.max_soc * self.capacity_kwh) - self.current_kwh
            actual_stored = min(energy_to_charge * self.efficiency, max(0.0, max_storable))
            self.current_kwh += actual_stored
            return actual_stored
        
        def discharge(self, energy_kwh: float, duration_hours: float) -> float:
            max_energy = self.max_discharge_rate_kw * duration_hours
            energy_requested = min(energy_kwh, max_energy)
            min_level = self.min_soc * self.capacity_kwh
            available = max(0.0, self.current_kwh - min_level)
            actual_discharge = min(energy_requested, available)
            self.current_kwh -= actual_discharge
            return actual_discharge * self.efficiency
    
    class GridPhysics:
        def __init__(self, nominal_voltage: float = 230.0, nominal_frequency: float = 50.0, ema_alpha: float = 0.05):
            self.nominal_voltage = nominal_voltage
            self.nominal_frequency = nominal_frequency
            self.ema_alpha = ema_alpha
        
        def smooth_ema(self, current: float, target: float) -> float:
            return self.ema_alpha * target + (1.0 - self.ema_alpha) * current
        
        def calculate_voltage(self, base_voltage: float, load_kw: float, generation_kw: float, impedance_pu: float) -> float:
            net_load = load_kw - generation_kw
            voltage_drop_pu = net_load * impedance_pu / 100.0
            voltage = base_voltage * (1.0 - voltage_drop_pu)
            return max(self.nominal_voltage * 0.9, min(self.nominal_voltage * 1.1, voltage))
        
        def calculate_frequency(self, base_freq: float, total_gen_mw: float, total_load_mw: float) -> float:
            imbalance_pct = (total_gen_mw - total_load_mw) / total_load_mw if total_load_mw > 0 else 0.0
            freq_deviation = imbalance_pct * 0.5
            return max(self.nominal_frequency - 0.5, min(self.nominal_frequency + 0.5, base_freq + freq_deviation))
        
        def calculate_power_factor(self, active_kw: float, reactive_kvar: float) -> float:
            if active_kw <= 0: return 0.95
            apparent = math.sqrt(active_kw**2 + reactive_kvar**2)
            return max(0.7, min(1.0, active_kw / apparent)) if apparent > 0 else 0.95
        
        def calculate_current(self, power_kw: float, voltage: float, power_factor: float) -> float:
            if voltage <= 0 or power_factor <= 0: return 0.0
            return power_kw * 1000.0 / (voltage * power_factor)
    
    class ZoneAggregator:
        def __init__(self):
            self.zones: Dict[int, dict] = {}
        
        def add_zone(self, zone_id: int, transformer_name: str, capacity_kw: float):
            self.zones[zone_id] = {"transformer_name": transformer_name, "meters": [], "total_load_kw": 0.0, "total_gen_kw": 0.0, "voltages": [], "capacity_kw": capacity_kw}
        
        def add_meter_to_zone(self, zone_id: int, meter_id: str):
            if zone_id in self.zones: self.zones[zone_id]["meters"].append(meter_id)
        
        def update_zone(self, zone_id: int, load_kw: float, gen_kw: float, voltage_pu: float):
            if zone_id in self.zones:
                self.zones[zone_id]["total_load_kw"] += load_kw
                self.zones[zone_id]["total_gen_kw"] += gen_kw
                self.zones[zone_id]["voltages"].append(voltage_pu)
        
        def reset_zones(self):
            for zone in self.zones.values():
                zone["total_load_kw"] = 0.0
                zone["total_gen_kw"] = 0.0
                zone["voltages"] = []
        
        def get_zone_state(self, zone_id: int) -> Optional[ZoneState]:
            zone = self.zones.get(zone_id)
            if not zone: return None
            if not zone["voltages"]: return ZoneState(zone_id=zone_id, transformer_name=zone["transformer_name"])
            avg_v = sum(zone["voltages"]) / len(zone["voltages"])
            min_v, max_v = min(zone["voltages"]), max(zone["voltages"])
            state = ZoneState(
                zone_id=zone_id, transformer_name=zone["transformer_name"], meter_count=len(zone["meters"]),
                avg_voltage_pu=avg_v, min_voltage_pu=min_v, max_voltage_pu=max_v,
                total_load_kw=zone["total_load_kw"], total_generation_kw=zone["total_gen_kw"],
                net_power_kw=zone["total_gen_kw"] - zone["total_load_kw"],
                has_voltage_violation=min_v < 0.95 or max_v > 1.05,
                has_overload=zone["total_load_kw"] > zone["capacity_kw"] * 0.8)
            state.calculate_health_score()
            return state
        
        def zone_ids(self) -> List[int]:
            return list(self.zones.keys())
    
    class MarketCalculator:
        def __init__(self, base_buy_price: float = 0.28, base_sell_price: float = 0.12, peak_multiplier: float = 1.5, demand_sensitivity: float = 0.1):
            self.base_buy_price = base_buy_price
            self.base_sell_price = base_sell_price
            self.peak_multiplier = peak_multiplier
            self.demand_sensitivity = demand_sensitivity
        
        def is_peak_hour(self, hour: int, is_weekend: bool) -> bool:
            if is_weekend: return False
            return 9 <= hour < 22
        
        def calculate_prices(self, hour: int, is_weekend: bool, total_gen_kw: float, total_load_kw: float) -> MarketPrices:
            is_peak = self.is_peak_hour(hour, is_weekend)
            demand_ratio = total_load_kw / total_gen_kw if total_gen_kw > 0 else 1.5
            demand_factor = 1.0 + (demand_ratio - 1.0) * self.demand_sensitivity
            peak_factor = self.peak_multiplier if is_peak else 1.0
            buy_price = self.base_buy_price * peak_factor * demand_factor
            sell_price = self.base_sell_price * peak_factor / max(0.5, demand_factor)
            return MarketPrices(grid_buy_price=buy_price, grid_sell_price=sell_price, p2p_price=(buy_price + sell_price) / 2.0, is_peak_hour=is_peak, demand_multiplier=demand_factor)
    
    class EmissionCalculator:
        def __init__(self, grid_factor: float = 0.5, solar_factor: float = 0.05):
            self.grid_factor = grid_factor
            self.solar_factor = solar_factor
        
        def calculate_net_emission(self, energy_consumed_kwh: float, energy_generated_kwh: float, energy_from_grid_kwh: float) -> float:
            grid_emissions = energy_from_grid_kwh * self.grid_factor
            solar_offset = min(energy_generated_kwh, energy_consumed_kwh) * (self.grid_factor - self.solar_factor)
            return grid_emissions - solar_offset
        
        def is_rec_eligible(self, surplus_kwh: float) -> bool:
            return surplus_kwh > 0.0


__all__ = [
    "is_rust_available",
    "MeterConfig", "MeterState", "EnergyReading", "GridState", "ZoneState", "MarketPrices",
    "SolarCalculator", "LoadCalculator", "BatteryState", "GridPhysics", "ZoneAggregator",
    "MarketCalculator", "EmissionCalculator",
]
