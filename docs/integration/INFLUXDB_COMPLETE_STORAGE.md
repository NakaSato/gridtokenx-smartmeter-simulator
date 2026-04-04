# Complete InfluxDB Integration - All Simulation Data

## 📊 **Overview**

The GridTokenX Smart Meter Simulator now stores **ALL simulation data** to InfluxDB for complete time-series history, Grafana dashboards, and historical analysis.

---

## 🗃️ **Data Stored in InfluxDB**

### **Measurements Overview**

| Measurement | Data Points | Frequency | Description |
|-------------|-------------|-----------|-------------|
| `meter_reading` | Per meter, per tick | 15s | Energy, voltage, current, battery, carbon |
| `grid_state_estimation` | Per tick | 15s | SE convergence, chi², health score |
| `vpp_cluster` | Per cluster, per tick | 15s | VPP capacity, dispatch, utilization |
| `vpp_dispatch` | Per meter, per tick | 15s | Setpoints, actual, compliance |
| `grid_frequency` | Per tick | 15s | Frequency, deviation, droop response |
| `grid_islanding` | Per tick | 15s | Mode, trigger, voltage, duration |
| `weather` | Per tick | 15s | Temperature, irradiance, cloud cover |
| `carbon_intensity` | Per tick | 15s | CO2 intensity, renewable %, offset |
| `price_history` | Per tick | 15s | ToU rates, P2P rates, FT charge |
| `simulation_step` | Per tick | 15s | Active meters, gen/cons, errors |
| `market_order` | Per order | On-demand | Bids, offers, matched volumes |
| `market_clearing` | Per clearing | On-demand | Clearing price, volume, matches |
| `demand_response` | Per event | On-demand | Target reduction, incentive, duration |
| `alert` | Per alert | On-demand | Type, severity, message, value |

---

## 🏗️ **Schema Details**

### **1. Meter Readings** (`meter_reading`)

**Tags:** `meter_id`, `meter_type`, `location`, `accuracy_class`

**Fields:**
```
energy_generated_kwh: float
energy_consumed_kwh: float
battery_level_kwh: float
battery_soc_pct: float
voltage_v: float
current_a: float
frequency_hz: float
active_power_kw: float
reactive_power_kvar: float
power_factor: float
carbon_offset_kg: float
temperature_c: float
```

---

### **2. Grid State Estimation** (`grid_state_estimation`)

**Tags:** `converged`, `algorithm`

**Fields:**
```
chi_squared: float
mae: float
max_residual: float
total_loss_mw: float
loss_pct: float
avg_voltage_pu: float
health_score: float (0-100)
violations: int
measurements_used: int
bad_data_removed: int
```

---

### **3. VPP Cluster** (`vpp_cluster`)

**Tags:** `cluster_id`, `status`

**Fields:**
```
total_capacity_kw: float
total_dispatch_kw: float
utilization_pct: float
health_score: float
carbon_saved_kg: float
num_meters: int
afrr_power_kw: float
```

---

### **4. VPP Dispatch** (`vpp_dispatch`)

**Tags:** `cluster_id`, `meter_id`, `dispatch_type`

**Fields:**
```
setpoint_kw: float
actual_kw: float
response_time_ms: float
compliance_pct: float
```

---

### **5. Grid Frequency** (`grid_frequency`)

**Tags:** `zone`

**Fields:**
```
frequency_hz: float
deviation_hz: float
droop_response_kw: float
total_generation_kw: float
total_load_kw: float
imbalance_kw: float
roc_hz_per_sec: float
```

---

### **6. Grid Islanding** (`grid_islanding`)

**Tags:** `mode`, `trigger`

**Fields:**
```
grid_voltage_v: float
island_frequency_hz: float
power_balance_kw: float
load_shed_kw: float
island_duration_s: float
reconnection_attempts: int
```

---

### **7. Weather** (`weather`)

**Tags:** `condition`, `location`

**Fields:**
```
temperature_c: float
humidity_pct: float
solar_irradiance_wm2: float
wind_speed_ms: float
cloud_cover_pct: float
solar_efficiency_pct: float
```

---

### **8. Carbon Intensity** (`carbon_intensity`)

**Tags:** `zone`

**Fields:**
```
intensity_gco2_kwh: float
renewable_pct: float
total_generation_kwh: float
total_consumption_kwh: float
carbon_offset_kg: float
carbon_cost_baht: float
```

---

### **9. Price History** (`price_history`)

**Tags:** `price_type`, `period`

**Fields:**
```
tou_rate_baht_kwh: float
p2p_rate_baht_kwh: float
wheeling_cost_baht_kwh: float
ft_charge_baht_kwh: float
vat_pct: float
discount_pct: float
```

---

### **10. Simulation Step** (`simulation_step`)

**Tags:** `status`

**Fields:**
```
elapsed_seconds: float
tick_duration_ms: float
active_meters: int
total_generation_kw: float
total_consumption_kw: float
net_balance_kw: float
readings_sent: int
errors_count: int
```

---

### **11. Market Order** (`market_order`)

**Tags:** `order_id`, `meter_id`, `side`, `status`

**Fields:**
```
quantity_kwh: float
price_baht: float
total_value_baht: float
min_price_baht: float
max_price_baht: float
```

---

### **12. Market Clearing** (`market_clearing`)

**Tags:** `market_id`, `status`

**Fields:**
```
clearing_price_baht: float
total_volume_kwh: float
total_value_baht: float
num_bids: int
num_offers: int
num_matched: int
supply_demand_ratio: float
clearing_time_ms: float
```

---

### **13. Demand Response** (`demand_response`)

**Tags:** `event_id`, `type`, `status`

**Fields:**
```
target_reduction_kw: float
actual_reduction_kw: float
participating_meters: int
incentive_baht: float
duration_minutes: float
```

---

### **14. Alert** (`alert`)

**Tags:** `type`, `severity`, `source`

**Fields:**
```
message: string
value: float
threshold: float
```

---

## 🔧 **Implementation**

### **Engine Integration**

The `SimulationEngine.tick()` method now calls `_store_all_to_influxdb()` after each simulation step:

```python
async def tick(self, timestamp: Optional[datetime] = None):
    # ... generate readings, run market, VPP, grid estimation ...
    
    # Send readings to all transports (HTTP, WebSocket, InfluxDB)
    await self._send_readings_async(timestamp, readings)
    
    # Store ALL simulation data to InfluxDB
    await self._store_all_to_influxdb(timestamp, readings)
    
    # Advance time
    self.current_sim_time += timedelta(seconds=self.interval)
```

### **Data Flow**

```
SimulationEngine.tick()
    ↓
Generate Readings (20-1000 meters)
    ↓
Run Market Clearing
    ↓
Run VPP Dispatch
    ↓
Run Grid State Estimation
    ↓
Send to Transports (HTTP, WS, Kafka, InfluxDB)
    ↓
_store_all_to_influxdb() ← NEW
    ↓
Parallel writes to InfluxDB:
  - Grid state estimation
  - VPP cluster status (per cluster)
  - VPP dispatch (per meter)
  - Grid frequency
  - Islanding status
  - Weather conditions
  - Carbon intensity
  - Price updates
  - Simulation step metrics
    ↓
Advance simulation time
```

---

## 📈 **Grafana Dashboard Queries**

### **Real-Time Meter Dashboard**

```flux
from(bucket: "meter_readings")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "meter_reading")
  |> filter(fn: (r) => r._field == "energy_generated_kwh" or r._field == "energy_consumed_kwh")
  |> aggregateWindow(every: 1m, fn: mean)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
```

### **Grid Health Score**

```flux
from(bucket: "meter_readings")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "grid_state_estimation")
  |> filter(fn: (r) => r._field == "health_score")
  |> aggregateWindow(every: 5m, fn: mean)
```

### **VPP Utilization**

```flux
from(bucket: "meter_readings")
  |> range(start: -6h)
  |> filter(fn: (r) => r._measurement == "vpp_cluster")
  |> filter(fn: (r) => r._field == "utilization_pct")
  |> aggregateWindow(every: 5m, fn: mean)
  |> yield(name: "mean")
```

### **Carbon Offset Tracking**

```flux
from(bucket: "meter_readings")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "carbon_intensity")
  |> filter(fn: (r) => r._field == "carbon_offset_kg")
  |> aggregateWindow(every: 1h, fn: sum)
  |> cumulativeSum()
```

### **Price Comparison (ToU vs P2P)**

```flux
from(bucket: "meter_readings")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "price_history")
  |> filter(fn: (r) => r._field == "tou_rate_baht_kwh" or r._field == "p2p_rate_baht_kwh")
  |> aggregateWindow(every: 15m, fn: mean)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
```

---

## 🚀 **Usage**

### **1. Start InfluxDB**

```bash
docker run -d \
  --name gridtokenx-influxdb \
  -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=admin_password \
  -e DOCKER_INFLUXDB_INIT_ORG=gridtokenx \
  -e DOCKER_INFLUXDB_INIT_BUCKET=meter_readings \
  -e DOCKER_INFLUXDB_INIT_RETENTION=52w \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=admin_token \
  -v influxdb_data:/var/lib/influxdb2 \
  influxdb:2.7
```

### **2. Configure Environment**

```bash
# .env
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=admin_token
INFLUXDB_ORG=gridtokenx
INFLUXDB_BUCKET=meter_readings
```

### **3. Start Simulator**

```bash
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

The simulator will automatically connect to InfluxDB and start storing all data.

---

## 📊 **API Endpoints**

All endpoints query the InfluxDB time-series database:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/timeseries/dashboard` | Real-time dashboard data |
| `GET /api/v1/timeseries/meters/{id}/history` | Historical meter readings |
| `GET /api/v1/timeseries/energy-summary` | Generation/consumption summary |
| `GET /api/v1/timeseries/alerts` | Recent alerts |
| `GET /api/v1/timeseries/status` | InfluxDB connection status |

---

## 🔍 **Verify Data Storage**

```bash
# Check InfluxDB is running
curl http://localhost:8086/health

# Query latest meter reading
curl -X POST http://localhost:8086/api/v2/query?org=gridtokenx \
  -H "Authorization: Token admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "from(bucket: \"meter_readings\") |> range(start: -5m) |> filter(fn: (r) => r._measurement == \"meter_reading\") |> last()",
    "type": "flux"
  }'
```

---

## 📁 **Files Modified**

| File | Changes | Description |
|------|---------|-------------|
| `transport/influxdb.py` | **+280 lines** | Added 10 new send methods for all data types |
| `core/engine.py` | **+160 lines** | Added `_store_all_to_influxdb()` integration |
| `docker-compose.yml` | Updated | Fixed retention format (`52w`), added healthcheck |
| `.env.example` | Updated | Corrected InfluxDB credentials |

---

## 📊 **Expected Data Volume**

| Simulation Duration | Meters | Data Points/Day | Storage Size |
|---------------------|--------|-----------------|--------------|
| 1 hour | 20 | ~17,280 | ~5 MB |
| 24 hours | 20 | ~414,720 | ~120 MB |
| 24 hours | 100 | ~2,073,600 | ~600 MB |
| 7 days | 100 | ~14,515,200 | ~4.2 GB |
| 30 days | 100 | ~62,208,000 | ~18 GB |

**Retention:** 52 weeks (1 year)

---

**Status:** ✅ All simulation data now stored in InfluxDB for complete time-series history!
