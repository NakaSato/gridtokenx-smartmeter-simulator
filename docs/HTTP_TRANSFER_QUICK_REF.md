# HTTP Transfer Quick Reference

## 🚀 Quick Start

### Default (Monitoring Mode) - Recommended
```python
# No changes needed! Automatically uses optimized monitoring payload
reading = EnergyReading(...)
payload = reading.to_submission_payload()  # → 376 bytes
```

### Full Telemetry Mode
```python
# Option 1: Configure transport globally
http_transport = HttpTransport(
    base_url=url,
    payload_mode='full'  # 775 bytes
)

# Option 2: Per-reading control
payload = reading.to_full_telemetry_payload()
```

## 📊 Payload Comparison

| Feature | Monitoring | Full |
|---------|-----------|------|
| **Size** | 376 bytes | 775 bytes |
| **Fields** | 15 | 29 |
| **Use Case** | Real-time monitoring | Detailed analysis |
| **Frequency** | High (1/min) | Low (periodic) |

## 🎯 When to Use Each Mode

### Monitoring Mode ✅
- ✅ Real-time grid monitoring
- ✅ High-frequency data collection
- ✅ Voltage/frequency stability tracking
- ✅ Power quality (THD) monitoring
- ✅ Battery dispatch optimization
- ✅ Zone-based grid balance

### Full Telemetry Mode 📈
- 📈 Detailed performance reports
- 📈 Blockchain transaction records
- 📈 REC certification submissions
- 📈 Carbon offset calculations
- 📈 Audit trails & compliance
- 📈 Historical data archiving

## 📝 Payload Fields

### Monitoring (15 fields)
```yaml
Identity:     meter_serial, meter_id, timestamp
Energy:       kwh, energy_generated, energy_consumed
Grid Physics: voltage, frequency, power_factor, thd_voltage, thd_current
Optimization: battery_level, zone_id, latitude, longitude
```

### Full Telemetry (+14 fields)
```yaml
All monitoring fields, PLUS:

Extended Identity: meter_type, wallet_address, meter_signature
Extended Energy:   surplus_energy, deficit_energy, total_*_generated/consumed
Electrical:        current, temperature
Environmental:     weather_condition
Certification:     rec_eligible, carbon_offset, net_emission
```

## 🔧 Configuration Examples

### Container Setup
```python
# src/app/container.py

# Development (complete data)
http_transport = HttpTransport(
    base_url="http://localhost:3000",
    payload_mode='full'
)

# Production (optimized)
http_transport = HttpTransport(
    base_url="https://api.gridtokenx.com",
    payload_mode='monitoring'
)
```

### Runtime Selection
```python
# Conditional payload mode
from datetime import datetime

def get_payload_mode():
    hour = datetime.now().hour
    
    # Full telemetry during off-peak hours for archiving
    if 0 <= hour < 6:
        return 'full'
    
    # Monitoring during peak hours for efficiency
    return 'monitoring'

http_transport = HttpTransport(
    base_url=url,
    payload_mode=get_payload_mode()
)
```

## 📈 Statistics API

```python
stats = http_transport.get_transfer_stats()

# Available metrics
stats['sent']                    # Total successful sends
stats['failed']                  # Total failures
stats['success_rate']            # "99.8%"
stats['total_bytes']             # Total bandwidth used
stats['avg_bytes_per_reading']   # Average payload size
stats['payload_mode']            # Current mode
```

## 🎨 Code Examples

### Basic Usage
```python
from src.app.models.reading import EnergyReading
from datetime import datetime

reading = EnergyReading(
    meter_id="METER_001",
    timestamp=datetime.now(),
    energy_generated=15.5,
    energy_consumed=10.2,
    surplus_energy=5.3,
    deficit_energy=0.0,
    voltage=230.5,
    frequency=50.0,
    # ... other required fields
)

# Default: monitoring mode
payload = reading.to_submission_payload()
print(f"Size: {len(json.dumps(payload))} bytes")  # ~376 bytes
```

### Explicit Mode Selection
```python
# Force monitoring mode
monitoring_payload = reading.to_grid_monitoring_payload()

# Force full telemetry
full_payload = reading.to_full_telemetry_payload()

# Compare sizes
print(f"Monitoring: {len(json.dumps(monitoring_payload))} bytes")
print(f"Full:       {len(json.dumps(full_payload))} bytes")
```

### Transport with Statistics
```python
from src.app.transport.http import HttpTransport

transport = HttpTransport(
    base_url="https://api.gridtokenx.com",
    payload_mode='monitoring'
)

await transport.connect()

# Send readings
for reading in meter.get_readings():
    success = await transport.send_reading(reading)
    if success:
        print("✓ Sent")

# Check statistics
stats = transport.get_transfer_stats()
print(f"Success rate: {stats['success_rate']}")
print(f"Avg size: {stats['avg_bytes_per_reading']:.0f} bytes")
```

## 🧪 Testing

### Validate Payload Content
```python
def test_monitoring_payload():
    reading = create_test_reading()
    payload = reading.to_grid_monitoring_payload()
    
    # Essential fields present
    assert 'voltage' in payload
    assert 'frequency' in payload
    assert 'kwh' in payload
    
    # P2P fields removed
    assert 'max_sell_price' not in payload
    assert 'max_buy_price' not in payload
    assert 'rec_eligible' not in payload
    
    print("✓ Monitoring payload validated")
```

### Compare Payload Sizes
```python
def test_payload_sizes():
    reading = create_test_reading()
    
    monitoring = reading.to_grid_monitoring_payload()
    full = reading.to_full_telemetry_payload()
    
    monitoring_size = len(json.dumps(monitoring))
    full_size = len(json.dumps(full))
    
    assert monitoring_size < full_size
    assert monitoring_size < 500  # Should be ~376 bytes
    assert full_size < 900         # Should be ~775 bytes
    
    reduction = (1 - monitoring_size / full_size) * 100
    print(f"✓ Monitoring mode {reduction:.1f}% smaller")
```

## 🐛 Troubleshooting

### Payload Too Large?
```python
# Switch to monitoring mode
http_transport = HttpTransport(
    base_url=url,
    payload_mode='monitoring'  # ← Change this
)
```

### Missing Fields in API Gateway?
```python
# Switch to full mode
http_transport = HttpTransport(
    base_url=url,
    payload_mode='full'  # ← Change this
)

# Or verify which fields are actually required
required_fields = ['meter_serial', 'kwh', 'timestamp', 'voltage']
payload = reading.to_grid_monitoring_payload()
assert all(field in payload for field in required_fields)
```

### Zero-Energy Readings Not Sent?
```python
# In monitoring mode, zero-energy readings are skipped for efficiency
# This is intentional! If you need all readings, use full mode:

http_transport = HttpTransport(
    base_url=url,
    payload_mode='full'  # Sends all readings, even zero-energy
)
```

## 📚 Related Documentation

- [HTTP_TRANSFER_OPTIMIZATION.md](HTTP_TRANSFER_OPTIMIZATION.md) - Complete guide
- [HTTP_TRANSFER_ARCHITECTURE.md](HTTP_TRANSFER_ARCHITECTURE.md) - Visual diagrams
- [../REFACTOR_HTTP_TRANSFER.md](../REFACTOR_HTTP_TRANSFER.md) - Refactoring summary

## 💡 Best Practices

1. **Use monitoring mode by default** - More efficient for real-time data
2. **Use full mode for archiving** - During off-peak hours or periodic reports
3. **Monitor transfer stats** - Track `get_transfer_stats()` for insights
4. **Validate API compatibility** - Ensure API Gateway accepts monitoring payload
5. **Test both modes** - Verify your system works with both payloads

## 📊 Performance Metrics

### Bandwidth Savings (10,000 meters @ 1 reading/min)
- **Per Day**: 9 GB saved
- **Per Month**: 254.5 GB saved
- **Per Year**: 3.05 TB saved

### Cost Savings (AWS Data Transfer @ $0.09/GB)
- **Per Month**: $22.91 saved
- **Per Year**: $274.92 saved
- **Per 1,000 meters/year**: $27.49 saved

### Network Efficiency
- **Monitoring Mode**: 2,789 readings/MB
- **Old Implementation**: 1,049 readings/MB
- **Improvement**: +166%

---

**Quick Tip**: Start with monitoring mode. Switch to full mode only when you need complete telemetry for specific use cases (blockchain, certification, audits).

**Status**: ✅ Production Ready  
**Version**: 1.0  
**Updated**: 2024-01
