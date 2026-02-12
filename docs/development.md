# Development Guide

This guide covers development workflows, testing, and extending the Smart Meter Simulator.

## Development Setup

### Prerequisites

- Python 3.11+
- pip or poetry
- Docker (optional, for dependencies)
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd gridtokenx-smartmeter-simulator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Or with poetry
poetry install
```

### Development Dependencies

The `[dev]` extras include:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "isort>=5.0",
    "mypy>=1.0",
    "flake8>=6.0",
    "pandapower>=2.14.0",
]
```

---

## Project Structure

```
src/smart_meter_simulator/
├── __init__.py
├── app.py                 # FastAPI application entry point
├── cli.py                 # Command-line interface
├── meter_generator.py     # Meter generation logic
├── config/                # Configuration management
│   └── __init__.py        # SimulatorConfig, enums
├── core/                  # Core simulation components
│   ├── engine.py          # Simulation engine
│   ├── meter.py           # Smart meter implementation
│   ├── analytics.py       # Grid health analytics
│   ├── attacker.py        # FDI attack simulation
│   ├── data_source.py     # Profile data management
│   ├── db.py              # Database manager
│   ├── adr.py             # Automated Demand Response
│   ├── frequency.py       # Frequency regulation
│   ├── island.py          # Islanding detection
│   ├── market.py          # Market integration
│   ├── optimizer.py       # Optimization algorithms
│   ├── settlement.py      # Settlement engine
│   └── vpp.py             # Virtual Power Plant
├── models/                # Pydantic data models
│   └── reading.py         # Energy reading model
├── transport/             # Transport layer implementations
│   ├── base.py            # Abstract base class
│   ├── composite.py       # Multi-transport aggregator
│   ├── http.py            # HTTP transport
│   ├── kafka.py           # Kafka transport
│   ├── websocket.py       # WebSocket transport
│   └── influxdb.py        # InfluxDB transport
├── adapters/              # External system adapters
│   ├── pandapower_adapter.py  # Grid modeling
│   ├── state_estimator.py     # State estimation
│   ├── topology_builder.py    # Network topology
│   ├── cim_adapter.py         # CIM integration
│   ├── mosaik_adapter.py      # Mosaik adapter
│   └── mosaik_shim.py         # Co-simulation
└── utils/                 # Utility functions
    ├── crypto.py          # Cryptographic operations
    └── zk_worker.py       # Zero-knowledge proof worker
```

---

## Running the Application

### Development Server

```bash
# With auto-reload
uvicorn smart_meter_simulator.app:app --reload --port 8000

# Or using the module
python -m uvicorn smart_meter_simulator.app:app --reload --port 8000
```

### Docker

```bash
# Build image
docker build -t gridtokenx/simulator .

# Run container
docker run -p 8000:8000 --env-file .env gridtokenx/simulator

# With docker-compose
docker-compose up -d
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/smart_meter_simulator --cov-report=html

# Run specific test file
pytest tests/test_meter.py

# Run specific test
pytest tests/test_meter.py::test_generate_reading

# Run with verbose output
pytest -v

# Run async tests
pytest -v tests/test_integration.py
```

### Test Organization

```
tests/
├── conftest.py                  # Pytest fixtures
├── README.md                    # Test documentation
├── test_accuracy_class.py       # Accuracy class tests
├── test_api_endpoints.py        # API endpoint tests
├── test_composite_transport.py  # Transport tests
├── test_http_transport.py       # HTTP transport tests
├── test_integration.py          # Integration tests
├── test_meter.py                # Meter unit tests
├── test_pandapower_adapter.py   # Adapter tests
├── test_pandapower_integration.py # Pandapower integration
├── test_phase2_integration.py   # Phase 2 feature tests
├── test_phase3_advanced.py      # Phase 3 feature tests
├── test_phase3_digital_twin.py  # Digital twin tests
├── test_phase4_playback.py      # Playback mode tests
├── test_phase5_analytics.py     # Analytics tests
└── ...
```

### Writing Tests

```python
# tests/test_example.py
import pytest
from datetime import datetime, timezone
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.models.reading import EnergyReading

@pytest.fixture
def sample_meter_config():
    return {
        "meter_id": "TEST_001",
        "meter_type": "Solar_Prosumer",
        "location": "Zone_1_Building_1",
        "user_type": "residential",
        "has_solar": True,
        "has_battery": False,
        "solar_capacity": 10.0,
    }

@pytest.fixture
def smart_meter(sample_meter_config):
    return SmartMeter(sample_meter_config)

def test_meter_initialization(smart_meter):
    assert smart_meter.meter_id == "TEST_001"
    assert smart_meter.config["has_solar"] is True

def test_generate_reading(smart_meter):
    timestamp = datetime.now(timezone.utc)
    reading = smart_meter.generate_reading(timestamp)
    
    assert isinstance(reading, EnergyReading)
    assert reading.meter_id == "TEST_001"
    assert reading.energy_generated >= 0
    assert reading.energy_consumed >= 0

@pytest.mark.asyncio
async def test_async_operation():
    # Test async code
    result = await some_async_function()
    assert result is not None
```

### Test Fixtures

Common fixtures in `conftest.py`:

```python
# tests/conftest.py
import pytest
import asyncio
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.transport.websocket import WebSocketManager, WebSocketTransport

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def websocket_manager():
    return WebSocketManager()

@pytest.fixture
def sample_meters():
    configs = [
        {"meter_id": f"M{i:03d}", "meter_type": "Residential", ...}
        for i in range(5)
    ]
    return [SmartMeter(c) for c in configs]
```

---

## Code Style

### Formatting

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check with flake8
flake8 src/ tests/
```

### Type Checking

```bash
# Run mypy
mypy src/smart_meter_simulator
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

```bash
# Install pre-commit
pip install pre-commit
pre-commit install
```

---

## Extending the Simulator

### Adding a New Transport

1. **Create transport class**:

```python
# src/smart_meter_simulator/transport/mqtt.py
from typing import Dict, Any, List
from .base import TransportLayer
from ..models.reading import EnergyReading

class MQTTTransport(TransportLayer):
    def __init__(self, broker: str, port: int, topic: str):
        self.broker = broker
        self.port = port
        self.topic = topic
        self._connected = False
        self.client = None
        
    async def connect(self) -> bool:
        import paho.mqtt.client as mqtt
        self.client = mqtt.Client()
        self.client.connect(self.broker, self.port)
        self._connected = True
        return True
        
    async def disconnect(self) -> bool:
        if self.client:
            self.client.disconnect()
        self._connected = False
        return True
        
    async def send_reading(self, reading: EnergyReading) -> bool:
        if not self._connected:
            return False
        payload = reading.model_dump_json()
        self.client.publish(self.topic, payload)
        return True
        
    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        for reading in readings:
            await self.send_reading(reading)
        return True
        
    async def send_grid_status(self, status: Dict[str, Any]) -> bool:
        import json
        self.client.publish(f"{self.topic}/grid", json.dumps(status))
        return True
        
    def is_connected(self) -> bool:
        return self._connected
```

2. **Register in app.py**:

```python
# In lifespan function
if config.MQTT_BROKER:
    mqtt_transport = MQTTTransport(
        broker=config.MQTT_BROKER,
        port=config.MQTT_PORT,
        topic=config.MQTT_TOPIC
    )
    transports.append(mqtt_transport)
```

3. **Add configuration**:

```python
# In config/__init__.py
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'meter_readings')
```

4. **Add tests**:

```python
# tests/test_mqtt_transport.py
import pytest
from smart_meter_simulator.transport.mqtt import MQTTTransport

@pytest.mark.asyncio
async def test_mqtt_transport():
    transport = MQTTTransport("localhost", 1883, "test")
    # Test implementation
```

### Adding a New Meter Type

1. **Add to MeterType enum**:

```python
# config/__init__.py
class MeterType(Enum):
    # ... existing types
    INDUSTRIAL = "Industrial"
```

2. **Configure accuracy and channels**:

```python
# config/__init__.py
METER_TYPE_CHANNELS = {
    # ... existing
    MeterType.INDUSTRIAL: {"v", "p", "q", "i", "ia", "va"},
}
```

3. **Update meter logic** (if needed):

```python
# core/meter.py
def _calculate_consumption(self, timestamp):
    if self.config['meter_type'] == 'Industrial':
        # Industrial-specific consumption logic
        return self._calculate_industrial_consumption(timestamp)
    # ... existing logic
```

### Adding a New API Endpoint

```python
# In app.py

@app.get("/api/custom/endpoint")
async def custom_endpoint():
    """Custom endpoint description."""
    if not engine:
        return {"error": "Simulator not initialized"}
    
    # Your logic here
    result = process_something(engine.meters)
    
    return {
        "success": True,
        "data": result
    }

@app.post("/api/custom/action")
async def custom_action(request: dict):
    """Custom action endpoint."""
    param = request.get('param')
    
    # Perform action
    
    return {"success": True, "result": param}
```

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Set level via environment
LOG_LEVEL=DEBUG uvicorn smart_meter_simulator.app:app --reload

# In code
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

### VS Code Launch Configuration

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "smart_meter_simulator.app:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "tests/"]
    }
  ]
}
```

---

## Database Migrations

Using SQLAlchemy with Alembic:

```bash
# Initialize alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Documentation

### Building Documentation

```bash
# Install docs dependencies
pip install mkdocs mkdocs-material

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """Short description of function.
    
    Longer description if needed. Can span multiple
    lines.
    
    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to 0.
        
    Returns:
        Description of return value.
        
    Raises:
        ValueError: If param1 is empty.
        
    Example:
        >>> example_function("test", 5)
        True
    """
    pass
```

---

## CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
          
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          
      - name: Run tests
        run: |
          pytest --cov=src/smart_meter_simulator --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Performance Profiling

```python
# Profile with cProfile
python -m cProfile -o profile.stats src/smart_meter_simulator/app.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats

# Memory profiling
pip install memory_profiler
python -m memory_profiler your_script.py
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black . && isort .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(transport): add MQTT transport support

Implements MQTT transport layer for IoT integration.
Includes connection management and QoS configuration.

Closes #123
```
