from datetime import datetime
from typing import Any, Dict, List
from influxdb_client import Point

def map_reading(data: Dict[str, Any]) -> Point:
    timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
    return Point("meter_reading") \
        .tag("meter_id", str(data.get("meter_id", "unknown"))) \
        .tag("meter_type", str(data.get("meter_type", "unknown"))) \
        .tag("location", str(data.get("location", "unknown"))) \
        .field("energy_generated_kwh", float(data.get("energy_generated_kwh", 0.0))) \
        .field("energy_consumed_kwh", float(data.get("energy_consumed_kwh", 0.0))) \
        .field("battery_soc_pct", float(data.get("battery_soc_pct", 0.0))) \
        .field("voltage_v", float(data.get("voltage_v", 0.0))) \
        .field("current_a", float(data.get("current_a", 0.0))) \
        .field("frequency_hz", float(data.get("frequency_hz", 50.0))) \
        .time(timestamp)

def map_grid_status(status: Dict[str, Any]) -> Point:
    timestamp = status.get("timestamp") or datetime.utcnow().isoformat()
    return Point("grid_state_estimation") \
        .tag("converged", str(status.get("converged", False))) \
        .field("total_loss_mw", float(status.get("total_loss_mw", 0.0))) \
        .field("avg_voltage_pu", float(status.get("avg_voltage_pu", 1.0))) \
        .field("health_score", float(status.get("health_score", 100.0))) \
        .time(timestamp)

def map_vpp_dispatch(dispatch_data: Dict[str, Any]) -> List[Point]:
    timestamp = dispatch_data.get("timestamp") or datetime.utcnow().isoformat()
    cluster_id = dispatch_data.get("cluster_id", "unknown")
    
    points = []
    points.append(Point("vpp_cluster") \
        .tag("cluster_id", cluster_id) \
        .field("total_dispatch_kw", float(dispatch_data.get("total_dispatch_kw", 0.0))) \
        .field("health_score", float(dispatch_data.get("health_score", 100.0))) \
        .time(timestamp))
        
    for m in dispatch_data.get("meters", []):
        points.append(Point("vpp_dispatch") \
            .tag("cluster_id", cluster_id) \
            .tag("meter_id", str(m.get("meter_id", "unknown"))) \
            .field("setpoint_kw", float(m.get("setpoint_kw", 0.0))) \
            .time(timestamp))
            
    return points
