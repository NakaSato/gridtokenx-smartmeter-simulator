# System Architecture Overview

This document provides a high-level overview of the Smart Meter Simulator architecture.

## System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                    GridTokenX Ecosystem                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Solana     │    │  API Gateway │    │  Trading     │      │
│  │  Blockchain  │◄──►│   (Rust)     │◄──►│   Service    │      │
│  └──────────────┘    └──────┬───────┘    └──────────────┘      │
│                             ▲                                   │
│                             │ HTTP/WebSocket                    │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Smart Meter Simulator (Python/FastAPI)         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Simulation│  │  Grid    │  │ Market   │  │  VPP     │ │   │
│  │  │  Engine   │  │ Adapter  │  │ Engine   │  │ Manager  │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│              ┌──────────────┼──────────────┐                   │
│              ▼              ▼              ▼                   │
│       ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│       │ Kafka    │  │InfluxDB  │  │PostgreSQL│                │
│       │ Events   │  │  Time-   │  │  State   │                │
│       │          │  │  series  │  │          │                │
│       └──────────┘  └──────────┘  └──────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Simulation Engine

**Location:** [`core/engine.py`](../src/smart_meter_simulator/core/engine.py)

The `SimulationEngine` orchestrates the entire simulation:

**Responsibilities:**
- Manages meter lifecycle and reading generation
- Coordinates weather simulation updates
- Dispatches readings through transport layers
- Integrates pandapower for grid state estimation
- Handles VPP dispatch commands
- Runs market matching and settlement
- Implements bad data detection

**Key Features:**
- Async meter orchestration (1000+ meters)
- Configurable simulation intervals
- Weather-aware solar generation modeling
- Real-time grid frequency regulation
- Islanding detection and black start capability

### 2. Smart Meter

**Location:** [`core/meter.py`](../src/smart_meter_simulator/core/meter.py)

Each `SmartMeter` instance represents a physical smart meter:

**Characteristics:**
- Ed25519 keypair for cryptographic signing
- Accuracy class modeling (ANSI C12.20)
- Frequency-watt droop control
- VPP dispatch setpoint handling
- Battery/EV logic

**Measurement Model:**
```python
z = h(x_true) + ε
ε ~ N(0, σ²)
σ = (accuracy_class / 300) × |value|
```

### 3. Grid Integration

**Location:** [`adapters/`](../src/smart_meter_simulator/adapters/)

#### Pandapower Adapter
- Converts meter readings to `net.measurement` tables
- Maps element types: bus, line, load, sgen, trafo
- Calculates std_dev from accuracy classes

#### State Estimator
- WLS algorithm (Newton-Raphson)
- Iwamoto method (divergence handling)
- Chi-squared test for bad data detection
- Normalized residuals analysis

### 4. Market Engine

**Location:** [`core/market.py`](../src/smart_meter_simulator/core/market.py)

**Features:**
- Double auction mechanism
- Locational Marginal Pricing (LMP)
- Dynamic pricing based on supply/demand
- Thai TOU tariff integration
- P2P trading settlement

**Pricing Formula:**
```python
p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min
D_t = (Demand - Supply) / 100
R_t = Demand / Supply
```

### 5. Transport Layer

**Location:** [`transport/`](../src/smart_meter_simulator/transport/)

Abstracted transport interface:

**Available Transports:**
- **HTTP:** REST API submission to API Gateway
- **WebSocket:** Real-time broadcasting
- **Kafka:** Event streaming for distributed systems
- **InfluxDB:** Time-series data persistence
- **Composite:** Aggregates multiple transports

## Data Flow

### Reading Generation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Weather   │────►│  Smart      │────►│  Energy     │
│  Simulator  │     │  Meter      │     │  Reading    │
└─────────────┘     └─────────────┘     └─────────────┘
                                             │
                                             ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   External  │◄────│  Transport  │◄────│  Signing    │
│   Systems   │     │  Layer      │     │  (Ed25519)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

### State Estimation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Meter     │────►│  Pandapower │────►│   Power     │
│  Readings   │     │  Adapter    │     │   Flow      │
└─────────────┘     └─────────────┘     └─────────────┘
                                             │
                                             ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Bad Data  │◄────│   State     │◄────│ Measurement │
│  Detection  │     │  Estimator  │     │   Table     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Market Clearing Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Buy       │────►│   Order     │────►│   Market    │
│   Orders    │     │   Book      │     │   Clearing  │
└─────────────┘     └─────────────┘     └─────────────┘
                                             │
                                             ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Grid      │◄────│   LMP       │◄────│   Supply/   │
│   Topology  │     │ Calculation │     │   Demand    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | REST API and WebSocket |
| Async Runtime | asyncio | Concurrent meter simulation |
| Grid Modeling | pandapower | Power system simulation |
| Numerical | NumPy, Polars | Vectorized calculations |
| Signing | cryptography | Ed25519 signatures |
| Validation | Pydantic | Data validation |

### Data Storage

| Storage | Technology | Use Case |
|---------|------------|----------|
| Time-series | InfluxDB | Meter readings |
| Relational | PostgreSQL | State, configuration |
| Event Stream | Kafka | Real-time events |
| Cache | Redis | Session, pub/sub |

### External Integrations

| System | Protocol | Purpose |
|--------|----------|---------|
| Solana | RPC | Blockchain settlement |
| API Gateway | HTTP/REST | Reading submission |
| Mapbox | API | Geographic matching |
| Mosaik | Co-simulation | Multi-domain simulation |

## Deployment Architecture

### Single Instance

```
┌─────────────────────────────────────┐
│         Smart Meter Simulator        │
│  ┌───────────────────────────────┐  │
│  │  FastAPI Server (8082)        │  │
│  │  - REST API                   │  │
│  │  - WebSocket                  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Simulation Engine            │  │
│  │  - Meters                     │  │
│  │  - Grid Model                 │  │
│  │  - Market                     │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Scaled Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Simulator   │ │  Simulator   │ │  Simulator   │
│  Instance 1  │ │  Instance 2  │ │  Instance N  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    Kafka     │ │  InfluxDB    │ │  PostgreSQL  │
│   Cluster    │ │   Cluster    │ │   Primary    │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Security Architecture

### Cryptographic Signing

Each meter generates an Ed25519 keypair:
- **Private Key:** Stored securely in meter instance
- **Public Key:** Included in readings for verification
- **Signature:** Signs reading data for authenticity

### Authentication

- **API Key:** Required for API Gateway integration
- **WebSocket:** Optional token-based authentication
- **mTLS:** Supported for service-to-service communication

### Data Protection

- **In Transit:** TLS/SSL for all external communication
- **At Rest:** Encrypted storage for sensitive data
- **Zero-Knowledge Proofs:** Optional ZK proof generation

## Performance Characteristics

### Scalability Targets

| Metric | Target |
|--------|--------|
| 1000+ meters × 365 days | <5 minutes |
| State Estimation convergence | >98% |
| FDI detection rate | >99% |

### Optimization Strategies

1. **Numba JIT:** 10-50x speedup for pandapower Jacobian
2. **Polars:** Fast DataFrame operations
3. **Vectorized Controllers:** Single `ConstControl` for multiple loads
4. **Async I/O:** All transports use async operations
5. **Matrix Recycling:** Reuse Ybus matrices in time-series

## Related Documents

- [Simulation Engine Architecture](simulation-engine.md)
- [Smart Meter Model](smart-meter.md)
- [Grid Integration](grid-integration.md)
- [Market Engine](market-engine.md)
- [Transport Layer](transport-layer.md)
