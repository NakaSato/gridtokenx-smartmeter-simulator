import random
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..models.reading import EnergyReading, MeasurementChannel
from ..utils.crypto import KeyManager
from ..config import SimulatorConfig, AccuracyClass, METER_TYPE_CHANNELS, MeterType

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
        
        # Accuracy and Channels
        # Assign default accuracy class based on meter type if not specified
        meter_type_enum = MeterType(self.config['meter_type'])
        
        # Default mapping from meter type to accuracy class
        accuracy_defaults = {
            MeterType.RESIDENTIAL: AccuracyClass.CLASS_2_0,
            MeterType.GRID_CONSUMER: AccuracyClass.CLASS_2_0,
            MeterType.COMMERCIAL: AccuracyClass.CLASS_1_0,
            MeterType.SOLAR_PROSUMER: AccuracyClass.CLASS_1_0,
            MeterType.HYBRID_PROSUMER: AccuracyClass.CLASS_1_0,
            MeterType.BATTERY_STORAGE: AccuracyClass.CLASS_0_5,
            MeterType.FEEDER: AccuracyClass.CLASS_0_5,
            MeterType.SUBSTATION: AccuracyClass.CLASS_0_2,
        }
        self.accuracy_class = accuracy_defaults.get(meter_type_enum, AccuracyClass.CLASS_2_0)
        
        # Assign channels
        self.channels = METER_TYPE_CHANNELS.get(meter_type_enum, set())

    def update_weather(self, weather: str):
        self.current_weather = weather
        
    def generate_reading(
        self, 
        timestamp: datetime, 
        override_gen: Optional[float] = None,
        override_cons: Optional[float] = None
    ) -> EnergyReading:
        """Generate a signed energy reading for the current timestamp."""
        
        # 1. Calculate Generation (Solar)
        energy_generated = override_gen if override_gen is not None else 0.0
        if override_gen is None and self.config.get('has_solar'):
            energy_generated = self._calculate_solar_generation(timestamp)
            
        # 2. Calculate Consumption
        energy_consumed = override_cons if override_cons is not None else self._calculate_consumption(timestamp)
        
        # 3. Battery Logic
        if self.config.get('has_battery'):
            self._update_battery(energy_generated, energy_consumed)
            
        # 4. Calculate Net & Trading
        net_energy = energy_generated - energy_consumed
        surplus = max(0, net_energy)
        deficit = max(0, -net_energy)
        
        # 5. Create Reading with all required fields
        # Measurement Noise Calculation based on Accuracy Class
        # σ = (AccuracyClass / 300) * NominalValue (using sigma_factor=3 logic from adapter)
        # We can implement a simplified noise generation here directly
        
        # Helper to apply accuracy-based noise
        def apply_noise(value, multiplier=1.0):
             # Multiplier allows higher uncertainty for Q (3.0) vs P (2.0) vs V (1.0)
             if value == 0: return 0.0
             sigma = (self.accuracy_class.value / 300.0) * abs(value) * multiplier
             return random.gauss(value, sigma)

        # Generate electrical parameters only if channel is active
        voltage = None
        if "v" in self.channels:
            voltage = apply_noise(240.0, 1.0) # Nominal 240V
            
        current = None
        if "i" in self.channels:
            # Approx current from power
            apparent_power = math.sqrt(energy_consumed**2 + energy_generated**2) * 4 # kW
            if voltage:
                current_val = (apparent_power * 1000) / voltage
                current = apply_noise(current_val, 1.0)
            else:
                current = 0.0 # Fallback
                
        # Power factor
        power_factor = None
        if "p" in self.channels or "q" in self.channels:
             power_factor = min(1.0, apply_noise(0.95, 0.5))

        # Frequency
        frequency = None
        if "v" in self.channels:
             frequency = apply_noise(50.0, 0.1)
             
        # Add noise to energy readings (Active Power proxy)
        # Energy itself is integral of power, but let's assume the reading reflects the accuracy
        # Applying noise to the accumulated energy might be wrong, but for instant power snapshot logic
        # embedded in these fields, let's keep it simple. The adapter uses P = Energy * 4.
        
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
            voltage=round(voltage, 2) if voltage else None,
            current=round(current, 3) if current else None,
            frequency=round(frequency, 2) if frequency else None,
            temperature=temperature,
            power_factor=round(power_factor, 2) if power_factor else None,
            max_sell_price=self.config.get('max_sell_price', SimulatorConfig.MAX_SELL_PRICE),
            max_buy_price=self.config.get('max_buy_price', SimulatorConfig.MAX_BUY_PRICE),
            rec_eligible=rec_eligible,
            carbon_offset=round(carbon_offset, 4),
            weather_condition=self.current_weather
        )
        
        # 6. Sign Data
        # Sign payload: kwh_amount|reading_timestamp
        # Must match the format used in to_submission_payload (string precision)
        kwh_str = f"{reading.energy_generated:.6f}"
        timestamp_str = reading.timestamp.isoformat()
        
        payload = f"{kwh_str}|{timestamp_str}"
        reading.meter_signature = self.key_manager.sign_data(payload)
        
        return reading

    def generate_confidential_bid(self, reading: EnergyReading) -> Optional[Dict[str, Any]]:
        """
        Evaluate if the meter should participate in a confidential auction.
        Returns a bid payload if thresholds are met, else None.
        """
        # Thresholds: bid if surplus > 1.0 or deficit > 1.0
        # In a real system, these would be configurable or market-driven
        
        is_bid = False
        amount = 0.0
        
        if reading.surplus_energy > 0.5:
            is_bid = False # Surplus -> Sell (Ask)
            amount = reading.surplus_energy
        elif reading.deficit_energy > 0.5:
            is_bid = True # Deficit -> Buy (Bid)
            amount = reading.deficit_energy
        else:
            return None
            
        # Mock ElGamal Encrypted Ciphertext (64 bytes)
        # In Phase 6, replace with real Python ElGamal
        mock_price_ciphertext = bytes([1] * 64)
        mock_amount_ciphertext = bytes([2] * 64)
        
        return {
            "is_bid": is_bid,
            "amount": amount,
            "encrypted_price": mock_price_ciphertext.hex(),
            "encrypted_amount": mock_amount_ciphertext.hex(),
            "meter_id": self.meter_id
        }

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
