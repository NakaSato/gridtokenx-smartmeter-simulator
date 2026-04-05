# Transport Layer

The **Transport Layer** is responsible for the reliable delivery of simulation telemetry, grid status, and alerts to external consumers. It abstracts the underlying communication protocols and provides a unified interface for the `SimulationEngine`.

## 🏗️ Architecture

All transport implementations inherit from a common `TransportLayer` base class (in `src/smart_meter_simulator/transport/base.py`), which provides:
-   **Connection Management**: Standardized `connect()` and `disconnect()` methods.
-   **Exponential Backoff**: Automated retry logic for transient network failures.
-   **State Tracking**: Thread-safe monitoring of the connection status.

## 📡 Supported Protocols

The simulator is designed to be protocol-agnostic, supporting several industrial and web standards:

### 1. HTTP / REST (`http.py`)
-   Sends JSON-encoded meter readings to the GridTokenX API Gateway.
-   Supports batch ingestion for high-throughput scenarios.
-   Uses `X-API-Key` for secure Cloud-to-Cloud (C2C) communication.

### 2. gRPC Gateway (`grpc.py`)
-   Standardized interface for industrial-grade data ingestion.
-   Uses high-performance Protobuf serialization.
-   Primary integration point for the GridTokenX Oracle Bridge.

### 3. MQTT (Industrial AMI) (`mqtt.py`)
-   Integrates with MQTT brokers (e.g., Mosquitto).
-   Supports **DLMS/COSEM** over MQTT for legacy AMI infrastructure compatibility.
-   Uses a hierarchical topic structure: `gridtokenx/ami/telemetry/{meter_id}`.

### 4. InfluxDB (Time-Series) (`influxdb.py`)
-   Direct persistence to InfluxDB v2.
-   Optimized for high-cadence time-series data storage.
-   Stores meter readings, grid state estimation, and VPP dispatch events.

### 5. WebSocket (`websocket.py`)
-   Provides real-time telemetry streams to the web dashboard.
-   Uses an asynchronous publish/subscribe model to broadcast updates to connected clients.

### 6. Kafka (`kafka.py`)
-   Integration for event-driven architectures and high-scale stream processing.
-   Publishes to configurable topics (default: `meter-readings`).

## 🔀 Composite Transport

The `CompositeTransport` (`composite.py`) is a specialized implementation that allows the simulator to broadcast data through multiple transport mechanisms simultaneously. For example, a single simulation can send data to InfluxDB for storage, Kafka for processing, and WebSocket for real-time visualization.

```python
# Multiple transports operating in parallel
transport = CompositeTransport([
    HttpTransport(api_url),
    InfluxDBTransport(influx_config),
    WebSocketTransport(ws_manager)
])
```

---
_Next: [Meter Specifications](../reference/meter-spec.md)_
