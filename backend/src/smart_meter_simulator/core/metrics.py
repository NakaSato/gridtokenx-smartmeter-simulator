"""
Prometheus Metrics for Simulation and Benchmarking
"""

import time
from contextlib import contextmanager
from prometheus_client import Histogram, Gauge, Counter

# Solver Metrics
SIMULATION_SOLVER_TIME = Histogram(
    "sim_solver_time_seconds",
    "Time spent executing Newton-Raphson power flow solver",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0],
)

# Transport Metrics
TRANSPORT_LATENCY = Histogram(
    "sim_transport_latency_seconds",
    "Latency of sending payloads to the transport layer",
    ["transport_type"],
    buckets=[0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
)

TRANSPORT_PAYLOAD_SIZE = Histogram(
    "sim_transport_payload_size_bytes",
    "Size of data payload sent in bytes",
    ["transport_type"],
    buckets=[1024, 10240, 102400, 1048576, 10485760],
)

# Core Execution Metrics
SIMULATION_TICK_TIME = Histogram(
    "sim_tick_time_seconds",
    "Total time spent processing one simulation tick",
    buckets=[0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
)

ACTIVE_METERS = Gauge(
    "sim_active_meters",
    "Number of active meters in the simulation",
)

@contextmanager
def measure_time(metric_histogram, **labels):
    start_time = time.time()
    yield
    duration = time.time() - start_time
    if labels:
        metric_histogram.labels(**labels).observe(duration)
    else:
        metric_histogram.observe(duration)
