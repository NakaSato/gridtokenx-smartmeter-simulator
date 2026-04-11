---
title: "Transport Layer"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/transport/base.py", "docs/architecture/transport-layer.md"]
tags: [transport, protocols, delivery]
related: [[gRPC Transport]], [[MQTT Transport]], [[WebSocket Protocol]], [[Kafka Transport]], [[InfluxDB Schema]], [[DLMS/COSEM]]
---

# Transport Layer

The transport layer provides an abstract interface for delivering meter readings to downstream systems. Multiple transports can be composed via `CompositeTransport` for parallel broadcasting.

## Summary

All transports inherit from `TransportLayer`, which provides connection state management, retry logic, and reading conversion helpers. Available implementations: HTTP REST, gRPC (DLMS/COSEM), MQTT, Kafka, InfluxDB, WebSocket, and Composite (multi-transport aggregator).

## Architecture

```
┌──────────────────────────────────────┐
│        CompositeTransport            │
│  ┌────────┐ ┌──────┐ ┌────────────┐ │
│  │ HTTP   │ │ gRPC │ │ InfluxDB   │ │
│  │ REST   │ │ DLMS │ │ Time-Series│ │
│  └────────┘ └──────┘ └────────────┘ │
└──────────────────────────────────────┘
         ↓                ↓
    API Gateway      Time-Series DB
```

## Transport Implementulations

### HTTP (`HttpTransport`)
- **Purpose:** REST API submission to API Gateway
- **Endpoint:** `POST {API_GATEWAY_URL}/api/readings`
- **Auth:** API key header
- **Retry:** Configurable attempts + delay

### gRPC (`GrpcTransport`)
- **Purpose:** Industrial DLMS/COSEM ingestion
- **Protocol:** Protobuf serialization
- **Gateway:** Configurable host:port (default localhost:50051)
- **Standard:** IEC 62056 DLMS/COSEM wrapper

### MQTT (`MqttTransport`)
- **Purpose:** IoT broker publishing
- **Broker:** Eclipse Mosquitto (port 1883)
- **Topic:** Configurable base topic (e.g., `gridtokenx/meters/`)
- **QoS:** At-least-once delivery

### Kafka (`KafkaTransport`)
- **Purpose:** Event streaming for distributed systems
- **Topic:** `meter_readings` (configurable)
- **Bootstrap:** Configurable broker list
- **Use case:** Multi-consumer event sourcing

### InfluxDB (`InfluxDBTransport`)
- **Purpose:** Time-series persistence
- **Bucket:** `meter_readings` (configurable)
- **Org:** `gridtokenx`
- **Retention:** 52 weeks (configurable)
- **See:** [[InfluxDB Schema]] for data model

### WebSocket (`WebSocketTransport`)
- **Purpose:** Real-time broadcasting to dashboards
- **Endpoint:** `ws://localhost:8765/ws`
- **Format:** JSON (see [[WebSocket Protocol]])
- **Managed by:** `WebSocketManager` in FastAPI app

### Composite (`CompositeTransport`)
- **Purpose:** Aggregates multiple transports for parallel broadcasting
- **Behavior:** Sends to all configured transports simultaneously
- **Error handling:** Continues if individual transport fails

## Base Class Interface

```python
class TransportLayer(ABC):
    async def connect(self) -> None
    async def disconnect(self) -> None
    async def send_reading(self, reading: EnergyReading) -> None
    async def send_batch(self, readings: List[EnergyReading]) -> None
    # Retry logic with configurable attempts/delay
```

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `TRANSPORT_TYPE` | grpc | Primary transport (grpc, http, kafka, mqtt) |
| `API_GATEWAY_URL` | http://localhost:4000 | HTTP REST endpoint |
| `GRPC_GATEWAY_HOST` | localhost | gRPC gateway host |
| `GRPC_GATEWAY_PORT` | 50051 | gRPC gateway port |
| `KAFKA_BOOTSTRAP_SERVERS` | localhost:29092 | Kafka broker list |
| `KAFKA_TOPIC` | meter_readings | Kafka topic name |
| `MQTT_BROKER_URL` | mqtt://localhost | MQTT broker URL |
| `MQTT_PORT` | 1883 | MQTT broker port |
| `INFLUXDB_URL` | http://localhost:8086 | InfluxDB endpoint |

## Relationships

- **Used by:** [[Simulation Engine]] (tick output)
- **Readings from:** [[Smart Meter]] (signed EnergyReading)
- **Formats:** [[DLMS/COSEM]], [[WebSocket Protocol]], [[InfluxDB Schema]]
- **Receivers:** API Gateway, InfluxDB, Kafka brokers, MQTT subscribers

## Known Issues

- CompositeTransport does not guarantee ordering across transports
- Retry logic is simple backoff — no exponential jitter
- gRPC transport assumes server is running — no connection pooling
- WebSocket connections not tracked for backpressure
