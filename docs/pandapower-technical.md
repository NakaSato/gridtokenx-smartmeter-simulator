# Pandapower Integration - Deep Technical Reference

This document provides an in-depth technical reference for the pandapower integration in the Smart Meter Simulator, covering state estimation, topology modeling, and measurement theory.

## Table of Contents

1. [Theoretical Foundations](#1-theoretical-foundations)
2. [Pandapower Network Architecture](#2-pandapower-network-architecture)
3. [Measurement Table Specification](#3-measurement-table-specification)
4. [Accuracy Class and Standard Deviation](#4-accuracy-class-and-standard-deviation)
5. [Topology Builder](#5-topology-builder)
6. [State Estimation](#6-state-estimation)
7. [Bad Data Detection](#7-bad-data-detection)
8. [Advanced Topics](#8-advanced-topics)

---

## 1. Theoretical Foundations

### 1.1 Physics vs. Cyber-Physical Modeling

The simulator implements a two-layer architecture that distinguishes between physical truth and measured values:

**Ground Truth Layer**: The "true" state from power flow calculation ($\mathbf{x}_{true}$), representing actual voltage magnitudes and angles at every bus.

**Measurement Layer**: The reported value $z$ corrupted by sensor inaccuracy and noise:

$$z = h(\mathbf{x}_{true}) + \epsilon$$

Where:
- $h(\cdot)$ is the measurement function (e.g., extracting voltage at a bus)
- $\epsilon$ is the error term

### 1.2 Measurement Uncertainty Model

The error term follows a Gaussian distribution:

$$\epsilon \sim \mathcal{N}(0, \sigma^2)$$

This assumption is foundational for **Weighted Least Squares (WLS)** state estimation, where the weight assigned to a measurement is the inverse of its variance:

$$W = \frac{1}{\sigma^2}$$

### 1.3 Real-World Error Sources

Beyond Gaussian noise, real measurements can include:

| Error Type | Description | Mitigation |
|------------|-------------|------------|
| **Systematic (Bias)** | Calibration drift in VT/CT | Periodic recalibration |
| **Gross Errors (Bad Data)** | Faulty electronics, packet corruption | Chi-squared detection |
| **Synchronization Errors** | Time skew between meters | NTP synchronization |

---

## 2. Pandapower Network Architecture

### 2.1 Tabular Data Structure

Pandapower organizes grid data into separate DataFrames:

```python
net.bus        # Bus definitions
net.line       # Line connections
net.load       # Load elements
net.sgen       # Static generators (PV)
net.trafo      # Transformers
net.ext_grid   # External grid (slack bus)
net.measurement # Measurement data for state estimation
```

### 2.2 Element-Based vs. Bus-Branch Models

**Important**: Pandapower maintains individual `load` and `sgen` elements rather than aggregating at bus level.

```
Bus 5 (Distribution Pillar)
├── Load_House_1 (element_index=0)
├── Load_House_2 (element_index=1)
├── Load_House_3 (element_index=2)
└── Sgen_PV_1 (element_index=0)
```

**Correct Modeling**:
- Residential smart meter → measures `load` element (`element_type='load'`)
- Voltage measurement → always at `bus` (`element_type='bus'`)

### 2.3 Sign Conventions

Critical for correct power flow:

| Element | Positive P/Q | Frame |
|---------|--------------|-------|
| `load` | Consumption (power out of grid) | Load Reference |
| `sgen` | Generation (power into grid) | Generator Reference |
| Bus injection | Generation positive, load negative | Generator Reference |

```python
# Consumer using 2 kW
net.load.p_mw = 0.002  # Positive

# If modeled as bus injection measurement
measurement.value = -0.002  # Negative (load = negative injection)
```

---

## 3. Measurement Table Specification

### 3.1 Schema Definition

The `net.measurement` DataFrame schema:

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Unique identifier (e.g., "M001_V") |
| `measurement_type` | str | Type: `v`, `p`, `q`, `i`, `ia`, `va` |
| `element_type` | str | Element: `bus`, `load`, `sgen`, `line`, `trafo` |
| `element` | int | Index in respective element table |
| `value` | float | Measured value |
| `std_dev` | float | Standard deviation |
| `side` | str | Branch side: `from`, `to`, or `None` |

### 3.2 Measurement Types

| Type | Description | Unit | Element Types |
|------|-------------|------|---------------|
| `v` | Voltage magnitude | p.u. | `bus` |
| `p` | Active power | MW | `load`, `sgen`, `line`, `trafo` |
| `q` | Reactive power | MVar | `load`, `sgen`, `line`, `trafo` |
| `i` | Current magnitude | kA | `line`, `trafo` |
| `ia` | Current angle | degree | `line`, `trafo` |
| `va` | Voltage angle | degree | `bus` |

### 3.3 Creating Measurements Programmatically

```python
import pandapower as pp

# Create measurement via pandapower API
pp.create_measurement(
    net,
    meas_type="v",
    element_type="bus",
    element=5,
    value=1.02,
    std_dev=0.002,
    name="M001_V"
)

# Or using MeasurementTableBuilder
from app.adapters.pandapower_adapter import MeasurementTableBuilder
from app.config import MeterType

builder = MeasurementTableBuilder(sigma_factor=3)
builder.add_voltage_measurement(
    meter_id="M001",
    bus_index=5,
    voltage_pu=1.02,
    meter_type=MeterType.RESIDENTIAL
)
```

---

## 4. Accuracy Class and Standard Deviation

### 4.1 ANSI C12.20 Accuracy Classes

| Class | Error Bound | Typical Application |
|-------|-------------|---------------------|
| CLASS_0_2 | ±0.2% | Substation meters, revenue metering |
| CLASS_0_5 | ±0.5% | Feeder head meters |
| CLASS_1_0 | ±1.0% | Commercial meters |
| CLASS_2_0 | ±2.0% | Residential meters |

### 4.2 Standard Deviation Derivation

Assuming error bound represents $3\sigma$ (99.7% confidence):

$$\sigma = \frac{\text{AccuracyClass}}{300} \times \text{NominalValue}$$

**Example**: Class 1.0 meter measuring 1.0 p.u. voltage:

$$\sigma_v = \frac{1.0}{300} \times 1.0 = 0.00333 \text{ p.u.}$$

### 4.3 Implementation

```python
class MeasurementTableBuilder:
    def __init__(self, sigma_factor: int = 3):
        """
        Args:
            sigma_factor: 3 = conservative (99.7%), 2 = standard (95%)
        """
        self.sigma_factor = sigma_factor
    
    def calculate_std_dev(self, accuracy_class: AccuracyClass, nominal_value: float) -> float:
        """
        Calculate σ from accuracy class.
        
        Formula: σ = (AccuracyClass / (100 × sigma_factor)) × NominalValue
        """
        accuracy_value = accuracy_class.value  # e.g., 0.02 for CLASS_2_0
        return (accuracy_value / (100 * self.sigma_factor)) * abs(nominal_value)
```

### 4.4 Measurement-Specific Multipliers

Different measurements have different uncertainty characteristics:

| Measurement | Multiplier | Rationale |
|-------------|------------|-----------|
| Voltage (V) | 1.0× | Base accuracy |
| Active Power (P) | 2.0× | CT/VT combined error |
| Reactive Power (Q) | 3.0× | Higher phase angle sensitivity |
| Current (I) | 1.5× | CT saturation effects |

```python
def add_active_power_measurement(self, ...):
    std_dev = self.calculate_std_dev(accuracy, power_mw) * 2.0  # 2× multiplier
```

---

## 5. Topology Builder

### 5.1 Network Structures

The `TopologyBuilder` supports multiple topology types:

```python
class NetworkTopology(Enum):
    RADIAL = "radial"    # Tree structure
    RING = "ring"        # Looped with redundancy
    MESH = "mesh"        # Fully connected
    FEEDER = "feeder"    # Multiple radial feeders
```

### 5.2 Voltage Levels

```python
class VoltageLevel(Enum):
    HV = "High Voltage"     # 110+ kV
    MV = "Medium Voltage"   # 1-35 kV
    LV = "Low Voltage"      # 0.23-0.4 kV
```

### 5.3 Building a Feeder Network

```python
from app.adapters.topology_builder import TopologyBuilder

builder = TopologyBuilder(network_name="Distribution Grid")

# Build multi-feeder network
net = builder.build_feeder_network(
    num_feeders=4,           # 4 radial feeders
    buses_per_feeder=10,     # 10 buses each
    voltage_kv=0.4,          # 400V LV network
    line_length_km=0.05,     # 50m between nodes
    substation_bus_id="Substation_01"
)

# Network structure:
# Substation_01 (ext_grid)
# ├── Feeder0_Bus0 ── Feeder0_Bus1 ── ... ── Feeder0_Bus9
# ├── Feeder1_Bus0 ── Feeder1_Bus1 ── ... ── Feeder1_Bus9
# ├── Feeder2_Bus0 ── Feeder2_Bus1 ── ... ── Feeder2_Bus9
# └── Feeder3_Bus0 ── Feeder3_Bus1 ── ... ── Feeder3_Bus9
```

### 5.4 Multi-Voltage Network

```python
net = builder.build_multi_voltage_network(
    hv_buses=1,           # 110 kV transmission
    mv_buses=3,           # 10 kV distribution per HV
    lv_buses_per_mv=5,    # 0.4 kV per MV bus
    hv_voltage_kv=110.0,
    mv_voltage_kv=10.0,
    lv_voltage_kv=0.4
)

# Network includes:
# - HV/MV transformers (10 MVA)
# - MV/LV transformers (400 kVA)
# - Appropriate line types per voltage level
```

### 5.5 Standard Line Types

| Voltage | Standard Type | Application |
|---------|---------------|-------------|
| LV | `NAYY 4x50 SE` | Residential underground |
| MV | `NA2XS2Y 1x185 RM/25 12/20 kV` | Primary distribution |
| HV | `N2XS(FL)2Y 1x120 RM/35 64/110 kV` | Transmission |

---

## 6. State Estimation

### 6.1 Algorithm Overview

The simulator uses **Weighted Least Squares (WLS)** state estimation:

$$\min_{\mathbf{x}} J(\mathbf{x}) = [\mathbf{z} - \mathbf{h}(\mathbf{x})]^T \mathbf{W} [\mathbf{z} - \mathbf{h}(\mathbf{x})]$$

Where:
- $\mathbf{z}$: Measurement vector
- $\mathbf{h}(\mathbf{x})$: Measurement function
- $\mathbf{W}$: Weight matrix ($W_{ii} = 1/\sigma_i^2$)

### 6.2 Available Algorithms

```python
class EstimationAlgorithm(Enum):
    WLS = "wls"                         # Standard Newton-Raphson WLS
    WLS_WITH_ZERO_CONSTRAINT = "wls_with_zero_constraint"
    LP = "lp"                           # Linear Programming
    OPT = "opt"                         # Optimization-based
```

### 6.3 Running State Estimation

```python
from app.adapters.state_estimator import StateEstimator, EstimationAlgorithm

estimator = StateEstimator(
    algorithm=EstimationAlgorithm.WLS,
    tolerance=1e-6,
    max_iterations=10
)

results = estimator.run_estimation(net, init="flat")

# Results structure
@dataclass
class EstimationResults:
    converged: bool                # Convergence status
    iterations: int                # Number of iterations
    residuals: pd.DataFrame        # Measurement residuals
    estimated_voltages: pd.DataFrame  # Bus voltage estimates
    bad_data_detected: List[str]   # Flagged measurements
    num_measurements: int
    chi2_statistic: float
    mean_absolute_error: float
    max_residual: float
    v_deviation_avg: float         # Avg |V - 1.0| p.u.
    total_losses_mw: float         # Grid losses
```

### 6.4 Initialization Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `flat` | V=1.0∠0° everywhere | Cold start, no prior info |
| `results` | Use previous results | Sequential estimation |
| `slack` | Use slack bus values | Known reference point |

### 6.5 Convergence Issues in Distribution Grids

Distribution networks have high R/X ratios that can cause convergence problems:

```python
# Auto-fallback mechanism
try:
    results = estimator.run_estimation(net, algorithm="wls")
except ConvergenceError:
    # Retry with Iwamoto (dampened Newton-Raphson)
    results = estimator.run_estimation(net, algorithm="iwamoto")
```

---

## 7. Bad Data Detection

### 7.1 Chi-Squared Test

Global hypothesis test for measurement quality:

$$\chi^2 = \sum_{i=1}^{m} \frac{(z_i - h_i(\hat{x}))^2}{\sigma_i^2}$$

If $\chi^2 > \chi^2_{\alpha, m-n}$, bad data is present (α = significance level, m = measurements, n = states).

```python
# Detect bad data
bad_measurements = estimator.detect_bad_data(net, chi2_prob_false=0.05)

# Remove and re-estimate
cleaned_net, removed = estimator.remove_bad_data(net, chi2_prob_false=0.05)
```

### 7.2 Normalized Residuals

Local test to identify specific bad measurements:

$$r_N^i = \frac{|z_i - h_i(\hat{x})|}{\sigma_i \sqrt{S_{ii}}}$$

Where $S_{ii}$ is the sensitivity matrix diagonal. Flag if $r_N^i > 3.0$.

### 7.3 Iterative Bad Data Removal

```python
def sanitize_measurements(net, estimator, max_iterations=5):
    """Iteratively remove bad data until clean."""
    for i in range(max_iterations):
        results = estimator.run_estimation(net)
        bad_data = estimator.detect_bad_data(net)
        
        if not bad_data:
            break
        
        # Remove highest normalized residual
        remove_bad_data(net, bad_data[:1])
    
    return net, results
```

---

## 8. Advanced Topics

### 8.1 Pseudo-Measurements for Observability

When meter coverage is sparse, add pseudo-measurements:

```python
def add_pseudo_measurements(net, unmeasured_loads, historical_profiles):
    """Generate pseudo-measurements for unobserved loads."""
    for load_idx in unmeasured_loads:
        # Get historical average
        avg_power = historical_profiles.get(load_idx, 0.002)  # 2 kW default
        
        # High std_dev (50-100% of value)
        pp.create_measurement(
            net,
            meas_type="p",
            element_type="load",
            element=load_idx,
            value=avg_power,
            std_dev=avg_power * 0.5,  # 50% uncertainty
            name=f"Pseudo_Load_{load_idx}"
        )
```

### 8.2 Virtual Measurements for Zero Injection Buses

Transit buses (no load/gen) provide exact information:

```python
def add_zero_injection_measurements(net):
    """Add virtual measurements for unconnected buses."""
    for bus_idx in net.bus.index:
        has_load = bus_idx in net.load.bus.values
        has_sgen = bus_idx in net.sgen.bus.values
        has_ext_grid = bus_idx in net.ext_grid.bus.values
        
        if not (has_load or has_sgen or has_ext_grid):
            # Zero injection - mathematical certainty
            pp.create_measurement(
                net, "p", "bus", bus_idx,
                value=0.0, std_dev=1e-6,  # Very high confidence
                name=f"Virtual_P_{bus_idx}"
            )
            pp.create_measurement(
                net, "q", "bus", bus_idx,
                value=0.0, std_dev=1e-6,
                name=f"Virtual_Q_{bus_idx}"
            )
```

### 8.3 Energy to Power Conversion

Smart meters report energy (kWh). Convert to power (MW) for pandapower:

```python
def energy_to_power(energy_kwh: float, interval_minutes: int = 15) -> float:
    """
    Convert energy reading to average power.
    
    Power (kW) = Energy (kWh) / Time (hours)
    Power (MW) = Power (kW) / 1000
    
    For 15-min interval: P_kW = E_kWh × 4
    """
    hours = interval_minutes / 60.0
    power_kw = energy_kwh / hours
    power_mw = power_kw / 1000.0
    return power_mw
```

### 8.4 Prosumer Net Metering

For prosumers, handle net power carefully:

```python
def add_prosumer_measurements(builder, meter, reading, bus_idx, load_idx, sgen_idx):
    """
    Handle prosumer with separate load and generation.
    
    The smart meter measures NET flow at connection point.
    When P_load ≈ P_gen, relative error becomes huge.
    """
    p_load_mw = reading.energy_consumed * 4 / 1000
    p_gen_mw = reading.energy_generated * 4 / 1000
    p_net_mw = p_gen_mw - p_load_mw
    
    # Option 1: Separate measurements (recommended for detail)
    builder.add_active_power_measurement(
        f"{meter.meter_id}_LOAD", load_idx, p_load_mw,
        meter_type=MeterType.RESIDENTIAL, is_generation=False
    )
    builder.add_active_power_measurement(
        f"{meter.meter_id}_GEN", sgen_idx, p_gen_mw,
        meter_type=MeterType.SOLAR_PROSUMER, is_generation=True
    )
    
    # Option 2: Net flow (simpler but higher uncertainty)
    # Calculate combined uncertainty
    sigma_net = sqrt(sigma_load**2 + sigma_gen**2)
    # Add net injection measurement at bus
```

### 8.5 Performance Optimization

For large-scale simulations:

```python
import pandapower as pp

# Enable numba JIT compilation (10-50x speedup)
pp.runpp(net, numba=True)

# Recycle Y-bus matrix for static topology
pp.runpp(net, recycle={"Ybus": True, "trafo": True})

# Use vectorized controllers for time-series
from pandapower.control import ConstControl
from pandapower.timeseries import DFData

ds = DFData(df_timeseries)
ConstControl(net, element='load', variable='p_mw',
             element_index=load_indices,  # Array of indices
             data_source=ds,
             profile_name=meter_columns)  # Array of column names
```

### 8.6 False Data Injection (FDI) Simulation

Test cyber-security with attack simulation:

```python
class FDI_Attacker:
    """Simulates False Data Injection attacks."""
    
    def inject_attack(self, measurements, targets, mode='bias', bias=0.1):
        """
        Modify measurements before state estimation.
        
        Args:
            measurements: Original measurement vector
            targets: List of measurement names to attack
            mode: 'bias' (constant offset) or 'scale' (multiplicative)
            bias: Attack magnitude
        """
        attacked = measurements.copy()
        
        for target in targets:
            if mode == 'bias':
                attacked.loc[target, 'value'] += bias
            elif mode == 'scale':
                attacked.loc[target, 'value'] *= (1 + bias)
        
        return attacked
    
    def stealth_attack(self, net, measurements, attack_vector):
        """
        Craft attack that bypasses chi-squared detection.
        
        Attack vector 'a' must satisfy: a = H·c
        where H is the Jacobian and c is the state perturbation.
        """
        # Calculate Jacobian
        H = calculate_jacobian(net)
        
        # Project attack onto column space of H
        stealth_a = H @ np.linalg.lstsq(H, attack_vector, rcond=None)[0]
        
        return measurements['value'] + stealth_a
```

---

## References

- [Pandapower Documentation](https://pandapower.readthedocs.io/)
- [meter_spec.md](../meter_spec.md) - Full specification document
- [ANSI C12.20-2010](https://webstore.ansi.org/) - Electricity Meters Accuracy Classes
- Abur, A., & Exposito, A. G. (2004). *Power System State Estimation: Theory and Implementation*
- [IEC 61970/61968 CIM Standards](https://cimug.ucaiug.org/)
