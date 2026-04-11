---
title: "DLMS/COSEM"
category: protocols
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/transport/grpc.py", "docs/reference/meter-spec.md"]
tags: [protocol, industrial, iec, grpc]
related: [[gRPC Transport]], [[Transport Layer]], [[EnergyReading Model]]
---

# DLMS/COSEM

DLMS/COSEM (Device Language Message Specification / Companion Specification for Energy Metering) is the IEC 62056 standard for smart meter data exchange. It defines the application layer protocol for reading meter registers, configuring parameters, and receiving push notifications.

## Summary

The Smart Meter Simulator implements a DLMS/COSEM wrapper over gRPC transport, enabling industrial-grade meter data ingestion compatible with standard AMI head-end systems.

## Protocol Stack

```
┌─────────────────────────────────────┐
│  DLMS/COSEM Application Layer      │  IEC 62056-53 (OBIS codes)
├─────────────────────────────────────┤
│  gRPC (HTTP/2 + Protobuf)          │  Transport + serialization
├─────────────────────────────────────┤
│  TCP/IP                            │  Network
└─────────────────────────────────────┘
```

## OBIS Codes

Object Identification System (OBIS) codes identify specific meter data:

| OBIS Code | Description | Simulator Field |
|-----------|-------------|-----------------|
| 1.8.0 | Active energy imported (total) | `energy_consumed_kwh` |
| 2.8.0 | Active energy exported (total) | `energy_generated_kwh` |
| 32.7.0 | Instantaneous voltage (L1) | `voltage_v` |
| 31.7.0 | Instantaneous current (L1) | `current_a` |
| 14.7.0 | Instantaneous frequency | `frequency_hz` |
| 13.7.0 | Instantaneous power factor | `power_factor` |
| 33.7.0 | Instantaneous reactive power | `reactive_power` |
| 81.7.x | Battery state of charge | `battery_level_kwh` |

## Protobuf Message

```protobuf
message EnergyReading {
  string meter_id = 1;
  string timestamp = 2;
  double energy_generated_kwh = 3;
  double energy_consumed_kwh = 4;
  double battery_level_kwh = 5;
  double voltage_v = 6;
  double current_a = 7;
  double frequency_hz = 8;
  double power_factor = 9;
  double reactive_power = 10;
  bytes signature = 11;
  bytes public_key = 12;
}

message ReadingBatch {
  repeated EnergyReading readings = 1;
}

service MeterIngestion {
  rpc SubmitReading(EnergyReading) returns (Ack);
  rpc SubmitBatch(ReadingBatch) returns (BatchAck);
}
```

## gRPC Service

| Method | Direction | Description |
|--------|-----------|-------------|
| `SubmitReading` | Meter → Server | Single reading submission |
| `SubmitBatch` | Meter → Server | Batch reading submission (multiple meters) |
| `GetMeterConfig` | Server → Meter | Retrieve meter configuration |
| `SetDispatch` | Server → Meter | VPP dispatch setpoint |

## Gateway Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `TRANSPORT_TYPE` | grpc | Selects gRPC transport |
| `GRPC_GATEWAY_HOST` | localhost | gRPC server hostname |
| `GRPC_GATEWAY_PORT` | 50051 | gRPC server port |

## Relationships

- **Transport:** [[gRPC Transport]]
- **Data model:** [[EnergyReading Model]]
- **Standard:** IEC 62056 DLMS/COSEM
- **Used by:** [[Transport Layer]]

## Known Issues

- Simplified DLMS wrapper — not full COSEM object model
- No HDLC/PLC lower layers (Ethernet only)
- No authentication/encryption at gRPC layer (mTLS not implemented)
- OBIS code mapping is approximate — not certified
