# Frontend Implementation & Architecture

This document provides a technical overview of the GridTokenX Smart Meter Simulator frontend, built with **Next.js 16** and **Tailwind CSS 4**.

## 1. Tech Stack
- **Framework**: Next.js 16.2 (App Router)
- **Runtime**: React 19 (Concurrent Mode)
- **Styling**: Tailwind CSS 4.0 (using `@import "tailwindcss"`)
- **Mapping**: 
    - **Leaflet**: High-performance 2D marker clustering and custom icons.
    - **Mapbox GL**: Globe projection, 3D terrain, and vector tile infrastructure layers.
- **Visualization**:
    - **Recharts**: Time-series forecasting and financial optimization charts.
    - **React Force Graph 3D**: WebGL-based grid topology exploration.
- **State & Integration**:
    - **WebSockets**: Real-time telemetry streaming and grid event alerts.
    - **Next.js Rewrites**: API proxying to avoid CORS issues and simplify environment switching.

---

## 2. Directory Structure

```text
frontend/
├── src/
│   ├── app/                 # App Router Pages & API Routes
│   │   ├── dashboard/       # Main Control Hub
│   │   ├── map/             # Unified Grid Visualizer
│   │   ├── adr/             # Automated Demand Response
│   │   ├── vpp/             # Virtual Power Plant Ops
│   │   ├── topology/        # 3D Grid Graph
│   │   └── api/             # Backend Proxy Routes
│   ├── components/          # Modular React Components
│   │   ├── dashboard/       # Specialized Dashboard widgets
│   │   ├── maps/            # Multi-layer Map implementations
│   │   ├── meters/          # Smart Meter UI (Cards, Popups)
│   │   ├── providers/       # Network & Context Providers
│   │   └── ui/              # Atomized UI components (Buttons, Stats)
│   ├── hooks/               # Custom React Hooks (WS, API, Auth)
│   └── lib/                 # Shared Utilities & Types
```

---

## 3. Core Modules

### Dashboard (`/dashboard`)
The central cockpit for simulation management.
- **Simulator Control**: Start/Stop/Pause actions via `GridControls`.
- **Environment Control**: Real-time adjustment of weather (Sunny/Stormy) and grid stress multipliers.
- **AI Forecasting Widget**: Visualizes the "Yellow/Blue Line" constraint logic (Demand vs. Capacity).
- **Console**: Live streaming of system logs and security alerts.

### Mapping System (`/map`)
A unified map interface supporting five distinct layers:
1. **Smart Meters**: Live telemetry for prosumers/consumers (Leaflet).
2. **Micro Grid**: Local circuit topology with PCC (Point of Common Coupling) status.
3. **Infrastructure**: EGAT/MEA/PEA substation and tower database.
4. **EGAT Grid**: High-voltage transmission network visualization.
5. **OSM Grid**: Real-world power grid data extracted from OpenStreetMap.

### 3.D Topology (`/topology`)
Visualizes the electrical network as a force-directed graph.
- Uses **Three.js** under the hood.
- Maps buses as nodes and lines as links.
- Nodes pulsate and change color based on live power flow (Generation vs. Consumption).

---

## 4. Data Flow & Networking

### Multi-Target API Proxy
The `NetworkProvider` allows switching between environments without rebuilding:
- **Local**: `http://localhost:8082` (Default)
- **APISIX Gateway**: `http://localhost:4001`
- **Production**: Custom Mesh endpoint.

### WebSocket Integration (`useWebSocket.ts`)
The application maintains a persistent connection for:
- `READING_RECEIVED`: Instant meter state updates.
- `GRID_STATUS`: Real-time health scores, frequency (Hz), and anomaly detection.
- `METER_ALERT`: Push notifications for grid violations or cyber attacks.

### API Proxy Routes (`/api/meters/route.ts`)
Next.js API routes act as a bridge to the simulator backend, handling ETag-based caching for OSM data and simplifying credential management.

---

## 5. UI/UX Design System
- **Theme**: Ultra-dark "Cyber-Grid" aesthetic.
- **Visual Language**: 
    - **Glassmorphism**: Extensive use of backdrop-blur and semi-transparent borders.
    - **Color Coding**: 
        - `Emerald`: Generation / Green Energy
        - `Blue`: Consumption / Stable Grid
        - `Amber`: Prosumer / Potential Risk
        - `Rose`: Critical Alert / Deficiency
    - **Interactions**: Framer Motion-inspired animations for state changes and data transitions.

---

## 6. Implementation Notes for Agents
- **Breaking Changes**: This version of Next.js/React has strict typing for Server Components. Refer to `frontend/AGENTS.md`.
- **Map Persistence**: Map coordinates and zoom levels are persisted in `localStorage` via the `usePersistedViewState` hook.
- **Environment**: Backend URL is configured in `.env` or via the in-app Network Settings (top-right gear icon).
