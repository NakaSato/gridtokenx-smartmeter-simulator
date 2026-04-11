---
title: "Thai Electricity Market"
category: markets
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/thai-market.md", "src/smart_meter_simulator/config/thai_market.py"]
tags: [thai, market, regulatory, structure]
related: [[TOU Tariffs]], [[Progressive Tariff Tiers]], [[P2P Energy Trading]], [[Billing Engine]], [[LMP]]
---

# Thai Electricity Market

The Thai electricity market is a single-buyer model dominated by state-owned utilities, with emerging P2P trading pilot programs under ERC (Energy Regulatory Commission) regulatory sandboxing.

## Summary

Thailand's electricity supply chain is vertically integrated with three main utilities: EGAT (generation + transmission), MEA (Bangkok distribution), and PEA (provincial distribution). The Smart Meter Simulator models this structure with Thai-specific tariffs, wheeling charges, and distribution network topologies.

## Market Structure

```
┌─────────────┐
│    EGAT     │  Electricity Generating Authority of Thailand
│  (Gen + Tx) │  - Owns power plants + 500/230 kV transmission
│             │  - Sells to MEA, PEA, and direct customers
└──────┬──────┘
       │ Wholesale (bulk supply tariff)
  ┌────┴────┐
  │         │
┌─▼──┐   ┌─▼──┐
│ MEA│   │ PEA│  Metropolitan / Provincial Electricity Authority
│(BKK│   │(Prov│  - 22kV MV / 400V LV distribution
│ +N) │   │ince)│  - End-user billing, customer service
└──┬──┘   └──┬──┘
   │         │
   └────┬────┘
        │
  ┌─────▼─────┐
  │  Customers │  Residential, Commercial, Industrial
  │            │  - TOU tariffs, FiT for prosumers
  └────────────┘
```

## Key Players

| Entity | Role | Coverage |
|--------|------|----------|
| **EGAT** | Generation + Transmission | National (500/230 kV grid) |
| **MEA** | Distribution (Bangkok metro) | Bangkok, Nonthaburi, Samut Prakan |
| **PEA** | Distribution (provincial) | 74 provinces (outside MEA area) |
| **ERC** | Regulation | National (tariff approval, licensing) |

## Pricing Structure

### Wholesale (EGAT → MEA/PEA)

| Component | Rate |
|-----------|------|
| Bulk Supply Tariff | ~2.80 Baht/kWh (varies by fuel mix) |
| Fuel Adjustment (Ft) | 0.0972 Baht/kWh (quarterly) |

### Retail (MEA/PEA → Customers)

| Category | Rate (Baht/kWh) |
|----------|-----------------|
| Residential (0-150 kWh) | 3.24 |
| Residential (151-400 kWh) | 4.22 |
| Residential (400+ kWh) | 4.42 |
| TOU On-Peak (< 22 kV) | 5.7982 |
| TOU Off-Peak (< 22 kV) | 2.6369 |
| Feed-in Tariff (FiT) | ~2.20 Baht/kWh |

### Additional Charges

| Charge | Rate | Description |
|--------|------|-------------|
| Service charge | 33.29 Baht/month | Fixed monthly fee |
| Ft (Fuel Adjustment) | 0.0972 Baht/kWh | Quarterly fuel cost pass-through |
| VAT | 7% | Applied to total bill |
| Wheeling charge | Variable | For P2P transactions (use of grid) |

## P2P Trading Pilot

Under ERC sandboxing:

| Aspect | Detail |
|--------|--------|
| **Model** | Bilateral contracts between prosumers and consumers |
| **Pricing** | Negotiated (bounded by FiT floor and retail ceiling) |
| **Settlement** | Solana GTNX tokens (blockchain) |
| **Wheeling** | Paid to MEA/PEA for grid use |
| **Platform** | GridTokenX Smart Meter Simulator |

## Wheeling Charges

When P2P energy flows across MEA/PEA distribution networks:

| Component | Description |
|-----------|-------------|
| Use of System (UoS) | Cost of distribution infrastructure |
| Loss compensation | I²R losses on distribution lines |
| Balancing service | Grid balancing and backup |

In the simulator: wheeling charges are applied per [[Thai Tariffs]] constants.

## ERC Regulatory Sandbox

| Feature | Description |
|---------|-------------|
| **Purpose** | Test innovative business models without full regulatory compliance |
| **Duration** | 1-2 year pilot |
| **Participants** | Limited (50-500 prosumers) |
| **Oversight** | ERC monitoring, consumer protection |

## Relationships

- **Tariff rates:** [[TOU Tariffs]], [[Progressive Tariff Tiers]]
- **P2P mechanism:** [[P2P Energy Trading]]
- **Grid topology:** [[Thai Grid Topology]]
- **Billing:** [[Billing Engine]]

## Known Issues

- Rates are 2026 estimates — actual rates published by ERC/MEA/PEA quarterly
- P2P pilot is simulated — not yet approved by Thai ERC
- Wheeling charges are approximated — not approved by regulator
- FiT rate may differ by technology (solar, wind, biomass)
