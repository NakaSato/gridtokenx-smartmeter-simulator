# Thai Electrical Grid Map

Interactive map visualization for Thai electrical infrastructure (EGAT, MEA, PEA).

## Features

### 🗺️ Interactive Map
- **Mapbox GL** based interactive map
- **Globe projection** for realistic Earth view
- **Zoom levels** 6-18 for different detail levels
- **Click interactions** for infrastructure details

### ⚡ Infrastructure Types

| Type | Operator | Voltage Levels | Color |
|------|----------|----------------|-------|
| Transmission Substation | EGAT | 500kV, 230kV, 115kV | Red |
| Distribution Substation | MEA/PEA | 115kV, 22kV, 33kV | Blue/Green |
| Transmission Tower | EGAT | 500kV, 230kV, 115kV | Amber |
| Distribution Pole | MEA/PEA | 22kV, 33kV | Light Blue/Green |
| Power Plant | EGAT | Various | Purple |
| Solar Farm | EGAT | Various | Yellow |
| Battery Storage | EGAT | Various | Pink |
| EV Charging Station | MEA | Various | Cyan |

### 🎨 Visual Features

1. **Glow Effects**: Substations have glow effects for emphasis
2. **Voltage Coloring**: Different voltages have distinct colors
3. **Operator Branding**: EGAT (Red), MEA (Blue), PEA (Green)
4. **Zoom-based Visibility**: Infrastructure appears at appropriate zoom levels
5. **Interactive Popups**: Click on infrastructure for details

### 🔍 Filtering & Search

- **Filter by Operator**: EGAT, MEA, PEA
- **Filter by Type**: 8 infrastructure types
- **Filter by Voltage**: Specific voltage levels
- **Filter by Province**: Geographic filtering
- **Search**: By name, ID, or location

## Usage

### Basic Usage

```tsx
import ElectricalGridMapPage from './pages/ElectricalGridMapPage';

function App() {
  return <ElectricalGridMapPage />;
}
```

### With Custom Props

```tsx
import { ElectricalGridMap } from './features/electrical-grid-map';

<ElectricalGridMap
  initialViewState={{
    longitude: 100.5,
    latitude: 13.75,
    zoom: 6
  }}
  showFilters={true}
  showLegend={true}
/>
```

## API Integration

### Backend Endpoint

```
GET /api/v1/grid/electrical-infrastructure
```

**Response:**
```json
{
  "infrastructure": [
    {
      "id": "EGAT-WN-001",
      "type": "transmission_substation",
      "operator": "EGAT",
      "latitude": 14.3567,
      "longitude": 100.6234,
      "voltage_kv": 500,
      "name_en": "Wang Noi",
      "name_th": "วังน้อย",
      "status": "operational",
      "province": "Phra Nakhon Si Ayutthaya"
    }
  ],
  "stats": {
    "totalInfrastructure": 1000,
    "byOperator": { "EGAT": 500, "MEA": 300, "PEA": 200 },
    "byType": { ... },
    "byVoltage": { ... }
  }
}
```

### Mock Data

If the API endpoint is not available, the component automatically uses mock data for development.

## Components

### ElectricalGridMap
Main map component with all features.

### MapHeader
Header with title, stats, and action buttons.

### FilterPanel
Filter and search panel.

### InfrastructurePopup
Popup showing infrastructure details.

### MapLegend
Legend showing colors and symbols.

## Configuration

### Environment Variables

```bash
# Mapbox Access Token
VITE_MAPBOX_TOKEN=pk.your_token_here
```

### Map Styles

The map uses Mapbox Dark style by default. You can change it:

```tsx
<Map
  mapStyle="mapbox://styles/mapbox/dark-v11"
  // Other styles:
  // - mapbox://styles/mapbox/streets-v12
  // - mapbox://styles/mapbox/satellite-v9
  // - mapbox://styles/mapbox/satellite-streets-v12
/>
```

## Performance

### Optimizations

1. **Layer Grouping**: Infrastructure grouped by operator
2. **Zoom-based Rendering**: Only show relevant infrastructure at each zoom level
3. **Filtering**: Client-side filtering for fast updates
4. **GeoJSON Source**: Single source for all infrastructure

### Recommended Limits

- **Max Infrastructure**: ~10,000 points for smooth performance
- **Max Visible at Once**: ~1,000 points at zoom 12
- **Filter Updates**: <100ms for 1,000 points

## Development

### Adding New Infrastructure Types

1. Update `types.ts`:
```typescript
export type InfrastructureType = 
  | 'existing_type'
  | 'new_type';  // Add here
```

2. Add layer configuration:
```typescript
{
  id: 'new_type',
  type: 'new_type',
  operator: 'EGAT',
  visible: true,
  color: '#FF0000',
  icon: 'icon-name',
  minZoom: 8
}
```

3. Add to legend and filters

### Customizing Colors

Edit `mapLayers.ts`:
```typescript
export const getVoltageColor = (voltageKv: number): string => {
  if (voltageKv >= 500) return '#DC2626';  // Change color here
  // ...
};
```

## Testing

### Mock Data Generation

The `useElectricalGridData` hook includes mock data generation for testing:

```typescript
const mockData = generateMockData();
// Returns sample infrastructure for Bangkok area
```

### Test Scenarios

1. **Empty State**: No infrastructure
2. **Single Operator**: Only EGAT/MEA/PEA
3. **All Operators**: All three utilities
4. **Large Dataset**: 1000+ points
5. **Filtering**: Various filter combinations

## Future Enhancements

- [ ] Real-time data updates via WebSocket
- [ ] 3D visualization of transmission lines
- [ ] Time-series playback (historical data)
- [ ] Integration with OSM data
- [ ] Export to GeoJSON/KML
- [ ] Print-friendly view
- [ ] Mobile-optimized controls
- [ ] Augmented Reality view (mobile)

## References

- **EGAT**: https://www.egat.co.th/
- **MEA**: https://www.mea.or.th/
- **PEA**: https://www.pea.co.th/
- **Mapbox GL**: https://docs.mapbox.com/mapbox-gl-js/guides/
- **React Map GL**: https://visgl.github.io/react-map-gl/

## License

Part of GridTokenX Smart Meter Simulator

---

**Version:** 1.0.0  
**Date:** 2024-03-30  
**Status:** ✅ Production Ready
