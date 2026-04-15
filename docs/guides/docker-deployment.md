# Docker Deployment

The **GridTokenX Smart Meter Simulator** is designed to be fully containerized, making it easy to deploy alongside other GridTokenX infrastructure services.

## 🐳 Docker Stack Overview

The `docker-compose.yml` file defines a comprehensive simulation stack:

1.  **`postgres`**: Main relational database for session metadata.
2.  **`gis-postgres`**: Specialized PostGIS database for spatial grid topology (MEA/PEA models).
3.  **`influxdb`**: Time-series database for high-frequency telemetry.
4.  **`redis`**: Real-time state cache.
5.  **`mosquitto`**: MQTT broker for industrial AMI protocol testing.
6.  **`simulator`**: The FastAPI-based simulator application.
7.  **`pgadmin`**: (Optional) Web interface for database management.

## 🚀 Deployment Steps

### 1. Configure Environment

Ensure your `.env` file contains the correct database credentials. The default `docker-compose.yml` uses:
-   User: `gridtokenx`
*   Password: `gridtokenx_password`

### 2. Start the Stack

```bash
docker compose up -d
```

### 3. Verify Health

Check the status of all containers:

```bash
docker compose ps
```

The simulator container will wait for the databases to pass their health checks before starting.

## 📁 Persistent Storage

The following Docker volumes are used to ensure data persistence across restarts:

-   `postgres_data`: Relational data.
-   `gis_postgres_data`: Spatial topology models.
-   `influxdb_data`: Historical telemetry.
-   `redis_data`: Cache state.

## 🌐 Networking

All services are connected via the `gridtokenx-network` (bridge). Within the network, services can communicate using their container names:
-   Postgres: `postgres:5432`
-   GIS Postgres: `gis-postgres:5432`
-   InfluxDB: `http://influxdb:7020`

## 🛠️ Common Commands

| Task | Command |
| :--- | :--- |
| **Stop Stack** | `docker compose down` |
| **View Simulator Logs** | `docker compose logs -f simulator` |
| **Rebuild Image** | `docker compose build simulator` |
| **Reset Data** | `docker compose down -v` (CAUTION: Deletes all volumes) |

---
_Next: [Grid Integration Architecture](../architecture/grid-integration.md)_
