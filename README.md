# Smart Meter Simulator for GridTokenX

**Version: 3.0.0**

## Overview

A high-fidelity AMI (Advanced Metering Infrastructure) and Grid Orchestration simulator. Designed for the GridTokenX ecosystem, it supports everything from basic P2P energy trading to advanced grid stability, nodal pricing, and co-simulation.

### Project Maturity (Phase 22)

This project has surpassed its initial roadmap and is currently at **Phase 22 (Advanced Grid Intelligence)**. It provides production-grade modeling for distribution networks, market dynamics, and microgrid controls.

## Features

### Core AMI & Trading

- **High-Fidelity Meters**: Solar Prosumers, Grid Consumers, Battery/EV systems with Ed25519 cryptographic signing for blockchain settlement.
- **P2P Market Engine**: Real-time matching, dynamic pricing, and automated energy settlement.
- **Data Source Excellence**: Ultra-fast profile loading using Polars & Parquet; Standard Load Profile (SLP) generation for residential and commercial loads.

### Advanced Grid Intelligence

- **Nodal Pricing (LMP)**: Locational Marginal Pricing based on line congestion and nodal sensitivities.
- **Grid Stability**: Real-time frequency regulation, ROCOF metrics, and Virtual Power Plant (VPP) balancing orchestration.
- **State Estimation (SE)**: Robust WLS/Iwamoto estimation with iterative bad data detection (Chi-squared & Normalized Residuals).
- **Carbon Tracking**: Real-time carbon intensity calculation and REC (Renewable Energy Certificate) generation.

### Interoperability & Security

- **CIM Support**: IEC 61970 Common Information Model RDF/XML round-trip for network exchange.
- **Co-Simulation**: Mosaik-compliant adapter for multi-domain energy system simulation.
- **Cyber-Security**: False Data Injection (FDI) attack simulation and anomaly detection.

## Project Structure

```
smart-meter-simulator/
├── src/smart_meter_simulator/
│   ├── core/           # Simulation Engine, VPP, Market, Frequency Regulation
│   ├── adapters/       # Pandapower, State Estimator, CIM, Mosaik
│   ├── models/         # Pydantic data models for energy readings
│   ├── transport/      # Kafka, InfluxDB, WebSocket, HTTP delivery
│   └── utils/          # Crypto (Ed25519), ZK Proofs, Mapbox Matching
├── tests/              # Comprehensive test suite (Integration & Unit)
├── docs/               # Technical specs (meter_spec.md)
├── scripts/            # Standalone runners
└── pyproject.toml      # UV-managed project configuration
```

## Quick Start

### Docker (Recommended)

```bash
docker-compose up -d
```

### Manual Setup (UV)

```bash
# Install dependencies
uv sync

# Run standalone simulator (20 meters)
uv run start-simulator --mode standalone --meters 20
```

## Performance Success Metrics

- **Scalability**: Simulates 1000+ meters for 365 days in <5 minutes.
- **Accuracy**: State Estimation convergence >98% on IEEE 123-node feeders.
- **Reliability**: FDI attack detection rate >99%.

## License

Part of the GridTokenX Ecosystem.

---

_Maintained by the GridTokenX Engineering Team._
