import random
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..models.reading import EnergyReading
from ..utils.crypto import KeyManager
from ..config import SimulatorConfig

class SmartMeter:
    """
    Represents a single smart meter instance.
    Handles energy generation/consumption logic and cryptographic signing.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config['meter_id']
        self.config = config
        self.key_manager = KeyManager()  # Generates new keypair on init
        
        # State
        self.battery_level = config.get('current_battery_level', 0.0)
        self.current_weather = "Sunny" # Default, updated by engine
        
    def update_weather(self, weather: str):
        self.current_weather = weather
        
    def generate_reading(self, timestamp: datetime) -> EnergyReading:
        """Generate a signed energy reading for the current timestamp."""
        
        # 1. Calculate Generation (Solar)
        energy_generated = 0.0
        if self.config.get('has_solar'):
            energy_generated = self._calculate_solar_generation(timestamp)
            
        # 2. Calculate Consumption
        energy_consumed = self._calculate_consumption(timestamp)
        
        # 3. Battery Logic
        if self.config.get('has_battery'):
            self._update_battery(energy_generated, energy_consumed)
            
        # 4. Calculate Net & Trading
        net_energy = energy_generated - energy_consumed
        surplus = max(0, net_energy)
        deficit = max(0, -net_energy)
        
        # 5. Create Reading with all required fields
        temperature = round(random.gauss(20.0, 5.0), 1)  # Simulated temperature
        
        # Determine REC eligibility and carbon offset
        rec_eligible = self.config.get('has_solar', False) and energy_generated > 0
        carbon_offset = energy_generated * SimulatorConfig.CARBON_OFFSET_RATE if rec_eligible else 0.0
        
        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            energy_generated=round(energy_generated, 4),
            energy_consumed=round(energy_consumed, 4),
            surplus_energy=round(surplus, 4),
            deficit_energy=round(deficit, 4),
            battery_level=round(self.battery_level, 1),
            location=self.config['location'],
            meter_type=self.config['meter_type'],
            user_type=self.config['user_type'],
            wallet_address=self.config.get('wallet_address'),  # Add wallet address
            voltage=round(random.gauss(240.0, 2.0), 2),
            current=round((energy_consumed + energy_generated) / 240.0 * 1000, 3) if energy_consumed + energy_generated > 0 else 0,
            frequency=round(random.gauss(50.0, 0.05), 2),
            temperature=temperature,
            power_factor=min(1.0, round(random.gauss(0.95, 0.02), 2)),
            max_sell_price=self.config.get('max_sell_price', SimulatorConfig.MAX_SELL_PRICE),
            max_buy_price=self.config.get('max_buy_price', SimulatorConfig.MAX_BUY_PRICE),
            rec_eligible=rec_eligible,
            carbon_offset=round(carbon_offset, 4),
            weather_condition=self.current_weather
        )
        
        # 6. Sign Data
        # Sign payload: kwh_amount|reading_timestamp
        # Must match the format used in to_submission_payload (string precision)
        kwh_str = f"{energy_generated:.6f}"
        timestamp_str = reading.timestamp.isoformat()
        
        payload = f"{kwh_str}|{timestamp_str}"
        reading.meter_signature = self.key_manager.sign_data(payload)
        
        return reading

    def _calculate_solar_generation(self, timestamp: datetime) -> float:
        hour = timestamp.hour
        if not (6 <= hour <= 18):
            return 0.0
            
        # Simplified solar curve
        time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2
        capacity = self.config.get('solar_capacity', 5.0)
        efficiency = self.config.get('panel_efficiency', 0.18)
        
        # Weather impact
        weather_factor = {
            "Sunny": 1.0,
            "Partly Cloudy": 0.8,
            "Cloudy": 0.5,
            "Rainy": 0.2
        }.get(self.current_weather, 1.0)
        
        generation = capacity * time_factor * efficiency * weather_factor * 10 # Scaling factor
        noise = random.gauss(0, generation * 0.05)
        return max(0, generation + noise)

    def _calculate_consumption(self, timestamp: datetime) -> float:
        hour = timestamp.hour + timestamp.minute / 60.0
        base = self.config.get('base_consumption', 1.0)
        
        # Gaussian peaks for Morning (8am) and Evening (7pm)
        # Peak 1: 8:00 AM, width 2 hours
        morning_peak = 0.8 * math.exp(-((hour - 8) ** 2) / (2 * 1.5 ** 2))
        
        # Peak 2: 7:00 PM, width 2.5 hours
        evening_peak = 1.2 * math.exp(-((hour - 19) ** 2) / (2 * 2.0 ** 2))
        
        # Random variation per meter to avoid identical profiles
        meter_offset = hash(self.meter_id) % 100 / 1000.0
        
        # Combined profile
        factor = 1.0 + morning_peak + evening_peak + meter_offset
        
        consumption = base * factor
        
        # Add random noise (Brownian-like or simple Gaussian)
        noise = random.gauss(0, consumption * 0.1)
        return max(0.1, consumption + noise)

    def _update_battery(self, gen: float, cons: float):
        capacity = self.config.get('battery_capacity', 10.0)
        net = gen - cons
        
        if net > 0: # Charge
            charge = min(net, capacity - self.battery_level)
            self.battery_level += charge
        else: # Discharge
            discharge = min(abs(net), self.battery_level)
            self.battery_level -= discharge
            
        self.battery_level = max(0, min(capacity, self.battery_level))
