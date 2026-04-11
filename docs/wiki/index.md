# Wiki Index

Content-oriented catalog of all pages in the Smart Meter Simulator wiki. Organized by category. The LLM reads this first to find relevant pages.

**Legend:** ✅ Created | 📋 Planned (entry reserved, page not yet written)

---

## Entities

| Page | Summary | Status | Tags | Updated |
|------|---------|--------|------|---------|
| [[Simulation Engine]] | Core orchestrator — tick cycle, meter lifecycle, Rust acceleration bridge | ✅ | `core` `engine` | 2026-04-10 |
| [[Smart Meter]] | SmartMeter class — Ed25519 signing, accuracy classes, battery/EV logic | ✅ | `meter` `crypto` `battery` | 2026-04-10 |
| [[State Estimator]] | WLS and Iwamoto algorithms — chi-squared test, normalized residuals | ✅ | `grid` `estimation` | 2026-04-10 |
| [[VPP Orchestrator]] | Virtual Power Plant — aFRR, multi-objective dispatch, cluster aggregation | ✅ | `vpp` `dispatch` | 2026-04-10 |
| [[Market Engine]] | P2P trading, double auction, order matching, settlement | ✅ | `market` `p2p` | 2026-04-10 |
| [[Transport Layer]] | Abstract transport interface — HTTP, gRPC, MQTT, InfluxDB, Kafka, WebSocket | ✅ | `transport` `protocols` | 2026-04-10 |
| [[Frequency Regulator]] | Grid frequency control — swing equation, RoCoF, damping | ✅ | `frequency` `stability` | 2026-04-10 |
| [[Island Manager]] | Microgrid islanding detection, load shedding, black start sequencing | ✅ | `island` `microgrid` | 2026-04-10 |
| [[Pandapower Adapter]] | Maps meter readings to pandapower measurement tables — bus, line, load, sgen | ✅ | `grid` `pandapower` | 2026-04-10 |
| [[Meter Generator]] | Meter configuration generation — type distribution, capacity assignment | ✅ | `meter` `config` | 2026-04-10 |
| [[FastAPI App]] | Main application — lifespan, middleware, WebSocket manager, OTEL | 📋 | `api` `fastapi` | — |
| [[CLI]] | start-simulator entry point — server vs standalone modes, CLI flags | 📋 | `cli` `config` | — |
| [[Price Provider]] | ToUPriceProvider — Thai TOU tariffs, on/off-peak, Ft adjustment | 📋 | `price` `thai` | — |
| [[Billing Engine]] | ERC ladder billing, net metering, Thai utility tariffs | 📋 | `billing` `thai` | — |
| [[FDI Attacker]] | False data injection attack simulation — anomaly detection testing | 📋 | `security` `attack` | — |

## Concepts

| Page | Summary | Status | Tags | Updated |
|------|---------|--------|------|---------|
| [[State Estimation]] | WLS algorithm overview — why it matters, observability analysis | ✅ | `grid` `algorithm` | 2026-04-10 |
| [[Bad Data Detection]] | Chi-squared test + normalized residuals — identifying bad measurements | ✅ | `grid` `quality` | 2026-04-10 |
| [[Droop Control]] | Frequency-power droop curve — 5% droop, ±0.02 Hz deadband | ✅ | `frequency` `control` | 2026-04-10 |
| [[aFRR]] | automatic Frequency Restoration Reserve — upward/downward flexibility | ✅ | `frequency` `vpp` | 2026-04-10 |
| [[Multi-Objective Dispatch]] | SoC balance (30%) + Price (40%) + Carbon (30%) optimization | ✅ | `vpp` `optimization` | 2026-04-10 |
| [[LMP]] | Locational Marginal Pricing — nodal prices, congestion, losses | ✅ | `market` `pricing` | 2026-04-10 |
| [[Double Auction]] | P2P market clearing — bid/ask matching, uniform price | ✅ | `market` `mechanism` | 2026-04-10 |
| [[Measurement Noise Model]] | σ = (Class/300) × \|Value\| — ANSI C12.20 accuracy class simulation | ✅ | `meter` `accuracy` | 2026-04-10 |
| [[Standard Load Profiles]] | H0 (residential) and G0 (commercial) consumption curves | ✅ | `load` `profiles` | 2026-04-10 |
| [[Net Metering]] | Surplus/deficit calculation, FiT rates, battery arbitrage | ✅ | `meter` `economics` | 2026-04-10 |
| [[Pseudo-Measurements]] | Zero-injection buses — improving observability without physical meters | ✅ | `grid` `estimation` | 2026-04-10 |
| [[Brownian Motion Simulation]] | Autocorrelated noise for generation/consumption time series | ✅ | `simulation` `noise` | 2026-04-10 |

## Protocols

| Page | Summary | Status | Tags | Updated |
|------|---------|--------|------|---------|
| [[Ed25519 Signing]] | Solana-compatible Ed25519 keypair generation and reading signature | ✅ | `crypto` `solana` | 2026-04-10 |
| [[DLMS/COSEM]] | IEC 62056 device language — OBIS codes, gRPC ingestion | ✅ | `protocol` `industrial` | 2026-04-10 |
| [[CIM RDF/XML]] | IEC 61970 Common Information Model — grid topology exchange | ✅ | `protocol` `interop` | 2026-04-10 |
| [[WebSocket Protocol]] | Real-time meter reading broadcast format — JSON schema | ✅ | `transport` `websocket` | 2026-04-10 |
| [[gRPC Transport]] | Protobuf-based telemetry ingestion — DLMS/COSEM wrapper | ✅ | `transport` `grpc` | 2026-04-10 |
| [[MQTT Transport]] | Eclipse Mosquitto broker — AMI telemetry publishing | ✅ | `transport` `mqtt` | 2026-04-10 |
| [[Kafka Transport]] | Event streaming — meter_readings topic, partition strategy | ✅ | `transport` `kafka` | 2026-04-10 |

## Markets

| Page | Summary | Status | Tags | Updated |
|------|---------|--------|------|---------|
| [[Thai Electricity Market]] | EGAT/MEA/PEA structure — single buyer model, P2P sandbox | ✅ | `thai` `market` | 2026-04-10 |
| [[TOU Tariffs]] | Time-of-Use pricing — on-peak 09:00-22:00, off-peak rates | ✅ | `thai` `tariff` | 2026-04-10 |
| [[P2P Energy Trading]] | Surplus discovery, nodal pricing, Solana GTNX settlement | ✅ | `p2p` `blockchain` | 2026-04-10 |
| [[Progressive Tariff Tiers]] | 3-tier rates: 0-150 kWh @ 3.24, 151-400 @ 4.22, 400+ @ 4.42 Baht | ✅ | `thai` `tariff` | 2026-04-10 |
| [[VPP Revenue Streams]] | aFRR, peak shaving, P2P commissions, carbon credits | ✅ | `vpp` `economics` | 2026-04-10 |
| [[Carbon Offset Model]] | 0.7 Baht/kWh carbon credit, gCO2/kWh tracking | ✅ | `carbon` `economics` | 2026-04-10 |

## Integration

| Page | Summary | Status | Tags | Updated |
|------|---------|--------|------|---------|
| [[Rust Acceleration]] | PyO3 + Maturin — 3,655-7,500x speedup for reading generation | ✅ | `performance` `rust` | 2026-04-10 |
| [[InfluxDB Schema]] | Time-series data model — meter_reading, grid_state_estimation, vpp_dispatch | ✅ | `database` `timeseries` | 2026-04-10 |
| [[PostGIS Integration]] | Spatial database — nearest neighbor, radius, GeoJSON export | ✅ | `database` `spatial` | 2026-04-10 |
| [[Thai Grid Topology]] | MEA/PEA network models — 22kV MV, 400V LV, regional variants | ✅ | `thai` `grid` | 2026-04-10 |
| [[InfluxDB Integration]] | Time-series storage + query service — Flux queries, Grafana | ✅ | `database` `timeseries` | 2026-04-10 |
| [[Docker Stack]] | 7-container compose — PostgreSQL, PostGIS, InfluxDB, Redis, Mosquitto | ✅ | `infrastructure` `docker` | 2026-04-10 |
| [[Mosaik Co-Simulation]] | Multi-domain co-simulation adapter — federated simulation | ✅ | `cosim` `mosaik` | 2026-04-10 |
| [[OpenTelemetry]] | OTEL tracing and metrics — OTLP exporter, FastAPI instrumentation | ✅ | `observability` `otel` | 2026-04-10 |

## Reference

| Page | Summary | Status | Tags | Updated |
|------|---------|--------|------|---------|
| [[EnergyReading Model]] | Complete data model — 20+ fields, electrical parameters, DER state | ✅ | `spec` `model` | 2026-04-10 |
| [[Performance Benchmarks]] | Rust vs Python comparison — reading generation, VPP dispatch | ✅ | `performance` `benchmarks` | 2026-04-10 |
| [[ANSI C12.20 Accuracy Classes]] | Class 0.2, 0.5, 1.0, 2.0 — error ranges, typical use cases | ✅ | `spec` `meter` | 2026-04-10 |
| [[Solana Integration]] | Ed25519 compatibility, Energy Token program, REC data feeds | ✅ | `blockchain` `solana` | 2026-04-10 |
| [[API Endpoint Reference]] | 67+ endpoints under /api/v1/ — REST + WebSocket | ✅ | `api` `reference` | 2026-04-10 |
| [[Meter Type Distribution]] | Solar 35%, Consumer 30%, Hybrid 20%, Battery 5%, EV 10% | ✅ | `config` `meter` | 2026-04-10 |

---

## Statistics

- **Total pages planned:** 55
- **Pages created:** 47 ✅
- **Pages planned:** 8 📋 (Billing Engine, FDI Attacker, FastAPI App, CLI, Price Provider — files not found in codebase)
- **Categories:** 6 (entities, concepts, protocols, markets, integration, reference)
- **Last full lint:** 2026-04-10
- **Creation progress:** 85%
