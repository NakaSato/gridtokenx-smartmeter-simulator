# Phase 2: AMI Foundation - GitHub Issues Template

This file contains issue templates for Phase 2 implementation. Copy each section to create individual GitHub issues.

---

## Issue 1: Pandapower Adapter for Measurement Table Generation

**Labels:** `enhancement`, `phase-2`, `pandapower`  
**Milestone:** Phase 2: AMI Foundation  
**Estimated Time:** 2 weeks

### Description

Implement a Pandapower adapter to convert SmartMeter instances into valid `net.measurement` DataFrames compatible with pandapower's AMI modeling framework.

### Acceptance Criteria

- [ ] Can generate valid pandapower `net.measurement` tables from 10+ meters without errors
- [ ] Measurement DataFrame includes all required columns: `meas_type`, `element_type`, `element`, `value`, `std_dev`, `side`, `name`
- [ ] Sign convention mapping correctly handles Load vs. Generator reference frames
- [ ] Element-based modeling correctly maps residential meters to load elements
- [ ] Unit tests validate DataFrame schema compliance
- [ ] Integration test: 50-meter network → pandapower net.measurement

### Tasks

- [ ] Add `pandapower>=2.14.0` dependency to `pyproject.toml` and `requirements.txt`
- [ ] Create `src/app/adapters/` directory
- [ ] Create `src/app/adapters/__init__.py`
- [ ] Implement `src/app/adapters/pandapower_adapter.py` with `MeasurementTableBuilder` class
- [ ] Implement mapping methods:
  - [ ] `_map_voltage_measurement(meter, bus_index)` → (meas_type='v', element_type='bus')
  - [ ] `_map_active_power(meter, load_index)` → (meas_type='p', element_type='load')
  - [ ] `_map_reactive_power(meter, load_index)` → (meas_type='q', element_type='load')
- [ ] Handle sign conventions: load consumption (positive), generation (negative bus injection)
- [ ] Create unit tests in `tests/test_pandapower_adapter.py`
- [ ] Document sign convention mapping in docstrings

### References

- Spec: [meter_spec.md](../meter_spec.md) Sections 4.1–4.3
- Pandapower docs: `net.measurement` DataFrame schema

---

## Issue 2: Accuracy Class Enum and Std Dev Mapping

**Labels:** `enhancement`, `phase-2`, `measurement-accuracy`  
**Milestone:** Phase 2: AMI Foundation  
**Estimated Time:** 1 week

### Description

Replace hard-coded noise injection with accuracy class-based standard deviation derivation following ANSI C12.20 standard.

### Acceptance Criteria

- [ ] Meter readings reflect configurable accuracy classes
- [ ] `std_dev` field in measurement table is populated correctly
- [ ] Accuracy class mapping matches ANSI C12.20 standard ±2%
- [ ] Per-channel uncertainty applied (V: 1%, P: 2%, Q: 3% for residential)
- [ ] Unit tests validate σ derivation formula

### Tasks

- [ ] Create `AccuracyClass` enum in `src/app/config/config.py`:
  - [ ] `CLASS_0_2 = 0.002`
  - [ ] `CLASS_0_5 = 0.005`
  - [ ] `CLASS_1_0 = 0.01`
  - [ ] `CLASS_2_0 = 0.02`
- [ ] Update `SmartMeter` class in `src/app/core/meter.py`:
  - [ ] Add `accuracy_class: AccuracyClass` attribute
  - [ ] Add `sigma_factor: int = 3` attribute (configurable 2 or 3)
- [ ] Implement σ derivation method:
  ```python
  def calculate_std_dev(self, nominal_value: float) -> float:
      """
      Calculate standard deviation from accuracy class.
      σ = (AccuracyClass / 300) × NominalValue  (for sigma_factor=3)
      """
      return (self.accuracy_class.value / (100 * self.sigma_factor)) * nominal_value
  ```
- [ ] Apply per-channel uncertainty in `generate_reading()`:
  - [ ] Voltage: `σ_v = calculate_std_dev(1.0)` (typically 1%)
  - [ ] Active Power: `σ_p = calculate_std_dev(P_nominal)` (typically 2%)
  - [ ] Reactive Power: `σ_q = calculate_std_dev(Q_nominal)` (typically 3%)
- [ ] Update `meter_generator.py` to assign accuracy classes based on meter type:
  - [ ] RESIDENTIAL: CLASS_1_0 or CLASS_2_0
  - [ ] COMMERCIAL: CLASS_0_5 or CLASS_1_0
  - [ ] FEEDER: CLASS_0_2 or CLASS_0_5
- [ ] Create unit tests in `tests/test_accuracy_class.py`
- [ ] Integration test: validate std_dev values in pandapower measurement table

### References

- Spec: [meter_spec.md](../meter_spec.md) Section 5.3
- ANSI C12.20 standard (reference document)

---

## Issue 3: Meter Type-Specific Channel Filtering

**Labels:** `enhancement`, `phase-2`, `measurement-channels`  
**Milestone:** Phase 2: AMI Foundation  
**Estimated Time:** 1 week

### Description

Implement channel-based architecture where different meter types generate appropriate measurement subsets (e.g., Residential: V, P, Q; Feeder: I, P, Q, V).

### Acceptance Criteria

- [ ] Different meter types generate appropriate channel subsets
- [ ] Reading generation only includes active channels
- [ ] Channel filtering reduces data volume by 40–60% for non-critical meters
- [ ] Unit tests validate channel filtering per meter type

### Tasks

- [ ] Create `MeasurementChannel` enum in `src/app/models/reading.py`:
  - [ ] `VOLTAGE = "v"`
  - [ ] `ACTIVE_POWER = "p"`
  - [ ] `REACTIVE_POWER = "q"`
  - [ ] `CURRENT = "i"`
  - [ ] `CURRENT_ANGLE = "ia"`
  - [ ] `VOLTAGE_ANGLE = "va"`
- [ ] Define channel sets per meter type in `src/app/config/config.py`:
  ```python
  METER_TYPE_CHANNELS = {
      MeterType.RESIDENTIAL: {VOLTAGE, ACTIVE_POWER, REACTIVE_POWER},
      MeterType.COMMERCIAL: {VOLTAGE, ACTIVE_POWER, REACTIVE_POWER, CURRENT},
      MeterType.FEEDER: {VOLTAGE, ACTIVE_POWER, REACTIVE_POWER, CURRENT},
      MeterType.SUBSTATION: {VOLTAGE, ACTIVE_POWER, REACTIVE_POWER, CURRENT, CURRENT_ANGLE, VOLTAGE_ANGLE}
  }
  ```
- [ ] Update `SmartMeter` class:
  - [ ] Add `channels: List[MeasurementChannel]` attribute
  - [ ] Filter `generate_reading()` to only include active channels
- [ ] Update `meter_generator.py`:
  - [ ] Assign channels based on meter type
  - [ ] Allow override for custom channel configurations
- [ ] Update `EnergyReading` Pydantic model:
  - [ ] Make all electrical fields Optional
  - [ ] Add channel metadata field
- [ ] Create unit tests in `tests/test_measurement_channels.py`
- [ ] Integration test: verify residential meter excludes current measurements

### References

- Spec: [meter_spec.md](../meter_spec.md) Section 5.2

---

## Issue 4: Accuracy Class Conversion Validation Tests

**Labels:** `testing`, `phase-2`, `measurement-accuracy`  
**Milestone:** Phase 2: AMI Foundation  
**Estimated Time:** 3 days

### Description

Comprehensive test suite validating accuracy class to standard deviation conversion and sign convention handling.

### Acceptance Criteria

- [ ] Test coverage for accuracy class module: >90%
- [ ] Validate σ derivation matches specification formula
- [ ] Validate sign conventions for load consumption and generator injection
- [ ] Integration test: 50-meter network → pandapower net.measurement

### Tasks

- [ ] Create `tests/test_accuracy_class.py`:
  - [ ] Test `calculate_std_dev()` for all accuracy classes
  - [ ] Test σ_factor=2 vs. σ_factor=3
  - [ ] Test per-channel uncertainty (V: 1%, P: 2%, Q: 3%)
  - [ ] Test edge cases (zero nominal value, negative values)
- [ ] Create `tests/test_sign_conventions.py`:
  - [ ] Test load consumption → positive value in load element
  - [ ] Test generator injection → negative value in bus measurement
  - [ ] Test prosumer net flow calculation
- [ ] Create `tests/test_pandapower_integration.py`:
  - [ ] Test 50-meter network → valid net.measurement DataFrame
  - [ ] Validate all required columns present
  - [ ] Validate data types and units
  - [ ] Validate no NaN values in critical columns
- [ ] Add test fixtures for sample meter configurations
- [ ] Document test scenarios in test docstrings

### References

- Spec: [meter_spec.md](../meter_spec.md) Sections 4.3, 5.3

---

## Phase 2 Milestone Summary

**Estimated Duration:** 4–6 weeks  
**Total Issues:** 4  
**Success Metrics:**
- [ ] Pandapower integration complete
- [ ] Accuracy class mapping ±2% of ANSI C12.20 standard
- [ ] Test coverage: 50–60%
- [ ] Can generate valid pandapower measurement tables from 50+ meters

**Blockers:**
- Pandapower documentation (available; non-blocking)
- Consensus on accuracy class default values (decision needed)

**Resources:**
- [meter_spec.md](../meter_spec.md) Sections 4.1–4.3, 5.2–5.3
- Pandapower documentation: https://pandapower.readthedocs.io/
- ANSI C12.20 standard

**Next Steps After Phase 2:**
- Begin Phase 3: State Estimation Loop implementation
- Implement pseudo-measurement generation
- Integrate chi-squared test and bad data detection
