"""
InfluxDB Transport Layer - Complete Smart Meter Simulator Data Storage

Stores ALL simulation data for time-series analysis and Grafana dashboards:
- Meter readings (generation, consumption, battery, voltage, current)
- Market orders & clearing results
- VPP dispatch commands & cluster health
- Grid frequency & stability metrics
- Islanding detection & microgrid status
- Demand response events
- Carbon intensity tracking
- State estimation results
- Weather conditions
- Price history (ToU, P2P dynamic)
- Alerts & anomalies
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .base import TransportLayer

logger = logging.getLogger(__name__)


class InfluxDBTransport(TransportLayer):
    """
    InfluxDB transport for complete simulation data storage.
    Stores all time-series data for Grafana visualization,
    trend analysis, and historical auditing.
    """

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
        max_retries: int = 3,
        retry_backoff: float = 1.0
    ):
        super().__init__(max_retries=max_retries, retry_backoff=retry_backoff)
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client: InfluxDBClient = None
        self.write_api = None

    async def connect(self) -> bool:
        """Initialize the InfluxDB client with optimized write options."""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=10_000
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self._set_connected(True)
            logger.info(f"✅ InfluxDB Transport connected to {self.url}, org={self.org}, bucket={self.bucket}, token={self.token[:10]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to connect InfluxDB Transport: {e}")
            self._set_connected(False)
            return False

    async def disconnect(self) -> bool:
        """Shutdown the InfluxDB client."""
        if self.client:
            self.write_api.close()
            self.client.close()
            self.client = None
            self.write_api = None
            self._set_connected(False)
            logger.info("InfluxDB Transport disconnected")
            return True
        return False

    # =========================================================================
    # Core Reading Conversion
    # =========================================================================

    def _reading_to_point(self, reading: Any) -> Point:
        """Convert a reading dict to an InfluxDB Point."""
        data = self._convert_reading_to_dict(reading)
        timestamp = data.get("timestamp") or datetime.utcnow().isoformat()

        point = Point("meter_reading") \
            .tag("meter_id", str(data.get("meter_id", "unknown"))) \
            .tag("meter_type", str(data.get("meter_type", "unknown"))) \
            .tag("location", str(data.get("location", "unknown"))) \
            .tag("accuracy_class", str(data.get("accuracy_class", "unknown"))) \
            .field("energy_generated_kwh", float(data.get("energy_generated_kwh", 0.0))) \
            .field("energy_consumed_kwh", float(data.get("energy_consumed_kwh", 0.0))) \
            .field("battery_level_kwh", float(data.get("battery_level_kwh", 0.0))) \
            .field("battery_soc_pct", float(data.get("battery_soc_pct", 0.0))) \
            .field("voltage_v", float(data.get("voltage_v", 0.0))) \
            .field("current_a", float(data.get("current_a", 0.0))) \
            .field("frequency_hz", float(data.get("frequency_hz", 50.0))) \
            .field("active_power_kw", float(data.get("active_power_kw", 0.0))) \
            .field("reactive_power_kvar", float(data.get("reactive_power_kvar", 0.0))) \
            .field("power_factor", float(data.get("power_factor", 1.0))) \
            .field("carbon_offset_kg", float(data.get("carbon_offset_kg", 0.0))) \
            .field("temperature_c", float(data.get("temperature_c", 25.0))) \
            .time(timestamp)

        return point

    # =========================================================================
    # Main Transport Methods (required by base class)
    # =========================================================================

    async def send_reading(self, reading: Any) -> bool:
        """Send a single meter reading to InfluxDB."""
        if not self.connected:
            return False
        try:
            point = self._reading_to_point(reading)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending reading to InfluxDB: {e}")
            return False

    async def send_batch(self, readings: List[Any]) -> bool:
        """Send a batch of meter readings to InfluxDB."""
        if not self.connected:
            logger.debug("InfluxDB not connected, skipping batch")
            return False
        try:
            points = [self._reading_to_point(r) for r in readings]
            logger.debug(f"Writing {len(points)} points to InfluxDB bucket={self.bucket}")
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.debug(f"✅ Successfully wrote {len(points)} readings to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Error sending batch to InfluxDB: {e}")
            return False

    async def send_auction_bid(self, bid_payload: Dict[str, Any], batch_id: str) -> bool:
        """Send market order/bid to InfluxDB."""
        if not self.connected:
            return False
        try:
            timestamp = bid_payload.get("timestamp") or datetime.utcnow().isoformat()
            point = Point("market_order") \
                .tag("order_id", str(bid_payload.get("order_id", "unknown"))) \
                .tag("meter_id", str(bid_payload.get("meter_id", "unknown"))) \
                .tag("side", str(bid_payload.get("side", "unknown"))) \
                .tag("status", str(bid_payload.get("status", "pending"))) \
                .field("quantity_kwh", float(bid_payload.get("quantity_kwh", 0.0))) \
                .field("price_baht", float(bid_payload.get("price_baht", 0.0))) \
                .field("total_value_baht", float(bid_payload.get("total_value_baht", 0.0))) \
                .field("min_price_baht", float(bid_payload.get("min_price_baht", 0.0))) \
                .field("max_price_baht", float(bid_payload.get("max_price_baht", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending order to InfluxDB: {e}")
            return False

    async def send_grid_status(self, status: Dict[str, Any]) -> bool:
        """Send state estimation results to InfluxDB."""
        if not self.connected:
            return False
        try:
            timestamp = status.get("timestamp") or datetime.utcnow().isoformat()
            point = Point("grid_state_estimation") \
                .tag("converged", str(status.get("converged", False))) \
                .tag("algorithm", str(status.get("algorithm", "wls"))) \
                .field("chi_squared", float(status.get("chi_squared", 0.0))) \
                .field("mae", float(status.get("mae", 0.0))) \
                .field("max_residual", float(status.get("max_residual", 0.0))) \
                .field("total_loss_mw", float(status.get("total_loss_mw", 0.0))) \
                .field("loss_pct", float(status.get("loss_pct", 0.0))) \
                .field("avg_voltage_pu", float(status.get("avg_voltage_pu", 1.0))) \
                .field("health_score", float(status.get("health_score", 100.0))) \
                .field("violations", int(status.get("violations", 0))) \
                .field("measurements_used", int(status.get("measurements_used", 0))) \
                .field("bad_data_removed", int(status.get("bad_data_removed", 0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending grid status to InfluxDB: {e}")
            return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to InfluxDB."""
        if not self.connected:
            return False
        try:
            timestamp = alert.get("timestamp") or datetime.utcnow().isoformat()
            point = Point("alert") \
                .tag("type", str(alert.get("type", "unknown"))) \
                .tag("severity", str(alert.get("severity", "info"))) \
                .tag("source", str(alert.get("source", "simulator"))) \
                .field("message", str(alert.get("message", ""))) \
                .field("value", float(alert.get("value", 0.0))) \
                .field("threshold", float(alert.get("threshold", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending alert to InfluxDB: {e}")
            return False

    # =========================================================================
    # Advanced Simulation Data Methods
    # =========================================================================

    async def send_vpp_dispatch(self, dispatch_data: Dict[str, Any]) -> bool:
        """Send VPP dispatch commands and cluster status."""
        if not self.connected:
            return False
        try:
            timestamp = dispatch_data.get("timestamp") or datetime.utcnow().isoformat()
            cluster_id = dispatch_data.get("cluster_id", "unknown")

            # Cluster-level metrics
            point = Point("vpp_cluster") \
                .tag("cluster_id", cluster_id) \
                .tag("status", str(dispatch_data.get("status", "active"))) \
                .field("total_capacity_kw", float(dispatch_data.get("total_capacity_kw", 0.0))) \
                .field("total_dispatch_kw", float(dispatch_data.get("total_dispatch_kw", 0.0))) \
                .field("utilization_pct", float(dispatch_data.get("utilization_pct", 0.0))) \
                .field("health_score", float(dispatch_data.get("health_score", 100.0))) \
                .field("carbon_saved_kg", float(dispatch_data.get("carbon_saved_kg", 0.0))) \
                .field("num_meters", int(dispatch_data.get("num_meters", 0))) \
                .field("afrr_power_kw", float(dispatch_data.get("afrr_power_kw", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

            # Per-meter dispatch
            for meter_dispatch in dispatch_data.get("meters", []):
                point = Point("vpp_dispatch") \
                    .tag("cluster_id", cluster_id) \
                    .tag("meter_id", str(meter_dispatch.get("meter_id", "unknown"))) \
                    .tag("dispatch_type", str(meter_dispatch.get("dispatch_type", "normal"))) \
                    .field("setpoint_kw", float(meter_dispatch.get("setpoint_kw", 0.0))) \
                    .field("actual_kw", float(meter_dispatch.get("actual_kw", 0.0))) \
                    .field("response_time_ms", float(meter_dispatch.get("response_time_ms", 0.0))) \
                    .field("compliance_pct", float(meter_dispatch.get("compliance_pct", 100.0))) \
                    .time(timestamp)

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending VPP dispatch to InfluxDB: {e}")
            return False

    async def send_market_clearing(self, clearing_data: Dict[str, Any]) -> bool:
        """Send market clearing results."""
        if not self.connected:
            return False
        try:
            timestamp = clearing_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("market_clearing") \
                .tag("market_id", str(clearing_data.get("market_id", "default"))) \
                .tag("status", str(clearing_data.get("status", "cleared"))) \
                .field("clearing_price_baht", float(clearing_data.get("clearing_price_baht", 0.0))) \
                .field("total_volume_kwh", float(clearing_data.get("total_volume_kwh", 0.0))) \
                .field("total_value_baht", float(clearing_data.get("total_value_baht", 0.0))) \
                .field("num_bids", int(clearing_data.get("num_bids", 0))) \
                .field("num_offers", int(clearing_data.get("num_offers", 0))) \
                .field("num_matched", int(clearing_data.get("num_matched", 0))) \
                .field("supply_demand_ratio", float(clearing_data.get("supply_demand_ratio", 1.0))) \
                .field("clearing_time_ms", float(clearing_data.get("clearing_time_ms", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending market clearing to InfluxDB: {e}")
            return False

    async def send_frequency_event(self, freq_data: Dict[str, Any]) -> bool:
        """Send grid frequency regulation events."""
        if not self.connected:
            return False
        try:
            timestamp = freq_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("grid_frequency") \
                .tag("zone", str(freq_data.get("zone", "default"))) \
                .field("frequency_hz", float(freq_data.get("frequency_hz", 50.0))) \
                .field("deviation_hz", float(freq_data.get("deviation_hz", 0.0))) \
                .field("droop_response_kw", float(freq_data.get("droop_response_kw", 0.0))) \
                .field("total_generation_kw", float(freq_data.get("total_generation_kw", 0.0))) \
                .field("total_load_kw", float(freq_data.get("total_load_kw", 0.0))) \
                .field("imbalance_kw", float(freq_data.get("imbalance_kw", 0.0))) \
                .field("roc_hz_per_sec", float(freq_data.get("roc_hz_per_sec", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending frequency event to InfluxDB: {e}")
            return False

    async def send_islanding_event(self, island_data: Dict[str, Any]) -> bool:
        """Send islanding detection and microgrid events."""
        if not self.connected:
            return False
        try:
            timestamp = island_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("grid_islanding") \
                .tag("mode", str(island_data.get("mode", "grid_connected"))) \
                .tag("trigger", str(island_data.get("trigger", "none"))) \
                .field("grid_voltage_v", float(island_data.get("grid_voltage_v", 0.0))) \
                .field("island_frequency_hz", float(island_data.get("island_frequency_hz", 50.0))) \
                .field("power_balance_kw", float(island_data.get("power_balance_kw", 0.0))) \
                .field("load_shed_kw", float(island_data.get("load_shed_kw", 0.0))) \
                .field("island_duration_s", float(island_data.get("island_duration_s", 0.0))) \
                .field("reconnection_attempts", int(island_data.get("reconnection_attempts", 0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending islanding event to InfluxDB: {e}")
            return False

    async def send_demand_response(self, dr_data: Dict[str, Any]) -> bool:
        """Send demand response events."""
        if not self.connected:
            return False
        try:
            timestamp = dr_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("demand_response") \
                .tag("event_id", str(dr_data.get("event_id", "unknown"))) \
                .tag("type", str(dr_data.get("type", "voluntary"))) \
                .tag("status", str(dr_data.get("status", "active"))) \
                .field("target_reduction_kw", float(dr_data.get("target_reduction_kw", 0.0))) \
                .field("actual_reduction_kw", float(dr_data.get("actual_reduction_kw", 0.0))) \
                .field("participating_meters", int(dr_data.get("participating_meters", 0))) \
                .field("incentive_baht", float(dr_data.get("incentive_baht", 0.0))) \
                .field("duration_minutes", float(dr_data.get("duration_minutes", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending demand response to InfluxDB: {e}")
            return False

    async def send_carbon_intensity(self, carbon_data: Dict[str, Any]) -> bool:
        """Send carbon intensity tracking."""
        if not self.connected:
            return False
        try:
            timestamp = carbon_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("carbon_intensity") \
                .tag("zone", str(carbon_data.get("zone", "default"))) \
                .field("intensity_gco2_kwh", float(carbon_data.get("intensity_gco2_kwh", 0.0))) \
                .field("renewable_pct", float(carbon_data.get("renewable_pct", 0.0))) \
                .field("total_generation_kwh", float(carbon_data.get("total_generation_kwh", 0.0))) \
                .field("total_consumption_kwh", float(carbon_data.get("total_consumption_kwh", 0.0))) \
                .field("carbon_offset_kg", float(carbon_data.get("carbon_offset_kg", 0.0))) \
                .field("carbon_cost_baht", float(carbon_data.get("carbon_cost_baht", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending carbon intensity to InfluxDB: {e}")
            return False

    async def send_weather(self, weather_data: Dict[str, Any]) -> bool:
        """Send weather simulation data."""
        if not self.connected:
            return False
        try:
            timestamp = weather_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("weather") \
                .tag("condition", str(weather_data.get("condition", "unknown"))) \
                .tag("location", str(weather_data.get("location", "default"))) \
                .field("temperature_c", float(weather_data.get("temperature_c", 25.0))) \
                .field("humidity_pct", float(weather_data.get("humidity_pct", 50.0))) \
                .field("solar_irradiance_wm2", float(weather_data.get("solar_irradiance_wm2", 0.0))) \
                .field("wind_speed_ms", float(weather_data.get("wind_speed_ms", 0.0))) \
                .field("cloud_cover_pct", float(weather_data.get("cloud_cover_pct", 0.0))) \
                .field("solar_efficiency_pct", float(weather_data.get("solar_efficiency_pct", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending weather to InfluxDB: {e}")
            return False

    async def send_price_update(self, price_data: Dict[str, Any]) -> bool:
        """Send price history (ToU, P2P dynamic)."""
        if not self.connected:
            return False
        try:
            timestamp = price_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("price_history") \
                .tag("price_type", str(price_data.get("price_type", "p2p"))) \
                .tag("period", str(price_data.get("period", "off_peak"))) \
                .field("tou_rate_baht_kwh", float(price_data.get("tou_rate_baht_kwh", 0.0))) \
                .field("p2p_rate_baht_kwh", float(price_data.get("p2p_rate_baht_kwh", 0.0))) \
                .field("wheeling_cost_baht_kwh", float(price_data.get("wheeling_cost_baht_kwh", 0.0))) \
                .field("ft_charge_baht_kwh", float(price_data.get("ft_charge_baht_kwh", 0.0))) \
                .field("vat_pct", float(price_data.get("vat_pct", 7.0))) \
                .field("discount_pct", float(price_data.get("discount_pct", 0.0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending price update to InfluxDB: {e}")
            return False

    async def send_simulation_step(self, step_data: Dict[str, Any]) -> bool:
        """Send simulation step metrics (overall health)."""
        if not self.connected:
            return False
        try:
            timestamp = step_data.get("timestamp") or datetime.utcnow().isoformat()

            point = Point("simulation_step") \
                .tag("status", str(step_data.get("status", "running"))) \
                .field("elapsed_seconds", float(step_data.get("elapsed_seconds", 0.0))) \
                .field("tick_duration_ms", float(step_data.get("tick_duration_ms", 0.0))) \
                .field("active_meters", int(step_data.get("active_meters", 0))) \
                .field("total_generation_kw", float(step_data.get("total_generation_kw", 0.0))) \
                .field("total_consumption_kw", float(step_data.get("total_consumption_kw", 0.0))) \
                .field("net_balance_kw", float(step_data.get("net_balance_kw", 0.0))) \
                .field("readings_sent", int(step_data.get("readings_sent", 0))) \
                .field("errors_count", int(step_data.get("errors_count", 0))) \
                .time(timestamp)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
        except Exception as e:
            logger.error(f"Error sending simulation step to InfluxDB: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self.connected
