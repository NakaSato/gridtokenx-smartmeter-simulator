# InfluxDB Real-Time Database Queries

The **InfluxDB Query Service** (`src/smart_meter_simulator/transport/influxdb_query.py`) provides an optimized interface for retrieving time-series data using the **Flux** query language.

## 📡 Query Capabilities

The service is designed for high-performance retrieval and provides the following real-time query methods:

1.  **`get_latest_readings`**: Retrieves the most recent measurement for a set of meters, providing a real-time snapshot of the grid.
2.  **`get_meter_history`**: Aggregates historical meter data (mean, max, sum) over periods such as 1h, 24h, or 7d.
3.  **`get_grid_metrics`**: Returns systemic metrics like total health score and chi-squared convergence of the state estimator.
4.  **`get_energy_summary`**: Provides cumulative generation and consumption totals for a specified duration.
5.  **`get_alerts`**: Retrieves recent system anomalies, filtered by severity (info, warning, critical).

## 📊 Flux Query Examples

The service encapsulates complex Flux logic. For example, to retrieve historical readings for a specific meter with a 5-minute aggregation window:

```flux
from(bucket: "meter_readings")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "meter_reading" and r.meter_id == "MTR_001")
    |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> sort(columns: ["_time"], desc: false)
```

## 🏗️ Real-Time Dashboard Data

The `get_real_time_dashboard` method provides a comprehensive aggregate of grid health, including:
- Total active meter count
- Aggregate generation vs. consumption
- Net balance across the simulated zone

---
_Maintained by the GridTokenX Telemetry Team._
