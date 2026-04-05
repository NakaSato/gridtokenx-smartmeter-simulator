# Market & VPP Engine

The **Market & VPP Engine** provides the intelligence layer for coordinating Distributed Energy Resources (DERs) to provide systemic grid services and economic optimization.

## 🔋 Virtual Power Plant (VPP)

The `VPPManager` (located in `src/smart_meter_simulator/core/vpp.py`) aggregates smart meters and batteries into logical **Clusters**. These clusters act as a single, large-scale flexible resource for the grid operator.

### Resource Aggregation

Meters are registered as `DERResource` objects with the following properties:
-   **Flexibility**: Calculated based on the current State-of-Charge (SoC) and rated power.
-   **Priority**: 1 (Critical), 2 (Normal), 3 (Sheddable).
-   **Reputation Score**: Automatically adjusted based on the resource's historical compliance and telemetry integrity (detection of "impossible" SoC jumps).

## ⚡ Grid Services: aFRR & Droop Control

The engine provides automated frequency restoration reserve (**aFRR**) to stabilize the grid:

1.  **Frequency Monitoring**: The `FrequencyModel` simulates system-wide rotational inertia.
2.  **Deadband Logic**: No action is taken within the $\pm0.02$ Hz deadband.
3.  **Proportional Response**: Outside the deadband, required power adjustment is calculated using a 5% droop gain.
4.  **Coordinated Dispatch**: The VPP cluster allocates the total required power across its constituent meters.

## 🎯 Multi-Objective Dispatch Optimization

When a dispatch setpoint is received, the engine uses a weighted optimization algorithm to allocate power:

| Objective | Weight | Logic |
| :--- | :--- | :--- |
| **SoC Balance** | 30% | Prefer high SoC for discharge; low SoC for charge. |
| **Nodal Price** | 40% | Dispatch resources in high-price nodes during peaks. |
| **Carbon Impact** | 30% | Prioritize discharging to displace dirty grid power. |

## 🏝️ Microgrid Stability (Island Mode)

In the event of a grid disconnection (Islanding), the VPP transitions to an emergency stability mode:

-   **Emergency Load Shedding**: If frequency drops below 49.0 Hz, priority 3 (sheddable) and then priority 2 loads are automatically disconnected to prevent a total blackout.
-   **Black Start Sequencing**: Coordinates the gradual restoration of loads and generation to prevent startup-induced instability.
-   **Local Balancing**: Adjusts battery setpoints in real-time to match local solar generation with critical loads.

## 🏭 Carbon Intensity Tracking

The engine tracks the **Carbon Intensity** (g CO2/kWh) of the grid in real-time. By coordinating VPP discharge during high-intensity periods, the simulator demonstrates how DERs can minimize the overall carbon footprint of the distribution network.

---
_Next: [Transport Layer](transport-layer.md)_
