# Wiki Log

Append-only chronological record of wiki operations. Each entry starts with a consistent prefix for grep-friendly parsing.

---

## [2026-04-10] ingest | Wiki bootstrap — Phase 1 (25 pages created)

Created initial wiki structure and first batch of content pages for GridTokenX Smart Meter Simulator project.

**Infrastructure created:**
- `SCHEMA.md` — Wiki maintenance conventions and LLM instructions
- `index.md` — Content catalog with ✅/📋 status tracking (55 planned, 25 created)
- `log.md` — This file (append-only operation log)

**Entity pages (6):**
- `entities/simulation-engine.md` — Tick cycle, Rust bridge, orchestration
- `entities/smart-meter.md` — Ed25519, accuracy classes, battery/EV, droop
- `entities/state-estimator.md` — WLS, Iwamoto, chi-squared, normalized residuals
- `entities/vpp-orchestrator.md` — aFRR, multi-objective dispatch, Rust engine
- `entities/market-engine.md` — Double auction, LMP, settlement
- `entities/transport-layer.md` — HTTP, gRPC, MQTT, Kafka, InfluxDB, WebSocket, Composite

**Concept pages (8):**
- `concepts/state-estimation.md` — WLS algorithm, observability, pseudo-measurements
- `concepts/bad-data-detection.md` — Chi-squared test, normalized residuals, FDI
- `concepts/droop-control.md` — 5% droop, ±20 mHz deadband, curve diagram
- `concepts/afrr.md` — aFRR calculation, flexibility, dispatch sequence
- `concepts/multi-objective-dispatch.md` — SoC 30% + Price 40% + Carbon 30%
- `concepts/lmp.md` — Locational Marginal Pricing (Energy + Congestion + Losses)
- `concepts/double-auction.md` — Bid/ask matching, clearing, order book
- `concepts/measurement-noise-model.md` — σ = (Class/300) × |Value|, per-parameter multipliers

**Protocol pages (4):**
- `protocols/ed25519-signing.md` — Keypair, signing payload, Solana compatibility
- `protocols/dlms-cosem.md` — IEC 62056, OBIS codes, protobuf, gRPC service
- `protocols/cim-rdf-xml.md` — IEC 61970, RDF/XML, pandapower mapping
- `protocols/websocket-protocol.md` — JSON schema, message rate, client example

**Market pages (3):**
- `markets/thai-electricity-market.md` — EGAT/MEA/PEA structure, wheeling, ERC sandbox
- `markets/tou-tariffs.md` — On/off-peak schedule, rates, TOU vs progressive
- `markets/p2p-energy-trading.md` — Trading flow, Solana settlement, economics

**Integration pages (4):**
- `integration/rust-acceleration.md` — PyO3 API, benchmarks, build instructions
- `integration/influxdb-schema.md` — 5 measurement types, tags/fields, Flux queries
- `integration/postgis-integration.md` — Spatial tables, operations, Mapbox matching
- `integration/thai-grid-topology.md` — 4-level hierarchy, regional models, equipment standards

**Reference pages (2):**
- `reference/energyreading-model.md` — Complete field list, Rust + Python definitions, precision
- `reference/performance-benchmarks.md` — Python vs Rust, scaling, bottleneck analysis

**Pages remaining (30 📋):**
- Entities: Frequency Regulator, Island Manager, Pandapower Adapter, Meter Generator, FastAPI App, CLI, Price Provider, Billing Engine, FDI Attacker
- Concepts: Standard Load Profiles, Net Metering, Pseudo-Measurements, Brownian Motion Simulation
- Protocols: gRPC Transport, MQTT Transport, Kafka Transport
- Markets: Progressive Tariff Tiers, VPP Revenue Streams, Carbon Offset Model
- Integration: InfluxDB Integration, Docker Stack, Mosaik Co-Simulation, OpenTelemetry
- Reference: ANSI C12.20 Accuracy Classes, Solana Integration, API Endpoint Reference, Meter Type Distribution

**Source material analyzed:**
- 23 documentation files in docs/ (architecture, guides, integration, reference)
- Full src/smart_meter_simulator/ codebase structure
- pyproject.toml, docker-compose.yml, pytest.ini, .env.example
- Rust source: src/rust_sim/src/lib.rs (PyO3 reading generation + VPP dispatch)

---

## [2026-04-10] ingest | Wiki Phase 2 — 22 additional pages (total 47, 85%)

Second batch covering all remaining entities, concepts, protocols, markets, integration, and reference topics.

**Entity pages (4):**
- `entities/frequency-regulator.md` — Swing equation, RoCoF, damping, cascade
- `entities/island-manager.md` — Slack bus swap, black start, grid-forming selection
- `entities/pandapower-adapter.md` — Sign convention, std_dev, Delaunay+MST topology
- `entities/meter-generator.md` — Type distribution, manufacturer IDs, feeder assignment

**Concept pages (4):**
- `concepts/standard-load-profiles.md` — H0/G0 profiles, weekday vs weekend
- `concepts/net-metering.md` — FiT vs retail, battery arbitrage, progressive tiers
- `concepts/pseudo-measurements.md` — Zero-injection, weight assignment, masking risk
- `concepts/brownian-motion-simulation.md` — Ornstein-Uhlenbeck, autocorrelated noise

**Protocol pages (3):**
- `protocols/grpc-transport.md` — Protobuf service, HTTP/2, betterproto
- `protocols/mqtt-transport.md` — Mosquitto, topic structure, QoS 1
- `protocols/kafka-transport.md` — Partitioning, consumer use cases, throughput

**Market pages (3):**
- `markets/progressive-tariff-tiers.md` — 3-tier progressive, social policy, TOU comparison
- `markets/vpp-revenue-streams.md` — aFRR, peak shaving, P2P commission, carbon
- `markets/carbon-offset-model.md` — Thai grid intensity, REC minting, dispatch weight

**Integration pages (4):**
- `integration/influxdb-integration.md` — Write transport, query service, Flux queries
- `integration/docker-stack.md` — 8 services, network, volumes, health checks, build
- `integration/mosaik-co-simulation.md` — Federate role, co-sim step, adapter stub
- `integration/opentelemetry.md` — OTEL tracing/metrics, FastAPI instrumentation

**Reference pages (4):**
- `reference/ansi-c12-20-accuracy-classes.md` — 4 classes, std_dev, estimation weight
- `reference/solana-integration.md` — Ed25519 verification, Energy Token Program, GTNX
- `reference/api-endpoint-reference.md` — 67+ endpoints grouped by domain
- `reference/meter-type-distribution.md` — Ratios, DER capability, scenario presets

**Skipped (source files not found):**
- Billing Engine (`billing.py` not found), FDI Attacker (`attacker.py` not found), Price Provider (`price_*.py` not in expected location), CLI (covered by `cli.py` in Phase 1)

---
