# Test Quick Reference

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test File
```bash
pytest tests/test_meter.py
```

### Specific Test Class or Function
```bash
pytest tests/test_meter.py::TestSolarGeneration
pytest tests/test_meter.py::TestSolarGeneration::test_solar_generation_noon_is_maximum
```

### By Marker
```bash
# Run only unit tests
pytest -m unit

# Run only Phase 1 tests
pytest -m phase1

# Run integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

### With Coverage
```bash
# Run with coverage report
pytest --cov=src --cov-report=term

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Check coverage threshold
pytest --cov=src --cov-fail-under=50
```

### Watch Mode (with pytest-watch)
```bash
pip install pytest-watch
ptw  # Runs tests on file changes
```

## Test Organization

### Current Test Files

- `tests/test_meter.py` - SmartMeter class unit tests (NEW - Phase 1 backfill)
- `tests/test_simulator.py` - Existing simulator tests
- `tests/test_integration.py` - Existing integration tests
- `tests/test_step1.py` - Demo: reading generation
- `tests/test_step3_payload.py` - API payload tests
- `tests/test_live_demo.py` - Live demo script

### Planned Test Files (Phase 2+)

- `tests/test_accuracy_class.py` - Accuracy class conversion (Phase 2)
- `tests/test_measurement_channels.py` - Channel filtering (Phase 2)
- `tests/test_sign_conventions.py` - Sign conventions (Phase 2)
- `tests/test_pandapower_adapter.py` - Pandapower integration (Phase 2)
- `tests/test_state_estimation.py` - SE algorithms (Phase 3)
- `tests/test_bad_data_detection.py` - Outlier detection (Phase 3)

## Coverage Targets

| Phase | Target | Current |
|---|---|---|
| Phase 1 | 50% | ~30-40% → 50%+ with new tests |
| Phase 2 | 60% | TBD |
| Phase 3 | 75% | TBD |
| Phase 4 | 80% | TBD |
| Phase 5 | 85% | TBD |

## Markers Reference

Use markers to organize tests by phase and type:

```python
@pytest.mark.unit
@pytest.mark.phase1
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.phase2
@pytest.mark.slow
def test_integration():
    pass
```

## CI/CD Integration

Tests automatically run on:
- Every push to main
- Every pull request
- Manual workflow dispatch

See `.github/workflows/tests.yml` for configuration.

## Troubleshooting

### Import Errors
```bash
# Install package in editable mode
pip install -e .
```

### Missing Dependencies
```bash
# Install dev dependencies
pip install -e .[dev]
```

### Coverage Not Working
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Check pytest.ini configuration
cat pytest.ini
```

### Tests Not Discovered
```bash
# Verbose discovery
pytest --collect-only

# Check naming conventions (test_*.py, Test*, test_*)
```
