# Pandapower Smart Grid Simulation Guide

## Overview

**What:** Simulate prosumer-based distribution grids (consumers with local generation) and generate synthetic Smart Meter data.

**Why:** Test grid algorithms, validate state estimation, and generate training data for Smart Grid analytics without real-world risk.

**Tools:** pandapower (power flow) + pvlib (PV generation) + pandas (data handling).

---

## Core Concepts: Modeling Prosumers

### Architecture
A prosumer = consumer + producer. In pandapower, model as **two separate elements on the same bus**:

1. **Load element** (`create_load()`) — Consumption
   - Positive P = power drawn from grid
   - Sign convention: Load Reference System

2. **Static Generator element** (`create_sgen()`) — Generation (PV, etc.)
   - Positive P = power injected to grid
   - **Preferred for DERs** (not `gen` which is for large plants)
   - Sign convention: Generator Reference System

### Net Power at Bus
The solver computes:
$$P_{net} = P_{sgen} - P_{load}$$

- **Night (0.005 MW load, 0 MW gen):** $P_{net} = -0.005$ MW → Power imports, voltage drops
- **Noon (0.010 MW gen, 0.002 MW load):** $P_{net} = +0.008$ MW → Power exports, voltage rises (reverse flow)

---

## Grid Elements Quick Reference

| Element | Purpose | Key Params | Notes |
|---------|---------|-----------|-------|
| **Bus** | Network node | `vn_kv` (nominal voltage) | Kirchhoff's Current Law enforced here |
| **Line** | Distribution feeder | `length_km`, `r_ohm_per_km`, `x_ohm_per_km` | Outputs `loading_percent` = thermal utilization |
| **Transformer** | Voltage conversion | `vn_hv_kv`, `vn_lv_kv`, `sn_mva` | Handles substation to feeder coupling |
| **Load** | Consumption | `p_mw`, `q_mvar` | Positive P = consumption |
| **Sgen** | Generation (PV, battery) | `p_mw`, `q_mvar` | Positive P = injection to grid |

---

## Physics-Based Profile Generation

### Consumption: Standard Load Profiles (SLP)

Use BDEW H0 profile (German standard) or equivalent for your region:
- Varies by season (winter heating, summer cooling)
- Varies by day type (weekday vs. weekend)
- Includes time-of-use peaks (e.g., 19:00 dinner cook)
- Formula: `P_load(t) = ScaleFactor × Profile(t, season, day_type)`

**Libraries:**
- `demandlib` — BDEW profile generation
- Or read from pandapower tutorial datasets

### Generation: Photovoltaic (PV)

Use `pvlib` to model physics-based PV output:

1. **Irradiance**: Convert weather data (Global Horizontal → Plane of Array)
2. **Temperature**: Cell efficiency drops ~0.4% per °C above STC
3. **Inverter**: AC power limited by inverter rating (clipping above `P_AC_max`)

**Key insight:** Simple scaling models miss clipping and cloud transients that appear in real Smart Meter data.

Example workflow:
```python
import pvlib
import pandas as pd

# Get solar position and irradiance
location = pvlib.location.Location(latitude=48.1, longitude=11.6, name='Munich')
times = pd.date_range('2024-06-21 06:00', '2024-06-21 18:00', freq='15min', tz='UTC')
solar_position = location.get_solarposition(times)
irradiance = location.get_clearsky(times)  # or use actual weather file

# Model PV output (with temperature and inverter limits)
# → feed into pandapower sgen with timeseries
```

---

## Time-Series Simulation Loop

### Basic Architecture
```
for each timestep t:
  1. Read profiles: fetch P, Q for load & sgen from DataFrames
  2. Update elements: set load[i].p_mw, sgen[j].p_mw
  3. Solve: pandapower.runpp() → Newton-Raphson power flow
  4. Log: OutputWriter saves voltages, currents, line loading, etc.
  5. Step: t → t+1
```

### Implementation Outline

```python
import pandapower as pp

# Create network
net = pp.create_empty_network()
# ... add buses, lines, transformers, loads, sgens ...

# Create profiles (pandas DataFrames, index=timestamps, columns=element indices)
load_profile_df = pd.DataFrame(data, columns=[0, 1, 2])  # kW for loads 0, 1, 2
gen_profile_df = pd.DataFrame(data, columns=[0, 1])      # kW for sgens 0, 1

# Set up time series
from pandapower.timeseries import DFData, ConstControl, OutputWriter, run_timeseries

ds = DFData(load_profile_df)  # DataSource wrapping load profile
run_timeseries(net, time_steps=range(len(load_profile_df)))
  # Internal loop calls runpp() for each step
```

### Managing Convergence Issues

Power flow may fail to converge at extreme conditions (high voltage, high reverse flow).

**Diagnosis:**
- Check `net.timeseries.powerflow_failed` for failed timesteps
- Often indicates physical infeasibility (overvoltage violation)

**Mitigation:**
- Relax tolerances: `pp.runpp(net, tolerance_mva=1e-3)`
- Use DC initialization: `pp.runpp(net, init='dc')`
- Non-convergence can be a **valid finding** (constraint violation)

---

## Synthetic Smart Meter Data

### Configurable Outputs

The `OutputWriter` logs pandapower internal results. Standard meter readings:

| Quantity | Source Table | Variable | Unit | Use Case |
|----------|--------------|----------|------|----------|
| Voltage | `res_bus` | `vm_pu` | p.u. | Voltage regulation, EN 50160 compliance (±10%) |
| Load Power | `res_load` | `p_mw` | MW | Gross consumption |
| Gen Power | `res_sgen` | `p_mw` | MW | Gross generation |
| Net Flow | Calculated | `p_sgen - p_load` | MW | Bidirectional flow; seen by utility meter |
| Reactive Power | `res_load/sgen` | `q_mvar` | MVAr | Power factor, inverter settings |
| Line Loading | `res_line` | `loading_percent` | % | Thermal congestion indicator |

### Injecting Measurement Noise

Real meters have tolerance classes (accuracy). Simulate this with Gaussian noise:

$$V_{measured} = V_{true} + \epsilon_V, \quad \epsilon_V \sim \mathcal{N}(0, \sigma_V^2)$$
$$P_{measured} = P_{true} + \epsilon_P, \quad \epsilon_P \sim \mathcal{N}(0, \sigma_P^2)$$

For Class 1 meter (1% error): $\sigma = 1\% / 3 \approx 0.0033$ p.u.

```python
import numpy as np

# Post-process OutputWriter results
voltage = results['res_bus']['vm_pu']
noise_std = 0.0033  # Class 1 meter
voltage_noisy = voltage + np.random.normal(0, noise_std, size=voltage.shape)
```

### Handling Data Artifacts

- **Missing data:** Randomly set rows to NaN to simulate communication failures
- **Integration window:** Real meters integrate over 15 min, not instantaneous values
- **Quantization:** Discretize to meter reporting precision (often 0.01 kWh)

---

## Sign Convention Reference (Critical!)

| Element | Attribute | P > 0 | P < 0 | Note |
|---------|-----------|-------|-------|------|
| Load | `p_mw` | Consumption | Generation (non-standard) | Load Reference |
| Sgen | `p_mw` | Injection (generation) | Withdrawal (battery charging) | Generator Reference |
| Gen | `p_mw` | Injection | Withdrawal | Generator Reference |
| Bus (result) | `p_mw` | Net injection | Net withdrawal | Solver result |

**⚠️ Always verify your pandapower versionscripts/verify_phase10_vpp.py* Historical versions used different conventions.

---

## Power Flow Solver Basics

pandapower uses **Newton-Raphson** method to solve the non-linear power flow equations:

**Simplified insight:**
- Input: Loads (P, Q demanded) and generators (P, Q supplied)
- Unknown: Voltage magnitude and angle at each bus
- Solver: Iteratively updates voltages until Kirchhoff's laws are satisfied
- Output: Voltages → derive currents, line loading, losses

**For high prosumer penetration:**
- Radial feeders with reverse flow can cause ill-conditioned Jacobian
- pandapower handles this with robust initialization (e.g., DC power flow pre-solve)
- Convergence failure = potential physical constraint violation (voltage swell, thermal limit)

---

## Case Study Example: High-PV Scenario

**Setup:**
- Use SimBench dataset (validated German LV grid)
- Add 66% PV penetration (10 of 15 houses)
- PV: 5–10 kWp each, BDEW H0 consumption profiles

**Expected Results:**

| Time | Load | Gen | Net | Voltage | Issue |
|------|------|-----|-----|---------|-------|
| 03:00 | 0.45 kW | 0 kW | +0.45 | 0.995 p.u. | Normal import |
| 13:00 | 0.50 kW | 8.5 kW | -8.0 | 1.065 p.u. ❌ | Voltage swell (limit 1.05) |
| 19:00 | 2.5 kW | 0.1 kW | +2.4 | 0.980 p.u. | Normal import |

**Key Finding:** Reverse power flow at 13:00 violates voltage limits. **Mitigation:** Implement Volt-Var control on inverters to absorb reactive power during peak generation.

---

## Validation with State Estimation

Once synthetic Smart Meter data is generated (with noise), validate the simulation's utility:

1. Feed noisy measurements → pandapower State Estimator
2. Recover voltage angles and magnitudes
3. Compare against true solver results

**Purpose:** Verify that your synthetic data, when processed by real SMG algorithms, yields acceptable accuracy. This closes the loop: Grid Physics → Synthetic Data → State Estimator → Recovered State.

---

## Key Functions Reference

| Function | Module | Purpose |
|----------|--------|---------|
| `create_load()` | `pandapower.create` | Add load element |
| `create_sgen()` | `pandapower.create` | Add static generator (PV) |
| `runpp()` | `pandapower.power_flow` | Solve power flow |
| `run_timeseries()` | `pandapower.timeseries` | Execute time-stepping loop |
| `DFData` | `pandapower.timeseries` | Wrap profile DataFrames |
| `ConstControl` | `pandapower.control` | Update element parameters each timestep |
| `OutputWriter` | `pandapower.timeseries` | Log results to disk/memory |
| `estimate()` | `pandapower.estimation` | State Estimation |

---

## Tips for Implementation

1. **Always use realistic profiles.** Don't use constant loads; they hide important dynamics.
2. **Verify sign conventions in your pandapower version** before running simulations.
3. **Test convergence early.** Run a few timesteps to catch topology/control issues.
4. **Log line loading and voltages.** These reveal constraint violations before failures.
5. **Inject noise that matches meter accuracy.** Unrealistic noise makes training data unhelpful.
6. **Validate against observed data if available.** Compare synthetic vs. real Smart Meter readings on same grid.
