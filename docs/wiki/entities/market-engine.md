---
title: "Market Engine"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/market.py", "docs/architecture/market-engine.md", "docs/reference/economic-models.md"]
tags: [market, p2p, auction, settlement]
related: [[Double Auction]], [[LMP]], [[P2P Energy Trading]], [[Thai Electricity Market]], [[Billing Engine]]
---

# Market Engine

The `MarketManager` implements P2P energy trading with double auction clearing, locational marginal pricing, and settlement integration.

## Summary

The market engine matches prosumer surplus with consumer deficit through a continuous double auction mechanism. It computes locational marginal prices (LMP) that reflect grid congestion and losses, then settles trades via the blockchain (Solana GTNX tokens) or traditional billing.

## Market Mechanism

### Double Auction

| Role | Action | Price Range |
|------|--------|-------------|
| Seller (Prosumer) | Posts surplus energy at ask price | Min sell: ~0.15 Baht/kWh |
| Buyer (Consumer) | Posts deficit energy at bid price | Max buy: ~0.40 Baht/kWh |
| Clearing | Match when bid ≥ ask | Uniform price at midpoint |

### Order Book
- **Active orders** sorted by price-time priority
- **Partial fills** supported (order may span multiple ticks)
- **Unmatched orders** carried forward or expired

### Settlement
After clearing:
1. Calculate transaction cost = cleared_quantity × cleared_price
2. Apply wheeling charges ([[Thai Electricity Market]])
3. Apply VAT (7%) + Ft adjustment
4. Record for blockchain settlement (Solana) or traditional billing

## Locational Marginal Pricing (LMP)

LMP = Energy + Congestion + Losses

| Component | Description |
|-----------|-------------|
| **Energy** | System-wide marginal cost (reference bus) |
| **Congestion** | Cost due to transmission limits |
| **Losses** | Marginal loss component (I²R) |

In the simulator, LMP is approximated from nodal prices derived from:
- Grid topology (feeder/substation mapping)
- VPP dispatch costs
- Local supply/demand imbalance

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_sell_price` | 0.15 Baht/kWh | Floor for ask orders |
| `max_sell_price` | 0.35 Baht/kWh | Ceiling for ask orders |
| `min_buy_price` | 0.20 Baht/kWh | Floor for bid orders |
| `max_buy_price` | 0.40 Baht/kWh | Ceiling for bid orders |
| `grid_purchase_rate` | 0.28 Baht/kWh | Default grid import rate |
| `grid_feed_in_rate` | 0.12 Baht/kWh | Default grid export (FiT) rate |

## Revenue Comparison

| Model | Description | Typical Price |
|-------|-------------|---------------|
| **Single Buyer (Utility)** | EGAT buys all surplus at fixed FiT | ~2.20 Baht/kWh |
| **P2P Trading** | Direct peer-to-peer at LMP | 0.15-0.40 Baht/kWh |
| **VPP Aggregated** | Cluster sells ancillary services | Variable (aFRR + peak shaving) |

See [[VPP Revenue Streams]] for detailed breakdown.

## Relationships

- **Input from:** [[Smart Meter]] (surplus/deficit from readings)
- **Price input:** [[Price Provider]] (TOU tariffs), [[LMP]] (nodal prices)
- **Settlement via:** [[Billing Engine]] (traditional) or Solana (P2P)
- **Wheeling charges:** [[Thai Electricity Market]]
- **Stored in:** Market clearing results via [[InfluxDB Integration]]

## Known Issues

- LMP approximation is simplified — full AC-OPF not implemented
- Order book is in-memory — no persistence across restarts
- Blockchain settlement is simulated — real Solana integration in parent platform
- Market manipulation (strategic bidding) not modeled
