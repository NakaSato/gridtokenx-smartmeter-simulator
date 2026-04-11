---
title: "Double Auction"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/market.py", "docs/reference/economic-models.md"]
tags: [market, mechanism, auction, clearing]
related: [[Market Engine]], [[LMP]], [[P2P Energy Trading]]
---

# Double Auction

The double auction mechanism is the core market clearing process where multiple buyers and sellers simultaneously submit bids and asks, and the market finds the uniform clearing price where supply meets demand.

## Summary

In the Smart Meter Simulator, P2P energy trading uses a continuous double auction. Prosumers post ask prices for surplus energy, consumers post bid prices for deficit energy, and trades execute whenever bid ≥ ask at the midpoint price.

## Mechanism

### Order Submission

| Role | Order Type | Price Bounds |
|------|-----------|--------------|
| Seller (Prosumer) | Ask (sell surplus) | 0.15 - 0.35 Baht/kWh |
| Buyer (Consumer) | Bid (buy deficit) | 0.20 - 0.40 Baht/kWh |

### Clearing Rule

```
Trade executes if: bid_price ≥ ask_price
Clearing price: (bid_price + ask_price) / 2  (midpoint)
Clearing quantity: min(bid_quantity, ask_quantity)
```

### Order Book Management

1. **Sort asks** by ascending price (cheapest first)
2. **Sort bids** by descending price (highest first)
3. **Match** top ask with top bid while bid ≥ ask
4. **Partial fills** — remaining quantity stays in book
5. **Unmatched orders** — carried to next tick or expire

### Example

Order book:

| Side | Price | Quantity |
|------|-------|----------|
| Ask | 0.20 | 5 kWh |
| Ask | 0.25 | 3 kWh |
| Ask | 0.30 | 8 kWh |
| --- | --- | --- |
| Bid | 0.35 | 4 kWh |
| Bid | 0.28 | 6 kWh |
| Bid | 0.22 | 10 kWh |

Clearing:
1. Bid 0.35 × Ask 0.20 → 4 kWh @ 0.275 (remaining ask: 1 kWh)
2. Bid 0.28 × Ask 0.20 → 1 kWh @ 0.24 (ask exhausted)
3. Bid 0.28 × Ask 0.25 → 2 kWh @ 0.265 (remaining bid: 4 kWh)
4. Bid 0.28 × Ask 0.30 → No trade (0.28 < 0.30)

Total traded: 7 kWh

## Uniform vs. Discriminatory Pricing

| Type | Description | In Simulator |
|------|-------------|--------------|
| **Uniform (midpoint)** | All trades at single clearing price | ✅ Used |
| **Discriminatory (pay-as-bid)** | Each trade at its own price | ❌ Not used |
| **Merc Auction** | Clearing at marginal bid price | ❌ Not used |

## Relationship to LMP

The double auction operates **at each node** with its own [[LMP]]:
- Local supply/demand determines the order book
- LMP sets the reference price for the node
- Cross-node trading requires wheeling charges (see [[Thai Electricity Market]])

## Properties

| Property | Value |
|----------|-------|
| **Strategy-proof** | Yes (truthful bidding is dominant strategy in theory) |
| **Efficient** | Yes (maximizes total surplus) |
| **Budget-balanced** | Yes (no subsidy needed) |
| **Continuous** | Yes (clears every tick, not batch) |

## Relationships

- **Implemented in:** [[Market Engine]]
- **Pricing input:** [[LMP]] (node reference prices)
- **Settlement:** [[P2P Energy Trading]]

## Known Issues

- Order book is in-memory — lost on restart
- No market maker — thin markets may have no trades
- No minimum trade size — very small trades may be inefficient
- Strategic bidding (shade bids below true value) not modeled
