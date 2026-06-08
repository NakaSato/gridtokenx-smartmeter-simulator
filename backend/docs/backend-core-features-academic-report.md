# Backend Core Features for Academic Report

## Research Positioning

The backend implements a topology-aware Advanced Metering Infrastructure (AMI)
digital twin for prosumer distribution grids. It combines smart-meter simulation,
physical feeder modeling, photovoltaic generation, load behavior, real telemetry
replay, and signed DLMS/COSEM-style telemetry export for GridTokenX settlement
integration.

Suggested academic description:

> This system provides a backend simulation framework for studying smart-meter
> telemetry, prosumer energy exchange, and distribution-grid operating conditions.
> The simulator maps AMI meters onto electrical feeder topology, computes
> voltage and power-flow effects from meter injections, and exports signed
> meter data for downstream oracle and settlement services.

## Main Backend Contributions

### 1. Topology-Aware AMI Digital Twin

The backend loads electrical feeder topology from GridLAB-D GLM files and
CINELDI/MATPOWER-style reference-grid folders. These inputs are normalized into
a common `GridTopology` model containing buses, lines, static loads, and PV
resources.

Academic framing:

- Enables feeder-level rather than meter-only simulation.
- Preserves the relationship between smart meters and physical grid buses.
- Supports experiments on different electrical network structures.

Implementation evidence:

- `src/smart_meter_simulator/core/topology.py`
- `src/smart_meter_simulator/core/topology_factory.py`
- `src/smart_meter_simulator/adapters/glm_topology_loader.py`
- `src/smart_meter_simulator/adapters/reference_grid_loader.py`

### 2. Physical Grid Simulation Engine

The `SimulationEngine` runs an asynchronous simulation loop. Each tick applies
telemetry overrides, generates meter readings, updates grid state, derives
frequency behavior, emits optional signed telemetry, and advances simulation
time.

Academic framing:

- Provides repeatable time-step simulation for AMI and grid studies.
- Supports both continuous real-time execution and manual step execution.
- Produces aggregate tick summaries for system-level analysis.

Implementation evidence:

- `src/smart_meter_simulator/core/engine.py`
- `src/smart_meter_simulator/core/reading_manager.py`

### 3. Feeder Power-Flow and Grid-State Analytics

The backend uses `pandapower` when available and falls back to a radial DistFlow
approximation. It computes bus voltages, line flows, line utilization,
congestion, line losses, transformer losses, transformer loading, and PV
curtailment.

Academic framing:

- Links prosumer meter behavior to distribution-grid operating constraints.
- Allows voltage, loss, congestion, and transformer-loading analysis.
- Supports grid-impact evaluation of distributed photovoltaic generation.

Implementation evidence:

- `src/smart_meter_simulator/core/grid_manager.py`

### 4. Smart-Meter and Measurement Model

The backend models multiple meter types, including grid consumers, residential
consumers, commercial meters, solar prosumers, hybrid prosumers, feeder meters,
and substation meters. Meter readings include energy generation, energy
consumption, surplus energy, deficit energy, voltage, current, reactive power,
frequency, power factor, temperature, and metadata.

Academic framing:

- Represents heterogeneous AMI devices in a prosumer distribution grid.
- Supports both consumer and bidirectional prosumer energy behavior.
- Encodes meter accuracy classes and measurement-channel availability.

Implementation evidence:

- `src/smart_meter_simulator/devices/ami.py`
- `src/smart_meter_simulator/models/reading.py`
- `src/smart_meter_simulator/config/enums.py`
- `src/smart_meter_simulator/config/channels.py`

### 5. Load and Photovoltaic Generation Modeling

The load model uses time-dependent consumption profiles with stochastic noise and
ZIP voltage response. The PV model uses `pvlib`/PVWatts when enabled, with
weather, location, surface tilt, azimuth, temperature coefficient, and DC/AC
ratio settings.

Academic framing:

- Captures time-varying consumer demand.
- Models voltage-sensitive load behavior.
- Simulates weather-dependent distributed PV output.

Implementation evidence:

- `src/smart_meter_simulator/devices/load.py`
- `src/smart_meter_simulator/devices/solar.py`
- `src/smart_meter_simulator/core/meter_logic/profiles.py`

### 6. Distributed Energy Resource Control Behavior

The backend includes distribution-grid control behavior such as frequency-watt
droop, PV volt-watt curtailment, MV/LV transformer modeling, and on-load tap
changer (OLTC) operation.

Academic framing:

- Enables analysis of DER control effects in high-PV feeders.
- Models inverter response to overvoltage and frequency deviation.
- Supports investigation of voltage regulation using transformer tap control.

Implementation evidence:

- `src/smart_meter_simulator/core/grid_manager.py`
- `src/smart_meter_simulator/core/meter_logic/electrical.py`
- `src/smart_meter_simulator/core/frequency.py`

### 7. Real-Telemetry Replay and Hybrid Simulation

The backend can replay measured telemetry from CSV files or reference-grid load
profiles. When telemetry exists for a meter, synthetic generation and load are
overridden. Meters without telemetry remain synthetic, enabling hybrid digital
twin experiments.

Academic framing:

- Bridges synthetic simulation and real measured data.
- Supports partial observability, where only some meters have real telemetry.
- Enables repeatable replay experiments using historical load profiles.

Implementation evidence:

- `src/smart_meter_simulator/core/telemetry_source.py`
- `src/smart_meter_simulator/meter_registry.py`
- `backend/docs/realtime-telemetry.md`

### 8. Meter Registry and Physical Bus Pinning

A meter registry maps real meter identifiers to physical buses. The simulator can
build a fleet from this registry instead of randomly generated meters.

Academic framing:

- Provides an identity layer for mapping physical meters to grid topology.
- Supports reproducible digital-twin experiments using known meter placement.
- Separates synthetic fleet generation from real-device experiments.

Implementation evidence:

- `src/smart_meter_simulator/meter_registry.py`
- `src/smart_meter_simulator/meter_generator.py`

### 9. REST API for Experiment Control

The FastAPI backend exposes endpoints for simulation status, start, stop, pause,
resume, step execution, environment changes, topology retrieval, telemetry
retrieval, grid statistics, meter CRUD operations, meter overrides, and meter
fleet size updates.

Academic framing:

- Provides programmable control for experiments and frontend visualization.
- Supports dynamic scenario configuration without restarting the backend.
- Enables external systems to read simulation telemetry and grid state.

Implementation evidence:

- `src/smart_meter_simulator/app.py`
- `src/smart_meter_simulator/routers/api_v1.py`
- `src/smart_meter_simulator/routers/simulation_v1.py`
- `src/smart_meter_simulator/routers/grid_v1.py`
- `src/smart_meter_simulator/routers/meters_v1.py`

### 10. Signed DLMS/COSEM-Style Telemetry Export

The backend can encode readings as OBIS-keyed DLMS/COSEM-style payloads and send
them to the GridTokenX Aggregator Bridge. Each meter has a deterministic Ed25519 key
used to sign telemetry for verification.

Academic framing:

- Connects simulated AMI data to secure energy-settlement infrastructure.
- Preserves bidirectional import/export energy semantics through OBIS codes.
- Provides cryptographic provenance for meter telemetry.

Implementation evidence:

- `src/smart_meter_simulator/transport/aggregator_bridge.py`
- `METER_PROTOCOL.md`

### 11. IAM Ownership Integration

The backend can onboard simulated meters through an IAM gateway and resolve
meter-owner mappings. These ownership mappings can be seeded into the Oracle
Bridge registry for attribution and settlement.

Academic framing:

- Links simulated meters to user identities.
- Supports owner-attributed energy telemetry.
- Prepares telemetry for user-level settlement workflows.

Implementation evidence:

- `src/smart_meter_simulator/transport/iam_onboarding.py`
- `src/smart_meter_simulator/transport/aggregator_bridge.py`

### 12. Observability and Validation

The backend exposes Prometheus metrics for active meter count, simulation tick
time, and Aggregator Bridge emission failures. It also includes tests for topology
loading, reference-grid replay, telemetry ingestion, frequency droop, OLTC
behavior, Aggregator Bridge signatures, and IAM onboarding.

Academic framing:

- Improves repeatability and operational monitoring.
- Provides validation coverage for core simulation and integration behavior.

Implementation evidence:

- `src/smart_meter_simulator/core/metrics.py`
- `backend/tests/test_glm_core_topology.py`
- `backend/tests/test_reference_grid_sources.py`
- `backend/tests/test_telemetry_ingestion.py`
- `backend/tests/test_freq_droop.py`
- `backend/tests/test_oltc.py`
- `backend/tests/test_aggregator_bridge_dlms.py`
- `backend/tests/test_iam_onboarding.py`

## Recommended Feature Table for Paper

| Feature | Purpose | Research Value |
| --- | --- | --- |
| GLM/reference-grid topology ingestion | Build feeder topology | Enables grid-aware AMI simulation |
| Smart-meter fleet model | Simulate heterogeneous meters | Represents consumers and prosumers |
| PV and ZIP load models | Model DER/load behavior | Studies demand and generation dynamics |
| Pandapower/DistFlow solver | Compute grid state | Evaluates voltage, losses, congestion |
| Volt-watt and droop controls | Model DER response | Supports stability and curtailment studies |
| Telemetry replay | Use measured data | Supports digital-twin experiments |
| Meter registry | Pin meters to buses | Links real devices to physical topology |
| REST API | Control experiments | Enables automation and visualization |
| DLMS/COSEM export | Standardized AMI payload | Supports settlement-grade data exchange |
| Ed25519 signing and IAM ownership | Secure attribution | Links telemetry to trusted identity |

## Suggested Paper Paragraph

The proposed backend simulator is designed as a topology-aware AMI digital twin
for prosumer distribution grids. Unlike a meter-only simulator, the system maps
smart meters to electrical feeder buses and computes the grid-level consequences
of meter injections, including voltage variation, line loading, transformer
loading, losses, and PV curtailment. The simulator supports both synthetic meter
behavior and replayed telemetry, allowing controlled experiments as well as
hybrid digital-twin operation with partial real-data coverage. In addition, the
backend exports signed DLMS/COSEM-style meter payloads for integration with
GridTokenX oracle and settlement services.

## Limitations to State Clearly

The current backend should not be described as a full state-estimation system.
It computes grid state from meter injections, but it does not yet perform
weighted-least-squares state estimation, measured-voltage reconciliation,
bad-data detection, or topology-error correction.

It is also a simulator-side DLMS/COSEM exporter, not a complete DLMS head-end.
It produces OBIS-keyed signed REST payloads for the Aggregator Bridge, but it does
not implement direct meter association, APDU parsing, HLS authentication, or
utility-grade DLMS key management.

## Useful Keywords

- Advanced Metering Infrastructure
- AMI digital twin
- Prosumer energy trading
- Distribution feeder simulation
- GridLAB-D topology
- Pandapower power-flow analysis
- Distributed photovoltaic generation
- Volt-watt control
- Frequency-watt droop
- Smart meter telemetry
- DLMS/COSEM
- OBIS code mapping
- Energy oracle
- Cryptographically signed telemetry
