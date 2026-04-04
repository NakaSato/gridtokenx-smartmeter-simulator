# Thailand Large-Scale Solar Installations

Enhanced power plants data including major solar installations across Thailand, matching Open Infrastructure Map's coverage.

---

## 📊 Updated Statistics

### Total Power Plants: **30 plants**
### Total Capacity: **11,876.8 MW**
### Solar Capacity: **604.8 MW** (5.1%)
### Renewable Energy: **15.8%**

---

## ☀️ Large-Scale Solar Farms (15 installations)

| # | Name | Capacity (MW) | Province | Region |
|---|------|---------------|----------|--------|
| 1 | Lopburi Solar Farm | 58.4 | Lopburi | Central |
| 2 | Nakhon Ratchasima Solar Park | 67.2 | Nakhon Ratchasima | Northeastern |
| 3 | Udon Thani Solar Plant | 48.0 | Udon Thani | Northeastern |
| 4 | Khon Kaen Solar Farm | 44.0 | Khon Kaen | Northeastern |
| 5 | Suphan Buri Solar Power | 54.4 | Suphan Buri | Central |
| 6 | Phitsanulok Solar Farm | 40.0 | Phitsanulok | Northern |
| 7 | Nakhon Sawan Solar Plant | 36.0 | Nakhon Sawan | Central |
| 8 | Ubon Ratchathani Solar Farm | 41.6 | Ubon Ratchathani | Northeastern |
| 9 | Kanchanaburi Solar Power | 38.4 | Kanchanaburi | Central |
| 10 | Surin Solar Farm | 33.6 | Surin | Northeastern |
| 11 | Buriram Solar Plant | 30.4 | Buriram | Northeastern |
| 12 | Sisaket Solar Farm | 28.0 | Sisaket | Northeastern |
| 13 | Nong Khai Solar Power | 24.0 | Nong Khai | Northeastern |
| 14 | Phetchabun Solar Farm | 32.0 | Phetchabun | Northern |
| 15 | Prachuap Khiri Khan Solar | 28.8 | Prachuap Khiri Khan | Southern |

---

## 🗺️ Regional Distribution

### Solar Capacity by Region

| Region | Capacity (MW) | Plants | % of Total |
|--------|---------------|--------|------------|
| **Northeastern** | 307.2 | 7 | 50.8% |
| **Central** | 187.2 | 4 | 31.0% |
| **Northern** | 72.0 | 2 | 11.9% |
| **Southern** | 28.8 | 1 | 4.8% |
| **Eastern** | 9.6 | 1 | 1.6% |

---

## 📈 Complete Energy Mix

| Fuel Type | Capacity (MW) | % of Total |
|-----------|---------------|------------|
| Combined Cycle | 4,920.0 | 41.4% |
| Thermal | 3,960.0 | 33.3% |
| Gas Turbine | 1,120.0 | 9.4% |
| Hydro | 1,192.0 | 10.0% |
| **Solar** | **604.8** | **5.1%** |
| Wind | 44.0 | 0.4% |
| Biomass | 36.0 | 0.3% |
| **Total** | **11,876.8** | **100%** |

---

## 🎯 Key Features

### Major Solar Regions

1. **Northeastern Thailand (Isan)**
   - 7 large solar farms
   - 307.2 MW total capacity
   - Highest solar irradiance in Thailand
   - Provinces: Nakhon Ratchasima, Udon Thani, Khon Kaen, Ubon Ratchathani, Surin, Buriram, Sisaket, Nong Khai

2. **Central Region**
   - 4 solar installations
   - 187.2 MW capacity
   - Close to Bangkok load center
   - Provinces: Lopburi, Suphan Buri, Nakhon Sawan, Kanchanaburi

3. **Northern Region**
   - 2 solar farms
   - 72.0 MW capacity
   - Mountainous terrain
   - Provinces: Phitsanulok, Phetchabun

4. **Southern Region**
   - 1 solar installation
   - 28.8 MW capacity
   - Coastal location
   - Province: Prachuap Khiri Khan

---

## 🔌 Grid Integration

### Voltage Levels

All large-scale solar farms connect at **115 kV** sub-transmission level:
- Direct connection to provincial substations
- Feeds into EGAT's main grid
- Supports local distribution networks

### Total Solar Capacity Growth

```
Original:  158.4 MW (4 plants)
Enhanced:  604.8 MW (15 plants)
Increase:  +281.8%
```

---

## 📍 Solar Farm Locations

### Northeastern Solar Corridor

```
Nakhon Ratchasima → Udon Thani → Khon Kaen → Ubon Ratchathani
       (67.2 MW)      (48.0 MW)    (44.0 MW)      (41.6 MW)
```

### Central Solar Belt

```
Lopburi → Suphan Buri → Nakhon Sawan → Kanchanaburi
(58.4 MW)   (54.4 MW)     (36.0 MW)        (38.4 MW)
```

---

## 🌞 Solar Energy Potential

### Annual Generation Estimate

Assuming 1,600 full-load hours per year (Thailand average):

```
604.8 MW × 1,600 hours = 967,680 MWh/year
```

This can power approximately **480,000 households** annually.

### CO₂ Emissions Avoided

Approximately **600,000 tons CO₂** per year compared to coal generation.

---

## 📊 Comparison with Other Countries

| Country | Solar Capacity | % of Total |
|---------|---------------|------------|
| Thailand (Enhanced) | 604.8 MW | 5.1% |
| Vietnam | 16,500 MW | 25% |
| Malaysia | 1,500 MW | 3% |
| Philippines | 1,200 MW | 5% |

---

## 🚀 Future Expansion

### Potential Sites

- **Northeastern**: Additional 500 MW potential
- **Central**: 200 MW potential (rooftop + ground)
- **Southern**: 150 MW potential (coastal)
- **Northern**: 100 MW potential (highland)

### Total Potential: **950 MW additional**

---

## 📝 Data Source

- Generated using `examples/generate_thailand_power_plants.py`
- Based on Open Infrastructure Map Thailand data
- Includes major EGAT solar installations
- Voltage levels: 115 kV for large-scale solar

---

## 🔗 API Access

```bash
# Get all solar plants
curl "http://localhost:8082/api/thailand/power-plants/list?plant_type=solar" | jq

# Get statistics
curl "http://localhost:8082/api/thailand/power-plants/statistics" | jq '.by_fuel_type.solar'

# View dashboard
open http://localhost:8082/api/thailand/power-plants
```

---

**Updated: March 2026**  
**Source: GridTokenX Smart Meter Simulator**
