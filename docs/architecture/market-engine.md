# Market & VPP Engine

The **Market & VPP Engine** provides the intelligence layer for coordinating Distributed Energy Resources (DERs) to provide systemic grid services and economic optimization, with specialized support for island microgrid bottleneck resolution.

## 🔋 Virtual Power Plant (VPP)

The `VPPManager` (located in `backend/src/smart_meter_simulator/core/vpp.py`) aggregates smart meters and batteries into logical **Clusters**. These clusters act as a single, large-scale flexible resource for the grid operator.

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

## 🎮 Bottleneck Game (Island Congestion Management)

When the 115 kV KMB line (Khanom → Samui) approaches its thermal limit, the engine activates the **Bottleneck Game** — a congestion management mechanism that resolves transmission constraints through coordinated DER dispatch:

1.  **Detection**: The `PandapowerAdapter` detects line loading > 95% on the bottleneck line.
2.  **Game Setup**: The VPP clusters on Samui are treated as players in a cooperative game.
3.  **Resolution**: Each cluster bids its available flexibility (BESS discharge, load curtailment).
4.  **Dispatch**: The engine dispatches the minimum-cost combination to relieve the constraint.
5.  **Financial Settlement**: Savings are calculated at 9 THB/kWh shifted from diesel to BESS.

The bottleneck game logic is tested in `backend/tests/test_bottleneck_game.py`.

## 💰 Financial VPP Optimization (PEA Island Mode)

For PEA-operated island microgrids, the engine implements a financial optimization layer:

-   **Diesel Displacement**: Every MW shifted from the Tao diesel generator to BESS or grid import saves ~9 THB/kWh.
-   **BESS Arbitrage**: Charge from cheap grid power (off-peak) and discharge during peak diesel hours.
-   **Forecast-Driven Scheduling**: The `EdgeForecastingEngine` provides 24-hour load forecasts to pre-position BESS state-of-charge.
-   **Early Warning System (EWS)**: Alerts are raised when forecast load exceeds 95% of island capacity, triggering pre-emptive BESS charging.

```python
# Example: Get recommended schedule from EdgeForecastingEngine
schedule = forecaster.get_recommended_schedule(forecast, capacity_mw=40.0)
# Returns hourly actions with potential_hourly_savings_thb
```

## 🎯 Multi-Objective Dispatch Optimization

When a dispatch setpoint is received, the engine uses a weighted optimization algorithm to allocate power:

| Objective | Weight | Logic |
| :--- | :--- | :--- |
| **SoC Balance** | 30% | Prefer high SoC for discharge; low SoC for charge. |
| **Nodal Price** | 40% | Dispatch resources in high-price nodes during peaks. |
| **Carbon Impact** | 30% | Prioritize discharging to displace dirty grid power. |

## 🏝️ Microgrid Stability (Island Mode)

In the event of a grid disconnection (Islanding), the VPP transitions to an emergency stability mode:

-   **Emergency Load Shedding**: If frequency drops below 49.0 Hz, priority 3 (sheddable) and then priority 2 loads are automatically disconnected.
-   **Black Start Sequencing**: Coordinates the gradual restoration of loads and generation.
-   **Local Balancing**: Adjusts battery setpoints in real-time to match local solar generation with critical loads.

## 🏭 Carbon Intensity Tracking

The engine tracks the **Carbon Intensity** (g CO2/kWh) of the grid in real-time. By coordinating VPP discharge during high-intensity periods, the simulator demonstrates how DERs can minimize the overall carbon footprint of the distribution network.

---
_Next: [Transport Layer](transport-layer.md)_
