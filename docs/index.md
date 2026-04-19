# GridTokenX Smart Meter Simulator Documentation

Welcome to the documentation for the **GridTokenX Smart Meter Simulator**. This system provides high-fidelity AMI (Advanced Metering Infrastructure) simulation with integrated grid analysis, VPP orchestration, and island-based microgrid modeling.

## Documentation Map

### [Getting Started](guides/getting-started.md)

Quickly set up the simulator using `uv` and `docker compose`. Covers the new `backend/` + `frontend/` project structure.

### Architecture

Understand the core components and how they interact.

- [System Overview](architecture/overview.md)
- [Simulation Engine](architecture/simulation-engine.md)
- [Smart Meter Model](architecture/smart-meter.md)
- [Grid Integration (Pandapower + EGAT)](architecture/grid-integration.md)
- [VPP & Market Engine](architecture/market-engine.md)
- [Transport Layer](architecture/transport-layer.md)

### Integration

How the simulator connects to external systems.

- [Rust Acceleration (PyO3)](integration/RUST_ACCELERATION.md)
- [InfluxDB Storage](integration/INFLUXDB_COMPLETE_STORAGE.md)
- [InfluxDB Real-Time Database](integration/INFLUXDB_REALTIME_DATABASE.md)
- [PostGIS Integration](integration/POSTGIS_INTEGRATION.md)
- [Thai Grid Integration](integration/THAI_GRID_INTEGRATION.md)
- [API v1 Reference](integration/API_V1_REFERENCE.md)

### Guides

Step-by-step operational guides.

- [Getting Started](guides/getting-started.md)
- [Configuration](guides/configuration.md)
- [Running Simulations](guides/running-simulations.md)
- [Docker Deployment](guides/docker-deployment.md)
- [Using OSM Data (Thailand Grid)](guides/using_osm_data_thailand_grid.md)
- [Power Plants & PostGIS](guides/power_plants_postgis_integration.md)

### Reference

Deep dives into specifications and data models.

- [Meter Specification](reference/meter-spec.md)
- [Pandapower Integration](reference/pandapower.md)
- [Thai Tariffs](reference/thai-tariffs.md)
- [Thai Market Dynamics](reference/thai-market.md)
- [Economic Models](reference/economic-models.md)
- [Thai Grid Topology](reference/thai-grid-topology.md)
- [OSM Power Tagging](reference/osm-power-tagging.md)

---

_Maintained by the GridTokenX Engineering Team._
