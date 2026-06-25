"""Contract tests for the Aggregator Bridge DLMS/COSEM REST egress.

Pin the wire contract the parent ``gridtokenx-aggregator-bridge`` parses:
- the OBIS-coded JSON payload (``DlmsStack.map_payload``),
- the ``{device_id}:{kwh}:{timestamp_ms}`` Ed25519 signature canonical string
  (``verify_rest_signature`` in ``src/handlers.rs``),
- the ``{protocol, device_id, payload}`` ingest envelope.

Pure unit tests — no running bridge, no Redis. The mirrored Wh<->kWh constants
match ``dlms.rs``'s own test (10000 Wh import -> 10 kWh).
"""

from __future__ import annotations

import asyncio
import base64
import json
import ssl
from datetime import datetime, timezone

import base58
import httpx
import pytest

from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.transport.aggregator_bridge import (
    OBIS_ACTIVE_EXPORT,
    OBIS_ACTIVE_EXPORT_RATE1,
    OBIS_ACTIVE_EXPORT_RATE2,
    OBIS_ACTIVE_IMPORT,
    OBIS_ACTIVE_IMPORT_RATE1,
    OBIS_ACTIVE_IMPORT_RATE2,
    OBIS_ACTIVE_TARIFF,
    OBIS_CURRENT_L1,
    OBIS_DR_STATUS,
    OBIS_FREQUENCY,
    OBIS_MAX_DEMAND_IMPORT,
    OBIS_POWER_FACTOR,
    OBIS_REACTIVE_EXPORT,
    OBIS_REACTIVE_IMPORT,
    OBIS_SUM_ACTIVE_POWER,
    OBIS_VOLTAGE_L1,
    AggregatorBridgeClient,
    AggregatorBridgeEmitter,
    MeterKey,
    TouSchedule,
    _build_obis_payload,
    _encrypt_envelope,
    _rust_f64_str,
    register_enckeys_redis,
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
        7,
    )
    assert full[OBIS_VOLTAGE_L1] == 230.5
    assert full[OBIS_CURRENT_L1] == 12.0
    assert full[OBIS_FREQUENCY] == 50.01
    assert full[OBIS_POWER_FACTOR] == 0.95
    # Wire zone_code is the stringified numeric code (parent parses its suffix).
    assert full["zone_code"] == "7"


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


def test_aes_key_is_deterministic_and_per_meter():
    # HKDF off the deterministic seed: same meter -> same 32-byte key across
    # instances (stable for the bridge's Redis lookup); different meter -> different.
    assert (
        MeterKey("METER-001").aes_key_bytes() == MeterKey("METER-001").aes_key_bytes()
    )
    assert len(MeterKey("METER-001").aes_key_bytes()) == 32
    assert (
        MeterKey("METER-001").aes_key_bytes() != MeterKey("METER-002").aes_key_bytes()
    )


def test_aes_key_independent_from_signing_seed():
    # The AES key is HKDF-domain-separated from the Ed25519 signing seed, so it
    # must not equal the raw seed (a leak of one must not reveal the other).
    key = MeterKey("METER-001")
    assert key.aes_key_bytes() != key.ed25519_seed_bytes()


def test_aes_key_hex_is_64_chars():
    assert len(MeterKey("METER-001").aes_key_hex()) == 64


def test_register_enckeys_redis_wire_shape(monkeypatch):
    # Seeds gridtokenx:devices:{id}:enckey = <hex> for each meter via _seed_redis.
    captured = {}

    def fake_seed(redis_url, pairs):
        captured["url"] = redis_url
        captured["pairs"] = list(pairs)
        return len(captured["pairs"])

    import smart_meter_simulator.transport.aggregator_bridge as mod

    monkeypatch.setattr(mod, "_seed_redis", fake_seed)
    n = register_enckeys_redis("redis://x:6379", [MeterKey("M-1"), MeterKey("M-2")])
    assert n == 2
    keys = {k for k, _ in captured["pairs"]}
    assert keys == {
        "gridtokenx:devices:M-1:enckey",
        "gridtokenx:devices:M-2:enckey",
    }
    # Value is the 64-char hex AES key matching the meter's derivation.
    by_key = dict(captured["pairs"])
    assert by_key["gridtokenx:devices:M-1:enckey"] == MeterKey("M-1").aes_key_hex()


def test_pubkey_hex_is_64_chars():
    key = MeterKey("METER-001")
    hex_pub = key.public_key_hex()
    assert len(hex_pub) == 64
    bytes.fromhex(hex_pub)  # valid hex


# --- AES-256-GCM payload encryption -----------------------------------------


def test_encrypt_envelope_round_trips():
    # The envelope decrypts back to the exact OBIS dict with the right key + AAD.
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = MeterKey("METER-001")
    obis = _build_obis_payload(_reading(), key, None)
    env = _encrypt_envelope("METER-001", obis, key.aes_key_bytes(), 42)

    assert env["counter"] == 42
    nonce = base64.b64decode(env["nonce"])
    ct = base64.b64decode(env["ciphertext"])
    aad = b"METER-001:42"
    plain = AESGCM(key.aes_key_bytes()).decrypt(nonce, ct, aad)
    assert json.loads(plain) == obis


def test_encrypt_envelope_rejects_wrong_key_and_aad():
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = MeterKey("METER-001")
    obis = _build_obis_payload(_reading(), key, None)
    env = _encrypt_envelope("METER-001", obis, key.aes_key_bytes(), 7)
    nonce = base64.b64decode(env["nonce"])
    ct = base64.b64decode(env["ciphertext"])

    # Wrong meter key -> GCM auth fails.
    with pytest.raises(InvalidTag):
        AESGCM(MeterKey("METER-002").aes_key_bytes()).decrypt(nonce, ct, b"METER-001:7")
    # Tampered AAD (counter) -> GCM auth fails (binds device_id:counter).
    with pytest.raises(InvalidTag):
        AESGCM(key.aes_key_bytes()).decrypt(nonce, ct, b"METER-001:8")


def test_encrypt_envelope_includes_kid_when_set():
    key = MeterKey("METER-001")
    obis = _build_obis_payload(_reading(), key, None)
    # No kid -> Phase-2 path (bridge uses legacy key); kid present -> versioned.
    assert "kid" not in _encrypt_envelope("METER-001", obis, key.aes_key_bytes(), 1)
    env = _encrypt_envelope("METER-001", obis, key.aes_key_bytes(), 1, kid=5)
    assert env["kid"] == 5


def test_encrypt_envelope_nonce_is_random_per_call():
    key = MeterKey("METER-001")
    obis = _build_obis_payload(_reading(), key, None)
    a = _encrypt_envelope("METER-001", obis, key.aes_key_bytes(), 1)
    b = _encrypt_envelope("METER-001", obis, key.aes_key_bytes(), 1)
    assert a["nonce"] != b["nonce"]  # fresh 96-bit nonce each frame


def test_send_reading_encrypted_emits_dlms_enc_envelope():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        return httpx.Response(202, json={"ok": True})

    async def run():
        client = AggregatorBridgeClient("http://bridge:4010")
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            await client.send_reading(
                _reading(), MeterKey("METER-001"), encrypt=True, counter=99
            )
        finally:
            await client.close()

    asyncio.run(run())

    body = captured["json"]
    assert body["protocol"] == "dlms-enc"
    assert body["device_id"] == "METER-001"
    enc = body["payload"]["enc"]
    assert enc["counter"] == 99
    assert set(enc) == {"counter", "nonce", "ciphertext"}
    # Plaintext OBIS must NOT be present on the wire (confidentiality).
    assert OBIS_ACTIVE_IMPORT not in body["payload"]


def test_emitter_counter_is_monotonic_per_meter():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010", redis_url="redis://x:6379", encrypt_enabled=True
    )
    seq = [em._next_counter("M-1") for _ in range(5)]
    assert seq == sorted(seq) and len(set(seq)) == 5  # strictly increasing
    # Independent per meter.
    assert em._next_counter("M-2") > 0


# --- mTLS client cert -------------------------------------------------------


class _FakeAsyncClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @property
    def is_closed(self):
        return False


def _make_self_signed(tmp_path):
    """Write a throwaway EC cert+key pair; return (cert_path, key_path)."""
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-client")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2020, 1, 1))
        .not_valid_after(datetime.datetime(2040, 1, 1))
        .sign(key, hashes.SHA256())
    )
    crt = tmp_path / "client.crt"
    k = tmp_path / "client.key"
    crt.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    k.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return str(crt), str(k)


def test_client_cert_builds_ssl_context(monkeypatch, tmp_path):
    # httpx 0.28 dropped `cert=`; with a client cert the verify arg must be a
    # configured SSLContext (loading the client cert chain) so httpx presents it.
    import smart_meter_simulator.transport.aggregator_bridge as mod

    monkeypatch.setattr(mod.httpx, "AsyncClient", _FakeAsyncClient)
    crt, key = _make_self_signed(tmp_path)
    client = AggregatorBridgeClient("https://bridge:4010", client_cert=(crt, key))
    verify_arg = client._client.kwargs["verify"]
    assert isinstance(verify_arg, ssl.SSLContext)
    assert "cert" not in client._client.kwargs  # never pass the ignored cert=


def test_no_client_cert_keeps_plain_verify(monkeypatch):
    import smart_meter_simulator.transport.aggregator_bridge as mod

    monkeypatch.setattr(mod.httpx, "AsyncClient", _FakeAsyncClient)
    client = AggregatorBridgeClient("https://bridge:4010", verify="/ca.pem")
    assert client._client.kwargs["verify"] == "/ca.pem"  # unchanged passthrough
    assert client._make_verify() == "/ca.pem"


# --- ingest envelope --------------------------------------------------------


def test_send_reading_posts_dlms_envelope():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    async def run():
        client = AggregatorBridgeClient("http://bridge:4010")
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
        client = AggregatorBridgeClient("http://bridge:4010", max_retries=1)
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
        client = AggregatorBridgeClient("http://bridge:4010", max_retries=2)
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            await client.send_reading(_reading(), MeterKey("METER-001"))
        finally:
            await client.close()

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(run())
    assert calls["n"] == 1  # 4xx not retried


def test_reopen_recreates_client_after_close():
    """Regression: a deterministic reset does stop() -> start(), which close()s
    then re-uses the same emitter/client. Without reopen(), httpx refuses every
    subsequent request ("client has been closed") and real telemetry silently
    stops. reopen() must rebuild the closed client so sends resume."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    async def run():
        client = AggregatorBridgeClient("http://bridge:4010")
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        # First send works, then the stop() path closes the shared client.
        await client.send_reading(_reading(), MeterKey("METER-001"))
        await client.close()
        assert client._client.is_closed

        # Without reopen(), this would raise "client has been closed".
        with pytest.raises(RuntimeError):
            await client.send_reading(_reading(), MeterKey("METER-001"))

        # start() calls reopen(); rebind transport (real start() would target the
        # live bridge) and confirm sends resume on the fresh client.
        client.reopen()
        assert not client._client.is_closed
        client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        resp = await client.send_reading(_reading(), MeterKey("METER-001"))
        await client.close()
        return resp.status_code

    assert asyncio.run(run()) == 200


def test_reopen_noop_when_client_open():
    """reopen() must not replace a live client (no churn on a normal start())."""

    async def run():
        client = AggregatorBridgeClient("http://bridge:4010")
        before = client._client
        client.reopen()
        same = client._client is before
        await client.close()
        return same

    assert asyncio.run(run()) is True


# --- residential OBIS register set (TOU, max demand, DR, active power) -------

PEAK_TS = datetime(2026, 6, 8, 10, 0, 0, tzinfo=timezone.utc)  # Monday 10:00 -> peak
OFFPEAK_TS = datetime(2026, 6, 8, 23, 0, 0, tzinfo=timezone.utc)  # Monday 23:00 -> off
WEEKEND_TS = datetime(2026, 6, 6, 10, 0, 0, tzinfo=timezone.utc)  # Saturday -> off-peak


def test_tou_peak_routes_energy_to_rate1():
    key = MeterKey("METER-001")
    p = _build_obis_payload(
        _reading(timestamp=PEAK_TS, interval_seconds=900), key, None, tou=TouSchedule()
    )
    assert p[OBIS_ACTIVE_TARIFF] == 1
    # The active rate register carries the full interval energy (= the total),
    # the other rate is absent: rate1 + rate2 over time reconstructs the total.
    assert p[OBIS_ACTIVE_IMPORT_RATE1] == p[OBIS_ACTIVE_IMPORT]
    assert p[OBIS_ACTIVE_EXPORT_RATE1] == p[OBIS_ACTIVE_EXPORT]
    assert OBIS_ACTIVE_IMPORT_RATE2 not in p
    assert OBIS_ACTIVE_EXPORT_RATE2 not in p


def test_tou_offpeak_and_weekend_route_to_rate2():
    key = MeterKey("METER-001")
    for ts in (OFFPEAK_TS, WEEKEND_TS):
        p = _build_obis_payload(
            _reading(timestamp=ts, interval_seconds=900), key, None, tou=TouSchedule()
        )
        assert p[OBIS_ACTIVE_TARIFF] == 2
        assert p[OBIS_ACTIVE_IMPORT_RATE2] == p[OBIS_ACTIVE_IMPORT]
        assert OBIS_ACTIVE_IMPORT_RATE1 not in p


def test_tou_disabled_emits_no_rate_registers():
    key = MeterKey("METER-001")
    p = _build_obis_payload(
        _reading(timestamp=PEAK_TS), key, None, tou=TouSchedule(enabled=False)
    )
    assert OBIS_ACTIVE_TARIFF not in p
    assert OBIS_ACTIVE_IMPORT_RATE1 not in p and OBIS_ACTIVE_IMPORT_RATE2 not in p
    # No tou argument at all -> also no tariff registers (back-compat default).
    assert OBIS_ACTIVE_TARIFF not in _build_obis_payload(_reading(), key, None)


def test_sum_active_power_is_signed_net_demand_kw():
    key = MeterKey("METER-001")
    # cons 10 - gen 5 = 5 kWh over 0.25 h -> 20 kW (net import). Signed C=16 register.
    p = _build_obis_payload(_reading(interval_seconds=900), key, None)
    assert p[OBIS_SUM_ACTIVE_POWER] == 20.0
    # Net export -> negative power.
    p2 = _build_obis_payload(
        _reading(energy_generated=10.0, energy_consumed=2.0, interval_seconds=900),
        key,
        None,
    )
    assert p2[OBIS_SUM_ACTIVE_POWER] == -32.0


def test_dr_status_present_only_when_shed():
    key = MeterKey("METER-001")
    assert OBIS_DR_STATUS not in _build_obis_payload(_reading(), key, None)
    p = _build_obis_payload(_reading(dr_shed_kw=1.5), key, None)
    assert p[OBIS_DR_STATUS] == 1


def test_max_demand_passthrough():
    key = MeterKey("METER-001")
    assert OBIS_MAX_DEMAND_IMPORT not in _build_obis_payload(_reading(), key, None)
    p = _build_obis_payload(_reading(), key, None, max_demand_kw=42.0)
    assert p[OBIS_MAX_DEMAND_IMPORT] == 42.0


def test_emitter_rolling_max_demand_tracks_peak_import_only():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010", redis_url="redis://localhost:7010"
    )
    d1 = em._update_max_demand(
        _reading(energy_consumed=4.0, energy_generated=0.0, interval_seconds=900)
    )
    assert d1 == 16.0  # 4 kWh / 0.25 h -> 16 kW
    d2 = em._update_max_demand(
        _reading(energy_consumed=10.0, energy_generated=0.0, interval_seconds=900)
    )
    assert d2 == 40.0  # higher import -> peak rises
    # A net-export interval is negative demand and must not lower the peak.
    d3 = em._update_max_demand(
        _reading(energy_consumed=0.0, energy_generated=8.0, interval_seconds=900)
    )
    assert d3 == 40.0


@pytest.mark.asyncio
async def test_emitter_threads_zone_code_from_zones_map():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010",
        redis_url="redis://localhost:7010",
        zones={"METER-001": 3},
    )

    captured: dict[str, object] = {}

    async def _fake_send(
        reading,
        key,
        *,
        zone_code=None,
        max_demand_kw=None,
        encrypt=False,
        counter=None,
        aes_key=None,
        kid=None,
    ):
        captured["zone_code"] = zone_code
        return None

    em._client.send_reading = _fake_send  # type: ignore[assignment]

    readings = [_reading(meter_id="METER-001")]
    await em._send(readings, em._keys_for(readings))

    assert captured["zone_code"] == 3


@pytest.mark.asyncio
async def test_emitter_zone_code_none_when_meter_ungrouped():
    em = AggregatorBridgeEmitter(
        "http://bridge:4010", redis_url="redis://localhost:7010"
    )

    captured: dict[str, object] = {"zone_code": "sentinel"}

    async def _fake_send(
        reading,
        key,
        *,
        zone_code=None,
        max_demand_kw=None,
        encrypt=False,
        counter=None,
        aes_key=None,
        kid=None,
    ):
        captured["zone_code"] = zone_code
        return None

    em._client.send_reading = _fake_send  # type: ignore[assignment]

    readings = [_reading(meter_id="METER-001")]
    await em._send(readings, em._keys_for(readings))

    assert captured["zone_code"] is None


def test_signature_unchanged_by_residential_registers():
    key = MeterKey("METER-001")
    reading = _reading(
        timestamp=PEAK_TS,
        interval_seconds=900,
        voltage=230.0,
        current=6.5,
        frequency=50.0,
        power_factor=0.98,
        reactive_power_kvar=0.5,
        dr_shed_kw=1.0,
    )
    payload = _build_obis_payload(
        reading, key, 7, tou=TouSchedule(), max_demand_kw=50.0
    )
    # Full residential payload still signs only the canonical kwh:ts string.
    ts_ms = int(PEAK_TS.replace(microsecond=0).timestamp()) * 1000
    canonical = f"{key.meter_id}:{_rust_f64_str(payload['kwh'])}:{ts_ms}"
    key.public_key.verify(base58.b58decode(payload["signature"]), canonical.encode())
