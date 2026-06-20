"""Transport adapters that ship simulator readings to external consumers.

Provides the Aggregator Bridge DLMS/COSEM (IEC 62056) REST client and per-tick
emitter (:mod:`smart_meter_simulator.transport.aggregator_bridge`) — the sole egress
path to the parent ``gridtokenx-aggregator-bridge`` — and the IAM onboarding client.
"""

from __future__ import annotations

from smart_meter_simulator.transport.iam_onboarding import (
    IamOnboardingClient,
    OnboardResult,
    onboard_fleet,
)
from smart_meter_simulator.transport.aggregator_bridge import (
    MeterKey,
    AggregatorBridgeClient,
    AggregatorBridgeEmitter,
    TouSchedule,
    read_meter_owners_redis,
    register_meter_owners_redis,
    register_pubkeys_redis,
)
from smart_meter_simulator.transport.operational_telemetry import (
    OperationalTelemetryClient,
    OperationalTelemetryEmitter,
    summary_to_points,
)

__all__ = [
    "MeterKey",
    "AggregatorBridgeClient",
    "AggregatorBridgeEmitter",
    "TouSchedule",
    "register_pubkeys_redis",
    "register_meter_owners_redis",
    "read_meter_owners_redis",
    "IamOnboardingClient",
    "OnboardResult",
    "onboard_fleet",
    "OperationalTelemetryClient",
    "OperationalTelemetryEmitter",
    "summary_to_points",
]
