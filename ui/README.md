# GridTokenX Smart Meter Simulator UI

[![React](https://img.shields.io/badge/react-19-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/typescript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/vite-7.3-purple.svg)](https://vite.dev/)
[![TailwindCSS](https://img.shields.io/badge/tailwind-3.4-38BDF8.svg)](https://tailwindcss.com/)
[![Bun](https://img.shields.io/badge/bun-1.1+-fbf0df.svg)](https://bun.sh/)

> **Modern React dashboard** for the GridTokenX Smart Meter Simulator. Real-time monitoring, grid topology visualization, market analytics, and P2P energy trading interface.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
bun install
```

### 2. Start Development Server

```bash
bun run dev
```

**Access:** http://localhost:5173

### 3. Connect to Simulator API

The UI automatically connects to the simulator API at `http://localhost:8082`.

Configure via `.env`:
```bash
VITE_API_URL=http://localhost:8082
VITE_WS_URL=ws://localhost:8765
```

---

## 🌟 Features

### 📊 Real-Time Dashboard

- **Live meter readings** with 15-second updates
- **Energy generation/consumption** charts
- **Grid health score** and state estimation metrics
- **VPP cluster status** and dispatch commands
- **Carbon offset tracking** with real-time calculations

### 🗺️ Interactive Map Views

| Map | Description |
|-----|-------------|
| **Smart Meter Map** | Geographic meter placement with Leaflet |
| **Electrical Grid Map** | Infrastructure overlay (substations, power lines) |
| **Thai Grid Topology** | MEA/PEA distribution network models |
| **3D Grid Topology** | Three-dimensional grid visualization |

### 💰 Market & Trading

- **P2P order book** with real-time matching
- **Price comparison** (ToU vs P2P dynamic rates)
- **Revenue analysis** and optimization
- **Market clearing results** with settlement history
- **Recurring orders (DCA)** for automated trading

### 🔍 Monitoring & Analytics

- **Grid quality analysis** with 4 custom analyzers
- **Power validation** with Thai infrastructure data
- **Solar detection** and generation forecasting
- **Demand response events** tracking
- **Frequency regulation** monitoring

---

## 🏗️ Architecture

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | React 19 + TypeScript |
| **Build Tool** | Vite 7.3 |
| **Styling** | TailwindCSS 3.4 + shadcn/ui |
| **State** | React Query + Context |
| **Routing** | React Router 7 |
| **Maps** | Leaflet + React-Leaflet |
| **Charts** | Recharts |
| **HTTP Client** | Axios |
| **WebSocket** | Native WebSocket API |

### Project Structure

```
ui/
├── src/
│   ├── components/         # Shared UI components
│   │   └── ui/            # shadcn/ui primitives
│   ├── features/          # Feature modules
│   │   ├── dashboard/     # Real-time dashboard
│   │   ├── meter/         # Meter management
│   │   ├── monitoring/    # Grid quality, analytics
│   │   ├── market/        # P2P trading interface
│   │   ├── vpp/           # VPP dispatch & clusters
│   │   ├── smart-meter-map/ # Map components
│   │   └── electrical-grid-map/ # Grid infrastructure
│   ├── pages/             # Route components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API clients
│   └── App.tsx            # Root component
├── public/                # Static assets
├── index.html             # Entry HTML
└── vite.config.ts         # Vite configuration
```

---

## 📱 Pages

| Page | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/` | Main overview with live metrics |
| **Meters** | `/meters` | List and manage smart meters |
| **Meter Details** | `/meters/:id` | Individual meter analytics |
| **Smart Meter Map** | `/map` | Geographic meter visualization |
| **Electrical Grid Map** | `/grid-map` | Infrastructure topology |
| **Grid Topology 3D** | `/grid-3d` | Three-dimensional grid view |
| **Market** | `/market` | P2P trading interface |
| **VPP** | `/vpp` | Virtual Power Plant control |
| **Monitoring** | `/monitoring` | Grid quality & validation |
| **Resilience** | `/resilience` | Grid stability metrics |
| **LPC Dashboard** | `/lpc` | Load profile analysis |

---

## 🔌 API Integration

### REST Endpoints Used

The UI consumes the simulator's `/api/v1/` endpoints:

| Feature | Endpoints |
|---------|-----------|
| **Dashboard** | `GET /api/v1/simulation/status`<br>`GET /api/v1/timeseries/dashboard` |
| **Meters** | `GET /api/v1/meters`<br>`GET /api/v1/meters/{id}` |
| **Grid** | `GET /api/v1/grid/status`<br>`GET /api/v1/grid/topology` |
| **Market** | `GET /api/v1/market/orders`<br>`GET /api/v1/market/clearing` |
| **VPP** | `GET /api/v1/vpp/status`<br>`GET /api/v1/vpp/dispatch` |
| **Time-Series** | `GET /api/v1/timeseries/meters/{id}/history`<br>`GET /api/v1/timeseries/energy-summary` |

### WebSocket Integration

Real-time updates via WebSocket:
```typescript
const ws = new WebSocket('ws://localhost:8765/ws');
ws.onmessage = (event) => {
  const reading = JSON.parse(event.data);
  // Update dashboard with live meter reading
};
```

---

## 🎨 Customization

### Theme

The UI uses TailwindCSS with a custom color palette configured in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: { /* ... */ },
      grid: { /* Grid-specific colors */ },
      energy: {
        generation: '#22c55e',
        consumption: '#ef4444',
        battery: '#3b82f6',
      }
    }
  }
}
```

### Adding New Components

1. Create component in `src/features/<feature>/components/`
2. Export from feature's `index.ts`
3. Use in pages or other components

Example:
```tsx
// src/features/dashboard/components/MetricCard.tsx
export function MetricCard({ title, value, unit }: Props) {
  return (
    <Card>
      <CardHeader>{title}</CardHeader>
      <CardContent>
        <span className="text-3xl font-bold">{value}</span>
        <span className="text-muted-foreground">{unit}</span>
      </CardContent>
    </Card>
  );
}
```

---

## 🧪 Testing

```bash
# Run tests (if configured)
bun test

# Build for production
bun run build

# Preview production build
bun run preview

# Lint check
bun run lint
```

---

## 🚢 Deployment

### Production Build

```bash
bun run build
```

Output: `dist/` directory

### Docker

```bash
docker build -t gridtokenx-simulator-ui .
docker run -p 80:80 gridtokenx-simulator-ui
```

### Nginx Configuration

The included `nginx.conf` provides:
- Static file serving from `dist/`
- API proxy to simulator (`/api` → `http://simulator:8082`)
- WebSocket proxy (`/ws` → `ws://simulator:8765`)

---

## 🔗 Related Projects

| Project | Description |
|---------|-------------|
| [Smart Meter Simulator](../) | Backend simulation engine |
| [GridTokenX API](../../gridtokenx-api/) | Primary API gateway |
| [GridTokenX Trading](../../gridtokenx-trading/) | P2P trading platform |
| [GridTokenX Portal](../../gridtokenx-portal/) | Admin dashboard |

---

## 📄 License

Part of the GridTokenX Ecosystem - Proprietary

---

_Maintained by the GridTokenX Engineering Team._
