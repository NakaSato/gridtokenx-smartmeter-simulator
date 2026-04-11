---
title: "aFRR"
category: concepts
created: 2026-04-10
updated: 2026-04-10
sources: ["docs/architecture/market-engine.md", "src/smart_meter_simulator/core/vpp.py", "src/rust_sim/src/lib.rs"]
tags: [frequency, vpp, ancillary, reserve]
related: [[Droop Control]], [[VPP Orchestrator]], [[Multi-Objective Dispatch]], [[Frequency Regulator]], [[VPP Revenue Streams]]
---

# aFRR (Automatic Frequency Restoration Reserve)

aFRR is the secondary frequency control mechanism that automatically restores grid frequency to its nominal value (50 Hz) after a disturbance, by dispatching flexible resources from VPP clusters.

## Summary

aFRR activates when frequency deviates beyond the deadband (±20 mHz) and dispatches VPP-aggregated DER resources to absorb or inject power, restoring frequency to 50 Hz. It is the automated, fast-acting replacement for manual frequency restoration.

## Mechanism

### Frequency Deviation Response

```python
def calculate_afrr(frequency_hz, max_flex_up, max_flex_down):
    deadband = 0.02  # 20 mHz
    deviation = frequency_hz - 50.0

    if abs(deviation) < deadband:
        return 0.0  # No action needed

    gain = 10.0  # MW/Hz (scaled for simulation)
    target = -deviation * gain  # Negative feedback

    # Clip to cluster flexibility limits
    if target > 0:
        return min(target, max_flex_up)   # Discharge
    else:
        return max(target, -max_flex_down) # Charge
```

### Upward vs Downward Flexibility

| Direction | Frequency | Action | Resource |
|-----------|-----------|--------|----------|
| **Upward** | Below 49.98 Hz | Discharge/increase gen | Battery discharge, solar curtailment recovery |
| **Downward** | Above 50.02 Hz | Charge/decrease gen | Battery charge, solar curtailment |

### Cluster Flexibility Calculation

For each DER resource:
```
max_flexibility_up = min(max_discharge_kw, current_soc_kwh / 0.25h)
max_flexibility_down = min(max_charge_kw, (capacity_kwh - current_soc_kwh) / 0.25h)
```

The 0.25h factor reflects the 15-minute dispatch interval.

## Dispatch Sequence

1. **Frequency deviation detected** (beyond ±20 mHz)
2. **Droop response activates** (instantaneous, primary control — see [[Droop Control]])
3. **aFRR calculates target** (centralized, secondary control)
4. **VPP dispatches resources** using [[Multi-Objective Dispatch]] weights
5. **Frequency restores** to 50 Hz
6. **aFRR ramps down** as deadband is re-entered

## Activation Conditions

| Condition | Threshold | Response |
|-----------|-----------|----------|
| Frequency deviation | > ±20 mHz | aFRR activates |
| SoC too low | < 10% | Resource excluded from upward flexibility |
| SoC too high | > 90% | Resource excluded from downward flexibility |
| Resource disabled | enabled = false | Excluded from dispatch |

## Revenue

aFRR is a revenue-generating ancillary service:
- **Capacity payment:** Paid for being available (€/MW-h of reserved capacity)
- **Energy payment:** Paid for actual energy delivered (€/MWh)
- **Penalty:** Paid for non-delivery (if resource fails to respond)

See [[VPP Revenue Streams]] for pricing details.

## Relationships

- **Calculated by:** [[VPP Orchestrator]]
- **Dispatched via:** [[Multi-Objective Dispatch]]
- **Triggered by:** [[Frequency Regulator]]
- **Primary control:** [[Droop Control]]
- **Revenue from:** [[VPP Revenue Streams]]

## Known Issues

- aFRR gain (10 MW/Hz) is simulation-scaled — real TSO values differ
- 15-minute dispatch interval is slow — European aFRR targets 5 minutes
- SoC limits may prevent full response during sustained deviations
- No distinction between aFRR-up and aFRR-down pricing in simulator
