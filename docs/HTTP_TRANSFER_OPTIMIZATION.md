# HTTP Transfer Data Optimization

## Overview

The HTTP transport layer has been refactored to support efficient grid physics monitoring while maintaining backward compatibility with full telemetry requirements.

## Payload Modes

### 1. Monitoring Mode (Default)
**Purpose**: Real-time grid monitoring and microgrid optimization  
**Size**: ~15 fields, ~400-500 bytes per reading  
**Use Case**: High-frequency meter readings for voltage stability, power quality, and grid balance monitoring

**Fields Included**:
```python
{
    # Identity & Energy
    "meter_serial": str,
    "meter_id": str,
    "kwh": float,              # Net energy (generation - consumption)
    "timestamp": str,
    
    # Energy Metrics
    "energy_generated": float,
    "energy_consumed": float,
    
    # Grid Physics (essential for stability monitoring)
    "voltage": float,          # Voltage level (pu)
    "frequency": float,        # Grid frequency (Hz)
    "power_factor": float,     # Power quality indicator
    
    # Power Quality
    "thd_voltage": float,      # Total Harmonic Distortion - Voltage
    "thd_current": float,      # Total Harmonic Distortion - Current
    
    # Location (for zone-based optimization)
    "zone_id": str,
    "latitude": float,
    "longitude": float,
    
    # Battery State
    "battery_level": float,    # SoC for dispatch optimization
}
```

**Optimizations**:
- ✅ Removed P2P trading fields (`max_sell_price`, `max_buy_price`)
- ✅ Removed certification fields (`rec_eligible`, `carbon_offset`, `net_emission`)
- ✅ Skips zero net energy readings (optimization for network efficiency)
- ✅ Compact payload for high-frequency transmission

### 2. Full Telemetry Mode
**Purpose**: Complete data for detailed analysis, reporting, and blockchain integration  
**Size**: ~30+ fields, ~800-1000 bytes per reading  
**Use Case**: Periodic detailed reporting, audit trails, renewable energy certification

**Additional Fields**:
```python
{
    # All monitoring mode fields, PLUS:
    
    # Extended Identity
    "meter_type": str,
    "wallet_address": str,
    "meter_signature": str,
    
    # Extended Energy Data
    "surplus_energy": float,
    "deficit_energy": float,
    "total_energy_generated": float,
    "total_energy_consumed": float,
    
    # Extended Electrical Parameters
    "current": float,
    "temperature": float,
    
    # Environmental
    "weather_condition": str,
    
    # Renewable Energy Certification
    "rec_eligible": bool,
    "carbon_offset": float,
    "net_emission": float,
}
```

## Configuration

### Container Setup
```python
# In src/app/container.py
http_transport = HttpTransport(
    base_url=settings.api_gateway_url,
    api_key=settings.api_key,
    payload_mode='monitoring',  # or 'full'
)
```

### Runtime Usage
```python
# Monitoring mode (default)
reading = EnergyReading(...)
payload = reading.to_grid_monitoring_payload()

# Full telemetry mode
payload = reading.to_full_telemetry_payload()

# Default submission (uses monitoring mode)
payload = reading.to_submission_payload()
```

## Transfer Statistics

The HTTP transport now tracks detailed statistics:

```python
transport.get_transfer_stats()
# Returns:
{
    'sent': 1234,
    'failed': 5,
    'success_rate': '99.6%',
    'total_bytes': 567890,
    'avg_bytes_per_reading': 460.5,
    'payload_mode': 'monitoring'
}
```

## Architecture Rationale

### Why Two Payload Modes?

**Grid Physics Focus**:
- The simulator now focuses on **realistic grid simulation** and **microgrid optimization**
- P2P energy matching and trading are handled by **API Gateway** and **Blockchain**
- Real-time grid monitoring requires high-frequency data with minimal latency

**Separation of Concerns**:
```
┌─────────────────────────────────────────────────────────────┐
│ Smart Meter Simulator                                       │
│ ├─ Grid Physics (voltage, frequency, THD)                   │
│ ├─ Power Flow Analysis (Pandapower)                         │
│ ├─ Microgrid Optimization (battery dispatch, zone balance)  │
│ └─ Monitoring Payload → API Gateway                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ API Gateway + Blockchain                                    │
│ ├─ P2P Energy Matching (pricing, quantum algorithms)        │
│ ├─ Token Minting/Burning (based on net kWh)                 │
│ ├─ REC Certification (carbon offsets, emissions)            │
│ └─ Trade Settlement                                         │
└─────────────────────────────────────────────────────────────┘
```

### Performance Comparison

**Before Refactoring**:
- Single payload: ~1000 bytes
- All P2P fields included even when unused
- Zero-energy readings transmitted unnecessarily

**After Refactoring** (Monitoring Mode):
- Optimized payload: ~450 bytes (**55% reduction**)
- Only grid-essential fields
- Zero-energy readings skipped
- **Result**: 2.2x more readings per MB of network bandwidth

### Example Network Efficiency

**Scenario**: 10,000 smart meters, 1 reading/minute

| Mode | Bytes/Reading | MB/Hour | MB/Day | GB/Month |
|------|---------------|---------|---------|----------|
| Old Payload | 1000 | 600 | 14.4 | 432 |
| Monitoring Mode | 450 | 270 | 6.5 | 195 |
| **Savings** | -55% | -55% | -55% | **-237 GB** |

## Migration Guide

### For Existing Systems

The `to_submission_payload()` method now defaults to monitoring mode but maintains the same interface:

```python
# No code changes needed - automatically uses monitoring mode
reading = EnergyReading(...)
payload = reading.to_submission_payload()  # Returns monitoring payload
```

### For Systems Requiring Full Telemetry

If your API Gateway expects all fields, switch to full mode:

```python
# Option 1: Configure transport mode
http_transport = HttpTransport(
    base_url=url,
    payload_mode='full'
)

# Option 2: Explicit method call
payload = reading.to_full_telemetry_payload()
```

## API Gateway Compatibility

### Monitoring Payload
The monitoring payload is **fully compatible** with minimal API Gateway expectations:

```typescript
// API Gateway minimal schema
interface MeterReading {
  meter_serial: string;
  kwh: number;
  timestamp: string;
  voltage: number;
  frequency: number;
  // ... all monitoring fields supported
}
```

### Full Telemetry Payload
Supports extended blockchain integration:

```typescript
// Extended schema for blockchain
interface BlockchainMeterReading extends MeterReading {
  wallet_address: string;
  meter_signature: string;
  rec_eligible: boolean;
  carbon_offset: number;
  // ... certification fields
}
```

## Testing

### Validate Payload Mode

```python
# Test monitoring mode
reading = create_test_reading()
monitoring = reading.to_grid_monitoring_payload()
assert 'max_sell_price' not in monitoring  # P2P field removed
assert 'voltage' in monitoring             # Grid physics retained

# Test full mode
full = reading.to_full_telemetry_payload()
assert 'rec_eligible' in full              # Certification included
assert len(full) > len(monitoring)         # More comprehensive

# Test backward compatibility
default = reading.to_submission_payload()
assert default == monitoring               # Defaults to monitoring
```

### Monitor Transfer Stats

```python
# Check efficiency improvements
stats = http_transport.get_transfer_stats()
print(f"Average payload size: {stats['avg_bytes_per_reading']:.0f} bytes")
print(f"Success rate: {stats['success_rate']}")
print(f"Total bandwidth saved: {stats['total_bytes'] / 1024 / 1024:.1f} MB")
```

## Related Documentation

- [Grid State Models](../src/app/models/grid_state.py) - Grid physics state representation
- [Physics Engine](../src/app/simulation/engine.py) - Grid simulation and optimization
- [Transport Layer](../src/app/transport/) - Multi-transport architecture

## Future Enhancements

### Planned Features

1. **Adaptive Payload Compression**
   - Gzip compression for payloads > 1KB
   - Protocol buffer (protobuf) support for binary encoding

2. **Batched Transmission**
   - Batch multiple readings into single HTTP POST
   - Configurable batch size (e.g., 10 readings/request)

3. **Delta Encoding**
   - Only send changed fields for high-frequency updates
   - Reference timestamp for delta base

4. **Edge Computing Integration**
   - Local aggregation at zone level
   - Send aggregated zone metrics instead of individual meters

### Estimated Impact

| Enhancement | Bandwidth Savings | Latency Improvement |
|-------------|-------------------|---------------------|
| Gzip Compression | 60-70% | -5% (CPU overhead) |
| Batching (10x) | 30-40% | +10ms (buffering) |
| Delta Encoding | 80-90% | +2% (computation) |
| Edge Aggregation | 95%+ | Variable |

---

**Last Updated**: 2024-01  
**Version**: 1.0  
**Author**: GridTokenX Platform Team
