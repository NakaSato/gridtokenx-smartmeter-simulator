---
title: "Ed25519 Signing"
category: protocols
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/utils/crypto.py", "docs/reference/meter-spec.md", "docs/architecture/smart-meter.md"]
tags: [crypto, solana, signing, keys]
related: [[Smart Meter]], [[Solana Integration]], [[EnergyReading Model]]
---

# Ed25519 Signing

Every smart meter reading is cryptographically signed at the source using Ed25519, the same signature scheme used by the Solana blockchain. This ensures data provenance, integrity, and non-repudiation from the meter to the settlement layer.

## Summary

Each `SmartMeter` generates an Ed25519 keypair on initialization. Every energy reading is signed with the meter's private key, and the signature is included in the reading payload. The signature can be verified by any downstream system using the meter's public key.

## Keypair Generation

```python
from nacl.signing import SigningKey

# Generate new keypair
signing_key = SigningKey.generate()
private_key = bytes(signing_key)        # 32 bytes
public_key = bytes(signing_key.verify_key)  # 32 bytes
```

Key properties:
- **Algorithm:** Ed25519 (RFC 8032)
- **Private key:** 32 bytes (seed)
- **Public key:** 32 bytes
- **Signature:** 64 bytes
- **Compatible with:** Solana ed25519_program

## Signing Payload

The signed payload is constructed from the reading data:

```python
import json

# Reading data as canonical JSON
payload = {
    "meter_id": "AMI_METER_001",
    "timestamp": "2026-04-10T12:00:00Z",
    "energy_generated_kwh": 5.234,
    "energy_consumed_kwh": 2.145,
    "battery_level_kwh": 7.5,
    "voltage_v": 239.8,
    "current_a": 12.3,
    "frequency_hz": 50.02,
}

# Canonical encoding (sorted keys, no whitespace)
message = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()

# Sign
signature = signing_key.sign(message).signature  # 64 bytes
```

## Verification

```python
from nacl.signing import VerifyKey

verify_key = VerifyKey(public_key_bytes)
verify_key.verify(message, signature)  # Raises BadSignatureError if invalid
```

## Solana Compatibility

The Ed25519 signatures are directly compatible with Solana's `ed25519_program`:

| Property | Value |
|----------|-------|
| **Signature scheme** | Ed25519 (pure) |
| **Key format** | Raw 32-byte seeds |
| **Encoding** | Base58 (Solana standard) |
| **Verification** | `ed25519_program.verify()` on-chain |

This enables:
- On-chain verification of meter readings
- Trustless data provenance
- REC (Renewable Energy Certificate) minting with signed data

## Reading Payload Format

```json
{
  "timestamp": "2026-04-10T12:00:00Z",
  "meter_id": "AMI_METER_001",
  "energy_generated_kwh": 5.234,
  "energy_consumed_kwh": 2.145,
  "battery_level_kwh": 7.5,
  "voltage_v": 239.8,
  "current_a": 12.3,
  "frequency_hz": 50.02,
  "power_factor": 0.95,
  "reactive_power": 1.642,
  "signature": "base64-encoded-64-byte-signature",
  "public_key": "base64-encoded-32-byte-public-key"
}
```

## Relationships

- **Used by:** [[Smart Meter]] (reading signing)
- **Verified by:** [[Solana Integration]] (on-chain)
- **Data model:** [[EnergyReading Model]]
- **Storage:** Public key persisted with meter configuration

## Known Issues

- Private keys stored in memory only — not persisted across restarts in simulation
- No key rotation model (real meters would need periodic key updates)
- Signature verification not enforced in transport layer (assumed downstream)
- Base64 encoding for transport (Solana uses Base58)
