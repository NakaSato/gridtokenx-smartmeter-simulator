# Grid Integration (Pandapower)

The **Grid Integration** layer acts as the "Digital Twin" of the physical electrical network. It uses the **Pandapower** library to translate individual meter readings into a unified grid state.

## 🏗️ Architecture

The integration is managed by the `PandapowerAdapter` and its specialized sub-components (located in `src/smart_meter_simulator/adapters/`):

1.  **Topology Builder**: Dynamically constructs a grid model (buses, lines, transformers, loads) based on the current set of active meters and spatial data from PostGIS.
2.  **State Estimator**: Performs **Weighted Least Squares (WLS)** analysis to estimate the voltage and power flow at every node, even where sensors are missing.
3.  **Measurement Sync**: Maps time-series meter telemetry (kW, kV) to the corresponding grid elements (Loads, SGens) using accuracy-aware weighting.

## 🔄 State Estimation Workflow

Each simulation tick triggers the following grid analysis cycle:

1.  **Ingestion**: Aggregate latest generation/consumption from all `SmartMeter` objects.
2.  **Mapping**: Convert kWh (energy) into average P (active) and Q (reactive) power (MW/MVar).
3.  **WLS Estimation**:
    *   Initialize from previous converged results or a "Flat Start".
    *   Solve the non-linear estimation equations.
    *   Verify results against **ANSI C12.20** accuracy standards.
4.  **Bad Data Detection**: Identify and remove outlier measurements using the $r_N$ (Normalized Residual) test.
5.  **Analytics**: Calculate systemic metrics such as total grid losses, average voltage deviation, and thermal line loading.

## 🗺️ Spatial Modeling (PostGIS)

The simulator integrates with a **PostGIS** spatial database to retrieve realistic grid topologies, specifically tailored for MEA/PEA (Thailand) distribution networks.

```python
# From simulation loop
net, meter_to_bus = self.adapter.build_network_from_meters(self.meters)
```

## 📐 Observability

A network is considered **Observable** if there are enough measurement points to uniquely determine the state at every node. The simulator handles low-observability scenarios by:
-   Injecting **Pseudo-measurements** derived from Standard Load Profiles (SLP).
-   Using **Geo-SAM** estimates for distributed solar capacity.

---
_Next: [Market & VPP Engine](market-engine.md)_
