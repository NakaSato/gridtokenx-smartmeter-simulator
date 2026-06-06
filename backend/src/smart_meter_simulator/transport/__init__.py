"""Transport adapters that ship simulator readings to external consumers.

Provides the Oracle Bridge DLMS/COSEM REST client
(:mod:`smart_meter_simulator.transport.oracle_bridge`) and the binary
Protocol-v4 gRPC ``BulkRawIngest`` client
(:mod:`smart_meter_simulator.transport.oracle_grpc`).
"""

from __future__ import annotations

from smart_meter_simulator.transport.iam_onboarding import (
    IamOnboardingClient,
    OnboardResult,
)
from smart_meter_simulator.transport.oracle_bridge import (
    MeterKey,
    OracleBridgeClient,
    register_device_aes_keys_redis,
    register_meter_owners_redis,
    register_pubkeys_redis,
)
from smart_meter_simulator.transport.oracle_grpc import (
    OracleGrpcClient,
    RustExtensionMissing,
    build_bulk_payload,
    build_meter_keys,
)

__all__ = [
    "MeterKey",
    "OracleBridgeClient",
    "register_pubkeys_redis",
    "register_device_aes_keys_redis",
    "register_meter_owners_redis",
    "IamOnboardingClient",
    "OnboardResult",
    "OracleGrpcClient",
    "RustExtensionMissing",
    "build_bulk_payload",
    "build_meter_keys",
]
