# Smart Meter Connection Status Feature

## Overview

The smart meter simulator now tracks and displays the connection status of each meter to the API gateway in real-time.

## Features Added

### 1. **Meter Connection Tracking**

Each `SmartMeter` instance now has:
- `is_connected` (bool) - Updated after each data transmission attempt
- `last_reading` (EnergyReading) - Stores the most recent reading for status display

### 2. **Enhanced Status API**

The `/api/status` endpoint now returns:

```json
{
  "status": "running",
  "running": true,
  "num_meters": 20,
  "connected_meters": 18,
  "disconnected_meters": 2,
  "api_gateway": "http://127.0.0.1:8080",
  "api_gateway_connected": true,
  "meters": [
    {
      "meter_id": "abc-123",
      "name": "Solar_Prosumer",
      "location": "Zone_1_Building_5",
      "is_connected": true,
      ...
    }
  ]
}
```

**New Fields:**
- `connected_meters` - Number of meters successfully connected to API gateway
- `disconnected_meters` - Number of meters that failed to connect
- `api_gateway_connected` - Overall API gateway connectivity status
- `meters[].is_connected` - Individual meter connection status

### 3. **Connection Status Monitor Script**

Run `check_meter_status.py` to see a formatted display:

```bash
python check_meter_status.py
```

**Output:**
```
======================================================================
Smart Meter Connection Status Monitor
======================================================================

Simulator Status: RUNNING
API Gateway: http://127.0.0.1:8080
API Gateway Connected: ✅ YES

Total Meters: 20
Connected: 18 ✅
Disconnected: 2 ❌

----------------------------------------------------------------------
Meter ID                                 Location             Status    
----------------------------------------------------------------------
abc-123-def-456                          Zone_1_Building_5    ✅ ONLINE 
xyz-789-ghi-012                          Zone_2_Building_3    ❌ OFFLINE
----------------------------------------------------------------------

✅ 18 meter(s) successfully connected to API gateway
⚠️  2 meter(s) not connected to API gateway
   Check API gateway status and authentication
======================================================================
```

## How It Works

### Connection Status Update Flow

```
1. Simulator generates reading
   ↓
2. Engine sends reading via HTTP transport
   ↓
3. HTTP transport returns success/failure
   ↓
4. Engine updates meter.is_connected = True/False
   ↓
5. Status API reflects current connection state
```

### Code Changes

#### SmartMeter Class (`core/meter.py`)
```python
def __init__(self, config: Dict[str, Any]):
    # ... existing code ...
    
    # Connection status to API Gateway
    self.is_connected = False  # Updated by engine
    self.last_reading = None   # Store last reading
```

#### SimulationEngine (`core/engine.py`)
```python
async def tick(self):
    # ... generate readings ...
    
    # Send readings and update connection status
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        meter = self.meters[i]
        if result is True:
            meter.is_connected = True  # ✅ Connected
        else:
            meter.is_connected = False  # ❌ Disconnected
```

## Usage Examples

### 1. Check Status via API

```bash
curl http://localhost:8000/api/status | jq '.connected_meters'
# Output: 18
```

### 2. Monitor Connection Status

```bash
# Run the monitoring script
python check_meter_status.py
```

### 3. View in Dashboard

Access the web dashboard at `http://localhost:8000/` to see:
- Overall connection status
- Individual meter connection indicators
- Real-time updates via WebSocket

## Troubleshooting

### All Meters Show Disconnected

**Possible causes:**
1. API Gateway is not running
2. API Gateway URL is incorrect
3. Authentication token is invalid or missing
4. Network connectivity issues

**Solutions:**
```bash
# Check API Gateway health
curl http://127.0.0.1:8080/health

# Verify API Gateway URL in .env
cat .env | grep API_GATEWAY_URL

# Check simulator logs
tail -f logs/simulator.log | grep "Failed to send"
```

### Some Meters Disconnected

**Possible causes:**
1. Rate limiting on API Gateway
2. Temporary network issues
3. Invalid meter data

**Solutions:**
- Check API Gateway logs for errors
- Verify meter readings are valid
- Check for rate limit responses (HTTP 429)

## Integration with API Gateway

The connection status reflects successful HTTP POST requests to:
```
POST http://127.0.0.1:8080/api/meters/submit-reading
```

**Success Criteria:**
- HTTP 200/201 response → `is_connected = True`
- Any error response → `is_connected = False`

**Authentication:**
- Requires valid JWT token in Authorization header
- Token obtained via `/api/auth/login`
- User must have `prosumer` role

## Benefits

1. **Real-time Monitoring** - See which meters are actively sending data
2. **Troubleshooting** - Quickly identify connection issues
3. **System Health** - Overall view of simulator-to-gateway connectivity
4. **Individual Tracking** - Per-meter connection status for debugging

## Next Steps

To see the connection status in action:

1. **Start API Gateway:**
   ```bash
   cd /Users/chanthawat/Developments/gridtokenx-platform
   docker-compose restart apigateway
   ```

2. **Start Simulator:**
   ```bash
   cd gridtokenx-smartmeter-simulator
   source .venv/bin/activate
   python server.py
   ```

3. **Check Status:**
   ```bash
   python check_meter_status.py
   ```

4. **View Dashboard:**
   Open browser to `http://localhost:8000/`

---

**Feature Status**: ✅ Implemented and Ready  
**API Version**: 2.0.0  
**Last Updated**: 2025-11-28
