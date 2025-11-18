"""
External Services Module
Handles connections to Kafka, InfluxDB, and PostgreSQL
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable, KafkaTimeoutError
except ImportError:
    KafkaProducer = None
    NoBrokersAvailable = None
    KafkaTimeoutError = None

try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    InfluxDBClient = None
    SYNCHRONOUS = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None


class ServiceManager:
    """Manages external service connections"""

    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self.db_conn = None
        self.influxdb_client: Optional[InfluxDBClient] = None
        self.influxdb_write_api = None
        self.services_available = 0

    def init_kafka(self, bootstrap_servers: str) -> bool:
        """Initialize Kafka producer"""
        if not KafkaProducer:
            logger.warning("Kafka not available: KafkaProducer not installed")
            return False
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers.split(','),
                value_serializer=lambda v: self._serialize_json(v),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                request_timeout_ms=10000,
                retries=3,
                max_request_size=1048576,
                compression_type='gzip'
            )
            logger.info("Kafka producer initialized successfully")
            self.services_available += 1
            return True
        except Exception as e:
            logger.warning(f"Kafka not available: {e}")
            self.producer = None
            return False

    def init_database(self, db_url: str) -> bool:
        """Initialize PostgreSQL database connection"""
        if not psycopg2:
            logger.warning("Main database not available: psycopg2 not installed")
            return False

        try:
            self.db_conn = psycopg2.connect(db_url)
            logger.info("Main database connection established")
            self.services_available += 1
            return True
        except Exception as e:
            logger.warning(f"Main database not available: {e}")
            self.db_conn = None
            return False

    def init_influxdb(
        self,
        url: str,
        token: str,
        org: str
    ) -> bool:
        """Initialize InfluxDB connection"""
        if not InfluxDBClient or not SYNCHRONOUS:
            logger.warning("InfluxDB not available: influxdb_client not installed")
            return False
        
        try:
            self.influxdb_client = InfluxDBClient(
                url=url,
                token=token,
                org=org
            )
            try:
                # Try new API (v1.18+)
                self.influxdb_write_api = (
                    self.influxdb_client.write_api(write_type=SYNCHRONOUS)
                )
            except TypeError:
                # Fallback to older API
                self.influxdb_write_api = (
                    self.influxdb_client.write_api(SYNCHRONOUS)
                )
            logger.info("InfluxDB connection established")
            self.services_available += 1
            return True
        except Exception as e:
            logger.warning(f"InfluxDB not available: {e}")
            self.influxdb_client = None
            self.influxdb_write_api = None
            return False

    def close_all(self):
        """Close all service connections"""
        if self.producer:
            try:
                self.producer.close()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka: {e}")

        if self.db_conn:
            try:
                self.db_conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")

        if self.influxdb_client:
            try:
                self.influxdb_client.close()
                logger.info("InfluxDB connection closed")
            except Exception as e:
                logger.error(f"Error closing InfluxDB: {e}")

    @staticmethod
    def _serialize_json(obj):
        """Serialize object to JSON bytes"""
        import json
        return json.dumps(obj, default=str).encode('utf-8')
