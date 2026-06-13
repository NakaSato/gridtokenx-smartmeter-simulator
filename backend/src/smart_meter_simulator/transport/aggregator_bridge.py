"""Aggregator Bridge DLMS/COSEM (IEC 62056) REST transport.

Ships :class:`EnergyReading`s to the parent ``gridtokenx-aggregator-bridge`` over its
IoT HTTP gateway (default ``:4010``) using the *DLMS/COSEM application data model*:
readings are encoded as an OBIS-code keyed JSON object and POSTed to
``/v1/private-network/ingest`` with ``protocol = "dlms"``. The bridge's
``DlmsStack`` (``src/protocol/stacks/dlms.rs``) maps the OBIS codes back to energy
metrics, and ``verify_rest_signature`` (``src/handlers.rs``) authenticates each
reading against the device's Ed25519 public key held in Redis.

This is the sole egress path: a plaintext, signed COSEM-object frame per reading.
No Rust extension, gRPC channel, or protobuf stubs are required.

Signature contract (must byte-match the bridge):
    canonical = f"{device_id}:{kwh}:{timestamp_ms}"
where ``kwh`` is the bridge's ``f64::to_string()`` of the JSON ``kwh`` field and
``timestamp_ms`` is the RFC-3339 ``timestamp`` field in epoch milliseconds. The
bridge falls back to a second-scale timestamp, so sub-second precision is dropped
on both sides to keep the strings identical.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import socket
from datetime import timezone
from typing import Iterable, Mapping, Optional
from urllib.parse import urlparse

import base58
import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from smart_meter_simulator.core.metrics import AGGREGATOR_EMIT_FAILED
from smart_meter_simulator.models.reading import EnergyReading

logger = logging.getLogger(__name__)

# IEC 62056 OBIS codes consumed by the Aggregator Bridge DlmsStack.map_payload.
OBIS_ACTIVE_IMPORT = "1.1.1.8.0.255"  # active energy import (consumed), Wh
OBIS_ACTIVE_EXPORT = "1.1.2.8.0.255"  # active energy export (generated), Wh
OBIS_REACTIVE_IMPORT = "1.1.3.8.0.255"  # reactive energy import Q+, varh
OBIS_REACTIVE_EXPORT = "1.1.4.8.0.255"  # reactive energy export Q-, varh
OBIS_VOLTAGE_L1 = "1.1.32.7.0.255"  # voltage L1, V
OBIS_CURRENT_L1 = "1.1.31.7.0.255"  # current L1, A
OBIS_FREQUENCY = "1.1.14.7.0.255"  # frequency, Hz
OBIS_POWER_FACTOR = "1.1.13.7.0.255"  # power factor, ratio


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
        """32-byte Ed25519 signing seed backing this meter's keypair."""
        return self._seed

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
    if reading.power_factor is not None:
        payload[OBIS_POWER_FACTOR] = round(reading.power_factor, 4)
    if reading.reactive_power_kvar is not None:
        # Bridge expects reactive *energy* in varh (it divides by 1000 -> kvarh).
        # Convert instantaneous kvar over the reading interval: kvar * h * 1000.
        interval_h = reading.interval_seconds / 3600.0
        varh = reading.reactive_power_kvar * interval_h * 1000.0
        if varh >= 0:
            payload[OBIS_REACTIVE_IMPORT] = round(varh, 3)
        else:
            payload[OBIS_REACTIVE_EXPORT] = round(-varh, 3)
    if zone_code:
        payload["zone_code"] = zone_code
    return payload


class AggregatorBridgeClient:
    """Async client for the Aggregator Bridge DLMS/COSEM REST ingestion endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:4010",
        *,
        api_key: str = "",
        timeout: float = 10.0,
        max_retries: int = 1,
    ):
        self.base_url = base_url.rstrip("/")
        self.ingest_url = f"{self.base_url}/v1/private-network/ingest"
        self.health_url = f"{self.base_url}/health"
        self._max_retries = max(0, max_retries)
        # The bridge's api_key_auth middleware requires X-API-KEY on ingest; send
        # it on every request. /health stays open but the header is harmless there.
        headers = {"X-API-KEY": api_key} if api_key else None
        self._client = httpx.AsyncClient(timeout=timeout, headers=headers)

    async def __aenter__(self) -> "AggregatorBridgeClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def health(self) -> bool:
        """Return True if the bridge ``/health`` endpoint is reachable and OK."""
        try:
            resp = await self._client.get(self.health_url)
            return resp.status_code < 500
        except httpx.HTTPError:
            return False

    async def send_reading(
        self,
        reading: EnergyReading,
        key: MeterKey,
        *,
        zone_code: Optional[str] = None,
    ) -> httpx.Response:
        """POST one reading as a signed DLMS/COSEM OBIS frame. Raises on HTTP error.

        Retries up to ``max_retries`` times on transport errors and 5xx responses
        with jittered backoff. 4xx responses (signature/contract rejections) are
        not retried — a retry cannot fix them.

        The backoff jitter uses the unseeded global ``random`` on purpose: it is
        network retry timing, not telemetry, and per-meter de-synchronisation is
        the point. It does not affect reading determinism (RANDOM_SEED).
        """
        body = {
            "protocol": "dlms",
            "device_id": key.meter_id,
            "payload": _build_obis_payload(reading, key, zone_code),
        }
        attempt = 0
        while True:
            try:
                resp = await self._client.post(self.ingest_url, json=body)
                if resp.status_code >= 500 and attempt < self._max_retries:
                    attempt += 1
                    await asyncio.sleep(0.05 + random.random() * 0.1)
                    continue
                resp.raise_for_status()
                return resp
            except httpx.TransportError:
                if attempt >= self._max_retries:
                    raise
                attempt += 1
                await asyncio.sleep(0.05 + random.random() * 0.1)


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


def register_meter_owners_redis(redis_url: str, ownership: dict[str, str]) -> int:
    """Seed the Aggregator Bridge meter→user owner map used for attribution/settlement.

    Writes ``gridtokenx:meters:{serial}:user_id = <user_id>`` for each entry of
    ``ownership`` (``{meter_serial: user_id}``). The Aggregator Bridge ``MeterRegistry``
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


def read_meter_owners_redis(redis_url: str, serials: Iterable[str]) -> dict[str, str]:
    """Read back the bridge owner map for ``serials`` from Redis.

    Inverse of :func:`register_meter_owners_redis`: pipelines ``GET
    gridtokenx:meters:{serial}:user_id`` over a raw RESP socket and returns
    ``{serial: user_id}`` for the keys that exist. Lets a re-run recover owners
    seeded by a prior run (the binding persists in the bridge's registry even
    when the sim can no longer re-derive it — e.g. an IAM account that exists but
    is not yet email-verified, so login can't return its user_id). Missing keys
    are omitted; logs and returns ``{}`` on connection failure. No ``redis`` dep.
    """
    serials = list(dict.fromkeys(serials))
    if not serials:
        return {}
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
            sock.settimeout(5.0)
            if parsed.password:
                sock.sendall(_resp("AUTH", parsed.password))
            buf = bytearray()
            for serial in serials:
                buf += _resp("GET", f"gridtokenx:meters:{serial}:user_id")
            sock.sendall(bytes(buf))
            expected = len(serials) + (1 if parsed.password else 0)
            data = bytearray()
            values = _read_resp_replies(sock, data, expected)
    except OSError as exc:
        logger.warning("Redis owner read-back skipped (%s).", exc)
        return {}

    # Drop the leading AUTH +OK reply, if any, then zip GET replies to serials.
    if parsed.password and values:
        values = values[1:]
    out: dict[str, str] = {}
    for serial, value in zip(serials, values):
        if value is not None:
            out[serial] = value
    return out


def _read_resp_replies(sock, data: bytearray, expected: int) -> list[Optional[str]]:
    """Parse exactly ``expected`` top-level RESP replies, recv'ing as needed.

    Handles the reply types Redis returns for AUTH/GET: simple string (``+``),
    error (``-``, surfaced as ``None``), integer (``:``), and bulk string
    (``$``, with ``$-1`` → ``None``). Returns one entry per reply in order.
    """
    replies: list[Optional[str]] = []
    pos = 0

    def _need(upto: int) -> None:
        while len(data) < upto:
            chunk = sock.recv(4096)
            if not chunk:
                raise OSError("connection closed mid-reply")
            data.extend(chunk)

    def _line(start: int) -> tuple[bytes, int]:
        idx = data.find(b"\r\n", start)
        while idx == -1:
            chunk = sock.recv(4096)
            if not chunk:
                raise OSError("connection closed mid-reply")
            data.extend(chunk)
            idx = data.find(b"\r\n", start)
        return bytes(data[start:idx]), idx + 2

    while len(replies) < expected:
        line, pos = _line(pos)
        kind, rest = line[:1], line[1:]
        if kind in (b"+", b"-", b":"):
            replies.append(None if kind == b"-" else rest.decode())
        elif kind == b"$":
            length = int(rest)
            if length == -1:
                replies.append(None)
            else:
                _need(pos + length + 2)
                replies.append(data[pos : pos + length].decode())
                pos += length + 2
        else:  # unexpected type — treat as nil to stay in sync
            replies.append(None)
    return replies


class AggregatorBridgeEmitter:
    """Non-blocking per-tick emitter for the DLMS/COSEM REST ingest path.

    The standard-protocol counterpart wired into the simulation loop: each tick's
    readings are POSTed to the Aggregator Bridge as signed OBIS frames, one HTTP call
    per meter, all fired concurrently with :func:`asyncio.gather`. The whole batch
    runs as a single background task; if the previous batch is still in flight
    (slow/hung bridge) the current tick is dropped rather than queued — back-pressure
    that keeps the loop real-time.

    Per-meter :class:`MeterKey`\\ s are cached and rebuilt only when the meter
    population changes, and their Ed25519 public keys are (re)registered in the
    bridge's Redis device registry on :meth:`start` so ``verify_rest_signature``
    can authenticate telemetry. The emitter degrades gracefully: a transport error
    is logged and never propagates into the tick.
    """

    def __init__(
        self,
        base_url: str,
        *,
        redis_url: str,
        api_key: str = "",
        emit_every: int = 1,
        secret: str = "gridtokenx-sim",
        timeout: float = 10.0,
        ownership: Optional[Mapping[str, str]] = None,
    ):
        self._client = AggregatorBridgeClient(base_url, api_key=api_key, timeout=timeout)
        self._redis_url = redis_url
        self._emit_every = max(1, emit_every)
        self._secret = secret
        self._ownership: dict[str, str] = dict(ownership or {})
        self._keys: dict[str, MeterKey] = {}
        self._key_ids: frozenset[str] = frozenset()
        self._inflight: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._started = False

    def add_ownership(self, ownership: Mapping[str, str]) -> None:
        """Merge extra meter->owner entries (e.g. resolved via IAM onboarding).

        Overrides any existing entries for the same meter and invalidates the
        cached key-id set so the next emit re-seeds the bridge owner map. Call
        before :meth:`start`.
        """
        if not ownership:
            return
        self._ownership.update(ownership)
        self._key_ids = frozenset()  # force owner/pubkey re-seed on next emit

    def start(self) -> None:
        """Mark active, register current keys, and probe the bridge.

        Schedules a non-blocking ``/health`` probe (logs a warning if the bridge
        is unreachable) when called inside a running event loop. Call once when
        the engine starts.
        """
        self._started = True
        logger.info("Aggregator DLMS emitter active -> %s", self._client.ingest_url)
        try:
            asyncio.get_running_loop().create_task(self._probe_health())
        except RuntimeError:
            pass  # no running loop (e.g. unit test) — skip the probe

    async def _probe_health(self) -> None:
        if not await self._client.health():
            logger.warning(
                "Aggregator Bridge health check failed (%s) — readings may be dropped",
                self._client.health_url,
            )

    def _keys_for(self, readings) -> dict[str, MeterKey]:
        ids = frozenset(r.meter_id for r in readings)
        if ids != self._key_ids:
            self._keys = {mid: MeterKey(mid, secret=self._secret) for mid in ids}
            self._key_ids = ids
            register_pubkeys_redis(self._redis_url, self._keys.values())
            owners = {
                mid: self._ownership[mid] for mid in ids if mid in self._ownership
            }
            if owners:
                register_meter_owners_redis(self._redis_url, owners)
        return self._keys

    def emit(self, readings) -> None:
        """Schedule a background DLMS batch send for this tick's readings.

        Synchronous and non-blocking: returns immediately. Drops the tick if a
        prior batch is still running or the emitter is not started.
        """
        if not self._started or not readings:
            return
        self._tick_count += 1
        if self._tick_count % self._emit_every != 0:
            return
        if self._inflight is not None and not self._inflight.done():
            logger.debug("Aggregator DLMS emit skipped: previous batch still in flight")
            return

        keys = self._keys_for(readings)
        snapshot = list(readings)
        self._inflight = asyncio.create_task(self._send(snapshot, keys))

    async def _send(self, readings, keys) -> None:
        try:
            results = await asyncio.gather(
                *(self._client.send_reading(r, keys[r.meter_id]) for r in readings),
                return_exceptions=True,
            )
            failures = [
                (readings[i].meter_id, r)
                for i, r in enumerate(results)
                if isinstance(r, Exception)
            ]
            if failures:
                AGGREGATOR_EMIT_FAILED.inc(len(failures))
                # Name the offending meter(s) and the exception type/message so a
                # persistent straggler is diagnosable from logs alone (the batch
                # otherwise swallows per-reading errors into a bare count).
                detail = "; ".join(
                    f"{mid}: {type(exc).__name__}: {exc}" for mid, exc in failures[:5]
                )
                logger.warning(
                    "Aggregator DLMS batch: %d/%d readings failed — %s",
                    len(failures),
                    len(results),
                    detail,
                )
        except Exception:
            logger.exception("Aggregator DLMS batch emit failed")

    async def close(self) -> None:
        """Cancel any in-flight batch and close the HTTP client."""
        if self._inflight is not None and not self._inflight.done():
            self._inflight.cancel()
        await self._client.close()
        self._started = False
