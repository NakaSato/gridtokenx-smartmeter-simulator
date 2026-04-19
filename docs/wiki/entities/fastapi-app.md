---
title: "FastAPI App"
category: entities
created: 2026-04-19
updated: 2026-04-19
sources: ["src/smart_meter_simulator/app.py"]
tags: [api, fastapi, web, otel]
related: [[Simulation Engine]], [[WebSocket Protocol]], [[Transport Layer]], [[OpenTelemetry]]
---

# FastAPI App

The `FastAPI` application serves as the primary interface for the Smart Meter Simulator, providing REST API endpoints, real-time WebSocket streams, and static asset serving for the dashboard.

## Summary

The app orchestrates the simulation lifecycle using FastAPI's lifespan events. It initializes the database, configures the telemetry transport pipeline (Composite Transport), generates meters, and starts the simulation engine in an asynchronous task. It also integrates OpenTelemetry for tracing and metrics.

## Details

### Lifecycle Management
The application uses an `asynccontextmanager` for its lifespan:
- **Startup:** Initializes `DatabaseManager`, sets up `CompositeTransport` (including gRPC, MQTT, HTTP, Kafka, and InfluxDB based on configuration), generates meters using `MeterGenerator`, registers them with the API gateway, and starts the `SimulationEngine`.
- **Shutdown:** Stops the simulation engine and cancels the background simulation task.

### Telemetry Pipeline
The app supports multiple ingestion protocols:
- **Primary:** gRPC (DLMS/COSEM), MQTT, or legacy REST.
- **Secondary:** Kafka, InfluxDB, and WebSocket streams.

### OpenTelemetry Integration
The app implements distributed tracing and metrics:
- **Tracing:** Exported via OTLP/gRPC to a collector.
- **Metrics:** Periodic exporting of system and application metrics.
- **Instrumentation:** Automatic instrumentation for FastAPI and logging.

## Key Parameters

| Parameter | Source | Description |
|-----------|--------|-------------|
| `PORT` | ENV | Server port (default: 8082) |
| `LOG_LEVEL` | ENV | Logging verbosity (ERROR, INFO, etc.) |
| `OTEL_ENABLED` | ENV | Enable/disable tracing (default: true) |
| `UI_DIST_DIR` | Filesystem | Path to built Next.js frontend assets |

## Relationships

- **Orchestrates:** [[Simulation Engine]]
- **Exposes:** [[API Endpoint Reference]], [[WebSocket Protocol]]
- **Observability via:** [[OpenTelemetry]]
- **Data via:** [[Transport Layer]]

## Known Issues

- The catch-all route for SPA routing may interfere with certain API extensions if not carefully ordered.
- OpenTelemetry initialization is synchronous and block during startup if the endpoint is unavailable (mitigated by gRPC timeout).
- Static file serving depends on the presence of the `ui/dist` directory.
