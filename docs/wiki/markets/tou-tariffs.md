---
title: "TOU Tariffs"
category: markets
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/reference/thai-tariffs.md", "src/smart_meter_simulator/config/thai_market.py", "TOU.md"]
tags: [thai, tariff, time-of-use, pricing]
related: [[Thai Electricity Market]], [[Progressive Tariff Tiers]], [[Price Provider]], [[Standard Load Profiles]]
---

# TOU Tariffs (Time-of-Use)

Time-of-Use (TOU) tariffs charge different electricity rates based on the time of consumption, incentivizing load shifting from peak to off-peak periods.

## Summary

Thai TOU tariffs have two periods: on-peak (Mon-Fri 09:00-22:00) and off-peak (all other times). On-peak rates are ~2.2× higher than off-peak, encouraging consumers to shift flexible loads (EV charging, water heating, battery charging) to nights and weekends.

## Time Schedule

| Period | Days | Hours |
|--------|------|-------|
| **On-Peak** | Mon-Fri (excluding public holidays) | 09:00 - 22:00 |
| **Off-Peak** | Mon-Fri 22:00-09:00 | All night |
| **Off-Peak** | Sat-Sun (all day) | 00:00-24:00 |
| **Off-Peak** | Public holidays (all day) | 00:00-24:00 |

```
Mon-Fri:
  00:00 ─────── OFF-PEAK ─────── 09:00 ──── ON-PEAK ──── 22:00 ── OFF ── 24:00
  
Sat-Sun:
  00:00 ─────────── OFF-PEAK (all day) ─────────────────────────── 24:00
```

## TOU Rates (2026, < 22 kV)

| Category | On-Peak | Off-Peak | Service Charge |
|----------|---------|----------|----------------|
| Residential (Type 1.2) | 5.7982 | 2.6369 | 33.29 Baht/month |
| Small Business (Type 2.2) | 5.7982 | 2.6369 | 33.29 Baht/month |

**Rate ratio:** On-peak / Off-peak = 2.20×

## Additional Charges

| Charge | Rate | Application |
|--------|------|-------------|
| Ft (Fuel Adjustment) | 0.0972 Baht/kWh | Both periods |
| VAT | 7% | Applied to total (energy + Ft + service) |

### Total Cost Calculation

```
energy_cost = consumption_on_peak × 5.7982 + consumption_off_peak × 2.6369
ft_charge = total_consumption × 0.0972
subtotal = energy_cost + ft_charge + service_charge
total = subtotal × 1.07  # VAT
```

## TOU vs. Progressive Tariff

| Property | TOU | Progressive |
|----------|-----|-------------|
| **Basis** | Time of use | Total volume |
| **Periods** | 2 (on/off) | 3 tiers (0-150, 151-400, 400+) |
| **Best for** | Flexible loads (battery, EV) | Low-consumption households |
| **On-peak rate** | 5.7982 | Up to 4.42 |
| **Off-peak rate** | 2.6369 | Same as on-peak |
| **Service charge** | 33.29/month | 38.22/month |

See [[Progressive Tariff Tiers]].

## TOU Multipliers (for Simulation)

In the simulator, TOU pricing is applied with multipliers:

| Period | Multiplier | Base Rate | Effective Rate |
|--------|-----------|-----------|----------------|
| On-Peak | 1.2× | 0.28 GXT/kWh | 0.336 GXT/kWh |
| Off-Peak | 0.8× | 0.28 GXT/kWh | 0.224 GXT/kWh |

## P2P Price Bounds

TOU rates bound the P2P trading range:

| Bound | Value | Rationale |
|-------|-------|-----------|
| **Floor** | FiT (~2.20 Baht) | Prosumer won't sell below guaranteed utility buyback |
| **Ceiling** | On-peak TOU (5.80 Baht) | Consumer won't pay more than grid retail price |

## Implementation

```python
def is_on_peak(dt: datetime) -> bool:
    """Check if a datetime falls in on-peak period."""
    if dt.weekday() >= 5:  # Sat=5, Sun=6
        return False
    if is_public_holiday(dt):
        return False
    return 9 <= dt.hour < 22

def get_tou_price(dt: datetime) -> float:
    if is_on_peak(dt):
        return 5.7982
    return 2.6369
```

## Relationships

- **Market context:** [[Thai Electricity Market]]
- **Alternative:** [[Progressive Tariff Tiers]]
- **Implementation:** [[Price Provider]] (ToUPriceProvider)
- **Load response:** [[Standard Load Profiles]]

## Known Issues

- Public holiday list must be updated annually
- TOU not available for all customer categories (small residential defaults to progressive)
- Ft rate changes quarterly — simulator uses fixed 2026 value
- No demand charge (kW-based) — only energy (kWh-based)
