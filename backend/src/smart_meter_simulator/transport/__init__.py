"""Transport adapters that ship simulator readings to external consumers.

Provides the Oracle Bridge DLMS/COSEM (IEC 62056) REST client and per-tick
emitter (:mod:`smart_meter_simulator.transport.oracle_bridge`) — the sole egress
path to the parent ``gridtokenx-oracle-bridge`` — and the IAM onboarding client.
"""

from __future__ import annotations

from smart_meter_simulator.transport.iam_onboarding import (
    IamOnboardingClient,
    OnboardResult,
)
from smart_meter_simulator.transport.oracle_bridge import (
    MeterKey,
    OracleBridgeClient,
    OracleBridgeEmitter,
    register_meter_owners_redis,
    register_pubkeys_redis,
)

__all__ = [
    "MeterKey",
    "OracleBridgeClient",
    "OracleBridgeEmitter",
    "register_pubkeys_redis",
    "register_meter_owners_redis",
    "IamOnboardingClient",
    "OnboardResult",
]
