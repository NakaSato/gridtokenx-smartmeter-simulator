# Individual Meter Status API

## New Endpoint

### GET `/api/meters/{meter_id}/status`

Get detailed status information for a specific meter.

## Usage

### Via API

```bash
# Get status for a specific meter
curl http://localhost:8000/api/meters/{meter_id}/status | jq .
```

### Via Python Script

```bash
# Show first meter's status
python get_meter_status.py

# Show specific meter's status
python get_meter_status.py abc-123-def-456
```

## Response Format

```json
{
  "meter_id": "abc-123-def-456",
  "meter_type": "Solar_Prosumer",
  "location": "Zone_1_Building_5",
  "user_type": "Prosumer",
  
  "is_connected": true,
  "connection_status": "✅ ONLINE",
  
  "config": {
    "has_solar": true,
    "solar_capacity": 10.0,
    "has_battery": true,
    "battery_capacity": 15.0,
    "trading_preference": "Moderate"
  },
  
  "current_state": {
    "battery_level": 75.5,
    "current_weather": "Sunny",
    "current_sell_price": 0.25,
    "current_buy_price": 0.30
  },
  
  "latest_reading": {
    "timestamp": "2025-11-28T03:15:00Z",
    "energy_generated": 5.5,
    "energy_consumed": 3.2,
    "surplus_energy": 2.3,
    "deficit_energy": 0.0,
    "battery_level": 75.5,
    "voltage": 240.0,
    "current": 10.5,
    "temperature": 25.0,
    "net_emission": -1.61,
    "rec_eligible": true
  },
  
  "coordinates": {
    "latitude": 13.7563,
    "longitude": 100.5018
  }
}
```

## Example Output

```
======================================================================
Individual Meter Status
======================================================================

Meter ID: abc-123-def-456
Type: Solar_Prosumer
Location: Zone_1_Building_5
User Type: Prosumer

Connection Status: ✅ ONLINE

Configuration:
  Solar Panel: Yes
  Solar Capacity: 10.0 kW
  Battery: Yes
  Battery Capacity: 15.0 kWh
  Trading Preference: Moderate

Current State:
  Battery Level: 75.5%
  Weather: Sunny
  Sell Price: $0.25/kWh
  Buy Price: $0.30/kWh

Latest Reading:
  Timestamp: 2025-11-28T03:15:00Z
  Generated: 5.5 kWh
  Consumed: 3.2 kWh
  Surplus: 2.3 kWh
  Deficit: 0.0 kWh
  Battery: 75.5%
  Voltage: 240.0 V
  Current: 10.5 A
  Temperature: 25.0 °C
  Net Emission: -1.61 kgCO2
  REC Eligible: Yes

GPS: 13.7563, 100.5018
======================================================================
```

## Error Handling

If meter is not found:

```json
{
  "error": "Meter not found",
  "meter_id": "invalid-id",
  "available_meters": ["abc-123", "def-456", "ghi-789"]
}
```

## Use Cases

1. **Debugging** - Check why a specific meter is not sending data
2. **Monitoring** - Track individual meter performance
3. **Troubleshooting** - Verify meter configuration and state
4. **Analytics** - Get detailed readings for specific meters
