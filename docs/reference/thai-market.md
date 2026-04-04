# Thai Electricity Market Analysis

## Executive Summary

Thailand's electricity market is transitioning from a centralized Single Buyer model to a decentralized prosumer-centric ecosystem. This document analyzes the regulatory framework, tariff structures, and market dynamics relevant to GridTokenX deployment.

## Utility Providers

### Jurisdictional Distribution

| Provider | Service Area | Consumers |
|----------|--------------|-----------|
| **MEA** | Bangkok, Nonthaburi, Samut Prakan | Urban high-density |
| **PEA** | 74 other provinces | Rural, industrial, agricultural |
| **EGAT** | National (generation/transmission) | Wholesale only |

### Key Differences

| Metric | MEA | PEA |
|--------|-----|-----|
| Grid Complexity | High-voltage underground | Long-distance transmission |
| Primary Challenge | Urban peak loads | Remote grid stability |
| Net Metering | Active urban program | Active provincial program |

## Residential Tariff Structures

### Type 1.1.2: Standard Residential (>150 kWh/month)

| Tier (kWh) | Rate (Baht/kWh) |
| :--- | :--- |
| 0 - 150 | 3.2484 |
| 151 - 400 | 4.2218 |
| > 400 | 4.4217 |

**Service Charge:** 24.62 Baht/month

### Type 1.2: Time of Use (TOU)

| Period | Rate (Baht/kWh) |
| :--- | :--- |
| On-Peak (Mon-Fri 09:00-22:00) | 5.7982 |
| Off-Peak (Mon-Fri 22:00-09:00) | 2.6369 |
| Off-Peak (Weekends/Holidays) | 2.6369 |

**Service Charge:** 33.29 Baht/month

## Fuel Adjustment Charge (Ft)

| Period | Ft Rate (Baht/kWh) |
| :--- | :--- |
| Jan - Apr 2026 | 0.0972 |
| Sep - Dec 2025 | 0.1572 |

**Note:** Ft is recalculated every 4 months based on fuel costs and exchange rates.

## Solar Incentives

### Royal Decree No. 805 (Tax Deduction)

| Provision | Details |
|-----------|---------|
| **Max Deduction** | 200,000 Baht |
| **Capacity Limit** | 10 kWp |
| **Validity** | Mar 3, 2026 - Dec 31, 2028 |
| **Eligibility** | Grid-tied systems, registered users |

### Installation Costs (2026)

| System Size | Cost (Baht) | Annual Generation | Payback |
|-------------|-------------|-------------------|---------|
| 3 kWp | 90k - 130k | 4,200 - 4,800 kWh | 5-6 years |
| 5 kWp | 150k - 200k | 7,000 - 8,000 kWh | 4-5 years |
| 10 kWp | 300k - 400k | 14,000 - 16,000 kWh | 3.5-4 years |

## P2P Trading Economics

### Arbitrage Opportunity

```
Grid Purchase Rate:  4.4217 Baht/kWh (high tier)
Grid Buyback Rate:   2.2000 Baht/kWh (fixed)
Arbitrage Spread:    2.2217 Baht/kWh
```

### TPA Wheeling Charges (Indicative)

| Component | Rate (Baht/kWh) |
|-----------|-----------------|
| Wheeling (T&D) | ~1.12 |
| System Security | ~0.50 |
| Policy Expense | ~0.14 |
| **Total** | **~1.76** |

### P2P Viability Threshold

```
Break-even P2P Price = Buyback Rate + Wheeling Cost
                     = 2.20 + 1.76
                     = 3.96 Baht/kWh

P2P is viable when: 2.20 < P2P_Price < 4.42
```

## Regulatory Framework

### ERC Sandbox Program

- Allows temporary exemptions for P2P testing
- University and industry partnerships
- Pathway to full commercial licensing

### Foreign Ownership Restrictions

- Maximum 49% foreign shareholding
- Maximum 50% foreign directors
- Existing licenses may be grandfathered

## Grid Modernization (PDP 2026-2037)

### Targets

- 50% clean energy by 2037
- 5,000 MW community solar
- ASEAN Power Grid interconnection
- Smart meter deployment nationwide

### Smart Grid Roadmap

1. **Phase 1 (2017-2021):** Foundation infrastructure ✅
2. **Phase 2 (2022-2031):** DER management systems (current)
3. **Phase 3 (2032+):** Full smart grid integration

## Market Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ft volatility | High | Solar hedging, P2P trading |
| Regulatory changes | Medium | ERC Sandbox participation |
| Foreign ownership limits | Medium | Local partnership structure |
| Grid instability | Low | Battery storage integration |

## Conclusion

The Thai market presents favorable conditions for GridTokenX:
- High retail tariffs create arbitrage opportunities
- Government incentives reduce solar adoption barriers
- TPA framework enables legal P2P trading
- Smart grid modernization provides infrastructure
