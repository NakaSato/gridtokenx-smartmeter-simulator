# AI Forecasting Quick Start Guide

## Prerequisites

1. Start the infrastructure:
```bash
docker compose up -d
```

2. Start the simulator:
```bash
cd backend
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

## Basic Usage

### 1. Get 24-Hour Dual-Target Forecast

This is the core AI forecasting endpoint that predicts both Load_Tao and Capacity_115kV.

```bash
curl "http://localhost:8082/api/v1/forecast/dual-target?current_load_kw=15000"
```

**What it returns:**
- 24 hourly predictions for Load_Tao (Yellow Line)
- 24 hourly predictions for Capacity_115kV (Blue Line)
- Delta calculation (Capacity - Load)
- Constraint flags (when capacity < load)
- Summary metrics

### 2. Analyze Constraints

Check if BESS dispatch is required and calculate requirements.

```bash
curl "http://localhost:8082/api/v1/forecast/constraints?current_load_kw=15000"
```

**What it returns:**
- BESS requirement status
- Peak power requirement (kW)
- Total energy requirement (kWh)
- Recommended BESS capacity with buffer
- List of critical hours

### 3. Get Demographic Metrics

Understand the population-driven load calculations.

```bash
curl "http://localhost:8082/api/v1/forecast/demographics"
```

**What it returns:**
- Koh Tao Daily Active Population (DAP)
- Tourist active count
- Base load calculations
- Koh Phangan metrics including Full Moon effect

### 4. Get Optimal Dispatch Schedule

Calculate cost-optimized 24-hour dispatch using OPF.

```bash
curl "http://localhost:8082/api/v1/optimize/schedule?current_load_mw=15.0"
```

**What it returns:**
- Hourly dispatch schedule (Grid, BESS, Diesel)
- BESS State of Charge tracking
- Cost savings per hour
- Total cost comparison (baseline vs optimized)

### 5. Calculate Cost Savings

Get financial impact of optimization.

```bash
curl "http://localhost:8082/api/v1/optimize/savings?current_load_mw=15.0"
```

**What it returns:**
- Daily, monthly, annual savings (THB)
- Cost reduction percentage
- Baseline vs optimized costs

## Python Examples

### Example 1: Get Forecast and Analyze Constraints

```python
import requests

BASE_URL = "http://localhost:8082/api/v1"

# Get dual-target forecast
response = requests.get(f"{BASE_URL}/forecast/dual-target", params={
    "current_load_kw": 15000.0
})
forecast = response.json()

print(f"Constraint Hours: {forecast['summary']['constraint_hours']}/24")
print(f"Peak Load: {forecast['summary']['peak_load_kw']} kW")
print(f"Min Capacity: {forecast['summary']['min_capacity_kw']} kW")

# Analyze constraints
response = requests.get(f"{BASE_URL}/forecast/constraints", params={
    "current_load_kw": 15000.0
})
constraints = response.json()

if constraints['bess_required']:
    reqs = constraints['bess_requirements']
    print(f"\nBESS Requirements:")
    print(f"  Peak Power: {reqs['peak_power_kw']} kW")
    print(f"  Total Energy: {reqs['total_energy_kwh']} kWh")
    print(f"  Recommended Capacity: {reqs['recommended_capacity_kwh']} kWh")
```

### Example 2: Calculate Cost Savings

```python
import requests

BASE_URL = "http://localhost:8082/api/v1"

response = requests.get(f"{BASE_URL}/optimize/savings", params={
    "node_id": "SAMUI-HUB-01",
    "current_load_mw": 15.0
})
savings = response.json()

print(f"Daily Savings: {savings['daily_savings_thb']:,.0f} THB")
print(f"Monthly Savings: {savings['monthly_savings_thb']:,.0f} THB")
print(f"Annual Savings: {savings['annual_savings_thb']:,.0f} THB")
print(f"Cost Reduction: {savings['cost_reduction_pct']}%")
```

### Example 3: Monitor Demographics

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8082/api/v1"

# Check demographics for next 7 days
for i in range(7):
    date = (datetime.now() + timedelta(days=i)).date().isoformat()
    response = requests.get(f"{BASE_URL}/forecast/demographics", params={
        "target_date": date
    })
    demo = response.json()
    
    print(f"\n{date}:")
    print(f"  Koh Tao DAP: {demo['koh_tao']['daily_active_population']:,}")
    print(f"  Koh Tao Load: {demo['koh_tao']['base_load_kw']:,.2f} kW")
    print(f"  Koh Phangan Load: {demo['koh_phangan']['base_load_kw']:,.2f} kW")
    if demo['koh_phangan']['full_moon_window']:
        print(f"  🌕 FULL MOON PARTY WINDOW!")
```

### Example 4: Simulate Grid Incident

```python
import requests

BASE_URL = "http://localhost:8082/api/v1"

# Simulate submarine cable overload
response = requests.post(f"{BASE_URL}/ews/simulate", json={
    "line_id": "115kV KMB Circuit 3",
    "line_capacity_mw": 70.0,
    "loading_pct": 98.0
})
incident = response.json()

if incident['alert']:
    alert = incident['alert']
    print(f"Alert Type: {alert['type']}")
    print(f"Severity: {alert['severity']}")
    print(f"Action: {alert['recommended_action']}")
    
    if 'emergency_response' in incident:
        resp = incident['emergency_response']
        print(f"\nEmergency Response:")
        print(f"  BESS Dispatch: {resp['bess_dispatch_mw']} MW")
        print(f"  Diesel Spinup: {resp['diesel_spinup_mw']} MW")
        print(f"  aFRR Triggered: {resp['afrr_triggered']}")
```

## Testing the Implementation

Run the comprehensive test suite:

```bash
cd backend
python3 scripts/test_ai_implementation.py
```

This will test:
- Feature engineering pipeline
- AI forecasting engine
- Demographic metrics calculation
- AI service integration

## Understanding the Output

### Constraint Active Flag

When `constraint_active: true`, it means:
- Capacity_115kV < Load_Tao
- BESS discharge is required
- Grid is at risk without intervention

### Delta Value

- **Positive Delta**: Capacity exceeds load (safe)
- **Negative Delta**: Load exceeds capacity (constraint violation)
- **Magnitude**: Amount of BESS dispatch required (kW)

### Thermal Derating

Shows how much the submarine cable capacity has been reduced due to:
- Heat accumulation from high upstream load
- High ambient sea temperatures
- Insufficient cooling time

## Common Use Cases

### Use Case 1: Daily Operations Planning

```bash
# Morning: Get today's forecast
curl "http://localhost:8082/api/v1/forecast/dual-target?current_load_kw=15000"

# Check if BESS dispatch needed
curl "http://localhost:8082/api/v1/forecast/constraints?current_load_kw=15000"

# Get optimal dispatch schedule
curl "http://localhost:8082/api/v1/optimize/schedule?current_load_mw=15.0"
```

### Use Case 2: Financial Analysis

```bash
# Calculate potential savings
curl "http://localhost:8082/api/v1/optimize/savings?current_load_mw=15.0"

# Compare different load scenarios
curl "http://localhost:8082/api/v1/optimize/savings?current_load_mw=20.0"
```

### Use Case 3: Tourism Impact Analysis

```bash
# Check demographics for high season
curl "http://localhost:8082/api/v1/forecast/demographics?target_date=2026-12-25"

# Check Full Moon Party impact
curl "http://localhost:8082/api/v1/forecast/demographics?target_date=2026-04-23"
```

### Use Case 4: Emergency Response Testing

```bash
# Simulate cable fault
curl -X POST "http://localhost:8082/api/v1/ews/simulate" \
  -H "Content-Type: application/json" \
  -d '{"line_id": "115kV KMB Circuit 3", "line_capacity_mw": 70.0, "loading_pct": 110.0}'

# Check EWS status
curl "http://localhost:8082/api/v1/ews/status"

# Reset after drill
curl -X POST "http://localhost:8082/api/v1/ews/reset"
```

## Next Steps

1. **Integrate with Dashboard**: Use these endpoints to build real-time monitoring dashboards
2. **Automate Dispatch**: Connect to BESS controllers for automated dispatch
3. **Historical Analysis**: Store forecasts in InfluxDB for accuracy tracking
4. **Model Training**: Collect real data and train LightGBM models using `/forecast/train`

## Troubleshooting

### Issue: Negative Capacity Values

This is expected when upstream load (Samui + Phangan) exceeds the submarine cable's base capacity. It indicates severe grid stress requiring immediate BESS intervention.

### Issue: All Hours Show Constraints

Check the `current_load_kw` parameter. If set too high, it will trigger constraints across all hours. Typical values: 10,000-20,000 kW.

### Issue: MAPE Too High

The edge forecasting engine uses rule-based models by default. Train a LightGBM model using:
```bash
curl -X POST "http://localhost:8082/api/v1/forecast/train"
```

## API Documentation

For complete API reference, see [API_AI_FORECASTING.md](./API_AI_FORECASTING.md)
