# GridTokenX Smart Meter Simulator

High-fidelity AMI (Advanced Metering Infrastructure) and Grid Orchestration simulator for the GridTokenX ecosystem. Specialized in real-time power flow simulation (Pandapower), VPP grid services, and industrial-standard telemetry.

## 🚀 Project Overview

The **GridTokenX Smart Meter Simulator** is a sophisticated simulation platform designed to model electrical grids, smart meters, and energy markets. It features Rust-accelerated performance, integration with spatial databases (PostGIS), and support for various industrial communication protocols.

### Key Technologies
- **Backend:** Python 3.11+ (FastAPI, Pandapower, Pydantic, SQLAlchemy)
- **Acceleration:** Rust (PyO3, Maturin) for high-performance reading generation.
- **Frontend:** React (Vite, Bun, TailwindCSS, Mapbox/Maplibre)
- **Databases:** PostgreSQL (with PostGIS), InfluxDB (Time-series), Redis (Cache/PubSub)
- **Messaging:** Apache Kafka, MQTT
- **Protocols:** gRPC (DLMS/COSEM), WebSocket, HTTP/REST

---

## 🛠 Building and Running

### 1. Infrastructure Setup
The project uses Docker Compose to orchestrate its dependencies (Postgres, PostGIS, Redis, InfluxDB, Mosquitto).
```bash
docker compose up -d
```

### 2. Python Environment & Dependencies
The project uses `uv` for Python package management.
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### 3. Rust Acceleration (Optional but Recommended)
To build and install the Rust acceleration module:
```bash
cd src/rust_sim
maturin develop --release
cd ../..
```

### 4. Running the Simulator
The simulator can be run in **Server** or **Standalone** mode.

**Server Mode (REST API + WebSocket + UI):**
```bash
# Using the defined script
uv run start

# Or directly via uvicorn
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

**Standalone Mode (Direct Simulation):**
```bash
uv run python -m smart_meter_simulator.cli --mode standalone --meters 50
```

### 5. Frontend Development
The UI is located in the `ui/` directory and managed with `bun`.
```bash
cd ui
bun install
bun run dev
```

---

## 🧪 Testing & Validation

Run the full test suite using `pytest`:
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run benchmarks
uv run pytest tests/benchmark_rust_performance.py -v
```

---

## 📁 Project Structure

- `src/smart_meter_simulator/`: Core Python application.
    - `core/`: Simulation engine, meter models, VPP logic, Rust wrappers.
    - `adapters/`: Grid topology (Pandapower), State Estimation.
    - `transport/`: Communication layers (gRPC, MQTT, Kafka, InfluxDB).
    - `routers/`: FastAPI endpoints (API v1).
- `src/rust_sim/`: Rust implementation of performance-critical components.
- `ui/`: React-based management and visualization dashboard.
- `database/migrations/`: SQL scripts for Postgres/PostGIS schema setup.
- `docs/`: Extensive documentation on architecture, integration, and guides.
- `scripts/`: Utility scripts for GIS data processing and maintenance.

---

## 📐 Development Conventions

- **Style:** Adhere to PEP 8. Use `black` for formatting and `isort` for import sorting.
- **Typing:** Use Python type hints throughout the codebase.
- **Security:** Every meter reading is cryptographically signed using Ed25519.
- **Documentation:** Maintain and update documentation in the `docs/` directory.
- **Environment:** Configuration is managed via environment variables (see `.env.example`).

---

## 🗺️ Important URLs (Local Development)

| Service | URL |
|---------|-----|
| **Simulator API / UI** | [http://localhost:8082](http://localhost:8082) |
| **API Documentation** | [http://localhost:8082/docs](http://localhost:8082/docs) |
| **PostgreSQL** | `localhost:5432` |
| **PostGIS (GIS DB)** | `localhost:5433` |
| **InfluxDB UI** | [http://localhost:8086](http://localhost:8086) |
| **Grafana Dashboards** | [http://localhost:3001](http://localhost:3001) (admin/admin_password) |
| **Mosquitto (MQTT)** | `localhost:1883` |
