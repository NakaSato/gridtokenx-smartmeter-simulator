---
title: "gRPC Transport"
category: protocols
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/transport/grpc.py", "docs/reference/meter-spec.md"]
tags: [transport, grpc, protobuf, industrial]
related: [[DLMS/COSEM]], [[Transport Layer]], [[EnergyReading Model]]
---

# gRPC Transport

gRPC transport provides industrial-grade telemetry ingestion using HTTP/2 + Protobuf serialization, wrapped in a DLMS/COSEM-compatible service interface.

## Summary

The `GrpcTransport` submits signed meter readings to a gRPC gateway endpoint using protobuf serialization. This is the default transport type (`TRANSPORT_TYPE=grpc`) and aligns with industrial AMI head-end system standards.

## Service Definition

```protobuf
// src/smart_meter_simulator/transport/proto/gridtokenx/oracle/v1/oracle.proto

service MeterIngestion {
  rpc SubmitReading(EnergyReading) returns (Ack);
  rpc SubmitBatch(ReadingBatch) returns (BatchAck);
}

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

message Ack {
  bool accepted = 1;
  string message = 2;
}

message BatchAck {
  int32 accepted_count = 1;
  int32 rejected_count = 2;
  repeated string rejected_ids = 3;
}
```

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `TRANSPORT_TYPE` | grpc | Selects gRPC as primary transport |
| `GRPC_GATEWAY_HOST` | localhost | gRPC server hostname |
| `GRPC_GATEWAY_PORT` | 5030 | gRPC server port |

## Usage

```python
from smart_meter_simulator.transport.grpc import GrpcTransport

transport = GrpcTransport(host="localhost", port=5030)
await transport.connect()
await transport.send_reading(energy_reading)
await transport.send_batch(readings)
```

## Protocol Stack

```
┌──────────────────────────┐
│  DLMS/COSEM semantics    │  Application layer (OBIS codes)
├──────────────────────────┤
│  gRPC (HTTP/2)           │  Transport + streaming
├──────────────────────────┤
│  Protobuf serialization  │  Binary encoding
├──────────────────────────┤
│  TCP/IP                  │  Network
└──────────────────────────┘
```

## Advantages over HTTP

| Property | HTTP/JSON | gRPC/Protobuf |
|----------|-----------|---------------|
| Payload size | ~500 bytes | ~150 bytes (3× smaller) |
| Serialization | Slow (JSON parse) | Fast (binary decode) |
| Streaming | No | Yes (server/client/bidi) |
| Type safety | Loose | Strict (compiled schema) |
| Multiplexing | No (HTTP/1.1) | Yes (HTTP/2 streams) |

## Proto Generation

Protobuf files are compiled using `betterproto`:

```bash
# Generate Python gRPC stubs
python -m grpc_tools.protoc \
  -I proto/ \
  --python_out=src/ \
  --grpc_python_out=src/ \
  proto/gridtokenx/oracle/v1/oracle.proto
```

## Relationships

- **Protocol:** [[DLMS/COSEM]] (application semantics)
- **Part of:** [[Transport Layer]]
- **Data model:** [[EnergyReading Model]]
- **Configuration:** `config/settings.py`

## Known Issues

- No mTLS configured — transport is unencrypted
- No connection pooling — single channel per transport
- No retry/backoff on transient failures
- Proto schema may drift if not kept in sync with EnergyReading model
