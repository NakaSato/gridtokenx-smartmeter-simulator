---
title: "Kafka Transport"
category: protocols
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/transport/kafka.py", "src/smart_meter_simulator/config/settings.py"]
tags: [transport, kafka, event-streaming, distributed]
related: [[Transport Layer]], [[EnergyReading Model]]
---

# Kafka Transport

Kafka transport provides high-throughput event streaming for distributed systems, enabling multiple consumers (analytics, billing, monitoring) to process meter readings independently.

## Summary

The `KafkaTransport` publishes meter readings to a Kafka topic as JSON messages, enabling event sourcing, replay, and multi-consumer processing pipelines. It is used alongside the primary transport (gRPC/HTTP/MQTT) via CompositeTransport.

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | localhost:29092 | Comma-separated broker list |
| `KAFKA_TOPIC` | `meter-readings` | Topic name |

## Message Format

JSON payload (same schema as [[EnergyReading Model]]):

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

### Key

The message key is the `meter_id`, enabling partitioning by meter:

```python
producer.send(
    topic="meter-readings",
    key=meter_id.encode(),        # Partition by meter
    value=json.dumps(reading).encode()
)
```

## Partitioning Strategy

| Strategy | Key | Effect |
|----------|-----|--------|
| **By meter_id** | `meter_id` | All readings from one meter go to same partition |
| **By feeder** | `feeder_id` | All meters on same feeder go to same partition |
| **Round-robin** | None | Even distribution across partitions |

Default: by `meter_id` — ensures ordering per meter.

## Consumer Use Cases

| Consumer | Purpose |
|----------|---------|
| Analytics engine | Real-time grid analytics |
| Billing service | Consumption tracking |
| Monitoring dashboard | Visualization |
| Anomaly detection | Bad data / FDI detection |
| Archive service | Long-term storage |

## Throughput

| Meters | Interval | Messages/sec | Est. Throughput |
|--------|----------|-------------|-----------------|
| 100 | 15s | 6.7 | ~3 KB/s |
| 1,000 | 15s | 67 | ~30 KB/s |
| 10,000 | 15s | 667 | ~300 KB/s |

Kafka easily handles these rates — bottleneck is typically the producer (simulation engine).

## Usage

```python
from smart_meter_simulator.transport.kafka import KafkaTransport

transport = KafkaTransport(
    bootstrap_servers="localhost:29092",
    topic="meter-readings"
)
await transport.connect()
await transport.send_reading(energy_reading)
```

## Relationships

- **Part of:** [[Transport Layer]]
- **Data model:** [[EnergyReading Model]]
- **Used with:** [[Transport Layer]] (CompositeTransport)

## Known Issues

- Kafka not included in default docker-compose (external dependency)
- No schema registry — payload format not enforced
- No consumer group management (producer-side only)
- No dead letter queue for failed processing
- Default topic name `meter-readings` uses hyphen (inconsistent with other transports)
