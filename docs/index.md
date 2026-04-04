# Smart Meter Simulator - Documentation

**Version:** 3.0.0
**Implementation Status:** Phase 24 (Thai Grid Integration & Spatial Analytics)

Welcome to the Smart Meter Simulator documentation. This simulator provides high-fidelity AMI (Advanced Metering Infrastructure) and Grid Orchestration for the GridTokenX P2P energy trading platform.

---

## Documentation Structure

### 📚 Guides

Practical guides for common tasks and workflows:

| Document | Description |
|----------|-------------|
| [Getting Started](guides/getting-started.md) | Quick start guide for new users |
| [Configuration Guide](guides/configuration.md) | Environment and configuration settings |
| [Running Simulations](guides/running-simulations.md) | How to run and manage simulations |
| [Docker Deployment](guides/docker-deployment.md) | Docker-based deployment guide |

### 🏗️ Architecture

Technical architecture and design documentation:

| Document | Description |
|----------|-------------|
| [System Overview](architecture/overview.md) | High-level system architecture |
| [Simulation Engine](architecture/simulation-engine.md) | Core simulation orchestration |
| [Smart Meter Model](architecture/smart-meter.md) | Smart meter implementation details |
| [Grid Integration](architecture/grid-integration.md) | Pandapower and state estimation |
| [Market Engine](architecture/market-engine.md) | P2P trading and pricing mechanisms |
| [Transport Layer](architecture/transport-layer.md) | Data delivery mechanisms |

### 📡 API Reference

REST API and WebSocket documentation:

| Document | Description |
|----------|-------------|
| [API Overview](api/overview.md) | API introduction and authentication |

**Additional API Documentation:**
- **PostGIS API Reference:** [integration/POSTGIS_API_REFERENCE.md](integration/POSTGIS_API_REFERENCE.md)
- **Electrical Grid API:** [implementation/ELECTRICAL_GRID_API_ENDPOINTS.md](implementation/ELECTRICAL_GRID_API_ENDPOINTS.md)
- **Power Validation API:** [implementation/POWER_VALIDATION_API.md](implementation/POWER_VALIDATION_API.md)

### 🔌 Integration Guides

External system integration and database setup:

| Document | Description |
|----------|-------------|
| [PostGIS Integration](integration/POSTGIS_INTEGRATION.md) | Complete PostGIS spatial database setup |
| [PostGIS Quick Start](integration/POSTGIS_QUICKSTART.md) | Quick start guide for PostGIS |
| [PostGIS API Reference](integration/POSTGIS_API_REFERENCE.md) | PostGIS REST API documentation |
| [PostGIS Summary](integration/POSTGIS_SUMMARY.md) | PostGIS features and capabilities |
| [Thai Grid Integration](integration/THAI_GRID_INTEGRATION.md) | Thai electrical grid (EGAT/MEA/PEA) modeling |
| [Thai Infrastructure Map](integration/THAI_INFRASTRUCTURE_MAP_INTEGRATION.md) | React map viewer integration |
| [Thai Map Quick Start](integration/THAI_INFRASTRUCTURE_MAP_QUICKSTART.md) | Map viewer quick start guide |
| [GIS Database Compose](integration/GIS_DATABASE_COMPOSE.md) | Docker Compose for GIS database |
| [Database Migration](integration/DATABASE_MIGRATION_GUIDE.md) | Database migration procedures |
| [Migration Summary](integration/MIGRATION_SUMMARY.md) | Migration completion report |

### 📊 Datasets

Data source documentation and import guides:

| Document | Description |
|----------|-------------|
| [OpenStreetMap Datasets](datasets/OSMOSE_DATASETS.md) | OSM data extraction and usage |
| [OSM Integration Complete](datasets/OSMOSE_INTEGRATION_COMPLETE.md) | OpenStreetMap integration report |
| [EGAT Data Import](datasets/EGAT_DATA_IMPORT_GUIDE.md) | EGAT infrastructure data import |
| [Thailand Power Plants](datasets/THAILAND_POWER_PLANTS.md) | Thai power plant dataset |
| [Thailand Solar Installations](datasets/THAILAND_SOLAR_INSTALLATIONS.md) | Solar installation dataset |

### 📖 Reference

Technical specifications and detailed references:

| Document | Description |
|----------|-------------|
| [Meter Specification](reference/meter-spec.md) | Complete AMI specification (Phases 1-24) |
| [Pandapower Integration](reference/pandapower.md) | Grid modeling integration guide |
| [Thai Tariffs](reference/thai-tariffs.md) | Thai electricity tariff structures |
| [Thai Market Analysis](reference/thai-market.md) | Thai electricity market dynamics |
| [Economic Models](reference/economic-models.md) | Single Buyer vs. P2P pricing |
| [Thai Grid Topology](reference/thai-grid-topology.md) | Thai distribution network models |
| [Grid Map Viewer](reference/grid-map-viewer.md) | Map viewer technical documentation |

### 🗺️ OSMOSE QA

OpenStreetMap quality assurance and validation:

| Document | Description |
|----------|-------------|
| [OSMOSE Overview](osmose/README.md) | OSMOSE integration overview |
| [OSMOSE Architecture](osmose/ARCHITECTURE.md) | System architecture and design |
| [Feature Comparison](osmose/FEATURE_COMPARISON.md) | Feature comparison with original OSMOSE |
| [Thai Infrastructure Data Sources](osmose/THAI_ELECTRICAL_INFRASTRUCTURE_DATA_SOURCES.md) | Thai electrical data sources |
| [French to Thai Adaptation](osmose/HOW_TO_ADAPT_FRENCH_POWER_ANALYSERS_FOR_THAILAND.md) | Adaptation guide for Thai context |
| [OSMOSE Index](osmose/INDEX.md) | Complete OSMOSE documentation index |

### 📝 Implementation Reports

Phase completion reports and implementation status:

| Document | Description |
|----------|-------------|
| [Phase 23 OSM Integration](implementation/PHASE23_OSMOSE_INTEGRATION.md) | OpenStreetMap integration (Phase 23) |
| [Phase 23 Quick Start](implementation/PHASE23_QUICKSTART.md) | Phase 23 quick start guide |
| [Phase 24A Thai Power Analysers](implementation/PHASE24A_THAI_POWER_ANALYSERS_COMPLETE.md) | Thai power analysis completion |
| [Power Infrastructure Complete](implementation/POWER_INFRASTRUCTURE_COMPLETE.md) | Power infrastructure implementation |
| [Electrical Grid API](implementation/ELECTRICAL_GRID_API_ENDPOINTS.md) | Electrical grid API documentation |
| [Electrical Grid Map Integration](implementation/ELECTRICAL_GRID_INTEGRATION_WITH_EXISTING_MAP.md) | Grid integration with existing map |
| [Power Validation API](implementation/POWER_VALIDATION_API.md) | Power validation endpoints |
| [Project Status Summary](implementation/PROJECT_STATUS_SUMMARY.md) | Overall project status report |

---

## Quick Links

### External Resources

- [GitHub Repository](https://github.com/gridtokenx/gridtokenx-smartmeter-simulator)
- [GridTokenX Platform](https://github.com/gridtokenx-platform-infa)
- [Solana Documentation](https://docs.solana.com/)
- [Pandapower Documentation](https://www.pandapower.org/)

### Key Files

| File | Purpose |
|------|---------|
| [`README.md`](../README.md) | User-facing project overview |
| [`QWEN.md`](../QWEN.md) | Development context |
| [`pyproject.toml`](../pyproject.toml) | Dependencies and build configuration |
| [`.env.example`](../.env.example) | Environment variable template |

---

## Support

For issues and questions:
- **Bug Reports:** GitHub Issues
- **Technical Questions:** GitHub Discussions
- **Security Issues:** Contact security@gridtokenx.io

---

_Maintained by the GridTokenX Engineering Team_
