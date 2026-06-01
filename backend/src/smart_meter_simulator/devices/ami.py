import random
from datetime import datetime
from typing import Dict, Any, Optional

from ..models.reading import EnergyReading
from ..utils.crypto import KeyManager
from ..config import AccuracyClass, METER_TYPE_CHANNELS, MeterType, get_config
from smart_meter_simulator.core.meter_logic import profiles, electrical
from .bess import BESS
from .ev_charger import EVCharger


class SmartMeter:
    """
    Represents a single smart meter instance (AMI).
    Delegates complex generation/consumption and physics logic to modular utilities.
    """

    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config["meter_id"]
        if config.get("meter_type") == "Residential":
            config["meter_type"] = "Residential"
        self.config = config
        self.key_manager = KeyManager()
        # AES-256 key for Protocol v4. In production, this would be injected or derived.
        # Here we use a deterministic but unique key per meter for simulation consistency.
        import hashlib
        self.device_key = hashlib.sha256(f"secret-{self.meter_id}".encode()).digest()
        self.sequence_number = 0

        # Sub-modules
        self.bess = BESS(config) if config.get("has_battery") else None

        try:
            meter_type_enum = MeterType(self.config["meter_type"])
        except ValueError:
            logger.warning(f"Unknown meter type: {self.config.get('meter_type')}, defaulting to GRID_CONSUMER")
            meter_type_enum = MeterType.GRID_CONSUMER
        if meter_type_enum in (MeterType.EV_CHARGER, MeterType.DC_FAST_CHARGER):
            self.ev_charger = EVCharger(config)
        else:
            self.ev_charger = None

        self.current_weather = "Sunny"
        self.current_frequency = 50.0
        self.last_cons_noise = 0.0
        self.last_gen_noise = 0.0
        self.vpp_dispatch_kw = 0.0
        self.priority = config.get("priority", 2)
        self.is_shed = False

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
            MeterType.DC_FAST_CHARGER: AccuracyClass.CLASS_0_5,
        }
        self.accuracy_class = accuracy_defaults.get(
            meter_type_enum, AccuracyClass.CLASS_2_0
        )
        self.channels = METER_TYPE_CHANNELS.get(meter_type_enum, set())

    @property
    def battery_level(self) -> float:
        """Helper to get current battery SOC percent."""
        if self.ev_charger:
            return self.ev_charger.soc_percent
        if self.bess:
            return self.bess.get_soc_percent()
        return 0.0

    def update_weather(self, weather: str):
        self.current_weather = weather

    def receive_frequency(self, frequency_hz: float):
        self.current_frequency = frequency_hz

    def receive_dispatch(self, dispatch_kw: float):
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
        grid_stress: float = 1.0,
    ) -> EnergyReading:
        time_factor = interval_seconds / 3600.0
        if self.vpp_dispatch_kw != 0:
            forced_dispatch = self.vpp_dispatch_kw

        # 1. Generation & Consumption
        gen, self.last_gen_noise = (
            profiles.calculate_solar_generation(
                timestamp, self.config, self.current_weather, self.last_gen_noise
            )
            if override_gen is None and self.config.get("has_solar")
            else (override_gen or 0.0, self.last_gen_noise)
        )
        cons, self.last_cons_noise = (
            profiles.calculate_consumption(
                timestamp, self.config, self.meter_id, self.last_cons_noise
            )
            if override_cons is None
            else (override_cons, self.last_cons_noise)
        )

        if grid_stress != 1.0 and override_cons is None:
            cons *= grid_stress
        if self.is_shed:
            cons = 0.0

        # 2. Physics & Controls
        gen, cons = electrical.apply_droop_control(gen, cons, self.current_frequency)

        if self.bess:
            self.bess.update(gen, cons, forced_dispatch, time_factor)

        if self.ev_charger:
            ev_gen, ev_cons = self.ev_charger.update(timestamp)
            gen += ev_gen / time_factor if time_factor > 0 else 0.0
            cons += ev_cons / time_factor if time_factor > 0 else 0.0

        # 3. Electrical parameters with noise
        e_params = electrical.calculate_electrical_params(
            gen, cons, self.accuracy_class.value, self.channels
        )

        self.sequence_number += 1

        # Determine reported battery level (EV or BESS)
        reported_soc = 0.0
        if self.ev_charger:
            reported_soc = self.ev_charger.soc_percent
        elif self.bess:
            reported_soc = self.bess.get_soc_percent()

        reading = EnergyReading(
            meter_id=self.meter_id,
            timestamp=timestamp,
            sequence_number=self.sequence_number,
            energy_generated=round(gen * time_factor, 6),
            energy_consumed=round(cons * time_factor, 6),
            surplus_energy=round(max(0, (gen - cons) * time_factor), 6),
            deficit_energy=round(max(0, (cons - gen) * time_factor), 6),
            interval_seconds=interval_seconds,
            battery_level=round(reported_soc, 1),
            location=self.config.get("location", "Unknown"),
            meter_type=self.config.get("meter_type", "Unknown"),
            user_type=self.config.get("user_type", "Unknown"),
            voltage=round(e_params.get("voltage"), 2)
            if "voltage" in e_params
            else None,
            current=round(e_params.get("current"), 3)
            if "current" in e_params
            else None,
            reactive_power_kvar=round(e_params.get("reactive_power"), 3)
            if "reactive_power" in e_params
            else None,
            frequency=round(e_params.get("frequency"), 2)
            if "frequency" in e_params
            else None,
            power_factor=round(e_params.get("power_factor"), 2)
            if "power_factor" in e_params
            else None,
            temperature=round(random.gauss(20.0, 5.0), 1),
            nodal_price=nodal_price,
            carbon_intensity=carbon_intensity,
            rec_eligible=False,
            carbon_offset=0.0,
            weather_condition=self.current_weather,
            device_key=self.device_key,
        )

        # 4. Signing (Path A - real-time telemetry)
        cfg = get_config()
        if getattr(cfg, "enable_protocol_v4", False):
            # Protocol v4 (UTT-S+) signing logic
            # Signature is over: {meter_id}:{kwh}:{timestamp_ms}:{sequence}
            sign_target = reading.get_v4_signature_canonical_string()
            reading.meter_signature = self.key_manager.sign_data(sign_target)
            # Binary payload is encrypted TLV
            # Note: In gRPC transport, we might want to store this raw payload
            # For now, we can add a property or field to EnergyReading if needed,
            # but generate_protocol_v4_payload(self.device_key) can be called later.
        elif cfg.transport_type == "grpc" and cfg.enable_dlms_binary:
            binary_payload = reading.generate_dlms_payload()
            reading.meter_signature = self.key_manager.sign_binary_data(binary_payload)
        else:
            # Legacy Path
            kwh_str = f"{reading.surplus_energy:.6f}"
            ts_seconds = int(reading.timestamp.timestamp())
            sign_target = f"{self.meter_id}:{kwh_str}:{ts_seconds}"
            reading.meter_signature = self.key_manager.sign_data(sign_target)
        return reading
