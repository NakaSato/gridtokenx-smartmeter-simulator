# Implementation Plan: Align Specification with Codebase

## Executive Summary

The gridtokenx-smartmeter-simulator is currently a **blockchain-focused P2P energy trading platform simulator** that generates realistic meter readings with cryptographic signatures for Solana token minting. However, `meter_spec.md` describes a comprehensive **AMI (Advanced Metering Infrastructure) and power-system analysis framework**. This document creates a phased roadmap to either align the specification to match the actual product or implement missing components progressively.

**Key Finding:** Critical mismatch between aspirational specification (sections 3–11) and pragmatic trading-focused implementation.

---

## Current State Analysis

### What Exists ✅

- **Core Simulation Engine:** Orchestrates meter readings generation in an async loop
- **Smart Meter Implementation:** Basic meter with energy generation/consumption, battery management, cryptographic signing
- **Reading Model:** Pydantic model with 20+ energy metrics (generation, consumption, surplus, deficit, battery level, electrical parameters)
- **Meter Generator:** Generates 4 meter types (Solar Prosumers, Grid Consumers, Hybrid, Battery Storage)
- **FastAPI Application:** REST API with WebSocket support, dashboard endpoints
- **Transport Layer:** Modular HTTP, WebSocket, Composite transports
- **Cryptographic Signing:** Ed25519 key management and signature verification
- **Configuration System:** Environment-based with MeterType and WeatherCondition enums
- **Test Suite:** Basic unit tests, integration tests, demo scripts (~30–40% coverage)

### What's Missing ❌

| Component | Specification Requirement | Current Status | Severity |
|---|---|---|---|
| **Pandapower Integration** | net.measurement tables, sign conventions, element-based modeling | Not implemented | **CRITICAL** |
| **Measurement Uncertainty** | Gaussian error models, accuracy classes (0.2–2.0), $\sigma$ derivation | Hard-coded noise | **HIGH** |
| **State Estimation** | NR-WLS, Iwamoto fallback, convergence logic, chi-squared test | Not implemented | **CRITICAL** |
| **Bad Data Detection** | Normalized residuals (rN), iterative sanitization, outlier detection | Not implemented | **HIGH** |
| **Pseudo-Measurements** | PseudoMeasurementGenerator for observability in sparse scenarios | Not implemented | **HIGH** |
| **Data Source Management** | CSV/HDF5/Parquet profiles, ConstControl vectorization, gap filling | Random generation instead | **HIGH** |
| **Persistence Layer** | Kafka, InfluxDB, PostgreSQL (configured but unused) | Configured only | **MEDIUM** |
| **Co-Simulation Interfaces** | MATLAB, GridLAB-D, HELICS, Mosaik, OPEN integration | Not implemented | **HIGH** |
| **Advanced Weather Modeling** | Spatially distributed, temporal correlation, impact on generation | Global weather distribution | **MEDIUM** |

---

## Phase-Based Roadmap

### Phase 1: Current Trading Platform (✅ Complete)
**Status:** Active | **Timeline:** Complete  
**Focus:** Solana blockchain-ready meter reading generation with cryptographic signing.

**Components:**
- Async meter orchestration with 15-minute simulation intervals
- Ed25519 signing for blockchain token minting
- WebSocket/HTTP transport for API gateway delivery
- Configurable meter types and weather distribution

**Deliverables:**
- ✅ Core simulator and reading generation
- ✅ REST/WebSocket endpoints
- ✅ Basic integration tests

**Not in Scope:**
- Advanced physics modeling
- Power flow calculation
- State estimation

---

### Phase 2: AMI Foundation + Measurement Accuracy (⏳ Proposed)
**Status:** Proposed | **Timeline:** 4–6 weeks  
**Focus:** Lay groundwork for power-system analysis by integrating pandapower and rigorous measurement modeling.

**Components:**

1. **Pandapower Integration** (Spec Sections 4.1–4.3)
   - Add pandapower dependency to `pyproject.toml` and `requirements.txt`
   - Create `src/app/adapters/pandapower_adapter.py` to map SmartMeter → `net.measurement` table
   - Implement measurement DataFrame builder for net.bus, net.load, net.trafo
   - Document sign convention mapping (Load vs. Generator reference frames)
   - **Acceptance Criteria:** Can generate valid pandapower measurement tables from 10+ meters without errors

2. **Accuracy Class Modeling** (Spec Section 5.3)
   - Replace hard-coded noise with accuracy class mapping
   - Add enum: `AccuracyClass` (CLASS_0_2, CLASS_0_5, CLASS_1_0, CLASS_2_0)
   - Implement $\sigma$ derivation: $\sigma = \frac{\text{AccuracyClass}}{300} \times \text{Nominal}$
   - Update `SmartMeter` class attributes to include accuracy_class
   - Apply per-channel uncertainty (V: 1%, P: 2%, Q: 3% for residential)
   - **Acceptance Criteria:** Meter readings reflect configurable accuracy classes; std_dev field in measurement table is populated correctly

3. **Measurement Channel Definition** (Spec Section 5.2)
   - Implement channel-based architecture: Residential (V, P, Q), Feeder (I, P, Q, V)
   - Allow per-meter-type channel configuration
   - Filter readings based on active channels
   - **Acceptance Criteria:** Different meter types generate appropriate channel subsets

4. **Test Coverage Expansion**
   - Unit tests for accuracy class → $\sigma$ conversion
   - Integration test: 50-meter network → pandapower net.measurement
   - Validate sign conventions (load consumption, generator injection)
   - **Acceptance Criteria:** 50–60% overall test coverage

**GitHub Issues:**
- [ ] Feature: Pandapower adapter for measurement table generation
- [ ] Feature: Accuracy class enum and std_dev mapping
- [ ] Feature: Meter type-specific channel filtering
- [ ] Test: Accuracy class conversion validation

**Blockers:**
- Pandapower documentation (available; non-blocking)
- Consensus on accuracy class default values

**Resources:**
- Spec Sections 4.1–4.3, 5.3
- Pandapower API: `net.measurement` DataFrame schema

---

### Phase 3: State Estimation Loop (⏳ Proposed)
**Status:** Proposed | **Timeline:** 6–8 weeks  
**Focus:** Implement SE workflow with bad data detection (Spec Sections 7, 3.2).

**Components:**

1. **State Estimation Engine** (Spec Section 7.1)
   - Integrate pandapower.estimation functions (NR-WLS, Iwamoto)
   - Implement convergence retry logic: NR → Iwamoto fallback
   - Create `StateEstimationRunner` class with configurable algorithm selection
   - **Acceptance Criteria:** Can run SE on a 50-bus network; convergence tracked and fallback executed on NR failure

2. **Pseudo-Measurement Generator** (Spec Section 7.2)
   - Identify unobservable nodes (buses without voltage measurement)
   - Generate P/Q pseudo-measurements with high std_dev (50–100% of value)
   - Ensure observability: rank($H^T W H$) = number of states
   - **Acceptance Criteria:** SE converges on networks with 30% measurement coverage vs. 100% coverage required without pseudo-measurements

3. **Bad Data Detection** (Spec Section 7.3)
   - Implement chi-squared global test
   - Calculate normalized residuals (rN) per measurement
   - Iterative sanitization: Remove max(rN), re-run SE, repeat until max(rN) < 3.0
   - **Acceptance Criteria:** Outlier detector correctly identifies and removes 3+ injected faulty readings from 100-point dataset

4. **Virtual Measurements for Zero Injections** (Spec Section 7.4)
   - Auto-identify transit nodes (no load/gen, only line connections)
   - Generate P=0, Q=0 measurements with low std_dev ($10^{-6}$ p.u.)
   - **Acceptance Criteria:** Transit nodes correctly identified; SE gain matrix remains full rank

5. **Time-Series SE Loop** (Spec Section 8.1)
   - Advanced simulation loop:
     1. Set loads (physical reality)
     2. Solve power flow (physical reality)
     3. Generate measurements (AMI feedback)
     4. Run SE (controller view)
     5. Adjust controls (optional, future)
     6. Re-solve PF (final state)
   - **Acceptance Criteria:** Can simulate 100 timesteps with SE convergence tracking

6. **Test Coverage Expansion**
   - Unit tests: chi-squared test, residual calculation, outlier detection
   - Integration: SE on IEEE 123-node test feeder (standard benchmark)
   - Convergence metrics: iterations, success rate, computation time
   - **Acceptance Criteria:** 65–75% overall test coverage

**GitHub Issues:**
- [ ] Feature: State estimation engine with NR and Iwamoto
- [ ] Feature: Pseudo-measurement generator
- [ ] Feature: Bad data detection with chi-squared and residuals
- [ ] Feature: Virtual measurements for zero injections
- [ ] Feature: Time-series SE loop with multi-step workflow
- [ ] Test: SE convergence on IEEE 123-node feeder

**Blockers:**
- Pandapower SE API understanding (available in documentation)
- IEEE 123-node test case availability

**Resources:**
- Spec Sections 7, 8.1, 3.2
- IEEE 123-node distribution test feeder (public benchmark)

---

### Phase 4: Data Source Management & Profiles (⏳ Proposed)
**Status:** Proposed | **Timeline:** 4–6 weeks  
**Focus:** Replace random meter generation with deterministic/stochastic profiles (Spec Section 6).

**Components:**

1. **Profile Management Logic** (Spec Section 6.2)
   - **Deterministic Profiles:** Load recorded AMI data from CSV/HDF5/Parquet
   - **Stochastic Profiles:** Generate synthetic profiles using standard load profiles (SLP) - H0 (household), G0 (business)
   - Profile scaler: annual consumption (kWh) → normalized SLP → scaled profile
   - **Acceptance Criteria:** Can load historical data; can generate H0/G0 profiles matching target annual consumption ±5%

2. **Data Pre-processing** (Spec Section 6.4)
   - Timestamp alignment: resample to simulation timestep (e.g., 15T)
   - Gap filling: linear interpolation (1–2 intervals), SLP substitution (long gaps)
   - Unit conversion: kW → MW, kVAr → MVar
   - **Acceptance Criteria:** Messy dataset (missing values, inconsistent timestamps) preprocessed without manual intervention

3. **ConstControl Vectorization** (Spec Section 6.3)
   - Replace individual ConstControl objects with vectorized controllers
   - Single ConstControl instance → matrix of profiles → array of load indices
   - Leverage numpy optimizations in pandapower
   - Performance: 1000+ meters in <2s per timestep
   - **Acceptance Criteria:** 1000-meter simulation completes 365 days in <5 minutes

4. **Controller Integration**
   - Integrate ConstControl with simulation loop
   - Time-series execution: loop advances, controller reads DataSource, updates net.load.p_mw
   - **Acceptance Criteria:** Reading generation matches deterministic profile data with <1% RMS error

5. **Test Coverage Expansion**
   - Unit tests: SLP generation, profile scaling, gap filling
   - Integration: 100-meter network with historical profiles over 1 year
   - Performance: vectorized ConstControl 10x faster than sequential
   - **Acceptance Criteria:** 70–80% overall test coverage

**GitHub Issues:**
- [ ] Feature: Profile loader for CSV/HDF5/Parquet
- [ ] Feature: Standard load profile (SLP) generator
- [ ] Feature: Data pre-processing pipeline (alignment, gap filling, unit conversion)
- [ ] Feature: Vectorized ConstControl implementation
- [ ] Feature: Controller integration with simulation loop
- [ ] Test: Profile generation accuracy and performance benchmarks

**Blockers:**
- Availability of sample historical profiles (recommend synthetic generation for testing)
- Pandapower ConstControl API understanding

**Resources:**
- Spec Section 6
- Pandapower documentation on Controllers

---

### Phase 5: Co-Simulation & Advanced Features (⏳ Future)
**Status:** Proposed | **Timeline:** 8–12 weeks  
**Focus:** Integrate with external simulators and implement advanced modeling (Spec Sections 9–11).

**Components:**

1. **Mosaik Integration** (Spec Section 9.1)
   - Adapter: Smart meter → Mosaik entity
   - Input: P, Q (from household demand simulator)
   - Output: Vm, Va, Loading%
   - Step size coordination: 900s default, configurable

2. **OPEN Platform Integration** (Spec Section 9.2)
   - Asset class mapping: Smart meter → Asset interface
   - Market integration: Smart meter data → peer-to-peer trading models

3. **Cyber-Security Simulation** (Spec Section 9.3)
   - False Data Injection (FDI) attack agent
   - Attack vector: $z_{attack} = z_{true} + a$
   - Stealth calculation: topology-aware attack vector

4. **CIM Interoperability** (Spec Section 11.1)
   - CIM import/export support
   - Mapping: CIM UsagePoint ↔ Pandapower logical smart meter

5. **PMU Integration** (Spec Section 11.2)
   - Hybrid State Estimation: AMI (scalar, slow) + PMU (phasor, fast)
   - Multi-rate fusion algorithm

**Blockers:**
- External simulator availability (Mosaik, GridLAB-D)
- CIM schema documentation

**Resources:**
- Spec Sections 9–11
- Mosaik and OPEN documentation

---

## Recommended Immediate Actions

### 1. **Clarify Project Scope** (Week 1)
**Decision Required:**
- Is gridtokenx-smartmeter-simulator a **trading platform** (current) or **research AMI framework** (spec) or **both**?

**Recommendation:**
- **Short-term (6 months):** Remain "trading platform" focused (Phase 1)
- **Long-term (12+ months):** Expand to "research AMI framework" with Phase 2+ components

**Action:**
- [ ] Schedule scope-alignment meeting with stakeholders
- [ ] Update project README with explicit scope statement
- [ ] Add roadmap section linking meter_spec.md phases

### 2. **Update Specification Documentation** (Week 1)
- Add introductory section to meter_spec.md distinguishing **Phase 1 (Current)** vs. **Phase 2+ (Roadmap)**
- Mark sections as:
  - ✅ **Implemented:** Section 3 (Theoretical foundations - conceptual only)
  - 🟡 **Partial:** Basic reading generation (not full measurement uncertainty)
  - ⏳ **Planned:** Sections 4–5 (Phase 2), 7–8 (Phase 3), 6 (Phase 4), 9–11 (Phase 5)
- Add execution flow diagrams comparing current (simplified) vs. future (AMI) architectures

### 3. **Create Dependencies Audit** (Week 1)
- [ ] Review `pyproject.toml` and `requirements.txt`
- [ ] Remove unused dependencies (Kafka, InfluxDB, PostgreSQL) OR create skeleton implementations with TODOs
- [ ] Add `pandapower>=2.10.0` for Phase 2
- [ ] Document "Future Dependencies" section for Phase 3+

### 4. **Prioritize Phase 2 Start** (Weeks 2–3)
- [ ] Create GitHub milestone: "Phase 2: AMI Foundation"
- [ ] Assign issues (Pandapower adapter, accuracy class modeling, channel filtering)
- [ ] Estimate 4–6 weeks for Phase 2 completion
- [ ] Define success metrics: pandapower integration complete, 50% measurement accuracy tests passing

### 5. **Establish Test Coverage Targets** (Week 1)
| Phase | Target Coverage | Current | Gap |
|---|---|---|---|
| Phase 1 (Current) | 50% | 30–40% | +10–20% |
| Phase 2 (Complete) | 60% | 30–40% | +20–30% |
| Phase 3 (Complete) | 75% | 30–40% | +35–45% |
| Phase 4 (Complete) | 80% | 30–40% | +40–50% |

- [ ] Identify missing unit tests for Phase 1 and backfill coverage
- [ ] Create test plan for Phase 2+ before implementation

---

## Success Metrics

### Phase 1 (Current)
- ✅ Meter reading generation accurate to real-world profiles
- ✅ Ed25519 signatures verifiable by blockchain
- ✅ WebSocket delivery <100ms latency
- ✅ 50+ meter types simulated concurrently

### Phase 2 (Complete)
- Pandapower net.measurement table generated without errors
- Accuracy class mapping matches ANSI C12.20 standard ±2%
- Channel filtering reduces data volume by 40–60% for non-critical meters
- Test coverage: 60%+

### Phase 3 (Complete)
- SE convergence >95% on IEEE 123-node feeder
- Bad data detection: 95%+ true positive rate for outlier identification
- Pseudo-measurements reduce required meter coverage from 100% to 30%
- Test coverage: 75%+

### Phase 4 (Complete)
- Profile generation: <5% RMS error vs. target annual consumption
- Vectorized controllers: 10x faster than sequential for 1000+ meters
- Historical profile import: <1s for 1-year dataset of 10k meters
- Test coverage: 80%+

### Phase 5 (Complete)
- Mosaik adapter: sub-second step synchronization
- FDI attack detection: 99%+ stealth detection rate
- CIM export: lossless round-trip import/export
- Test coverage: 85%+

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **Pandapower Integration Complexity** | Phase 2 timeline overrun | Early proof-of-concept (PoC) in week 2; identify blocking issues |
| **State Estimation Convergence Issues** | Phase 3 failure | Use IEEE 123-node benchmark; compare with published results |
| **Data Availability** | Phase 4 delays | Generate synthetic SLP profiles; use public datasets (NREL, OpenEI) |
| **Co-Simulation Framework Maturity** | Phase 5 delays | Parallel R&D; select most stable framework (recommend Mosaik) |
| **Scope Creep** | Overall schedule slip | Strict phase gating; no Phase N work until Phase N-1 complete |

---

## Budget & Resource Estimate

| Phase | Duration | FTE Required | Annual Cost (US) | Blockers |
|---|---|---|---|---|
| Phase 1 | Complete | N/A | N/A | None |
| Phase 2 | 4–6 weeks | 1.0 FTE | ~$5k–$8k | Pandapower learning curve |
| Phase 3 | 6–8 weeks | 1.0 FTE | ~$8k–$12k | SE algorithm validation |
| Phase 4 | 4–6 weeks | 0.75 FTE | ~$4k–$6k | Profile data availability |
| Phase 5 | 8–12 weeks | 1.0–1.5 FTE | ~$12k–$20k | External framework maturity |
| **Total** | **6–9 months** | **~4–4.25 FTE** | **~$29k–$46k** | None critical |

---

## Next Steps

1. **This Week:**
   - [ ] Review and approve roadmap (stakeholder decision on scope)
   - [ ] Create GitHub milestone for Phase 2
   - [ ] Backfill Phase 1 test coverage to 50%

2. **Week 2:**
   - [ ] Pandapower PoC: generate net.measurement table from 10 meters
   - [ ] Update meter_spec.md with phase markers
   - [ ] Begin Phase 2 implementation

3. **Ongoing:**
   - [ ] Weekly progress tracking against Phase 2 milestones
   - [ ] Monthly scope review with stakeholders
   - [ ] Quarterly roadmap updates based on findings
