# Smart Meter Model Architecture

**Location:** [`src/smart_meter_simulator/core/meter.py`](../src/smart_meter_simulator/core/meter.py)

This document describes the smart meter implementation in the simulator.

## Class Overview

```python
class SmartMeter:
    """
    Represents a single smart meter with:
    - Ed25519 keypair for cryptographic signing
    - Accuracy class modeling (ANSI C12.20)
    - Frequency-watt droop control
    - VPP dispatch setpoint handling
    - Battery/EV logic
    """
```

## Meter Types

### Supported Types

| Type | Description | Accuracy Class | Channels |
|------|-------------|----------------|----------|
| `Solar_Prosumer` | Solar + grid consumption | CLASS_1_0 | P, Q, V |
| `Grid_Consumer` | Grid-only consumption | CLASS_2_0 | P, Q, V |
| `Hybrid_Prosumer` | Solar + battery + grid | CLASS_1_0 | P, Q, V, Battery |
| `Battery_Storage` | Standalone battery | CLASS_0_5 | P, Q, V, Battery |
| `EV_Charger` | Electric vehicle charging | CLASS_1_0 | P, Q, V |
| `Residential` | Standard residential | CLASS_2_0 | P, Q, V |
| `Commercial` | Commercial/industrial | CLASS_1_0 | P, Q, V |
| `Feeder` | Feeder head metering | CLASS_0_5 | P, Q, V, I |
| `Substation` | Substation metering | CLASS_0_2 | P, Q, V, I, F |

### Meter Type Distribution

Default distribution (configurable):

```python
METER_DISTRIBUTION = {
    'Solar_Prosumer': 0.40,
    'Grid_Consumer': 0.35,
    'Hybrid_Prosumer': 0.20,
    'Battery_Storage': 0.05,
    'EV_Charger': 0.00
}
```

## Accuracy Classes

### ANSI C12.20 Standard

```python
class AccuracyClass(Enum):
    CLASS_0_2 = 0.002  # ±0.2% (substation meters)
    CLASS_0_5 = 0.005  # ±0.5% (feeder head meters)
    CLASS_1_0 = 0.010  # ±1.0% (commercial meters)
    CLASS_2_0 = 0.020  # ±2.0% (residential meters)
```

### Standard Deviation Calculation

```python
def calculate_std_dev(self, value: float) -> float:
    """
    Calculate standard deviation from accuracy class.
    
    σ = (accuracy_class / 300) × |value|
    
    Example: CLASS_1_0 (1.0) with 5.0 kW reading
    σ = (1.0 / 300) × 5000 = 16.67 W
    """
    return (self.accuracy_class.value / 300.0) * abs(value)
```

### Measurement Noise Model

```python
def apply_measurement_noise(self, true_value: float) -> float:
    """
    Apply Gaussian noise based on accuracy class.
    
    z = h(x_true) + ε
    ε ~ N(0, σ²)
    """
    sigma = self.calculate_std_dev(true_value)
    noise = np.random.normal(0, sigma)
    return true_value + noise
```

## Cryptographic Signing

### Ed25519 Keypair Generation

```python
def generate_keypair(self) -> Tuple[bytes, bytes]:
    """
    Generate Ed25519 keypair for signing.
    
    Returns:
        private_key: 32-byte private key
        public_key: 32-byte public key
    """
    private_key = ed25519.SigningKey.generate()
    public_key = private_key.get_verifying_key()
    return private_key, public_key
```

### Reading Signature

```python
def sign_reading(self, reading: dict) -> str:
    """
    Sign energy reading with Ed25519.
    
    Signature covers:
    - timestamp
    - meter_id
    - energy values
    - voltage, current, frequency
    """
    # Create canonical representation
    message = self.canonicalize(reading)
    
    # Sign with private key
    signature = self.private_key.sign(message)
    
    return base64.b64encode(signature).decode()
```

### Solana Compatibility

Ed25519 signatures are compatible with Solana blockchain:

```python
# Solana verification
from solana.transaction import Signature

signature = Signature(signature_bytes)
public_key = PublicKey(public_key_bytes)

# Verify signature
is_valid = signature.verify(public_key, message)
```

## Measurement Channels

### Active Power (P)

```python
class ActivePowerChannel:
    """
    Active power measurement channel.
    
    Sign Convention:
    - Positive P (generation): Exporting to grid
    - Negative P (consumption): Importing from grid
    
    Units: kW
    Accuracy: Based on meter accuracy class
    """
```

### Reactive Power (Q)

```python
class ReactivePowerChannel:
    """
    Reactive power measurement channel.
    
    Sign Convention:
    - Positive Q: Inductive load (lagging PF)
    - Negative Q: Capacitive load (leading PF)
    
    Units: kVAR
    """
```

### Voltage (V)

```python
class VoltageChannel:
    """
    Voltage magnitude measurement.
    
    Nominal Values:
    - Single-phase: 230V (Thailand)
    - Three-phase: 400V (line-to-line)
    
    Units: V
    Accuracy: Typically ±0.5%
    """
```

### Current (I)

```python
class CurrentChannel:
    """
    Current magnitude measurement.
    
    Typical Ranges:
    - Residential: 0-100A
    - Commercial: 0-1000A
    
    Units: A
    """
```

### Frequency (F)

```python
class FrequencyChannel:
    """
    Grid frequency measurement.
    
    Nominal: 50.0 Hz (Thailand)
    Normal Range: 49.5-50.5 Hz
    Accuracy: ±0.01 Hz
    """
```

### Battery State

```python
class BatteryChannel:
    """
    Battery state of charge measurement.
    
    Parameters:
    - capacity_kwh: Total battery capacity
    - soc_kwh: Current state of charge
    - soc_percent: State of charge percentage
    - charge_rate_kw: Current charge/discharge rate
    
    Efficiency: 90-95% (round-trip)
    """
```

## Frequency-Watt Droop Control

### Droop Characteristics

```python
class FrequencyWattDroop:
    """
    Frequency-watt droop control for grid stability.
    
    Parameters:
    - droop_percent: 5% (typical)
    - deadband_hz: ±0.05 Hz
    - max_adjustment: ±10% of rated power
    
    Response:
    - f > 50.05 Hz: Reduce generation
    - f < 49.95 Hz: Increase generation
    """
```

### Implementation

```python
def calculate_droop_response(self, frequency_hz: float) -> float:
    """
    Calculate power adjustment based on frequency deviation.
    
    Returns:
        adjustment_kw: Power adjustment (positive = increase)
    """
    deadband = 0.05  # Hz
    droop = 0.05     # 5% droop
    
    deviation = frequency_hz - 50.0
    
    # Check deadband
    if abs(deviation) < deadband:
        return 0.0
    
    # Calculate adjustment
    if deviation > 0:
        # Frequency high - reduce generation
        adjustment = -self.rated_power * (deviation / droop)
    else:
        # Frequency low - increase generation
        adjustment = self.rated_power * (abs(deviation) / droop)
    
    return max(-self.max_adjustment, min(self.max_adjustment, adjustment))
```

## Battery Logic

### Charging/Discharging

```python
class BatteryLogic:
    """
    Battery charge/discharge control logic.
    
    Constraints:
    - soc_min: 10% (prevent deep discharge)
    - soc_max: 90% (prevent overcharge)
    - max_charge_rate: C/2 (2-hour rate)
    - max_discharge_rate: C/2
    
    Efficiency:
    - charge_efficiency: 95%
    - discharge_efficiency: 95%
    """
```

### VPP Dispatch

```python
async def apply_vpp_setpoint(self, setpoint: dict):
    """
    Apply VPP dispatch setpoint.
    
    Setpoint Format:
    {
        "mode": "charge" | "discharge" | "hold",
        "power_kw": 5.0,
        "duration_minutes": 30
    }
    """
    if setpoint['mode'] == 'charge':
        await self.charge(setpoint['power_kw'])
    elif setpoint['mode'] == 'discharge':
        await self.discharge(setpoint['power_kw'])
```

## Reading Generation

### Complete Reading

```python
def generate_reading(self) -> EnergyReading:
    """
    Generate complete energy reading.
    
    Returns:
        EnergyReading with:
        - timestamp (UTC)
        - meter_id
        - energy_generated_kwh
        - energy_consumed_kwh
        - battery_level_kwh (if applicable)
        - voltage_v
        - current_a
        - frequency_hz
        - signature (Ed25519)
        - public_key
    """
    reading = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'meter_id': self.meter_id,
        'energy_generated_kwh': self.generation_channel.read(),
        'energy_consumed_kwh': self.consumption_channel.read(),
        'voltage_v': self.voltage_channel.read(),
        'current_a': self.current_channel.read(),
        'frequency_hz': self.frequency_channel.read(),
    }
    
    # Add battery if applicable
    if self.has_battery:
        reading['battery_level_kwh'] = self.battery_channel.read()
    
    # Sign reading
    reading['signature'] = self.sign_reading(reading)
    reading['public_key'] = self.public_key_hex
    
    return EnergyReading(**reading)
```

## Configuration

### Meter Configuration Schema

```python
class MeterConfig(BaseModel):
    """Smart meter configuration."""
    
    meter_id: str
    meter_type: MeterType
    accuracy_class: AccuracyClass
    rated_power_kw: float
    voltage_nominal_v: float = 230.0
    frequency_nominal_hz: float = 50.0
    
    # Optional battery
    battery_capacity_kwh: Optional[float] = None
    battery_efficiency: float = 0.95
    
    # Optional solar
    solar_capacity_kwp: Optional[float] = None
    solar_efficiency: float = 0.90
    
    # Geographic
    latitude: Optional[float] = None
    longitude: Optional[float] = None
```

### Example Configuration

```python
config = MeterConfig(
    meter_id="AMI_METER_001",
    meter_type=MeterType.SOLAR_PROSUMER,
    accuracy_class=AccuracyClass.CLASS_1_0,
    rated_power_kw=5.0,
    solar_capacity_kwp=5.0,
    battery_capacity_kwh=10.0,
    latitude=13.7563,  # Bangkok
    longitude=100.5018
)
```

## Testing

### Unit Tests

```python
@pytest.mark.unit
def test_meter_reading_generation(meter):
    reading = meter.generate_reading()
    
    assert reading.meter_id == meter.meter_id
    assert reading.signature is not None
    assert reading.public_key is not None
    assert reading.timestamp is not None

@pytest.mark.crypto
def test_reading_signature_verification(meter):
    reading = meter.generate_reading()
    
    # Verify signature
    is_valid = meter.verify_signature(reading)
    assert is_valid == True
```

## Related Documents

- [System Overview](overview.md)
- [Simulation Engine](simulation-engine.md)
- [Accuracy Classes Reference](../reference/accuracy-classes.md)
