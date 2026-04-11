---
title: "Simulation Engine"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/engine.py", "docs/architecture/simulation-engine.md"]
tags: [core, engine, simulation]
related: [[Smart Meter]], [[Rust Acceleration]], [[VPP Orchestrator]], [[Transport Layer]]
---

# Simulation Engine

The `SimulationEngine` is the central orchestrator for the entire Smart Meter Simulator. It manages the meter lifecycle, coordinates grid state estimation, dispatches VPP commands, runs market matching, and broadcasts readings through transport layers.

## Summary

The engine runs a continuous tick cycle that generates meter readings, applies VPP dispatch corrections, performs grid state estimation, and delivers results through configured transports. It supports both server mode (FastAPI REST + WebSocket) and standalone mode (direct API Gateway submission).

## Tick Cycle

Each tick (~15 seconds by default) executes in sequence:

1. **Reading Generation** — Each `SmartMeter` generates a signed energy reading (Rust-accelerated batch)
2. **VPP Dispatch** — Apply droop control + aFRR corrections to DER-capable meters
3. **Grid Analysis** — Pandapower adapter updates measurements, runs state estimation
4. **Market Clearing** — P2P double auction matches surplus with deficit
5. **Transport Dispatch** — Broadcast readings through HTTP/gRPC/MQTT/Kafka/InfluxDB
6. **State Persistence** — Write to PostgreSQL + InfluxDB + Redis cache

```
┌─────────────────────────────────────────────────┐
│                  Tick Cycle                      │
├─────────────────────────────────────────────────┤
│  Meter Reading (Rust)  →  VPP Dispatch (aFRR)  │
│         ↓                        ↓               │
│  Grid State Est. (WLS)  →  Market Clearing     │
│         ↓                        ↓               │
│  Transport Dispatch   →  State Persistence      │
└─────────────────────────────────────────────────┘
```

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `simulation_interval` | 15s | Time between ticks |
| `num_meters` | 55 | Number of simulated meters |
| `rust_accelerated` | true | Use PyO3 engine for reading generation |
| `enable_grid_integration` | true | Run pandapower state estimation |
| `enable_market_dynamics` | true | Run P2P market clearing |
| `enable_vpp` | true | Dispatch VPP cluster commands |
| `enable_frequency_control` | true | Apply droop control corrections |
| `fast_ingestion_mode` | false | Bypass physics/analytics for stress testing |

## Rust Acceleration Bridge

The engine automatically detects and uses the Rust PyO3 module (`gridtokenx_sim`) for reading generation:

| Meters | Python | Rust | Speedup |
|--------|--------|------|---------|
| 100 | ~300 ms | 0.02 ms | 15,000x |
| 500 | ~1,500 ms | 0.11 ms | 13,636x |
| 1,000 | ~3,000 ms | 0.28 ms | 10,714x |

See [[Rust Acceleration]] for build and performance details.

## Relationships

- **Manages:** [[Smart Meter]] instances (lifecycle, reading generation)
- **Delegates to:** [[VPP Orchestrator]] for dispatch commands
- **Delegates to:** [[State Estimator]] for grid analysis
- **Delegates to:** [[Market Engine]] for P2P clearing
- **Outputs via:** [[Transport Layer]] (HTTP, gRPC, MQTT, Kafka, InfluxDB, WebSocket)
- **Persists to:** [[PostGIS Integration]], [[InfluxDB Integration]]

## Known Issues

- State estimation may diverge if grid topology has unrealistic R/X ratios (switch to Iwamoto algorithm)
- Database initialization is best-effort — simulator continues without persistence if unavailable
- Fast ingestion mode bypasses all analytics — use only for throughput testing
