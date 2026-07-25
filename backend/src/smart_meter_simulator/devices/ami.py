import hashlib
import logging
import random
from datetime import datetime
from typing import Any, Dict, Optional

from smart_meter_simulator.core.meter_logic import electrical

from ..config import METER_TYPE_CHANNELS, AccuracyClass, MeterType, get_config
from ..models.reading import EnergyReading
from ..pricing.thai_tariff import is_peak_period
from .battery import Battery
from .ev import EVCharger
from .load import Load
from .solar import Solar

logger = logging.getLogger(__name__)


def _meter_seed(meter_id: str, base_seed: int) -> int:
    """Derive a stable per-meter RNG seed from the global seed + meter id.

    Uses a process-stable SHA-256 digest of the meter id (Python's built-in
    ``hash`` is salted per-process, so it cannot be used). Each meter draws its
    noise from an independent stream, so adding or removing a meter does not
    shift any other meter's readings.
    """
    digest = hashlib.sha256(str(meter_id).encode("utf-8")).digest()[:8]
    return base_seed ^ int.from_bytes(digest, "big")


class SmartMeter:
    """
    Represents a single smart meter instance (AMI).
    Delegates complex generation/consumption and physics logic to modular utilities.
    """

    def __init__(self, config: Dict[str, Any]):
        self.meter_id = config["meter_id"]
        self.config = config
        # Stored as an attribute (not only in config) so engine snapshots that tag
        # derived points by meter type read the real value, not "".
        self.meter_type = config.get("meter_type", "")
        self.sequence_number = 0

        # Lifetime energy accumulators (kWh) for per-meter billing. Import =
        # grid deficit (consumption > generation), export = surplus sold back to
        # the grid. Peak/off-peak import is split by the Thai TOU window so a TOU
        # tariff can be billed too. Reset when the fleet is rebuilt.
        self.cumulative_import_kwh = 0.0
        self.cumulative_export_kwh = 0.0
        self.cumulative_peak_import_kwh = 0.0
        self.cumulative_offpeak_import_kwh = 0.0

        # Independent per-meter noise stream for deterministic runs.
        self._rng = random.Random(_meter_seed(self.meter_id, get_config().random_seed))

        # Sub-modules
        self.load = Load(config)
        self.solar = Solar(config) if config.get("has_solar") else None
        self.battery = Battery(config) if config.get("has_battery") else None
        self.ev = EVCharger(config) if config.get("has_ev_charger") else None

        # Local distribution-transformer loading (%) from the prior tick's solve,
        # fed to the BESS for congestion-relief dispatch (one-tick lag, like
        # frequency). Defaults to 0 so a BESS is inert until the grid reports.
        self._transformer_loading_pct = 0.0

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
            MeterType.BESS: AccuracyClass.CLASS_0_5,
            MeterType.EV_CHARGER: AccuracyClass.CLASS_1_0,
            MeterType.DC_FAST_CHARGER: AccuracyClass.CLASS_0_5,
        }
        self.accuracy_class = accuracy_defaults.get(
            meter_type_enum, AccuracyClass.CLASS_2_0
        )
        self.channels = METER_TYPE_CHANNELS.get(meter_type_enum, set())

    def update_weather(self, weather: str):
        self.current_weather = weather

    def receive_frequency(self, frequency_hz: float):
        self.current_frequency = frequency_hz

    def receive_grid_loading(self, loading_pct: float):
        """Store the prior tick's local transformer loading (%) for BESS
        congestion-relief dispatch."""
        self._transformer_loading_pct = loading_pct

    def generate_reading(
        self,
        timestamp: datetime,
        override_gen: Optional[float] = None,
        override_cons: Optional[float] = None,
        override_reactive_kvar: Optional[float] = None,
        interval_seconds: int = 15,
        grid_stress: float = 1.0,
        grid_voltage_pu: float = 1.0,
        dr_load_factor: float = 1.0,
    ) -> EnergyReading:
        time_factor = interval_seconds / 3600.0

        # 1. Generation & Consumption
        gen, self.last_gen_noise = (
            (
                self.solar.get_generation_kw(
                    timestamp, self.current_weather, rng=self._rng
                ),
                self.last_gen_noise,
            )
            if override_gen is None and self.solar
            else (override_gen or 0.0, self.last_gen_noise)
        )

        cons = (
            self.load.get_consumption_kw(
                timestamp, voltage_pu=grid_voltage_pu, rng=self._rng
            )
            if override_cons is None
            else override_cons
        )

        if grid_stress != 1.0 and override_cons is None:
            cons *= grid_stress

        # Demand-response load shed. A utility DR event curtails the flexible
        # portion of the load while the event window is active. Skipped on real
        # telemetry overrides (the reported draw already reflects any shed). The
        # shed power is recorded so the feeder relief is accountable; reported
        # consumption is net of it.
        dr_shed_kw: Optional[float] = None
        if dr_load_factor < 1.0 and override_cons is None:
            pre_shed = cons
            cons *= dr_load_factor
            dr_shed_kw = pre_shed - cons

        # Smart Inverter Over-Voltage Curtailment Logic
        self.inverter_curtailed = False
        if gen > 0 and grid_voltage_pu > 1.05:
            # Linear curtailment from 1.05 pu (100% gen) to 1.10 pu (0% gen)
            curtailment_factor = max(0.0, 1.0 - (grid_voltage_pu - 1.05) * 20.0)
            gen *= curtailment_factor
            self.inverter_curtailed = True

        # 2. Physics & Controls
        gen, cons = electrical.apply_droop_control(gen, cons, self.current_frequency)

        # 2b. Storage & EV dispatch — applied AFTER apply_droop_control so the
        # battery's own frequency-watt droop is not re-scaled by the generation-only
        # governor law above (double-counting). EV is a constant-power additive load.
        battery_soc_pct: Optional[float] = None
        battery_dispatch_kw: Optional[float] = None
        ev_charge_kw: Optional[float] = None

        if self.ev is not None and override_cons is None:
            ev_charge_kw = self.ev.get_charge_kw(timestamp, rng=self._rng)
            cons += ev_charge_kw

        if self.battery is not None and override_gen is None and override_cons is None:
            disp = self.battery.dispatch(
                self.current_frequency,
                self._transformer_loading_pct,
                interval_seconds,
            )
            battery_dispatch_kw = disp
            battery_soc_pct = self.battery.soc_pct
            if disp > 0:  # discharge -> grid injection
                gen += disp
            elif disp < 0:  # charge -> load
                cons += -disp

        # 3. Electrical parameters with noise
        e_params = electrical.calculate_electrical_params(
            gen,
            cons,
            self.accuracy_class.value,
            self.channels,
            grid_voltage_pu=grid_voltage_pu,
            rng=self._rng,
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
            temperature=round(self._rng.gauss(20.0, 5.0), 1),
            weather_condition=self.current_weather,
            # Per-unit voltage at this meter's bus (from the prior tick's solve),
            # the same value the ZIP load model was evaluated against.
            voltage_pu=round(grid_voltage_pu, 5),
            dr_shed_kw=(round(dr_shed_kw, 3) if dr_shed_kw is not None else None),
            battery_soc_pct=(
                round(battery_soc_pct, 4) if battery_soc_pct is not None else None
            ),
            battery_dispatch_kw=(
                round(battery_dispatch_kw, 4)
                if battery_dispatch_kw is not None
                else None
            ),
            ev_charge_kw=(round(ev_charge_kw, 4) if ev_charge_kw is not None else None),
        )

        # Accumulate lifetime energy for per-meter billing. Surplus is sold back
        # to the grid (export buy-back); deficit is grid import, split into the
        # TOU peak/off-peak buckets so either tariff structure can be billed.
        self.cumulative_export_kwh += reading.surplus_energy
        self.cumulative_import_kwh += reading.deficit_energy
        if is_peak_period(timestamp):
            self.cumulative_peak_import_kwh += reading.deficit_energy
        else:
            self.cumulative_offpeak_import_kwh += reading.deficit_energy

        return reading
