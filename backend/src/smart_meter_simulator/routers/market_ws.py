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
            await asyncio.sleep(_PUSH_INTERVAL_S)
    except WebSocketDisconnect:
        logger.debug("market_ws client disconnected")
    except Exception:  # noqa: BLE001 - never let a socket error crash the server
        logger.exception("market_ws push loop failed")
