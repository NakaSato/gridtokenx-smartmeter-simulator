"""Oracle Bridge DLMS/COSEM (IEC 62056) REST transport.

Ships :class:`EnergyReading`s to the parent ``gridtokenx-oracle-bridge`` over its
IoT HTTP gateway (default ``:4010``) using the *DLMS/COSEM application data model*:
readings are encoded as an OBIS-code keyed JSON object and POSTed to
``/v1/private-network/ingest`` with ``protocol = "dlms"``. The bridge's
``DlmsStack`` (``src/protocol/stacks/dlms.rs``) maps the OBIS codes back to energy
metrics, and ``verify_rest_signature`` (``src/handlers.rs``) authenticates each
reading against the device's Ed25519 public key held in Redis.

This is the plaintext COSEM-object path — distinct from the encrypted binary
"Secure DLMS-lite v4" framing in ``src/rust_sim`` / the Oracle Bridge gRPC
``BulkRawIngest`` endpoint. No Rust extension or protobuf stubs are required here.

Signature contract (must byte-match the bridge):
    canonical = f"{device_id}:{kwh}:{timestamp_ms}"
where ``kwh`` is the bridge's ``f64::to_string()`` of the JSON ``kwh`` field and
``timestamp_ms`` is the RFC-3339 ``timestamp`` field in epoch milliseconds. The
bridge falls back to a second-scale timestamp, so sub-second precision is dropped
on both sides to keep the strings identical.
"""

from __future__ import annotations

import hashlib
import logging
import socket
from datetime import timezone
from typing import Iterable, Optional
from urllib.parse import urlparse

import base58
import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from smart_meter_simulator.models.reading import EnergyReading

logger = logging.getLogger(__name__)

# IEC 62056 OBIS codes consumed by the Oracle Bridge DlmsStack.map_payload.
OBIS_ACTIVE_IMPORT = "1.1.1.8.0.255"  # active energy import (consumed), Wh
OBIS_ACTIVE_EXPORT = "1.1.2.8.0.255"  # active energy export (generated), Wh
OBIS_VOLTAGE_L1 = "1.1.32.7.0.255"  # voltage L1, V
OBIS_CURRENT_L1 = "1.1.31.7.0.255"  # current L1, A
OBIS_FREQUENCY = "1.1.14.7.0.255"  # frequency, Hz


def _rust_f64_str(x: float) -> str:
    """Emulate Rust's ``f64::to_string()`` for the signature canonical string.

    Rust renders the shortest round-tripping decimal (like Python's ``repr``) but
    drops the fractional part of integral values (``1.0`` -> ``"1"``), whereas
    Python keeps it (``"1.0"``). Reconcile only that case; both runtimes agree on
    the shortest representation for the kWh magnitudes the simulator produces.
    """
    if x == int(x) and abs(x) < 1e16:
        return str(int(x))
    return repr(x)


class MeterKey:
    """Per-meter Ed25519 identity used to sign telemetry.

    The keypair is derived deterministically from ``meter_id`` (+ optional
    ``secret``) so it is stable across process restarts — the public key
    registered in Redis stays valid without persisting key material.
    """

    def __init__(self, meter_id: str, secret: str = "gridtokenx-sim"):
        seed = hashlib.sha256(f"{secret}:{meter_id}".encode()).digest()
        self._private = Ed25519PrivateKey.from_private_bytes(seed)
        self._seed = seed
        self.meter_id = meter_id

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self._private.public_key()

    def ed25519_seed_bytes(self) -> bytes:
        """32-byte Ed25519 signing seed.

        This is the exact value the Rust ``generate_utt_v4_batch`` framing codec
        expects per meter (``SigningKey::from_bytes`` takes the 32-byte seed), so
        signatures produced in Rust verify against :meth:`public_key_hex`.
        """
        return self._seed

    def aes_device_key(self) -> bytes:
        """Deterministic 32-byte AES-256-GCM device key for binary v4 framing.

        Derived from the meter id so it is stable across restarts and can be
        seeded into the Oracle Bridge device registry (see
        :func:`register_device_aes_keys_redis`) without persisting key material.
        Distinct domain separation (``aes:`` prefix) keeps it independent of the
        Ed25519 seed.
        """
        return hashlib.sha256(f"aes:{self.meter_id}".encode()).digest()

    def public_key_hex(self) -> str:
        """32-byte raw public key as 64-char hex (Redis registry format)."""
        raw = self.public_key.public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        return raw.hex()

    def sign_base58(self, message: str) -> str:
        """Sign ``message`` (UTF-8) and return the base58 signature."""
        sig = self._private.sign(message.encode())
        return base58.b58encode(sig).decode()


def _build_obis_payload(
    reading: EnergyReading,
    key: MeterKey,
    zone_code: Optional[str],
) -> dict:
    """Encode a reading as the DLMS/COSEM OBIS JSON the bridge expects, signed."""
    ts = reading.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    # Drop sub-second precision so the signed timestamp_ms matches the bridge's
    # RFC-3339 -> millis parse exactly (it also tries second-scale on fallback).
    ts = ts.astimezone(timezone.utc).replace(microsecond=0)
    timestamp_iso = ts.isoformat()
    timestamp_ms = int(ts.timestamp()) * 1000

    net_kwh = round(reading.energy_generated - reading.energy_consumed, 6)
    kwh_str = _rust_f64_str(net_kwh)

    canonical = f"{key.meter_id}:{kwh_str}:{timestamp_ms}"
    signature = key.sign_base58(canonical)

    payload = {
        # OBIS-coded measurements (energy in Wh, as the DlmsStack expects).
        OBIS_ACTIVE_IMPORT: round(reading.energy_consumed * 1000.0, 3),
        OBIS_ACTIVE_EXPORT: round(reading.energy_generated * 1000.0, 3),
        # Convenience / signature fields read directly by the REST handler.
        "kwh": net_kwh,
        "energy_generated": round(reading.energy_generated, 6),
        "energy_consumed": round(reading.energy_consumed, 6),
        "timestamp": timestamp_iso,
        "signature": signature,
    }
    if reading.voltage is not None:
        payload[OBIS_VOLTAGE_L1] = round(reading.voltage, 2)
    if reading.current is not None:
        payload[OBIS_CURRENT_L1] = round(reading.current, 3)
    if reading.frequency is not None:
        payload[OBIS_FREQUENCY] = round(reading.frequency, 3)
    if zone_code:
        payload["zone_code"] = zone_code
    return payload


class OracleBridgeClient:
    """Async client for the Oracle Bridge DLMS/COSEM REST ingestion endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:4010",
        *,
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.ingest_url = f"{self.base_url}/v1/private-network/ingest"
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "OracleBridgeClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def send_reading(
        self,
        reading: EnergyReading,
        key: MeterKey,
        *,
        zone_code: Optional[str] = None,
    ) -> httpx.Response:
        """POST one reading as a signed DLMS/COSEM OBIS frame. Raises on HTTP error."""
        body = {
            "protocol": "dlms",
            "device_id": key.meter_id,
            "payload": _build_obis_payload(reading, key, zone_code),
        }
        resp = await self._client.post(self.ingest_url, json=body)
        resp.raise_for_status()
        return resp


def _seed_redis(redis_url: str, pairs: list[tuple[str, str]]) -> int:
    """Pipeline ``SET key value`` for each pair over a raw RESP socket.

    Avoids a ``redis`` dependency. Returns the number of keys written; logs and
    returns 0 on connection failure.
    """
    if not pairs:
        return 0
    parsed = urlparse(redis_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379

    def _resp(*parts: str) -> bytes:
        out = [f"*{len(parts)}\r\n".encode()]
        for p in parts:
            b = p.encode()
            out.append(f"${len(b)}\r\n".encode() + b + b"\r\n")
        return b"".join(out)

    try:
        with socket.create_connection((host, port), timeout=5.0) as sock:
            if parsed.password:
                sock.sendall(_resp("AUTH", parsed.password))
            buf = bytearray()
            for key, value in pairs:
                buf += _resp("SET", key, value)
            sock.sendall(bytes(buf))
            # Drain replies so server-side writes flush before we close.
            sock.settimeout(5.0)
            expected = len(pairs) + (1 if parsed.password else 0)
            data = b""
            while data.count(b"\r\n") < expected:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
        return len(pairs)
    except OSError as exc:
        logger.warning("Redis seed skipped (%s).", exc)
        return 0


def register_pubkeys_redis(redis_url: str, keys: Iterable[MeterKey]) -> int:
    """Register meter Ed25519 public keys in the bridge's device registry.

    Writes ``gridtokenx:devices:{meter_id}:pubkey = <hex>`` for each meter so
    ``verify_rest_signature`` can authenticate telemetry. Returns count written.
    """
    keys = list(keys)
    pairs = [
        (f"gridtokenx:devices:{k.meter_id}:pubkey", k.public_key_hex()) for k in keys
    ]
    n = _seed_redis(redis_url, pairs)
    if n:
        logger.info("Registered %d meter public keys in Redis", n)
    return n


def register_device_aes_keys_redis(redis_url: str, keys: Iterable[MeterKey]) -> int:
    """Register meter AES-256-GCM device keys in the bridge registry.

    The binary Protocol-v4 path (:func:`OracleGrpcClient.bulk_raw_ingest`)
    encrypts each frame with the per-meter key from :meth:`MeterKey.aes_device_key`.
    The bridge must hold the same key (hex-encoded) to decrypt; writes
    ``gridtokenx:devices:{meter_id}:aeskey = <hex>``. Returns count written.
    """
    keys = list(keys)
    pairs = [
        (f"gridtokenx:devices:{k.meter_id}:aeskey", k.aes_device_key().hex())
        for k in keys
    ]
    n = _seed_redis(redis_url, pairs)
    if n:
        logger.info("Registered %d meter AES device keys in Redis", n)
    return n


def register_meter_owners_redis(redis_url: str, ownership: dict[str, str]) -> int:
    """Seed the Oracle Bridge meter→user owner map used for attribution/settlement.

    Writes ``gridtokenx:meters:{serial}:user_id = <user_id>`` for each entry of
    ``ownership`` (``{meter_serial: user_id}``). The Oracle Bridge ``MeterRegistry``
    reads this key (``resolve_user_id``); without it telemetry resolves to
    ``Uuid::nil`` and settlement is skipped. No service writes this key, so the
    onboarding step must. Returns count written.
    """
    pairs = [
        (f"gridtokenx:meters:{serial}:user_id", user_id)
        for serial, user_id in ownership.items()
    ]
    n = _seed_redis(redis_url, pairs)
    if n:
        logger.info("Seeded %d meter→user owner mappings in Redis", n)
    return n
