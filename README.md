# Smart Meter Simulator for GridTokenX

**Version:** 3.0.0  
**Status:** (Multi-Currency Settlement & Tokenized Economy)

## Overview

High-fidelity AMI (Advanced Metering Infrastructure) and Grid Orchestration simulator for the GridTokenX ecosystem. Supports P2P energy trading, grid stability modeling, nodal pricing, and co-simulation.

## Features

### Core AMI & Trading

- **High-Fidelity Meters:** Solar prosumers, grid consumers, battery/EV systems with Ed25519 signing
- **P2P Market Engine:** Real-time matching, dynamic pricing, automated settlement
- **Data Source Excellence:** Polars/Parquet profile loading, SLP generation

### Advanced Grid Intelligence

- **Nodal Pricing (LMP):** Line congestion and nodal sensitivity pricing
- **Grid Stability:** Frequency regulation, ROCOF metrics, VPP orchestration
- **State Estimation:** WLS/Iwamoto with Chi-squared & normalized residuals
- **Carbon Tracking:** Real-time carbon intensity, REC generation

### Interoperability & Security

- **CIM Support:** IEC 61970 RDF/XML round-trip
- **Co-Simulation:** Mosaik-compliant adapter
- **Cyber-Security:** FDI attack simulation, anomaly detection

## Quick Start

### OrbStack / Docker (Recommended)

```bash
docker compose up -d
```

### Manual Setup (UV)

```bash
# Install dependencies
uv sync

# Run standalone simulator
uv run start-simulator --mode standalone --meters 20
```

## Project Structure

```
smart-meter-simulator/
├── src/smart_meter_simulator/
│   ├── core/           # Simulation engine, VPP, market, frequency
│   ├── adapters/       # Pandapower, SE, CIM, Mosaik
│   ├── models/         # Pydantic data models
│   ├── transport/      # Kafka, InfluxDB, WebSocket, HTTP
│   └── utils/          # Crypto, ZK proofs, Mapbox
├── tests/              # Test suite
├── docs/               # Technical documentation
└── pyproject.toml      # UV configuration
```

## Performance Metrics

| Metric      | Target                              |
| ----------- | ----------------------------------- |
| Scalability | 1000+ meters × 365 days in <5 min   |
| Accuracy    | SE convergence >98% (IEEE 123-node) |
| Reliability | FDI detection rate >99%             |

## API Endpoints

### Price Comparison

- `POST /api/v1/price/compare` - Compare utility vs P2P prices
- `GET /api/v1/price/utility-rates` - Get utility rates
- `GET /api/v1/price/p2p-dynamic` - Get dynamic P2P price

### Revenue Analysis

- `POST /api/v1/revenue/compare` - Compare revenue models
- `GET /api/v1/revenue/optimize` - Optimize revenue configuration

### Market Data

- `GET /api/v1/p2p/market-prices` - Get market prices
- `POST /api/v1/p2p/calculate-cost` - Calculate P2P transaction cost

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_dynamic_pricing.py -v
```

## Documentation

### Quick Start

| Document | Description |
| -------- | ----------- |
| [Getting Started](docs/guides/getting-started.md) | Installation and quick start |
| [Configuration](docs/guides/configuration.md) | Environment and settings |
| [Running Simulations](docs/guides/running-simulations.md) | Simulation management |
| [Docker Deployment](docs/guides/docker-deployment.md) | Docker-based deployment |

### Architecture

| Document | Description |
| -------- | ----------- |
| [System Overview](docs/architecture/overview.md) | High-level architecture |
| [Simulation Engine](docs/architecture/simulation-engine.md) | Core orchestration |
| [Smart Meter Model](docs/architecture/smart-meter.md) | Meter implementation |
| [Grid Integration](docs/architecture/grid-integration.md) | Pandapower and SE |
| [Market Engine](docs/architecture/market-engine.md) | P2P trading and pricing |
| [Transport Layer](docs/architecture/transport-layer.md) | Data delivery |

### API Reference

| Document | Description |
| -------- | ----------- |
| [API Overview](docs/api/overview.md) | REST API and WebSocket |

### Reference Specifications

| Document | Description |
| -------- | ----------- |
| [Meter Specification](docs/reference/meter-spec.md) | AMI specification (Phases 1-22) |
| [Pandapower Integration](docs/reference/pandapower.md) | Grid modeling guide |
| [Thai Tariffs](docs/reference/thai-tariffs.md) | TOU tariff rates (2026) |
| [Thai Market Analysis](docs/reference/thai-market.md) | Market dynamics |
| [Economic Models](docs/reference/economic-models.md) | Single Buyer vs. P2P |

### Development

| Document | Description |
| -------- | ----------- |
| [QWEN.md](QWEN.md) | Development context |
| [docs/index.md](docs/index.md) | Full documentation index |

## License

Part of the GridTokenX Ecosystem.

---

_Maintained by the GridTokenX Engineering Team._
