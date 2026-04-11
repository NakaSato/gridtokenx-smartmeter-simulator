---
title: "P2P Energy Trading"
category: markets
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/thai-market.md", "docs/reference/economic-models.md", "src/smart_meter_simulator/core/market.py"]
tags: [p2p, blockchain, solana, trading]
related: [[Double Auction]], [[LMP]], [[Thai Electricity Market]], [[Market Engine]], [[Solana Integration]]
---

# P2P Energy Trading

Peer-to-Peer (P2P) energy trading enables prosumers to sell surplus renewable energy directly to neighboring consumers, bypassing the traditional utility buyback model.

## Summary

The GridTokenX platform implements P2P energy trading on Solana, where prosumers post surplus energy as sell orders, consumers post buy orders, and trades clear via a double auction mechanism. Settlement uses GTNX tokens with automatic wheeling charge payment to the distribution utility (MEA/PEA).

## Trading Flow

```
┌─────────────────┐          ┌─────────────────┐
│   Prosumer      │          │    Consumer     │
│   (Seller)      │          │    (Buyer)       │
└────────┬────────┘          └────────┬────────┘
         │                            │
         │  Sell Order (Ask)          │  Buy Order (Bid)
         │  qty: 5 kWh, price: 0.25   │  qty: 3 kWh, price: 0.30
         ▼                            ▼
    ┌──────────────────────────────────────┐
    │       Market Engine (Double Auction)  │
    │       Clearing: 3 kWh @ 0.275         │
    └──────────────────┬───────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌──────────┐
    │ Solana  │  │ Wheeling│  │ REC      │
    │ GTNX    │  │ to MEA  │  │ Minting  │
    │ Transfer│  │ /PEA    │  │          │
    └─────────┘  └─────────┘  └──────────┘
```

## Order Lifecycle

1. **Surplus Discovery** — Prosumer generates more than consumed
2. **Ask Order Created** — Quantity, minimum price (≥ FiT rate)
3. **Bid Order Created** — Consumer requests energy, maximum price (≤ TOU retail)
4. **Matching** — Market engine finds bid ≥ ask
5. **Clearing** — Trade executes at midpoint price
6. **Settlement** — GTNX tokens transfer on Solana
7. **Wheeling** — Grid usage fee paid to MEA/PEA
8. **REC Minting** — Renewable Energy Certificate minted for green attribute

## Price Bounds

| Bound | Value | Rationale |
|-------|-------|-----------|
| **Ask Floor** | ~2.20 Baht/kWh (FiT) | Prosumer can always sell to utility at this rate |
| **Bid Ceiling** | ~5.80 Baht/kWh (TOU on-peak) | Consumer can always buy from utility at this rate |
| **Typical Clearing** | 2.50-4.50 Baht/kWh | Between floor and ceiling |

## Settlement on Solana

| Step | On-Chain Action |
|------|-----------------|
| Order placement | Record order hash on-chain (optional) |
| Trade clearing | Off-chain match, on-chain settlement |
| Token transfer | `spl_token::transfer` from buyer to seller |
| Wheeling payment | `spl_token::transfer` from buyer to utility |
| REC minting | `energy_token_program::mint_rec` to prosumer |
| Audit trail | Transaction signature + meter reading signature |

## Economic Comparison

| Model | Prosumer Revenue | Consumer Cost | Utility Impact |
|-------|-----------------|---------------|----------------|
| **FiT (Single Buyer)** | 2.20 Baht/kWh | N/A | Buys surplus, resells |
| **P2P Trading** | 2.50-4.50 Baht/kWh | 2.50-4.50 Baht/kWh | Collects wheeling only |
| **Grid Import** | N/A | 5.80 Baht/kWh (on-peak) | Sells at retail |

P2P benefits both parties: prosumer earns more than FiT, consumer pays less than retail.

## Wheeling Charges

For each P2P transaction:

```
wheeling_fee = traded_kwh × wheeling_rate  # Baht/kWh
utility_revenue += wheeling_fee
```

Wheeling rate compensates MEA/PEA for grid use (see [[Thai Electricity Market]]).

## Relationships

- **Mechanism:** [[Double Auction]]
- **Pricing:** [[LMP]] (nodal reference)
- **Market context:** [[Thai Electricity Market]]
- **Settlement:** [[Solana Integration]]
- **Engine:** [[Market Engine]]

## Known Issues

- Real-time Solana settlement is simulated — blockchain integration in parent platform
- Wheeling rates are approximated — not ERC-approved
- REC minting is off-chain — on-chain implementation pending
- No dispute resolution mechanism (meter disagreement, delivery shortfall)
