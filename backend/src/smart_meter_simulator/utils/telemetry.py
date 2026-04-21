import logging
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor

logger = logging.getLogger(__name__)

def setup_telemetry(service_name: str):
    """Set up OpenTelemetry and logging."""
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    otel_enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
    if not otel_enabled:
        logger.info("OpenTelemetry is disabled")
        return False

    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    logger.info(f"Initializing OpenTelemetry with endpoint: {otel_endpoint}")

    try:
        # Resource attributes
        resource = Resource.create({
            "service.name": service_name,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })

        # Tracing
        tracer_provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)

        # Metrics
        metric_exporter = OTLPMetricExporter(endpoint=otel_endpoint, insecure=True)
        reader = PeriodicExportingMetricReader(metric_exporter)
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)
        
        # Logging Instrumentation
        LoggingInstrumentor().instrument(set_logging_format=True)
        
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}")
        return False
