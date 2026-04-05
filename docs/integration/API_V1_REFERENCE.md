# API v1 Reference

The **GridTokenX Smart Meter Simulator** provides a unified REST API under the `/api/v1` prefix. This API allows for full control of the simulation, meter management, grid telemetry, and VPP orchestration.

## 📡 Simulation Control

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/simulation/status` | `GET` | Get current simulator status, weather, and grid stress. |
| `/simulation/status/full` | `GET` | Comprehensive status including grid topology and Rust engine state. |
| `/simulation/acceleration` | `GET` | Detailed performance metrics for the Rust PyO3 engine. |
| `/simulation/actions/start` | `POST` | Start the simulation tick loop. |
| `/simulation/actions/stop` | `POST` | Stop the simulation gracefully. |
| `/simulation/actions/pause` | `POST` | Pause the simulation. |
| `/simulation/actions/resume` | `POST` | Resume a paused simulation. |
| `/simulation/environment` | `PATCH` | Update weather mode and grid stress multiplier. |

## 📟 Meter Management

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/meters` | `GET` | List all active smart meters with their types and locations. |
| `/meters/{meter_id}` | `GET` | Get detailed technical specifications for a specific meter. |
| `/meters/{meter_id}/readings` | `GET` | Retrieve historical readings for a specific meter. |
| `/meters/{meter_id}/readings/override` | `POST` | Manually override meter physics for a set number of ticks. |
| `/meters/profiles` | `GET` | List available Standard Load Profiles (SLP). |

## ⚡ Grid & VPP Infrastructure

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/grid/topology` | `GET` | Get current network statistics (buses, lines, loads). |
| `/grid/state-estimation` | `GET` | Retrieve the latest WLS state estimation results. |
| `/grid/export` | `GET` | Export grid data in **GeoJSON**, **CIM**, or **MVT** formats. |
| `/vpp/clusters` | `GET` | Get real-time status of Virtual Power Plant clusters. |
| `/vpp/actions/dispatch` | `POST` | Send manual dispatch commands (curtail, charge, discharge, shed). |

## 📊 Analytics

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/analytics/summary` | `GET` | High-level dashboard data: grid health, LMP stats, and carbon intensity. |

---
_Note: Industrial protocols such as **DLMS/COSEM** are handled via the gRPC gateway on port `50051`. Refer to the [Transport Layer](../architecture/transport-layer.md) documentation for more details._
