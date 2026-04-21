# Forecast Cost & Economic Reporting

This document describes the cost-optimized reporting mechanisms used for grid operations and financial oversight.

## 1. Forecast Cost Reporting

The `OptimizationEngine` generates a 24-hour **Recommended Schedule** that balances load requirements with the Levelized Cost of Energy (LCOE) from different sources.

### Cost Parameters (Standardized)
| Source | Cost (THB/kWh) | Strategic Priority |
|--------|----------------|--------------------|
| **Grid Import** | 2.50 | 1 (Primary) |
| **BESS (Battery)** | 3.50 | 2 (Constraint Mitigation) |
| **Solar (PV)** | 0.00 | 0 (Always First) |
| **Diesel Gen** | 13.00 | 3 (Last Resort) |

### Forecast Report Structure
Every hour, the AI Forecaster generates a report containing the following cost-related fields:

```json
{
  "timestamp": "2026-04-19T14:00:00Z",
  "forecast_summary": {
    "total_demand_mw": 8.5,
    "total_pv_gen_mw": 1.2,
    "net_deficit_mw": 7.3
  },
  "recommended_schedule": [
    {
      "hour_offset": 1,
      "p_grid_mw": 5.0,
      "p_bess_mw": 2.3,
      "p_diesel_mw": 0.0,
      "cost_thb": 20550.00,
      "savings_vs_diesel_thb": 21850.00
    }
  ],
  "total_24h_operational_cost_thb": 452000.50
}
```

### KPI: "Savings vs. Legacy"
A key metric reported to the dashboard is the **Avoided Cost**. This is calculated as:
$$\text{Savings} = P_{BESS} \times (\text{Cost}_{Diesel} - \text{Cost}_{BESS})$$
This explicitly shows the economic value of the AI-driven battery dispatch in avoiding expensive diesel generation on the islands.

## 2. Optimization Integration
-   **Optimization Trigger**: The `SimulationEngine` calls `calculate_cost_optimized_schedule` every cycle to ensure the grid is always operating at the lowest marginal cost while respecting safety constraints.
