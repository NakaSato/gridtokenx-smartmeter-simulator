---
name: oracle-protocol-v4
description: Work with the Oracle ingestion contract and Protocol v4 (UTT-S+) telemetry framing — proto/oracle.proto, the gridtokenx_sim Rust codec (TLV encode + AES-256-GCM + CRC-32 + Ed25519 sign), and the binary frame layout the parent Oracle Bridge expects. Use when wiring the simulator to emit verified readings to the Oracle Bridge, changing the frame format, or matching the proto contract. NOTE: this path is the contract/codec only — it is not currently wired into the running simulator.
---

# Oracle ingestion & Protocol v4 framing

This skill covers how a meter reading becomes a **verified, signed binary frame** the parent
GridTokenX **Oracle Bridge** ingests. Two artifacts define the contract; a third would carry it.

> **Reality check before you start:** this is **not wired into the live simulator today.**
> `grep` the Python backend and there is no gRPC client, no Oracle call, and `import
> gridtokenx_sim` is on no active code path (the engine serves readings over the REST API and,
> per config, can write `OUTPUT_FILE` jsonl — that's the only sink). The proto + Rust crate are
> the **contract and codec** for an emission path that is greenfield work. Don't assume an
> existing producer; you may be building it.

## The pieces

### 1. The gRPC contract — `proto/oracle.proto`
`package gridtokenx.oracle.v1`, `service OracleService`:
- `Ingest(MeterReading) -> IngestResponse` — single verified reading (VPP path A + settlement
  path B). `MeterReading` carries `reading_id, meter_id, meter_serial, user_id, wallet_address,
  zone_code?, kwh, energy_generated?, energy_consumed?, voltage?, current?, battery_level?,
  temperature?, timestamp, raw_payload (bytes), signature? (Ed25519, Base58)`. **Numeric
  fields are `string`** (decimal-as-string to avoid float drift).
- `IngestBatch(MeterReadingBatchRequest) -> ...` — `repeated MeterReading`; response reports
  `accepted_count` / `rejected_count`.
- `BulkRawIngest(BulkRawRequest) -> BulkRawResponse` — the **simulator's** high-throughput
  endpoint. `payload` is packed binary Protocol-v4 frames (bypasses per-reading protobuf
  overhead); `meter_count` says how many frames are inside.

### 2. The Protocol v4 codec — `src/rust_sim/` (`gridtokenx_sim`, PyO3)
`generate_utt_v4_batch(readings, ed25519_private_keys, aes_device_keys, sequence_numbers)`
encodes each reading and returns one packed buffer per meter. Per reading it:
1. **TLV-encodes** the measured quantities (`encode_tlv`),
2. **AES-256-GCM encrypts** the payload (header authenticated as AAD; 16-byte tag),
3. **CRC-32s** the frame,
4. **Ed25519-signs** it with the meter's device key.

Frame layout (matches `BulkRawRequest.payload` framing in the proto):
```
[frame_len: u8] [frame] [signature: 64 bytes]
  frame = 0x04 (version) | len | manuf_id(?) | ldn(8) | timestamp_sec(8, BE) | ciphertext | crc32
```
The 1-byte length field caps a frame at **255 bytes** — `generate_utt_v4_batch` raises if a
frame exceeds it. The three key/seq lists must be the **same length** as `readings`.

## If you are wiring emission up (the likely task)

1. Build with maturin from `src/rust_sim/` (`maturin develop`) — maturin is **not** in
   `pyproject.toml`, install it separately. Only then does `import gridtokenx_sim` resolve. The
   Docker build already compiles the crate to `gridtokenx_sim.so` (see root `Dockerfile` stage 2).
2. Map `EnergyReading` (`models/reading.py`) fields → `MeterFrameInput` for the codec, and →
   `MeterReading` proto fields for the typed paths. Mind the decimal-as-string convention and
   the optional-field semantics.
3. Add a sink that runs **after** `engine.tick()` produces `last_readings` (don't block the
   tick loop — dispatch with `asyncio.to_thread` like reading generation, or a background task).
   Manage Ed25519/AES device keys per meter — never log them (`#[instrument(skip(...))]`
   equivalent: keep keys out of logs).
4. Transport to the Oracle Bridge is gRPC (`tonic`/ConnectRPC on the Rust side of the
   ecosystem). The parent monorepo's Chain/Oracle conventions apply there, not here.

## Tests

Crypto/protocol tests are marked `@pytest.mark.crypto` (see `pytest.ini` markers). Run the
existing telemetry/ingestion tests with `PYTEST_ADDOPTS=--no-cov uv run pytest -q
tests/test_telemetry_ingestion.py`. If you add a frame producer, assert round-trips against the
frame layout above (version byte `0x04`, length field, 64-byte trailing signature) rather than
mocking the codec.

Related: driving meters *from* real data (the inverse direction) is the **meter-fleet-registry**
and telemetry-source work, not this skill.
