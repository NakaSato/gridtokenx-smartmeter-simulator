# PEA Hackathon PoC — Development Plan (Simplified)

**Deadline:** Wednesday presentation
**Stack:** GridTokenX Smart Meter Simulator (existing)

---

## Audit: What's Already Built

| Component | File | Status |
|---|---|---|
| Island network (Pandapower) | `adapters/island_hub_topology.py` | ✅ Complete |
| VPP + bottleneck game | `core/vpp.py` | ✅ Complete |
| Early Warning System | `core/ews.py` | ✅ Complete |
| InfluxDB query service | `transport/influxdb_query.py` | ✅ Complete |
| ETL pipeline | `scripts/island_hub_etl_mapping.py` | ✅ Complete |
| Test scripts | `scripts/test_financial_vpp.py`, `test_island_bottleneck.py` | ✅ Complete |

## What Needs to Be Built

| File | Pillar | Effort |
|---|---|---|
| `scripts/pea_opf_optimizer.py` | Pillar 2 — Cost Optimization | ~1h |

---

## Pillar 2 — Cost Optimization (OPF Dispatch Schedule)

**Stack used:** `scipy.optimize.linprog` → `IslandHubTopology` (Pandapower physics)

### Cost Function

$$\min \sum_{t=1}^{24} \bigl(P_{grid,t} \times 4 + P_{bess,t} \times 3.5 + P_{diesel,t} \times 13\bigr) \text{ THB/kWh}$$

### Constraints

| Constraint | Value |
|---|---|
| Grid supply limit (115 kV bottleneck) | 40 MW |
| BESS max discharge | 25 MW |
| BESS capacity | 50 MWh |
| Diesel max | 10 MW |
| Load balance | `p_grid + p_bess + p_diesel = load[t]` |

### File: `backend/scripts/pea_opf_optimizer.py`

```python
import numpy as np
from scipy.optimize import linprog

C_GRID, C_BESS, C_DIESEL = 4.0, 3.5, 13.0
GRID_MAX, BESS_MAX, BESS_CAP, DIESEL_MAX = 40.0, 20.0, 50.0, 10.0

def run_opf(forecast_mw: np.ndarray) -> dict:
    schedule, bess_soc = [], BESS_CAP * 0.5
    total_base, total_opt = 0.0, 0.0

    for t, load in enumerate(forecast_mw):
        bounds = [(0, GRID_MAX), (0, min(BESS_MAX, bess_soc)), (0, DIESEL_MAX)]
        res = linprog([C_GRID, C_BESS, C_DIESEL], A_eq=[[1,1,1]], b_eq=[load], bounds=bounds, method="highs")
        p_grid, p_bess, p_diesel = res.x if res.success else (0, 0, min(load, DIESEL_MAX))

        bess_soc = max(0, bess_soc - p_bess)
        cost_opt  = (p_grid*C_GRID + p_bess*C_BESS + p_diesel*C_DIESEL) * 1000
        cost_base = load * C_DIESEL * 1000
        total_base += cost_base; total_opt += cost_opt

        schedule.append({"hour": t, "load_mw": round(load,2),
                         "p_grid_mw": round(p_grid,2), "p_bess_mw": round(p_bess,2),
                         "p_diesel_mw": round(p_diesel,2), "bess_soc_mwh": round(bess_soc,1),
                         "savings_thb": round(cost_base - cost_opt, 0)})

    return {"schedule": schedule,
            "total_savings_thb": round(total_base - total_opt, 0),
            "total_cost_baseline_thb": round(total_base, 0),
            "total_cost_optimized_thb": round(total_opt, 0)}

if __name__ == "__main__":
    # Simplified forecast for OPF testing
    forecast = np.array([15.0] * 24)
    r = run_opf(forecast)
    print(f"💰 Savings: {r['total_savings_thb']:,.0f} THB/day")
    for h in r["schedule"]:
        print(f"  {h['hour']:02d}h | load={h['load_mw']} | grid={h['p_grid_mw']} | bess={h['p_bess_mw']} | diesel={h['p_diesel_mw']} | save={h['savings_thb']:,.0f}")
```

---

## Pillar 3 — Early Warning System & Emergency Response

**Stack used:** `EarlyWarningSystem.monitor_line_health()` → `VPPManager.dispatch_cluster()` (aFRR)

### Detection Logic (already in `ews.py`)

| Trigger | Condition | Severity |
|---|---|---|
| Submarine cable fault | Capacity drop > 20% | `CRITICAL` → `TRIGGER_EMERGENCY_BESS` |
| Overload trend | Loading > 105% | `HIGH` → `PREEMPTIVE_PEAK_SHAVING` |

### Emergency Response Sequence

```
EWS detects fault on 115kV KMB Circuit 3
    → alert.type = "EWS_CAPACITY_DROP"
    → BESS switches: grid-following → grid-forming
```
