"""
Rust-powered Smart Meter implementation.

This module provides a SmartMeter class that uses the Rust core for
high-performance calculations while maintaining Python compatibility.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging
import random

from ..models.reading import EnergyReading
from ..utils.crypto import KeyManager
from ..config import SimulatorConfig

# Import Rust core (with Python fallback)
from ..rust_core import (
    is_rust_available,
    MeterConfig,
    MeterState,
    SolarCalculator,
    LoadCalculator,
    BatteryState,
    GridPhysics,
    MarketPrices,
    EmissionCalculator,
)

logger = logging.getLogger(__name__)


class RustSmartMeter:
    """
    Smart Meter implementation powered by Rust core calculations.
    
    Uses Rust for:
    - Solar generation calculation
    - Load profile calculation  
    - Battery state management
    - Grid physics simulation
    - Emission calculation
    
    Keeps in Python:
    - Wallet/crypto operations
    - Reading generation and signing
    - Network communication
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config["meter_id"]
        self.config = config
        
        # Coordinate resolution
        self.latitude = config.get("latitude") or config.get("lat")
        self.longitude = config.get("longitude") or config.get("lon")
        
        if self.latitude is None or self.longitude is None:
            location = config.get("location")
            if isinstance(location, list) and len(location) >= 2:
                self.latitude = location[0]
                self.longitude = location[1]
            elif isinstance(location, dict):
                self.latitude = location.get("lat") or location.get("latitude")
                self.longitude = location.get("lon") or location.get("longitude")
        
        # Key management (Python - crypto operations)
        self.key_manager = KeyManager()
        
        # Initialize Rust calculators
        self._init_rust_calculators(config)
        
        # State tracking
        self.current_weather = "Clear"
        self.irradiance_factor = 1.0
        self.temp_offset = 0.0
        self.current_sell_price = config.get("max_sell_price", SimulatorConfig.MAX_SELL_PRICE)
        self.current_buy_price = config.get("max_buy_price", SimulatorConfig.MAX_BUY_PRICE)
        
        # Token balances (simulated)
        self.balance_gtx = config.get("balance_gtx", random.uniform(100.0, 1000.0))
        self.balance_nrg = config.get("balance_nrg", 0.0)
        self.wallet_address_cache = None
        
        # Connection status
        self.is_connected = False
        self.last_reading = None
        
        # Zone assignment
        self.grid_zone_id: Optional[int] = None
        
        # Static data override
        self.static_data: Optional[Dict[str, Any]] = None
        
        # Accumulators for lifetime energy
        self._total_energy_consumed = config.get("total_energy_consumed", random.uniform(500.0, 5000.0))
        self._total_energy_generated = config.get("total_energy_generated",
            random.uniform(500.0, 5000.0) if config.get("has_solar") else 0.0)
        
        # Smooth state tracking
        self._last_consumption = config.get("base_consumption", 1.0)
        self._last_generation = 0.0
        
        if is_rust_available():
            logger.debug(f"Meter {self.meter_id} using Rust core")
        else:
            logger.debug(f"Meter {self.meter_id} using Python fallback")
    
    def _init_rust_calculators(self, config: Dict[str, Any]):
        """Initialize Rust calculator instances."""
        # Solar calculator
        panel_efficiency = config.get("panel_efficiency", 0.18)
        self.solar_calc = SolarCalculator(
            panel_efficiency=panel_efficiency,
            temp_coefficient=0.004
        )
        self.solar_capacity_kw = config.get("solar_capacity_kw", 0.0) if config.get("has_solar") else 0.0
        
        # Load calculator
        base_load = config.get("base_consumption", 1.0)
        user_type = config.get("user_type", "Residential")
        self.load_calc = LoadCalculator(
            base_load_kw=base_load,
            profile_type=user_type,
            variation=0.1
        )
        
        # Battery state
        if config.get("has_battery"):
            battery_capacity = config.get("battery_capacity_kwh", 10.0)
            initial_level = config.get("current_battery_level", 50.0) / 100.0
            self.battery = BatteryState(
                capacity_kwh=battery_capacity,
                max_charge_rate_kw=config.get("max_charge_rate_kw", 5.0),
                max_discharge_rate_kw=config.get("max_discharge_rate_kw", 5.0),
                efficiency=0.95,
                initial_soc=initial_level
            )
        else:
            self.battery = None
        
        # Grid physics
        self.grid_physics = GridPhysics(
            nominal_voltage=230.0,
            nominal_frequency=50.0,
            ema_alpha=0.05
        )
        
        # Emission calculator
        self.emission_calc = EmissionCalculator(
            grid_factor=0.5,
            solar_factor=0.05
        )
        
        # Current grid state
        self._voltage_state = 230.0
        self._frequency_state = 50.0
        self._power_factor_state = 0.95
        self._temperature_state = 25.0
    
    @property
    def wallet_address(self) -> str:
        """Get or generate wallet address."""
        if self.wallet_address_cache:
            return self.wallet_address_cache
        
        wallet = self.config.get("wallet_address")
        if not wallet:
            import hashlib
            import base58
            seed = hashlib.sha256(self.meter_id.encode()).digest()
            wallet = base58.b58encode(seed).decode("utf-8")
        
        self.wallet_address_cache = wallet
        return wallet
    
    @property
    def battery_level(self) -> float:
        """Get current battery level percentage."""
        if self.battery:
            return self.battery.level_pct()
        return 0.0
    
    @property
    def current_load_kw(self) -> float:
        """Get current load for zone utilization tracking."""
        return self._last_consumption
    
    def update_weather(self, weather: str, irradiance: float, temp_offset: float):
        """Update weather conditions."""
        self.current_weather = weather
        self.irradiance_factor = irradiance
        self.temp_offset = temp_offset
    
    def update_prices(self, sell_price: float, buy_price: float):
        """Update market prices."""
        self.current_sell_price = sell_price
        self.current_buy_price = buy_price
    
    def generate_reading(self, timestamp: datetime) -> EnergyReading:
        """Generate energy reading using Rust calculators."""
        
        # Check for static data override
        if self.static_data is not None:
            return self._generate_static_reading(timestamp)
        
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5
        temperature = 25.0 + self.temp_offset
        
        # 1. Calculate solar generation (Rust)
        raw_generation_kw = 0.0
        if self.solar_capacity_kw > 0:
            raw_generation_kw = self.solar_calc.calculate(
                capacity_kw=self.solar_capacity_kw,
                hour=hour,
                irradiance_factor=self.irradiance_factor,
                temperature_c=temperature,
                weather=self.current_weather
            )
        
        # Smooth generation
        self._last_generation = self.solar_calc.calculate_smooth(
            current_value=self._last_generation,
            target_value=raw_generation_kw,
            alpha=0.025
        )
        power_generated_kw = self._last_generation
        
        # 2. Calculate consumption (Rust)
        raw_consumption_kw = self.load_calc.calculate(
            hour=hour,
            temperature_c=temperature,
            is_weekend=is_weekend
        )
        
        # Smooth consumption
        self._last_consumption = self.load_calc.calculate_smooth(
            current_value=self._last_consumption,
            target_value=raw_consumption_kw,
            alpha=0.025
        )
        power_consumed_kw = self._last_consumption
        
        # 3. Update grid physics (Rust EMA smoothing)
        target_voltage = 230.0 + random.gauss(0, 0.1)
        target_frequency = 50.0 + random.gauss(0, 0.002)
        target_pf = min(1.0, 0.95 + random.gauss(0, 0.001))
        target_temp = 20.0 + self.temp_offset + random.gauss(0, 0.05)
        
        self._voltage_state = self.grid_physics.smooth_ema(self._voltage_state, target_voltage)
        self._frequency_state = self.grid_physics.smooth_ema(self._frequency_state, target_frequency)
        self._power_factor_state = self.grid_physics.smooth_ema(self._power_factor_state, target_pf)
        self._temperature_state = self.grid_physics.smooth_ema(self._temperature_state, target_temp)
        
        # 4. Convert power to energy (15-minute interval)
        sim_interval_hours = 0.25
        energy_generated_kwh = power_generated_kw * sim_interval_hours
        energy_consumed_kwh = power_consumed_kw * sim_interval_hours
        
        # Update lifetime accumulators
        self._total_energy_consumed += energy_consumed_kwh
        self._total_energy_generated += energy_generated_kwh
        
        # 5. Battery logic (Rust)
        if self.battery:
            net_energy = energy_generated_kwh - energy_consumed_kwh
            if net_energy > 0:
                # Surplus: charge battery
                self.battery.charge(net_energy, sim_interval_hours)
            elif net_energy < 0:
                # Deficit: discharge battery
                discharged = self.battery.discharge(-net_energy, sim_interval_hours)
                energy_consumed_kwh -= discharged  # Offset consumption
        
        # 6. Calculate net energy
        net_energy_kwh = energy_generated_kwh - energy_consumed_kwh
        surplus_kwh = max(0, net_energy_kwh)
        deficit_kwh = max(0, -net_energy_kwh)
        
        # 7. Emissions (Rust)
        energy_from_grid = max(0, deficit_kwh)
        net_emission = self.emission_calc.calculate_net_emission(
            energy_consumed_kwh=energy_consumed_kwh,
            energy_generated_kwh=energy_generated_kwh,
            energy_from_grid_kwh=energy_from_grid
        )
        rec_eligible = self.emission_calc.is_rec_eligible(surplus_kwh)
        carbon_offset = energy_generated_kwh * SimulatorConfig.CARBON_OFFSET_RATE if rec_eligible else 0.0
        
        # 8. Calculate current
        total_power_kw = power_consumed_kw + power_generated_kw
        current_amps = self.grid_physics.calculate_current(
            power_kw=total_power_kw,
            voltage=self._voltage_state,
            power_factor=self._power_factor_state
        )
        
        # 9. Create reading
        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            
            # Energy (kWh)
            energy_generated=round(energy_generated_kwh, 6),
            energy_consumed=round(energy_consumed_kwh, 6),
            surplus_energy=round(surplus_kwh, 6),
            deficit_energy=round(deficit_kwh, 6),
            
            # Power (kW)
            power_generated=round(power_generated_kw, 4),
            power_consumed=round(power_consumed_kw, 4),
            
            # Lifetime totals
            total_energy_generated=round(self._total_energy_generated, 4),
            total_energy_consumed=round(self._total_energy_consumed, 4),
            
            # Battery
            battery_level=round(self.battery_level, 2),
            
            # Location
            location=self.config.get("location", [0.0, 0.0]),
            latitude=self.latitude,
            longitude=self.longitude,
            meter_type=self.config.get("meter_type", "Grid_Consumer"),
            user_type=self.config.get("user_type", "Residential"),
            grid_zone_id=self.grid_zone_id,
            
            # Grid state
            voltage=round(self._voltage_state, 2),
            current=round(current_amps, 3),
            frequency=round(self._frequency_state, 2),
            temperature=round(self._temperature_state, 1),
            power_factor=round(self._power_factor_state, 2),
            
            # Market
            max_sell_price=round(self.current_sell_price, 4),
            max_buy_price=round(self.current_buy_price, 4),
            rec_eligible=rec_eligible,
            carbon_offset=round(carbon_offset, 4),
            net_emission=round(net_emission, 4),
            weather_condition=self.current_weather,
            wallet_address=self.wallet_address,
        )
        
        # 10. Sign reading
        canonical_message = (
            f"GRIDTOKENX_METER_READING\n"
            f"meter_serial: {self.meter_id}\n"
            f"timestamp: {reading.timestamp.isoformat()}\n"
            f"kwh_amount: {surplus_kwh:.6f}\n"
            f"wallet: {self.wallet_address}"
        )
        reading.meter_signature = self.key_manager.sign_data(canonical_message)
        
        self.last_reading = reading
        return reading
    
    def _generate_static_reading(self, timestamp: datetime) -> EnergyReading:
        """Generate reading from static data override."""
        data = self.static_data
        
        energy_generated = float(data.get("energy_generated", 0.0))
        energy_consumed = float(data.get("energy_consumed", 0.0))
        
        net_energy = energy_generated - energy_consumed
        surplus = max(0, net_energy)
        deficit = max(0, -net_energy)
        
        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            energy_generated=energy_generated,
            energy_consumed=energy_consumed,
            surplus_energy=surplus,
            deficit_energy=deficit,
            power_generated=data.get("power_generated", energy_generated * 4),
            power_consumed=data.get("power_consumed", energy_consumed * 4),
            total_energy_generated=self._total_energy_generated + energy_generated,
            total_energy_consumed=self._total_energy_consumed + energy_consumed,
            battery_level=data.get("battery_level", self.battery_level),
            location=self.config.get("location", [0.0, 0.0]),
            latitude=self.latitude,
            longitude=self.longitude,
            meter_type=self.config.get("meter_type", "Grid_Consumer"),
            user_type=self.config.get("user_type", "Residential"),
            grid_zone_id=self.grid_zone_id,
            voltage=data.get("voltage", 230.0),
            current=data.get("current", 0.0),
            frequency=data.get("frequency", 50.0),
            temperature=data.get("temperature", 25.0),
            power_factor=data.get("power_factor", 0.95),
            max_sell_price=self.current_sell_price,
            max_buy_price=self.current_buy_price,
            rec_eligible=data.get("rec_eligible", False),
            carbon_offset=data.get("carbon_offset", 0.0),
            net_emission=data.get("net_emission", 0.0),
            weather_condition=self.current_weather,
            wallet_address=self.wallet_address,
        )
        
        canonical_message = (
            f"GRIDTOKENX_METER_READING\n"
            f"meter_serial: {self.meter_id}\n"
            f"timestamp: {reading.timestamp.isoformat()}\n"
            f"kwh_amount: {surplus:.6f}\n"
            f"wallet: {self.wallet_address}"
        )
        reading.meter_signature = self.key_manager.sign_data(canonical_message)
        
        self.last_reading = reading
        return reading


# Alias for backward compatibility
SmartMeter = RustSmartMeter
