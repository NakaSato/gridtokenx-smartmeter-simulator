"""Transport adapters that ship simulator readings to external consumers.

Currently provides the Oracle Bridge DLMS/COSEM REST client
(:mod:`smart_meter_simulator.transport.oracle_bridge`).
"""

from __future__ import annotations

from smart_meter_simulator.transport.iam_onboarding import (
    IamOnboardingClient,
    OnboardResult,
)
from smart_meter_simulator.transport.oracle_bridge import (
    MeterKey,
    OracleBridgeClient,
    register_meter_owners_redis,
    register_pubkeys_redis,
)

__all__ = [
    "MeterKey",
    "OracleBridgeClient",
    "register_pubkeys_redis",
    "register_meter_owners_redis",
    "IamOnboardingClient",
    "OnboardResult",
]
