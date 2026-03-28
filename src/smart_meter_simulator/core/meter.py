import random
import math
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..models.reading import EnergyReading, MeasurementChannel
from ..utils.crypto import KeyManager
from ..config import AccuracyClass, METER_TYPE_CHANNELS, MeterType, get_config
from .market import CurrentTariff

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
        self.current_tariff: Optional[CurrentTariff] = None
        self.current_frequency: float = 50.0 # Hz
        self.last_cons_noise = 0.0
        self.last_gen_noise = 0.0
        self.vpp_dispatch_kw = 0.0 # Phase 15: VPP Setpoint
        self.priority = config.get('priority', 2) # Phase 19: 1=Critical, 2=Normal, 3=Sheddable
        self.is_shed = False # Phase 19: Load shedding state
        
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
            MeterType.EV_CHARGER: AccuracyClass.CLASS_1_0,
        }
        self.accuracy_class = accuracy_defaults.get(meter_type_enum, AccuracyClass.CLASS_2_0)
        
        # Assign channels
        self.channels = METER_TYPE_CHANNELS.get(meter_type_enum, set())

    def update_weather(self, weather: str):
        self.current_weather = weather
        
    def receive_price_signal(self, tariff: CurrentTariff):
        self.current_tariff = tariff
        
    def receive_frequency(self, frequency_hz: float):
        self.current_frequency = frequency_hz

    def receive_dispatch(self, dispatch_kw: float):
        """Receive a power setpoint from VPP Orchestrator."""
        self.vpp_dispatch_kw = dispatch_kw
        
    def generate_reading(
        self, 
        timestamp: datetime, 
        override_gen: Optional[float] = None,
        override_cons: Optional[float] = None,
        forced_dispatch: Optional[float] = None,
        interval_seconds: int = 900,
        nodal_price: float = 0.50,
        carbon_intensity: float = 0.0,
        grid_stress: float = 1.0
    ) -> EnergyReading:
        """Generate a signed energy reading for the current timestamp."""
        
        # Scaling factor to convert kW (power) to kWh (energy over interval)
        time_factor = interval_seconds / 3600.0
        
        # Phase 15: Overwrite forced_dispatch with VPP setpoint if active
        if self.vpp_dispatch_kw != 0:
            forced_dispatch = self.vpp_dispatch_kw
            # Important: Clear it after reading or keep it sustained until next update?
            # For this simulation, we'll treat it as a sustained command until reset.
        
        # 1. Calculate Generation (Solar)
        energy_generated = override_gen if override_gen is not None else 0.0
        if override_gen is None and self.config.get('has_solar'):
            energy_generated = self._calculate_solar_generation(timestamp)
            
        # 2. Calculate Consumption
        energy_consumed = override_cons if override_cons is not None else self._calculate_consumption(timestamp)
        
        # Phase 31: Apply Grid Stress
        if grid_stress != 1.0 and override_cons is None:
            energy_consumed *= grid_stress

        # Phase 12: Frequency-Watt Droop Control (Primary Response)
        # If frequency < 50Hz (Under-frequency), decrease load / increase gen
        # If frequency > 50Hz (Over-frequency), increase load / decrease gen
        # Droop setting: 5% (0.05). Means 5% freq change caused 100% power change.
        # K = 1 / 0.05 = 20 pu/pu
        
        f_dev_pu = (self.current_frequency - 50.0) / 50.0
        # Deadband +/- 0.05 Hz (0.001 pu)
        if abs(f_dev_pu) > 0.001:
             # Droop gain K = 20
             p_sadj_pu = -20.0 * f_dev_pu
             
             # Apply to Generation (Increase if freq low)
             if energy_generated > 0:
                 # Cap adjustment to +/- 20% of rated
                 adj_gen = max(-0.2, min(0.2, p_sadj_pu))
                 energy_generated *= (1 + adj_gen)
                 
             # Apply to Consumption (Decrease if freq low - Demand Response)
             # Only for smart appliances (assume 50% of load is controllable for now?)
             # adj_cons = max(-0.2, min(0.2, -p_sadj_pu)) # Inverse sign for load
             # energy_consumed *= (1 + adj_cons) 
        
        # 3. Battery Logic
        if self.config.get('has_battery'):
            self._update_battery(energy_generated, energy_consumed, forced_dispatch=forced_dispatch)

        # 3.5 EV Logic
        if MeterType(self.config['meter_type']) == MeterType.EV_CHARGER:
             ev_gen, ev_cons = self._calculate_ev_behavior(timestamp)
             energy_generated += ev_gen
             energy_consumed += ev_cons
            
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
            # Power is in kW
            apparent_power = math.sqrt(energy_consumed**2 + energy_generated**2)
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
        # embedded in these fields, let's keep it simple. The adapter uses P = Energy * 4.
        
        temperature = round(random.gauss(20.0, 5.0), 1)  # Simulated temperature
        
        # Phase 19: Load Shedding Logic
        if self.is_shed:
            energy_consumed = 0.0

        # Phase 20: Scale power (kW) to interval energy (kWh)
        energy_gen_kwh = energy_generated * time_factor
        energy_cons_kwh = energy_consumed * time_factor

        # Calculate Net & Trading in kWh
        net_energy = energy_gen_kwh - energy_cons_kwh
        surplus = max(0, net_energy)
        deficit = max(0, -net_energy)

        # Determine REC eligibility based on generation in interval
        rec_eligible = self.config.get('has_solar', False) and energy_gen_kwh > 0
        config = get_config()
        carbon_offset = energy_gen_kwh * config.carbon_offset_rate if rec_eligible else 0.0
        
        # Reactive power calculation
        reactive_power = None
        if "q" in self.channels:
             p_eff = (energy_consumed - energy_generated)
             pf_val = power_factor if power_factor else 0.95
             q_factor = math.sqrt(1 - pf_val**2) / pf_val if pf_val > 0 else 0
             reactive_power = p_eff * q_factor
        
        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            energy_generated=round(energy_gen_kwh, 6),
            energy_consumed=round(energy_cons_kwh, 6),
            surplus_energy=round(surplus, 6),
            deficit_energy=round(deficit, 6),
            interval_seconds=interval_seconds,
            battery_level=round(self.battery_level, 1),
            location=self.config.get('location', 'Unknown'),
            meter_type=self.config.get('meter_type', 'Unknown'),
            user_type=self.config.get('user_type', 'Unknown'),
            wallet_address=self.config.get('wallet_address'),
            voltage=round(voltage, 2) if voltage else None,
            current=round(current, 3) if current else None,
            reactive_power_kvar=round(reactive_power, 3) if reactive_power is not None else None,
            frequency=round(frequency, 2) if frequency else None,
            temperature=temperature,
            power_factor=round(power_factor, 2) if power_factor else None,
            nodal_price=nodal_price,
            carbon_intensity=carbon_intensity,
            max_sell_price=self.config.get('max_sell_price', config.max_sell_price),
            max_buy_price=self.config.get('max_buy_price', config.min_buy_price),
            rec_eligible=rec_eligible,
            carbon_offset=round(carbon_offset, 6),
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

    def get_bid_params(self, reading: EnergyReading) -> Optional[Dict[str, Any]]:
        """
        Evaluate if a bid is needed and return the parameters for proof generation.
        This part is lightweight and can run on the main loop.
        """
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

        # Return parameters needed for the heavy ZK work
        return {
            "meter_id": self.meter_id,
            "is_bid": is_bid,
            "amount": amount,
            "amount_u64": int(amount * 1000),
            "price_u64": 100 # Mock price or market logic
        }

    def from_worker_result(self, params: Dict[str, Any], result: tuple) -> Dict[str, Any]:
        """Convert worker result back into a bid payload."""
        enc_amount, enc_price, range_proof = result
        
        if enc_amount is None: # Fallback to mock if proof failed
            import hashlib
            import base64
            seed_p = f"{self.meter_id}|proof_fail|price".encode()
            seed_a = f"{self.meter_id}|proof_fail|amount".encode()
            enc_price = base64.b64encode(hashlib.sha512(seed_p).digest()).decode('utf-8')
            enc_amount = base64.b64encode(hashlib.sha512(seed_a).digest()).decode('utf-8')
            range_proof = "mock_range_proof"

        return {
            "is_bid": params["is_bid"],
            "amount": params["amount"],
            "encrypted_price": enc_price,
            "encrypted_amount": enc_amount,
            "range_proof": range_proof,
            "meter_id": self.meter_id
        }

    def _calculate_solar_generation(self, timestamp: datetime) -> float:
        hour = timestamp.hour + timestamp.minute / 60.0
        if not (6 <= hour <= 18):
            return 0.0
            
        # Realistic solar curve (sine with some variation)
        time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2
        capacity = self.config.get('solar_capacity', 5.0)
        efficiency = self.config.get('panel_efficiency', 0.18)
        
        # Weather impact - apply smoothing to transitions
        weather_factors = {
            "Sunny": 1.0,
            "Partly Cloudy": 0.7,
            "Cloudy": 0.4,
            "Rainy": 0.1,
            "Stormy": 0.05,
            "Eclipse": 0.01
        }
        target_weather_factor = weather_factors.get(self.current_weather, 1.0)
        
        # Base generation
        base_gen = capacity * time_factor * efficiency * 2 # Reduced scaling from 5 to 2 for grid stability
        
        # Autocorrelated noise (Brownian motion)
        # This prevents erratic jumping between ticks
        innovation = random.gauss(0, base_gen * 0.02)
        self.last_gen_noise = 0.8 * self.last_gen_noise + innovation
        
        generation = base_gen * target_weather_factor + self.last_gen_noise
        return max(0, generation)

    def _calculate_consumption(self, timestamp: datetime) -> float:
        hour = timestamp.hour + timestamp.minute / 60.0
        weekday = timestamp.weekday() < 5 # True if Mon-Fri
        base = self.config.get('base_consumption', 1.0)
        meter_type = MeterType(self.config['meter_type'])
        
        # Random offset to differentiate meters of the same type
        meter_offset = (hash(self.meter_id) % 100) / 100.0
        
        factor = 1.0
        if meter_type in [MeterType.RESIDENTIAL, MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER]:
            # Residential Profile: Morning and Evening Peaks
            m_peak_time = 7.5 + (meter_offset * 1.5) # Peak around 7:30 - 9:00
            e_peak_time = 18.5 + (meter_offset * 2.0) # Peak around 6:30 - 8:30
            
            m_peak = 0.8 * math.exp(-((hour - m_peak_time) ** 2) / (2 * 1.2 ** 2))
            e_peak = 1.5 * math.exp(-((hour - e_peak_time) ** 2) / (2 * 2.5 ** 2))
            
            # Weekend effect: more consumption throughout the day
            if not weekday:
                factor = 1.2 + m_peak * 0.5 + e_peak * 1.2 + 0.3 * math.sin(math.pi * hour / 24)
            else:
                factor = 0.6 + m_peak + e_peak
                
        elif meter_type == MeterType.COMMERCIAL:
            # Commercial Profile: Business Hours (9 AM - 6 PM)
            if weekday:
                # Flat peak during 9-5
                business_hours = 1.8 if (9 <= hour <= 17) else 0.4
                # Smooth transitions
                if 7 <= hour < 9: # Ramp up
                   business_hours = 0.4 + (1.4 * (hour - 7) / 2.0)
                elif 17 < hour <= 19: # Ramp down
                   business_hours = 1.8 - (1.4 * (hour - 17) / 2.0)
                factor = business_hours + meter_offset * 0.2
            else:
                # Weekend: Very low base consumption
                factor = 0.3 + meter_offset * 0.1
        elif meter_type == MeterType.EV_CHARGER:
            # EV Chargers have very low base consumption when not active
            factor = 0.05 + meter_offset * 0.05
        else:
            # Generic/Industrial Profile
            factor = 1.0 + 0.2 * math.sin(2 * math.pi * hour / 24) + meter_offset
            
        consumption = base * factor
        
        # Price Elasticity Response (Phase 11)
        if self.current_tariff and self.current_tariff.is_peak:
            # Shift load if price is high
            elasticity = self.config.get('price_elasticity', 0.15)
            # Add some randomness to response
            response = elasticity * random.uniform(0.8, 1.2)
            consumption *= (1.0 - response)

        # Autocorrelated noise for consumption
        innovation = random.gauss(0, consumption * 0.015)
        self.last_cons_noise = 0.85 * self.last_cons_noise + innovation
        
        return max(0.1, consumption + self.last_cons_noise)

    def _calculate_ev_behavior(self, timestamp: datetime) -> tuple:
        """
        Simulate EV charging and V2G behavior.
        Returns (generation_kwh, consumption_kwh)
        """
        hour = timestamp.hour + timestamp.minute / 60.0
        
        # Determine if vehicle is at home/charging station
        # Model: Home between 6 PM and 8 AM
        is_at_station = hour >= 18 or hour <= 8
        
        if not is_at_station:
            # Vehicle is away, consuming SoC for driving
            if 8 < hour < 18:
                # Random discharge to simulate driving (0.1-0.8% per simulated reading)
                self.battery_level = max(20.0, self.battery_level - random.uniform(0.1, 0.8))
            return 0.0, 0.0

        gen_kwh = 0.0
        cons_kwh = 0.0
        config = get_config()

        # V2G Logic (Bi-directional) - Check FIRST during peak
        # Discharge if: Peak period (6 PM - 9 PM) and SoC > Threshold
        is_peak = 18 <= hour <= 21
        if is_peak and self.battery_level > (config.ev_v2g_threshold_soc * 100):
            # Moderate discharge
            discharge_power = config.ev_v2g_discharge_rate_kw
            gen_kwh = discharge_power / 4.0
            capacity_kwh = self.config.get('ev_battery_capacity', config.ev_battery_capacity_max)
            self.battery_level = max(0.0, self.battery_level - (gen_kwh / capacity_kwh) * 100)
            # If we are discharging for V2G, don't charge simultaneously
            return gen_kwh, cons_kwh

        # EV Charging Logic (if not in V2G or not peak)
        # Charge if SoC < 90%
        if self.battery_level < 90.0:
            charge_power = config.ev_charge_rate_kw
            # Scale by random to simulate charging curve or availability
            charge_power *= random.uniform(0.8, 1.0)
            cons_kwh = charge_power / 4.0
            # Capacity is in kWh, battery_level is in %
            # Correct SoC update: (cons_kwh / capacity_kwh) * 100
            capacity_kwh = self.config.get('ev_battery_capacity', config.ev_battery_capacity_max)
            self.battery_level = min(100.0, self.battery_level + (cons_kwh / capacity_kwh) * 100)

        return gen_kwh, cons_kwh

    def _update_battery(self, gen: float, cons: float, forced_dispatch: Optional[float] = None):
        capacity = self.config.get('battery_capacity', 10.0)
        net = gen - cons
        
        if forced_dispatch is not None:
            # Positive: Discharge, Negative: Charge
            if forced_dispatch > 0:
                actual = min(forced_dispatch, self.battery_level)
                self.battery_level -= actual
            else:
                actual = min(abs(forced_dispatch), capacity - self.battery_level)
                self.battery_level += actual
        else:
            if net > 0: # Charge
                charge = min(net, capacity - self.battery_level)
                self.battery_level += charge
            else: # Discharge
                discharge = min(abs(net), self.battery_level)
                self.battery_level -= discharge
            
        self.battery_level = max(0, min(capacity, self.battery_level))
