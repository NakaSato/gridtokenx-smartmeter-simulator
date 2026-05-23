"""
InfluxDB Query Service for real-time time-series data retrieval.

Provides high-performance queries for dashboards, analytics, and real-time monitoring.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from influxdb_client import InfluxDBClient

    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None


class InfluxDBQueryService:
    """
    Service for querying real-time time-series data from InfluxDB.

    Provides optimized queries for:
    - Latest meter readings
    - Historical trends
    - Aggregations (mean, max, min, sum)
    - Real-time grid metrics
    - Alert history
    """

    def __init__(
        self,
        url: str = "http://gridtokenx-influxdb:8086",
        token: str = "",
        org: str = "gridtokenx",
        bucket: str = "meter_readings",
    ):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client: Optional[InfluxDBClient] = None
        self.connected = False

        if not INFLUXDB_AVAILABLE:
            logger.warning("InfluxDB client not installed. Run: uv add influxdb-client")

    async def connect(self) -> bool:
        """Initialize InfluxDB client."""
        if not INFLUXDB_AVAILABLE:
            return False

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)

            # Test connection by pinging
            self.client.ping()
            self.connected = True
            logger.info(f"InfluxDB query service connected to {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect InfluxDB query service: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Close InfluxDB client."""
        if self.client:
            self.client.close()
            self.client = None
            self.connected = False
            logger.info("InfluxDB query service disconnected")

    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute Flux query and return results as list of dicts."""
        if not self.connected or not self.client:
            return []

        try:
            query_api = self.client.query_api()
            tables = query_api.query(query, org=self.org)

            results = []
            for table in tables:
                for record in table.records:
                    results.append(
                        {
                            "time": record.get_time().isoformat()
                            if record.get_time()
                            else None,
                            "measurement": record.get_measurement(),
                            "meter_id": record.values.get("meter_id"),
                            "field": record.get_field(),
                            "value": record.get_value(),
                            **{
                                k: v
                                for k, v in record.values.items()
                                if k.startswith("tag_")
                                or k in ["meter_type", "location"]
                            },
                        }
                    )

            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    # =========================================================================
    # Real-Time Queries
    # =========================================================================

    def get_latest_readings(
        self,
        meter_ids: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get latest readings for specified meters."""
        meter_filter = ""
        if meter_ids:
            ids_str = '", "'.join(meter_ids)
            meter_filter = f' and r._measurement == "meter_reading" and r.meter_id =~ /({ids_str})/"'

        query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r._measurement == "meter_reading"{meter_filter})
                |> last()
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> limit(n: {limit})
        '''

        return self._execute_query(query)

    def get_meter_history(
        self,
        meter_id: str,
        duration: str = "24h",
        aggregation: str = "mean",
    ) -> List[Dict[str, Any]]:
        """Get historical readings for a specific meter."""
        agg_fn = (
            aggregation
            if aggregation in ["mean", "max", "min", "sum", "last", "first"]
            else "mean"
        )

        query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{duration})
                |> filter(fn: (r) => r._measurement == "meter_reading" and r.meter_id == "{meter_id}")
                |> aggregateWindow(every: 5m, fn: {agg_fn}, createEmpty: false)
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
        '''

        return self._execute_query(query)

    def get_grid_metrics(
        self,
        duration: str = "1h",
        interval: str = "5m",
    ) -> List[Dict[str, Any]]:
        """Get aggregated grid metrics over time."""
        query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{duration})
                |> filter(fn: (r) => r._measurement == "grid_status")
                |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
        '''

        return self._execute_query(query)

    def get_energy_summary(
        self,
        duration: str = "24h",
        meter_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get energy generation/consumption summary."""
        meter_filter = ""
        if meter_ids:
            '", "'.join(meter_ids)
            meter_filter = f" and r.meter_id =~ /({'|'.join(meter_ids)})/"

        # Generation summary
        gen_query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{duration})
                |> filter(fn: (r) => r._measurement == "meter_reading" and r._field == "energy_generated"{meter_filter})
                |> sum()
        '''

        # Consumption summary
        cons_query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{duration})
                |> filter(fn: (r) => r._measurement == "meter_reading" and r._field == "energy_consumed"{meter_filter})
                |> sum()
        '''

        gen_results = self._execute_query(gen_query)
        cons_results = self._execute_query(cons_query)

        total_gen = sum(r.get("value", 0) for r in gen_results if r.get("value"))
        total_cons = sum(r.get("value", 0) for r in cons_results if r.get("value"))

        return {
            "duration": duration,
            "total_generation_kwh": round(total_gen, 2),
            "total_consumption_kwh": round(total_cons, 2),
            "net_energy_kwh": round(total_gen - total_cons, 2),
            "self_sufficiency_pct": round(
                (total_gen / total_cons * 100) if total_cons > 0 else 0, 1
            ),
        }

    def get_alerts(
        self,
        duration: str = "24h",
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        severity_filter = f' and r.severity == "{severity}"' if severity else ""

        query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{duration})
                |> filter(fn: (r) => r._measurement == "alert"{severity_filter})
                |> sort(columns: ["_time"], desc: true)
                |> limit(n: {limit})
        '''

        return self._execute_query(query)

    def get_real_time_dashboard(
        self,
        meter_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive real-time dashboard data."""
        readings = self.get_latest_readings(meter_ids=meter_ids, limit=1000)

        # Aggregate statistics
        total_gen = 0.0
        total_cons = 0.0
        active_meters = set()

        for r in readings:
            if r.get("meter_id"):
                active_meters.add(r["meter_id"])
            total_gen += r.get("energy_generated", 0) or 0
            total_cons += r.get("energy_consumed", 0) or 0

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_meters": len(active_meters),
            "total_generation_kw": round(total_gen, 2),
            "total_consumption_kw": round(total_cons, 2),
            "net_balance_kw": round(total_gen - total_cons, 2),
            "readings": readings[:100],  # Limit for API response
        }
