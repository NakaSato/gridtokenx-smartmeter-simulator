"""Shape + posture contract for the /api/v1/security/status endpoint."""

from __future__ import annotations

import asyncio

from smart_meter_simulator.routers.security_v1 import security_status


def test_security_status_shape_and_layers(monkeypatch):
    # No engine -> empty key versions; config from env defaults.
    import smart_meter_simulator.core.app_state as app_state

    monkeypatch.setattr(app_state, "engine", None, raising=False)
    body = asyncio.run(security_status())

    assert set(body) == {
        "secure",
        "layers",
        "metering_egress",
        "operational_egress",
        "keys",
    }
    # Four named metering layers, each a name + bool.
    names = [layer["name"] for layer in body["layers"]]
    assert "TLS in transit" in names and "mTLS (client cert)" in names
    assert all(isinstance(layer["on"], bool) for layer in body["layers"])
    # `secure` is the AND of the layers + metering enabled.
    expected = (
        all(layer["on"] for layer in body["layers"])
        and body["metering_egress"]["enabled"]
    )
    assert body["secure"] is expected
    # Keys block present with no engine -> not rotating, 0 meters.
    assert body["keys"] == {"rotation_active": False, "meter_count": 0, "versions": {}}
