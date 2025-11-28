"""
Database configuration settings.
"""

from typing import Optional
from pydantic import Field, BaseModel


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    
    url: str = Field(default="sqlite:///smart_meter.db", description="Database URL")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum overflow connections")
    pool_timeout: int = Field(default=30, description="Connection timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Connection recycle time in seconds")
    echo: bool = Field(default=False, description="Enable SQL logging")
    
    @property
    def database_path(self) -> Optional[str]:
        """Extract database path from URL for SQLite."""
        if self.url.startswith("sqlite:///"):
            return self.url.replace("sqlite:///", "")
        return None
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.url.startswith("sqlite://")
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL."""
        return self.url.startswith("postgresql://") or self.url.startswith("postgres://")
