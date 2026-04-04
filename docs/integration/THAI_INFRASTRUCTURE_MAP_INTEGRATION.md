# Thai Infrastructure Map - Integration Guide

## Overview

The Thai Infrastructure Map has been integrated into the GridTokenX platform as a React component with backend API support.

## Files Created

### Frontend (React/TypeScript)

**`ui/src/pages/ThaiInfrastructureMap.tsx`**
- Full-screen interactive map viewer
- Leaflet.js integration
- Voltage-based layer controls
- Real-time statistics
- Drag-and-drop GeoJSON upload
- Base map selector (OSM, Satellite, Dark Matter)

### Backend (Python/FastAPI)

**`src/smart_meter_simulator/routers/grid.py`** (modified)
- Added `/api/grid/geojson` endpoint - Returns current network as GeoJSON
- Added `/api/grid/geojson/export` endpoint - Downloads GeoJSON file

**`src/smart_meter_simulator/adapters/geojson_exporter.py`** (existing)
- NetworkGeoJSONExporter class for pandapower → GeoJSON conversion

## Routes

### Frontend Route

```
/thai-grid-map
```

Access via: `http://localhost:5173/thai-grid-map` (development)

### API Endpoints

```
GET /api/grid/geojson
```
Returns current grid network as GeoJSON FeatureCollection.

```
GET /api/grid/geojson/export
```
Downloads GeoJSON file for offline use.

## Usage

### 1. Start the Simulator

```bash
# Backend
cd /Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-smartmeter-simulator
uv run start-simulator --mode server --port 8082

# Frontend (in separate terminal)
cd ui
bun run dev
```

### 2. Access the Map

Open browser to: `http://localhost:5173/thai-grid-map`

### 3. Load Network Data

The map will automatically load the current network from the API.

Or drag-and-drop any GeoJSON file onto the map.

## Features

### Voltage Level Visualization

| Voltage | Color | Usage |
|---------|-------|-------|
| 500 kV | 🔴 Red | Transmission (EGAT) |
| 230 kV | 🟠 Orange | Transmission (EGAT) |
| 115 kV | 🟡 Yellow | Sub-transmission |
| 22 kV | 🟠 Orange | Distribution (MEA/PEA) |
| 0.4 kV | 🟡 Yellow | LV Distribution |
| Substation | 🟣 Purple | MV/LV substations |
| Transformer | 🔵 Blue | Distribution transformers |

### Interactive Controls

- **Sidebar:** Collapsible left panel with statistics and layers
- **Layer Toggles:** Switch voltage levels on/off
- **Base Maps:** Choose between OSM, Satellite, Dark Matter
- **Popups:** Click elements for details
- **Zoom/Pan:** Standard map navigation
- **Export:** Download current view as GeoJSON
- **Import:** Upload GeoJSON files

## Customization

### Add to Navigation Menu

If your app has a navigation menu, add:

```tsx
// Example: Add to your sidebar/nav component
<Link to="/thai-grid-map">
  <MapIcon />
  <span>Thai Grid Map</span>
</Link>
```

### Modify Default Location

Edit `ui/src/pages/ThaiInfrastructureMap.tsx`, line ~120:

```typescript
mapRef.current = L.map(mapContainerRef.current, {
  center: [13.7563, 100.5018],  // Change to your location
  zoom: 12,                      // Change zoom level
  zoomControl: false,
});
```

### Add More Voltage Levels

Edit the `VOLTAGE_LEVELS` constant:

```typescript
const VOLTAGE_LEVELS = {
  500: { color: '#e6194B', weight: 5, label: '500 kV', icon: Zap },
  230: { color: '#f58231', weight: 4, label: '230 kV', icon: Zap },
  // Add more levels here
};
```

## API Integration

### Example: Fetch GeoJSON

```typescript
const response = await fetch('/api/grid/geojson');
const geojson = await response.json();
console.log(geojson.features); // Array of network elements
```

### Example: Generate Network in Backend

```python
from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder
from smart_meter_simulator.adapters.geojson_exporter import NetworkGeoJSONExporter

# Create network
builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
net = builder.build_urban_network(num_households=100)

# Export to GeoJSON
exporter = NetworkGeoJSONExporter()
geojson = exporter.to_geojson(net)
```

## Troubleshooting

### Map Not Loading

1. Check browser console for errors
2. Verify backend is running at `http://localhost:8082`
3. Ensure frontend can reach API (CORS configured)

### No Features Displayed

1. Check if simulator has loaded a network
2. Verify `/api/grid/geojson` returns data
3. Toggle layers on/off in sidebar

### Coordinates Wrong

- GeoJSON uses `[longitude, latitude]` order
- Ensure coordinates are in decimal degrees
- Check pandapower network has valid geo data

## Dependencies

### Frontend

```json
{
  "leaflet": "^1.9.4",
  "lucide-react": "^0.x",
  "react": "^18.x",
  "@/components/ui/*": "shadcn/ui components"
}
```

### Backend

```python
pandapower>=2.14.0
fastapi>=0.100.0
```

## Related Files

| File | Purpose |
|------|---------|
| `ui/src/pages/ThaiInfrastructureMap.tsx` | React map component |
| `src/smart_meter_simulator/routers/grid.py` | API endpoints |
| `src/smart_meter_simulator/adapters/geojson_exporter.py` | GeoJSON export |
| `src/smart_meter_simulator/adapters/thai_grid_topology.py` | Thai network models |
| `examples/export_thai_grid_geojson.py` | Export script |

## Next Steps

1. **Add to Navigation:** Integrate link into your app's main menu
2. **Customize Styling:** Match colors/theme to your brand
3. **Add Features:** Solar farms, wind plants, generation data
4. **Real-time Updates:** WebSocket integration for live data
5. **Analytics:** Add network analysis tools

---

**Part of the GridTokenX Platform**

For more information, see:
- `docs/THAI_INFRASTRUCTURE_MAP_QUICKSTART.md`
- `docs/GRID_MAP_VIEWER.md`
- `docs/THAI_GRID_TOPOLOGY.md`
