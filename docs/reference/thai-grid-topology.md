# Thai Grid Topology Guide

## Overview

This module provides realistic electrical distribution network models for **Thailand**, supporting the GridTokenX Smart Meter Simulator with geographically and technically accurate grid topologies.

### Authority Coverage

| Authority | Region | Coverage | Characteristics |
|-----------|--------|----------|-----------------|
| **EGAT** (กฟผ.) | National | Transmission (115-500 kV) | Power generation, transmission |
| **MEA** (การไฟฟ้านครหลวง) | Bangkok Metro | Distribution (22 kV) | Underground cables, high density |
| **PEA** (การไฟฟ้าส่วนภูมิภาค) | Provincial | Distribution (22 kV) | Mixed overhead/underground |

---

## Installation

```bash
# Ensure pandapower is installed
uv sync

# For visualization (optional)
uv add matplotlib
```

---

## Quick Start

### Create a Bangkok Urban Network

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder, ThaiRegion

builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)

net = builder.build_urban_network(
    num_households=200,
    transformer_capacity_kva=630,
    province="Bangkok",
    district="Bang Khen",
    latitude=13.8788,
    longitude=100.6025
)

print(f"Created: {len(net.bus)} buses, {len(net.line)} lines")
```

### Create a Rural Feeder (Central Thailand)

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder, ThaiRegion

builder = ThaiGridBuilder(region=ThaiRegion.CENTRAL)

net = builder.build_rural_feeder(
    num_villages=5,
    households_per_village=20,
    province="Ayutthaya",
    latitude=14.3532,
    longitude=100.5775
)
```

---

## Thai Distribution Network Characteristics

### Voltage Levels

| Level | Voltage | Application |
|-------|---------|-------------|
| **MV (Medium Voltage)** | 22 kV | Primary distribution |
| **LV (Low Voltage)** | 0.4 kV (3-phase), 230V (1-phase) | Secondary distribution |

### Standard Transformers (22/0.4 kV)

| Capacity | Application | Area |
|----------|-------------|------|
| 160 kVA | Small rural | Village (5-10 houses) |
| 250 kVA | Rural village | Village (10-20 houses) |
| 315 kVA | Standard rural | Village (20-30 houses) |
| 400 kVA | Suburban | Residential (30-50 houses) |
| 500 kVA | Urban residential | Bangkok (50-80 houses) |
| 630 kVA | Urban commercial | Shopping area |
| 800 kVA | High-density | Commercial district |
| 1000 kVA | Industrial | Factory, large commercial |

### Cable Types

#### MV Cables (22 kV)
| Type | Installation | Application |
|------|-------------|-------------|
| AAC 185 mm² | Overhead | Rural/Suburban (PEA) |
| XLPE 185 mm² | Underground | Urban (MEA) |
| XLPE 240 mm² | Underground | High-density urban |

#### LV Cables (0.4 kV)
| Type | Installation | Application |
|------|-------------|-------------|
| NAYY 4x50 SE | Underground/Overhead | Service drop |
| NAYY 4x95 SE | Underground | Commercial feeder |
| NAYY 4x150 SE | Underground | Urban main feeder |
| AAC 70 mm² | Overhead | Rural service drop |

---

## API Reference

### ThaiGridBuilder

Main class for building Thai distribution networks.

#### Constructor

```python
builder = ThaiGridBuilder(
    region=ThaiRegion.BANGKOK,  # or CENTRAL, NORTH, NORTHEAST, SOUTH
    network_name="My Network"
)
```

#### Methods

##### `build_urban_network()`

Create a Bangkok-style urban network with underground cables.

```python
net = builder.build_urban_network(
    num_households=200,           # Number of households
    transformer_capacity_kva=630, # Transformer capacity (auto-calculated if None)
    underground=True,             # Underground cables (default True for Bangkok)
    province="Bangkok",           # Province name
    district="Bang Khen",         # District name
    latitude=13.8788,             # Center latitude
    longitude=100.6025            # Center longitude
)
```

##### `build_rural_feeder()`

Create a rural feeder with multiple villages (PEA style).

```python
net = builder.build_rural_feeder(
    num_villages=5,               # Number of villages along feeder
    households_per_village=20,    # Houses per village
    province="Ayutthaya",         # Province name
    latitude=14.3532,             # Starting latitude
    longitude=100.5775            # Starting longitude
)
```

##### `build_commercial_network()`

Create a commercial district network with high load density.

```python
net = builder.build_commercial_network(
    num_shops=50,                 # Number of commercial units
    transformer_capacity_kva=800, # Transformer capacity
    province="Bangkok",
    district="Pathum Wan",
    latitude=13.7465,
    longitude=100.5347
)
```

##### `create_thai_substation()`

Create a Thai distribution substation (22 kV MV bus).

```python
mv_bus_idx = builder.create_thai_substation(
    location_name="บางเขน",       # Thai name (Unicode supported)
    province="Bangkok",
    latitude=13.8788,
    longitude=100.6025,
    mv_voltage_kv=22.0
)
```

##### `create_distribution_transformer()`

Add a distribution transformer (22/0.4 kV).

```python
trafo_idx = builder.create_distribution_transformer(
    mv_bus_id="MV_Bus_1",
    lv_bus_id="LV_Bus_1",
    capacity_kva=500,
    location_name="TX-001",
    transformer_type=TransformerType.TX_500
)
```

##### `get_network_summary()`

Get network statistics.

```python
summary = builder.get_network_summary()
print(summary)
# {
#   'name': 'Thai Distribution Network',
#   'region': 'bangkok',
#   'buses': 205,
#   'lines': 204,
#   'distribution_transformers': 1,
#   'total_transformer_capacity_kva': 630.0,
#   'mv_voltage_kv': 22.0,
#   'lv_voltage_kv': 0.4,
#   'cable_types': {'NAYY 4x150 SE': 4, 'NAYY 4x50 SE': 200}
# }
```

---

## Regional Presets

### ThaiRegion Enum

```python
class ThaiRegion(Enum):
    BANGKOK = "bangkok"          # MEA: Underground, high density
    CENTRAL = "central"          # PEA: Mixed, rice farming areas
    NORTH = "north"              # PEA: Mountainous, hydro
    NORTHEAST = "northeast"      # PEA: Rural, solar farms
    SOUTH = "south"              # PEA: Coastal, tourism
```

### Regional Characteristics

| Region | Cable Type | Transformer | Topology |
|--------|-----------|-------------|----------|
| Bangkok | Underground XLPE/NAYY | 500-1000 kVA | Dense radial |
| Central | Overhead AAC | 160-315 kVA | Long feeder |
| North | Overhead AAC | 160-400 kVA | Mountainous |
| Northeast | Overhead AAC | 160-315 kVA | Rural radial |
| South | Mixed | 315-630 kVA | Coastal/tourism |

---

## Integration with Smart Meter Simulator

### Generate Meters on Thai Grid

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
from smart_meter_simulator.core.meter_generator import MeterGenerator

# Create Thai grid
builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
net = builder.build_urban_network(num_households=100)

# Generate meters
generator = MeterGenerator(num_meters=100)
meters = generator.generate_meters()

# Map meters to grid
adapter = PandapowerAdapter()
net, meter_to_bus = adapter.build_network_from_meters(meters)

print(f"Mapped {len(meter_to_bus)} meters to grid")
```

### Run State Estimation

```python
from smart_meter_simulator.adapters.state_estimator import StateEstimator

# Run power flow
import pandapower as pp
pp.runpp(net)

# Run state estimation
estimator = StateEstimator()
estimation = estimator.estimate_state(net)

print(f"Voltage estimation: {estimation['vm_pu'].mean():.4f} p.u.")
```

---

## Examples

Run the example script to see all network types:

```bash
# Run all examples
python examples/thai_grid_examples.py

# Output visualizations saved to: data/
# - data/bangkok_urban_network.png
# - data/central_thailand_rural.png
# - data/bangkok_commercial.png
```

### Example Output

```
============================================================
Example 1: Bangkok Urban Residential Network
============================================================

Network: Thai Distribution Network
Region: bangkok
Buses: 205
Lines: 204
Transformers: 1
Total Capacity: 630 kVA
Voltage Levels: MV=22 kV, LV=0.4 kV

Cable Types:
  - NAYY 4x150 SE: 4 lines
  - NAYY 4x50 SE: 200 lines

Running power flow for: Bangkok Urban
  Voltage range: 0.9823 - 1.0000 p.u.
  ✓ Voltage within limits (±5%)
  Max line loading: 45.2%
  Max transformer loading: 62.8%
```

---

## Power Quality Standards

### Thai Voltage Standards (MEA/PEA)

| Parameter | Standard | Tolerance |
|-----------|----------|-----------|
| MV Voltage | 22 kV | ±5% |
| LV Voltage | 400V (3-phase), 230V (1-phase) | ±5% |
| Frequency | 50 Hz | ±0.05 Hz (normal) |

### Voltage Drop Limits

| Level | Max Drop |
|-------|----------|
| MV Feeder | 3% |
| LV Service Drop | 2% |
| **Total** | **5%** |

---

## Customization

### Add Custom Cable Type

```python
from smart_meter_simulator.adapters.thai_grid_topology import CableType

# Custom cable types are automatically handled via pandapower standard types
# Common Thai standards:
# - MV: "AAC 95 mm²", "AAC 185 mm²", "XLPE 185 mm²"
# - LV: "NAYY 4x50 SE", "NAYY 4x95 SE", "NAYY 4x150 SE"
```

### Custom Transformer Parameters

```python
builder.create_distribution_transformer(
    mv_bus_id="MV_1",
    lv_bus_id="LV_1",
    capacity_kva=500,
    location_name="Custom_TX"
)

# Or manually with custom parameters:
from smart_meter_simulator.adapters.topology_builder import TransformerConfig

trafo_config = TransformerConfig(
    hv_bus_id="MV_1",
    lv_bus_id="LV_1",
    sn_mva=0.5,
    vn_hv_kv=22.0,
    vn_lv_kv=0.4,
    vk_percent=4.0,      # Short-circuit voltage
    vkr_percent=1.2,     # Resistive component
    name="Custom_TX"
)
builder.add_transformer(trafo_config)
```

---

## Geographic Coordinates Reference

### Bangkok & Central Thailand

| Location | Latitude | Longitude | Authority |
|----------|---------|-----------|-----------|
| Bangkok (Bang Khen) | 13.8788 | 100.6025 | MEA |
| Bangkok (Pathum Wan) | 13.7465 | 100.5347 | MEA |
| Bangkok (Lat Krabang) | 13.7297 | 100.7469 | MEA |
| Ayutthaya | 14.3532 | 100.5775 | PEA |
| Pathum Thani | 14.0208 | 100.5250 | PEA |
| Nonthaburi | 13.8621 | 100.5144 | MEA |
| Samut Prakan | 13.5991 | 100.5998 | MEA |

### Other Regions

| Location | Latitude | Longitude | Authority |
|----------|---------|-----------|-----------|
| Chiang Mai | 18.7883 | 98.9853 | PEA North |
| Nakhon Ratchasima | 14.9799 | 102.0977 | PEA Northeast |
| Phuket | 7.8804 | 98.3923 | PEA South |
| Hat Yai | 7.0089 | 100.4744 | PEA South |

---

## Troubleshooting

### Power Flow Divergence

**Problem:** Power flow fails to converge.

**Solutions:**
1. Check R/X ratios (should be >0.1 for distribution networks)
2. Reduce line lengths or increase cable sizes
3. Add more transformer capacity
4. Use `pp.runpp(net, calculate_voltage_angles=True)`

### Voltage Violations

**Problem:** Bus voltages outside ±5% limits.

**Solutions:**
1. Increase transformer capacity
2. Reduce feeder length
3. Use larger cable cross-sections
4. Add voltage regulators or capacitors

### Missing pandapower Standard Types

**Problem:** `ValueError: Standard type X not found`

**Solution:** Use available pandapower standard types:
```python
# Check available types
import pandapower as pp
print(pp.available_std_types())

# Common alternatives:
# MV: "NA2XS2Y 1x185 RM/25 12/20 kV"
# LV: "NAYY 4x50 SE", "NAYY 4x150 SE"
```

---

## References

### Thai Standards
- **MEA Distribution Standards**: Metropolitan Electricity Authority
- **PEA Distribution Standards**: Provincial Electricity Authority
- **EGAT Transmission Standards**: Electricity Generating Authority of Thailand
- **Thai Electrical Code**: มาตรฐานการติดตั้งทางไฟฟ้า

### Technical References
- pandapower documentation: https://pandapower.readthedocs.io/
- IEC 60502: Power cables with extruded insulation
- IEEE 1547: Interconnection standards (for DER integration)

---

## License

Part of the GridTokenX Ecosystem - Proprietary

---

_Maintained by the GridTokenX Engineering Team._
