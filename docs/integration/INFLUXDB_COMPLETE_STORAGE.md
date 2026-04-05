# InfluxDB Complete Storage

The **GridTokenX Smart Meter Simulator** utilizes InfluxDB as its primary time-series database to store all telemetry, grid events, and VPP metrics.

## 🗄️ Data Schema

The InfluxDB transport (`src/smart_meter_simulator/transport/influxdb.py`) organizes data into several distinct measurements:

### 1. `meter_reading`
Stores individual meter telemetry.
- **Tags**: `meter_id`, `meter_type`, `location`, `accuracy_class`
- **Fields**:
  - `energy_generated_kwh`, `energy_consumed_kwh`
  - `battery_level_kwh`, `battery_soc_pct`
  - `voltage_v`, `current_a`, `frequency_hz`
  - `active_power_kw`, `power_factor`, `temperature_c`

### 2. `grid_state_estimation`
Stores results from the Pandapower state estimator.
- **Tags**: `converged`, `algorithm`
- **Fields**: `chi_squared`, `mae`, `max_residual`, `total_loss_mw`, `avg_voltage_pu`, `health_score`

### 3. `vpp_cluster` & `vpp_dispatch`
Tracks Virtual Power Plant operations.
- **Fields**: `total_capacity_kw`, `total_dispatch_kw`, `utilization_pct`, `afrr_power_kw`, `compliance_pct`

### 4. `grid_frequency`
Records real-time frequency dynamics.
- **Fields**: `frequency_hz`, `deviation_hz`, `roc_hz_per_sec`, `imbalance_kw`

### 5. `carbon_intensity`
Tracks the environmental impact of the grid.
- **Fields**: `intensity_gco2_kwh`, `renewable_pct`, `carbon_offset_kg`

## 🚀 Retention Policies

By default, the simulator assumes an InfluxDB retention policy of **30 days** for high-resolution data and **1 year** for downsampled aggregates.

## 📊 Dashboard Integration

The stored data is optimized for **Grafana**. Pre-configured dashboards are designed to query these measurements to provide real-time grid observability.

---
_Next: [Real-Time Database Queries](INFLUXDB_REALTIME_DATABASE.md)_
