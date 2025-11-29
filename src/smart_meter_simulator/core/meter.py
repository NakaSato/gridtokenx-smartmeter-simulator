import random
import math
from datetime import datetime
from typing import Dict, Any, Optional

from ..models.reading import EnergyReading
from ..utils.crypto import KeyManager
from ..config import SimulatorConfig
from .profiles import get_profile


class SmartMeter:
    """
    Represents a single smart meter instance.
    Handles energy generation/consumption logic and cryptographic signing.
    """

    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config["meter_id"]
        self.config = config
        self.latitude = config.get("latitude")
        self.longitude = config.get("longitude")
        self.key_manager = KeyManager()  # Generates new keypair on init

        # State
        self.battery_level = config.get("current_battery_level", 0.0)
        self.current_weather = "Sunny"  # Default, updated by engine
        self.irradiance_factor = 1.0
        self.temp_offset = 0.0

        # Connection status to API Gateway
        self.is_connected = False  # Updated by engine after each send attempt
        self.last_reading = None  # Store last generated reading for status display

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

    @property
    def wallet_address(self) -> str:
        return self.key_manager.get_wallet_address()

    def update_weather(self, weather: str, irradiance: float, temp_offset: float):
        self.current_weather = weather
        self.irradiance_factor = irradiance
        self.temp_offset = temp_offset

    def update_prices(self, sell_price: float, buy_price: float):
        self.current_sell_price = sell_price
        self.current_buy_price = buy_price

    def generate_reading(self, timestamp: datetime) -> EnergyReading:
        """Generate a signed energy reading for the current timestamp."""

        # Check for static data override
        if hasattr(self, "static_data") and self.static_data:
            return self._generate_static_reading(timestamp)

        # 1. Calculate Generation (Solar)
        energy_generated = 0.0
        if self.config.get("has_solar"):
            energy_generated = self._calculate_solar_generation(timestamp)

        # 2. Calculate Consumption
        energy_consumed = self._calculate_consumption(timestamp)

        # 3. Battery Logic
        if self.config.get("has_battery"):
            self._update_battery(energy_generated, energy_consumed)

        # 4. Calculate Net & Trading
        net_energy = energy_generated - energy_consumed
        surplus = max(0, net_energy)
        deficit = max(0, -net_energy)

        # 5. Create Reading with all required fields
        # Base temp 20C + weather offset + random fluctuation
        temperature = round(20.0 + self.temp_offset + random.gauss(0, 1.0), 1)

        # Determine REC eligibility and carbon offset
        rec_eligible = self.config.get("has_solar", False) and energy_generated > 0
        carbon_offset = (
            energy_generated * SimulatorConfig.CARBON_OFFSET_RATE
            if rec_eligible
            else 0.0
        )

        net_emission = (energy_consumed * self.GRID_EMISSION_FACTOR) - (
            energy_generated * (self.GRID_EMISSION_FACTOR - self.SOLAR_EMISSION_FACTOR)
        )

        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            energy_generated=round(energy_generated, 4),
            energy_consumed=round(energy_consumed, 4),
            surplus_energy=round(surplus, 4),
            deficit_energy=round(deficit, 4),
            battery_level=round(self.battery_level, 1),
            location=self.config["location"],
            latitude=self.latitude,
            longitude=self.longitude,
            meter_type=self.config["meter_type"],
            user_type=self.config["user_type"],
            voltage=round(random.gauss(240.0, 2.0), 2),
            current=round((energy_consumed + energy_generated) / 240.0 * 1000, 3)
            if energy_consumed + energy_generated > 0
            else 0,
            frequency=round(random.gauss(50.0, 0.05), 2),
            temperature=temperature,
            power_factor=min(1.0, round(random.gauss(0.95, 0.02), 2)),
            max_sell_price=round(self.current_sell_price, 4),
            max_buy_price=round(self.current_buy_price, 4),
            rec_eligible=rec_eligible,
            carbon_offset=round(carbon_offset, 4),
            net_emission=round(net_emission, 4),
            weather_condition=self.current_weather,
            wallet_address=self.wallet_address,
        )

        # 6. Sign Data
        # Sign payload: kwh_amount|reading_timestamp
        # Must match the format used in to_submission_payload (string precision)
        kwh_str = f"{energy_generated:.6f}"
        timestamp_str = reading.timestamp.isoformat()

        payload = f"{kwh_str}|{timestamp_str}"
        reading.meter_signature = self.key_manager.sign_data(payload)

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

        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            energy_generated=energy_generated,
            energy_consumed=energy_consumed,
            surplus_energy=surplus,
            deficit_energy=deficit,
            battery_level=self.battery_level,
            location=self.config["location"],
            latitude=self.latitude,
            longitude=self.longitude,
            meter_type=self.config["meter_type"],
            user_type=self.config["user_type"],
            voltage=float(data.get("voltage", 240.0)),
            current=float(data.get("current", 0.0)),
            frequency=float(data.get("frequency", 50.0)),
            temperature=float(data.get("temperature", 25.0)),
            power_factor=float(data.get("power_factor", 1.0)),
            max_sell_price=float(data.get("max_sell_price", self.current_sell_price)),
            max_buy_price=float(data.get("max_buy_price", self.current_buy_price)),
            rec_eligible=rec_eligible,
            carbon_offset=carbon_offset,
            net_emission=net_emission,
            weather_condition=self.current_weather,
            wallet_address=self.wallet_address,
        )

        # Sign Data
        kwh_str = f"{energy_generated:.6f}"
        timestamp_str = reading.timestamp.isoformat()
        payload = f"{kwh_str}|{timestamp_str}"
        reading.meter_signature = self.key_manager.sign_data(payload)

        return reading

    def _calculate_solar_generation(self, timestamp: datetime) -> float:
        hour = timestamp.hour + timestamp.minute / 60.0

        # Solar window: 6am to 6pm
        if not (6 <= hour <= 18):
            return 0.0

        # Solar curve (Bell curve)
        # Peak at 12:00 PM
        time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2

        capacity = self.config.get("solar_capacity", 5.0)
        efficiency = self.config.get("panel_efficiency", 0.18)

        # Use dynamic irradiance from weather system
        generation = (
            capacity * time_factor * efficiency * self.irradiance_factor * 10
        )  # Scaling factor

        # Add some cloud passing noise
        noise = random.gauss(0, generation * 0.05)
        return max(0, generation + noise)

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
