---
title: "Docker Stack"
category: integration
created: 2026-04-10
updated: 2026-04-10
sources: ["docker-compose.yml", "Dockerfile", "docs/guides/docker-deployment.md"]
tags: [infrastructure, docker, compose, deployment]
related: [[InfluxDB Integration]], [[PostGIS Integration]], [[OpenTelemetry]]
---

# Docker Stack

The full simulation stack is orchestrated via Docker Compose, providing 7+ containers for databases, caching, messaging, the simulator API, and the React UI.

## Summary

A single `docker compose up -d` starts the complete infrastructure: PostgreSQL (relational), PostGIS (spatial), Redis (cache), Mosquitto (MQTT), InfluxDB (time-series), the FastAPI simulator, and the Bun-based React dashboard.

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **postgres** | postgis/postgis:15-3.3 | 5432 | Relational database |
| **gis-postgres** | postgis/postgis:17-3.4 | 5433 | Spatial database |
| **pgadmin** | dpage/pgadmin4:latest | 5050 | Database management UI |
| **redis** | redis:7-alpine | 7010 | Caching & Pub/Sub |
| **mosquitto** | eclipse-mosquitto:2.0 | 1883, 9001 | MQTT broker |
| **influxdb** | influxdb:2.7 | 7020 | Time-series database |
| **simulator** | Custom (Dockerfile) | 8082 | FastAPI + Rust |
| **ui** | oven/bun:1 | 5173 | React dev server |

## Network

All containers share the `gridtokenx-network` bridge network:

```yaml
networks:
  gridtokenx-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

Inter-container DNS resolution by service name:
- `postgres` → 172.28.x.x
- `redis` → 172.28.x.x
- `influxdb` → 172.28.x.x

## Volumes

| Volume | Service | Purpose |
|--------|---------|---------|
| `postgres_data` | postgres | Database files |
| `gis_postgres_data` | gis-postgres | Spatial database files |
| `pgadmin_data` | pgadmin | Server configurations |
| `redis_data` | redis | Append-only file |
| `influxdb_data` | influxdb | Time-series data |

## Health Checks

| Service | Check | Interval | Retries |
|---------|-------|----------|---------|
| postgres | `pg_isready -U gridtokenx` | 10s | 5 |
| gis-postgres | `pg_isready -U gridtokenx` | 10s | 5 |
| redis | `redis-cli ping` | 10s | 5 |
| influxdb | `influx ping` | 10s | 5 |
| simulator | `curl /health` | 30s | 3 |

## Build Pipeline

```
┌────────────────────┐     ┌────────────────────┐
│  ui/ (Bun/Vite)    │     │  src/ (Python)     │
│  bun x vite build  │     │  uv sync --frozen  │
└────────┬───────────┘     └────────┬───────────┘
         │                         │
         ↓                         ↓
┌─────────────────────────────────────────────────┐
│              Docker Image                       │
│  Stage 1: UI builder (oven/bun:1)               │
│  Stage 2: Python backend (python:3.11-slim)     │
│    + Rust module (maturin)                      │
│    + Built UI dist/                             │
└─────────────────────────────────────────────────┘
```

## Resource Limits

```yaml
simulator:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2gb
```

## Usage

```bash
# Start all services
docker compose up -d

# View simulator logs
docker compose logs -f simulator

# View specific service
docker compose logs -f postgres

# Restart simulator only
docker compose restart simulator

# Stop all services (preserve data)
docker compose down

# Stop and remove volumes (destroy data)
docker compose down -v

# Rebuild simulator image
docker compose up -d --build simulator
```

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Simulator API | http://localhost:8082 | — |
| API Docs | http://localhost:8082/docs | — |
| pgAdmin | http://localhost:5050 | admin@gridtokenx.local / admin_password |
| InfluxDB UI | http://localhost:7020 | admin / admin_password |
| React UI | http://localhost:5173 | — |

## Relationships

- **Orchestration:** docker-compose.yml
- **Build:** Dockerfile (multi-stage)
- **Databases:** [[PostGIS Integration]], [[InfluxDB Integration]]
- **Runtime:** OrbStack (recommended for macOS)

## Known Issues

- Kafka not included in compose (external dependency)
- No Grafana container (separate deployment)
- UI dev server (Bun) runs in container — slow on macOS without OrbStack
- PostgreSQL 15 vs 17 version mismatch between main and GIS databases
- Simulator image is large (~2GB) due to Python dependencies
