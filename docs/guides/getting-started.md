# Getting Started

Welcome to the **GridTokenX Smart Meter Simulator**! This guide will walk you through the process of setting up and running the simulator on your local machine.

## 📋 Prerequisites

Before you begin, ensure you have the following tools installed:

1.  **Python 3.11+**: The core simulator is written in Python.
2.  **uv**: A fast Python package installer and resolver.
    *   `curl -LsSf https://astral.sh/uv/install.sh | sh`
3.  **Docker & Docker Compose**: For running the database and infrastructure.
4.  **Rust (Optional)**: Required only if you plan to modify or recompile the `rust_sim` acceleration module.

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/GridTokenX/gridtokenx-smartmeter-simulator.git
cd gridtokenx-smartmeter-simulator
```

### 2. Initialize Infrastructure

Start the PostgreSQL, PostGIS, and Redis services using Docker Compose:

```bash
docker compose up -d
```

### 3. Sync Dependencies

Use `uv` to create a virtual environment and install all required dependencies:

```bash
uv sync
```

## 🏃 Running the Simulator

### Server Mode (REST API + gRPC)

Recommended mode for production-like environments where you need to interact via the web dashboard or external APIs.

```bash
uv run uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8082
```

### Standalone Mode (Direct Output)

Ideal for quick testing and local debugging.

```bash
uv run start-simulator --mode standalone --meters 20
```

## 🌐 Accessing Services

Once the simulator is running, you can access the following services:

| Service | URL | Description |
| :--- | :--- | :--- |
| **Simulator API** | [http://localhost:8082](http://localhost:8082) | Main REST API |
| **Interactive Docs** | [http://localhost:8082/docs](http://localhost:8082/docs) | Swagger UI for API testing |
| **PostgreSQL** | `localhost:5432` | Relational Database |
| **PostGIS** | `localhost:5433` | Spatial Grid Topology |

## 🧪 Verifying the Installation

To verify that everything is working correctly, run the core test suite:

```bash
uv run pytest
```

---
_Next: [Configuration Guide](configuration.md)_
