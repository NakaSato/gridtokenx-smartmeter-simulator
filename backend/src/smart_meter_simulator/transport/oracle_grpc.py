"""Oracle Bridge binary Protocol-v4 (UTT-S+) gRPC transport.

The high-throughput counterpart to the plaintext DLMS/COSEM REST path in
:mod:`smart_meter_simulator.transport.oracle_bridge`. Instead of one signed JSON
POST per reading, this path frames a whole batch of readings into encrypted
binary packets with the Rust ``gridtokenx_sim`` extension and ships them in a
single ``OracleService.BulkRawIngest`` gRPC call.

Frame layout (produced by ``gridtokenx_sim.generate_utt_v4_batch``), per meter::

    [frame_len: u8][frame][signature: 64 bytes]
    frame = [version][length][manuf_id(3)][ldn(8)][timestamp(8)][ciphertext][crc32(4)]

``BulkRawRequest.payload`` is the concatenation of every meter's packed buffer and
``meter_count`` is the number of frames — exactly what the bridge's
``BulkRawIngest`` handler splits back apart.

The Rust extension is an **optional accelerator**: it is only imported lazily when
a bulk send is attempted. If the compiled ``gridtokenx_sim`` module is absent (no
``.so`` built), :class:`OracleGrpcClient` raises a clear :class:`RustExtensionMissing`
rather than failing at import time, so the rest of the simulator keeps working.

Key material is derived deterministically per meter by
:class:`~smart_meter_simulator.transport.oracle_bridge.MeterKey`
(Ed25519 seed + AES-256 device key); seed the bridge registry with
``register_pubkeys_redis`` + ``register_device_aes_keys_redis`` so it can verify
and decrypt.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timezone
from typing import Iterable, Optional, Sequence

import grpc

from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.transport.grpc_gen import oracle_pb2, oracle_pb2_grpc
from smart_meter_simulator.transport.oracle_bridge import MeterKey

logger = logging.getLogger(__name__)


class RustExtensionMissing(RuntimeError):
    """Raised when the ``gridtokenx_sim`` binary extension is not importable.

    The binary v4 framing path requires the compiled Rust crate. Build it with
    ``cargo build --release`` in ``src/rust_sim`` (then copy the lib to
    ``src/gridtokenx_sim.so``) or ``maturin develop`` from ``src/rust_sim``.
    """


def _load_framer():
    """Import the Rust framing entry points, or raise :class:`RustExtensionMissing`."""
    try:
        from gridtokenx_sim import MeterFrameInput, generate_utt_v4_batch
    except ImportError as exc:  # pragma: no cover - exercised via the missing-ext path
        raise RustExtensionMissing(
            "gridtokenx_sim extension not built; binary v4 ingest unavailable. "
            "Build it in src/rust_sim (cargo build --release) and copy the lib to "
            "src/gridtokenx_sim.so."
        ) from exc
    return MeterFrameInput, generate_utt_v4_batch


def _timestamp_sec(reading: EnergyReading) -> int:
    """Epoch-seconds for a reading, normalising naive datetimes to UTC."""
    ts = reading.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return int(ts.timestamp())


def build_bulk_payload(
    readings: Sequence[EnergyReading],
    keys: dict[str, MeterKey],
) -> tuple[bytes, int]:
    """Frame ``readings`` into a single ``BulkRawRequest.payload`` blob.

    Returns ``(payload, meter_count)``. All readings in a batch share one
    timestamp field (the first reading's), matching the Rust batch signature
    which takes a single ``timestamp_sec`` for the whole batch. Each reading
    carries its own ``sequence_number`` and per-meter key.

    Raises :class:`RustExtensionMissing` if the Rust extension is unavailable and
    :class:`KeyError` if a reading has no key in ``keys``.
    """
    MeterFrameInput, generate_utt_v4_batch = _load_framer()
    if not readings:
        return b"", 0

    frame_inputs = []
    ed25519_keys: list[bytes] = []
    aes_keys: list[bytes] = []
    sequences: list[int] = []

    for reading in readings:
        key = keys[reading.meter_id]
        surplus = round(reading.energy_generated - reading.energy_consumed, 6)
        frame_inputs.append(
            MeterFrameInput(
                meter_id=reading.meter_id,
                energy_import_kwh=reading.energy_consumed,
                energy_export_kwh=reading.energy_generated,
                surplus_kwh=surplus,
                voltage=reading.voltage if reading.voltage is not None else 230.0,
                current=reading.current if reading.current is not None else 0.0,
            )
        )
        ed25519_keys.append(key.ed25519_seed_bytes())
        aes_keys.append(key.aes_device_key())
        sequences.append(int(reading.sequence_number))

    timestamp_sec = _timestamp_sec(readings[0])
    frames = generate_utt_v4_batch(
        frame_inputs, ed25519_keys, aes_keys, timestamp_sec, sequences
    )
    payload = b"".join(bytes(frame) for frame in frames)
    return payload, len(frames)


class OracleGrpcClient:
    """Async client for the Oracle Bridge ``BulkRawIngest`` gRPC endpoint."""

    def __init__(self, target: str = "localhost:50051", *, timeout: float = 10.0):
        self.target = target
        self.timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[oracle_pb2_grpc.OracleServiceStub] = None

    def connect(self) -> "OracleGrpcClient":
        """Open the gRPC channel + stub. Idempotent; safe to call once at start."""
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self.target)
            self._stub = oracle_pb2_grpc.OracleServiceStub(self._channel)
        return self

    async def __aenter__(self) -> "OracleGrpcClient":
        return self.connect()

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def bulk_raw_ingest(
        self,
        readings: Sequence[EnergyReading],
        keys: dict[str, MeterKey],
    ) -> oracle_pb2.BulkRawResponse:
        """Frame and ship a batch of readings in one ``BulkRawIngest`` call.

        Raises :class:`RustExtensionMissing` if the framing extension is absent
        and ``RuntimeError`` if the client is used outside its async context.
        """
        if self._stub is None:
            raise RuntimeError(
                "OracleGrpcClient must be used as an async context manager"
            )

        payload, meter_count = build_bulk_payload(readings, keys)
        request = oracle_pb2.BulkRawRequest(payload=payload, meter_count=meter_count)
        response = await self._stub.BulkRawIngest(request, timeout=self.timeout)
        logger.info(
            "BulkRawIngest: %d meters -> processed=%d status=%s",
            meter_count,
            response.processed_count,
            response.status,
        )
        return response


def build_meter_keys(
    meter_ids: Iterable[str], secret: str = "gridtokenx-sim"
) -> dict[str, MeterKey]:
    """Build the ``{meter_id: MeterKey}`` map the bulk path needs from meter ids."""
    return {mid: MeterKey(mid, secret=secret) for mid in meter_ids}


class OracleGrpcEmitter:
    """Non-blocking per-tick emitter for the binary v4 ``BulkRawIngest`` path.

    Owns one long-lived gRPC channel and ships each tick's readings without
    blocking the simulation loop: a send runs as a background task and, if the
    previous send is still in flight (slow/hung bridge), the current tick is
    dropped rather than queued — back-pressure that keeps the loop real-time.

    Per-meter :class:`MeterKey`\\ s are cached and rebuilt only when the meter
    population changes. The emitter degrades gracefully: a missing Rust extension
    or a transport error is logged once and never propagates into the tick.
    """

    def __init__(
        self,
        target: str,
        *,
        emit_every: int = 1,
        secret: str = "gridtokenx-sim",
        timeout: float = 10.0,
    ):
        self._client = OracleGrpcClient(target, timeout=timeout)
        self._emit_every = max(1, emit_every)
        self._secret = secret
        self._keys: dict[str, MeterKey] = {}
        self._key_ids: frozenset[str] = frozenset()
        self._inflight: Optional["object"] = None  # asyncio.Task
        self._tick_count = 0
        self._ext_missing_logged = False
        self._started = False

    def start(self) -> None:
        """Open the channel. Call once when the engine starts."""
        self._client.connect()
        self._started = True
        logger.info("Oracle gRPC emitter active -> %s", self._client.target)

    def _keys_for(self, readings) -> dict[str, MeterKey]:
        ids = frozenset(r.meter_id for r in readings)
        if ids != self._key_ids:
            self._keys = build_meter_keys(ids, secret=self._secret)
            self._key_ids = ids
        return self._keys

    def emit(self, readings) -> None:
        """Schedule a background bulk send for this tick's readings.

        Synchronous and non-blocking: returns immediately. Drops the tick if a
        prior send is still running or the emitter is not started.
        """
        if not self._started or not readings:
            return
        self._tick_count += 1
        if self._tick_count % self._emit_every != 0:
            return
        if self._inflight is not None and not self._inflight.done():
            logger.debug("Oracle gRPC emit skipped: previous send still in flight")
            return

        keys = self._keys_for(readings)
        snapshot = list(readings)
        self._inflight = asyncio.create_task(self._send(snapshot, keys))

    async def _send(self, readings, keys) -> None:
        try:
            await self._client.bulk_raw_ingest(readings, keys)
        except RustExtensionMissing:
            if not self._ext_missing_logged:
                logger.warning(
                    "Oracle gRPC emit disabled: gridtokenx_sim extension not built"
                )
                self._ext_missing_logged = True
        except Exception:
            logger.exception("Oracle gRPC bulk emit failed")

    async def close(self) -> None:
        """Cancel any in-flight send and close the channel."""
        if self._inflight is not None and not self._inflight.done():
            self._inflight.cancel()
        await self._client.close()
        self._started = False
