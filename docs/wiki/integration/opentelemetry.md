---
title: "OpenTelemetry"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/app.py", "pyproject.toml"]
tags: [observability, otel, tracing, metrics]
related: [[Docker Stack]], [[InfluxDB Integration]], [[FastAPI App]]
---

# OpenTelemetry

OpenTelemetry (OTEL) provides distributed tracing and metrics for the Smart Meter Simulator, enabling observability into the simulation pipeline from reading generation through transport delivery.

## Summary

The simulator instruments FastAPI with OTEL auto-instrumentation, exporting traces and metrics via OTLP (gRPC) to a collector endpoint. This enables end-to-end request tracing, performance profiling, and real-time monitoring.

## Instrumentation

### Tracing

```python
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

resource = Resource.create({
    "service.name": "gridtokenx-smartmeter-simulator",
    "deployment.environment": "development",
})

tracer_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(tracer_provider)
```

### Metrics

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

metric_exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
```

### FastAPI Instrumentation

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

FastAPIInstrumentor.instrument_app(app)
LoggingInstrumentor().instrument(set_logging_format=True)
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `opentelemetry-api` | API definitions |
| `opentelemetry-sdk` | SDK implementation |
| `opentelemetry-exporter-otlp` | OTLP gRPC exporter |
| `opentelemetry-instrumentation-fastapi` | Auto-instrument FastAPI |
| `opentelemetry-instrumentation-logging` | Auto-instrument logging |

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `OTEL_ENABLED` | true | Enable/disable OTEL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | OTLP collector endpoint |
| `OTEL_SERVICE_NAME` | `gridtokenx-smartmeter-simulator` | Service name |
| `OTEL_RESOURCE_ATTRIBUTES` | — | Additional resource attributes |

## Traced Spans

FastAPI auto-instrumentation generates spans for:

| Span | Description |
|------|-------------|
| `HTTP {method} {path}` | Each API request |
| `SimulationEngine.tick` | Each simulation cycle |
| `TransportLayer.send_*` | Each transport dispatch |

Custom spans can be added:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("generate_readings"):
    readings = engine.generate_readings()
```

## Metrics Exported

| Metric | Type | Description |
|--------|------|-------------|
| `http.server.duration` | Histogram | Request latency |
| `http.server.active_requests` | UpDownCounter | Concurrent requests |
| `http.server.response.size` | Histogram | Response size |
| `process.runtime.memory` | Gauge | Memory usage |
| `process.runtime.cpu.time` | Counter | CPU time |

## OTLP Collector (Not in Stack)

The simulator exports to an OTLP collector (not included in docker-compose). The collector would:

1. Receive traces/metrics from simulator
2. Batch and export to backends (Jaeger, Prometheus, etc.)
3. Apply sampling and filtering policies

```yaml
# Example otel-collector config (not in current stack)
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

## Relationships

- **Instrumented app:** [[FastAPI App]]
- **Service:** Part of [[Docker Stack]] (not yet included)
- **Metrics:** Complements [[InfluxDB Integration]] (business metrics)

## Known Issues

- OTEL collector not included in docker-compose
- No custom spans for simulation internals (tick, dispatch, estimation)
- No log correlation with traces (correlation context not propagated)
- Insecure gRPC (no TLS) to collector
- Prometheus metrics exporter available but no Prometheus in stack
