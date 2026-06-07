"""Configuration for the GLM grid model simulator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from smart_meter_simulator.config.enums import WeatherCondition

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class SimulatorConfig(BaseSettings):
    """Environment-backed simulator settings."""

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(PROJECT_ROOT / ".env.local")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    simulation_interval: int = Field(default=15, alias="SIMULATION_INTERVAL", gt=0)
    num_meters: int = Field(default=80, alias="NUM_METERS", gt=0)
    output_file: str = Field(default="./data/meter_readings.jsonl", alias="OUTPUT_FILE")
    autostart_simulation: bool = Field(default=True, alias="AUTOSTART_SIMULATION")

    grid_topology: str = Field(
        default="glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm",
        alias="GRID_TOPOLOGY",
        description=(
            "Topology source spec. Supports glm:path/to/file.glm and "
            "reference-grid:path/to/grid_folder."
        ),
    )

    telemetry_source: str = Field(
        default="synthetic",
        alias="TELEMETRY_SOURCE",
        description=(
            "Telemetry source spec. 'synthetic' (device models) or "
            "'replay:path/to/readings.csv' / 'reference-grid:path/to/grid_folder' "
            "to drive meters from real data."
        ),
    )
    meter_registry: str = Field(
        default="",
        alias="METER_REGISTRY",
        description=(
            "Optional path to a meter registry (.csv/.json) pinning real meters to "
            "topology buses. Also accepts reference-grid:path/to/grid_folder. "
            "When set, the fleet is built from it instead of randomly."
        ),
    )

    solar_efficiency_min: float = Field(
        default=0.85, alias="SOLAR_PANEL_EFFICIENCY_MIN", ge=0, le=1
    )
    solar_efficiency_max: float = Field(
        default=0.95, alias="SOLAR_PANEL_EFFICIENCY_MAX", ge=0, le=1
    )
    base_generation_min: float = Field(default=2.0, alias="BASE_GENERATION_MIN", ge=0)
    base_generation_max: float = Field(default=7.0, alias="BASE_GENERATION_MAX", ge=0)
    pv_model_enabled: bool = Field(default=True, alias="PV_MODEL_ENABLED")
    pv_surface_tilt_deg: float = Field(default=15.0, alias="PV_SURFACE_TILT_DEG")
    pv_surface_azimuth_deg: float = Field(default=180.0, alias="PV_SURFACE_AZIMUTH_DEG")
    pv_temperature_coefficient: float = Field(
        default=-0.003, alias="PV_TEMPERATURE_COEFFICIENT"
    )
    pv_dc_ac_ratio: float = Field(default=1.10, alias="PV_DC_AC_RATIO", gt=0)
    pv_on_every_bus: bool = Field(default=True, alias="PV_ON_EVERY_BUS")
    bus_pv_capacity_min_kw: float = Field(
        default=10.0, alias="BUS_PV_CAPACITY_MIN_KW", ge=0
    )
    bus_pv_capacity_max_kw: float = Field(
        default=10.0, alias="BUS_PV_CAPACITY_MAX_KW", ge=0
    )

    # IEEE 1547 / AS4777 volt-watt response: a PV inverter throttles real-power
    # export as local bus voltage rises, protecting the LV feeder from
    # overvoltage backfeed. Full export at/below v_start, ramps linearly to zero
    # export at v_end. The power flow iterates to a fixed point since curtailment
    # lowers the voltage that drives it.
    pv_voltwatt_enabled: bool = Field(default=True, alias="PV_VOLTWATT_ENABLED")
    pv_voltwatt_v_start: float = Field(
        default=1.06, alias="PV_VOLTWATT_V_START", gt=1.0
    )
    pv_voltwatt_v_end: float = Field(default=1.10, alias="PV_VOLTWATT_V_END", gt=1.0)
    pv_voltwatt_max_iter: int = Field(default=5, alias="PV_VOLTWATT_MAX_ITER", gt=0)

    # IEEE 1547 volt-VAR (Q(V)) response: a PV inverter injects reactive power to
    # raise a sagging bus and absorbs it to pull down an overvoltage bus, before
    # any real-power curtailment. Piecewise Q(V) curve over four per-unit voltage
    # breakpoints with a deadband between v2 and v3: full injection (-Q) at/below
    # v1, ramping to 0 at v2; 0 in the deadband v2..v3; ramping to full absorption
    # (+Q) at v4 and beyond. Q is bounded by the inverter's available headroom
    # sqrt(sn^2 - p^2) and by q_max_frac of the apparent rating. The power flow
    # iterates to a fixed point (reactive support moves the voltage that drives it).
    pv_voltvar_enabled: bool = Field(default=True, alias="PV_VOLTVAR_ENABLED")
    pv_voltvar_v1: float = Field(default=0.92, alias="PV_VOLTVAR_V1", gt=0)
    pv_voltvar_v2: float = Field(default=0.98, alias="PV_VOLTVAR_V2", gt=0)
    pv_voltvar_v3: float = Field(default=1.02, alias="PV_VOLTVAR_V3", gt=0)
    pv_voltvar_v4: float = Field(default=1.08, alias="PV_VOLTVAR_V4", gt=0)
    # Max reactive power as a fraction of inverter apparent rating (IEEE 1547
    # Category B = 0.44). Inverter kVA = PV nameplate kW x oversize.
    pv_voltvar_q_max_frac: float = Field(
        default=0.44, alias="PV_VOLTVAR_Q_MAX_FRAC", ge=0, le=1
    )
    pv_voltvar_inverter_oversize: float = Field(
        default=1.1, alias="PV_VOLTVAR_INVERTER_OVERSIZE", gt=0
    )
    pv_voltvar_max_iter: int = Field(default=5, alias="PV_VOLTVAR_MAX_ITER", gt=0)

    # Battery energy storage (BESS). When enabled, hybrid-prosumer meters get a
    # behind-the-meter battery that follows a self-consumption dispatch: charge
    # from PV surplus, discharge to cover the household deficit — flattening the
    # meter's net exchange with the grid. State of charge persists across ticks.
    # Round-trip efficiency is split evenly between charge and discharge legs.
    battery_enabled: bool = Field(default=True, alias="BATTERY_ENABLED")
    battery_capacity_kwh: float = Field(
        default=13.5, alias="BATTERY_CAPACITY_KWH", gt=0
    )
    battery_max_charge_kw: float = Field(
        default=5.0, alias="BATTERY_MAX_CHARGE_KW", gt=0
    )
    battery_max_discharge_kw: float = Field(
        default=5.0, alias="BATTERY_MAX_DISCHARGE_KW", gt=0
    )
    battery_round_trip_efficiency: float = Field(
        default=0.90, alias="BATTERY_ROUND_TRIP_EFFICIENCY", gt=0, le=1
    )
    battery_min_soc_frac: float = Field(
        default=0.10, alias="BATTERY_MIN_SOC_FRAC", ge=0, le=1
    )
    battery_initial_soc_frac: float = Field(
        default=0.50, alias="BATTERY_INITIAL_SOC_FRAC", ge=0, le=1
    )

    # Frequency-watt droop (primary response). The engine derives a system
    # frequency from the supply/demand imbalance each tick — surplus generation
    # pushes frequency above nominal, deficit below — and feeds it to the meters,
    # whose inverters throttle real-power export under over-frequency (the
    # `apply_droop_control` law). Frequency = nominal + full_swing * ratio, where
    # ratio = (gen - load) / max(gen, load) is bounded to [-1, 1], so the swing is
    # self-scaling and needs no absolute base. One-tick governor lag: this tick's
    # imbalance sets the frequency the next tick's generation reacts to. Disable to
    # pin frequency at nominal (droop inert).
    freq_droop_enabled: bool = Field(default=True, alias="FREQ_DROOP_ENABLED")
    freq_nominal_hz: float = Field(default=50.0, alias="FREQ_NOMINAL_HZ", gt=0)
    freq_full_swing_hz: float = Field(default=0.5, alias="FREQ_FULL_SWING_HZ", gt=0)

    base_consumption_min: float = Field(default=0.5, alias="BASE_CONSUMPTION_MIN", ge=0)
    base_consumption_max: float = Field(default=3.0, alias="BASE_CONSUMPTION_MAX", ge=0)
    noise_factor_min: float = Field(default=0.05, alias="NOISE_FACTOR_MIN", ge=0, le=1)
    noise_factor_max: float = Field(default=0.15, alias="NOISE_FACTOR_MAX", ge=0, le=1)
    zip_impedance_fraction: float = Field(
        default=0.20, alias="ZIP_IMPEDANCE_FRACTION", ge=0
    )
    zip_current_fraction: float = Field(
        default=0.30, alias="ZIP_CURRENT_FRACTION", ge=0
    )
    zip_power_fraction: float = Field(default=0.50, alias="ZIP_POWER_FRACTION", ge=0)

    line_length_unit: str = Field(default="ft", alias="LINE_LENGTH_UNIT")
    # Realistic LV distribution trunk: 240 mm^2 Al overhead/cable. r ~0.125 ohm/km,
    # x ~0.08 ohm/km, ampacity ~420 A. Sized so the 0.4 kV feeder can physically
    # carry its aggregate load (thin defaults caused power-flow non-convergence).
    line_resistance_ohm_per_km: float = Field(
        default=0.125, alias="LINE_RESISTANCE_OHM_PER_KM", gt=0
    )
    line_reactance_ohm_per_km: float = Field(
        default=0.08, alias="LINE_REACTANCE_OHM_PER_KM", ge=0
    )
    line_capacity_kw: float = Field(default=500.0, alias="LINE_CAPACITY_KW", gt=0)
    # Thermal current rating per line (kA), used as pandapower max_i_ka for
    # loading_percent. 0.42 kA ~ 420 A for a 240 mm^2 LV conductor.
    line_ampacity_ka: float = Field(default=0.42, alias="LINE_AMPACITY_KA", gt=0)

    # MV/LV distribution transformer feeding the substation bus. When enabled the
    # power flow models a real upstream transformer: an MV external-grid slack on
    # the HV side and a transformer (short-circuit + iron losses) stepping down to
    # the LV substation bus. The LV bus voltage then sags under load and rises on
    # PV backfeed across the transformer impedance, instead of being pinned to a
    # stiff 1.0 pu ideal source. Disable to revert to the ideal LV slack.
    transformer_enabled: bool = Field(default=True, alias="TRANSFORMER_ENABLED")
    transformer_mv_kv: float = Field(default=22.0, alias="TRANSFORMER_MV_KV", gt=0)
    transformer_sn_mva: float = Field(default=0.63, alias="TRANSFORMER_SN_MVA", gt=0)
    transformer_vk_percent: float = Field(
        default=4.0, alias="TRANSFORMER_VK_PERCENT", gt=0
    )
    transformer_vkr_percent: float = Field(
        default=1.2, alias="TRANSFORMER_VKR_PERCENT", ge=0
    )
    transformer_pfe_kw: float = Field(default=1.0, alias="TRANSFORMER_PFE_KW", ge=0)
    transformer_i0_percent: float = Field(
        default=0.3, alias="TRANSFORMER_I0_PERCENT", ge=0
    )

    # On-load tap changer (OLTC) on the distribution transformer. When enabled the
    # power flow steps the HV-side tap each tick to regulate the LV feeder-head
    # voltage toward v_target within a deadband, re-solving until in-band or the
    # tap hits its limit. Bulk regulation runs before volt-watt, so the tap absorbs
    # what it can and local PV curtailment only handles residual overvoltage.
    transformer_oltc_enabled: bool = Field(
        default=True, alias="TRANSFORMER_OLTC_ENABLED"
    )
    transformer_tap_step_percent: float = Field(
        default=1.25, alias="TRANSFORMER_TAP_STEP_PERCENT", gt=0
    )
    transformer_tap_max: int = Field(default=8, alias="TRANSFORMER_TAP_MAX", gt=0)
    transformer_oltc_v_target: float = Field(
        default=1.0, alias="TRANSFORMER_OLTC_V_TARGET", gt=0
    )
    transformer_oltc_deadband: float = Field(
        default=0.0125, alias="TRANSFORMER_OLTC_DEADBAND", gt=0
    )
    transformer_oltc_max_steps: int = Field(
        default=10, alias="TRANSFORMER_OLTC_MAX_STEPS", gt=0
    )

    solar_prosumer_ratio: float = Field(
        default=0.25, alias="SOLAR_PROSUMER_RATIO", ge=0, le=1
    )
    grid_consumer_ratio: float = Field(
        default=0.50, alias="GRID_CONSUMER_RATIO", ge=0, le=1
    )
    hybrid_prosumer_ratio: float = Field(
        default=0.15, alias="HYBRID_PROSUMER_RATIO", ge=0, le=1
    )

    weather_sunny_weight: float = Field(
        default=0.4, alias="WEATHER_SUNNY_WEIGHT", ge=0, le=1
    )
    weather_partly_cloudy_weight: float = Field(
        default=0.3, alias="WEATHER_PARTLY_CLOUDY_WEIGHT", ge=0, le=1
    )
    weather_cloudy_weight: float = Field(
        default=0.15, alias="WEATHER_CLOUDY_WEIGHT", ge=0, le=1
    )
    weather_overcast_weight: float = Field(
        default=0.1, alias="WEATHER_OVERCAST_WEIGHT", ge=0, le=1
    )
    weather_rainy_weight: float = Field(
        default=0.05, alias="WEATHER_RAINY_WEIGHT", ge=0, le=1
    )

    # Oracle Bridge DLMS/COSEM egress (parent gridtokenx-oracle-bridge IoT gateway).
    oracle_bridge_url: str = Field(
        default="http://localhost:4010", alias="ORACLE_BRIDGE_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # DLMS/COSEM (IEC 62056) REST egress to the Oracle Bridge ingest endpoint
    # (oracle_bridge_url above). Off by default; signs each reading per-meter and
    # registers pubkeys in Redis (redis_url) on start.
    oracle_dlms_enabled: bool = Field(default=False, alias="ORACLE_DLMS_ENABLED")
    # Emit the reading batch every N ticks (1 = every tick).
    oracle_dlms_emit_every: int = Field(default=1, alias="ORACLE_DLMS_EMIT_EVERY", gt=0)
    # Static meter->owner map seeded into the bridge's Redis registry so telemetry
    # resolves to a user_id (settlement). JSON object {meter_id: user_id}; without
    # an entry the bridge resolves to Uuid::nil and settlement is skipped. Empty by
    # default — set when not driving ownership via IAM onboarding.
    oracle_meter_owner_map: dict[str, str] = Field(
        default_factory=dict, alias="ORACLE_METER_OWNER_MAP"
    )
    # When enabled, the engine onboards each meter to the IAM service (register ->
    # login -> claim) at start and uses the resulting user_ids as the owner map
    # (merged over oracle_meter_owner_map). Non-fatal: failures fall back to the
    # static map. Requires the IAM gateway (APISIX) reachable at iam_gateway_url.
    oracle_iam_onboard_enabled: bool = Field(
        default=False, alias="ORACLE_IAM_ONBOARD_ENABLED"
    )
    iam_gateway_url: str = Field(
        default="http://localhost:4001", alias="IAM_GATEWAY_URL"
    )

    # PostGIS persistence (parent geo asset DB; migrations under database/migrations).
    # When enabled, each tick's readings are batch-inserted into grid.meter_readings
    # and the meter population is upserted into grid.meters on start, so the run's
    # telemetry is queryable for replay/history and geo lookups. Off by default; the
    # writer is non-blocking and drops a tick if the prior batch is still in flight.
    postgis_enabled: bool = Field(default=False, alias="POSTGIS_ENABLED")
    postgis_url: str = Field(
        default="postgresql://gridtokenx_user:gridtokenx_password@localhost:7001/gridtokenx",
        alias="POSTGIS_URL",
    )
    # Persist the reading batch every N ticks (1 = every tick).
    postgis_persist_every: int = Field(default=1, alias="POSTGIS_PERSIST_EVERY", gt=0)

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    metrics_port: int = Field(default=9091, alias="METRICS_PORT", gt=0)
    simulation_speed_multiplier: float = Field(
        default=1.0, alias="SIMULATION_SPEED_MULTIPLIER", gt=0
    )
    random_seed: int = Field(default=42, alias="RANDOM_SEED")
    weather_change_frequency: int = Field(
        default=5, alias="WEATHER_CHANGE_FREQUENCY", gt=0
    )
    base_latitude: float = Field(default=13.758252, alias="BASE_LATITUDE")
    base_longitude: float = Field(default=100.687455, alias="BASE_LONGITUDE")
    # IANA timezone for the grid location. The sim clock is naive wall-clock
    # local time-of-day; the PV model localizes to this zone so solar position
    # (and thus generation) tracks local noon, not UTC.
    timezone: str = Field(default="Asia/Bangkok", alias="TIMEZONE")
    min_load_kw: float = Field(default=0.1, alias="MIN_LOAD_KW", ge=0)
    max_load_kw: float = Field(default=500.0, alias="MAX_LOAD_KW", gt=0)

    @property
    def weather_weights(self) -> Dict[WeatherCondition, float]:
        return {
            WeatherCondition.SUNNY: self.weather_sunny_weight,
            WeatherCondition.PARTLY_CLOUDY: self.weather_partly_cloudy_weight,
            WeatherCondition.CLOUDY: self.weather_cloudy_weight,
            WeatherCondition.OVERCAST: self.weather_overcast_weight,
            WeatherCondition.RAINY: self.weather_rainy_weight,
        }

    @field_validator("*", mode="before")
    @classmethod
    def expand_env_vars(cls, value: Any) -> Any:
        if isinstance(value, str) and "${" in value:
            import re

            def replace_var(match: re.Match[str]) -> str:
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))

            return re.sub(r"\${([^}]+)}", replace_var, value)
        return value


_config_instance: SimulatorConfig | None = None


def get_config() -> SimulatorConfig:
    """Return the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = SimulatorConfig()
    return _config_instance


def __getattr__(name: str) -> Any:
    if name.isupper():
        field_name = name.lower()
        config = get_config()
        if hasattr(config, field_name):
            return getattr(config, field_name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
