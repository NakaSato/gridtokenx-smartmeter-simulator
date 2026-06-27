"""Security-posture endpoint for the dashboard.

Reports what telemetry hardening this simulator's egress is configured for — TLS,
mTLS, per-meter AES-256-GCM payload encryption, Vault-KEK key rotation — for both
the DLMS metering path and the operational/SCADA path, plus live per-meter key
versions. Read-only; surfaces config + the engine's current key state so the UI
can show the security stack at a glance. See ``docs/telemetry-security.md`` in the
parent monorepo for the full model.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/security", tags=["Security"])


def _config():
    from smart_meter_simulator.config.settings import get_config

    return get_config()


@router.get("/status")
async def security_status() -> Dict[str, Any]:
    """The simulator's egress security posture + live key versions."""
    c = _config()
    from smart_meter_simulator.core import app_state

    engine = app_state.engine
    key_versions: Dict[str, int] = engine.meter_key_status() if engine else {}

    bridge_https = c.aggregator_bridge_url.lower().startswith("https")
    metering_mtls = bool(c.aggregator_tls_client_cert and c.aggregator_tls_client_key)
    op_https = c.operational_outstation_url.lower().startswith("https")
    op_mtls = bool(c.operational_tls_client_cert and c.operational_tls_client_key)

    metering = {
        "enabled": c.aggregator_dlms_enabled,
        "endpoint": c.aggregator_bridge_url,
        "tls": bridge_https,
        "tls_verify": bool(c.aggregator_tls_ca) or bridge_https,
        "mtls": metering_mtls,
        "payload_encryption": c.aggregator_encrypt_enabled,
        "key_rotation": c.aggregator_key_rotation_enabled,
        "rotation_interval_s": c.aggregator_key_rotation_interval_s,
        "key_grace_versions": c.aggregator_key_grace_versions,
    }
    operational = {
        "enabled": c.operational_telemetry_enabled,
        "transport": c.operational_transport,
        "endpoint": c.operational_outstation_url,
        "tls": op_https,
        "mtls": op_mtls,
        "api_key": bool(c.operational_api_key),
    }
    keys = {
        "rotation_active": bool(key_versions),
        "meter_count": len(key_versions),
        "versions": key_versions,
    }

    # Flat on/off list for an at-a-glance UI badge row (metering path).
    layers = [
        {"name": "TLS in transit", "on": metering["tls"]},
        {"name": "mTLS (client cert)", "on": metering["mtls"]},
        {
            "name": "Payload encryption (AES-256-GCM)",
            "on": metering["payload_encryption"],
        },
        {"name": "Key rotation (Vault-KEK)", "on": metering["key_rotation"]},
    ]
    secure = all(layer["on"] for layer in layers) and metering["enabled"]

    return {
        "secure": secure,
        "layers": layers,
        "metering_egress": metering,
        "operational_egress": operational,
        "keys": keys,
    }
