---
name: frontend-dashboard-dev
description: Develop the Next.js 16 / React 19 simulator dashboard — pages (dashboard, map, topology, meter detail), components (Leaflet/Mapbox maps, Three.js 3D topology, Recharts), the backend API client, WebSocket/polling telemetry, and the React Context providers. Use when adding or changing UI, wiring a new backend endpoint into the frontend, touching the map/3D views, or debugging API-target / proxy issues. Read this BEFORE writing frontend code.
---

# Developing the simulator dashboard (frontend/)

Next.js **16.2** App Router + React **19.2**, Tailwind CSS **v4**, TypeScript 5, ESLint 9.
Path alias `@/*` → `./src/*`. All paths below are under `frontend/`.

## Read this first: Next.js 16 is not the Next.js you know

`frontend/AGENTS.md` is law here: **this Next.js version has breaking changes vs. training
data.** Before writing App-Router code (layouts, route handlers, `dynamic`, metadata, server
vs. client components, caching), read the matching guide under
`node_modules/next/dist/docs/01-app/`. Don't trust remembered Next 13/14 conventions. Heed
deprecation notices the compiler prints.

## Page structure (`src/app/`)

- `layout.tsx` — root: dark theme, wraps everything in `AppProvider`, sets
  `export const dynamic = "force-dynamic"` (no static generation — the whole app is live data).
- `dashboard/page.tsx` — main control panel: grid stats, meter cards/list, controls.
- `map/page.tsx` — thin wrapper that **dynamically imports** `map-content.tsx` (maps are
  client-only / SSR-unsafe — keep them behind `next/dynamic` with `ssr: false` or `ClientOnly`).
- `topology/page.tsx` — 3D grid view (`react-force-graph-3d` + three.js).
- `meter/[meterId]/page.tsx` — per-meter detail (telemetry, charts, billing).
- `api/meters/route.ts` — a Node route handler that proxies to the backend server-side.

## Backend integration (the important part)

The frontend talks to the backend in three layers — **use the existing ones, don't hand-roll
`fetch` to a hardcoded URL**:

1. **Rewrite proxy** — `next.config.ts` rewrites `/api/v1/:path*` and `/ws` to
   `process.env.SIMULATOR_URL`. ⚠️ **The default in code is `http://localhost:12010`, but the
   backend dev server runs on `:8082`** (see backend README / `cli.py`). For local dev set
   `SIMULATOR_URL=http://localhost:8082` in `frontend/.env`, or you'll get connection errors.
2. **`NetworkProvider`** (`src/components/providers/NetworkProvider.tsx`) — `useNetwork()`
   exposes `getApiUrl(path)` / `getWsUrl(path)` with runtime target selection (localStorage
   key `gridtokenx_api_target`; presets include :12010, :8082, mesh :4030, APISIX). **Build
   request URLs via `getApiUrl()`**, not string literals.
3. **`useApi(getApiUrl, addLog)`** (`src/hooks/useApi.ts`) — thin `fetch` wrapper that parses
   JSON and surfaces backend `detail` + `suggestion` error fields. No SWR / react-query.

**Live telemetry** arrives two ways:
- **WebSocket** via `useWebSocket()` (subscribes to a `market_events` channel; receives
  `meter_readings` / `grid_status`). Auto-reconnects.
- **Polling** via plain `useEffect` + `setInterval` (topology/map ≈ 2 s, meter detail ≈ 30 s).
  There is no polling library — follow the existing interval+cleanup pattern.

The backend API surface these hit is `/api/v1/...` (simulation control, meters, grid,
telemetry) — see backend `routers/`. Reading/grid payload shapes are mirrored in
`src/lib/types.ts` (`Reading`, `GridHealth`, `SimulatorStatus`, `WsMessage`, etc.). **When a
backend field changes, update `src/lib/types.ts` to match** — they are hand-kept in sync, not
generated.

## State, components, styling

- **State**: React Context only (no Redux/zustand). `SimulatorProvider` holds shared sim state
  (readings, status, controls, meter CRUD, env updates); `NetworkProvider` holds API target.
  Consume via `useSimulator()` / `useNetwork()` — no prop drilling.
- **Components** (`src/components/`): `dashboard/` (controls), `maps/` (Leaflet **and** Mapbox
  GL views + overlays — note two map stacks coexist), `meters/` (cards, modals, Recharts),
  `ui/` (nav, stat cards, `ClientOnly`), `providers/`, `console/`. Map/3D libs are
  SSR-incompatible — always render them client-side only.
- **Styling**: Tailwind v4 via `@import "tailwindcss"` in `src/app/globals.css`; custom energy
  theme vars (`--color-energy-green/blue/purple`); dark mode default. Compose classes with
  `cn()` from `src/lib/common.ts` (clsx + tailwind-merge). No CSS modules.

## Build / run / lint

```bash
cd frontend
bun install
bun run dev      # next dev (localhost:3000) — set SIMULATOR_URL first (see above)
bun run build    # next build
bun run lint     # eslint (flat config: next/core-web-vitals + next/typescript)
```

`NEXT_PUBLIC_MAPBOX_TOKEN` is required for the Mapbox views. The Docker image builds the
frontend with **bun** (`bun x next build`) — keep `bun.lock` in sync if you change deps.
