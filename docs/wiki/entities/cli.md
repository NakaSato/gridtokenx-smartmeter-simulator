---
title: "CLI"
category: entities
created: 2026-04-19
updated: 2026-04-19
sources: ["src/smart_meter_simulator/cli.py"]
tags: [cli, config, mode]
related: [[FastAPI App]], [[Simulation Engine]]
---

# CLI

The command-line interface provides the primary entry point for starting the simulator in different modes and configuring its parameters without modifying environment variables directly.

## Summary

The CLI supports two main modes: `server` (starts the FastAPI application) and `standalone` (runs the simulation engine directly without a web server). It provides arguments for overriding simulation intervals, pricing rates, energy bounds, and meter type distributions.

## Details

### Run Modes
- **Server Mode:** Launches the FastAPI application using Uvicorn. This is the default mode and enables web-based monitoring and API access.
- **Standalone Mode:** Runs a simplified simulation loop that submits readings directly to an API gateway via HTTP, bypassing the local FastAPI server and its analytics/grid layers.

### Parameter Overrides
The CLI maps command-line arguments to environment variables, which are then consumed by the `SimulatorConfig`:
- **Simulation:** `--meters`, `--interval`, `--port`.
- **Pricing:** `--purchase-rate`, `--feed-in-rate`.
- **Energy:** `--base-gen-min/max`, `--base-cons-min/max`.
- **Distribution:** Ratios for solar, consumer, hybrid, battery, EV, and DC chargers.

## Key Parameters

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--mode` | string | server | `server` or `standalone` |
| `--meters` | int | 20 | Number of meters to generate |
| `--api-url` | string | http://localhost:3000 | Gateway URL for standalone mode |
| `--port` | int | 8082 | Port for server mode |
| `--interval`| int | - | Simulation tick interval (seconds) |

## Relationships

- **Starts:** [[FastAPI App]] (server mode)
- **Starts:** [[Simulation Engine]] (standalone mode)
- **Configures:** [[Meter Type Distribution]]

## Known Issues

- Standing mode only supports `HttpTransport`; it does not initialize gRPC or MQTT transports.
- Standalone mode does not include the Pandapower grid engine or state estimation.
