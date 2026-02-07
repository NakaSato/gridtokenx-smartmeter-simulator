# Data Models

This document describes the data models used in the Smart Meter Simulator.

## Core Models

### EnergyReading

The primary data model for meter readings.

**Location**: [models/reading.py](../src/app/models/reading.py)

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class EnergyReading(BaseModel):
    """Data model for a single smart meter reading."""
    
    # Identification
    meter_id: str
    timestamp: datetime
    
    # Energy Data (kWh)
    energy_generated: float = Field(..., ge=0)
    energy_consumed: float = Field(..., ge=0)
    surplus_energy: float = Field(..., ge=0)
    deficit_energy: float = Field(..., ge=0)
    
    # Battery Data
    battery_level: float = Field(0.0, ge=0, le=100)
    
    # Electrical Parameters (Optional)
    voltage: Optional[float] = Field(None, ge=0)
    current: Optional[float] = Field(None, ge=0)
    power_factor: Optional[float] = Field(None, ge=0, le=1)
    frequency: Optional[float] = Field(None, ge=0)
    temperature: Optional[float] = Field(None, ge=-50, le=60)
    
    # Metadata
    location: str
    meter_type: str
    user_type: str
    wallet_address: Optional[str] = None
    
    # Trading Data
    max_sell_price: Optional[float] = Field(None, ge=0)
    max_buy_price: Optional[float] = Field(None, ge=0)
    rec_eligible: bool = False
    carbon_offset: float = Field(0.0, ge=0)
    weather_condition: str = "Sunny"
    
    # Security
    meter_signature: Optional[str] = None
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `meter_id` | str | Unique identifier for the meter |
| `timestamp` | datetime | Reading timestamp (UTC) |
| `energy_generated` | float | Energy generated in kWh |
| `energy_consumed` | float | Energy consumed in kWh |
| `surplus_energy` | float | Net positive energy (generation > consumption) |
| `deficit_energy` | float | Net negative energy (consumption > generation) |
| `battery_level` | float | Current battery charge (0-100%) |
| `voltage` | float | Voltage magnitude in volts |
| `current` | float | Current magnitude in amperes |
| `power_factor` | float | Power factor (0-1) |
| `frequency` | float | Grid frequency in Hz |
| `temperature` | float | Device temperature in Celsius |
| `location` | str | Physical location identifier |
| `meter_type` | str | Type of meter (e.g., "Solar_Prosumer") |
| `user_type` | str | User classification |
| `wallet_address` | str | Solana wallet address for token minting |
| `max_sell_price` | float | Maximum price willing to sell ($/kWh) |
| `max_buy_price` | float | Maximum price willing to buy ($/kWh) |
| `rec_eligible` | bool | Eligible for Renewable Energy Certificates |
| `carbon_offset` | float | CO2 offset in kg |
| `weather_condition` | str | Current weather condition |
| `meter_signature` | str | Ed25519 signature for data integrity |

### Methods

#### `to_submission_payload()`

Convert to API Gateway submission format for blockchain integration:

```python
def to_submission_payload(self) -> dict:
    """Convert to API Gateway submission format."""
    kwh_amount = max(0.0, self.surplus_energy)
    
    return {
        "wallet_address": self.wallet_address,
        "kwh_amount": f"{kwh_amount:.6f}",
        "reading_timestamp": self.timestamp.isoformat(),
        "meter_signature": self.meter_signature,
        "meter_serial": self.meter_id
    }
```

### JSON Serialization

```python
reading = EnergyReading(
    meter_id="M001",
    timestamp=datetime.now(timezone.utc),
    energy_generated=2.5,
    energy_consumed=1.2,
    surplus_energy=1.3,
    deficit_energy=0,
    location="Zone_1",
    meter_type="Solar_Prosumer",
    user_type="residential"
)

# To JSON
json_str = reading.model_dump_json()

# To dict
data_dict = reading.model_dump()
```

---

## MeasurementChannel Enum

Defines available measurement channels for smart meters.

```python
class MeasurementChannel(str, Enum):
    """Available measurement channels for smart meters."""
    VOLTAGE = "v"           # Voltage magnitude
    ACTIVE_POWER = "p"      # Active power
    REACTIVE_POWER = "q"    # Reactive power
    CURRENT = "i"           # Current magnitude
    CURRENT_ANGLE = "ia"    # Current angle
    VOLTAGE_ANGLE = "va"    # Voltage angle
```

---

## Configuration Models

### SmartMeter Configuration

Configuration dictionary structure for SmartMeter initialization:

```python
meter_config = {
    "meter_id": str,           # Required: Unique identifier
    "meter_type": str,         # Required: MeterType enum value
    "location": str,           # Required: Physical location
    "user_type": str,          # Required: User classification
    
    # Optional solar configuration
    "has_solar": bool,         # Default: False
    "solar_capacity": float,   # kW capacity
    "panel_efficiency": float, # 0.0-1.0
    
    # Optional battery configuration
    "has_battery": bool,       # Default: False
    "battery_capacity": float, # kWh capacity
    "battery_efficiency": float, # 0.0-1.0
    "current_battery_level": float, # 0-100%
    
    # Trading configuration
    "max_sell_price": float,   # $/kWh
    "max_buy_price": float,    # $/kWh
    "wallet_address": str,     # Solana wallet
    
    # Grid configuration
    "accuracy_class": str,     # AccuracyClass enum value
}
```

---

## Analytics Models

### GridHealthReport

Report structure for grid health analytics.

**Location**: [core/analytics.py](../src/app/core/analytics.py)

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List

@dataclass
class GridHealthReport:
    timestamp: datetime
    total_loss_mw: float
    avg_voltage_pu: float
    max_voltage_pu: float
    min_voltage_pu: float
    num_violations: int
    violations: List[Dict[str, Any]] = field(default_factory=list)
    loss_percentage: float = 0.0
```

### Violation Structure

```python
violation = {
    "bus_idx": int,       # Bus index in network
    "bus_name": str,      # Bus name
    "type": str,          # "overvoltage" or "undervoltage"
    "value": float,       # Actual voltage (p.u.)
    "limit": float,       # Violated limit
}
```

---

## State Estimation Models

### EstimationResults

Results from state estimation.

**Location**: [adapters/state_estimator.py](../src/app/adapters/state_estimator.py)

```python
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd

@dataclass
class EstimationResults:
    converged: bool                        # Whether estimation converged
    iterations: int                        # Number of iterations
    residuals: pd.DataFrame               # Measurement residuals
    estimated_voltages: pd.DataFrame      # Estimated bus voltages
    bad_data_detected: List[str]          # List of bad measurement names
    num_measurements: int = 0             # Total measurements used
    chi2_statistic: Optional[float] = None # Chi-squared test statistic
    mean_absolute_error: Optional[float] = None
    max_residual: Optional[float] = None
    v_deviation_avg: Optional[float] = None
    total_losses_mw: Optional[float] = None
```

### AccuracyMetrics

ANSI C12.20 accuracy metrics.

```python
@dataclass
class AccuracyMetrics:
    measurement_name: str
    true_value: float
    estimated_value: float
    error_percent: float
    std_dev: float
    within_tolerance: bool
    tolerance_percent: float = 2.0
```

---

## Topology Models

### BusConfig

Configuration for network buses.

**Location**: [adapters/topology_builder.py](../src/app/adapters/topology_builder.py)

```python
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class BusConfig:
    bus_id: str
    voltage_level: VoltageLevel
    vn_kv: float
    name: Optional[str] = None
    zone: Optional[str] = None
    geo_data: Optional[Dict[str, float]] = None
```

### LineConfig

Configuration for network lines.

```python
@dataclass
class LineConfig:
    from_bus_id: str
    to_bus_id: str
    length_km: float
    std_type: str = "NAYY 4x50 SE"
    name: Optional[str] = None
    parallel: int = 1
```

### TransformerConfig

Configuration for transformers.

```python
@dataclass
class TransformerConfig:
    hv_bus_id: str
    lv_bus_id: str
    sn_mva: float
    vn_hv_kv: float
    vn_lv_kv: float
    std_type: Optional[str] = None
    name: Optional[str] = None
```

---

## Pandapower Measurement Schema

Structure of entries in `net.measurement` DataFrame.

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Measurement identifier (e.g., "M001_V") |
| `measurement_type` | str | Type: "v", "p", "q", "i" |
| `element_type` | str | Element: "bus", "load", "sgen", "line" |
| `element` | int | Index of element in network |
| `value` | float | Measured value |
| `std_dev` | float | Standard deviation |
| `side` | str | Side for branch measurements ("from"/"to") |

---

## API Response Models

### Status Response

```python
{
    "status": str,           # "running" or "stopped"
    "running": bool,
    "paused": bool,
    "meters": List[MeterInfo],
    "num_meters": int,
    "mode": str,
    "api_gateway": str,
    "grid_metrics": GridMetrics,
    "websocket_clients": int
}
```

### MeterInfo

```python
{
    "meter_id": str,
    "name": str,
    "location": str,
    "capacity": float,
    "current_generation": float,
    "current_consumption": float,
    "energy_type": str,
    "status": str
}
```

### GridMetrics

```python
{
    "converged": bool,
    "num_measurements": int,
    "chi2": float,
    "v_deviation_avg": float
}
```

### Control Response

```python
{
    "success": bool,
    "message": str,
    "status": {
        "running": bool,
        "paused": bool,
        "num_meters": int
    }
}
```

---

## WebSocket Message Models

### MeterReadings Message

```python
{
    "type": "meter_readings",
    "timestamp": str,  # ISO format
    "readings": List[EnergyReading]
}
```

### GridStatus Message

```python
{
    "type": "grid_status",
    "converged": bool,
    "num_measurements": int,
    "v_deviation_avg": float,
    "total_losses_mw": float
}
```

---

## Validation

All Pydantic models include built-in validation:

```python
from pydantic import ValidationError

try:
    reading = EnergyReading(
        meter_id="M001",
        timestamp=datetime.now(timezone.utc),
        energy_generated=-1.0,  # Invalid: must be >= 0
        energy_consumed=1.0,
        surplus_energy=0,
        deficit_energy=0,
        location="Zone_1",
        meter_type="Solar_Prosumer",
        user_type="residential"
    )
except ValidationError as e:
    print(e.json())
```

Output:
```json
[
  {
    "loc": ["energy_generated"],
    "msg": "ensure this value is greater than or equal to 0",
    "type": "value_error.number.not_ge"
  }
]
```
