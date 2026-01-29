"""
High-performance HTTP Transport using Rust Hyper library.

This module provides an HttpTransport implementation that uses the Rust Hyper
library for maximum performance when available, with automatic fallback to
the pure Python aiohttp implementation.

Features:
- HTTP/1.1 and HTTP/2 support
- Connection pooling
- Automatic retries with exponential backoff
- Compression (gzip, brotli)
- Statistics tracking
- Zero-energy reading optimization
"""

import logging
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

from .base import TransportLayer
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)

# Try to import Hyper module
try:
    from ..hyper import (
        is_rust_available,
        HyperTransport as RustHyperTransport,
        TransportConfig as RustTransportConfig,
        TransportMode,
        MonitoringReading,
        BatchResult,
    )
    HYPER_AVAILABLE = is_rust_available()
except ImportError:
    HYPER_AVAILABLE = False
    logger.warning("Hyper module not available, using legacy aiohttp transport")


@dataclass
class HttpHyperTransportStats:
    """Statistics for HTTP transport."""
    sent: int = 0
    failed: int = 0
    bytes_sent: int = 0
    batch_sent: int = 0
    registrations: int = 0
    skipped: int = 0
    avg_latency_ms: float = 0.0


class HttpHyperTransport(TransportLayer):
    """
    High-performance HTTP transport using Rust Hyper library.
    
    Falls back to aiohttp-based HttpTransport when Rust extension is not available.
    
    Features when using Rust Hyper:
    - HTTP/1.1 and HTTP/2 support
    - Connection pooling with configurable limits
    - Automatic retries with exponential backoff
    - gzip/brotli compression
    - Async I/O optimized for high throughput
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        payload_mode: str = 'monitoring',
        batch_size: int = 100,
        max_concurrent: int = 10,
        timeout_secs: int = 30,
        retry_attempts: int = 3,
        skip_zero_energy: bool = True,
        enable_http2: bool = True,
        enable_compression: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.payload_mode = payload_mode
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.timeout_secs = timeout_secs
        self.retry_attempts = retry_attempts
        self.skip_zero_energy = skip_zero_energy
        self.enable_http2 = enable_http2
        self.enable_compression = enable_compression
        
        # Statistics
        self._stats = HttpHyperTransportStats()
        
        # Registered meters tracking
        self.registered_meters: set = set()
        
        # Backend selection
        self._use_rust = HYPER_AVAILABLE
        self._rust_transport: Optional[RustHyperTransport] = None
        self._legacy_transport = None
        
        if self._use_rust:
            logger.info("🚀 Using Rust Hyper HTTP transport (high-performance mode)")
        else:
            logger.info("📦 Using legacy aiohttp HTTP transport")

    async def connect(self) -> bool:
        """Initialize transport connection."""
        if self._use_rust:
            mode = TransportMode.MONITORING if self.payload_mode == 'monitoring' else TransportMode.FULL
            config = RustTransportConfig(
                base_url=self.base_url,
                api_key=self.api_key,
                mode=mode,
                timeout_secs=self.timeout_secs,
                retry_attempts=self.retry_attempts,
                batch_size=self.batch_size,
                batch_timeout_ms=5000,
                max_concurrent=self.max_concurrent,
                skip_zero_energy=self.skip_zero_energy,
                enable_http2=self.enable_http2,
                enable_compression=self.enable_compression,
            )
            self._rust_transport = RustHyperTransport(config)
            result = await self._rust_transport.connect()
            if result:
                logger.info(f"✅ Hyper HTTP Transport connected to {self.base_url}")
            return result
        else:
            # Fall back to legacy transport
            from .http import HttpTransport as LegacyHttpTransport
            self._legacy_transport = LegacyHttpTransport(
                base_url=self.base_url,
                api_key=self.api_key,
                payload_mode=self.payload_mode,
                batch_size=self.batch_size,
            )
            return await self._legacy_transport.connect()

    async def disconnect(self) -> bool:
        """Close transport connection."""
        if self._use_rust and self._rust_transport:
            result = await self._rust_transport.disconnect()
            self._rust_transport = None
            logger.info("🔌 Hyper HTTP Transport disconnected")
            return result
        elif self._legacy_transport:
            return await self._legacy_transport.disconnect()
        return True

    async def register_meter(
        self,
        meter_id: str,
        wallet_address: str,
        meter_type: str = "solar",
        location: str = None,
        latitude: float = None,
        longitude: float = None,
        zone_id: int = None,
    ) -> bool:
        """Register meter with API Gateway before sending readings."""
        if meter_id in self.registered_meters:
            return True
        
        if self._use_rust and self._rust_transport:
            grid_zone = f"zone-{zone_id}" if zone_id else None
            result = await self._rust_transport.register_meter(
                meter_id=meter_id,
                meter_type=meter_type,
                location=location,
                grid_zone=grid_zone,
                latitude=latitude,
                longitude=longitude,
                capacity_kw=None,
            )
            if result:
                self.registered_meters.add(meter_id)
                self._stats.registrations += 1
            return result
        elif self._legacy_transport:
            result = await self._legacy_transport.register_meter(
                meter_id, wallet_address, meter_type,
                location, latitude, longitude, zone_id
            )
            if result:
                self.registered_meters.add(meter_id)
                self._stats.registrations += 1
            return result
        return False

    def _convert_to_monitoring_reading(self, reading: EnergyReading) -> 'MonitoringReading':
        """Convert EnergyReading to MonitoringReading for Rust transport."""
        is_dict = isinstance(reading, dict)
        
        if is_dict:
            return MonitoringReading(
                meter_id=reading.get("meter_serial", ""),
                timestamp=reading.get("timestamp", datetime.utcnow().isoformat()),
                power_w=float(reading.get("power_watts", 0)),
                energy_kwh=float(reading.get("kwh", 0)),
                voltage=float(reading.get("voltage", 230)),
                frequency=float(reading.get("frequency", 50)),
                power_factor=float(reading.get("power_factor", 0.95)),
                meter_type=reading.get("meter_type", "solar"),
            )
        else:
            payload = reading.to_grid_monitoring_payload()
            return MonitoringReading(
                meter_id=payload.get("meter_serial", ""),
                timestamp=payload.get("timestamp", datetime.utcnow().isoformat()),
                power_w=float(payload.get("power_watts", 0)),
                energy_kwh=float(payload.get("kwh", 0)),
                voltage=float(payload.get("voltage", 230)),
                frequency=float(payload.get("frequency", 50)),
                power_factor=float(payload.get("power_factor", 0.95)),
                meter_type=payload.get("meter_type", "solar"),
            )

    async def send_reading(self, reading: EnergyReading) -> bool:
        """Send a single reading via Hyper HTTP transport."""
        if self._use_rust and self._rust_transport:
            try:
                monitoring_reading = self._convert_to_monitoring_reading(reading)
                
                # Skip zero energy readings if configured
                if self.skip_zero_energy and monitoring_reading.energy_kwh == 0 and monitoring_reading.power_w == 0:
                    self._stats.skipped += 1
                    return True
                
                result = await self._rust_transport.send_reading(monitoring_reading)
                if result:
                    self._stats.sent += 1
                else:
                    self._stats.failed += 1
                return result
            except Exception as e:
                logger.error(f"Error sending reading via Hyper: {e}")
                self._stats.failed += 1
                return False
        elif self._legacy_transport:
            return await self._legacy_transport.send_reading(reading)
        return False

    async def send_batch(self, readings: List[EnergyReading]) -> bool:
        """Send a batch of readings via Hyper HTTP transport."""
        if not readings:
            return True
        
        if self._use_rust and self._rust_transport:
            try:
                monitoring_readings = [
                    self._convert_to_monitoring_reading(r) for r in readings
                ]
                
                result: BatchResult = await self._rust_transport.send_batch(monitoring_readings)
                
                self._stats.sent += result.successful
                self._stats.failed += result.failed
                self._stats.batch_sent += 1
                
                success_rate = result.success_rate()
                logger.info(
                    f"Batch sent: {result.successful}/{result.total} "
                    f"({success_rate:.1%}) in {result.elapsed_ms:.1f}ms"
                )
                
                return success_rate > 0.5
            except Exception as e:
                logger.error(f"Error sending batch via Hyper: {e}")
                self._stats.failed += len(readings)
                return False
        elif self._legacy_transport:
            return await self._legacy_transport.send_batch(readings)
        return False

    def get_transfer_stats(self) -> dict:
        """Get transfer statistics for monitoring."""
        if self._use_rust and self._rust_transport:
            rust_stats = self._rust_transport.get_stats()
            total = self._stats.sent + self._stats.failed
            return {
                'sent': self._stats.sent,
                'failed': self._stats.failed,
                'success_rate': f"{(self._stats.sent / max(1, total) * 100):.1f}%",
                'registrations': self._stats.registrations,
                'batches_sent': self._stats.batch_sent,
                'skipped': self._stats.skipped,
                'payload_mode': self.payload_mode,
                'backend': 'rust-hyper',
                'http2_enabled': self.enable_http2,
                'compression_enabled': self.enable_compression,
            }
        elif self._legacy_transport:
            stats = self._legacy_transport.get_transfer_stats()
            stats['backend'] = 'aiohttp'
            return stats
        return {
            'sent': self._stats.sent,
            'failed': self._stats.failed,
            'backend': 'none',
        }

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        if self._use_rust and self._rust_transport:
            return self._rust_transport.is_connected
        elif self._legacy_transport:
            return self._legacy_transport.session is not None
        return False


def create_http_transport(
    base_url: str,
    api_key: Optional[str] = None,
    payload_mode: str = 'monitoring',
    prefer_hyper: bool = True,
    **kwargs
) -> TransportLayer:
    """
    Create an HTTP transport instance.
    
    Args:
        base_url: API Gateway base URL
        api_key: Optional API key for authentication
        payload_mode: 'monitoring' or 'full'
        prefer_hyper: If True, use Rust Hyper when available
        **kwargs: Additional configuration options
    
    Returns:
        HttpHyperTransport if Hyper available and preferred, else legacy HttpTransport
    """
    if prefer_hyper and HYPER_AVAILABLE:
        return HttpHyperTransport(
            base_url=base_url,
            api_key=api_key,
            payload_mode=payload_mode,
            **kwargs
        )
    else:
        from .http import HttpTransport
        return HttpTransport(
            base_url=base_url,
            api_key=api_key,
            payload_mode=payload_mode,
            batch_size=kwargs.get('batch_size', 10),
        )
