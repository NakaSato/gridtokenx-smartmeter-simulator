---
title: "MQTT Transport"
category: protocols
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/transport/mqtt.py", "docker-compose.yml"]
tags: [transport, mqtt, iot, broker]
related: [[Transport Layer]], [[EnergyReading Model]]
---

# MQTT Transport

MQTT transport publishes meter readings to an MQTT broker for IoT ecosystem integration, enabling industrial AMI data ingestion by head-end systems and SCADA platforms.

## Summary

The `MqttTransport` connects to an Eclipse Mosquitto broker and publishes signed meter readings as JSON payloads on configurable topics. It supports QoS 1 (at-least-once) delivery for reliable telemetry.

## Broker Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `MQTT_BROKER_URL` | mqtt://localhost | Broker URL |
| `MQTT_PORT` | 1883 | Broker port |
| `MQTT_USERNAME` | (empty) | Auth username |
| `MQTT_PASSWORD` | (empty) | Auth password |
| `MQTT_TOPIC` | `gridtokenx/ami/telemetry` | Base topic |

## Topic Structure

```
gridtokenx/ami/telemetry/{meter_type}/{meter_id}

Examples:
  gridtokenx/ami/telemetry/solar_prosumer/AMI_METER_001
  gridtokenx/ami/telemetry/grid_consumer/AMI_METER_015
  gridtokenx/ami/telemetry/battery_storage/AMI_METER_042
```

## Payload Format

JSON (same schema as [[EnergyReading Model]]):

```json
{
  "meter_id": "AMI_METER_001",
  "timestamp": "2026-04-10T12:00:00Z",
  "energy_generated_kwh": 5.234,
  "energy_consumed_kwh": 2.145,
  "battery_level_kwh": 7.5,
  "voltage_v": 239.8,
  "current_a": 12.3,
  "frequency_hz": 50.02,
  "power_factor": 0.95,
  "reactive_power": 1.642,
  "signature": "base64...",
  "public_key": "base64..."
}
```

## QoS Level

| QoS | Delivery | In Simulator |
|-----|----------|--------------|
| 0 (at most once) | Fire and forget | ❌ Not used |
| 1 (at least once) | Acknowledged, may duplicate | ✅ Used |
| 2 (exactly once) | Four-handshake, guaranteed | ❌ Overhead too high |

QoS 1 is the default — broker acknowledges receipt, ensuring no data loss on transient failures.

## Docker Service

```yaml
mosquitto:
  image: eclipse-mosquitto:2.0
  ports:
    - "1883:1883"   # MQTT
    - "9001:9001"   # WebSocket
  volumes:
    - ./docker/mosquitto/config:/mosquitto/config
```

## Usage

```python
from smart_meter_simulator.transport.mqtt import MqttTransport

transport = MqttTransport(
    broker_url="mqtt://localhost",
    port=1883,
    base_topic="gridtokenx/ami/telemetry"
)
await transport.connect()
await transport.send_reading(energy_reading)  # Publishes to topic
```

## Relationships

- **Broker:** Eclipse Mosquitto 2.0
- **Part of:** [[Transport Layer]]
- **Data model:** [[EnergyReading Model]]
- **Docker:** `docker-compose.yml` (mosquitto service)

## Known Issues

- No TLS by default — credentials sent in plaintext
- No retained messages — late subscribers miss prior readings
- No Last Will and Testament (LWT) for meter offline detection
- Topic structure doesn't include feeder or substation context
