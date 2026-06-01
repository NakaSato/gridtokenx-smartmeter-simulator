from datetime import datetime
from typing import Any, Dict, List
from influxdb_client import Point


def map_reading(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("meter_reading")
        .tag("meter_id", str(data.get("meter_id", "unknown")))
        .tag("meter_type", str(data.get("meter_type", "unknown")))
        .tag("location", str(data.get("location", "unknown")))
        .field("energy_generated_kwh", float(data.get("energy_generated_kwh", 0.0)))
        .field("energy_consumed_kwh", float(data.get("energy_consumed_kwh", 0.0)))
        .field("battery_soc_pct", float(data.get("battery_soc_pct", 0.0)))
        .field("voltage_v", float(data.get("voltage_v", 0.0)))
        .field("current_a", float(data.get("current_a", 0.0)))
        .field("frequency_hz", float(data.get("frequency_hz", 50.0)))
        .time(timestamp)
    )


def map_grid_status(status: Dict[str, Any]) -> Point:
    timestamp = status.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("grid_state_estimation")
        .tag("converged", str(status.get("converged", False)))
        .field("total_loss_mw", float(status.get("total_loss_mw", 0.0)))
        .field("avg_voltage_pu", float(status.get("avg_voltage_pu", 1.0)))
        .field("health_score", float(status.get("health_score", 100.0)))
        .time(timestamp)
    )


def map_vpp_dispatch(dispatch_data: Dict[str, Any]) -> List[Point]:
    timestamp = dispatch_data.get("timestamp") or datetime.utcnow().isoformat()
    cluster_id = dispatch_data.get("cluster_id", "unknown")

    points = []
    points.append(
        Point("vpp_cluster")
        .tag("cluster_id", cluster_id)
        .field("total_dispatch_kw", float(dispatch_data.get("total_dispatch_kw", 0.0)))
        .field("health_score", float(dispatch_data.get("health_score", 100.0)))
        .time(timestamp)
    )

    for m in dispatch_data.get("meters", []):
        points.append(
            Point("vpp_dispatch")
            .tag("cluster_id", cluster_id)
            .tag("meter_id", str(m.get("meter_id", "unknown")))
            .field("setpoint_kw", float(m.get("setpoint_kw", 0.0)))
            .time(timestamp)
        )

    return points


def map_frequency_event(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("grid_frequency")
        .tag("event_type", str(data.get("event_type", "normal")))
        .field("frequency_hz", float(data.get("frequency_hz", 50.0)))
        .field("deviation_hz", float(data.get("deviation_hz", 0.0)))
        .time(timestamp)
    )


def map_islanding_event(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("grid_topology")
        .tag("islanding_status", str(data.get("status", "connected")))
        .tag("island_id", str(data.get("island_id", "main_grid")))
        .field("meters_count", int(data.get("meters_count", 0)))
        .time(timestamp)
    )


def map_demand_response(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("demand_response")
        .tag("program_id", str(data.get("program_id", "unknown")))
        .field("target_reduction_kw", float(data.get("target_reduction_kw", 0.0)))
        .field("actual_reduction_kw", float(data.get("actual_reduction_kw", 0.0)))
        .time(timestamp)
    )


def map_carbon_intensity(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("carbon_metrics")
        .tag("zone", str(data.get("zone", "thailand")))
        .field("intensity_gco2_kwh", float(data.get("intensity", 0.0)))
        .time(timestamp)
    )


def map_weather(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("weather_conditions")
        .tag("condition", str(data.get("condition", "sunny")))
        .field("temperature_c", float(data.get("temperature", 25.0)))
        .field("cloud_cover_pct", float(data.get("cloud_cover", 0.0)))
        .field("irradiance_wm2", float(data.get("irradiance", 800.0)))
        .time(timestamp)
    )


def map_operational_cost(cost_data: Dict[str, Any]) -> Point:
    timestamp = cost_data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("operational_costs")
        .tag("meter_id", str(cost_data.get("meter_id", "system")))
        .tag("zone", str(cost_data.get("zone", "thailand")))
        .tag("source", str(cost_data.get("source", "grid")))
        .tag("strategy_mode", str(cost_data.get("strategy_mode", "NORMAL")))
        .field("cost_thb", float(cost_data.get("cost_thb", 0.0)))
        .field("savings_thb", float(cost_data.get("savings_thb", 0.0)))
        .field("carbon_tax_thb", float(cost_data.get("carbon_tax_thb", 0.0)))
        .field("diesel_displaced_liters", float(cost_data.get("diesel_displaced_liters", 0.0)))
        .field("carbon_offset_kg", float(cost_data.get("carbon_offset_kg", 0.0)))
        .time(timestamp)
    )


def map_simulation_step(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return (
        Point("simulation_metrics")
        .field("step_index", int(data.get("step_index", 0)))
        .field("execution_time_ms", float(data.get("execution_time_ms", 0.0)))
        .time(timestamp)
    )
