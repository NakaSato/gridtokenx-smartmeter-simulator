"""
Dependency injection container for the smart meter simulator.
"""

import logging
from typing import Dict, Any, Optional, TypeVar, Type, Callable

from .config.settings import Settings
from .exceptions import ContainerError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container."""

    def __init__(self):
        """Initialize the container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._settings: Optional[Settings] = None

    def register_settings(self, settings: Settings) -> None:
        """Register application settings."""
        self._settings = settings
        logger.info("Settings registered in container")

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a service instance."""
        key = self._get_key(service_type)
        self._services[key] = instance
        logger.debug(f"Registered instance: {key}")

    def register_singleton(
        self, service_type: Type[T], factory: Callable[[], T]
    ) -> None:
        """Register a singleton service factory."""
        key = self._get_key(service_type)
        self._factories[key] = factory
        logger.debug(f"Registered singleton factory: {key}")

    def register_transient(
        self, service_type: Type[T], factory: Callable[[], T]
    ) -> None:
        """Register a transient service factory."""
        key = self._get_key(service_type)
        self._factories[key] = factory
        logger.debug(f"Registered transient factory: {key}")

    def get(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        key = self._get_key(service_type)

        # Check for registered instances first
        if key in self._services:
            return self._services[key]

        # Check for singletons
        if key in self._singletons:
            return self._singletons[key]

        # Check for factories
        if key in self._factories:
            instance = self._factories[key]()

            # Store as singleton if it was registered as such
            # For simplicity, we'll treat all factories as singletons for now
            self._singletons[key] = instance
            logger.debug(f"Created singleton instance: {key}")
            return instance

        raise ContainerError(f"Service {service_type.__name__} not registered")

    def get_settings(self) -> Settings:
        """Get application settings."""
        if not self._settings:
            raise ContainerError("Settings not registered")
        return self._settings

    def has(self, service_type: Type[T]) -> bool:
        """Check if a service is registered."""
        key = self._get_key(service_type)
        return (
            key in self._services or key in self._factories or key in self._singletons
        )

    def _get_key(self, service_type: Type) -> str:
        """Get the registration key for a service type."""
        return f"{service_type.__module__}.{service_type.__name__}"

    def clear(self) -> None:
        """Clear all registered services (useful for testing)."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._settings = None
        logger.debug("Container cleared")


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = DIContainer()
        logger.info(f"Created new container instance: {id(_container)}")
    else:
        logger.debug(f"Retrieved existing container: {id(_container)}")
    return _container


def configure_container(settings: Settings) -> DIContainer:
    """Configure the container with default services."""
    container = get_container()
    logger.info(f"Configuring container: {id(container)}")
    container.register_settings(settings)

    # Import here to avoid circular imports
    from .core.database import DatabaseManager
    from .core.engine import SimulationEngine
    from .services.meter_service import MeterService
    from .services.simulation_service import SimulationService
    from .transport.websocket import WebSocketManager, WebSocketTransport
    from .transport.http import HttpTransport
    from .transport.composite import CompositeTransport
    from .transport.kafka import KafkaTransport
    from .config.constants import SimulatorConfig

    # Register core services
    db_manager = DatabaseManager(settings.sqlite_db_path)
    container.register_instance(DatabaseManager, db_manager)

    # Configure WebSocket transport (for dashboard)
    ws_manager = WebSocketManager()
    container.register_instance(WebSocketManager, ws_manager)

    ws_transport = WebSocketTransport(ws_manager)
    container.register_instance(WebSocketTransport, ws_transport)

    # Configure HTTP transport (for API Gateway)
    # Use 'monitoring' mode for efficient real-time grid monitoring
    # Use 'full' mode when detailed telemetry is needed
    http_transport = HttpTransport(
        base_url=settings.api_gateway_url, 
        api_key=settings.api_key,
        payload_mode='monitoring',  # Optimized for grid physics monitoring
    )
    container.register_instance(HttpTransport, http_transport)

    # Build transport list (HTTP for API Gateway, WebSocket for dashboard)
    transports = [http_transport, ws_transport]
    
    # Add Kafka transport if enabled for high-throughput streaming
    if SimulatorConfig.KAFKA_ENABLED:
        kafka_transport = KafkaTransport(
            bootstrap_servers=SimulatorConfig.KAFKA_SERVERS,
            topic=SimulatorConfig.KAFKA_TOPIC,
        )
        transports.append(kafka_transport)
        logger.info(f"✅ Kafka transport enabled: {SimulatorConfig.KAFKA_SERVERS} -> {SimulatorConfig.KAFKA_TOPIC}")
    
    # Use CompositeTransport to send to all configured transports
    composite_transport = CompositeTransport(transports)
    
    # Initialize engine with composite transport (sends to both Gateway and Dashboard)
    from .simulation.engine import PhysicsSimulationEngine
    
    # Select grid model based on settings or default to THAI_GRID
    model_type = "THAI_GRID" 
    
    # Load meters from database
    from .core.meter import SmartMeter
    loaded_configs = db_manager.load_meters()
    
    # Limit number of meters based on settings
    max_meters = settings.num_meters
    if max_meters > 0 and len(loaded_configs) > max_meters:
        logger.info(f"Limiting loaded meters from {len(loaded_configs)} to {max_meters}")
        loaded_configs = loaded_configs[:max_meters]
        
    meters = [SmartMeter(config) for config in loaded_configs]
    logger.info(f"Loaded {len(meters)} meters from database into engine")

    # Initialize Physics Simulation Engine (focused on grid simulation, no P2P matching)
    sim_engine = PhysicsSimulationEngine(
        meters=meters, 
        transport=composite_transport, 
        model_type=model_type,
        db_manager=db_manager
    )
    container.register_instance(SimulationEngine, sim_engine)

    # Register application services
    meter_service = MeterService(engine=sim_engine, db_manager=db_manager)
    container.register_instance(MeterService, meter_service)

    sim_service = SimulationService(engine=sim_engine, db_manager=db_manager)
    container.register_instance(SimulationService, sim_service)

    # Register additional core services
    from .services.gis_service import GISService
    from .services.ledger_service import LedgerService
    from .services.token_service import TokenService
    from .services.zoning_service import MicrogridZoningService
    from .services.transaction_service import P2PTransactionService
    from .core.weather_service import WeatherService

    gis_service = GISService()
    container.register_instance(GISService, gis_service)

    zoning_service = MicrogridZoningService()
    container.register_instance(MicrogridZoningService, zoning_service)

    weather_service = WeatherService()
    container.register_instance(WeatherService, weather_service)

    token_service = TokenService()
    container.register_instance(TokenService, token_service)

    ledger_service = LedgerService(db_manager=db_manager)
    container.register_instance(LedgerService, ledger_service)

    transaction_service = P2PTransactionService(zoning_service=zoning_service)
    container.register_instance(P2PTransactionService, transaction_service)

    logger.info("Container configured with default services")
    return container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    if _container:
        _container.clear()
    _container = None
    logger.debug("Container reset")
