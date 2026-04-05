# Pandapower Implementation

The **GridTokenX Smart Meter Simulator** leverages **Pandapower**, an open-source tool for electrical power system modeling and analysis, to provide an accurate representation of the distribution network.

## 🏗️ State Estimation (WLS)

The simulator uses Pandapower's **Weighted Least Squares (WLS)** state estimation engine to provide grid observability in the presence of incomplete or noisy sensor data.

### 1. Measurement Ingestion
Individual `EnergyReading` objects are converted into measurements (Bus Voltage, Line Power, Load Power) with associated standard deviations based on the meter's Accuracy Class (e.g., 0.2, 0.5, 1.0).

### 2. Zero-Injection Constraints
Buses with no attached generation or load are modeled as zero-injection constraints to simplify the network calculation.

### 3. Convergence & Health
The `StateEstimator` tracks the following metrics to ensure grid reliability:
-   **Chi-Squared Test**: Validates the statistical consistency of the estimated state.
-   **Normalized Residual ($r_N$)**: Identifies bad data or sensor tampering.
-   **Voltage Profile**: Monitors for overvoltage/undervoltage conditions across the network (typically 0.95 - 1.05 pu).

## 📐 Grid Modeling Elements

Pandapower structures the distribution network into several key elements:

| Element | Description | Integration in Simulator |
| :--- | :--- | :--- |
| **`bus`** | Nodes in the grid (e.g., substations, feeder junctions). | Mapped to geospatial locations in PostGIS. |
| **`line`** | Electrical lines connecting buses. | Modeled with resistance (R), reactance (X), and capacitance (C). |
| **`load`** | Residential or commercial power consumption. | Driven by `SmartMeter` consumption profiles. |
| **`sgen`** | Distributed solar or wind generation. | Driven by `SmartMeter` PV generation profiles. |
| **`storage`** | Residential or utility-scale batteries. | Driven by `SmartMeter` and VPP battery logic. |

## ⚙️ Performance & Scalability

For large-scale simulations (1,000+ meters), the simulator uses an optimized subset of the `pandapower_net` to reduce the computational overhead of the Newton-Raphson power flow solver.

```python
# From state_estimator.py
from pandapower.estimation import estimate
success = estimate(net, init='flat', tolerance=1e-6)
```

---
_Next: [Thai Grid Tariffs](thai-tariffs.md)_
