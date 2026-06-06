"""Round-trip tests for the binary Protocol-v4 gRPC framing path.

Validates that ``build_bulk_payload`` (Rust ``generate_utt_v4_batch`` +
``MeterKey`` plumbing) produces frames the Oracle Bridge can split, authenticate,
and decrypt — without needing a running bridge. Skipped if the Rust extension is
not built.
"""

from __future__ import annotations

import struct
from datetime import datetime, timezone

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.transport import grpc_gen  # noqa: F401  (import smoke)
from smart_meter_simulator.transport.grpc_gen import oracle_pb2
from smart_meter_simulator.transport.oracle_grpc import (
    RustExtensionMissing,
    build_bulk_payload,
    build_meter_keys,
)

try:
    import gridtokenx_sim  # noqa: F401

    HAVE_RUST = True
except ImportError:
    HAVE_RUST = False

rust_only = pytest.mark.skipif(
    not HAVE_RUST, reason="gridtokenx_sim extension not built"
)

HEADER_LEN = 21  # version + length + manuf(3) + ldn(8) + timestamp(8)
SIG_LEN = 64
CRC_LEN = 4
MANUF = b"GXT"


def _reading(meter_id: str, gen: float, cons: float, seq: int, ts: datetime):
    return EnergyReading(
        meter_id=meter_id,
        timestamp=ts,
        energy_generated=gen,
        energy_consumed=cons,
        surplus_energy=max(gen - cons, 0.0),
        deficit_energy=max(cons - gen, 0.0),
        interval_seconds=15,
        voltage=231.5,
        current=4.2,
        sequence_number=seq,
        location="test-bus",
        meter_type="Solar_Prosumer",
        user_type="residential",
    )


def _split_frames(payload: bytes, meter_count: int) -> list[bytes]:
    """Split the concatenated [len][frame][sig 64] buffers back into packets."""
    packets = []
    offset = 0
    for _ in range(meter_count):
        frame_len = payload[offset]
        start = offset + 1
        end = start + frame_len + SIG_LEN
        packets.append(payload[offset:end])
        offset = end
    assert offset == len(payload), "payload had trailing bytes after meter_count frames"
    return packets


@rust_only
def test_bulk_payload_roundtrip_authenticates_and_decrypts():
    ts = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    ts_sec = int(ts.timestamp())
    ts_ms = ts_sec * 1000
    readings = [
        _reading("METER-001", gen=2.5, cons=1.0, seq=7, ts=ts),
        _reading("METER-002", gen=0.0, cons=3.25, seq=8, ts=ts),
    ]
    keys = build_meter_keys(r.meter_id for r in readings)

    payload, count = build_bulk_payload(readings, keys)
    assert count == len(readings)

    packets = _split_frames(payload, count)
    assert len(packets) == len(readings)

    for i, (reading, packet) in enumerate(zip(readings, packets)):
        key = keys[reading.meter_id]
        frame_len = packet[0]
        frame = packet[1 : 1 + frame_len]
        signature = packet[1 + frame_len :]
        assert len(signature) == SIG_LEN

        # --- header ---
        assert frame[0] == 0x04  # version
        assert frame[2:5] == MANUF
        header = frame[:HEADER_LEN]
        ts_in_frame = struct.unpack(">Q", frame[13:21])[0]
        assert ts_in_frame == ts_sec

        ciphertext = frame[HEADER_LEN:-CRC_LEN]

        # --- AES-256-GCM decrypt (header is AAD, nonce = manuf+ts+0x04) ---
        nonce = MANUF + struct.pack(">Q", ts_sec) + bytes([0x04])
        assert len(nonce) == 12
        aes = AESGCM(key.aes_device_key())
        tlv = aes.decrypt(nonce, ciphertext, header)

        # TLV tags: 0x01 import (Wh), 0x02 export (Wh), 0x03 V*100, 0x04 I*1000
        assert tlv[0] == 0x01 and tlv[1] == 8
        import_wh = struct.unpack(">Q", tlv[2:10])[0]
        assert import_wh == int(reading.energy_consumed * 1000.0)
        assert tlv[10] == 0x02 and tlv[11] == 8
        export_wh = struct.unpack(">Q", tlv[12:20])[0]
        assert export_wh == int(reading.energy_generated * 1000.0)

        # --- Ed25519 signature over the canonical string ---
        surplus = round(reading.energy_generated - reading.energy_consumed, 6)
        canonical = (
            f"{reading.meter_id}:{surplus:.6f}:{ts_ms}:{reading.sequence_number}"
        )
        key.public_key.verify(signature, canonical.encode())

        # tampering breaks verification
        with pytest.raises(InvalidSignature):
            key.public_key.verify(signature, (canonical + "x").encode())


@rust_only
def test_build_bulk_payload_empty_returns_zero():
    payload, count = build_bulk_payload([], {})
    assert payload == b"" and count == 0


@rust_only
def test_payload_fits_bulkrawrequest_message():
    ts = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    readings = [_reading("METER-001", 1.0, 0.5, 1, ts)]
    keys = build_meter_keys(["METER-001"])
    payload, count = build_bulk_payload(readings, keys)
    req = oracle_pb2.BulkRawRequest(payload=payload, meter_count=count)
    assert req.meter_count == 1
    assert req.payload == payload


def test_stubs_expose_bulk_raw_ingest():
    # Stub import works regardless of the Rust extension.
    from smart_meter_simulator.transport.grpc_gen import oracle_pb2_grpc

    assert hasattr(oracle_pb2_grpc.OracleServiceStub, "__init__")
    assert oracle_pb2.BulkRawRequest.DESCRIPTOR.name == "BulkRawRequest"


def test_missing_extension_error_is_clear(monkeypatch):
    # Force the lazy import to fail and confirm we surface RustExtensionMissing.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "gridtokenx_sim":
            raise ImportError("simulated missing extension")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RustExtensionMissing):
        build_bulk_payload([], {})


class _FakeClient:
    """Stand-in for OracleGrpcClient that records sends and can stall."""

    def __init__(self, *, delay: float = 0.0):
        self.target = "fake:0"
        self.calls: list[int] = []
        self._delay = delay
        self.connected = False
        self.closed = False

    def connect(self):
        self.connected = True
        return self

    async def bulk_raw_ingest(self, readings, keys):
        if self._delay:
            await __import__("asyncio").sleep(self._delay)
        self.calls.append(len(readings))

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_emitter_emits_non_blocking_and_caches_keys():
    from smart_meter_simulator.transport.oracle_grpc import OracleGrpcEmitter

    ts = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    readings = [_reading("METER-001", 1.0, 0.5, 1, ts)]

    emitter = OracleGrpcEmitter("fake:0")
    fake = _FakeClient()
    emitter._client = fake
    emitter.start()
    assert fake.connected

    emitter.emit(readings)  # returns immediately
    assert emitter._inflight is not None
    await emitter._inflight
    assert fake.calls == [1]

    # Keys cached: same meter set -> no rebuild.
    keys_first = emitter._keys
    emitter.emit(readings)
    await emitter._inflight
    assert emitter._keys is keys_first
    assert fake.calls == [1, 1]

    await emitter.close()
    assert fake.closed


@pytest.mark.asyncio
async def test_emitter_drops_tick_while_send_in_flight():
    from smart_meter_simulator.transport.oracle_grpc import OracleGrpcEmitter

    ts = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    readings = [_reading("METER-001", 1.0, 0.5, 1, ts)]

    emitter = OracleGrpcEmitter("fake:0")
    fake = _FakeClient(delay=0.2)
    emitter._client = fake
    emitter.start()

    emitter.emit(readings)  # starts a slow send
    first = emitter._inflight
    emitter.emit(readings)  # dropped: previous still running
    assert emitter._inflight is first

    await first
    assert fake.calls == [1]  # only one send happened
    await emitter.close()


@pytest.mark.asyncio
async def test_emitter_respects_emit_every():
    from smart_meter_simulator.transport.oracle_grpc import OracleGrpcEmitter

    ts = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    readings = [_reading("METER-001", 1.0, 0.5, 1, ts)]

    emitter = OracleGrpcEmitter("fake:0", emit_every=3)
    fake = _FakeClient()
    emitter._client = fake
    emitter.start()

    for _ in range(3):  # only the 3rd tick emits
        emitter.emit(readings)
        if emitter._inflight is not None:
            await emitter._inflight
    assert fake.calls == [1]
    await emitter.close()
