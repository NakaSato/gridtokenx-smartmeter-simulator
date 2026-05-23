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

Object Identification System (OBIS) codes identify specific meter data according to the IEC 62056-61 standard using the `A-B:C.D.E*F` schema:

| OBIS Code | Description | Simulator Field |
|-----------|-------------|-----------------|
| `1.0.1.8.0.255` | Active energy imported (total) | `energy_consumed_kwh` |
| `1.0.2.8.0.255` | Active energy exported (total) | `energy_generated_kwh` |
| `1.0.1.7.0.255` | Active power imported (+P) | `active_power_cons_kw` |
| `1.0.2.7.0.255` | Active power exported (-P) | `active_power_gen_kw` |
| `1.0.32.7.0.255` | Instantaneous voltage (L1) | `voltage_v` |
| `1.0.31.7.0.255` | Instantaneous current (L1) | `current_a` |
| `1.0.14.7.0.255` | Instantaneous frequency | `frequency_hz` |
| `1.0.13.7.0.255` | Instantaneous power factor | `power_factor` |
| `1.0.3.7.0.255` | Instantaneous reactive power (+Q) | `reactive_power` |
| `0.0.96.6.3.255` | Battery state of charge (Abstract) | `battery_level` |
| `0.0.1.0.0.255` | Clock object | `timestamp` |

... (Protobuf Message section skipped) ...

## DLMS Interface Classes (IEC 62056-62)
Data is structured natively into the JSON payload according to COSEM Interface Classes (IC):
- **Class 1 (Data):** Simple abstract values.
- **Class 3 (Register):** Includes value, scalar, and standard DLMS units (V, A, W, Var, Hz).
- **Class 4 (Extended Register):** Includes value, scalar, units, and capture timestamps.
- **Class 7 (Profile Generic):** Used for buffering 15-minute time series profiles.
- **Class 8 (Clock):** Time sync management.

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
| `GRPC_GATEWAY_PORT` | 5030 | gRPC server port |

## Relationships

- **Transport:** [[gRPC Transport]]
- **Data model:** [[EnergyReading Model]]
- **Standard:** IEC 62056 DLMS/COSEM
- **Used by:** [[Transport Layer]]

## Implementation Notes

- **Interface Classes**: The system dynamically maps values to IC 1 (Data), IC 3 (Register), IC 4 (Extended Register), IC 7 (Profile Generic), and IC 8 (Clock) with corresponding scalars and units.
- **OBIS Standards**: Mapping strictly follows the IEC 62056-61 standard schema (A-B:C.D.E*F).
- **Transport**: Operates over Ethernet/gRPC (no HDLC/PLC lower layers modeled in this simulation layer).
