"""Contract tests for the Oracle Bridge DLMS/COSEM REST egress.

Pin the wire contract the parent ``gridtokenx-oracle-bridge`` parses:
- the OBIS-coded JSON payload (``DlmsStack.map_payload``),
- the ``{device_id}:{kwh}:{timestamp_ms}`` Ed25519 signature canonical string
  (``verify_rest_signature`` in ``src/handlers.rs``),
- the ``{protocol, device_id, payload}`` ingest envelope.

Pure unit tests — no running bridge, no Redis. The mirrored Wh<->kWh constants
match ``dlms.rs``'s own test (10000 Wh import -> 10 kWh).
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import base58
import httpx
import pytest

from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.transport.oracle_bridge import (
    OBIS_ACTIVE_EXPORT,
    OBIS_ACTIVE_IMPORT,
    OBIS_CURRENT_L1,
    OBIS_FREQUENCY,
    OBIS_POWER_FACTOR,
    OBIS_REACTIVE_EXPORT,
    OBIS_REACTIVE_IMPORT,
    OBIS_VOLTAGE_L1,
    MeterKey,
    OracleBridgeClient,
    _build_obis_payload,
    _rust_f64_str,
)


def _reading(**overrides) -> EnergyReading:
    base = dict(
        meter_id="METER-001",
        timestamp=datetime(2026, 6, 6, 8, 30, 0, tzinfo=timezone.utc),
        energy_generated=5.0,  # kWh -> 5000 Wh export
        energy_consumed=10.0,  # kWh -> 10000 Wh import
        surplus_energy=0.0,
        deficit_energy=5.0,
        location="bus-1",
        meter_type="grid_consumer",
        user_type="residential",
    )
    base.update(overrides)
    return EnergyReading(**base)


# --- _rust_f64_str (must match Rust f64::to_string) -------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (1.0, "1"),
        (-2.0, "-2"),
        (0.0, "0"),
        (0.5, "0.5"),
        (-0.123456, "-0.123456"),
        (10.0, "10"),
    ],
)
def test_rust_f64_str(value, expected):
    assert _rust_f64_str(value) == expected


# --- OBIS payload shape -----------------------------------------------------


def test_obis_payload_active_energy_in_wh():
    key = MeterKey("METER-001")
    payload = _build_obis_payload(_reading(), key, None)
    # dlms.rs maps these OBIS codes back to kWh by dividing by 1000.
    assert payload[OBIS_ACTIVE_IMPORT] == 10000.0  # 10 kWh consumed
    assert payload[OBIS_ACTIVE_EXPORT] == 5000.0  # 5 kWh generated
    assert payload["kwh"] == -5.0  # net = generated - consumed


def test_obis_payload_optional_fields_present_only_when_set():
    key = MeterKey("METER-001")
    bare = _build_obis_payload(_reading(), key, None)
    assert OBIS_VOLTAGE_L1 not in bare
    assert OBIS_CURRENT_L1 not in bare
    assert OBIS_FREQUENCY not in bare
    assert OBIS_POWER_FACTOR not in bare
    assert OBIS_REACTIVE_IMPORT not in bare and OBIS_REACTIVE_EXPORT not in bare

    full = _build_obis_payload(
        _reading(
            voltage=230.5,
            current=12.0,
            frequency=50.01,
            power_factor=0.95,
        ),
        key,
        "ZONE-A",
    )
    assert full[OBIS_VOLTAGE_L1] == 230.5
    assert full[OBIS_CURRENT_L1] == 12.0
    assert full[OBIS_FREQUENCY] == 50.01
    assert full[OBIS_POWER_FACTOR] == 0.95
    assert full["zone_code"] == "ZONE-A"


def test_obis_reactive_energy_sign_and_scaling():
    key = MeterKey("METER-001")
    # +6 kvar over a 900 s (0.25 h) interval = 1.5 kvarh = 1500 varh, import side.
    imp = _build_obis_payload(
        _reading(reactive_power_kvar=6.0, interval_seconds=900), key, None
    )
    assert imp[OBIS_REACTIVE_IMPORT] == 1500.0
    assert OBIS_REACTIVE_EXPORT not in imp

    # negative kvar -> export side, magnitude only.
    exp = _build_obis_payload(
        _reading(reactive_power_kvar=-6.0, interval_seconds=900), key, None
    )
    assert exp[OBIS_REACTIVE_EXPORT] == 1500.0
    assert OBIS_REACTIVE_IMPORT not in exp


# --- signature canonical contract -------------------------------------------


def test_signature_matches_bridge_canonical_and_verifies():
    key = MeterKey("METER-001")
    reading = _reading()
    payload = _build_obis_payload(reading, key, None)

    # Reconstruct the canonical string exactly as handlers.rs does:
    #   {device_id}:{kwh_via_f64_to_string}:{timestamp_millis}
    ts = reading.timestamp.replace(microsecond=0)
    ts_ms = int(ts.timestamp()) * 1000
    kwh_str = _rust_f64_str(payload["kwh"])
    canonical = f"{key.meter_id}:{kwh_str}:{ts_ms}"

    sig_bytes = base58.b58decode(payload["signature"])
    # raises InvalidSignature if the sim signed anything other than `canonical`.
    key.public_key.verify(sig_bytes, canonical.encode())


def test_timestamp_subsecond_dropped():
    key = MeterKey("METER-001")
    reading = _reading(
        timestamp=datetime(2026, 6, 6, 8, 30, 45, 123456, tzinfo=timezone.utc)
    )
    payload = _build_obis_payload(reading, key, None)
    # Signed against second-floored millis; verify the contract still holds.
    ts_ms = int(reading.timestamp.replace(microsecond=0).timestamp()) * 1000
    canonical = f"{key.meter_id}:{_rust_f64_str(payload['kwh'])}:{ts_ms}"
    key.public_key.verify(base58.b58decode(payload["signature"]), canonical.encode())
    assert payload["timestamp"].endswith("+00:00")
    assert "45" in payload["timestamp"]  # second kept


def test_pubkey_hex_is_64_chars():
    key = MeterKey("METER-001")
    hex_pub = key.public_key_hex()
    assert len(hex_pub) == 64
    bytes.fromhex(hex_pub)  # valid hex


# --- ingest envelope --------------------------------------------------------


def test_send_reading_posts_dlms_envelope():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    async def run():
        client = OracleBridgeClient("http://bridge:4010")
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            await client.send_reading(_reading(), MeterKey("METER-001"))
        finally:
            await client.close()

    asyncio.run(run())

    assert captured["url"] == "http://bridge:4010/v1/private-network/ingest"
    body = captured["json"]
    assert body["protocol"] == "dlms"
    assert body["device_id"] == "METER-001"
    assert body["payload"][OBIS_ACTIVE_IMPORT] == 10000.0


def test_send_reading_retries_on_5xx_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    async def run():
        client = OracleBridgeClient("http://bridge:4010", max_retries=1)
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            resp = await client.send_reading(_reading(), MeterKey("METER-001"))
            return resp.status_code
        finally:
            await client.close()

    assert asyncio.run(run()) == 200
    assert calls["n"] == 2  # one retry


def test_send_reading_does_not_retry_4xx():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(403, json={"error": "bad sig"})

    async def run():
        client = OracleBridgeClient("http://bridge:4010", max_retries=2)
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            await client.send_reading(_reading(), MeterKey("METER-001"))
        finally:
            await client.close()

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(run())
    assert calls["n"] == 1  # 4xx not retried
