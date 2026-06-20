"""Operational-telemetry egress — operator-facing grid/microgrid state.

DLMS/COSEM (``aggregator_bridge.py``) ships **meter** registers; this ships the
**operator** points a SCADA master expects but OBIS has no codes for: per-zone
frequency, island/breaker status, bus-fault counters, DER curtailment, transformer
loading/tap, tie-switch state. It consumes the engine **tick summary** (not
per-meter readings) and maps it to a flat list of typed DNP3/IEC-104-shaped
points.

The mapping (:func:`summary_to_points`) is the reusable, standards-aligned part —
each point carries a DNP3 group (``AI`` analog input / ``BI`` binary input) and an
IEC 60870-5-104 ASDU type id, so a real outstation stack (pydnp3, c104) can be
dropped in later. The transport here is a deliberately thin JSON-collector POST:
it proves the point model end-to-end without pulling in a DNP3/104 TCP server.

Lifecycle mirrors the DLMS emitter and the persistence stores: optional,
config-gated, fire-and-forget per tick, **drops a tick if the prior batch is still
in flight**, and never propagates a failure into the tick (increments
``operational_emit_failed_total`` instead). Default off.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Mapping, Optional

import httpx

from smart_meter_simulator.core.metrics import OPERATIONAL_EMIT_FAILED

logger = logging.getLogger(__name__)


# DNP3 point group (monitor direction) and the matching IEC 60870-5-104 ASDU
# type id, kept together so one mapping serves either outstation.
#   AI  -> analog input   ; IEC-104 M_ME_NC (13) short-float measured value
#   BI  -> binary input   ; IEC-104 M_SP_NA (1)  single-point status
#   CTR -> counter        ; IEC-104 M_ME_NB (11) scaled measured value
DNP3_AI = "AI"
DNP3_BI = "BI"
DNP3_CTR = "CTR"

IEC104_M_ME_NC = 13  # measured value, short floating point
IEC104_M_SP_NA = 1  # single-point information (status bit)
IEC104_M_ME_NB = 11  # measured value, scaled integer (counters)


def _pt(index: int, name: str, group: str, asdu: int, value: Any) -> dict:
    """One typed telemetry point in the flat outstation point list."""
    return {
        "index": index,
        "name": name,
        "dnp3_group": group,
        "iec104_asdu": asdu,
        "value": value,
    }


def summary_to_points(summary: Mapping[str, Any]) -> List[dict]:
    """Map an engine tick summary to a flat list of SCADA points.

    Pure function (no I/O, no state) so it is trivially testable and reusable by
    any transport. Point indices are stable within a category: system points are
    fixed, per-zone/per-switch points are offset by a deterministic base so a
    master can address ``zone <code>`` or ``switch <name>`` consistently.
    """
    points: List[dict] = []

    # --- System analog inputs (feeder-wide state) ---------------------------
    points.append(
        _pt(
            0, "grid_frequency_hz", DNP3_AI, IEC104_M_ME_NC, summary.get("frequency_hz")
        )
    )
    points.append(
        _pt(
            1,
            "total_losses_kw",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_losses_kw"),
        )
    )
    points.append(
        _pt(
            2,
            "total_curtailed_kw",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_curtailed_kw"),
        )
    )
    points.append(
        _pt(
            3,
            "total_reactive_support_kvar",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_reactive_support_kvar"),
        )
    )
    points.append(
        _pt(
            4,
            "transformer_loading_pct",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("transformer_loading_pct"),
        )
    )
    points.append(
        _pt(
            5,
            "transformer_tap_pos",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("transformer_tap_pos"),
        )
    )
    points.append(
        _pt(
            6,
            "total_dr_shed_kw",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_dr_shed_kw"),
        )
    )

    # --- System counters (contingency state) --------------------------------
    points.append(
        _pt(0, "fault_count", DNP3_CTR, IEC104_M_ME_NB, summary.get("fault_count"))
    )
    points.append(
        _pt(
            1,
            "islanded_bus_count",
            DNP3_CTR,
            IEC104_M_ME_NB,
            summary.get("islanded_bus_count"),
        )
    )
    points.append(
        _pt(
            2,
            "active_dr_events",
            DNP3_CTR,
            IEC104_M_ME_NB,
            summary.get("active_dr_events"),
        )
    )

    # --- Per-zone points: AI frequency, BI island/breaker status ------------
    # index = base offset + zone_code, so zone N's points are addressable.
    Z_FREQ_BASE = 100
    Z_ISL_BASE = 0
    Z_CMD_BASE = 1000
    for z in summary.get("zones", []) or []:
        code = int(z.get("zone_code", 0))
        points.append(
            _pt(
                Z_FREQ_BASE + code,
                f"zone_{code}_frequency_hz",
                DNP3_AI,
                IEC104_M_ME_NC,
                z.get("frequency_hz"),
            )
        )
        # Electrical island (zone de-energized / off the slack).
        points.append(
            _pt(
                Z_ISL_BASE + code,
                f"zone_{code}_islanded",
                DNP3_BI,
                IEC104_M_SP_NA,
                bool(z.get("islanded")),
            )
        )
        # Commanded island = PCC breaker open (operator action).
        points.append(
            _pt(
                Z_CMD_BASE + code,
                f"zone_{code}_breaker_open",
                DNP3_BI,
                IEC104_M_SP_NA,
                bool(z.get("commanded_island")),
            )
        )

    # --- Per-switch binary status (tie/sectionalizer closed?) ---------------
    # Optional: only present when the engine threads switch status into the
    # summary (see OperationalTelemetryEmitter.emit). Indexed by enumeration order.
    S_BASE = 2000
    for i, sw in enumerate(summary.get("switches", []) or []):
        points.append(
            _pt(
                S_BASE + i,
                f"switch_{sw.get('name')}_closed",
                DNP3_BI,
                IEC104_M_SP_NA,
                bool(sw.get("closed")),
            )
        )

    return points


class OperationalTelemetryClient:
    """Async client posting a SCADA point batch to a collector endpoint.

    Thin stand-in for a DNP3/IEC-104 outstation: a single JSON POST of the point
    list. Swap this class for a real outstation stack without touching the
    mapping or the emitter.
    """

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.ingest_url = f"{self.base_url}/operational/telemetry"
        self._client = httpx.AsyncClient(timeout=timeout)

    async def send_points(self, timestamp: str, points: List[dict]) -> httpx.Response:
        resp = await self._client.post(
            self.ingest_url, json={"timestamp": timestamp, "points": points}
        )
        resp.raise_for_status()
        return resp

    async def close(self) -> None:
        await self._client.aclose()


class OperationalTelemetryEmitter:
    """Ship per-tick operational points to a SCADA collector, non-blocking.

    Consumes the tick **summary**; call :meth:`emit` once per tick after the
    engine has built it. Drops a tick if a prior batch is still in flight, so a
    slow collector throttles cadence instead of backing up the sim loop.
    """

    def __init__(self, base_url: str, *, emit_every: int = 1, timeout: float = 10.0):
        self._client = OperationalTelemetryClient(base_url, timeout=timeout)
        self._emit_every = max(1, emit_every)
        self._inflight: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._started = False

    def start(self) -> None:
        """Mark active. Call once when the engine starts."""
        self._started = True
        logger.info(
            "Operational telemetry emitter active -> %s", self._client.ingest_url
        )

    def emit(self, summary: Mapping[str, Any]) -> None:
        """Schedule a background point-batch send for this tick's summary.

        Synchronous and non-blocking. Drops the tick if the emitter is not
        started, there is no summary, the cadence gate skips it, or a prior
        batch is still running.
        """
        if not self._started or not summary:
            return
        self._tick_count += 1
        if self._tick_count % self._emit_every != 0:
            return
        if self._inflight is not None and not self._inflight.done():
            logger.debug("Operational emit skipped: previous batch still in flight")
            return
        points = summary_to_points(summary)
        timestamp = str(summary.get("timestamp", ""))
        self._inflight = asyncio.create_task(self._send(timestamp, points))

    async def _send(self, timestamp: str, points: List[dict]) -> None:
        try:
            await self._client.send_points(timestamp, points)
        except Exception:
            OPERATIONAL_EMIT_FAILED.inc()
            logger.warning(
                "Operational telemetry batch failed (%d points)", len(points)
            )

    async def close(self) -> None:
        """Cancel any in-flight batch and close the HTTP client."""
        if self._inflight is not None and not self._inflight.done():
            self._inflight.cancel()
        await self._client.close()
