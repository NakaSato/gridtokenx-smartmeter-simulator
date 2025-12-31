"""
Transport configuration settings.
"""

from typing import Optional, Dict, Any
from pydantic import Field, BaseModel


class TransportConfig(BaseModel):
    """Transport configuration settings."""
    
    # HTTP Transport
    http_base_url: str = Field(default="http://localhost:8080", description="HTTP API base URL")
    http_api_key: str = Field(default="sim-secret-key", description="HTTP API key")
    http_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    http_retry_attempts: int = Field(default=3, description="HTTP retry attempts")
    http_retry_delay: float = Field(default=1.0, description="HTTP retry delay in seconds")
    
    # WebSocket Transport
    websocket_enabled: bool = Field(default=True, description="Enable WebSocket transport")
    websocket_heartbeat_interval: int = Field(default=30, description="WebSocket heartbeat interval")
    websocket_max_connections: int = Field(default=100, description="Maximum WebSocket connections")
    
    # General Transport Settings
    batch_size: int = Field(default=10, description="Batch size for sending readings")
    batch_timeout: float = Field(default=5.0, description="Batch timeout in seconds")
    compression_enabled: bool = Field(default=False, description="Enable compression")
    
    def get_http_config(self) -> Dict[str, Any]:
        """Get HTTP transport configuration."""
        return {
            "base_url": self.http_base_url,
            "api_key": self.http_api_key,
            "timeout": self.http_timeout,
            "retry_attempts": self.http_retry_attempts,
            "retry_delay": self.http_retry_delay,
        }
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket transport configuration."""
        return {
            "enabled": self.websocket_enabled,
            "heartbeat_interval": self.websocket_heartbeat_interval,
            "max_connections": self.websocket_max_connections,
        }
