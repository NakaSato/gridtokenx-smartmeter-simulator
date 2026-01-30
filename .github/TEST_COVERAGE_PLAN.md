# Test Coverage Plan

## Current Coverage Status

**Overall Coverage:** ~30–40%  
**Coverage Tool:** pytest with pytest-cov  
**Target by Phase:** See phase-specific targets below

## Phase 1: Current Trading Platform

### Current Test Files

| File | Purpose | Coverage | Status |
|---|---|---|---|
| `test_simulator.py` | Unit tests for SmartMeter, engine tick | ~40% | ✅ Basic |
| `test_integration.py` | Integration with HTTP transport | ~50% | ✅ Basic |
| `test_live_demo.py` | Real-time demo script | N/A | ✅ Demo |
| `test_step1.py` | Reading generation across time-of-day | ~60% | ✅ Demo |
| `test_step3_payload.py` | API payload formatting | ~70% | ✅ Basic |

### Missing Tests (Phase 1 Backfill)

**Priority: HIGH** - Backfill to 50% coverage before Phase 2

- [ ] **Unit Tests:**
  - [ ] `tests/test_meter.py`: SmartMeter class methods
    - [ ] `generate_reading()` edge cases (zero solar, full battery, negative grid)
    - [ ] Battery charge/discharge logic
    - [ ] Signature generation and verification
    - [ ] Weather impact on solar generation
  - [ ] `tests/test_meter_generator.py`: Meter type distribution
    - [ ] Validate type distribution percentages
    - [ ] Validate meter configuration parameters
    - [ ] Test edge cases (0 meters, 1000+ meters)
  - [ ] `tests/test_config.py`: Configuration validation
    - [ ] Environment variable loading
    - [ ] Default value fallbacks
    - [ ] Invalid configuration handling
  - [ ] `tests/test_reading_model.py`: Pydantic model validation
    - [ ] Field validation (negative energy, invalid timestamps)
    - [ ] Serialization/deserialization
    - [ ] Optional field handling

- [ ] **Integration Tests:**
  - [ ] `tests/test_transport_layer.py`: HTTP, WebSocket, Composite
    - [ ] Message delivery confirmation
    - [ ] Error handling (network failures, timeouts)
    - [ ] Batch vs. individual message delivery
  - [ ] `tests/test_engine_loop.py`: Simulation engine
    - [ ] Multi-timestep execution (100+ steps)
    - [ ] Concurrent meter orchestration
    - [ ] Weather distribution across meters
  - [ ] `tests/test_api_endpoints.py`: FastAPI endpoints
    - [ ] GET /health, /api/stats, /api/status
    - [ ] POST /api/control/start, /api/control/stop
    - [ ] WebSocket connection lifecycle

- [ ] **Performance Tests:**
  - [ ] `tests/test_performance.py`: Scalability
    - [ ] 100-meter simulation performance
    - [ ] 1000-meter simulation performance
    - [ ] Memory usage profiling
    - [ ] CPU utilization tracking

**Estimated Time:** 1–2 weeks  
**Target Coverage:** 50%+

---

## Phase 2: AMI Foundation

### New Test Files

**Priority: CRITICAL** - Must reach 60% coverage

- [ ] **Unit Tests:**
  - [ ] `tests/test_accuracy_class.py`: Accuracy class conversion
    - [ ] `calculate_std_dev()` for all accuracy classes (0.2, 0.5, 1.0, 2.0)
    - [ ] Sigma factor=2 vs. factor=3
    - [ ] Per-channel uncertainty (V: 1%, P: 2%, Q: 3%)
    - [ ] Edge cases (zero nominal, negative values)
  - [ ] `tests/test_measurement_channels.py`: Channel filtering
    - [ ] Residential meter channels (V, P, Q)
    - [ ] Commercial meter channels (V, P, Q, I)
    - [ ] Feeder meter channels (V, P, Q, I)
    - [ ] Channel exclusion validation
  - [ ] `tests/test_sign_conventions.py`: Sign convention mapping
    - [ ] Load consumption → positive load element
    - [ ] Generator injection → negative bus measurement
    - [ ] Prosumer net flow calculation
    - [ ] Bus injection vs. element measurement

- [ ] **Integration Tests:**
  - [ ] `tests/test_pandapower_adapter.py`: Pandapower integration
    - [ ] 10-meter network → valid net.measurement DataFrame
    - [ ] 50-meter network → schema compliance
    - [ ] DataFrame column validation (meas_type, element_type, element, value, std_dev, side, name)
    - [ ] Data type and unit validation
    - [ ] NaN value detection
  - [ ] `tests/test_pandapower_integration.py`: End-to-end
    - [ ] SmartMeter → Pandapower → net.measurement
    - [ ] Multiple meter types in single network
    - [ ] Accuracy class propagation to std_dev
    - [ ] Sign convention enforcement

**Estimated Time:** 1 week  
**Target Coverage:** 60%+

---

## Phase 3: State Estimation Loop

### New Test Files

**Priority: CRITICAL** - Must reach 75% coverage

- [ ] **Unit Tests:**
  - [ ] `tests/test_state_estimation.py`: SE algorithms
    - [ ] NR-WLS convergence on well-conditioned network
    - [ ] Iwamoto fallback on NR divergence
    - [ ] Current-based SE for distribution grids
    - [ ] Convergence tracking (iterations, success rate)
  - [ ] `tests/test_pseudo_measurements.py`: Observability
    - [ ] Unobservable node identification
    - [ ] Pseudo-measurement generation (P, Q)
    - [ ] High std_dev assignment (50–100%)
    - [ ] SE convergence with 30% meter coverage
  - [ ] `tests/test_bad_data_detection.py`: Outlier detection
    - [ ] Chi-squared global test
    - [ ] Normalized residuals (rN) calculation
    - [ ] Iterative sanitization (remove max rN, re-run)
    - [ ] 95%+ true positive rate for injected faults
  - [ ] `tests/test_virtual_measurements.py`: Zero injections
    - [ ] Transit node identification
    - [ ] P=0, Q=0 measurement generation
    - [ ] Low std_dev ($10^{-6}$ p.u.)
    - [ ] SE gain matrix rank validation

- [ ] **Integration Tests:**
  - [ ] `tests/test_se_ieee123.py`: IEEE 123-node benchmark
    - [ ] SE convergence >95%
    - [ ] Comparison with published results
    - [ ] Computation time tracking
  - [ ] `tests/test_timeseries_se.py`: Time-series SE loop
    - [ ] 100-timestep simulation
    - [ ] Multi-step workflow (set loads → PF → measurements → SE → controls → PF)
    - [ ] Convergence tracking across timesteps

**Estimated Time:** 2 weeks  
**Target Coverage:** 75%+

---

## Phase 4: Data Source Management

### New Test Files

**Priority: HIGH** - Must reach 80% coverage

- [ ] **Unit Tests:**
  - [ ] `tests/test_profile_management.py`: Profile generation
    - [ ] SLP generation (H0, G0 profiles)
    - [ ] Profile scaling (annual consumption → scaled profile)
    - [ ] <5% RMS error vs. target consumption
  - [ ] `tests/test_data_preprocessing.py`: Data cleaning
    - [ ] Timestamp alignment (resample to 15T)
    - [ ] Gap filling (linear interpolation, SLP substitution)
    - [ ] Unit conversion (kW → MW, kVAr → MVar)
  - [ ] `tests/test_constcontrol.py`: Vectorized controllers
    - [ ] Single ConstControl → matrix of profiles
    - [ ] 10x performance improvement vs. sequential
    - [ ] 1000-meter simulation <5 minutes for 365 days

- [ ] **Integration Tests:**
  - [ ] `tests/test_profile_loading.py`: Historical data
    - [ ] CSV/HDF5/Parquet loading
    - [ ] 1-year dataset of 10k meters <1s
    - [ ] Profile mapping to load elements
  - [ ] `tests/test_controller_integration.py`: Simulation loop
    - [ ] Reading generation matches deterministic profile <1% RMS error
    - [ ] Time-series execution with ConstControl
    - [ ] DataSource integration

**Estimated Time:** 1 week  
**Target Coverage:** 80%+

---

## Phase 5: Co-Simulation & Advanced Features

### New Test Files

**Priority: MEDIUM** - Must reach 85% coverage

- [ ] **Unit Tests:**
  - [ ] `tests/test_mosaik_adapter.py`: Mosaik integration
    - [ ] Entity mapping (SmartMeter → Mosaik entity)
    - [ ] Step synchronization <1s
  - [ ] `tests/test_fdi_attack.py`: Cyber-security
    - [ ] False Data Injection attack vector calculation
    - [ ] Stealth detection rate >99%
  - [ ] `tests/test_cim_export.py`: CIM interoperability
    - [ ] Lossless round-trip import/export
    - [ ] Mapping validation (UsagePoint ↔ SmartMeter)

**Estimated Time:** 2 weeks  
**Target Coverage:** 85%+

---

## Coverage Targets Summary

| Phase | Target Coverage | Current | Gap | Estimated Time |
|---|---|---|---|---|
| Phase 1 (Backfill) | 50% | 30–40% | +10–20% | 1–2 weeks |
| Phase 2 (Complete) | 60% | 30–40% | +20–30% | 1 week |
| Phase 3 (Complete) | 75% | 30–40% | +35–45% | 2 weeks |
| Phase 4 (Complete) | 80% | 30–40% | +40–50% | 1 week |
| Phase 5 (Complete) | 85% | 30–40% | +45–55% | 2 weeks |

**Total Estimated Time:** 7–9 weeks (distributed across phases)

---

## Test Execution Strategy

### Continuous Integration

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest --cov=src --cov-report=html --cov-report=term
      - run: pytest --cov=src --cov-fail-under=50  # Phase 1 target
```

### Local Test Execution

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_accuracy_class.py -v

# Run tests matching pattern
pytest -k "test_accuracy" -v

# Run with coverage threshold
pytest --cov=src --cov-fail-under=50
```

### Coverage Reporting

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal coverage summary
pytest --cov=src --cov-report=term-missing

# Upload to Codecov (CI)
codecov --token=$CODECOV_TOKEN
```

---

## Test Quality Guidelines

### Unit Test Standards

- **Naming:** `test_<function_name>_<scenario>` (e.g., `test_calculate_std_dev_class_1_0`)
- **Structure:** Arrange-Act-Assert pattern
- **Independence:** No shared state between tests
- **Coverage:** Aim for edge cases, not just happy paths
- **Speed:** Unit tests <100ms each

### Integration Test Standards

- **Naming:** `test_<component>_<integration_scenario>`
- **Fixtures:** Use pytest fixtures for setup/teardown
- **Isolation:** Use mocks for external dependencies
- **Speed:** Integration tests <1s each
- **Cleanup:** Always cleanup resources (files, connections)

### Performance Test Standards

- **Metrics:** Track execution time, memory, CPU
- **Baselines:** Compare against previous runs
- **Thresholds:** Define acceptable performance bounds
- **Profiling:** Use cProfile for bottleneck identification

---

## Next Steps

1. **This Week:**
   - [ ] Backfill Phase 1 missing tests to 50% coverage
   - [ ] Set up pytest-cov in CI/CD pipeline
   - [ ] Create test fixtures for sample meter configurations

2. **Phase 2 Start:**
   - [ ] Implement Phase 2 test files concurrently with features
   - [ ] Validate accuracy class tests before merging
   - [ ] Track coverage progression weekly

3. **Ongoing:**
   - [ ] Weekly coverage reports in standup
   - [ ] Quarterly test quality review
   - [ ] Update this plan as phases progress
