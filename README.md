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

### Docker (Recommended)

```bash
docker-compose up -d
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

### User Guides

| Document             | Description                      |
| -------------------- | -------------------------------- |
| `README.md`          | This file (project overview)     |
| `simulator_logic.md` | Pricing model comparison         |
| `TOU.md`             | Thai TOU tariff rates            |
| `TOU_list.md`        | Thai electricity market analysis |
| `meter_spec.md`      | AMI specification                |
| `pandapower.md`      | Pandapower integration guide     |

### Technical Documentation

| Document                                    | Description                       |
| ------------------------------------------- | --------------------------------- |
| `docs/index.md`                             | Technical documentation index     |
| `docs/PRICE_PROVIDER_ABSTRACTION.md`        | Price provider architecture & API |
| `docs/price_history.md`                     | Price history storage & analytics |
| `docs/websocket_prices.md`                  | Real-time price streaming         |
| `docs/pandapower-technical.md`              | Pandapower integration details    |
| `docs/PERSISTENT_STORAGE_IMPLEMENTATION.md` | SQLite persistence layer          |
| `docs/THAI_MARKET_INTEGRATION.md`           | Thai market integration guide     |
| `docs/`                                     | Full technical documentation      |

## License

Part of the GridTokenX Ecosystem.

---

_Maintained by the GridTokenX Engineering Team._
