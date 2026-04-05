# Thai Grid Topology

The **GridTokenX Smart Meter Simulator** incorporates a high-fidelity geospatial representation of the Thai electrical distribution network, specifically the **22kV (Medium Voltage)** and **230V/400V (Low Voltage)** feeders managed by MEA and PEA.

## 📐 Network Configuration

The distribution grid is modeled as a hierarchical network from the substation to individual customer premises:

1.  **Substation (District Level)**: 69kV or 115kV transmission stepped down to 22kV Distribution.
2.  **Primary Feeder (Medium Voltage)**: 22kV three-phase lines that traverse urban and rural areas.
3.  **Distribution Transformer**: Steps down 22kV to 230V (Single-Phase) or 400V (Three-Phase) for residential and commercial use.
4.  **Secondary Grid (Low Voltage)**: The final segment connecting transformers to the smart meters.

## 🗺️ Geospatial Modeling (PostGIS)

The simulator integrates with a **PostGIS** spatial database to maintain realistic topology data:

-   **Bus Location**: Lat/Lon coordinates for every pole and transformer.
-   **Line Segments**: Vector data (LineStrings) containing the R (Resistance) and X (Reactance) values based on the physical conductor type.
-   **Feeder Clusters**: Logical grouping of meters into feeders to enable localized VPP dispatch.

```python
# Default Base Location (Bangkok / Samut Prakan)
BASE_LATITUDE = 13.758252
BASE_LONGITUDE = 100.687455
```

## 🏗️ Digital Twin Mapping

When the simulation starts, the `PandapowerAdapter` builds a "Digital Twin" of the grid using these steps:
1.  **Bus Creation**: Transformer locations and meter points are mapped to Pandapower buses.
2.  **Line Creation**: Vector lines from PostGIS are converted into Pandapower branch elements.
3.  **Load/Gen Assignment**: Smart meters are attached to the nearest LV bus as a Load (Consumer) or Static Generator (Prosumer).

## 🏙️ Regional Topologies

The simulator supports switching between different representative Thai grid topologies:

| Region | Utility | Characteristics |
| :--- | :--- | :--- |
| **Bangkok Central** | MEA | Underground 22kV network, high load density, multi-feed redundancy. |
| **Samut Prakan** | MEA | Industrial-heavy feeders, significant harmonic distortion. |
| **Phuket / Chiang Mai** | PEA | Long-distance rural feeders, higher voltage drop, frequent islanding. |

## 🏝️ Microgrid Integration

The topology includes the definition of **Islanding Nodes** (Microgrid Isolators). In a grid failure scenario, these breakers trip, and the local VPP cluster takes over to maintain the stability of the isolated feeder segment.

---
_Documentation Complete._
