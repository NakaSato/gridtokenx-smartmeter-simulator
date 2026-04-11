---
title: "InfluxDB Schema"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/integration/INFLUXDB_COMPLETE_STORAGE.md", "docs/integration/INFLUXDB_REALTIME_DATABASE.md", "src/smart_meter_simulator/transport/influxdb.py"]
tags: [database, timeseries, influxdb, storage]
related: [[Transport Layer]], [[InfluxDB Integration]], [[EnergyReading Model]]
---

# InfluxDB Schema

All simulation data — meter readings, grid state estimates, VPP dispatches, frequency metrics, and carbon intensity — is stored in InfluxDB as time-series measurements with appropriate tags and fields.

## Summary

The InfluxDB transport writes five measurement types to the `meter_readings` bucket, each with a consistent tag schema for filtering and aggregation. Retention policies range from 30 days (high-frequency) to 1 year (aggregated).

## Measurement Types

### 1. meter_reading

Individual smart meter readings at each simulation tick.

**Measurement:** `meter_reading`

| Tag | Description |
|-----|-------------|
| `meter_id` | Smart meter identifier |
| `meter_type` | Solar_Prosumer, Grid_Consumer, etc. |
| `feeder_id` | Electrical feeder assignment |

| Field | Type | Description |
|-------|------|-------------|
| `energy_generated_kwh` | float | Generation in interval |
| `energy_consumed_kwh` | float | Consumption in interval |
| `surplus_energy` | float | Net export |
| `deficit_energy` | float | Net import |
| `battery_level_kwh` | float | Battery state |
| `voltage_v` | float | Line voltage |
| `current_a` | float | Line current |
| `frequency_hz` | float | Grid frequency |
| `power_factor` | float | Power factor |
| `reactive_power` | float | Reactive power |

### 2. grid_state_estimation

Results from WLS state estimation.

**Measurement:** `grid_state_estimation`

| Tag | Description |
|-----|-------------|
| `estimation_id` | Estimation run identifier |
| `algorithm` | WLS or Iwamoto |

| Field | Type | Description |
|-------|------|-------------|
| `chi_squared_statistic` | float | J(x̂) value |
| `chi_squared_critical` | float | χ² threshold |
| `max_normalized_residual` | float | Largest r_N |
| `bad_data_detected` | bool | Chi-squared test result |
| `iterations` | int | WLS iterations |
| `converged` | bool | Estimation converged |

### 3. vpp_cluster

VPP cluster aggregation and dispatch results.

**Measurement:** `vpp_cluster`

| Tag | Description |
|-----|-------------|
| `cluster_id` | VPP cluster identifier |
| `feeder_id` | Feeder assignment |

| Field | Type | Description |
|-------|------|-------------|
| `total_capacity_kw` | float | Aggregate capacity |
| `total_soc_percent` | float | Average SoC |
| `target_kw` | float | Dispatch target |
| `carbon_saved_g` | float | CO₂ savings |
| `cluster_health` | float | 0-100 health score |
| `dispatch_count` | int | Number of dispatched meters |

### 4. grid_frequency

Grid frequency tracking over time.

**Measurement:** `grid_frequency`

| Field | Type | Description |
|-------|------|-------------|
| `frequency_hz` | float | Measured frequency |
| `deviation_hz` | float | Deviation from 50 Hz |
| `afrr_active` | bool | aFRR activated |
| `afrr_target_kw` | float | aFRR power target |

### 5. carbon_intensity

Grid carbon intensity tracking.

| Tag | Description |
|-----|-------------|
| `region` | Geographic region |

| Field | Type | Description |
|-------|------|-------------|
| `intensity_gco2_kwh` | float | gCO₂ per kWh |
| `carbon_saved_g` | float | Cumulative savings |

## Retention Policies

| Measurement | Retention | Reason |
|-------------|-----------|--------|
| `meter_reading` | 30 days | High frequency, large volume |
| `grid_state_estimation` | 1 year | Lower frequency, diagnostic value |
| `vpp_cluster` | 1 year | Dispatch history, revenue tracking |
| `grid_frequency` | 30 days | High frequency |
| `carbon_intensity` | 1 year | Slow-changing reference |

## Query Examples (Flux)

```flux
// Latest reading for a specific meter
from(bucket: "meter_readings")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "meter_reading")
  |> filter(fn: (r) => r.meter_id == "AMI_METER_001")
  |> last()

// Average voltage across all meters
from(bucket: "meter_readings")
  |> range(start: -1h)
  |> filter(fn: (r) => r._field == "voltage_v")
  |> mean()

// VPP cluster health over time
from(bucket: "meter_readings")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "vpp_cluster")
  |> filter(fn: (r) => r._field == "cluster_health")
```

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `INFLUXDB_URL` | http://localhost:8086 | InfluxDB endpoint |
| `INFLUXDB_TOKEN` | admin_token | Auth token |
| `INFLUXDB_ORG` | gridtokenx | Organization |
| `INFLUXDB_BUCKET` | meter_readings | Bucket name |

## Relationships

- **Transport:** [[InfluxDB Integration]], [[Transport Layer]]
- **Data model:** [[EnergyReading Model]]
- **Query service:** `transport/influxdb_query.py`
- **Visualization:** Grafana dashboards (Phase 28)

## Known Issues

- No downsampling tasks configured for long-term retention
- High write throughput at 1000+ meters may need batching optimization
- No continuous queries for derived metrics (e.g., hourly averages)
- Token-based auth only — no mTLS for InfluxDB connection
