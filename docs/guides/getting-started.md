# Getting Started

Welcome to the **GridTokenX Smart Meter Simulator**! This guide will walk you through the process of setting up and running the simulator on your local machine.

## 📋 Prerequisites

Before you begin, ensure you have the following tools installed:

1.  **Python 3.11+**: The core simulator is written in Python.
2.  **uv**: A fast Python package installer and resolver.
    *   `curl -LsSf https://astral.sh/uv/install.sh | sh`
3.  **Bun**: JavaScript runtime for the Next.js frontend.
    *   `curl -fsSL https://bun.sh/install | bash`
4.  **Docker & Docker Compose**: For running the database and infrastructure.
5.  **Rust (Optional)**: Required only if you plan to modify or recompile the `rust_sim` acceleration module.

## 📁 Project Structure

The project is split into two top-level directories:

```
gridtokenx-smartmeter-simulator/
├── backend/          # Python FastAPI simulator (uv-managed)
│   ├── src/smart_meter_simulator/
│   ├── tests/
│   ├── scripts/
│   ├── pyproject.toml
│   └── .env.example
└── frontend/         # Next.js 16 dashboard (Bun-managed)
    ├── src/
    ├── package.json
    └── next.config.ts
```

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/GridTokenX/gridtokenx-smartmeter-simulator.git
cd gridtokenx-smartmeter-simulator
```

### 2. Initialize Infrastructure

Start the PostgreSQL, PostGIS, Redis, and InfluxDB services using Docker Compose:

```bash
docker compose up -d
```

### 3. Sync Backend Dependencies

Use `uv` to create a virtual environment and install all required dependencies:

```bash
cd backend
uv sync
```

### 4. Install Frontend Dependencies

```bash
cd frontend
bun install
```

## 🏃 Running the Simulator

All backend commands are run from the `backend/` directory.

### Server Mode (REST API + gRPC)

Recommended mode for production-like environments where you need to interact via the web dashboard or external APIs.

```bash
cd backend
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

### Island Microgrid Scenario (Khanom–Samui–Phangan–Tao)

```bash
cd backend
./run_islands_sim.sh
```

### Khanom Power Station Scenario

```bash
cd backend
./run_khanom_sim.sh
```

### Standalone Mode (Direct Output)

Ideal for quick testing and local debugging.

```bash
cd backend
uv run start-simulator --mode standalone --meters 20
```

## 🖥️ Running the Frontend

```bash
cd frontend
bun run dev
```

The dashboard will be available at `http://localhost:3000`.

## 🌐 Accessing Services

Once the simulator is running, you can access the following services:

| Service | URL | Description |
| :--- | :--- | :--- |
| **Simulator API** | [http://localhost:8082](http://localhost:8082) | Main REST API |
| **Interactive Docs** | [http://localhost:8082/docs](http://localhost:8082/docs) | Swagger UI for API testing |
| **Frontend Dashboard** | [http://localhost:3000](http://localhost:3000) | Next.js map & telemetry UI |
| **PostgreSQL** | `localhost:5432` | Relational Database |
| **PostGIS** | `localhost:5433` | Spatial Grid Topology |
| **InfluxDB** | `localhost:8086` | Time-Series Database |
| **Redis** | `localhost:6379` | Cache & Pub/Sub |

## 🧪 Verifying the Installation

To verify that everything is working correctly, run the core test suite from the `backend/` directory:

```bash
cd backend
uv run pytest
```

---
_Next: [Configuration Guide](configuration.md)_
