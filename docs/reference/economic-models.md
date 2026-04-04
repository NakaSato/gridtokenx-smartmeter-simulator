# Simulator Logic: Single Buyer vs Blockchain P2P Pricing

## Overview

This document defines the economic comparison framework for GridTokenX, comparing the centralized Single Buyer (ESB) model against the decentralized P2P blockchain model.

## Single Buyer Model (Baseline)

### Pricing Logic

**Energy Charge (Ladder Tariff Type 1.1.2):**
| Tier (kWh) | Rate (Baht/kWh) |
| :--- | :--- |
| 0 - 150 | 3.2484 |
| 151 - 400 | 4.2218 |
| > 400 | 4.4217 |

**Additional Charges:**
- **Ft (Jan-Apr 2026):** 0.0972 Baht/kWh
- **Service Charge:** 24.62 Baht/month
- **VAT:** 7%

**Feed-in Tariff:** 2.20 Baht/kWh (fixed buy-back rate)

### Bill Calculation

```
Total Bill = (Energy_Charge + Ft_Charge + Service_Charge) × 1.07
```

## GridTokenX P2P Model

### Dynamic Pricing Formula

```
p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min

Where:
  D_t = (Demand - Supply) / 100    # Normalized difference
  R_t = Demand / Supply             # Ratio
  p_min = 2.20 Baht/kWh             # Price floor (buy-back rate)
```

### Price Characteristics

| Scenario | Supply | Demand | Price Range |
|----------|--------|--------|-------------|
| Balanced | 100 | 100 | ~3.06 Baht/kWh |
| High Demand | 50 | 150 | ~3.5-4.5 Baht/kWh |
| Oversupply | 200 | 50 | ~2.0-2.5 Baht/kWh |
| Scarcity | 0 | 100 | 3.30 Baht/kWh (1.5× base) |

### Matching Mechanism

**Double Auction Engine:**
- Buyers submit bids (price, quantity)
- Sellers submit asks (price, quantity)
- Clearing price = intersection of supply/demand curves
- Settlement via Solana smart contracts

## Comparative Economics

### Revenue Comparison

| Component | Single Buyer | P2P Blockchain |
|-----------|--------------|----------------|
| **Export Price** | 2.20 Baht/kWh (fixed) | 2.50-4.00 Baht/kWh (dynamic) |
| **Import Price** | 3.88-4.42 Baht/kWh | 3.00-3.70 Baht/kWh + wheeling |
| **Wheeling Fee** | Included | 1.50-1.80 Baht/kWh |
| **Settlement** | Monthly billing | Real-time (block speed) |

### Savings Calculation

```
Buyer Savings = Grid_Retail_Rate - (P2P_Price + Wheeling)
Seller Gain   = P2P_Price - Wheeling - Grid_Buyback_Rate
Total Welfare = Buyer_Savings + Seller_Gain
```

### Break-even Analysis

```
Break-even P2P Price = Grid_Buyback + Wheeling
                     = 2.20 + 1.76
                     = 3.96 Baht/kWh

Viable Range: 2.20 < P2P_Price < 4.42
```

## Simulation Parameters

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `solar_capacity_kwp` | 5.0 | Rooftop solar capacity |
| `self_consumption_ratio` | 0.3 | Fraction consumed on-site |
| `p2p_participation_rate` | 0.8 | Fraction sold via P2P |
| `wheeling_cost` | 1.76 | TPA wheeling charge |
| `simulation_days` | 30 | Simulation period |

## Expected Outcomes

### Community Savings

Simulation results indicate **up to 56% reduction** in community energy costs through:
- Maximized self-consumption
- Reduced high-tier grid purchases
- Efficient local energy matching

### Prosumer Benefits

| Metric | Single Buyer | P2P Blockchain | Improvement |
|--------|--------------|----------------|-------------|
| Export Revenue | 2.20 Baht/kWh | 3.30 Baht/kWh | +50% |
| Annual Revenue (5kWp) | ~1,040 Baht | ~1,560 Baht | +50% |

### Consumer Benefits

| Metric | Single Buyer | P2P Blockchain | Improvement |
|--------|--------------|----------------|-------------|
| Import Cost | 4.42 Baht/kWh | 3.70 Baht/kWh | -16% |
| Monthly Bill (500kWh) | ~2,200 Baht | ~1,850 Baht | -16% |

## Implementation

The pricing logic is implemented in:
- `core/price_comparison.py` - Price comparison engine
- `core/market.py` - Double auction matching
- `routers/market.py` - API endpoints (`/api/v1/revenue/compare`)
- `tests/test_dynamic_pricing.py` - Formula verification tests
