# Migration Guide: Restructuring to Modular Project Layout

This guide documents the changes made to restructure the Smart Meter Simulator from a flat layout to a modular, scalable Python package structure.

## Overview of Changes

The project has been restructured to follow Python packaging best practices with a `src/` layout. This improves maintainability, testing, and distribution.

### Old Structure (Flat)
```
smart-meter-simulator/
├── app.py
├── config.py
├── meter_generator.py
├── services.py
├── simulator.py
├── statistics.py
├── utils.py
├── websocket_server.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── data/
├── docs/
├── static/
└── templates/
```

### New Structure (Modular)
```
smart-meter-simulator/
├── src/
│   └── smart_meter_simulator/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── meter_generator.py
│       ├── services.py
│       ├── simulator.py
│       ├── statistics.py
│       ├── utils.py
│       └── websocket_server.py
├── tests/
├── scripts/
│   └── run.py
├── templates/
│   ├── meter_template.py
│   ├── config_template.yaml
│   └── report_template.md
├── pyproject.toml
├── requirements.txt
├── README.md
├── data/
├── docs/
└── static/
```

## File Movements

| Old Path | New Path | Notes |
|----------|----------|-------|
| `app.py` | `src/smart_meter_simulator/app.py` | Main FastAPI application |
| `config.py` | `src/smart_meter_simulator/config.py` | Configuration and enums |
| `meter_generator.py` | `src/smart_meter_simulator/meter_generator.py` | Meter generation logic |
| `services.py` | `src/smart_meter_simulator/services.py` | External service connectors |
| `simulator.py` | `src/smart_meter_simulator/simulator.py` | Core simulation engine |
| `statistics.py` | `src/smart_meter_simulator/statistics.py` | Statistics and analytics |
| `utils.py` | `src/smart_meter_simulator/utils.py` | Utility functions and dataclasses |
| `websocket_server.py` | `src/smart_meter_simulator/websocket_server.py` | WebSocket server implementation |

## Import Updates

All relative imports have been updated to absolute imports using the `smart_meter_simulator` package:

### Before
```python
from simulator import SmartMeterSimulator
from config import MeterType
from utils import EnergyReading
```

### After
```python
from smart_meter_simulator.simulator import SmartMeterSimulator
from smart_meter_simulator.config import MeterType
from smart_meter_simulator.utils import EnergyReading
```

## Running the Application

### Old Way
```bash
python app.py
```

### New Way
```bash
# From project root
python scripts/run.py

# Or using uvicorn directly
uvicorn smart_meter_simulator.app:app --host 0.0.0.0 --port 8000 --reload
```

## Build and Installation

The project now uses proper Python packaging:

### Install in Development Mode
```bash
pip install -e .
```

### Build Distribution
```bash
python -m build
```

### Install from Local Build
```bash
pip install dist/smart_meter_simulator-0.1.0.tar.gz
```

## Testing

Tests should be placed in the `tests/` directory. Example structure:
```
tests/
├── __init__.py
├── test_simulator.py
├── test_meter_generator.py
└── test_app.py
```

Run tests with:
```bash
pytest
```

## Configuration Changes

- `pyproject.toml`: Updated build configuration for `src/` layout
- Package name: `smart_meter_simulator`
- Entry points: Can be added for console scripts if needed

## Benefits of New Structure

1. **Clean Separation**: Code, tests, docs, and assets are clearly separated
2. **Package Safety**: Prevents accidental imports of local modules
3. **Scalability**: Easy to add new modules and subpackages
4. **Testing**: Dedicated test directory with proper isolation
5. **Distribution**: Proper Python package that can be installed via pip
6. **IDE Support**: Better autocomplete and refactoring support

## Troubleshooting

### Import Errors
If you encounter import errors, ensure you're running from the project root and the package is properly installed:

```bash
pip install -e .
```

### Module Not Found
The `smart_meter_simulator` package must be importable. Check your `PYTHONPATH` or ensure the `src/` directory is included.

### Running Tests
Make sure pytest is configured to find the package:

```bash
# In pyproject.toml or pytest.ini
[tool:pytest]
pythonpath = ["src"]
```

## Next Steps

1. Add comprehensive unit tests in `tests/`
2. Update documentation to reflect new structure
3. Add CI/CD configuration (GitHub Actions, etc.)
4. Consider adding type hints and linting configuration
5. Update README.md with new installation and usage instructions

## Rollback (if needed)

To revert to the old structure:

1. Move files back from `src/smart_meter_simulator/` to root
2. Revert import statements to relative imports
3. Update `pyproject.toml` packages back to `["."]`
4. Remove `src/` and `tests/` directories
5. Update run commands back to `python app.py`