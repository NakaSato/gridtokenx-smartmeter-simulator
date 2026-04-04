# Transport Layer Architecture

**Location:** [`src/smart_meter_simulator/transport/`](../src/smart_meter_simulator/transport/)

This document describes the transport layer for data delivery to external systems.

## Components Overview

```
┌────────────────────────────────────────────────────────────┐
│                    Transport Layer                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CompositeTransport                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │  HTTP    │  │WebSocket │  │  Kafka   │          │  │
│  │  │Transport │  │Transport │  │Transport │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  │  ┌──────────┐                                       │  │
│  │  │InfluxDB  │                                       │  │
│  │  │Transport │                                       │  │
│  │  └──────────┘                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              TransportLayer (Base)                    │  │
│  │  - Connection state management                        │  │
│  │  - Retry logic                                        │  │
│  │  - Reading conversion                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## Base Transport Layer

**Location:** [`transport/base.py`](../src/smart_meter_simulator/transport/base.py)

### Abstract Base Class

```python
class TransportLayer(ABC):
    """
    Abstract base class for all transport layers.
    
    Features:
    - Connection state management
    - Retry logic with configurable attempts
    - Reading conversion helpers
    - Error handling and logging
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to transport endpoint."""
        pass
    
    @abstractmethod
    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send single reading to endpoint."""
        pass
    
    @abstractmethod
    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send batch of readings to endpoint."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to endpoint."""
        pass
```

### Retry Logic

```python
class RetryConfig:
    """Retry configuration."""
    
    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 30.0

async def send_with_retry(self, reading: EnergyReading) -> bool:
    """
    Send reading with exponential backoff retry.
    
    Retry Schedule:
    - Attempt 1: Immediate
    - Attempt 2: After 1s
    - Attempt 3: After 2s
    - Attempt 4: After 4s (if max_attempts=4)
    """
    delay = self.retry_config.delay_seconds
    
    for attempt in range(self.retry_config.max_attempts):
        try:
            success = await self._send_impl(reading)
            if success:
                return True
        except Exception as e:
            logger.warning(f"Send attempt {attempt + 1} failed: {e}")
            
            if attempt < self.retry_config.max_attempts - 1:
                await asyncio.sleep(delay)
                delay = min(
                    delay * self.retry_config.backoff_multiplier,
                    self.retry_config.max_delay_seconds
                )
    
    return False
```

## HTTP Transport

**Location:** [`transport/http.py`](../src/smart_meter_simulator/transport/http.py)

### REST API Client

```python
class HttpTransport(TransportLayer):
    """
    HTTP transport for REST API submission.
    
    Configuration:
    - base_url: API Gateway endpoint
    - api_key: Authentication key
    - timeout: Request timeout
    - retry_config: Retry settings
    
    Endpoints:
    - POST /api/readings - Submit readings
    - POST /api/meters/register - Register meters
    """
```

### Implementation

```python
async def send_reading(self, reading: EnergyReading) -> bool:
    """
    Send reading to API Gateway.
    
    Request:
    POST {base_url}/api/readings
    Headers:
      Authorization: Bearer {api_key}
      Content-Type: application/json
    Body:
      {
        "meter_id": "...",
        "timestamp": "...",
        "energy_generated_kwh": ...,
        "energy_consumed_kwh": ...,
        "signature": "...",
        "public_key": "..."
      }
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.base_url}/api/readings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=reading.to_dict()
        ) as response:
            if response.status == 200:
                logger.debug(f"Reading sent: {reading.meter_id}")
                return True
            else:
                logger.error(f"HTTP error: {response.status}")
                return False
```

### Meter Registration

```python
async def register_meters(self, meters: List[SmartMeter]) -> bool:
    """
    Register meters with API Gateway.
    
    Request:
    POST {base_url}/api/meters/register
    Body:
      {
        "meters": [
          {
            "meter_id": "...",
            "type": "...",
            "public_key": "...",
            "accuracy_class": "..."
          }
        ]
      }
    """
    meter_data = [
        {
            "meter_id": m.meter_id,
            "type": m.meter_type,
            "public_key": m.public_key_hex,
            "accuracy_class": m.accuracy_class.name
        }
        for m in meters
    ]
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.base_url}/api/meters/register",
            json={"meters": meter_data}
        ) as response:
            return response.status == 200
```

## WebSocket Transport

**Location:** [`transport/websocket.py`](../src/smart_meter_simulator/transport/websocket.py)

### Real-time Broadcasting

```python
class WebSocketTransport(TransportLayer):
    """
    WebSocket transport for real-time broadcasting.
    
    Features:
    - Bidirectional communication
    - Real-time reading streaming
    - Connection pooling
    - Automatic reconnection
    
    Endpoint: ws://{host}:{port}/ws
    """
```

### WebSocket Manager

```python
class WebSocketManager:
    """
    Manage WebSocket connections.
    
    Features:
    - Connection tracking
    - Broadcast to all clients
    - Per-client message queues
    - Heartbeat/ping-pong
    """
    
    async def broadcast(self, reading: EnergyReading):
        """
        Broadcast reading to all connected clients.
        
        Message Format:
        {
          "type": "reading",
          "data": {
            "meter_id": "...",
            "timestamp": "...",
            "energy_generated_kwh": ...,
            ...
          }
        }
        """
        message = json.dumps({
            "type": "reading",
            "data": reading.to_dict()
        })
        
        # Send to all connected clients
        for websocket in self.connections:
            try:
                await websocket.send(message)
            except Exception as e:
                logger.warning(f"Broadcast failed: {e}")
                await self.remove_connection(websocket)
```

### Client Example

```javascript
// JavaScript client example
const ws = new WebSocket('ws://localhost:8082/ws');

ws.onopen = () => {
  console.log('Connected to simulator');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'reading') {
    console.log('Meter reading:', message.data);
  } else if (message.type === 'price') {
    console.log('Price update:', message.data);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
  // Reconnect after 5 seconds
  setTimeout(connect, 5000);
};
```

## Kafka Transport

**Location:** [`transport/kafka.py`](../src/smart_meter_simulator/transport/kafka.py)

### Event Streaming

```python
class KafkaTransport(TransportLayer):
    """
    Kafka transport for event streaming.
    
    Configuration:
    - bootstrap_servers: Kafka brokers
    - topic: Topic name
    - producer_config: Kafka producer settings
    
    Features:
    - High throughput
    - Durability (persistent logs)
    - Multiple consumers
    - Event sourcing
    """
```

### Implementation

```python
from aiokafka import AIOKafkaProducer

class KafkaTransport(TransportLayer):
    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
    
    async def connect(self) -> bool:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        return True
    
    async def send_reading(self, reading: EnergyReading) -> bool:
        try:
            await self.producer.send_and_wait(
                self.topic,
                reading.to_dict()
            )
            return True
        except Exception as e:
            logger.error(f"Kafka send failed: {e}")
            return False
```

### Consumer Example

```python
from aiokafka import AIOKafkaConsumer

async def consume_readings():
    consumer = AIOKafkaConsumer(
        'meter_readings',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    await consumer.start()
    
    async for msg in consumer:
        reading = msg.value
        print(f"Received: {reading['meter_id']}")
```

## InfluxDB Transport

**Location:** [`transport/influxdb.py`](../src/smart_meter_simulator/transport/influxdb.py)

### Time-Series Storage

```python
class InfluxDBTransport(TransportLayer):
    """
    InfluxDB transport for time-series storage.
    
    Configuration:
    - url: InfluxDB server URL
    - token: Authentication token
    - org: Organization name
    - bucket: Bucket name
    
    Measurement Schema:
    - measurement: energy_readings
    - tags: meter_id, meter_type, accuracy_class
    - fields: energy_generated, energy_consumed, voltage, current, frequency
    - time: timestamp
    """
```

### Implementation

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

class InfluxDBTransport(TransportLayer):
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        
        self.client = InfluxDBClient(url=url, token=token)
        self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
    
    async def send_reading(self, reading: EnergyReading) -> bool:
        try:
            point = Point("energy_readings") \
                .tag("meter_id", reading.meter_id) \
                .tag("meter_type", reading.meter_type) \
                .field("energy_generated_kwh", reading.energy_generated_kwh) \
                .field("energy_consumed_kwh", reading.energy_consumed_kwh) \
                .field("voltage_v", reading.voltage_v) \
                .field("current_a", reading.current_a) \
                .field("frequency_hz", reading.frequency_hz) \
                .time(reading.timestamp)
            
            await self.write_api.write(bucket=self.bucket, record=point)
            return True
        except Exception as e:
            logger.error(f"InfluxDB write failed: {e}")
            return False
```

### Query Example

```python
def query_readings(self, meter_id: str, start: str, stop: str):
    """
    Query readings from InfluxDB.
    
    Flux Query:
    from(bucket: "energy_readings")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "energy_readings")
      |> filter(fn: (r) => r.meter_id == "AMI_METER_001")
      |> filter(fn: (r) => r._field == "energy_generated_kwh")
    """
    query = f'''
    from(bucket: "{self.bucket}")
      |> range(start: {start}, stop: {stop})
      |> filter(fn: (r) => r._measurement == "energy_readings")
      |> filter(fn: (r) => r.meter_id == "{meter_id}")
    '''
    
    result = self.client.query_api().query(query)
    return result
```

## Composite Transport

**Location:** [`transport/composite.py`](../src/smart_meter_simulator/transport/composite.py)

### Multi-Transport Aggregation

```python
class CompositeTransport(TransportLayer):
    """
    Aggregate multiple transport layers.
    
    Features:
    - Send to all transports simultaneously
    - Independent failure handling
    - Configurable transport list
    
    Use Cases:
    - Send to API Gateway + Kafka + InfluxDB
    - Redundant data delivery
    - Multi-system integration
    """
    
    def __init__(self, transports: List[TransportLayer]):
        self.transports = transports
    
    async def send_reading(self, reading: EnergyReading) -> bool:
        """
        Send reading to all transports.
        
        Returns:
            True if at least one transport succeeded
        """
        results = await asyncio.gather(
            *[t.send_reading(reading) for t in self.transports],
            return_exceptions=True
        )
        
        successes = sum(1 for r in results if r is True)
        failures = len(results) - successes
        
        logger.debug(
            f"Transport results: {successes} succeeded, {failures} failed"
        )
        
        return successes > 0
```

### Configuration Example

```python
# Create transports
http_transport = HttpTransport(
    base_url="http://api.gridtokenx.io",
    api_key="secret-key"
)

websocket_transport = WebSocketTransport(websocket_manager)

kafka_transport = KafkaTransport(
    bootstrap_servers="localhost:9092",
    topic="meter_readings"
)

influxdb_transport = InfluxDBTransport(
    url="http://localhost:8086",
    token="my-token",
    org="gridtoken",
    bucket="energy_readings"
)

# Create composite transport
composite = CompositeTransport([
    http_transport,
    websocket_transport,
    kafka_transport,
    influxdb_transport
])

# Use in simulation engine
engine = SimulationEngine(meters, composite)
```

## Error Handling

### Transport Errors

```python
class TransportError(Exception):
    """Base transport error."""
    pass

class ConnectionError(TransportError):
    """Connection failed."""
    pass

class TimeoutError(TransportError):
    """Request timed out."""
    pass

class AuthenticationError(TransportError):
    """Authentication failed."""
    pass
```

### Error Recovery

```python
async def handle_transport_error(self, error: Exception):
    """
    Handle transport errors with recovery strategies.
    
    Strategies:
    - Connection error: Reconnect with backoff
    - Timeout: Retry with exponential backoff
    - Authentication error: Refresh credentials
    - Unknown error: Log and continue
    """
    if isinstance(error, ConnectionError):
        await self.reconnect()
    elif isinstance(error, TimeoutError):
        await self.retry_with_backoff()
    elif isinstance(error, AuthenticationError):
        await self.refresh_credentials()
    else:
        logger.error(f"Unknown transport error: {error}")
```

## Performance Considerations

### Batch Processing

```python
async def send_batch(self, readings: List[EnergyReading]) -> bool:
    """
    Send batch of readings for better throughput.
    
    Benefits:
    - Reduced network overhead
    - Better compression
    - Lower API call count
    
    Trade-offs:
    - Higher latency
    - Larger memory footprint
    """
    # Group readings by meter
    by_meter = defaultdict(list)
    for reading in readings:
        by_meter[reading.meter_id].append(reading)
    
    # Send batched request
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.base_url}/api/readings/batch",
            json={"readings": [r.to_dict() for r in readings]}
        ) as response:
            return response.status == 200
```

### Async Concurrency

```python
# Parallel transport dispatch
async def send_to_all_transports(self, reading: EnergyReading):
    tasks = [
        self.http_transport.send_reading(reading),
        self.kafka_transport.send_reading(reading),
        self.influxdb_transport.send_reading(reading)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Testing

```python
@pytest.mark.unit
async def test_http_transport_send(http_transport, reading):
    success = await http_transport.send_reading(reading)
    assert success == True

@pytest.mark.integration
async def test_kafka_transport_send(kafka_transport, reading):
    success = await kafka_transport.send_reading(reading)
    assert success == True
    
    # Verify message in Kafka
    consumer = AIOKafkaConsumer('meter_readings')
    msg = await consumer.getone()
    assert msg.value['meter_id'] == reading.meter_id

@pytest.mark.unit
async def test_composite_transport_send(composite_transport, reading):
    success = await composite_transport.send_reading(reading)
    assert success == True
```

## Related Documents

- [System Overview](overview.md)
- [Simulation Engine](simulation-engine.md)
- [API Reference](../api/overview.md)
