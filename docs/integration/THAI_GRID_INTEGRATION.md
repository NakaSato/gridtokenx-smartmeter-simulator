# Thai Grid Integration (MEA/PEA)

The **GridTokenX Smart Meter Simulator** provides high-fidelity modeling of Thailand's electrical distribution infrastructure, specifically tailored for the standards of the **Metropolitan Electricity Authority (MEA)** and the **Provincial Electricity Authority (PEA)**.

## 🏗️ Grid Infrastructure Standards

The simulator incorporates the following Thai electrical standards (located in `src/smart_meter_simulator/adapters/thai_grid_topology.py`):

### 1. Voltage Levels
-   **MV (Medium Voltage)**: 22 kV (Global Standard for MEA/PEA Distribution).
-   **LV (Low Voltage)**: 400V (3-Phase, 4-Wire) or 230V (Phase-to-Neutral).

### 2. Standard Transformers (22 / 0.4 kV)
The simulator models standard Thai distribution transformers with the following capacities:
-   **160 - 315 kVA**: Typical for rural villages (PEA).
-   **400 - 630 kVA**: Standard for suburban residential areas.
-   **800 - 1000 kVA**: Used in high-density urban areas (MEA) and industrial parks.

### 3. Thai Conductor Types
Physical properties (Resistance, Reactance, Capacitance) for common Thai conductors are integrated into the `pandapower` model:
-   **AAC (Aluminum) / ACSR**: Standard for overhead 22kV and LV distribution.
-   **XLPE Insulated**: Used for underground 22kV feeders in Bangkok (MEA).
-   **NAYY (Aluminum)**: Standard LV underground and service drop cables.

## 🏙️ Regional Network Modeling

The `ThaiGridBuilder` allows for the creation of representative network topologies based on Thai regional characteristics:

| Region | Utility | Feeder Characteristics |
| :--- | :--- | :--- |
| **Bangkok Urban** | MEA | Dense load, mostly underground XLPE/NAYY cabling, 630-1000kVA transformers. |
| **Central Thailand** | PEA | Mixed urban/rural, long overhead AAC feeders along main roads, 250-400kVA transformers. |
| **Rural (Northeast)** | PEA | Long-distance radial feeders, lower load density, 160kVA transformers common. |

## ⚙️ Usage in Simulation

To build a realistic Thai grid segment for testing, use the `ThaiGridBuilder` within the simulation setup:

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder, ThaiRegion

# Create a Bangkok urban distribution network
builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
net = builder.build_urban_network(
    num_households=150,
    province="Bangkok",
    district="Pathum Wan",
    underground=True
)
```

## 📐 Grid Health & ANSI Standards

The simulator validates the Thai grid state against local regulatory limits:
-   **Voltage Tolerance**: Typically $\pm 5\%$ for MEA/PEA (0.95 - 1.05 pu).
-   **Line Loading**: Alerts are triggered if line thermal capacity exceeds 90%.
-   **Phase Balance**: Monitoring for neutrality current in 3-phase, 4-wire configurations.

---
_Documentation suite finalized._
