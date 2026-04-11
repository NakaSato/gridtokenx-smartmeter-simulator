---
title: "Solana Integration"
category: reference
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/thai-market.md", "docs/reference/economic-models.md", "docs/reference/meter-spec.md"]
tags: [blockchain, solana, settlement, token]
related: [[Ed25519 Signing]], [[P2P Energy Trading]], [[EnergyReading Model]], [[Carbon Offset Model]]
---

# Solana Integration

The Smart Meter Simulator is designed for integration with the Solana blockchain, providing Ed25519-compatible signed readings for on-chain verification, P2P energy settlement via SPL tokens, and REC (Renewable Energy Certificate) minting through the Energy Token Program.

## Summary

While the simulator itself does not run on-chain, it produces cryptographically signed data that is compatible with Solana's `ed25519_program` for verification. The parent GridTokenX platform handles on-chain settlement, token transfers, and REC minting.

## Ed25519 Compatibility

| Property | Value |
|----------|-------|
| **Signature scheme** | Ed25519 (RFC 8032) |
| **Private key** | 32 bytes (seed) |
| **Public key** | 32 bytes |
| **Signature** | 64 bytes |
| **Solana program** | `ed25519_program` |

Each meter's Ed25519 keypair is directly usable by Solana's on-chain Ed25519 signature verification:

```rust
// Solana ed25519_program
solana_program::ed25519_program::ed25519_verify(
    &message,
    &signature,
    &public_key
)
```

See [[Ed25519 Signing]] for signing details.

## Energy Token Program

The GridTokenX Energy Token Program (Solana smart contract) handles:

| Function | Description |
|----------|-------------|
| `mint_rec` | Mint Renewable Energy Certificate for verified generation |
| `transfer_energy` | Transfer GTNX tokens between prosumer and consumer |
| `settle_trade` | Settle P2P trade with atomic token swap |
| `record_reading` | Store verified reading hash on-chain |

### REC Minting Flow

```
1. Meter generates energy → signed reading
2. Oracle verifies Ed25519 signature
3. Oracle submits reading hash to Solana
4. Energy Token Program mints 1 REC per MWh
5. REC assigned to prosumer's wallet
6. REC can be sold separately from energy
```

## P2P Settlement Flow

```
Buyer Wallet                    Solana                      Seller Wallet
    │                             │                              │
    ├─── Place bid order ─────────┤                              │
    │                             │                              │
    │                             ├─── Match with ask order ──────┤
    │                             │                              │
    ├─── GTNX transfer ──────────→┤─── Atomic swap ──────────────→│
    │   (payment)                  │   (energy tokens)             │
    │                             │                              │
    │←── Trade receipt ───────────┤                              │
    │                             │←── Trade receipt ──────────────│
    │                             │                              │
    │                             ├─── Wheeling fee ──────────────→│
    │                             │   (to MEA/PEA wallet)          │
    │                             │                              │
```

### On-Chain Data

| Data | Stored On-Chain | Description |
|------|----------------|-------------|
| Reading hash | ✅ | SHA-256 hash of signed reading |
| Signature | ❌ | Verified off-chain, hash stored |
| Public key | ❌ | Registered in IAM service |
| Trade record | ✅ | Buyer, seller, quantity, price |
| REC ownership | ✅ | Token balance in wallet |
| Meter registration | ✅ | Meter ID → wallet mapping |

## GTNX Token

| Property | Value |
|----------|-------|
| **Token type** | SPL Token |
| **Decimals** | 6 |
| **Purpose** | P2P energy settlement |
| **1 GTNX** | ~1 Baht (pegged) |
| **Distribution** | Earned by prosumers, purchased by consumers |

## Wallet Architecture

Each service in the GridTokenX platform manages its own wallet:

| Service | Wallet Role |
|---------|-------------|
| IAM Service | Meter registration, identity → wallet mapping |
| Trading Service | Order matching, escrow |
| Oracle Bridge | Reading verification, REC minting |
| Utility (MEA/PEA) | Wheeling fee recipient |

The simulator does not hold a wallet — it produces signed data for on-chain verification by the Oracle Bridge.

## Relationships

- **Signing:** [[Ed25519 Signing]]
- **P2P market:** [[P2P Energy Trading]]
- **REC:** [[Carbon Offset Model]]
- **Data model:** [[EnergyReading Model]]

## Known Issues

- On-chain integration is in the parent GridTokenX platform, not the simulator
- GTNX token contract not yet deployed on Solana mainnet
- Oracle Bridge signing key distribution not finalized
- REC minting requires third-party certification (not just signed data)
- No dispute resolution for on-chain settlement errors
