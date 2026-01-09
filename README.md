# Smart Meter Simulator

A Python-based simulator for the GridTokenX platform that mimics smart meter behavior, generates energy readings, and simulates grid topology.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Poetry or pip
- Node.js (for visualization frontend, optional)

### Installation

```bash
cd gridtokenx-smartmeter-simulator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Simulator

```bash
# Start the simulator on port 8080
./start-simulator.sh
```

The API will be available at `http://localhost:8080`.

## ⚙️ Configuration

The simulator is configured via environment variables in `.env`:

```env
PORT=8080
API_GATEWAY_URL=http://localhost:4000
LOG_LEVEL=INFO
```

## 🔌 API Endpoints

- `GET /api/zones`: Get grid topology and zones.
- `GET /api/meters`: Get all registered meters.
- `POST /api/control/generate`: Force generate new readings.
- `WS /ws/meters`: Real-time meter updates.
## 📡 HTTP Transfer Optimization

The simulator now uses **optimized payload modes** for efficient data transfer:

### Monitoring Mode (Default) - 62.4% Bandwidth Reduction
- **Size**: 376 bytes (15 fields)
- **Use Case**: Real-time grid monitoring & microgrid optimization
- **Fields**: Grid physics (voltage, frequency, THD), energy metrics, battery state, location
- **Performance**: 2,789 readings/MB (vs 1,049 old implementation)

### Full Telemetry Mode - Complete Data
- **Size**: 775 bytes (29 fields)  
- **Use Case**: Detailed reporting, blockchain integration, REC certification
- **Fields**: All monitoring fields + certification, blockchain, extended metrics

**Configuration** (in `src/app/container.py`):
```python
http_transport = HttpTransport(
    base_url=settings.api_gateway_url,
    payload_mode='monitoring'  # or 'full'
)
```

**Documentation**:
- [Quick Reference](docs/HTTP_TRANSFER_QUICK_REF.md)
- [Complete Guide](docs/HTTP_TRANSFER_OPTIMIZATION.md)
- [Architecture Diagrams](docs/HTTP_TRANSFER_ARCHITECTURE.md)
- [Refactoring Summary](REFACTOR_HTTP_TRANSFER.md)

**Impact**: 254.5 GB/month bandwidth savings (10,000 meters @ 1 reading/min)