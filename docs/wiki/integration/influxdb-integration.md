---
title: "InfluxDB Integration"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/integration/INFLUXDB_REALTIME_DATABASE.md", "src/smart_meter_simulator/transport/influxdb.py", "src/smart_meter_simulator/transport/influxdb_query.py"]
tags: [database, timeseries, influxdb, query]
related: [[InfluxDB Schema]], [[Transport Layer]], [[Rust Acceleration]]
---

# InfluxDB Integration

InfluxDB serves as the time-series database for all simulation data, providing high-throughput writes, real-time querying, and dashboard data services.

## Summary

The InfluxDB integration consists of a write transport (`InfluxDBTransport`) that streams measurement data to the `meter_readings` bucket, and a query service (`InfluxDBQueryService`) that provides real-time data retrieval for dashboards and analytics.

## Architecture

```
┌────────────────────┐     ┌──────────────────┐
│  Simulation Engine  │     │ Query Service    │
│  InfluxDBTransport │     │ InfluxDBQuery    │
└────────┬───────────┘     └────────┬─────────┘
         │ Writes                   │ Queries
         ↓                          ↓
    ┌────────────────────────────────────┐
    │       InfluxDB 2.7                 │
    │  Bucket: meter_readings            │
    │  Org: gridtokenx                   │
    │  Retention: 52 weeks               │
    └────────────────────────────────────┘
```

## Write Transport

```python
from smart_meter_simulator.transport.influxdb import InfluxDBTransport

transport = InfluxDBTransport(
    url="http://localhost:8086",
    token="admin_token",
    org="gridtokenx",
    bucket="meter_readings"
)

# Write single point
await transport.send_reading(reading, tags={"meter_type": "Solar_Prosumer"})

# Write batch
await transport.send_batch(readings, measurement="meter_reading")
```

### Write Modes

| Mode | Description |
|------|-------------|
| Synchronous | Write immediately |
| Batch | Buffer N points, flush on interval |
| Async | Write in background task |

## Query Service

```python
from smart_meter_simulator.transport.influxdb_query import InfluxDBQueryService

query = InfluxDBQueryService(
    url="http://localhost:8086",
    token="admin_token",
    org="gridtokenx",
    bucket="meter_readings"
)

# Latest reading for a meter
latest = await query.get_latest_readings(meter_id="AMI_METER_001")

# Historical data
history = await query.get_meter_history(
    meter_id="AMI_METER_001",
    start="-24h",
    field="voltage_v"
)

# Grid metrics summary
metrics = await query.get_grid_metrics()

# Energy summary
summary = await query.get_energy_summary(start="-1h", group_by="meter_type")

# Alerts (threshold breaches)
alerts = await query.get_alerts(
    field="frequency_hz",
    lower=49.9,
    upper=50.1,
    start="-1h"
)
```

## Flux Query Examples

### Latest Reading
```flux
from(bucket: "meter_readings")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "meter_reading")
  |> filter(fn: (r) => r.meter_id == "AMI_METER_001")
  |> last()
```

### Voltage Trend
```flux
from(bucket: "meter_readings")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "meter_reading")
  |> filter(fn: (r) => r._field == "voltage_v")
  |> aggregateWindow(every: 5m, fn: mean)
```

### Cluster Health
```flux
from(bucket: "meter_readings")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "vpp_cluster")
  |> filter(fn: (r) => r._field == "cluster_health")
  |> group(columns: ["cluster_id"])
```

## Data Types Stored

| Measurement | Fields | Tags | Retention |
|-------------|--------|------|-----------|
| `meter_reading` | 10 energy/electrical fields | meter_id, meter_type, feeder_id | 30 days |
| `grid_state_estimation` | 6 estimation fields | estimation_id, algorithm | 1 year |
| `vpp_cluster` | 6 dispatch fields | cluster_id, feeder_id | 1 year |
| `grid_frequency` | 4 frequency fields | — | 30 days |
| `carbon_intensity` | 2 carbon fields | region | 1 year |

See [[InfluxDB Schema]] for complete field/tag definitions.

## Docker Configuration

```yaml
influxdb:
  image: influxdb:2.7
  ports:
    - "8086:8086"
  environment:
    DOCKER_INFLUXDB_INIT_MODE: setup
    DOCKER_INFLUXDB_INIT_USERNAME: admin
    DOCKER_INFLUXDB_INIT_PASSWORD: admin_password
    DOCKER_INFLUXDB_INIT_ORG: gridtokenx
    DOCKER_INFLUXDB_INIT_BUCKET: meter_readings
    DOCKER_INFLUXDB_INIT_RETENTION: 52w
    DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: admin_token
```

## Performance

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Single write | ~5 ms | ~200 points/s |
| Batch write (100) | ~20 ms | ~5,000 points/s |
| Latest query | ~10 ms | — |
| Historical query (1h) | ~50 ms | — |

## Grafana Integration

InfluxDB is the data source for Grafana dashboards (Phase 28):
- Grid overview dashboard
- VPP performance dashboard
- ADR dashboard
- Individual meter detail

## Relationships

- **Schema:** [[InfluxDB Schema]]
- **Transport:** [[Transport Layer]]
- **Visualization:** Grafana dashboards
- **Query service:** `transport/influxdb_query.py`

## Known Issues

- No continuous queries for derived metrics
- No downsampling for long-term retention
- Query service returns raw data — no aggregation
- No authentication beyond admin token (no user-level ACL)
- At 1000+ meters, individual writes become a bottleneck — batching needed
