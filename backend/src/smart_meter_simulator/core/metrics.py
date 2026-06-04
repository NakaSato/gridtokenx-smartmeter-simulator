"""Prometheus metrics for the GLM grid simulator."""

import time
from contextlib import contextmanager
from prometheus_client import Gauge, Histogram

SIMULATION_TICK_TIME = Histogram(
    "sim_tick_time_seconds",
    "Time spent processing one simulation tick",
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
