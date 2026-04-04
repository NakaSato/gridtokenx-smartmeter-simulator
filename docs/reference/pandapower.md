# Pandapower Integration Guide

## Overview

Guide for integrating pandapower with the Smart Meter Simulator for grid modeling and state estimation.

## Quick Start

### Create Simple Network

```python
import pandapower as pp
from smart_meter_simulator.adapters import PandapowerAdapter, TopologyBuilder

# Build network
builder = TopologyBuilder()
net = builder.build_radial_network(num_buses=5)

# Run power flow
pp.runpp(net)

# View results
print(net.res_bus.vm_pu)
```

### Add Measurements

```python
from smart_meter_simulator.adapters import PandapowerAdapter

adapter = PandapowerAdapter()
measurements = adapter.create_measurement_table(net, meters)
```

### Run State Estimation

```python
from smart_meter_simulator.adapters import StateEstimator

estimator = StateEstimator()
results = estimator.run_estimation(net)
print(f"Converged: {results.converged}")
```

## Meter Types

### Residential Meter

```python
{
    "meter_type": "Residential",
    "accuracy_class": "CLASS_2_0",  # ±2.0%
    "channels": {"p", "q", "v"}
}
```

### Solar Prosumer

```python
{
    "meter_type": "Solar Prosumer",
    "accuracy_class": "CLASS_1_0",  # ±1.0%
    "has_solar": True,
    "channels": {"p", "q", "v"}
}
```

### Battery Storage

```python
{
    "meter_type": "Battery Storage",
    "accuracy_class": "CLASS_0_5",  # ±0.5%
    "has_battery": True,
    "channels": {"p", "q", "v", "soc"}
}
```

## Measurement Mapping

### Meter to Pandapower

| Meter Channel | Pandapower Measurement |
|---------------|----------------------|
| P (active) | `meas_type="p"` |
| Q (reactive) | `meas_type="q"` |
| V (voltage) | `meas_type="v"`, `element_type="bus"` |
| SOC | Custom field (not in SE) |

### Sign Convention

```python
# Load (consumption positive)
pp.create_load(net, bus=0, p_mw=0.05)  # Import

# SGen (generation positive)
pp.create_sgen(net, bus=0, p_mw=0.08)  # Export

# Net power at bus
P_net = P_gen - P_load  # = 0.08 - 0.05 = 0.03 MW export
```

## Accuracy Classes

### ANSI C12.20

| Class | Error | Std Dev Formula | Use Case |
|-------|-------|----------------|----------|
| 0.2 | ±0.2% | σ = 0.002 × \|V\| / 3 | Substation |
| 0.5 | ±0.5% | σ = 0.005 × \|V\| / 3 | Feeder |
| 1.0 | ±1.0% | σ = 0.01 × \|V\| / 3 | Commercial |
| 2.0 | ±2.0% | σ = 0.02 × \|V\| / 3 | Residential |

### Example

```python
# Residential meter (CLASS_2_0) with 240V reading
accuracy_class = 2.0
voltage = 240.0
sigma = (accuracy_class / 300.0) * voltage  # = 1.6V
```

## State Estimation

### WLS Algorithm

```python
estimator = StateEstimator()
results = estimator.run_estimation(net)

# Results
print(f"Converged: {results.converged}")
print(f"Iterations: {results.iterations}")
print(f"Chi-squared: {results.chi_squared}")
```

### Bad Data Detection

```python
# Detect bad data
bad_data = estimator.detect_bad_data(net)
print(f"Bad measurements: {bad_data}")

# Run with sanitization
results = estimator.run_sanitized_estimation(net)
print(f"Removed: {results.bad_data_detected}")
```

## Topology Examples

### Radial Network

```python
builder = TopologyBuilder()
net = builder.build_radial_network(num_buses=5)

# Structure:
# Bus 0 (Substation) → Bus 1 → Bus 2 → Bus 3 → Bus 4
```

### Multi-Feeder

```python
net = builder.build_feeder_network(num_feeders=2, buses_per_feeder=3)

# Structure:
#              Feeder A: Bus 1 → Bus 2 → Bus 3
# Substation (Bus 0) →
#              Feeder B: Bus 4 → Bus 5 → Bus 6
```

## Common Operations

### Get Measurement Table

```python
adapter = PandapowerAdapter()
measurements = adapter.get_measurements(net)
print(measurements)
```

### Update Load Profile

```python
# Update load at bus 1
net.load.loc[0, 'p_mw'] = 0.1  # New active power
net.load.loc[0, 'q_mvar'] = 0.02  # New reactive power

# Re-run power flow
pp.runpp(net)
```

### Add Solar Generation

```python
# Add static generator at bus 1
pp.create_sgen(net, bus=1, p_mw=0.1, q_mvar=0.0, name="Solar")
```

## Troubleshooting

### Power Flow Divergence

```python
# Try Iwamoto algorithm
pp.runpp(net, algorithm="iwamoto")

# Or check network parameters
print(net.line)  # Check R/X ratios
```

### State Estimation Fails

```python
# Check observability
observable = estimator.check_observability(net)
print(f"Observable: {observable}")

# Add pseudo-measurements if not observable
pp.create_measurement(net, "p", "bus", value=0.0, std_dev=1.0, element=0)
```

### Measurement Errors

```python
# Check measurement table
print(net.measurement)

# Verify std_dev values (should be > 0)
assert all(net.measurement['std_dev'] > 0)
```

## Resources

- [Pandapower Documentation](https://pandapower.readthedocs.io/)
- [Technical Reference](pandapower-technical.md)
- [Meter Specification](../meter_spec.md)
