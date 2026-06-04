import logging
import random
from datetime import datetime
from typing import Any, Dict, Optional

from smart_meter_simulator.core.meter_logic import electrical

from ..config import METER_TYPE_CHANNELS, AccuracyClass, MeterType
from ..models.reading import EnergyReading
from .load import Load
from .solar import Solar

logger = logging.getLogger(__name__)


class SmartMeter:
    """
    Represents a single smart meter instance (AMI).
    Delegates complex generation/consumption and physics logic to modular utilities.
    """

    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config["meter_id"]
        self.config = config
        self.sequence_number = 0

        # Sub-modules
        self.load = Load(config)
        self.solar = Solar(config) if config.get("has_solar") else None

        try:
            meter_type_enum = MeterType(self.config["meter_type"])
        except ValueError:
            logger.warning(
                f"Unknown meter type: {self.config.get('meter_type')}, defaulting to GRID_CONSUMER"
            )
            meter_type_enum = MeterType.GRID_CONSUMER

        self.current_weather = "Sunny"
        self.current_frequency = 50.0
        self.last_cons_noise = 0.0
        self.last_gen_noise = 0.0

        accuracy_defaults = {
            MeterType.RESIDENTIAL: AccuracyClass.CLASS_2_0,
            MeterType.GRID_CONSUMER: AccuracyClass.CLASS_2_0,
            MeterType.COMMERCIAL: AccuracyClass.CLASS_1_0,
            MeterType.SOLAR_PROSUMER: AccuracyClass.CLASS_1_0,
            MeterType.HYBRID_PROSUMER: AccuracyClass.CLASS_1_0,
            MeterType.FEEDER: AccuracyClass.CLASS_0_5,
            MeterType.SUBSTATION: AccuracyClass.CLASS_0_2,
        }
        self.accuracy_class = accuracy_defaults.get(
            meter_type_enum, AccuracyClass.CLASS_2_0
        )
        self.channels = METER_TYPE_CHANNELS.get(meter_type_enum, set())

    def update_weather(self, weather: str):
        self.current_weather = weather

    def receive_frequency(self, frequency_hz: float):
        self.current_frequency = frequency_hz

    def generate_reading(
        self,
        timestamp: datetime,
        override_gen: Optional[float] = None,
        override_cons: Optional[float] = None,
        override_reactive_kvar: Optional[float] = None,
        interval_seconds: int = 15,
        grid_stress: float = 1.0,
        grid_voltage_pu: float = 1.0,
    ) -> EnergyReading:
        time_factor = interval_seconds / 3600.0

        # 1. Generation & Consumption
        gen, self.last_gen_noise = (
            (
                self.solar.get_generation_kw(timestamp, self.current_weather),
                self.last_gen_noise,
            )
            if override_gen is None and self.solar
            else (override_gen or 0.0, self.last_gen_noise)
        )

        cons = (
            self.load.get_consumption_kw(timestamp, voltage_pu=grid_voltage_pu)
            if override_cons is None
            else override_cons
        )

        if grid_stress != 1.0 and override_cons is None:
            cons *= grid_stress

        # Smart Inverter Over-Voltage Curtailment Logic
        self.inverter_curtailed = False
        if gen > 0 and grid_voltage_pu > 1.05:
            # Linear curtailment from 1.05 pu (100% gen) to 1.10 pu (0% gen)
            curtailment_factor = max(0.0, 1.0 - (grid_voltage_pu - 1.05) * 20.0)
            gen *= curtailment_factor
            self.inverter_curtailed = True

        # 2. Physics & Controls
        gen, cons = electrical.apply_droop_control(gen, cons, self.current_frequency)

        # 3. Electrical parameters with noise
        e_params = electrical.calculate_electrical_params(
            gen,
            cons,
            self.accuracy_class.value,
            self.channels,
            grid_voltage_pu=grid_voltage_pu,
        )

        self.sequence_number += 1

        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            sequence_number=self.sequence_number,
            energy_generated=round(gen * time_factor, 6),
            energy_consumed=round(cons * time_factor, 6),
            surplus_energy=round(max(0, (gen - cons) * time_factor), 6),
            deficit_energy=round(max(0, (cons - gen) * time_factor), 6),
            interval_seconds=interval_seconds,
            location=self.config.get("location", "Unknown"),
            meter_type=self.config.get("meter_type", "Unknown"),
            user_type=self.config.get("user_type", "Unknown"),
            voltage=(
                round(e_params.get("voltage"), 2) if "voltage" in e_params else None
            ),
            current=(
                round(e_params.get("current"), 3) if "current" in e_params else None
            ),
            reactive_power_kvar=(
                round(override_reactive_kvar, 3)
                if override_reactive_kvar is not None
                else (
                    round(e_params.get("reactive_power"), 3)
                    if "reactive_power" in e_params
                    else None
                )
            ),
            frequency=(
                round(e_params.get("frequency"), 2) if "frequency" in e_params else None
            ),
            power_factor=(
                round(e_params.get("power_factor"), 2)
                if "power_factor" in e_params
                else None
            ),
            temperature=round(random.gauss(20.0, 5.0), 1),
            weather_condition=self.current_weather,
        )
        return reading
