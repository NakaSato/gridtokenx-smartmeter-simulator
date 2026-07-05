"""Public market/grid WebSocket endpoint.

Pushes live aggregate grid status to browser clients. Exposed at the app root as
`/ws` (not under the `/api/v1` prefix) because the APISIX public gateway rewrites
`/api/market/ws` -> `/ws` before proxying (see apisix_conf/apisix.yaml route id 9).

The push is decoupled from the simulation tick loop: this handler polls
`engine.last_tick_summary` on a fixed cadence and emits a `grid_status` frame. The
trading dashboard's `useGridStatus` hook merges these frames into its React Query
cache (components/energy-grid/useGridStatus.ts) and falls back to REST polling when
the socket is unavailable, so a missed frame is never fatal.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Market WS"])

# Cadence of grid_status pushes, seconds. Matches the dashboard's expectation of
# near-real-time updates without flooding idle clients.
_PUSH_INTERVAL_S = 2.0


def _get_app_state():
    from smart_meter_simulator.core import app_state

    return app_state


def _build_grid_status(engine: Any) -> dict[str, Any]:
    """Map the engine's last tick summary into the dashboard's grid_status shape.

    Field names mirror the `GridStatus` type consumed by the trading web client.
    Absent metrics are simply omitted; the client treats every field as optional.
    """
    summary = getattr(engine, "last_tick_summary", None) or {}
    return {
        "total_generation": summary.get("total_generation_kwh"),
        "total_consumption": summary.get("total_consumption_kwh"),
        "net_balance": summary.get("net_energy_kwh"),
        "active_meters": len(getattr(engine, "meters", []) or []),
        "frequency": summary.get("frequency_hz"),
        "timestamp": summary.get("timestamp"),
    }


def _build_meter_telemetry(engine: Any) -> list[dict[str, Any]]:
    """Per-meter live telemetry frame (map contract `meter.telemetry`).

    One entry per meter from the last tick's readings, energy-per-interval
    converted to average kW — the same real values the REST /meters payload
    exposes, pushed so map markers update between 30s polls.
    """
    frames: list[dict[str, Any]] = []
    for reading in getattr(engine, "last_readings", None) or []:
        interval_s = getattr(reading, "interval_seconds", 0) or 0
        if interval_s <= 0:
            continue
        to_kw = 3600.0 / interval_s
        generation_kw = (reading.energy_generated or 0.0) * to_kw
        consumption_kw = (reading.energy_consumed or 0.0) * to_kw
        net_kw = generation_kw - consumption_kw
        frames.append(
            {
                "meter_id": reading.meter_id,
                "generation_kw": round(generation_kw, 3),
                "consumption_kw": round(consumption_kw, 3),
                "surplus_kw": round(max(net_kw, 0.0), 3),
                "deficit_kw": round(max(-net_kw, 0.0), 3),
                "status": "active",
            }
        )
    return frames


@router.websocket("/ws")
async def market_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            engine = _get_app_state().engine
            if engine is not None:
                await websocket.send_json(
                    {
                        "type": "grid_status",
                        "data": _build_grid_status(engine),
                    }
                )
                telemetry = _build_meter_telemetry(engine)
                if telemetry:
                    await websocket.send_json(
                        {"type": "meter.telemetry", "data": telemetry}
                    )
            await asyncio.sleep(_PUSH_INTERVAL_S)
    except WebSocketDisconnect:
        logger.debug("market_ws client disconnected")
    except Exception:  # noqa: BLE001 - never let a socket error crash the server
        logger.exception("market_ws push loop failed")
