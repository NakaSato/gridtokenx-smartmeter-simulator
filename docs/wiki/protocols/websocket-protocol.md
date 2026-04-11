---
title: "WebSocket Protocol"
category: protocols
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/transport/websocket.py", "src/smart_meter_simulator/app.py"]
tags: [transport, websocket, real-time, json]
related: [[Transport Layer]], [[FastAPI App]], [[EnergyReading Model]]
---

# WebSocket Protocol

The WebSocket protocol provides real-time streaming of meter readings to connected clients (dashboards, monitoring systems, analytics pipelines).

## Summary

The simulator broadcasts signed meter readings over WebSocket to all connected clients. Each message is a JSON object containing the full EnergyReading payload plus the Ed25519 signature.

## Connection

```
ws://localhost:8765/ws
```

Multiple clients can connect simultaneously. All clients receive all readings (broadcast model).

## Message Format

Each message is a single JSON object:

```json
{
  "timestamp": "2026-04-10T12:00:00Z",
  "meter_id": "AMI_METER_001",
  "energy_generated_kwh": 5.234,
  "energy_consumed_kwh": 2.145,
  "surplus_energy": 3.089,
  "deficit_energy": 0.0,
  "battery_level_kwh": 7.5,
  "voltage_v": 239.8,
  "current_a": 12.3,
  "frequency_hz": 50.02,
  "power_factor": 0.95,
  "reactive_power": 1.642,
  "signature": "base64-encoded-64-byte-signature",
  "public_key": "base64-encoded-32-byte-public-key"
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (ISO 8601) | Reading timestamp (UTC) |
| `meter_id` | string | Unique meter identifier |
| `energy_generated_kwh` | float | Generation in the interval (kWh) |
| `energy_consumed_kwh` | float | Consumption in the interval (kWh) |
| `surplus_energy` | float | Net export (kWh) |
| `deficit_energy` | float | Net import (kWh) |
| `battery_level_kwh` | float | Current battery state (kWh) |
| `voltage_v` | float | Line voltage (Volts) |
| `current_a` | float | Line current (Amps) |
| `frequency_hz` | float | Grid frequency (Hz) |
| `power_factor` | float | Power factor [0, 1] |
| `reactive_power` | float | Reactive power (kVAR) |
| `signature` | string (base64) | Ed25519 signature (64 bytes) |
| `public_key` | string (base64) | Signer's public key (32 bytes) |

## Message Rate

| Configuration | Interval | Messages/sec (55 meters) |
|---------------|----------|--------------------------|
| Default | 15s | ~3.7 msg/s |
| Fast | 5s | ~11 msg/s |
| Stress | 1s | ~55 msg/s |

## WebSocket Manager

The `WebSocketManager` class handles:
- Connection lifecycle (accept, track, disconnect)
- Broadcast to all connected clients
- Automatic cleanup on disconnect
- Connection count tracking

## Client Example (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onmessage = (event) => {
  const reading = JSON.parse(event.data);
  console.log(`${reading.meter_id}: ${reading.energy_generated_kwh} kWh gen`);
};

ws.onclose = () => console.log('WebSocket closed');
```

## Relationships

- **Managed by:** [[FastAPI App]] (WebSocketManager)
- **Part of:** [[Transport Layer]]
- **Data model:** [[EnergyReading Model]]
- **Signing:** [[Ed25519 Signing]]

## Known Issues

- No message filtering (clients receive all meters)
- No backpressure (fast producers may overwhelm slow clients)
- No authentication (anyone can connect)
- Reconnection logic is client-side responsibility
