//! `gridtokenx_sim` — Protocol v4 (UTT-S+) framing codec.
//!
//! Scope: this crate does **framing + cryptography only**. Reading *generation*
//! (PV via pvlib/PVWatts, ZIP voltage-response loads) lives in the Python path
//! (`devices/solar.py`, `devices/load.py`, `core/meter_logic/`) and cannot be
//! faithfully reproduced in Rust, so it is intentionally not duplicated here.
//! Python computes the physics and hands already-resolved per-meter values to
//! [`generate_utt_v4_batch`], which encodes, encrypts (AES-256-GCM), CRCs, and
//! signs (Ed25519) each reading into a binary frame ready for transmission.

use aes_gcm::{
    aead::{Aead, Payload},
    Aes256Gcm, Key, KeyInit, Nonce,
};
use crc32fast::Hasher;
use ed25519_dalek::{Signer, SigningKey};
use pyo3::prelude::*;

/// Header bytes that follow the 1-byte length field: manufacturer id (3) +
/// logical device name (8) + timestamp (8). Used to size the frame-length field.
const HEADER_TAIL_LEN: usize = 19;
/// AES-256-GCM authentication tag length appended to every ciphertext.
const GCM_TAG_LEN: usize = 16;
/// CRC-32 trailer length.
const CRC_LEN: usize = 4;

/// A single per-meter reading, already computed by the Python physics path,
/// ready to be framed into a Protocol v4 packet.
// `from_py_object` is required so the batch function can extract a
// `Vec<MeterFrameInput>` argument directly from a Python list.
#[pyclass(from_py_object)]
#[derive(Debug, Clone)]
pub struct MeterFrameInput {
    #[pyo3(get, set)]
    pub meter_id: String,
    /// Active energy imported (consumed) over the interval, in kWh.
    #[pyo3(get, set)]
    pub energy_import_kwh: f64,
    /// Active energy exported (generated) over the interval, in kWh.
    #[pyo3(get, set)]
    pub energy_export_kwh: f64,
    /// Net surplus over the interval, in kWh — used in the signature canonical string.
    #[pyo3(get, set)]
    pub surplus_kwh: f64,
    /// Measured voltage, in volts.
    #[pyo3(get, set)]
    pub voltage: f64,
    /// Measured current, in amperes.
    #[pyo3(get, set)]
    pub current: f64,
}

#[pymethods]
impl MeterFrameInput {
    #[new]
    #[pyo3(signature = (
        meter_id,
        energy_import_kwh,
        energy_export_kwh,
        surplus_kwh,
        voltage = 230.0,
        current = 0.0,
    ))]
    fn new(
        meter_id: String,
        energy_import_kwh: f64,
        energy_export_kwh: f64,
        surplus_kwh: f64,
        voltage: f64,
        current: f64,
    ) -> Self {
        Self {
            meter_id,
            energy_import_kwh,
            energy_export_kwh,
            surplus_kwh,
            voltage,
            current,
        }
    }
}

/// Encode one reading's measured quantities as a Protocol v4 TLV payload.
///
/// Tag layout (big-endian values):
/// - `0x01` Active Energy Import, 8 bytes, Wh
/// - `0x02` Active Energy Export, 8 bytes, Wh
/// - `0x03` Voltage, 4 bytes, 0.01 V
/// - `0x04` Current, 4 bytes, 1 mA
fn encode_tlv(r: &MeterFrameInput) -> Vec<u8> {
    let mut tlv = Vec::with_capacity(32);

    tlv.push(0x01);
    tlv.push(8);
    tlv.extend_from_slice(&((r.energy_import_kwh * 1000.0) as u64).to_be_bytes());

    tlv.push(0x02);
    tlv.push(8);
    tlv.extend_from_slice(&((r.energy_export_kwh * 1000.0) as u64).to_be_bytes());

    tlv.push(0x03);
    tlv.push(4);
    tlv.extend_from_slice(&((r.voltage * 100.0) as u32).to_be_bytes());

    tlv.push(0x04);
    tlv.push(4);
    tlv.extend_from_slice(&((r.current * 1000.0) as u32).to_be_bytes());

    tlv
}

/// High-performance UTT v4 batch framing.
///
/// Encodes, encrypts (AES-256-GCM, header authenticated as AAD), CRC-32s, and
/// Ed25519-signs each reading. Returns one packed buffer per meter, laid out as:
/// `[frame_len: u8][frame][signature: 64 bytes]`, where `frame` is
/// `[version][length][manuf_id(3)][ldn(8)][timestamp(8)][ciphertext][crc32(4)]`.
#[pyfunction]
#[pyo3(signature = (
    readings,
    ed25519_private_keys,
    aes_device_keys,
    timestamp_sec,
    sequence_numbers,
))]
fn generate_utt_v4_batch(
    readings: Vec<MeterFrameInput>,
    ed25519_private_keys: Vec<[u8; 32]>,
    aes_device_keys: Vec<[u8; 32]>,
    timestamp_sec: u64,
    sequence_numbers: Vec<u32>,
) -> PyResult<Vec<Vec<u8>>> {
    if readings.len() != ed25519_private_keys.len()
        || readings.len() != aes_device_keys.len()
        || readings.len() != sequence_numbers.len()
    {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "readings, ed25519_private_keys, aes_device_keys, and sequence_numbers must have the same length",
        ));
    }

    let timestamp_ms = timestamp_sec.saturating_mul(1000);
    let mut frames = Vec::with_capacity(readings.len());

    for (i, r) in readings.iter().enumerate() {
        // 1. TLV payload (plaintext). Its length is deterministic, so we can
        //    size the frame-length field before encrypting and authenticate the
        //    full header as AAD.
        let tlv = encode_tlv(r);
        let ciphertext_len = tlv.len() + GCM_TAG_LEN;

        // 2. Frame length field counts every byte after itself.
        let frame_len = HEADER_TAIL_LEN + ciphertext_len + CRC_LEN;
        let length_byte = u8::try_from(frame_len).map_err(|_| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "frame length {frame_len} exceeds the 1-byte length field (max 255)"
            ))
        })?;

        // 3. Build the 21-byte header: version, length, manuf id, LDN, timestamp.
        let mut manuf_id = [0u8; 3];
        manuf_id.copy_from_slice(b"GXT");

        let mut ldn = [0u8; 8];
        let ldn_src = format!("LDN-{:0>8}", i % 100_000_000);
        let ldn_bytes = ldn_src.as_bytes();
        let copy_len = ldn_bytes.len().min(8);
        ldn[..copy_len].copy_from_slice(&ldn_bytes[..copy_len]);

        let mut frame = Vec::with_capacity(1 + frame_len);
        frame.push(0x04); // Version
        frame.push(length_byte);
        frame.extend_from_slice(&manuf_id);
        frame.extend_from_slice(&ldn);
        frame.extend_from_slice(&timestamp_sec.to_be_bytes());
        debug_assert_eq!(frame.len(), HEADER_TAIL_LEN + 2, "header must be 21 bytes");

        // 4. AES-256-GCM. The header is authenticated as AAD (authenticated but
        //    not encrypted), so any tampering with version/id/timestamp/length
        //    fails decryption.
        let key = Key::<Aes256Gcm>::from_slice(&aes_device_keys[i]);
        let cipher = Aes256Gcm::new(key);

        let mut nonce_bytes = [0u8; 12];
        nonce_bytes[0..3].copy_from_slice(&manuf_id);
        nonce_bytes[3..11].copy_from_slice(&timestamp_sec.to_be_bytes());
        nonce_bytes[11] = 0x04;
        let nonce = Nonce::from_slice(&nonce_bytes);

        let header = frame.clone();
        let ciphertext = cipher
            .encrypt(
                nonce,
                Payload {
                    msg: &tlv,
                    aad: &header,
                },
            )
            .map_err(|_| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("AES-GCM encryption failed")
            })?;
        debug_assert_eq!(ciphertext.len(), ciphertext_len);
        frame.extend_from_slice(&ciphertext);

        // 5. CRC-32 over version + length + header tail + ciphertext.
        let mut hasher = Hasher::new();
        hasher.update(&frame);
        let crc = hasher.finalize();
        frame.extend_from_slice(&crc.to_be_bytes());

        // 6. Ed25519 signature over the canonical string
        //    "{meter_id}:{surplus_kwh:.6}:{timestamp_ms}:{sequence_number}".
        let canonical = format!(
            "{}:{:.6}:{}:{}",
            r.meter_id, r.surplus_kwh, timestamp_ms, sequence_numbers[i]
        );
        let signing_key = SigningKey::from_bytes(&ed25519_private_keys[i]);
        let signature = signing_key.sign(canonical.as_bytes());

        // 7. Pack: [frame_len: u8][frame][signature: 64 bytes].
        let mut packed = Vec::with_capacity(1 + frame.len() + 64);
        packed.push(frame.len() as u8);
        packed.extend_from_slice(&frame);
        packed.extend_from_slice(&signature.to_bytes());

        frames.push(packed);
    }

    Ok(frames)
}

#[pymodule]
fn gridtokenx_sim(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MeterFrameInput>()?;
    m.add_function(wrap_pyfunction!(generate_utt_v4_batch, m)?)?;
    Ok(())
}
