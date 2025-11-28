"""
Simple dependency injection container for Smart Meter Simulator.
"""

from typing import Dict, Any, Optional, TypeVar, Type, Callable
from functools import lru_cache

T = TypeVar('T')


class DIContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton instance."""
        key = self._get_key(service_type)
        self._singletons[key] = instance
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for a service."""
        key = self._get_key(service_type)
        self._factories[key] = factory
    
    def register_transient(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a transient service (new instance each time)."""
        key = self._get_key(service_type)
        self._services[key] = factory
    
    def get(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        key = self._get_key(service_type)
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check factories
        if key in self._factories:
            instance = self._factories[key]()
            self._singletons[key] = instance  # Cache the instance
            return instance
        
        # Check transient services
        if key in self._services:
            return self._services[key]()
        
        raise ValueError(f"Service {service_type.__name__} not registered")
    
    def _get_key(self, service_type: Type) -> str:
        """Get the registration key for a service type."""
        return f"{service_type.__module__}.{service_type.__name__}"
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global dependency injection container."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def init_container() -> DIContainer:
    """Initialize the container with default services."""
    container = get_container()
    
    # This will be populated later with actual services
    return container


def inject(service_type: Type[T]) -> T:
    """Dependency injection decorator/function."""
    container = get_container()
    return container.get(service_type)


@lru_cache()
def get_settings():
    """Get settings instance with caching."""
    from ..config.settings import get_settings as _get_settings
    return _get_settings()


@lru_cache()
def get_database_config():
    """Get database config with caching."""
    from ..config.database import DatabaseConfig
    return DatabaseConfig()


@lru_cache()
def get_simulation_config():
    """Get simulation config with caching."""
    from ..config.simulation import SimulationConfig
    return SimulationConfig()


@lru_cache()
def get_transport_config():
    """Get transport config with caching."""
    from ..config.transport import TransportConfig
    return TransportConfig()
