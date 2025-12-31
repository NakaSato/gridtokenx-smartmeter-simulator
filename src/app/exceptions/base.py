"""
Base exception classes for the Smart Meter Simulator.
"""

from typing import Optional


class SmartMeterSimulatorError(Exception):
    """Base exception for all Smart Meter Simulator errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize the base exception."""
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the exception."""
        return self.message


class ConfigurationError(SmartMeterSimulatorError):
    """Raised when there's a configuration error."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """Initialize configuration error."""
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, details)


class DatabaseError(SmartMeterSimulatorError):
    """Raised when there's a database operation error."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        """Initialize database error."""
        details = {"operation": operation} if operation else {}
        super().__init__(message, details)


class TransportError(SmartMeterSimulatorError):
    """Raised when there's a transport layer error."""
    
    def __init__(self, message: str, transport_type: Optional[str] = None):
        """Initialize transport error."""
        details = {"transport_type": transport_type} if transport_type else {}
        super().__init__(message, details)


class SimulationError(SmartMeterSimulatorError):
    """Raised when there's a simulation operation error."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        """Initialize simulation error."""
        details = {"operation": operation} if operation else {}
        super().__init__(message, details)


class MeterError(SmartMeterSimulatorError):
    """Raised when there's a meter operation error."""
    
    def __init__(self, message: str, meter_id: Optional[str] = None):
        """Initialize meter error."""
        details = {"meter_id": meter_id} if meter_id else {}
        super().__init__(message, details)


class ValidationError(SmartMeterSimulatorError):
    """Raised when there's a validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        """Initialize validation error."""
        details = {}
        if field:
            details["field"] = field
        if value:
            details["value"] = value
        super().__init__(message, details)


class ContainerError(SmartMeterSimulatorError):
    """Raised when there's a dependency injection container error."""
    
    def __init__(self, message: str, service_name: Optional[str] = None):
        """Initialize container error."""
        details = {"service_name": service_name} if service_name else {}
        super().__init__(message, details)
