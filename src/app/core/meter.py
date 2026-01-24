import logging
import random
import math
from datetime import datetime
from typing import Dict, Any, Optional

from ..models.reading import EnergyReading
from ..utils.crypto import KeyManager
from ..config import SimulatorConfig
from .profiles import get_profile

logger = logging.getLogger(__name__)


class SmartMeter:
    """
    Represents a single smart meter instance.
    Handles energy generation/consumption logic and cryptographic signing.
    """

    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config["meter_id"]
        self.config = config
        # Coordinate resolution: check latitude, then lat, then location list/dict
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
        self.key_manager = KeyManager()  # Generates new keypair on init

        # State
        self.battery_level = config.get("current_battery_level", 0.0)
        self.current_weather = "Sunny"  # Default, updated by engine
        self.irradiance_factor = 1.0
        self.temp_offset = 0.0

        # ========== TOKEN LAYER (SIMULATED) ==========
        # In a real app, we would query the blockchain config/state.
        # Here we simulate the wallet state within the meter object.
        self.balance_gtx = config.get("balance_gtx", random.uniform(100.0, 1000.0)) # Payment Token
        self.balance_nrg = config.get("balance_nrg", 0.0) # Energy Token (REC/Certificate)
        self.wallet_address_cache = None

        # Connection status to API Gateway
        self.is_connected = False  # Updated by engine after each send attempt
        self.last_reading = None  # Store last generated reading for status display

        # Microgrid Zone ID (assigned by MicrogridZoningService)
        self.grid_zone_id: Optional[int] = None

        # Static data override (for manual control)
        self.static_data: Optional[Dict[str, Any]] = None

        # Dynamic Prices
        self.current_sell_price = config.get(
            "max_sell_price", SimulatorConfig.MAX_SELL_PRICE
        )
        self.current_buy_price = config.get(
            "max_buy_price", SimulatorConfig.MAX_BUY_PRICE
        )

        # Emission Factors (kgCO2/kWh)
        self.GRID_EMISSION_FACTOR = 0.5
        self.SOLAR_EMISSION_FACTOR = 0.05

        # Load Profile
        self.profile = get_profile(config.get("user_type", "Residential"))
        
        # ========== STATE PERSISTENCE FOR SMOOTH TRANSITIONS ==========
        # Using EMA (Exponential Moving Average) for realistic gradual changes
        # Each parameter maintains its current state and drifts slowly toward target
        self._ema_alpha = 0.05  # Smoothing factor: 5% new value, 95% previous
        
        # Electrical state (persisted between ticks)
        self._voltage_state = 240.0  # Base voltage (V)
        self._frequency_state = 50.0  # Base frequency (Hz)
        self._power_factor_state = 0.95  # Base power factor
        self._temperature_state = 25.0  # Initial ambient temperature (°C)
        
        # Consumption/generation state for smooth transitions
        self._last_consumption = config.get("base_consumption", 1.0)
        self._last_generation = 0.0
        
        # Accumulators for lifetime energy (kWh)
        # Initialize with a random realistic starting value for a "lived-in" feel
        self._total_energy_consumed = config.get("total_energy_consumed", random.uniform(500.0, 5000.0))
        self._total_energy_generated = config.get("total_energy_generated", 
            random.uniform(500.0, 5000.0) if config.get("has_solar") else 0.0)

    @property
    def wallet_address(self) -> str:
        if self.wallet_address_cache:
            return self.wallet_address_cache
            
        # Use configured wallet if available
        wallet = self.config.get("wallet_address")
        if not wallet:
            # Generate a consistent fake Solana address based on meter_id for stability
            # Base58 chars: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
            import hashlib
            import base58
            seed = hashlib.sha256(self.meter_id.encode()).digest()
            # Valid Solana address is 32 bytes base58 encoded
            wallet = base58.b58encode(seed).decode("utf-8")
            
        self.wallet_address_cache = wallet
        return wallet

    def update_weather(self, weather: str, irradiance: float, temp_offset: float):
        self.current_weather = weather
        self.irradiance_factor = irradiance
        self.temp_offset = temp_offset

    def update_prices(self, sell_price: float, buy_price: float):
        self.current_sell_price = sell_price
        self.current_buy_price = buy_price

    def _calculate_current_from_power(self, power_kw: float, voltage: float, power_factor: float) -> float:
        """Calculate current (A) from power using physics: I = P / (V * PF)"""
        if voltage <= 0 or power_factor <= 0:
            return 0.0
        # P (kW) = V * I * PF / 1000, so I = P * 1000 / (V * PF)
        return round(power_kw * 1000 / (voltage * power_factor), 3)

    def _smooth_ema(self, current: float, target: float, alpha: float = None) -> float:
        """Apply Exponential Moving Average for smooth state transitions.
        
        Formula: new_state = alpha * target + (1 - alpha) * current
        With alpha=0.05, we blend 5% new target + 95% previous value.
        """
        if alpha is None:
            alpha = self._ema_alpha
        return alpha * target + (1 - alpha) * current
    
    def generate_reading(self, timestamp: datetime) -> EnergyReading:
        """Generate a signed energy reading for the current timestamp."""

        # Check for static data override
        if getattr(self, "static_data", None) is not None:
            return self._generate_static_reading(timestamp)

        # 1. Calculate Generation (Solar Power kW) - with EMA smoothing
        raw_generation_kw = 0.0
        if self.config.get("has_solar"):
            raw_generation_kw = self._calculate_solar_generation(timestamp)
        # Smooth transition with lower alpha for more stable output (2.5% change per tick)
        self._last_generation = self._smooth_ema(self._last_generation, raw_generation_kw, 0.025)
        power_generated_kw = self._last_generation

        # 2. Calculate Consumption (Load Power kW) - with EMA smoothing
        base_consumption_kw = self._calculate_consumption(timestamp)
        
        # Add small random fluctuation (±1%) to target so it looks alive
        # This prevents the "frozen" look while keeping it stable
        noise = random.gauss(0, 0.01) * base_consumption_kw
        target_consumption_kw = base_consumption_kw + noise

        # Smooth transition (consumption changes gradually)
        self._last_consumption = self._smooth_ema(self._last_consumption, target_consumption_kw, 0.025)
        power_consumed_kw = self._last_consumption

        # 3. Electrical State Update (Voltage, PF, etc)
        # Target values with tiny micro-variations (real grid behavior)
        target_voltage = 240.0 + random.gauss(0, 0.1)  # Target with micro-drift
        target_frequency = 50.0 + random.gauss(0, 0.002)  # Very tight frequency control
        target_pf = min(1.0, 0.95 + random.gauss(0, 0.001))  # Stable power factor
        target_temp = 20.0 + self.temp_offset + random.gauss(0, 0.05)  # Environmental temp
        
        # Apply EMA smoothing - values change gradually (5% per tick)
        self._voltage_state = self._smooth_ema(self._voltage_state, target_voltage)
        self._frequency_state = self._smooth_ema(self._frequency_state, target_frequency)
        self._power_factor_state = self._smooth_ema(self._power_factor_state, target_pf)
        self._temperature_state = self._smooth_ema(self._temperature_state, target_temp)

        # 4. Integrate Power to Energy (kW -> kWh)
        # Simulation Step is roughly 15 minutes
        # Using 15 minutes exactly (0.25h) to match standard market settlement period
        sim_interval_hours = 0.25 
        
        energy_generated_kwh = power_generated_kw * sim_interval_hours
        energy_consumed_kwh = power_consumed_kw * sim_interval_hours

        # Update accumulators
        self._total_energy_consumed += energy_consumed_kwh
        self._total_energy_generated += energy_generated_kwh
        
        # 5. Battery Logic
        if self.config.get("has_battery"):
            # Update battery with Energy (kWh), not Power
            self._update_battery(energy_generated_kwh, energy_consumed_kwh)

        # 6. Calculate Net & Trading (in kWh)
        net_energy_kwh = energy_generated_kwh - energy_consumed_kwh
        surplus_kwh = max(0, net_energy_kwh)
        deficit_kwh = max(0, -net_energy_kwh)

        # Determine REC eligibility and carbon offset
        rec_eligible = self.config.get("has_solar", False) and energy_generated_kwh > 0
        carbon_offset = (
            energy_generated_kwh * SimulatorConfig.CARBON_OFFSET_RATE
            if rec_eligible
            else 0.0
        )

        net_emission = (energy_consumed_kwh * self.GRID_EMISSION_FACTOR) - (
            energy_generated_kwh * (self.GRID_EMISSION_FACTOR - self.SOLAR_EMISSION_FACTOR)
        )
        
        # Calculate current from Power (kW)
        # I = P / (V * PF)
        total_power_kw = power_consumed_kw + power_generated_kw
        current_amps = 0.0
        if total_power_kw > 0 and self._voltage_state > 0:
             current_amps = round(total_power_kw * 1000 / (self._voltage_state * self._power_factor_state), 3)

        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            
            # Energy Values (kWh) - Small variations per tick
            energy_generated=round(energy_generated_kwh, 6), # Increased precision for small values
            energy_consumed=round(energy_consumed_kwh, 6),
            surplus_energy=round(surplus_kwh, 6),
            deficit_energy=round(deficit_kwh, 6),
            
            # Power Values (kW) - Instantaneous
            power_generated=round(power_generated_kw, 4),
            power_consumed=round(power_consumed_kw, 4),
            
            # Accumulated Lifetime Energy
            total_energy_generated=round(self._total_energy_generated, 4),
            total_energy_consumed=round(self._total_energy_consumed, 4),
            
            # Battery
            battery_level=round(self.battery_level, 2),
            
            location=self.config.get("location", [0.0, 0.0]),
            latitude=self.latitude,
            longitude=self.longitude,
            meter_type=self.config.get("meter_type", "Grid_Consumer"),
            user_type=self.config.get("user_type", "Residential"),
            grid_zone_id=self.grid_zone_id,
            
            voltage=round(self._voltage_state, 2),
            current=current_amps,
            frequency=round(self._frequency_state, 2),
            temperature=round(self._temperature_state, 1),
            power_factor=round(self._power_factor_state, 2),
            
            max_sell_price=round(self.current_sell_price, 4),
            max_buy_price=round(self.current_buy_price, 4),
            rec_eligible=rec_eligible,
            carbon_offset=round(carbon_offset, 4),
            net_emission=round(net_emission, 4),
            weather_condition=self.current_weather,
            wallet_address=self.wallet_address,
        )

        # 6. Sign Data using canonical message format
        # Must match the format used in API Gateway:
        # GRIDTOKENX_METER_READING
        # meter_serial: {meter_serial}
        # timestamp: {reading_timestamp}
        # kwh_amount: {kwh_amount}
        # wallet: {wallet_address}

        canonical_message = (
            f"GRIDTOKENX_METER_READING\n"
            f"meter_serial: {self.meter_id}\n"
            f"timestamp: {reading.timestamp.isoformat()}\n"
            f"kwh_amount: {surplus_kwh:.6f}\n"
            f"wallet: {self.wallet_address}"
        )

        reading.meter_signature = self.key_manager.sign_data(canonical_message)

        # Store last reading for status display
        self.last_reading = reading

        return reading

    def _generate_static_reading(self, timestamp: datetime) -> EnergyReading:
        """Generate a reading based on static data."""
        assert self.static_data is not None, (
            "static_data must be set before calling _generate_static_reading"
        )
        data = self.static_data

        # Calculate derived values if not provided
        energy_generated = float(data.get("energy_generated", 0.0))
        energy_consumed = float(data.get("energy_consumed", 0.0))

        # Update battery if provided
        if "battery_level" in data:
            self.battery_level = float(data["battery_level"])

        net_energy = energy_generated - energy_consumed
        surplus = max(0, net_energy)
        deficit = max(0, -net_energy)

        rec_eligible = self.config.get("has_solar", False) and energy_generated > 0
        carbon_offset = (
            energy_generated * SimulatorConfig.CARBON_OFFSET_RATE
            if rec_eligible
            else 0.0
        )

        net_emission = (energy_consumed * self.GRID_EMISSION_FACTOR) - (
            energy_generated * (self.GRID_EMISSION_FACTOR - self.SOLAR_EMISSION_FACTOR)
        )

        # Accumulate total energy (kW * hours = kWh)
        sim_interval_hours = 16.0 / 60.0  # 16 minutes
        self._total_energy_generated += energy_generated * sim_interval_hours
        self._total_energy_consumed += energy_consumed * sim_interval_hours

        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            energy_generated=energy_generated,
            energy_consumed=energy_consumed,
            power_generated=float(data.get("power_generated", energy_generated)),
            power_consumed=float(data.get("power_consumed", energy_consumed)),
            total_energy_generated=round(self._total_energy_generated, 4),
            total_energy_consumed=round(self._total_energy_consumed, 4),
            surplus_energy=surplus,
            deficit_energy=deficit,
            battery_level=self.battery_level,
            location=self.config.get("location", [0.0, 0.0]),
            latitude=self.latitude,
            longitude=self.longitude,
            meter_type=self.config.get("meter_type", "Grid_Consumer"),
            user_type=self.config.get("user_type", "Residential"),
            grid_zone_id=self.grid_zone_id,
            voltage=float(data.get("voltage", 230.0)),
            # Calculate current from physics: I = P / (V * PF)
            current=self._calculate_current_from_power(
                energy_consumed + energy_generated,
                float(data.get("voltage", 230.0)),
                float(data.get("power_factor", 0.95))
            ),
            frequency=float(data.get("frequency", 50.0)),
            temperature=float(data.get("temperature", 25.0)),
            power_factor=float(data.get("power_factor", 0.95)),
            max_sell_price=float(data.get("max_sell_price", self.current_sell_price)),
            max_buy_price=float(data.get("max_buy_price", self.current_buy_price)),
            rec_eligible=rec_eligible,
            carbon_offset=carbon_offset,
            net_emission=net_emission,
            weather_condition=self.current_weather,
            wallet_address=self.wallet_address,
        )

        # Sign Data using canonical message format
        canonical_message = (
            f"GRIDTOKENX_METER_READING\n"
            f"meter_serial: {self.meter_id}\n"
            f"timestamp: {reading.timestamp.isoformat()}\n"
            f"kwh_amount: {surplus:.6f}\n"
            f"wallet: {self.wallet_address}"
        )

        reading.meter_signature = self.key_manager.sign_data(canonical_message)
        
        # Inject simulated balance data into the reading object for frontend display
        reading.balance_gtx = round(self.balance_gtx, 2)
        reading.balance_nrg = round(self.balance_nrg, 2)
        
        self.last_reading = reading
        return reading

    def _calculate_solar_generation(self, timestamp: datetime) -> float:
        """Calculate solar generation based on capacity and weather (time-independent)."""
        capacity = self.config.get("solar_capacity", 5.0)
        efficiency = self.config.get("panel_efficiency", 0.18)

        # Use dynamic irradiance from weather system (no time dependency)
        # Scaling factor reduced for realistic output
        generation = capacity * efficiency * self.irradiance_factor * 1.5

        return max(0, generation)

    def _calculate_consumption(self, timestamp: datetime) -> float:
        base = self.config.get("base_consumption", 1.0)
        # Delegate to LoadProfile
        return self.profile.calculate_consumption(timestamp, base)

    def _update_battery(self, gen: float, cons: float):
        capacity = self.config.get("battery_capacity", 10.0)
        net = gen - cons

        if net > 0:  # Charge
            charge = min(net, capacity - self.battery_level)
            self.battery_level += charge
        else:  # Discharge
            discharge = min(abs(net), self.battery_level)
            self.battery_level -= discharge

        self.battery_level = max(0, min(capacity, self.battery_level))
