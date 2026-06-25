"""Configuration for the GLM grid model simulator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

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
    # Fraction of buses that carry rooftop PV when pv_on_every_bus is set. <1.0
    # gives a realistic partial penetration (0.25 of 80 buses = 20 PV nodes);
    # 1.0 keeps the legacy "PV on every bus" behaviour. GLM-authored PV buses are
    # always selected first, then the remainder is spread evenly across the feeder.
    pv_bus_penetration: float = Field(
        default=0.25, alias="PV_BUS_PENETRATION", ge=0.0, le=1.0
    )
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

    # Aggregator Bridge DLMS/COSEM egress (parent gridtokenx-aggregator-bridge IoT gateway).
    # Host-networked dev defaults: gateway on :4030 (docker-compose maps
    # IOT_GATEWAY_PORT -> container :4010; host :4010 is the IAM service, not the
    # bridge), Redis published on :7010. In the docker network override with
    # AGGREGATOR_BRIDGE_URL=http://aggregator-bridge:4010 and REDIS_URL=redis://redis:6379.
    aggregator_bridge_url: str = Field(
        default="http://localhost:4030", alias="AGGREGATOR_BRIDGE_URL"
    )
    # CA bundle path trusted when the bridge URL is https (dev self-signed cert
    # whose SAN covers `aggregator-bridge`). Empty -> httpx uses the system CA
    # store. Ignored for plain-http bridge URLs.
    aggregator_tls_ca: str = Field(default="", alias="AGGREGATOR_TLS_CA")
    # AES-256-GCM per-meter payload encryption (DLMS security-suite aligned). When
    # on, the emitter seeds each meter's AES key into the bridge's enckey registry
    # and sends `dlms-enc` envelopes (confidentiality + replay protection) instead
    # of plaintext OBIS. Default off (plaintext `dlms`, backward-compatible).
    aggregator_encrypt_enabled: bool = Field(
        default=False, alias="AGGREGATOR_ENCRYPT_ENABLED"
    )
    # Per-meter key rotation with Vault-Transit KEK wrapping (DLMS Security-Setup
    # model). When on (and encryption enabled), each meter gets a random GUEK
    # wrapped by the Vault Transit KEK; only the wrapped blob is seeded to Redis
    # (raw key never at rest), frames carry a key version `kid`, and the key can be
    # rotated at runtime. Off -> Phase-2 derived static key (no kid). Needs Vault.
    aggregator_key_rotation_enabled: bool = Field(
        default=False, alias="AGGREGATOR_KEY_ROTATION_ENABLED"
    )
    vault_addr: str = Field(default="http://localhost:13001", alias="VAULT_ADDR")
    vault_token: str = Field(default="root", alias="VAULT_TOKEN")
    vault_meter_kek_name: str = Field(
        default="gridtokenx-meter-kek", alias="VAULT_METER_KEK_NAME"
    )
    redis_url: str = Field(default="redis://localhost:7010", alias="REDIS_URL")

    # API key sent as the X-API-KEY header on every ingest POST. The bridge's
    # api_key_auth middleware rejects unauthenticated requests (401 "Missing API
    # Key"); the key must match one in the bridge's GRIDTOKENX_API_KEYS (or be
    # accepted by IAM). Empty by default — set in docker-compose / .env.
    aggregator_api_key: str = Field(default="", alias="AGGREGATOR_API_KEY")

    # DLMS/COSEM (IEC 62056) REST egress to the Aggregator Bridge ingest endpoint
    # (aggregator_bridge_url above). Off by default; signs each reading per-meter and
    # registers pubkeys in Redis (redis_url) on start.
    aggregator_dlms_enabled: bool = Field(
        default=False, alias="AGGREGATOR_DLMS_ENABLED"
    )
    # Emit the reading batch every N ticks (1 = every tick).
    aggregator_dlms_emit_every: int = Field(
        default=1, alias="AGGREGATOR_DLMS_EMIT_EVERY", gt=0
    )
    # Static meter->owner map seeded into the bridge's Redis registry so telemetry
    # resolves to a user_id (settlement). JSON object {meter_id: user_id}; without
    # an entry the bridge resolves to Uuid::nil and settlement is skipped. Empty by
    # default — set when not driving ownership via IAM onboarding.
    aggregator_meter_owner_map: dict[str, str] = Field(
        default_factory=dict, alias="AGGREGATOR_METER_OWNER_MAP"
    )
    # When enabled, the engine onboards each meter to the IAM service (register ->
    # login -> claim) at start and uses the resulting user_ids as the owner map
    # (merged over aggregator_meter_owner_map). Non-fatal: failures fall back to the
    # static map. Requires the IAM gateway (APISIX) reachable at iam_gateway_url.
    aggregator_iam_onboard_enabled: bool = Field(
        default=False, alias="AGGREGATOR_IAM_ONBOARD_ENABLED"
    )
    iam_gateway_url: str = Field(
        default="http://localhost:4001", alias="IAM_GATEWAY_URL"
    )
    # Persistent {meter_id: user_id} owner cache. Meters present here skip IAM
    # onboarding on boot (the bridge already resolves them from their durable
    # Postgres `meters` row), so coverage accumulates across boots under IAM's
    # tight register/login rate limits instead of being redone every run. Lives
    # under the mounted data/ volume so it survives container recreation.
    iam_onboard_cache_path: str = Field(
        default="data/iam_owner_map.json", alias="IAM_ONBOARD_CACHE_PATH"
    )

    # Time-of-use (TOU) tariff classification for the residential OBIS register
    # set. When enabled, the DLMS egress splits each interval's import/export
    # energy into rate-1 (peak) / rate-2 (off-peak) OBIS registers and emits the
    # active-tariff indicator (0.0.96.14.0.255). 2-tier weekday peak window
    # [start, end) in the reading's local clock hour; weekends are all off-peak
    # (Thai MEA/PEA residential TOU: peak 09:00-22:00 weekdays). Energy totals
    # (1.1.1.8.0.255 / 1.1.2.8.0.255) are unaffected — rate registers are
    # additional metadata, not a re-split of the settlement energy.
    aggregator_tou_enabled: bool = Field(default=True, alias="AGGREGATOR_TOU_ENABLED")
    aggregator_tou_peak_start_hour: int = Field(
        default=9, alias="AGGREGATOR_TOU_PEAK_START_HOUR", ge=0, le=23
    )
    aggregator_tou_peak_end_hour: int = Field(
        default=22, alias="AGGREGATOR_TOU_PEAK_END_HOUR", ge=1, le=24
    )

    # Operational-telemetry egress — operator/SCADA-facing grid + microgrid state
    # that DLMS/OBIS has no codes for (per-zone frequency, island/breaker status,
    # fault counters, DER curtailment, transformer loading/tap, tie-switch state).
    # Consumes the tick summary and POSTs a DNP3/IEC-104-shaped point list to a
    # collector (operational_outstation_url). Off by default; non-blocking, drops a
    # tick if the prior batch is in flight. Distinct from DLMS metering egress.
    operational_telemetry_enabled: bool = Field(
        default=False, alias="OPERATIONAL_TELEMETRY_ENABLED"
    )
    operational_outstation_url: str = Field(
        default="http://localhost:4040", alias="OPERATIONAL_OUTSTATION_URL"
    )
    # Emit the point batch every N ticks (1 = every tick).
    operational_emit_every: int = Field(default=1, alias="OPERATIONAL_EMIT_EVERY", gt=0)
    # Wire protocol: "json" (default collector POST to operational_outstation_url)
    # or "iec104" (real IEC 60870-5-104 outstation; needs the `iec104` extra:
    # uv sync --extra iec104). Same point map either way.
    operational_transport: str = Field(default="json", alias="OPERATIONAL_TRANSPORT")
    # IEC-104 outstation listen port + station common address (transport=iec104).
    operational_iec104_port: int = Field(
        default=2404, alias="OPERATIONAL_IEC104_PORT", gt=0, le=65535
    )
    operational_iec104_common_address: int = Field(
        default=1, alias="OPERATIONAL_IEC104_COMMON_ADDRESS", gt=0
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

    # InfluxDB 2.x time-series persistence (standalone sim bucket; independent of
    # PostGIS). Each tick writes, in one batch tagged with the run_id (seed+clock
    # identity): per-meter readings, a grid_state point (losses/transformer/freq/
    # faults), and per-meter carbon + bill points — so a run is fully queryable as
    # one series for plotting. On by default; the writer is non-blocking, drops a
    # tick if the prior batch is still in flight, and self-disables for the run if
    # the broker is unreachable on start (so default-on is safe with no Influx up).
    influx_enabled: bool = Field(default=True, alias="INFLUX_ENABLED")
    influx_url: str = Field(default="http://localhost:8086", alias="INFLUX_URL")
    influx_token: str = Field(default="", alias="INFLUX_TOKEN")
    influx_org: str = Field(default="gridtokenx", alias="INFLUX_ORG")
    influx_bucket: str = Field(default="smartmeter_sim", alias="INFLUX_BUCKET")
    influx_measurement: str = Field(default="meter_reading", alias="INFLUX_MEASUREMENT")
    influx_grid_measurement: str = Field(
        default="grid_state", alias="INFLUX_GRID_MEASUREMENT"
    )
    influx_carbon_measurement: str = Field(
        default="meter_carbon", alias="INFLUX_CARBON_MEASUREMENT"
    )
    influx_bill_measurement: str = Field(
        default="meter_bill", alias="INFLUX_BILL_MEASUREMENT"
    )
    influx_persist_every: int = Field(default=1, alias="INFLUX_PERSIST_EVERY", gt=0)
    influx_persist_grid_state: bool = Field(
        default=True, alias="INFLUX_PERSIST_GRID_STATE"
    )
    influx_persist_carbon: bool = Field(default=True, alias="INFLUX_PERSIST_CARBON")
    influx_persist_bill: bool = Field(default=True, alias="INFLUX_PERSIST_BILL")

    # Thai retail electricity tariff (MEA/PEA). The structured energy-charge rate
    # tables live in pricing/thai_tariff.py; only the two volatile, period-revised
    # components are config-driven here. Ft (fuel adjustment) is a flat ฿/kWh
    # surcharge on all energy, revised by the ERC ~quarterly — default is the
    # Jan–Apr 2025 retail value (0.3672 ฿/kWh = 36.72 satang). VAT is 7%.
    tariff_ft_per_kwh: float = Field(default=0.3672, alias="TARIFF_FT_PER_KWH")
    tariff_vat_rate: float = Field(default=0.07, alias="TARIFF_VAT_RATE", ge=0, le=1)
    # Net-billing solar export buy-back rate (฿/kWh). Thailand buys exported
    # rooftop-PV surplus separately at a flat rate (NOT net metering — not netted
    # against import units before the tariff). 2.20 is the residential rooftop
    # scheme rate (≤10 kW). The 90 MW quota was met in 2024, so set 0.0 to model a
    # new entrant who gets no buy-back.
    tariff_export_per_kwh: float = Field(
        default=2.20, alias="TARIFF_EXPORT_PER_KWH", ge=0
    )

    # Carbon / avoided-emissions accounting (emissions/carbon.py). All kg CO2e
    # per kWh. grid_intensity default is the Thailand grid-average factor (TGO);
    # solar_intensity is the IPCC AR5 median life-cycle intensity for rooftop PV;
    # kg_per_tree_year is the US EPA per-tree annual sequestration used only for
    # the tangible "trees-equivalent" display.
    carbon_grid_intensity_kgco2_per_kwh: float = Field(
        default=0.4999, alias="CARBON_GRID_INTENSITY_KGCO2_PER_KWH", ge=0
    )
    carbon_solar_intensity_kgco2_per_kwh: float = Field(
        default=0.041, alias="CARBON_SOLAR_INTENSITY_KGCO2_PER_KWH", ge=0
    )
    carbon_kg_per_tree_year: float = Field(
        default=21.77, alias="CARBON_KG_PER_TREE_YEAR", gt=0
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    metrics_port: int = Field(default=9091, alias="METRICS_PORT", gt=0)
    simulation_speed_multiplier: float = Field(
        default=1.0, alias="SIMULATION_SPEED_MULTIPLIER", gt=0
    )
    random_seed: int = Field(default=42, alias="RANDOM_SEED")
    simulation_start_time: Optional[str] = Field(
        default=None,
        alias="SIMULATION_START_TIME",
        description=(
            "ISO-8601 sim clock start (e.g. 2026-06-10T08:00:00+00:00). When set, "
            "the simulation starts at this instant instead of the current wall "
            "clock — pin it together with RANDOM_SEED for byte-identical replay. "
            "Unset = start at today 08:00 UTC."
        ),
    )
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
