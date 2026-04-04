# Grid Integration Architecture

**Location:** [`src/smart_meter_simulator/adapters/`](../src/smart_meter_simulator/adapters/)

This document describes the grid integration components including pandapower adapter and state estimation.

## Components Overview

```
┌────────────────────────────────────────────────────────────┐
│                    Grid Integration                         │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Pandapower      │  │  State           │               │
│  │  Adapter         │  │  Estimator       │               │
│  └────────┬─────────┘  └────────┬─────────┘               │
│           │                     │                          │
│           ▼                     ▼                          │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Topology        │  │  Bad Data        │               │
│  │  Builder         │  │  Detection       │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  CIM Adapter     │  │  Mosaik          │               │
│  │  (IEC 61970)     │  │  Adapter         │               │
│  └──────────────────┘  └──────────────────┘               │
└────────────────────────────────────────────────────────────┘
```

## Pandapower Adapter

**Location:** [`adapters/pandapower_adapter.py`](../src/smart_meter_simulator/adapters/pandapower_adapter.py)

### Purpose

Converts smart meter readings to pandapower measurement tables for power flow and state estimation.

### Measurement Table Schema

```python
class MeasurementTable:
    """
    Pandapower measurement table schema.
    
    Columns:
    - meas_type: Physical quantity (v, p, q, i)
    - element_type: Grid element (bus, line, load, sgen, trafo)
    - element: Index of the element
    - value: Measured value
    - std_dev: Standard deviation from accuracy class
    - side: Branch side (from, to) - for line/trafo
    - name: AMI ID label
    """
```

### Sign Convention

```python
# Pandapower Convention
# Load: Positive P = consumption (draws from grid)
# Static Generator (sgen): Positive P = injection (exports to grid)
# Net Power at Bus: P_net = P_sgen - P_load

# Example
load_p = 5.0   # 5 kW consumption
sgen_p = 3.0   # 3 kW generation
p_net = -2.0   # Net: 2 kW consumption (negative = load)
```

### Measurement Mapping

```python
def create_measurement_table(self, net, meters, readings):
    """
    Create pandapower measurement table from meter readings.
    
    Mapping:
    - Voltage (V) → bus measurement (meas_type='v')
    - Active Power (P) → load/sgen measurement (meas_type='p')
    - Reactive Power (Q) → load/sgen measurement (meas_type='q')
    - Current (I) → line measurement (meas_type='i')
    """
    measurements = []
    
    for reading in readings:
        meter = self.get_meter(reading.meter_id)
        
        # Voltage measurement at bus
        measurements.append({
            'meas_type': 'v',
            'element_type': 'bus',
            'element': meter.bus_idx,
            'value': reading.voltage_v / 230.0,  # Convert to p.u.
            'std_dev': meter.voltage_std_dev,
            'name': f"{reading.meter_id}_V"
        })
        
        # Power measurement at load/sgen
        measurements.append({
            'meas_type': 'p',
            'element_type': 'sgen' if reading.is_exporting else 'load',
            'element': meter.element_idx,
            'value': abs(reading.power_kw) / 1000.0,  # Convert to MW
            'std_dev': meter.power_std_dev,
            'name': f"{reading.meter_id}_P"
        })
    
    return pd.DataFrame(measurements)
```

### Accuracy Class Integration

```python
def calculate_std_dev(self, value: float, accuracy_class: AccuracyClass) -> float:
    """
    Calculate standard deviation from accuracy class.
    
    Formula: σ = (accuracy_class / 300) × |value|
    
    Examples:
    - CLASS_1_0 with 5.0 kW: σ = (1.0 / 300) × 5000 = 16.67 W
    - CLASS_0_5 with 100 V: σ = (0.5 / 300) × 100 = 0.167 V
    """
    return (accuracy_class.value / 300.0) * abs(value)
```

## State Estimator

**Location:** [`adapters/state_estimator.py`](../src/smart_meter_simulator/adapters/state_estimator.py)

### Algorithms

#### Weighted Least Squares (WLS)

```python
class WLSEstimator:
    """
    Weighted Least Squares state estimation.
    
    Objective:
    min J(x) = [z - h(x)]^T W [z - h(x)]
    
    Where:
    - z: Measurement vector
    - h(x): Measurement function
    - W: Weight matrix (W = R^-1, R = covariance)
    - x: State vector (voltage magnitudes and angles)
    
    Solution (Newton-Raphson):
    x^(k+1) = x^(k) + [H^T W H]^-1 H^T W [z - h(x^(k))]
    
    Where H = ∂h/∂x (Jacobian matrix)
    """
```

#### Iwamoto Method

```python
class IwamotoEstimator:
    """
    Iwamoto method for divergent cases.
    
    Features:
    - Optimal multiplier for divergence handling
    - Better convergence for high R/X ratios
    - Robust for distribution networks
    
    Update:
    x^(k+1) = x^(k) + μ Δx
    
    Where μ is optimal multiplier minimizing J(x)
    """
```

### Implementation

```python
def run_estimation(self, net):
    """
    Run state estimation on pandapower network.
    
    Returns:
        EstimationResult with:
        - converged: bool
        - iterations: int
        - voltage_magnitudes: array
        - voltage_angles: array
        - chi_squared: float
        - bad_data_detected: bool
    """
    # Initialize state
    x = self.initialize_state(net)
    
    # Newton-Raphson iterations
    for iteration in range(self.max_iterations):
        # Calculate Jacobian
        H = self.calculate_jacobian(net, x)
        
        # Calculate residuals
        z_hat = self.measurement_function(x)
        r = self.measurements - z_hat
        
        # Calculate gain matrix
        G = H.T @ self.W @ H
        
        # Solve for state update
        dx = np.linalg.solve(G, H.T @ self.W @ r)
        
        # Update state
        x = x + dx
        
        # Check convergence
        if np.max(np.abs(dx)) < self.tolerance:
            break
    
    # Bad data detection
    chi_squared = r.T @ self.W @ r
    bad_data = self.detect_bad_data(chi_squared, r)
    
    return EstimationResult(
        converged=converged,
        iterations=iteration,
        results=x,
        chi_squared=chi_squared,
        bad_data_detected=bad_data
    )
```

## Bad Data Detection

### Chi-Squared Test

```python
def chi_squared_test(self, J_x_hat, degrees_of_freedom, alpha=0.05):
    """
    Chi-squared test for bad data detection.
    
    Test Statistic: J(x̂) = [z - h(x̂)]^T W [z - h(x̂)]
    
    Threshold: χ²(ν, α) where ν = m - n (redundancy)
    - m: Number of measurements
    - n: Number of states
    
    Decision:
    - J(x̂) > χ²(ν, α): Bad data detected
    - J(x̂) ≤ χ²(ν, α): No bad data
    """
    from scipy.stats import chi2
    
    threshold = chi2.ppf(1 - alpha, degrees_of_freedom)
    
    if J_x_hat > threshold:
        return True, threshold  # Bad data detected
    else:
        return False, threshold  # No bad data
```

### Normalized Residuals

```python
def normalized_residuals_test(self, residuals, covariance_matrix):
    """
    Normalized residuals test for bad data identification.
    
    Normalized Residual: r_N_i = r_i / sqrt(C_ii)
    
    Where C = I - H(G^-1)H^T W (residual covariance)
    
    Threshold: |r_N| > 3.0 (3-sigma)
    
    Identification:
    - Measurement with largest |r_N| is suspect
    """
    # Calculate residual covariance
    C = np.eye(len(residuals)) - self.H @ self.G_inv @ self.H.T @ self.W
    
    # Normalize residuals
    sigma_r = np.sqrt(np.diag(C))
    r_normalized = residuals / sigma_r
    
    # Find largest residual
    max_idx = np.argmax(np.abs(r_normalized))
    max_residual = r_normalized[max_idx]
    
    # Test threshold
    if np.abs(max_residual) > 3.0:
        return True, max_idx, max_residual
    else:
        return False, None, max_residual
```

### Virtual Measurements

```python
def add_virtual_measurements(self, net):
    """
    Add virtual measurements for zero-injection buses.
    
    Zero-injection buses have known P=0, Q=0.
    These provide additional constraints for SE.
    
    Characteristics:
    - Very high weight (low std_dev)
    - Improves observability
    - No measurement cost
    """
    for bus_idx in net.zero_injection_buses:
        # Zero active power injection
        measurements.append({
            'meas_type': 'p',
            'element_type': 'bus',
            'element': bus_idx,
            'value': 0.0,
            'std_dev': 1e-6,  # Very high confidence
            'name': f'virtual_p_{bus_idx}'
        })
        
        # Zero reactive power injection
        measurements.append({
            'meas_type': 'q',
            'element_type': 'bus',
            'element': bus_idx,
            'value': 0.0,
            'std_dev': 1e-6,
            'name': f'virtual_q_{bus_idx}'
        })
```

## Topology Builder

**Location:** [`adapters/topology_builder.py`](../src/smart_meter_simulator/adapters/topology_builder.py)

### Radial Network Construction

```python
def build_radial_network(self, num_buses=10):
    """
    Build radial (tree) distribution network.
    
    Structure:
    Substation → Bus1 → Bus2 → ... → BusN
    
    Parameters:
    - num_buses: Number of buses
    - base_voltage_kv: Nominal voltage (default 0.4 kV)
    - line_length_km: Line length between buses
    """
    net = pp.create_empty_network()
    
    # Create buses
    for i in range(num_buses):
        pp.create_bus(net, vn_kv=0.4, name=f'Bus_{i}')
    
    # Create lines
    for i in range(num_buses - 1):
        pp.create_line(net, from_bus=i, to_bus=i+1, 
                      length_km=1.0, std_type='NAYY 4x50 SE')
    
    # Create loads
    for i in range(1, num_buses):
        pp.create_load(net, bus=i, p_mw=0.005, q_mvar=0.002)
    
    # Create external grid (substation)
    pp.create_ext_grid(net, bus=0)
    
    return net
```

### Thai Grid Topology

```python
def build_thai_lv_network(self):
    """
    Build typical Thai low-voltage distribution network.
    
    Characteristics:
    - 400V three-phase (line-to-line)
    - 230V single-phase (line-to-neutral)
    - Overhead lines (rural)
    - Underground cables (urban)
    """
    net = pp.create_empty_network()
    
    # MV/LV transformer (22kV/400V)
    pp.create_trafo(net, hv_bus=0, lv_bus=1, 
                   std_type='0.4 MVA 22/0.4 kV')
    
    # LV feeders
    for phase in ['A', 'B', 'C']:
        self.create_single_phase_feeder(net, phase)
    
    return net
```

## CIM Adapter

**Location:** [`adapters/cim_adapter.py`](../src/smart_meter_simulator/adapters/cim_adapter.py)

### IEC 61970 Support

```python
class CIMAdapter:
    """
    IEC 61970 Common Information Model (CIM) adapter.
    
    Supported Classes:
    - ConductingEquipment (Bus, Line, Load, Generator)
    - Measurements (Analog, Discrete)
    - Topology (ConnectivityNode, Terminal)
    
    Formats:
    - RDF/XML import
    - RDF/XML export
    """
```

### Import/Export

```python
def import_cim_rdf(self, rdf_file: str) -> pandapowerNet:
    """
    Import CIM RDF/XML to pandapower.
    
    Process:
    1. Parse RDF/XML
    2. Extract equipment
    3. Build topology
    4. Create pandapower network
    """
    tree = etree.parse(rdf_file)
    
    # Extract buses
    buses = self.parse_conducting_equipment(tree)
    
    # Extract lines
    lines = self.parse_ac_line_segments(tree)
    
    # Extract loads
    loads = self.parse_energy_consumers(tree)
    
    # Build pandapower network
    net = self.build_pandapower_network(buses, lines, loads)
    
    return net

def export_cim_rdf(self, net: pandapowerNet) -> str:
    """
    Export pandapower to CIM RDF/XML.
    
    Process:
    1. Extract pandapower elements
    2. Map to CIM classes
    3. Generate RDF/XML
    """
    rdf = self.create_rdf_document()
    
    # Add buses
    for bus in net.bus.itertuples():
        self.add_substation_voltage_level(rdf, bus)
    
    # Add lines
    for line in net.line.itertuples():
        self.add_ac_line_segment(rdf, line)
    
    # Add loads
    for load in net.load.itertuples():
        self.add_energy_consumer(rdf, load)
    
    return rdf.toxml()
```

## Mosaik Adapter

**Location:** [`adapters/mosaik_adapter.py`](../src/smart_meter_simulator/adapters/mosaik_adapter.py)

### Co-Simulation Support

```python
class MosaikAdapter:
    """
    Mosaik co-simulation adapter.
    
    Purpose:
    - Multi-domain simulation coordination
    - Power grid + communication + control
    - Time synchronization
    
    Integration:
    - Mosaik simulator API
    - Entity-based modeling
    - Data exchange via Mosaik runtime
    """
```

## Performance Optimization

### Numba JIT

```python
from numba import jit

@jit(nopython=True)
def calculate_jacobian_fast(net, x):
    """
    JIT-compiled Jacobian calculation.
    
    Speedup: 10-50x faster than pure Python
    """
    # Optimized Jacobian computation
    ...
```

### Matrix Recycling

```python
def recycle_ybus(self, net):
    """
    Reuse Ybus matrix for time-series simulation.
    
    Benefit: Avoids repeated matrix assembly
    """
    if self.ybus_cached:
        return self.ybus_cache
    else:
        self.ybus_cache = pp.makeYbus(net)
        self.ybus_cached = True
        return self.ybus_cache
```

## Testing

```python
@pytest.mark.grid
def test_state_estimation_convergence(estimator, test_network):
    result = estimator.run_estimation(test_network)
    
    assert result.converged == True
    assert result.iterations < 10
    assert result.chi_squared < result.chi_squared_critical

@pytest.mark.integration
def test_measurement_mapping(adapter, meters, readings):
    measurements = adapter.create_measurement_table(readings)
    
    assert len(measurements) == len(readings) * 2  # P and V per reading
    assert 'meas_type' in measurements.columns
    assert 'std_dev' in measurements.columns
```

## Related Documents

- [System Overview](overview.md)
- [Simulation Engine](simulation-engine.md)
- [Pandapower Reference](../reference/pandapower.md)
